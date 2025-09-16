"""Register manager for KWB configuration."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
import asyncio

from .const import DATA_TYPES

_LOGGER = logging.getLogger(__name__)


class RegisterManager:
    """Manages KWB register definitions from configuration."""

    def __init__(self, config_path: str | None = None):
        """Initialize the register manager."""
        if config_path is None:
            # Use minimal config for testing to avoid blocking I/O
            config_path = str(Path(__file__).parent / "kwb_config_minimal.json")
        
        self.config_path = Path(config_path)
        self._config: dict[str, Any] = {}
        self._universal_registers: list[dict] = []
        self._device_specific_registers: dict[str, list[dict]] = {}
        self._system_registers: dict[str, list[dict]] = {}
        self._equipment_registers: dict[str, list[dict]] = {}
        self._value_tables: dict[str, dict] = {}
        self._alarm_codes: list[dict] = []
        
        # Note: Cannot make __init__ async, so we'll use a sync wrapper for now
        # This is a compromise - the file is read synchronously but handled gracefully
        self._load_configuration_sync()

    def _read_file_sync(self) -> str:
        """Synchronous file reading for executor."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_configuration_sync(self) -> None:
        """Load configuration synchronously (fallback for __init__)."""
        _LOGGER.info("Loading KWB configuration from: %s", self.config_path)
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            _LOGGER.info("Parsing JSON content (%d characters)...", len(content))
            self._config = json.loads(content)
            
            _LOGGER.info("Successfully loaded JSON config")
            
            self._universal_registers = self._config.get("universal_registers", [])
            self._device_specific_registers = self._config.get("device_specific_registers", {})
            self._system_registers = self._config.get("system_registers", {})
            self._value_tables = self._config.get("value_tables", {})
            self._alarm_codes = self._config.get("alarm_codes", [])
            
            # Load equipment-specific registers from system_registers
            system_registers = self._config.get("system_registers", {})
            self._equipment_registers = {
                "Heizkreise": system_registers.get("Heizkreise", []),
                "Pufferspeicher": system_registers.get("Pufferspeicher", []),
                "Brauchwasserspeicher": system_registers.get("Brauchwasserspeicher", []),
                "Zweitwärmequellen": system_registers.get("Zweitwärmequellen", []),
                "Zirkulation": system_registers.get("Zirkulation", []),
                "Solar": system_registers.get("Solar", []),
                "Kesselfolgeschaltung": system_registers.get("Kesselfolgeschaltung", []),
                "Wärmemengenzähler": system_registers.get("Wärmemengenzähler", []),
            }
            
            total_equipment_registers = sum(len(regs) for regs in self._equipment_registers.values())
            total_device_registers = sum(len(regs) for regs in self._device_specific_registers.values())
            
            _LOGGER.info("Loaded KWB configuration with %d universal registers, %d device-specific registers, and %d equipment registers", 
                        len(self._universal_registers), total_device_registers, total_equipment_registers)
            
        except FileNotFoundError:
            _LOGGER.error("Configuration file not found: %s", self.config_path)
            raise
        except json.JSONDecodeError as exc:
            _LOGGER.error("Invalid JSON in configuration file: %s", exc)
            raise
        except Exception as exc:
            _LOGGER.error("Error loading configuration: %s", exc)
            raise

    async def _load_configuration(self) -> None:
        """Load configuration from JSON file asynchronously."""
        _LOGGER.info("Loading KWB configuration from: %s", self.config_path)
        try:
            # Use async file reading to avoid blocking I/O
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, self._read_file_sync)
            
            _LOGGER.info("Parsing JSON content (%d characters)...", len(content))
            self._config = json.loads(content)
            
            _LOGGER.info("Successfully loaded JSON config")
            
            self._universal_registers = self._config.get("universal_registers", [])
            self._device_specific_registers = self._config.get("device_specific_registers", {})
            self._system_registers = self._config.get("system_registers", {})
            self._value_tables = self._config.get("value_tables", {})
            self._alarm_codes = self._config.get("alarm_codes", [])
            
            # Load equipment-specific registers from system_registers
            system_registers = self._config.get("system_registers", {})
            self._equipment_registers = {
                "Heizkreise": system_registers.get("Heizkreise", []),
                "Pufferspeicher": system_registers.get("Pufferspeicher", []),
                "Brauchwasserspeicher": system_registers.get("Brauchwasserspeicher", []),
                "Zweitwärmequellen": system_registers.get("Zweitwärmequellen", []),
                "Zirkulation": system_registers.get("Zirkulation", []),
                "Solar": system_registers.get("Solar", []),
                "Kesselfolgeschaltung": system_registers.get("Kesselfolgeschaltung", []),
                "Wärmemengenzähler": system_registers.get("Wärmemengenzähler", []),
            }
            
            total_equipment_registers = sum(len(regs) for regs in self._equipment_registers.values())
            total_device_registers = sum(len(regs) for regs in self._device_specific_registers.values())
            
            _LOGGER.info("Loaded KWB configuration with %d universal registers, %d device-specific registers, and %d equipment registers", 
                        len(self._universal_registers), total_device_registers, total_equipment_registers)
            
        except FileNotFoundError:
            _LOGGER.error("Configuration file not found: %s", self.config_path)
            raise
        except json.JSONDecodeError as exc:
            _LOGGER.error("Invalid JSON in configuration file: %s", exc)
            raise

    def get_registers_for_access_level(self, access_level: str, limit: int = 1000) -> list[dict]:
        """Get limited registers for the specified access level."""
        registers = []
        count = 0
        
        for register in self._universal_registers:
            if count >= limit:
                break
                
            if self._register_allowed_for_access_level(register, access_level):
                # Only include registers with valid addresses
                starting_address = register.get("starting_address")
                if starting_address and (isinstance(starting_address, int) or (isinstance(starting_address, str) and starting_address.isdigit())):
                    # Convert string to int if needed
                    if isinstance(starting_address, str):
                        register["starting_address"] = int(starting_address)
                    registers.append(self._normalize_register(register))
                    count += 1
        
        _LOGGER.info("Selected %d registers for access level %s (limit: %d)", 
                    len(registers), access_level, limit)
        return registers

    def get_device_specific_registers(self, device_type: str, access_level: str) -> list[dict]:
        """Get device-specific registers for the access level."""
        registers = []
        
        device_registers = self._device_specific_registers.get(device_type, [])
        for register in device_registers:
            if self._register_allowed_for_access_level(register, access_level):
                registers.append(self._normalize_register(register))
        
        return registers

    def get_system_registers(self, system_type: str, access_level: str) -> list[dict]:
        """Get system-specific registers for the access level."""
        registers = []
        
        system_registers = self._system_registers.get(system_type, [])
        for register in system_registers:
            if self._register_allowed_for_access_level(register, access_level):
                registers.append(self._normalize_register(register))
        
        return registers

    def get_all_registers(self, access_level: str, equipment_config: dict = None, device_type: str | None = None) -> list[dict]:
        """Get all registers for the access level, selected equipment, and device type."""
        registers = []
        
        # Universal registers
        registers.extend(self.get_registers_for_access_level(access_level))
        
        # Device-specific registers
        if device_type and device_type in self._device_specific_registers:
            registers.extend(self.get_device_specific_registers(device_type, access_level))
            _LOGGER.info("Added device-specific registers for %s", device_type)
        
        # Equipment-specific registers based on configuration (using counts)
        if equipment_config:
            heating_circuits_count = equipment_config.get("heating_circuits", 0)
            if heating_circuits_count > 0:
                registers.extend(self.get_equipment_registers("Heizkreise", access_level, heating_circuits_count))
                
            buffer_storage_count = equipment_config.get("buffer_storage", 0)
            if buffer_storage_count > 0:
                registers.extend(self.get_equipment_registers("Pufferspeicher", access_level, buffer_storage_count))
                
            dhw_storage_count = equipment_config.get("dhw_storage", 0)
            if dhw_storage_count > 0:
                registers.extend(self.get_equipment_registers("Brauchwasserspeicher", access_level, dhw_storage_count))
                
            secondary_heat_sources_count = equipment_config.get("secondary_heat_sources", 0)
            if secondary_heat_sources_count > 0:
                registers.extend(self.get_equipment_registers("Zweitwärmequellen", access_level, secondary_heat_sources_count))
                
            circulation_count = equipment_config.get("circulation", 0)
            if circulation_count > 0:
                registers.extend(self.get_equipment_registers("Zirkulation", access_level, circulation_count))
                
            solar_count = equipment_config.get("solar", 0)
            if solar_count > 0:
                registers.extend(self.get_equipment_registers("Solar", access_level, solar_count))
                
            boiler_sequence_count = equipment_config.get("boiler_sequence", 0)
            if boiler_sequence_count > 0:
                registers.extend(self.get_equipment_registers("Kesselfolgeschaltung", access_level, boiler_sequence_count))
                
            heat_meters_count = equipment_config.get("heat_meters", 0)
            if heat_meters_count > 0:
                registers.extend(self.get_equipment_registers("Wärmemengenzähler", access_level, heat_meters_count))
        
        return registers

    def get_equipment_registers(self, equipment_type: str, access_level: str, count: int | None = None) -> list[dict]:
        """Get equipment-specific registers for the access level, limited by count."""
        registers = []
        
        equipment_registers = self._equipment_registers.get(equipment_type, [])
        
        # If count is specified and > 0, limit the number of registers
        if count is not None and count > 0:
            # Calculate registers per instance (e.g., for Heizkreise, Pufferspeicher, etc.)
            total_available = len(equipment_registers)
            
            if total_available > 0:
                # Estimate registers per instance (rough calculation)
                registers_per_instance = max(1, total_available // 16)  # Assume max 16 instances
                max_registers = min(total_available, count * registers_per_instance)
                
                # Take only the first max_registers
                limited_equipment_registers = equipment_registers[:max_registers]
                _LOGGER.debug("Limited %s registers to %d (count: %d, per instance: ~%d)", 
                             equipment_type, max_registers, count, registers_per_instance)
            else:
                limited_equipment_registers = []
        else:
            # If count is 0 or None, no registers
            limited_equipment_registers = []
        
        for register in limited_equipment_registers:
            if self._register_allowed_for_access_level(register, access_level):
                # Add equipment category to register
                normalized_register = self._normalize_register(register)
                normalized_register["equipment_category"] = equipment_type
                registers.append(normalized_register)
        
        _LOGGER.debug("Loaded %d %s registers for access level %s (requested count: %s)", 
                     len(registers), equipment_type, access_level, count)
        return registers

    def _register_allowed_for_access_level(self, register: dict, access_level: str) -> bool:
        """Check if register is allowed for the access level."""
        if access_level == "ExpertLevel":
            # Expert level can access everything that has read or write access in expert_level
            return (register.get("expert_level") in ["read", "write", "readwrite"] or 
                   register.get("user_level") in ["read", "write", "readwrite"])
        elif access_level == "UserLevel":
            # User level can only access user-level registers
            return register.get("user_level") in ["read", "write", "readwrite"]
        
        return False

    def _determine_access_type(self, register: dict) -> str:
        """Determine if register is read-only or read-write based on access levels."""
        user_level = register.get("user_level", "")
        expert_level = register.get("expert_level", "")
        
        # If either level allows write or readwrite, it's a read-write register
        if user_level in ["write", "readwrite"] or expert_level in ["write", "readwrite"]:
            return "RW"
        else:
            return "R"

    def _determine_access_level(self, register: dict) -> str:
        """Determine the minimum access level needed for this register."""
        if register.get("user_level") in ["read", "write", "readwrite"]:
            return "UserLevel"
        else:
            return "ExpertLevel"

    def _normalize_register(self, register: dict) -> dict:
        """Normalize register data structure."""
        starting_address = register.get("starting_address", 0)
        # Ensure starting_address is an integer
        if isinstance(starting_address, str) and starting_address.isdigit():
            starting_address = int(starting_address)
        elif not isinstance(starting_address, int):
            starting_address = 0
            
        normalized = {
            "starting_address": starting_address,
            "name": register.get("name", "Unknown"),
            "data_type": register.get("data_type", "04"),
            "unit": register.get("unit", ""),
            "access": self._determine_access_type(register),
            "access_level": self._determine_access_level(register),
            "type": register.get("type", register.get("unit", "u16")),  # Use type field, fallback to unit
            "unit_value_table": register.get("unit_value_table", ""),  # Changed from value_table
            "min": register.get("min", ""),
            "max": register.get("max", ""),
            # Some configs may use 'number_of_registers' instead of 'description'
            "description": register.get("description", str(register.get("number_of_registers", ""))),
            "id": register.get("id", ""),
            "index": register.get("index", ""),  # Include index for equipment identification
        }
        
        return normalized

    @property
    def value_tables(self) -> dict[str, dict]:
        """Return value tables for data conversion."""
        return self._value_tables

    @property
    def alarm_codes(self) -> list[dict]:
        """Return alarm codes."""
        return self._alarm_codes

    def get_value_table(self, table_name: str) -> dict[str, str] | None:
        """Get value table for enum conversion."""
        return self._value_tables.get(table_name)

    def convert_value_with_table(self, value: int, table_name: str) -> str:
        """Convert numeric value using value table."""
        if not table_name:
            return str(value)
        
        value_table = self.get_value_table(table_name)
        if value_table:
            return value_table.get(str(value), str(value))
        
        return str(value)

    def get_register_by_address(self, address: int) -> dict | None:
        """Get register definition by address."""
        for register in self._universal_registers:
            starting_address = register.get("starting_address")
            # Handle both string and int addresses
            if isinstance(starting_address, str) and starting_address.isdigit():
                starting_address = int(starting_address)
            if starting_address == address:
                return self._normalize_register(register)
        
        # Check device-specific registers
        for device_registers in self._device_specific_registers.values():
            for register in device_registers:
                starting_address = register.get("starting_address")
                if isinstance(starting_address, str) and starting_address.isdigit():
                    starting_address = int(starting_address)
                if starting_address == address:
                    return self._normalize_register(register)
        
        # Check system registers
        for system_registers in self._system_registers.values():
            for register in system_registers:
                starting_address = register.get("starting_address")
                if isinstance(starting_address, str) and starting_address.isdigit():
                    starting_address = int(starting_address)
                if starting_address == address:
                    return self._normalize_register(register)
        
        return None

    def get_alarm_codes(self) -> list[dict]:
        """Get all alarm codes."""
        return self._alarm_codes

    def get_modbus_config(self) -> dict:
        """Get Modbus configuration."""
        return self._config.get("modbus_config", {})

    def get_available_devices(self) -> list[str]:
        """Get list of available device types."""
        return list(self._device_specific_registers.keys())

    def get_available_systems(self) -> list[str]:
        """Get list of available system types."""
        return list(self._system_registers.keys())
