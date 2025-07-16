"""Sensor platform for KWB Heating integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfPressure,
    UnitOfPower,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KWBDataUpdateCoordinator

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
    
    _LOGGER.info("Setting up %d KWB sensor entities", len(entities))
    async_add_entities(entities)


class KWBSensor(CoordinatorEntity, SensorEntity):
    """Representation of a KWB heating system sensor."""

    def __init__(
        self,
        coordinator: KWBDataUpdateCoordinator,
        register: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._register = register
        self._address = register["starting_address"]
        
        # Generate proper entity name and unique ID based on index and equipment category
        self._attr_name, self._attr_unique_id = self._generate_entity_name_and_id(register, coordinator)
        
        # Set device info
        self._attr_device_info = coordinator.device_info
        
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

    @property
    def icon(self) -> str | None:
        """Return icon for the sensor."""
        # Provide icons based on sensor name/type
        name_lower = self._register["name"].lower()
        
        if "temperature" in name_lower or "temp" in name_lower:
            return "mdi:thermometer"
        elif "pressure" in name_lower:
            return "mdi:gauge"
        elif "power" in name_lower or "leistung" in name_lower:
            return "mdi:flash"
        elif "pump" in name_lower or "pumpe" in name_lower:
            return "mdi:pump"
        elif "fan" in name_lower or "gebläse" in name_lower:
            return "mdi:fan"
        elif "valve" in name_lower or "ventil" in name_lower:
            return "mdi:valve"
        elif "alarm" in name_lower or "error" in name_lower:
            return "mdi:alert"
        elif "version" in name_lower or "software" in name_lower:
            return "mdi:information"
        elif "status" in name_lower:
            return "mdi:checkbox-marked-circle"
        
        return None

    def _generate_entity_name_and_id(self, register: dict, coordinator) -> tuple[str, str]:
        """Generate proper entity name and unique ID."""
        # Use the name as-is from register (already processed by async_modular_register_manager)
        entity_name = register["name"]
        address = register["starting_address"]
        
        # Create unique entity ID (lowercase, underscore-separated)
        device_id = next(iter(coordinator.device_info['identifiers']))[1]
        
        # Sanitize for entity ID - remove special characters and normalize
        def sanitize_for_id(text: str) -> str:
            return (text.lower()
                   .replace(" ", "_")
                   .replace(".", "_")
                   .replace("(", "")
                   .replace(")", "")
                   .replace("/", "_")
                   .replace("-", "_")
                   .replace(":", "_")
                   .replace("ä", "ae")
                   .replace("ö", "oe") 
                   .replace("ü", "ue")
                   .replace("ß", "ss"))
        
        base_id = sanitize_for_id(entity_name)
        unique_id = f"kwb_heating_{device_id}_{base_id}_{address}"
        
        return entity_name, unique_id

