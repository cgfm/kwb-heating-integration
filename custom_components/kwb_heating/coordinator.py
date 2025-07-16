"""Data update coordinator for KWB Heating integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_SLAVE_ID,
    CONF_ACCESS_LEVEL,
    CONF_UPDATE_INTERVAL,
    CONF_DEVICE_TYPE,
    CONF_HEATING_CIRCUITS,
    CONF_BUFFER_STORAGE,
    CONF_DHW_STORAGE,
    CONF_SECONDARY_HEAT_SOURCES,
    CONF_CIRCULATION,
    CONF_SOLAR,
    CONF_BOILER_SEQUENCE,
    CONF_HEAT_METERS,
    DEFAULT_UPDATE_INTERVAL,
)
from .data_conversion import KWBDataConverter
from .modbus_client import KWBModbusClient
from .async_modular_register_manager import AsyncModularRegisterManager

_LOGGER = logging.getLogger(__name__)


class KWBDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the KWB heating system."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.host = entry.data[CONF_HOST]
        self.port = entry.data[CONF_PORT]
        self.slave_id = entry.data[CONF_SLAVE_ID]
        self.access_level = entry.data[CONF_ACCESS_LEVEL]
        
        # Merge data and options for complete configuration
        self.config = {**entry.data, **entry.options}
        
        update_interval = self.config.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )
        
        # Initialize modbus client
        self.modbus_client = KWBModbusClient(
            host=self.host,
            port=self.port,
            slave_id=self.slave_id
        )

    async def _initialize_register_manager(self) -> None:
        """Initialize or reinitialize the register manager asynchronously."""
        # Initialize async register manager
        self.register_manager = AsyncModularRegisterManager()
        
        # Initialize data converter with value tables (after async init)
        await self.register_manager.initialize()
        value_tables = self.register_manager.value_tables
        self.data_converter = KWBDataConverter(value_tables)
        
        # Get access level from config (options take precedence)
        access_level = self.config.get(CONF_ACCESS_LEVEL, self.access_level)
        
        # Get device type from config
        device_type = self.config.get(CONF_DEVICE_TYPE)
        
        # Build equipment configuration - use counts directly, not boolean conversion
        equipment_config = {
            "heating_circuits": self.config.get(CONF_HEATING_CIRCUITS, 0),
            "buffer_storage": self.config.get(CONF_BUFFER_STORAGE, 0),
            "dhw_storage": self.config.get(CONF_DHW_STORAGE, 0),
            "secondary_heat_sources": self.config.get(CONF_SECONDARY_HEAT_SOURCES, 0),
            "circulation": self.config.get(CONF_CIRCULATION, 0),
            "solar": self.config.get(CONF_SOLAR, 0),
            "boiler_sequence": self.config.get(CONF_BOILER_SEQUENCE, 0),
            "heat_meters": self.config.get(CONF_HEAT_METERS, 0),
        }
        
        # Store equipment counts for register filtering
        self.equipment_counts = equipment_config.copy()
        
        # Get registers for the current access level, equipment, and device type
        self._registers = await self.register_manager.get_all_registers(
            access_level, 
            equipment_config,
            device_type
        )
        
        _LOGGER.info("Set up %d registers for access level %s, device type %s with equipment: %s", 
                    len(self._registers), access_level, device_type, equipment_config)

    async def async_update_config(self, data: dict, options: dict) -> None:
        """Update configuration and reinitialize if needed."""
        _LOGGER.info("Updating coordinator configuration")
        
        # Update config
        old_config = self.config.copy()
        self.config = {**data, **options}
        
        # Check if access level or equipment changed
        access_level_changed = (
            old_config.get(CONF_ACCESS_LEVEL) != self.config.get(CONF_ACCESS_LEVEL)
        )
        
        equipment_changed = any(
            old_config.get(key) != self.config.get(key)
            for key in [CONF_HEATING_CIRCUITS, CONF_BUFFER_STORAGE, CONF_DHW_STORAGE, 
                       CONF_SECONDARY_HEAT_SOURCES, CONF_CIRCULATION, CONF_SOLAR,
                       CONF_BOILER_SEQUENCE, CONF_HEAT_METERS]
        )
        
        # Update interval changed
        update_interval_changed = (
            old_config.get(CONF_UPDATE_INTERVAL) != self.config.get(CONF_UPDATE_INTERVAL)
        )
        
        if access_level_changed or equipment_changed:
            _LOGGER.info("Equipment or access level changed, reinitializing registers")
            await self._initialize_register_manager()
        
        if update_interval_changed:
            new_interval = self.config.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
            _LOGGER.info("Update interval changed to %d seconds", new_interval)
            self.update_interval = timedelta(seconds=new_interval)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the KWB heating system."""
        # Initialize register manager on first run
        if not hasattr(self, 'register_manager') or self.register_manager is None:
            await self._initialize_register_manager()
        
        if not self._registers:
            _LOGGER.warning("No registers configured")
            return {}

        try:
            # Ensure connection
            if not self.modbus_client._connected:
                _LOGGER.info("Connecting to KWB heating system at %s:%d", self.host, self.port)
                await self.modbus_client.connect()
            
            # Read registers in batches for efficiency
            register_data = await self.modbus_client.read_batch_registers(self._registers)
            
            # Process and convert data
            processed_data = {}
            for register in self._registers:
                address = register["starting_address"]
                if address in register_data:
                    processed_data[address] = self._process_register_value(
                        register, register_data[address]
                    )
                else:
                    _LOGGER.debug("No data for register %d (%s)", address, register["name"])
            
            _LOGGER.debug("Successfully updated %d registers", len(processed_data))
            return processed_data
            
        except Exception as exc:
            _LOGGER.warning("Error updating data from KWB heating system: %s", exc)
            # Return empty dict instead of raising exception to allow retry
            return {}

    def _process_register_value(self, register: dict, raw_value: int) -> dict[str, Any]:
        """Process raw register value according to register definition."""
        processed = {
            "raw_value": raw_value,
            "register": register,
        }
        
        # Use data converter for value processing
        converted_value = self.data_converter.convert_to_ha_value(register, raw_value)
        processed["value"] = converted_value
        
        # Get unit and device class
        unit = self.data_converter.get_unit(register)
        device_class = self.data_converter.get_device_class(register)
        
        if unit:
            processed["unit"] = unit
        if device_class:
            processed["device_class"] = device_class
        
        # Check if value has a text representation (value table)
        if self.data_converter.has_value_table(register):
            text_value = self.data_converter.get_display_value(register, raw_value)
            if text_value:
                processed["display_value"] = text_value
        
        return processed

    async def async_write_register(self, address: int, value: int) -> bool:
        """Write value to a register."""
        try:
            # Ensure connection
            if not self.modbus_client._connected:
                await self.modbus_client.connect()
            
            # Find register definition
            register = None
            for reg in self._registers:
                if reg["starting_address"] == address:
                    register = reg
                    break
            
            if not register:
                _LOGGER.error("Register %d not found in configuration", address)
                return False
            
            # Check if register is writable
            if register.get("access") != "RW":
                _LOGGER.error("Register %d is not writable", address)
                return False
            
            # Write the value
            success = await self.modbus_client.write_single_register(address, value)
            
            if success:
                _LOGGER.debug("Successfully wrote value %d to register %d", value, address)
                # Update our data immediately
                await self.async_request_refresh()
            else:
                _LOGGER.error("Failed to write value %d to register %d", value, address)
            
            return success
            
        except Exception as exc:
            _LOGGER.error("Error writing to register %d: %s", address, exc)
            return False

    def get_register_by_address(self, address: int) -> dict | None:
        """Get register definition by address."""
        if hasattr(self, '_registers') and self._registers:
            for register in self._registers:
                if register.get("starting_address") == address:
                    return register
        return None

    def get_registers_by_category(self, category: str) -> list[dict]:
        """Get registers filtered by category."""
        # This could be enhanced to categorize registers
        return [reg for reg in self._registers if category.lower() in reg["name"].lower()]

    @property
    def registers(self) -> list[dict]:
        """Get all configured registers."""
        return self._registers

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"{self.host}_{self.slave_id}")},
            "name": f"KWB Heating System ({self.host})",
            "manufacturer": "KWB",
            "model": "Heating System",
            "sw_version": "1.0.0",
            "configuration_url": f"http://{self.host}",
        }
