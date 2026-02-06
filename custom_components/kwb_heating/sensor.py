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

# Device types that support firewood (Stückholz)
FIREWOOD_DEVICE_TYPES = [
    "KWB CF 1",
    "KWB CF 1.5",
    "KWB CF 2",
    "KWB Combifire",
    "KWB Multifire",
]

# Modbus address for firewood boiler status (Status Stückholz)
FIREWOOD_STATUS_ADDRESS = 8212

# Boiler status values indicating active firewood operation (ksm_kesselstatus_anzeige_t)
FIREWOOD_ACTIVE_VALUES = [
    36,  # Anheizen
    37,  # Warten Zündanf.
    38,  # Warten Zündfreig.
    39,  # Start Zündung
    40,  # Zünden
    41,  # Heizen
    42,  # Feuerhaltung
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

_LOGGER = logging.getLogger(__name__)


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
    
    # Add computed sensor for firewood devices: "Last Firewood Fire"
    device_type = coordinator.config.get("device_type", "")
    if device_type in FIREWOOD_DEVICE_TYPES:
        # Check if the firewood status register is available
        has_firewood_status = any(
            reg.get("starting_address") == FIREWOOD_STATUS_ADDRESS
            for reg in coordinator._registers
        )
        if has_firewood_status:
            _LOGGER.info("Adding 'Last Firewood Fire' sensor for device type: %s", device_type)
            entities.append(KWBLastFirewoodFireSensor(coordinator))
        else:
            _LOGGER.debug("Firewood status register not found, skipping 'Last Firewood Fire' sensor")

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

    def __init__(self, coordinator: KWBDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

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

        # Set explicit entity_id using language-specific suffix
        self._attr_entity_id = f"sensor.{device_prefix_id}_{translations['entity_id_suffix']}"

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
        if self.coordinator.data and FIREWOOD_STATUS_ADDRESS in self.coordinator.data:
            register_data = self.coordinator.data[FIREWOOD_STATUS_ADDRESS]
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

        if self.coordinator.data and FIREWOOD_STATUS_ADDRESS in self.coordinator.data:
            register_data = self.coordinator.data[FIREWOOD_STATUS_ADDRESS]
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

