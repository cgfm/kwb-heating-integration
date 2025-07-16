"""Modular register manager for KWB configuration."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .const import DATA_TYPES

_LOGGER = logging.getLogger(__name__)


class ModularRegisterManager:
    """Manages KWB register definitions from modular configuration files."""

    def __init__(self, config_path: str | None = None):
        """Initialize the modular register manager."""
        if config_path is None:
            # Default to config directory in the same directory
            config_path = str(Path(__file__).parent / "config")
        
        self.config_dir = Path(config_path)
        self._meta_config: dict[str, Any] = {}
        self._universal_registers: list[dict] = []
        self._value_tables: dict[str, dict] = {}
        self._alarm_codes: list[dict] = []
        
        # Cache for loaded device and equipment configs
        self._device_cache: dict[str, list[dict]] = {}
        self._equipment_cache: dict[str, list[dict]] = {}
        
        self._load_base_configuration()

    def _load_base_configuration(self) -> None:
        """Load base configuration (meta, universal, value tables)."""
        try:
            # Load meta config
            meta_path = self.config_dir / "meta_config.json"
            if meta_path.exists():
                with open(meta_path, 'r', encoding='utf-8') as f:
                    self._meta_config = json.load(f)
            
            # Load universal registers
            universal_path = self.config_dir / "universal_registers.json"
            if universal_path.exists():
                with open(universal_path, 'r', encoding='utf-8') as f:
                    universal_data = json.load(f)
                    self._universal_registers = universal_data.get("universal_registers", [])
            
            # Load value tables
            value_tables_path = self.config_dir / "value_tables.json"
            if value_tables_path.exists():
                with open(value_tables_path, 'r', encoding='utf-8') as f:
                    value_tables_data = json.load(f)
                    self._value_tables = value_tables_data.get("value_tables", {})
            
            # Load alarm codes (optional, on demand)
            alarm_codes_path = self.config_dir / "alarm_codes.json"
            if alarm_codes_path.exists():
                with open(alarm_codes_path, 'r', encoding='utf-8') as f:
                    alarm_data = json.load(f)
                    self._alarm_codes = alarm_data.get("alarm_codes", [])
            
            _LOGGER.info("Loaded modular KWB configuration: %d universal registers, %d value tables", 
                        len(self._universal_registers), len(self._value_tables))
            
        except FileNotFoundError as exc:
            _LOGGER.error("Configuration file not found: %s", exc)
            raise
        except json.JSONDecodeError as exc:
            _LOGGER.error("Invalid JSON in configuration file: %s", exc)
            raise

    def _load_device_registers(self, device_type: str) -> list[dict]:
        """Load device-specific registers on demand."""
        if device_type in self._device_cache:
            return self._device_cache[device_type]
        
        # Map device type to filename
        device_file_mapping = {
            "KWB Easyfire": "kwb_easyfire.json",
            "KWB Multifire": "kwb_multifire.json", 
            "KWB Pelletfire+": "kwb_pelletfire_plus.json",
            "KWB Combifire": "kwb_combifire.json",
            "KWB CF 2": "kwb_cf2.json",
            "KWB CF 1": "kwb_cf1.json",
            "KWB CF 1.5": "kwb_cf1_5.json"
        }
        
        filename = device_file_mapping.get(device_type)
        if not filename:
            _LOGGER.warning("Unknown device type: %s", device_type)
            self._device_cache[device_type] = []
            return []
        
        device_path = self.config_dir / "devices" / filename
        try:
            with open(device_path, 'r', encoding='utf-8') as f:
                device_data = json.load(f)
                registers = device_data.get("registers", [])
                self._device_cache[device_type] = registers
                _LOGGER.info("Loaded %d registers for device type %s", len(registers), device_type)
                return registers
                
        except FileNotFoundError:
            _LOGGER.warning("Device configuration not found: %s", device_path)
            self._device_cache[device_type] = []
            return []
        except json.JSONDecodeError as exc:
            _LOGGER.error("Invalid JSON in device configuration %s: %s", device_path, exc)
            self._device_cache[device_type] = []
            return []

    def _load_equipment_registers(self, equipment_type: str) -> list[dict]:
        """Load equipment-specific registers on demand."""
        if equipment_type in self._equipment_cache:
            return self._equipment_cache[equipment_type]
        
        # Map equipment type to filename
        equipment_file_mapping = {
            "Heizkreise": "heizkreise.json",
            "Pufferspeicher": "pufferspeicher.json",
            "Brauchwasserspeicher": "brauchwasser.json", 
            "Zweitwärmequellen": "zweitwaermequellen.json",
            "Zirkulation": "zirkulation.json",
            "Solar": "solar.json",
            "Kesselfolgeschaltung": "kesselfolge.json",
            "Wärmemengenzähler": "waermemengenzaehler.json"
        }
        
        filename = equipment_file_mapping.get(equipment_type)
        if not filename:
            _LOGGER.warning("Unknown equipment type: %s", equipment_type)
            self._equipment_cache[equipment_type] = []
            return []
        
        equipment_path = self.config_dir / "equipment" / filename
        try:
            with open(equipment_path, 'r', encoding='utf-8') as f:
                equipment_data = json.load(f)
                registers = equipment_data.get("registers", [])
                self._equipment_cache[equipment_type] = registers
                _LOGGER.info("Loaded %d registers for equipment type %s", len(registers), equipment_type)
                return registers
                
        except FileNotFoundError:
            _LOGGER.warning("Equipment configuration not found: %s", equipment_path)
            self._equipment_cache[equipment_type] = []
            return []
        except json.JSONDecodeError as exc:
            _LOGGER.error("Invalid JSON in equipment configuration %s: %s", equipment_path, exc)
            self._equipment_cache[equipment_type] = []
            return []

    def get_registers_for_access_level(self, access_level: str, limit: int = 1000) -> list[dict]:
        """Get limited universal registers for the specified access level."""
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
        
        _LOGGER.info("Selected %d universal registers for access level %s (limit: %d)", 
                    len(registers), access_level, limit)
        return registers

    def get_device_specific_registers(self, device_type: str, access_level: str) -> list[dict]:
        """Get device-specific registers for the access level."""
        registers = []
        
        device_registers = self._load_device_registers(device_type)
        for register in device_registers:
            if self._register_allowed_for_access_level(register, access_level):
                registers.append(self._normalize_register(register))
        
        return registers

    def get_equipment_registers(self, equipment_type: str, access_level: str, count: int | None = None) -> list[dict]:
        """Get equipment-specific registers for the access level, limited by count."""
        registers = []
        
        equipment_registers = self._load_equipment_registers(equipment_type)
        
        # If count is specified and > 0, limit the number of registers
        if count is not None and count > 0:
            # Take only the first 'count' sets of registers for this equipment type
            # Assuming each equipment instance has the same number of registers
            if equipment_registers:
                registers_per_instance = len(equipment_registers) // max(1, count)
                if registers_per_instance > 0:
                    limited_registers = equipment_registers[:count * registers_per_instance]
                else:
                    limited_registers = equipment_registers[:count]
            else:
                limited_registers = []
        else:
            limited_registers = equipment_registers
        
        for register in limited_registers:
            if self._register_allowed_for_access_level(register, access_level):
                registers.append(self._normalize_register(register))
        
        _LOGGER.info("Selected %d %s registers for access level %s (count: %s)", 
                    len(registers), equipment_type, access_level, count)
        return registers

    def get_all_registers(self, access_level: str, equipment_config: dict = None, device_type: str | None = None) -> list[dict]:
        """Get all registers for the access level, selected equipment, and device type."""
        registers = []
        
        # Universal registers
        registers.extend(self.get_registers_for_access_level(access_level))
        
        # Device-specific registers
        if device_type:
            device_registers = self.get_device_specific_registers(device_type, access_level)
            registers.extend(device_registers)
            _LOGGER.info("Added %d device-specific registers for %s", len(device_registers), device_type)
        
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

    def _register_allowed_for_access_level(self, register: dict, access_level: str) -> bool:
        """Check if register is allowed for the given access level."""
        if access_level == "ExpertLevel":
            # Expert level can access all registers
            return True
        elif access_level == "UserLevel":
            # User level: must have read access for user level
            user_level = register.get("user_level", "")
            return "read" in user_level.lower()
        
        return False

    def _normalize_register(self, register: dict) -> dict:
        """Normalize register definition."""
        normalized = register.copy()
        
        # Ensure starting_address is integer
        if "starting_address" in normalized:
            addr = normalized["starting_address"]
            if isinstance(addr, str) and addr.isdigit():
                normalized["starting_address"] = int(addr)
        
        # Add default access level if missing
        if "access_level" not in normalized:
            user_level = normalized.get("user_level", "read")
            expert_level = normalized.get("expert_level", "read")
            
            if "write" in user_level.lower():
                normalized["access_level"] = "UserLevel"
            elif "write" in expert_level.lower():
                normalized["access_level"] = "ExpertLevel"
            else:
                normalized["access_level"] = "UserLevel"
        
        return normalized

    def get_register_by_address(self, address: int) -> dict | None:
        """Get register definition by address."""
        # Search in all loaded registers
        for register in self._universal_registers:
            if register.get("starting_address") == address:
                return register
        
        # Search in cached device registers
        for device_registers in self._device_cache.values():
            for register in device_registers:
                if register.get("starting_address") == address:
                    return register
        
        # Search in cached equipment registers
        for equipment_registers in self._equipment_cache.values():
            for register in equipment_registers:
                if register.get("starting_address") == address:
                    return register
        
        return None

    def get_value_table(self, table_name: str) -> dict | None:
        """Get specific value table by name."""
        return self._value_tables.get(table_name)

    def has_value_table(self, table_name: str) -> bool:
        """Check if value table exists."""
        return table_name in self._value_tables

    @property
    def value_tables(self) -> dict[str, dict]:
        """Get value tables."""
        return self._value_tables

    @property
    def alarm_codes(self) -> list[dict]:
        """Get alarm codes."""
        return self._alarm_codes
