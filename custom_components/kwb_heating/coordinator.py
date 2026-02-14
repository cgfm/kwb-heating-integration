"""Data update coordinator for KWB Heating integration."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_CONNECTION_TYPE,
    CONF_SLAVE_ID,
    CONF_ACCESS_LEVEL,
    CONF_UPDATE_INTERVAL,
    CONF_DEVICE_TYPE,
    CONF_DEVICE_NAME,
    CONF_SERIAL_PORT,
    CONF_BAUDRATE,
    CONF_PARITY,
    CONF_STOPBITS,
    CONF_BYTESIZE,
    CONF_HEATING_CIRCUITS,
    CONF_BUFFER_STORAGE,
    CONF_DHW_STORAGE,
    CONF_SECONDARY_HEAT_SOURCES,
    CONF_CIRCULATION,
    CONF_SOLAR,
    CONF_BOILER_SEQUENCE,
    CONF_HEAT_METERS,
    CONNECTION_TYPE_TCP,
    CONNECTION_TYPE_SERIAL,
    DEFAULT_PORT,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_BAUDRATE,
    DEFAULT_PARITY,
    DEFAULT_STOPBITS,
    DEFAULT_BYTESIZE,
)
from .data_conversion import KWBDataConverter
from .modbus_client import KWBModbusClient
from .async_modular_register_manager import AsyncModularRegisterManager
from .version_manager import VersionManager
from .language_manager import LanguageManager

_LOGGER = logging.getLogger(__name__)

# Pre-compiled regex for entity ID sanitization (more efficient than chained replace)
_ENTITY_ID_INVALID_CHARS = re.compile(r"[^a-z0-9_]")

# Character replacements for entity ID sanitization
_ENTITY_ID_REPLACEMENTS = str.maketrans({
    " ": "_", ".": "_", "/": "_", "-": "_", ":": "_",
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "&": "and", "@": "at",
    "(": "", ")": "", "#": "", "!": "", "?": "", ",": "", ";": "", "'": "", '"': "",
})


class KWBDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the KWB heating system."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.connection_type = entry.data.get(CONF_CONNECTION_TYPE, CONNECTION_TYPE_TCP)
        self.host = entry.data.get(CONF_HOST)
        self.port = entry.data.get(CONF_PORT, DEFAULT_PORT)
        self.slave_id = entry.data.get(CONF_SLAVE_ID, 1)
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
            connection_type=self.connection_type,
            host=self.host,
            port=self.port,
            serial_port=entry.data.get(CONF_SERIAL_PORT),
            baudrate=entry.data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE),
            parity=entry.data.get(CONF_PARITY, DEFAULT_PARITY),
            stopbits=entry.data.get(CONF_STOPBITS, DEFAULT_STOPBITS),
            bytesize=entry.data.get(CONF_BYTESIZE, DEFAULT_BYTESIZE),
            slave_id=self.slave_id,
        )

        # Initialize version and language managers
        self.version_manager = VersionManager()
        self.language_manager = LanguageManager()

        # Version and language info (will be detected on first update)
        self.detected_version: str | None = None
        self.current_language: str = self.config.get("language", "auto")

    async def _detect_version(self) -> None:
        """Detect software version from the device."""
        try:
            # Ensure connection
            if not self.modbus_client.is_connected:
                await self.modbus_client.connect()

            # Detect version using version manager
            version = await self.version_manager.detect_version(self.modbus_client)
            self.detected_version = version

            _LOGGER.info("Detected KWB software version: %s", version)

        except Exception as exc:
            _LOGGER.warning("Could not detect version, using default: %s", exc)
            self.detected_version = self.version_manager.default_version

    async def _initialize_register_manager(self) -> None:
        """Initialize or reinitialize the register manager asynchronously."""
        # Initialize managers asynchronously (loads config files)
        await self.version_manager.async_initialize()
        await self.language_manager.async_initialize()

        # Detect version if not already done
        if not self.detected_version:
            await self._detect_version()

        # Resolve language
        ha_locale = self.hass.config.language if self.hass else None
        user_language = self.config.get("language", "auto")

        # Get supported languages for detected version
        supported_languages = self.version_manager.get_supported_languages(
            self.detected_version or "22.7.1"
        )

        resolved_language = self.language_manager.resolve_language(
            user_preference=user_language if user_language != "auto" else None,
            ha_locale=ha_locale,
            supported_languages=supported_languages
        )

        _LOGGER.info(
            "Initializing register manager for version %s, language %s",
            self.detected_version, resolved_language
        )

        # Initialize async register manager with version and language
        self.register_manager = AsyncModularRegisterManager(
            version=self.detected_version,
            language=resolved_language,
            version_manager=self.version_manager,
            language_manager=self.language_manager
        )

        # Initialize data converter with value tables (after async init)
        await self.register_manager.initialize()
        value_tables = self.register_manager.value_tables
        self.data_converter = KWBDataConverter(value_tables)
        
        # Get access level from config (options take precedence)
        access_level = self.config.get(CONF_ACCESS_LEVEL, self.access_level)
        
        # Get device type from config
        device_type = self.config.get(CONF_DEVICE_TYPE)
        
        # Store device type for device_info
        self.device_type = device_type
        
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
            if not self.modbus_client.is_connected:
                _LOGGER.info("Connecting to KWB heating system at %s", self.modbus_client._connection_label)
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
            if not self.modbus_client.is_connected:
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
            user_level = register.get("user_level", "")
            if user_level != "readwrite":
                _LOGGER.error("Register %d is not writable (user_level: %s)", address, user_level)
                return False
                
            # Check if this is a 32-bit register (2 Modbus registers)
            data_type = register.get("unit", "u16")
            
            if data_type in ["u32", "s32"]:
                # Split 32-bit value into two 16-bit values
                high_word = (value >> 16) & 0xFFFF
                low_word = value & 0xFFFF
                
                # Write both registers
                success = await self.modbus_client.write_multiple_registers(
                    address, [high_word, low_word]
                )
            else:
                # Write single 16-bit register
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
        # Use custom device name if available, otherwise fallback to device type or generic name
        device_name = self.config.get(CONF_DEVICE_NAME) or getattr(self, 'device_type', None) or "KWB Heating System"
        model_name = getattr(self, 'device_type', None) or "Heating System"

        # Create consistent device identifier based on connection and slave_id
        if self.connection_type == CONNECTION_TYPE_SERIAL:
            serial_port = self.config.get(CONF_SERIAL_PORT, "serial")
            device_identifier = f"{serial_port}_{self.slave_id}"
        else:
            device_identifier = f"{self.host}_{self.slave_id}"

        # Include detected version in sw_version
        sw_version = self.detected_version if self.detected_version else "Unknown"

        info: dict[str, Any] = {
            "identifiers": {(DOMAIN, device_identifier)},
            "name": device_name,
            "manufacturer": "KWB",
            "model": model_name,
            "sw_version": sw_version,
        }

        # Only add configuration_url for TCP connections
        if self.connection_type == CONNECTION_TYPE_TCP and self.host:
            info["configuration_url"] = f"http://{self.host}"

        return info

    @property
    def device_name_prefix(self) -> str:
        """Return device name suitable for entity name prefixes."""
        # Use custom device name if available, otherwise fallback to device type
        device_name = self.config.get(CONF_DEVICE_NAME) or getattr(self, 'device_type', None) or "KWB"
        
        # Remove redundant "KWB" prefix if it's already there and return a clean prefix
        if device_name.startswith("KWB "):
            return device_name[4:]  # Remove "KWB " prefix
        return device_name

    def sanitize_for_entity_id(self, text: str) -> str:
        """Sanitize text for use in entity IDs - shared method for consistent entity naming.

        Uses pre-compiled translation table and regex for better performance.
        """
        # Apply character translations and convert to lowercase
        result = text.lower().translate(_ENTITY_ID_REPLACEMENTS)
        # Remove any remaining invalid characters
        result = _ENTITY_ID_INVALID_CHARS.sub("", result)
        # Collapse multiple underscores and strip leading/trailing underscores
        result = re.sub(r"_+", "_", result).strip("_")
        return result

    def generate_entity_unique_id(self, register: dict) -> str:
        """Generate a stable, language-independent unique ID for an entity."""
        # Determine the unique device identifier, which is stable for the connection
        if self.connection_type == CONNECTION_TYPE_SERIAL:
            device_identifier = f"{self.config.get(CONF_SERIAL_PORT, 'serial')}_{self.slave_id}"
        else:
            device_identifier = f"{self.host}_{self.slave_id}"

        # The 'entity_id' from the JSON file is the primary stable identifier. It is language-independent.
        stable_id = register.get("entity_id")
        if stable_id:
            return f"{device_identifier}_{stable_id}"

        # Fallback for universal or older registers without a pre-defined 'entity_id'.
        # The 'parameter' field from the manufacturer's spec is a good stable key.
        parameter = register.get("parameter")
        address = register["starting_address"]
        if parameter:
            # Sanitize the parameter to be a valid component in a unique_id
            sanitized_parameter = re.sub(r'[^a-zA-Z0-9_.]', '_', parameter).replace('.', '_')
            return f"{device_identifier}_{sanitized_parameter}_{address}"

        # Absolute fallback using only the address, which is guaranteed to be unique and stable.
        _LOGGER.warning(
            "Register '%s' at address %d has no 'entity_id' or 'parameter' for unique ID generation. "
            "Falling back to address-only ID. This may be unstable if addresses change.",
            register.get('name', 'Unknown'), address
        )
        return f"{device_identifier}_{address}"
