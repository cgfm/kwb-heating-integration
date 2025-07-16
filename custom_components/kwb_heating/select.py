"""Select platform for KWB Heating integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KWBDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KWB Heating select platform."""
    coordinator: KWBDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # Wait for register manager initialization if needed
    if not hasattr(coordinator, '_registers') or coordinator._registers is None:
        await coordinator._initialize_register_manager()
    
    # Create select entities for read-write registers with value tables
    for register in coordinator._registers:
        if (register.get("user_level") == "readwrite" and 
            coordinator.data_converter.has_value_table(register)):
            entities.append(KWBSelect(coordinator, register))
    
    _LOGGER.info("Setting up %d KWB select entities", len(entities))
    async_add_entities(entities)


class KWBSelect(CoordinatorEntity, SelectEntity):
    """Representation of a KWB heating system select control."""

    def __init__(
        self,
        coordinator: KWBDataUpdateCoordinator,
        register: dict,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._register = register
        self._address = register["starting_address"]
        
        # Generate structured entity name and unique ID
        entity_name, unique_id = self._generate_entity_name_and_id(register, coordinator)
        self._attr_name = entity_name
        self._attr_unique_id = unique_id
        
        # Set device info
        self._attr_device_info = coordinator.device_info
        
        # Configure select properties
        self._configure_select()

    def _configure_select(self) -> None:
        """Configure select properties based on register definition."""
        # Get value table for options using data converter
        unit_value_table = self._register.get("unit_value_table", "")
        if unit_value_table in self.coordinator.data_converter.value_tables:
            value_table = self.coordinator.data_converter.value_tables[unit_value_table]
            # Options are the display values from the table
            self._attr_options = list(value_table.values())
        else:
            self._attr_options = ["Unknown"]

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if self.coordinator.data and self._address in self.coordinator.data:
            register_data = self.coordinator.data[self._address]
            
            # Use display_value if available
            if "display_value" in register_data:
                return register_data["display_value"]
            
            # Convert raw value using data converter
            raw_value = register_data.get("raw_value", 0)
            return self.coordinator.data_converter.get_display_value(self._register, raw_value)
        
        return None

    async def async_select_option(self, option: str) -> None:
        """Select new option."""
        # Find the numeric value for this option using data converter
        unit_value_table = self._register.get("unit_value_table", "")
        if unit_value_table not in self.coordinator.data_converter.value_tables:
            _LOGGER.error("Value table %s not found", unit_value_table)
            return
        
        value_table = self.coordinator.data_converter.value_tables[unit_value_table]
        
        # Find the key (numeric value) for the selected option (display value)
        numeric_value = None
        for key, display_value in value_table.items():
            if display_value == option:
                try:
                    numeric_value = int(key)
                    break
                except ValueError:
                    _LOGGER.error("Invalid numeric key %s in value table %s", key, unit_value_table)
                    continue
        
        if numeric_value is None:
            _LOGGER.error("Option %s not found in value table %s", option, unit_value_table)
            return
        
        # Write to device
        success = await self.coordinator.async_write_register(self._address, numeric_value)
        
        if not success:
            _LOGGER.error("Failed to write option %s (value %d) to register %d", 
                         option, numeric_value, self._address)
            return
        
        # Update our local data immediately
        if self.coordinator.data and self._address in self.coordinator.data:
            self.coordinator.data[self._address]["value"] = numeric_value
            self.coordinator.data[self._address]["display_value"] = option
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
        """Return icon for the select entity."""
        name_lower = self._register["name"].lower()
        
        if "mode" in name_lower or "modus" in name_lower:
            return "mdi:cog"
        elif "program" in name_lower or "programm" in name_lower:
            return "mdi:calendar-clock"
        elif "level" in name_lower or "stufe" in name_lower:
            return "mdi:format-list-numbered"
        elif "status" in name_lower:
            return "mdi:information"
        
        return "mdi:format-list-bulleted"
    
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
