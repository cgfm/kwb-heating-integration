"""Switch platform for KWB Heating integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up KWB Heating switch platform."""
    coordinator: KWBDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # Wait for register manager initialization if needed
    if not hasattr(coordinator, '_registers') or coordinator._registers is None:
        await coordinator._initialize_register_manager()
    
    # Create switch entities for read-write registers with boolean values
    for register in coordinator._registers:
        if (register.get("user_level") == "readwrite" and 
            coordinator.data_converter.has_value_table(register) and
            _is_boolean_value_table(register, coordinator.data_converter)):
            entities.append(KWBSwitch(coordinator, register))
    
    _LOGGER.info("Setting up %d KWB switch entities", len(entities))
    async_add_entities(entities)


def _is_boolean_value_table(register: dict, data_converter) -> bool:
    """Check if value table represents boolean values (on/off, enabled/disabled)."""
    unit_value_table = register.get("unit_value_table", "")
    if not unit_value_table or unit_value_table not in data_converter.value_tables:
        return False
    
    value_table = data_converter.value_tables[unit_value_table]
    if not isinstance(value_table, dict):
        return False
    
    # Check if it's a simple boolean mapping (0/1, true/false, etc.)
    values = list(value_table.keys())
    if len(values) == 2:
        # Common boolean patterns
        boolean_patterns = [
            ["0", "1"],
            ["false", "true"], 
            ["off", "on"],
            ["disabled", "enabled"],
            ["aus", "ein"],  # German
        ]
        
        values_lower = [str(v).lower() for v in sorted(values)]
        return any(sorted(pattern) == values_lower for pattern in boolean_patterns)
    
    return False


class KWBSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a KWB heating system switch control."""

    def __init__(
        self,
        coordinator: KWBDataUpdateCoordinator,
        register: dict,
    ) -> None:
        """Initialize the switch entity."""
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
        self._attr_entity_id = f"switch.{device_prefix}_{register_name}"
        
        # Set device info
        self._attr_device_info = coordinator.device_info
        
        # Set icon based on register definition
        self._attr_icon = get_entity_icon(self._register, "switch")
        
        # Determine on/off values from value table using data converter
        unit_value_table = self._register.get("unit_value_table", "")
        
        self._on_value = None
        self._off_value = None
        
        if unit_value_table in self.coordinator.data_converter.value_tables:
            value_table = self.coordinator.data_converter.value_tables[unit_value_table]
            
            # Find which value represents "on" state
            for value, description in value_table.items():
                desc_lower = str(description).lower()
                if any(keyword in desc_lower for keyword in ["on", "ein", "enabled", "true", "1"]):
                    try:
                        self._on_value = int(value)
                    except ValueError:
                        self._on_value = value
                elif any(keyword in desc_lower for keyword in ["off", "aus", "disabled", "false", "0"]):
                    try:
                        self._off_value = int(value)
                    except ValueError:
                        self._off_value = value
                    try:
                        self._off_value = int(value)
                    except ValueError:
                        self._off_value = value
            
            # Fallback: use 0 as off, 1 as on for simple boolean tables
            if self._on_value is None or self._off_value is None:
                keys = list(value_table.keys())
                if len(keys) == 2:
                    try:
                        sorted_keys = sorted([int(k) for k in keys])
                        self._off_value = sorted_keys[0]
                        self._on_value = sorted_keys[1]
                    except ValueError:
                        # Non-numeric keys
                        sorted_keys = sorted(keys)
                        self._off_value = sorted_keys[0]
                        self._on_value = sorted_keys[1]

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        if self.coordinator.data and self._address in self.coordinator.data:
            register_data = self.coordinator.data[self._address]
            # Try different value keys
            raw_value = register_data.get("raw_value")
            if raw_value is None:
                raw_value = register_data.get("value")
            if raw_value is not None:
                return raw_value == self._on_value
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        if self._on_value is not None:
            success = await self.coordinator.async_write_register(self._address, self._on_value)
            if success:
                # Update our local data immediately
                if self.coordinator.data and self._address in self.coordinator.data:
                    self.coordinator.data[self._address]["value"] = self._on_value
                    self.coordinator.data[self._address]["raw_value"] = self._on_value
                    # Update display value
                    display_value = self.coordinator.data_converter.get_display_value(self._register, self._on_value)
                    if display_value:
                        self.coordinator.data[self._address]["display_value"] = display_value
                    self.async_write_ha_state()
            else:
                _LOGGER.error("Failed to turn on switch %s", self.name)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        if self._off_value is not None:
            success = await self.coordinator.async_write_register(self._address, self._off_value)
            if success:
                # Update our local data immediately
                if self.coordinator.data and self._address in self.coordinator.data:
                    self.coordinator.data[self._address]["value"] = self._off_value
                    self.coordinator.data[self._address]["raw_value"] = self._off_value
                    # Update display value
                    display_value = self.coordinator.data_converter.get_display_value(self._register, self._off_value)
                    if display_value:
                        self.coordinator.data[self._address]["display_value"] = display_value
                    self.async_write_ha_state()
            else:
                _LOGGER.error("Failed to turn off switch %s", self.name)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attributes = {
            "register_address": self._address,
            "data_type": self._register.get("type"),
            "access": self._register.get("access"),
        }
        
        # Add current raw value
        if self.coordinator.data is not None and self._address in self.coordinator.data:
            reg_data = self.coordinator.data[self._address]
            raw_val = reg_data.get("raw_value")
            if raw_val is not None:
                attributes["raw_value"] = raw_val
                # Add value description if available via data converter
                disp = self.coordinator.data_converter.get_display_value(self._register, raw_val)
                if disp is not None:
                    attributes["value_description"] = disp
        
        return attributes

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
