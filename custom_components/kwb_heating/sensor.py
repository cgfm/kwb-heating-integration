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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .coordinator import KWBDataUpdateCoordinator
from .entity import KWBBaseEntity
from .icon_utils import get_entity_icon

# KWB parameter path for firewood boiler status (logwood status). Looked up
# by parameter rather than a hardcoded address, since the JSON config is the
# source of truth for register addresses (they're also not guaranteed to
# match across versions/devices, even though they happen to today).
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

# CF2.betriebsmodus (operating mode) - the only signal that distinguishes
# which fuel is currently burning on a dual-fuel Combifire-family boiler.
FUEL_MODE_PARAMETER = "CF2.betriebsmodus"
# cf2_betriebsmodus_t raw values: 0=Kein, 1=Stückholz, 2=Pellets,
# 3=Stückholz (PM Nachlauf), 4=Relaistest. Off/relay-test periods are
# intentionally left unattributed to either fuel.
PELLET_MODE_VALUES = {2}
LOG_WOOD_MODE_VALUES = {1, 3}

# KSM.waermemenge_gesamt_kwh - the boiler's single combined lifetime heat
# output counter. KWB does not expose separate per-fuel energy registers, so
# this is split after the fact using FUEL_MODE_PARAMETER above.
TOTAL_HEAT_PARAMETER = "KSM.waermemenge_gesamt_kwh"

FUEL_SPLIT_TRANSLATIONS = {
    "pellets": {
        "de": {"name": "Pellet-Energie Gesamt", "entity_id_suffix": "pellet_energie_gesamt"},
        "en": {"name": "Pellet Energy Total", "entity_id_suffix": "pellet_energy_total"},
    },
    "log_wood": {
        "de": {"name": "Stückholz-Energie Gesamt", "entity_id_suffix": "stueckholz_energie_gesamt"},
        "en": {"name": "Log Wood Energy Total", "entity_id_suffix": "log_wood_energy_total"},
    },
}

_LOGGER = logging.getLogger(__name__)


def _find_register_address(registers: list[dict], parameter: str) -> int | None:
    """Look up a register's Modbus address by its stable KWB parameter path.

    Register addresses live in the JSON config, not in Python code - looking
    them up by parameter (rather than hardcoding an address) keeps computed
    sensors correct if a device/version ever places a register elsewhere,
    and naturally handles a parameter being absent on older firmware.
    """
    for register in registers:
        if register.get("parameter") == parameter:
            return register.get("starting_address")
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KWB Heating sensor platform."""
    coordinator: KWBDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # Wait for register manager initialization if needed
    if not hasattr(coordinator, '_registers') or coordinator._registers is None:
        await coordinator._initialize_register_manager()
    
    _LOGGER.debug("Processing %d registers for sensor entities", len(coordinator._registers) if coordinator._registers else 0)
    
    # Create sensor entities for all read-only registers and RW registers that should show values
    for register in coordinator._registers:
        # Sensors are created for:
        # 1. Read-only registers (access="R")
        # 2. Read-write registers that have value tables (display values)
        # 3. Read-write registers that are diagnostic or informational
        # Get access level and determine if this register should create a sensor
        user_level = register.get("user_level", "")
        expert_level = register.get("expert_level", "")
        access_level = coordinator.access_level  # UserLevel or ExpertLevel
        
        # Check if this register is accessible at the current access level
        is_readable = False
        if access_level == "UserLevel" and user_level in ["read", "write"]:
            is_readable = True
        elif access_level == "ExpertLevel" and expert_level in ["read", "write"]:
            is_readable = True
        
        _LOGGER.debug("Register %s: user_level=%s, expert_level=%s, current_access=%s, readable=%s", 
                      register.get("name", "Unknown"), user_level, expert_level, access_level, is_readable)
        
        # Create sensor for readable registers
        if is_readable:
            _LOGGER.debug("Creating sensor for register: %s", register.get("name", "Unknown"))
            entities.append(KWBSensor(coordinator, register))
    
    # Add computed sensor for firewood devices: "Last Firewood Fire".
    # Gated purely on whether the register actually exists for this device -
    # no hardcoded device-type list, since that would just be a second,
    # independently-maintained copy of the same information already in the
    # JSON config (and one that had already drifted: it used to list
    # Multifire, which has never actually had this register).
    firewood_status_address = _find_register_address(
        coordinator._registers, FIREWOOD_STATUS_PARAMETER
    )
    if firewood_status_address is not None:
        _LOGGER.info("Adding 'Last Firewood Fire' sensor (register found at address %d)", firewood_status_address)
        entities.append(KWBLastFirewoodFireSensor(coordinator, firewood_status_address))
    else:
        _LOGGER.debug("Firewood status register not found, skipping 'Last Firewood Fire' sensor")

    # Add computed sensors for dual-fuel devices: pellet/log-wood energy
    # split. Same reasoning - gated on register presence, not device type.
    mode_address = _find_register_address(coordinator._registers, FUEL_MODE_PARAMETER)
    total_heat_address = _find_register_address(coordinator._registers, TOTAL_HEAT_PARAMETER)
    if mode_address is not None and total_heat_address is not None:
        _LOGGER.info("Adding pellet/log-wood energy split sensors (registers found)")
        entities.append(KWBFuelSplitEnergySensor(
            coordinator, "pellets", PELLET_MODE_VALUES, mode_address, total_heat_address
        ))
        entities.append(KWBFuelSplitEnergySensor(
            coordinator, "log_wood", LOG_WOOD_MODE_VALUES, mode_address, total_heat_address
        ))
    else:
        _LOGGER.debug(
            "Operating mode or total heat register not found, skipping fuel energy split sensors"
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
        
        attributes = {
            "register_address": self._address,
            "register_type": self._register.get("type"),
            "data_type": self._register.get("data_type"),
            "raw_value": register_data.get("raw_value"),
        }

        # Keep only snake_case attributes for consistency
        
        # Add register description if available
        if self._register.get("description"):
            attributes["description"] = self._register["description"]
        
        # Add access level info
        if self._register.get("access_level"):
            attributes["access_level"] = self._register["access_level"]
        
        # Add min/max values if available
        if self._register.get("min"):
            attributes["min_value"] = self._register["min"]
        if self._register.get("max"):
            attributes["max_value"] = self._register["max"]
        
        return attributes

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._address in self.coordinator.data
        )


class KWBLastFirewoodFireSensor(CoordinatorEntity, RestoreEntity, SensorEntity):
    """Sensor that tracks when the last firewood fire was active."""

    def __init__(self, coordinator: KWBDataUpdateCoordinator, status_address: int) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._status_address = status_address

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

        # Set entity attributes
        device_prefix = coordinator.device_name_prefix
        self._attr_name = f"{device_prefix} {translations['name']}"

        # Generate unique ID (always use English for consistency)
        device_identifier = f"{coordinator.host}_{coordinator.slave_id}"
        device_prefix_id = coordinator.sanitize_for_entity_id(device_prefix)
        self._attr_unique_id = f"kwb_heating_{device_identifier}_{device_prefix_id}_last_firewood_fire"

        # Set explicit entity_id - always use English for language-independent IDs
        english_suffix = FIREWOOD_SENSOR_TRANSLATIONS["en"]["entity_id_suffix"]
        self._attr_entity_id = f"sensor.{device_prefix_id}_{english_suffix}"

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
        """Handle updated data from the coordinator."""
        if self.coordinator.data and self._status_address in self.coordinator.data:
            register_data = self.coordinator.data[self._status_address]
            raw_value = register_data.get("raw_value")

            if raw_value is not None:
                is_firewood_active = raw_value in FIREWOOD_ACTIVE_VALUES

                # Update timestamp when firewood becomes active or stays active
                if is_firewood_active:
                    self._last_firewood_time = datetime.now(tz=timezone.utc)
                    if not self._was_firewood_active:
                        _LOGGER.info("Firewood fire started at %s", self._last_firewood_time)

                self._was_firewood_active = is_firewood_active

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

        if self.coordinator.data and self._status_address in self.coordinator.data:
            register_data = self.coordinator.data[self._status_address]
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


class KWBFuelSplitEnergySensor(CoordinatorEntity, RestoreEntity, SensorEntity):
    """Cumulative energy attributed to one fuel on a dual-fuel boiler.

    KWB only exposes a single combined lifetime heat-output counter
    (KSM.waermemenge_gesamt_kwh) on Combifire-family boilers that can burn
    both log wood and pellets - there is no separate per-fuel energy
    register. This sensor splits it after the fact: each time the combined
    counter increases, the delta is attributed to whichever fuel
    CF2.betriebsmodus reports as active at that moment. Off/relay-test
    periods are left unattributed to either fuel.

    This produces a lifetime cumulative total per fuel (state_class
    total_increasing), suitable for wrapping in a Home Assistant Utility
    Meter helper (daily cycle) to get daily energy per fuel.
    """

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "kWh"

    def __init__(
        self,
        coordinator: KWBDataUpdateCoordinator,
        fuel: str,
        mode_values: set[int],
        mode_address: int,
        total_heat_address: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._fuel = fuel
        self._mode_values = mode_values
        self._mode_address = mode_address
        self._total_heat_address = total_heat_address
        self._accumulated_kwh: float = 0.0
        self._last_total_heat: float | None = None

        # Get language from register manager (default to "de" if not available)
        language = "de"
        if hasattr(coordinator, 'register_manager') and coordinator.register_manager:
            language = getattr(coordinator.register_manager, '_language', 'de') or 'de'

        translations = FUEL_SPLIT_TRANSLATIONS[fuel].get(
            language, FUEL_SPLIT_TRANSLATIONS[fuel]["en"]
        )

        device_prefix = coordinator.device_name_prefix
        self._attr_name = f"{device_prefix} {translations['name']}"

        # Generate unique ID and entity_id (always English, for consistency)
        device_identifier = f"{coordinator.host}_{coordinator.slave_id}"
        device_prefix_id = coordinator.sanitize_for_entity_id(device_prefix)
        english_suffix = FUEL_SPLIT_TRANSLATIONS[fuel]["en"]["entity_id_suffix"]
        self._attr_unique_id = f"kwb_heating_{device_identifier}_{device_prefix_id}_{english_suffix}"
        self._attr_entity_id = f"sensor.{device_prefix_id}_{english_suffix}"

        self._attr_device_info = coordinator.device_info
        self._attr_icon = "mdi:pine-tree" if fuel == "log_wood" else "mdi:grain"

    async def async_added_to_hass(self) -> None:
        """Restore previous state when added to hass."""
        await super().async_added_to_hass()

        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state not in (None, "unknown", "unavailable"):
                try:
                    self._accumulated_kwh = float(last_state.state)
                except (ValueError, TypeError) as exc:
                    _LOGGER.warning("Could not restore %s energy total: %s", self._fuel, exc)

            last_total_heat = last_state.attributes.get("source_total_heat_kwh")
            if last_total_heat is not None:
                try:
                    self._last_total_heat = float(last_total_heat)
                except (ValueError, TypeError):
                    pass

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data
            and self._total_heat_address in self.coordinator.data
            and self._mode_address in self.coordinator.data
        ):
            current_total = self.coordinator.data[self._total_heat_address].get("value")
            current_mode = self.coordinator.data[self._mode_address].get("raw_value")

            if current_total is not None:
                if self._last_total_heat is not None:
                    delta = current_total - self._last_total_heat
                    # A negative delta means the source counter was reset
                    # (e.g. by a technician) - treat as "nothing to
                    # attribute yet" rather than corrupting our own total.
                    if delta > 0 and current_mode in self._mode_values:
                        self._accumulated_kwh += delta
                self._last_total_heat = current_total

        self.async_write_ha_state()

    @property
    def native_value(self) -> float:
        """Return the accumulated energy for this fuel."""
        return round(self._accumulated_kwh, 3)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attributes: dict[str, Any] = {"fuel": self._fuel}
        if self._last_total_heat is not None:
            attributes["source_total_heat_kwh"] = self._last_total_heat
        return attributes

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
        )

