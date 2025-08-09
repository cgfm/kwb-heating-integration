"""Number platform for KWB Heating integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KWBDataUpdateCoordinator
from .icon_utils import get_entity_icon

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KWB Heating number platform."""
    coordinator: KWBDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # Wait for register manager initialization if needed
    if not hasattr(coordinator, '_registers') or coordinator._registers is None:
        await coordinator._initialize_register_manager()
    
    # Create number entities for read-write registers with numeric values (no value table)
    for register in coordinator._registers:
        if (register.get("user_level") == "readwrite" and 
            coordinator.data_converter.is_numeric(register) and
            not coordinator.data_converter.has_value_table(register)):
            entities.append(KWBNumber(coordinator, register))
    
    _LOGGER.info("Setting up %d KWB number entities", len(entities))
    async_add_entities(entities)


class KWBNumber(CoordinatorEntity, NumberEntity):
    """Representation of a KWB heating system number control."""

    def __init__(
        self,
        coordinator: KWBDataUpdateCoordinator,
        register: dict,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._register = register
        self._address = register["starting_address"]
        
        # Generate structured entity name and unique ID
        entity_name, unique_id = self._generate_entity_name_and_id(register, coordinator)
        self._attr_name = entity_name
        self._attr_unique_id = unique_id
        
        # Set explicit entity_id to ensure device name prefix is included
        device_prefix = coordinator.sanitize_for_entity_id(coordinator.device_name_prefix)
        register_name = coordinator.sanitize_for_entity_id(register["name"])
        self._attr_entity_id = f"number.{device_prefix}_{register_name}"
        
        # Set device info
        self._attr_device_info = coordinator.device_info
        
        # Set icon based on register name
        self._attr_icon = get_entity_icon(self._register["name"], "number")
        
        # Configure number properties
        self._configure_number()

    def _configure_number(self) -> None:
        """Configure number properties based on register definition."""
        # Use data converter for unit
        unit = self.coordinator.data_converter.get_unit(self._register)
        if unit:
            self._attr_native_unit_of_measurement = unit
        
        # Set min/max values from register or use data converter defaults
        min_val = self._register.get("min")
        max_val = self._register.get("max")
        
        if min_val and str(min_val).replace("-", "").replace(".", "").isdigit():
            self._attr_native_min_value = float(min_val)
        else:
            # Get default from data converter based on data type
            self._attr_native_min_value = self.coordinator.data_converter.get_min_value(self._register)
        
        if max_val and str(max_val).replace(".", "").isdigit():
            self._attr_native_max_value = float(max_val)
        else:
            # Get default from data converter based on data type
            self._attr_native_max_value = self.coordinator.data_converter.get_max_value(self._register)
        
        # Set step based on scaling
        self._attr_native_step = self.coordinator.data_converter.get_step_value(self._register)

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.coordinator.data and self._address in self.coordinator.data:
            register_data = self.coordinator.data[self._address]
            value = register_data.get("value")
            if value is not None:
                return float(value)
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        # Use data converter to convert Home Assistant value back to Modbus value
        modbus_value = self.coordinator.data_converter.convert_to_modbus_value(self._register, value)
        
        # Write to device
        success = await self.coordinator.async_write_register(self._address, modbus_value)
        
        if not success:
            _LOGGER.error("Failed to write value %s (modbus: %s) to register %d", 
                         value, modbus_value, self._address)
            return
        
        # Update our local data immediately with the converted HA value
        if self.coordinator.data and self._address in self.coordinator.data:
            self.coordinator.data[self._address]["value"] = value
            self.async_write_ha_state()

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
        """Return icon for the number entity."""
        name_lower = self._register["name"].lower()
        
        if "temperature" in name_lower or "temp" in name_lower:
            return "mdi:thermometer"
        elif "pressure" in name_lower:
            return "mdi:gauge"
        elif "speed" in name_lower or "drehzahl" in name_lower:
            return "mdi:speedometer"
        elif "power" in name_lower or "leistung" in name_lower:
            return "mdi:flash"
        elif "setpoint" in name_lower or "sollwert" in name_lower:
            return "mdi:target"
        
        return "mdi:numeric"
    
    def _generate_entity_name_and_id(self, register: dict, coordinator) -> tuple[str, str]:
        """Generate proper entity name and unique ID."""
        # Get base name from register
        base_name = register["name"]
        
        # Add device name prefix to entity name
        device_prefix = coordinator.device_name_prefix
        entity_name = f"{device_prefix} {base_name}"
        
        # Use coordinator's centralized unique ID generation
        unique_id = coordinator.generate_entity_unique_id(register)
        
        return entity_name, unique_id
