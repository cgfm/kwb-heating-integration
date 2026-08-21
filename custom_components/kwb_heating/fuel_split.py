"""Shared, persistent pellet/log-wood energy accounting."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import math
from typing import Any, Protocol

from .register_utils import find_register_by_parameter, normalize_register_address

_LOGGER = logging.getLogger(__name__)

TOTAL_HEAT_PARAMETER = "KSM.waermemenge_gesamt_kwh"
FUEL_MODE_PARAMETER = "CF2.betriebsmodus"

FUEL_GROUP_PELLETS = "pellets"
FUEL_GROUP_LOG_WOOD = "log_wood"
FUEL_GROUP_NONE = "none"
FUEL_GROUP_UNKNOWN = "unknown"

# The cf2_betriebsmodus_t raw mapping is identical in every canonical firmware:
# 0=None/off, 1=log wood, 2=pellets, 3=log wood/PM run-on, 4=relay test.
FUEL_MODE_GROUPS = {
    0: FUEL_GROUP_NONE,
    1: FUEL_GROUP_LOG_WOOD,
    2: FUEL_GROUP_PELLETS,
    3: FUEL_GROUP_LOG_WOOD,
    4: FUEL_GROUP_NONE,
}

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = "kwb_heating.fuel_split"
STORAGE_SAVE_DELAY_SECONDS = 10
STORAGE_REQUEST_INTERVAL_SECONDS = 300
LONG_GAP_INTERVAL_MULTIPLIER = 3


class FuelSplitStore(Protocol):
    """Subset of Home Assistant Store used by the tracker."""

    async def async_load(self) -> dict[str, Any] | None:
        """Load persisted state."""

    def async_delay_save(
        self, data_func: Callable[[], dict[str, Any]], delay: float = 0
    ) -> None:
        """Schedule a delayed save."""

    async def async_save(self, data: dict[str, Any]) -> None:
        """Save state immediately."""


@dataclass
class FuelSplitState:
    """Versioned state shared by all three derived entities."""

    pellet_kwh: float = 0.0
    log_wood_kwh: float = 0.0
    unattributed_kwh: float = 0.0
    last_source_total_kwh: float | None = None
    last_mode_raw: int | None = None
    last_fuel_group: str | None = None
    last_observation_timestamp: datetime | None = None
    tracking_started_at: datetime | None = None
    source_total_at_start: float | None = None
    source_reset_count: int = 0


def fuel_split_storage_key(entry_id: str) -> str:
    """Return the language-independent, config-entry-specific storage key."""
    return f"{STORAGE_KEY_PREFIX}.{entry_id}"


def get_fuel_split_register_addresses(
    registers: list[dict[str, Any]],
) -> tuple[int, int] | None:
    """Discover total and mode addresses from exact register parameters."""
    total_register = find_register_by_parameter(registers, TOTAL_HEAT_PARAMETER)
    mode_register = find_register_by_parameter(registers, FUEL_MODE_PARAMETER)
    total_address = normalize_register_address(
        total_register.get("starting_address") if total_register else None
    )
    mode_address = normalize_register_address(
        mode_register.get("starting_address") if mode_register else None
    )
    if total_address is None or mode_address is None:
        return None
    return total_address, mode_address


def fuel_group_for_raw_mode(value: Any) -> tuple[int | None, str]:
    """Normalize a raw mode and classify it without localized labels."""
    if isinstance(value, bool):
        return None, FUEL_GROUP_UNKNOWN
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None, FUEL_GROUP_UNKNOWN
    if not math.isfinite(numeric) or not numeric.is_integer():
        return None, FUEL_GROUP_UNKNOWN
    raw = int(numeric)
    return raw, FUEL_MODE_GROUPS.get(raw, FUEL_GROUP_UNKNOWN)


def _finite_number(value: Any) -> float | None:
    """Return a finite float, rejecting booleans and malformed values."""
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _nonnegative_number(value: Any, default: float = 0.0) -> float:
    number = _finite_number(value)
    return number if number is not None and number >= 0 else default


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class FuelSplitTracker:
    """Process each combined-counter observation once for one config entry."""

    def __init__(
        self,
        coordinator: Any,
        store: FuelSplitStore,
        total_address: int,
        mode_address: int,
        expected_interval_seconds: float,
        *,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.coordinator = coordinator
        self._store = store
        self.total_address = total_address
        self.mode_address = mode_address
        self.expected_interval_seconds = max(float(expected_interval_seconds), 1.0)
        self.long_gap_seconds = (
            self.expected_interval_seconds * LONG_GAP_INTERVAL_MULTIPLIER
        )
        self._now = now or (lambda: datetime.now(tz=timezone.utc))
        self.state = FuelSplitState()
        self._listeners: set[Callable[[], None]] = set()
        self._unsub_coordinator: Callable[[], None] | None = None
        self._last_persist_request_at: datetime | None = None
        self._initialized = False
        self._shutdown = False

    @property
    def pellet_kwh(self) -> float:
        return self.state.pellet_kwh

    @property
    def log_wood_kwh(self) -> float:
        return self.state.log_wood_kwh

    @property
    def unattributed_kwh(self) -> float:
        return self.state.unattributed_kwh

    @property
    def has_source_baseline(self) -> bool:
        return self.state.last_source_total_kwh is not None

    async def async_initialize(self) -> None:
        """Restore state, subscribe once, and process the current observation."""
        if self._initialized:
            return
        try:
            stored = await self._store.async_load()
        except Exception as exc:  # A corrupt store must not break integration setup.
            _LOGGER.warning("Could not load fuel-split tracker state: %s", exc)
            stored = None
        if stored is not None:
            if isinstance(stored, dict):
                self._restore(stored)
            else:
                _LOGGER.warning("Ignoring malformed fuel-split tracker state")

        self._unsub_coordinator = self.coordinator.async_add_listener(
            self._handle_coordinator_update
        )
        self._initialized = True
        self._process_observation()

    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Subscribe an entity to already-processed tracker updates."""
        self._listeners.add(listener)

        def remove_listener() -> None:
            self._listeners.discard(listener)

        return remove_listener

    def _handle_coordinator_update(self) -> None:
        """Process one coordinator update, independent of entity callbacks."""
        if not self._shutdown:
            self._process_observation()

    def _process_observation(self) -> None:
        if not getattr(self.coordinator, "last_update_success", True):
            # DataUpdateCoordinator retains its previous data after a failed
            # poll. Do not treat that stale value as a fresh observation or it
            # would conceal a long data gap.
            self._notify_listeners()
            return
        data = self.coordinator.data or {}
        total_data = data.get(self.total_address)
        if not isinstance(total_data, dict):
            return
        current_total = _finite_number(total_data.get("value"))
        if current_total is None:
            _LOGGER.debug("Fuel-split source total is missing or non-numeric")
            return

        mode_data = data.get(self.mode_address)
        mode_value = mode_data.get("raw_value") if isinstance(mode_data, dict) else None
        current_mode_raw, current_group = fuel_group_for_raw_mode(mode_value)
        now = self._normalized_now()
        previous_total = self.state.last_source_total_kwh

        if previous_total is None:
            self.state.last_source_total_kwh = current_total
            self.state.last_mode_raw = current_mode_raw
            self.state.last_fuel_group = current_group
            self.state.last_observation_timestamp = now
            self.state.tracking_started_at = now
            self.state.source_total_at_start = current_total
            self._state_changed(now)
            return

        delta = current_total - previous_total
        if delta < 0:
            self.state.source_reset_count += 1
            _LOGGER.warning(
                "KWB combined heat counter reset from %s to %s; derived fuel totals "
                "remain unchanged",
                previous_total,
                current_total,
            )
        elif delta > 0:
            if self._observation_gap_is_long(now):
                self.state.unattributed_kwh += delta
            elif (
                self.state.last_fuel_group == FUEL_GROUP_PELLETS
                and current_group == FUEL_GROUP_PELLETS
            ):
                self.state.pellet_kwh += delta
            elif (
                self.state.last_fuel_group == FUEL_GROUP_LOG_WOOD
                and current_group == FUEL_GROUP_LOG_WOOD
            ):
                self.state.log_wood_kwh += delta
            else:
                self.state.unattributed_kwh += delta

        # Advance every valid observation, including zero deltas, uncertain
        # intervals, and source resets. No delta is ever reconsidered.
        self.state.last_source_total_kwh = current_total
        self.state.last_mode_raw = current_mode_raw
        self.state.last_fuel_group = current_group
        self.state.last_observation_timestamp = now
        self._state_changed(now)

    def _normalized_now(self) -> datetime:
        now = self._now()
        if now.tzinfo is None:
            return now.replace(tzinfo=timezone.utc)
        return now.astimezone(timezone.utc)

    def _observation_gap_is_long(self, now: datetime) -> bool:
        previous = self.state.last_observation_timestamp
        if previous is None:
            return True
        elapsed = (now - previous).total_seconds()
        return elapsed < 0 or elapsed > self.long_gap_seconds

    def _state_changed(self, now: datetime) -> None:
        # Baselines change on every successful poll, but writing a storage file
        # every poll would be excessive. Request a debounced Store write at
        # most once per five minutes; normal unload and HA shutdown still flush
        # the latest in-memory state.
        previous_request = self._last_persist_request_at
        since_request = (
            (now - previous_request).total_seconds()
            if previous_request is not None
            else None
        )
        if (
            since_request is None
            or since_request < 0
            or since_request >= STORAGE_REQUEST_INTERVAL_SECONDS
        ):
            self._store.async_delay_save(self._serialize, STORAGE_SAVE_DELAY_SECONDS)
            self._last_persist_request_at = now
        self._notify_listeners()

    def _notify_listeners(self) -> None:
        for listener in tuple(self._listeners):
            listener()

    def _restore(self, stored: dict[str, Any]) -> None:
        state = FuelSplitState(
            pellet_kwh=_nonnegative_number(stored.get("pellet_kwh")),
            log_wood_kwh=_nonnegative_number(stored.get("log_wood_kwh")),
            unattributed_kwh=_nonnegative_number(stored.get("unattributed_kwh")),
            last_source_total_kwh=_finite_number(
                stored.get("last_source_total_kwh")
            ),
            last_observation_timestamp=_parse_timestamp(
                stored.get("last_observation_timestamp")
            ),
            tracking_started_at=_parse_timestamp(stored.get("tracking_started_at")),
            source_total_at_start=_finite_number(stored.get("source_total_at_start")),
            source_reset_count=max(
                int(stored.get("source_reset_count", 0)), 0
            ) if str(stored.get("source_reset_count", 0)).isdigit() else 0,
        )
        raw_mode, group = fuel_group_for_raw_mode(stored.get("last_mode_raw"))
        state.last_mode_raw = raw_mode
        state.last_fuel_group = group
        if state.last_source_total_kwh is not None and state.last_source_total_kwh < 0:
            state.last_source_total_kwh = None
        if state.source_total_at_start is not None and state.source_total_at_start < 0:
            state.source_total_at_start = None
        self.state = state

    def _serialize(self) -> dict[str, Any]:
        return {
            "pellet_kwh": self.state.pellet_kwh,
            "log_wood_kwh": self.state.log_wood_kwh,
            "unattributed_kwh": self.state.unattributed_kwh,
            "last_source_total_kwh": self.state.last_source_total_kwh,
            "last_mode_raw": self.state.last_mode_raw,
            "last_fuel_group": self.state.last_fuel_group,
            "last_observation_timestamp": self._timestamp(
                self.state.last_observation_timestamp
            ),
            "tracking_started_at": self._timestamp(self.state.tracking_started_at),
            "source_total_at_start": self.state.source_total_at_start,
            "source_reset_count": self.state.source_reset_count,
        }

    @staticmethod
    def _timestamp(value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None

    def diagnostic_attributes(self) -> dict[str, Any]:
        """Return compact quality metadata for the diagnostic entity."""
        return {
            "tracking_started_at": self._timestamp(self.state.tracking_started_at),
            "source_total_at_start": self.state.source_total_at_start,
            "last_source_total_kwh": self.state.last_source_total_kwh,
            "last_mode_raw": self.state.last_mode_raw,
            "last_fuel_group": self.state.last_fuel_group,
            "source_reset_count": self.state.source_reset_count,
            "last_observation_timestamp": self._timestamp(
                self.state.last_observation_timestamp
            ),
        }

    async def async_shutdown(self) -> None:
        """Unsubscribe and flush the latest baseline during a normal unload."""
        if self._shutdown:
            return
        self._shutdown = True
        if self._unsub_coordinator is not None:
            self._unsub_coordinator()
            self._unsub_coordinator = None
        try:
            await self._store.async_save(self._serialize())
        except Exception as exc:
            _LOGGER.warning("Could not flush fuel-split tracker state: %s", exc)
        self._listeners.clear()
