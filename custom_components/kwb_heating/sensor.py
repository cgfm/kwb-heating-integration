"""Sensor platform for KWB Heating integration."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .coordinator import KWBDataUpdateCoordinator
from .entity import KWBBaseEntity
from .fuel_split import FuelSplitTracker
from .fuel_split_entity_ids import fuel_split_entity_identity
from .icon_utils import get_entity_icon
from .register_utils import find_register_by_parameter, normalize_register_address

# Logical register capability required by the computed firewood sensor.
FIREWOOD_STATUS_PARAMETER = "CF2.kesselstatus_anzeige_sh"

# Boiler status values indicating active firewood operation (boiler status display_t)
FIREWOOD_ACTIVE_VALUES = [
    36,  # Igniting
    37,  # Waiting for ignition start
    38,  # Waiting for ignition release
    39,  # Start ignition
    40,  # Igniting
    41,  # Heating
    42,  # Fire holding
]

# Translations for the Last Firewood Fire sensor
FIREWOOD_SENSOR_TRANSLATIONS = {
    "de": {
        "name": "Letztes Stückholzfeuer",
        "entity_id_suffix": "letztes_stueckholzfeuer",
        "attr_firewood_active": "stueckholz_aktiv",
        "attr_boiler_status_raw": "kesselstatus_rohwert",
        "attr_boiler_status": "kesselstatus",
    },
    "en": {
        "name": "Last Firewood Fire",
        "entity_id_suffix": "last_firewood_fire",
        "attr_firewood_active": "firewood_currently_active",
        "attr_boiler_status_raw": "boiler_status_raw",
        "attr_boiler_status": "boiler_status",
    },
}

FUEL_SPLIT_TRANSLATIONS = {
    "pellet": {
        "de": "Pellet-Energie Gesamt",
        "en": "Pellet Energy Total",
        "entity_id_suffix": "pellet_energy_total",
        "icon": "mdi:grain",
    },
    "log_wood": {
        "de": "Stückholz-Energie Gesamt",
        "en": "Log Wood Energy Total",
        "entity_id_suffix": "log_wood_energy_total",
        "icon": "mdi:pine-tree",
    },
    "unattributed": {
        "de": "Nicht zugeordnete Brennstoffenergie",
        "en": "Unattributed Fuel Energy",
        "entity_id_suffix": "fuel_energy_unattributed",
        "icon": "mdi:help-circle-outline",
    },
}

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KWB Heating sensor platform."""
    coordinator: KWBDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []

    await coordinator.ensure_initialized()

    _LOGGER.debug("Processing %d registers for sensor entities", len(coordinator._registers) if coordinator._registers else 0)

    access_level = coordinator.access_level
    level_field = "user_level" if access_level == "UserLevel" else "expert_level"

    # Sensors are only created for read-only registers at the active access level.
    # Read-write registers become number/select/switch entities instead.
    for register in coordinator._registers:
        level_value = register.get(level_field, "")
        is_readable = level_value == "read"

        _LOGGER.debug("Register %s: %s=%s, current_access=%s, readable=%s",
                      register.get("name", "Unknown"), level_field, level_value, access_level, is_readable)

        if is_readable:
            entities.append(KWBSensor(coordinator, register))

    firewood_register = find_register_by_parameter(
        coordinator.registers, FIREWOOD_STATUS_PARAMETER
    )
    firewood_address = normalize_register_address(
        firewood_register.get("starting_address") if firewood_register else None
    )
    if firewood_address is not None:
        _LOGGER.info(
            "Adding 'Last Firewood Fire' sensor from %s at address %s",
            FIREWOOD_STATUS_PARAMETER,
            firewood_address,
        )
        entities.append(KWBLastFirewoodFireSensor(coordinator, firewood_address))
    else:
        _LOGGER.debug(
            "Firewood status parameter not found, skipping 'Last Firewood Fire' sensor"
        )

    tracker = coordinator.fuel_split_tracker
    if tracker is not None:
        entities.extend(
            (
                KWBFuelSplitEnergySensor(coordinator, tracker, "pellet"),
                KWBFuelSplitEnergySensor(coordinator, tracker, "log_wood"),
                KWBFuelSplitEnergySensor(coordinator, tracker, "unattributed"),
            )
        )

    _LOGGER.info("Setting up %d KWB sensor entities", len(entities))
    async_add_entities(entities)


class KWBSensor(KWBBaseEntity, SensorEntity):
    """Representation of a KWB heating system sensor."""

    def __init__(
        self,
        coordinator: KWBDataUpdateCoordinator,
        register: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, register, "sensor")

        # Configure sensor properties based on register
        self._configure_sensor()

        # Cache static attributes that never change (issue #35)
        self._static_attrs: dict[str, Any] = self._build_static_attrs()

    def _configure_sensor(self) -> None:
        """Configure sensor properties based on register definition."""
        # Use data converter for unit and device class
        unit = self.coordinator.data_converter.get_unit(self._register)
        device_class = self.coordinator.data_converter.get_device_class(self._register)

        if unit:
            self._attr_native_unit_of_measurement = unit

        if device_class:
            self._attr_device_class = device_class

        # Set state class ONLY for truly numeric values (no value tables)
        if (self.coordinator.data_converter.is_numeric(self._register) and
            not self.coordinator.data_converter.has_value_table(self._register)):
            self._attr_state_class = SensorStateClass.MEASUREMENT

        # Set icon based on register definition
        self._attr_icon = get_entity_icon(self._register, "sensor")

        # Set entity category based on register properties
        name_lower = self._register["name"].lower()
        if any(keyword in name_lower for keyword in ["version", "revision", "software"]):
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        elif any(keyword in name_lower for keyword in ["alarm", "error", "störung"]):
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data and self._address in self.coordinator.data:
            register_data = self.coordinator.data[self._address]

            # Use display value if available (from value table)
            if "display_value" in register_data:
                return register_data["display_value"]

            # Otherwise use converted value
            return register_data.get("value")

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data or self._address not in self.coordinator.data:
            return {}

        register_data = self.coordinator.data[self._address]

        # Merge cached static attributes with dynamic raw_value (issue #35)
        attributes = {**self._static_attrs, "raw_value": register_data.get("raw_value")}
        return attributes

    # available property inherited from KWBBaseEntity

class KWBLastFirewoodFireSensor(CoordinatorEntity, RestoreEntity, SensorEntity):
    """Sensor that tracks when the last firewood fire was active."""

    def __init__(
        self, coordinator: KWBDataUpdateCoordinator, firewood_status_address: int
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._firewood_status_address = firewood_status_address

        # Store the last timestamp when firewood was active
        self._last_firewood_time: datetime | None = None
        self._was_firewood_active: bool = False

        # Get language from register manager (default to "de" if not available)
        language = "de"
        if hasattr(coordinator, 'register_manager') and coordinator.register_manager:
            language = getattr(coordinator.register_manager, '_language', 'de') or 'de'

        # Get translations for the current language (fallback to English)
        translations = FIREWOOD_SENSOR_TRANSLATIONS.get(
            language, FIREWOOD_SENSOR_TRANSLATIONS["en"]
        )

        # Set entity attributes — use has_entity_name so HA prefixes the device name
        self._attr_has_entity_name = True
        self._attr_name = translations['name']

        # Generate unique ID (always use English for consistency)
        device_identifier = f"{coordinator.host}_{coordinator.slave_id}"
        device_prefix_id = coordinator.sanitize_for_entity_id(coordinator.device_name_prefix)
        self._attr_unique_id = f"kwb_heating_{device_identifier}_{device_prefix_id}_last_firewood_fire"

        # Set explicit entity_id - always use English for language-independent IDs
        english_suffix = FIREWOOD_SENSOR_TRANSLATIONS["en"]["entity_id_suffix"]
        self.entity_id = f"sensor.{device_prefix_id}_{english_suffix}"

        # Set device info
        self._attr_device_info = coordinator.device_info

        # Sensor configuration
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = "mdi:fire-alert"

        # Store language for attribute translations
        self._language = language

    async def async_added_to_hass(self) -> None:
        """Restore previous state when added to hass."""
        await super().async_added_to_hass()

        # Restore previous state if available
        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state not in (None, "unknown", "unavailable"):
                try:
                    restored = datetime.fromisoformat(last_state.state)
                    if restored.tzinfo is None:
                        restored = restored.replace(tzinfo=timezone.utc)
                    self._last_firewood_time = restored
                    _LOGGER.debug(
                        "Restored last firewood fire timestamp: %s",
                        self._last_firewood_time
                    )
                except (ValueError, TypeError) as exc:
                    _LOGGER.warning("Could not restore last firewood state: %s", exc)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator.

        Only writes HA state when the firewood status actually changes,
        avoiding unnecessary DB writes every poll cycle (issue #23).
        """
        state_changed = False

        if (
            self.coordinator.data
            and self._firewood_status_address in self.coordinator.data
        ):
            register_data = self.coordinator.data[self._firewood_status_address]
            raw_value = register_data.get("raw_value")

            if raw_value is not None:
                is_firewood_active = raw_value in FIREWOOD_ACTIVE_VALUES

                # Update timestamp when firewood becomes active or stays active
                if is_firewood_active:
                    self._last_firewood_time = datetime.now(tz=timezone.utc)
                    state_changed = True
                    if not self._was_firewood_active:
                        _LOGGER.info("Firewood fire started at %s", self._last_firewood_time)

                if is_firewood_active != self._was_firewood_active:
                    state_changed = True

                self._was_firewood_active = is_firewood_active

        if state_changed:
            self.async_write_ha_state()

    @property
    def native_value(self) -> datetime | None:
        """Return the last time firewood was active."""
        return self._last_firewood_time

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attributes = {}

        # Get translations for attribute names
        translations = FIREWOOD_SENSOR_TRANSLATIONS.get(
            self._language, FIREWOOD_SENSOR_TRANSLATIONS["en"]
        )

        if (
            self.coordinator.data
            and self._firewood_status_address in self.coordinator.data
        ):
            register_data = self.coordinator.data[self._firewood_status_address]
            raw_value = register_data.get("raw_value")

            if raw_value is not None:
                attributes[translations["attr_firewood_active"]] = raw_value in FIREWOOD_ACTIVE_VALUES
                attributes[translations["attr_boiler_status_raw"]] = raw_value

                # Add display value if available
                if "display_value" in register_data:
                    attributes[translations["attr_boiler_status"]] = register_data["display_value"]

        return attributes

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
        )


class KWBFuelSplitEnergySensor(SensorEntity):
    """Expose one value calculated by the config-entry fuel-split tracker."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KWBDataUpdateCoordinator,
        tracker: FuelSplitTracker,
        kind: str,
    ) -> None:
        self.coordinator = coordinator
        self.tracker = tracker
        self.kind = kind

        language = "de"
        if hasattr(coordinator, "register_manager") and coordinator.register_manager:
            language = getattr(coordinator.register_manager, "_language", "de") or "de"
        translations = FUEL_SPLIT_TRANSLATIONS[kind]
        self._attr_name = translations.get(language, translations["en"])
        self._attr_icon = translations["icon"]

        unique_id, entity_id = fuel_split_entity_identity(coordinator, kind)
        self._attr_unique_id = unique_id
        self.entity_id = entity_id
        self._attr_device_info = coordinator.device_info

        if kind == "unattributed":
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
            self._attr_entity_registry_enabled_default = False

    async def async_added_to_hass(self) -> None:
        """Listen only for already-accounted tracker changes."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.tracker.async_add_listener(self._handle_tracker_update)
        )

    @callback
    def _handle_tracker_update(self) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> float:
        """Return a monotonic derived total."""
        if self.kind == "pellet":
            value = self.tracker.pellet_kwh
        elif self.kind == "log_wood":
            value = self.tracker.log_wood_kwh
        else:
            value = self.tracker.unattributed_kwh
        return round(value, 6)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose split-quality metadata only on the diagnostic entity."""
        if self.kind != "unattributed":
            return None
        return self.tracker.diagnostic_attributes()

    @property
    def available(self) -> bool:
        """Retain stored totals but flag unavailable source observations."""
        return (
            self.coordinator.last_update_success
            and self.tracker.has_source_baseline
        )

