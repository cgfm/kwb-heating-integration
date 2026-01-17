"""Async modular register manager for KWB configuration."""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any
import aiofiles

from .const import DATA_TYPES

_LOGGER = logging.getLogger(__name__)


class AsyncModularRegisterManager:
    """Manages KWB register definitions from modular configuration files (async)."""

    def __init__(
        self,
        config_path: str | None = None,
        version: str | None = None,
        language: str | None = None,
        version_manager=None,
        language_manager=None
    ):
        """Initialize the async modular register manager.

        Args:
            config_path: Path to configuration directory. If None, uses default.
            version: Software version (e.g., "22.7.1"). If None, uses current config.
            language: Language code (e.g., "de", "en"). If None, uses "de".
            version_manager: Optional VersionManager instance for version-aware config loading.
            language_manager: Optional LanguageManager instance for language-aware config loading.
        """
        # Store version and language info
        self._version = version
        self._language = language or "de"
        self._version_manager = version_manager
        self._language_manager = language_manager

        # Determine config directory
        if config_path is None:
            config_path = str(Path(__file__).parent / "config")

        # If version and language are provided with managers, use version-specific path
        if version and language and version_manager:
            try:
                self.config_dir = version_manager.get_config_path(version, language)
                _LOGGER.info("Using version-specific config path: %s", self.config_dir)
            except Exception as exc:
                _LOGGER.warning("Could not get version-specific path, using default: %s", exc)
                self.config_dir = Path(config_path)
        else:
            self.config_dir = Path(config_path)

        self._meta_config: dict[str, Any] = {}
        self._universal_registers: list[dict] = []
        self._value_tables: dict[str, dict] = {}
        self._alarm_codes: list[dict] = []

        # Cache for loaded device and equipment configs
        self._device_cache: dict[str, list[dict]] = {}
        self._equipment_cache: dict[str, list[dict]] = {}

        self._initialized = False

    async def initialize(self) -> None:
        """Async initialization."""
        if self._initialized:
            return
            
        await self._load_base_configuration()
        self._initialized = True

    async def _load_base_configuration(self) -> None:
        """Load base configuration (meta, universal, value tables) asynchronously."""
        try:
            # Load universal registers from modbus_registers.json
            modbus_registers_path = self.config_dir / "modbus_registers.json"
            if modbus_registers_path.exists():
                async with aiofiles.open(modbus_registers_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    universal_data = json.loads(content)
                    self._universal_registers = universal_data.get("universal_registers", [])
            
            # Load value tables
            value_tables_path = self.config_dir / "value_tables.json"
            if value_tables_path.exists():
                async with aiofiles.open(value_tables_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    value_tables_data = json.loads(content)
                    self._value_tables = value_tables_data.get("value_tables", {})
            
            _LOGGER.info("Loaded async modular KWB configuration: %d universal registers, %d value tables", 
                        len(self._universal_registers), len(self._value_tables))
            
        except FileNotFoundError as exc:
            _LOGGER.error("Configuration file not found: %s", exc)
            raise
        except json.JSONDecodeError as exc:
            _LOGGER.error("Invalid JSON in configuration file: %s", exc)
            raise

    async def _load_device_registers(self, device_type: str) -> list[dict]:
        """Load device-specific registers on demand asynchronously."""
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
            "KWB CF 1.5": "kwb_cf1_5.json",
            "KWB EasyAir Plus": "kwb_easyair_plus.json"
        }
        
        filename = device_file_mapping.get(device_type)
        if not filename:
            _LOGGER.warning("Unknown device type: %s", device_type)
            self._device_cache[device_type] = []
            return []
        
        device_path = self.config_dir / "devices" / filename
        try:
            async with aiofiles.open(device_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                device_data = json.loads(content)
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

    async def _load_equipment_registers(self, equipment_type: str) -> list[dict]:
        """Load equipment-specific registers on demand asynchronously."""
        if equipment_type in self._equipment_cache:
            return self._equipment_cache[equipment_type]
        
        # Map equipment type to filename
        equipment_file_mapping = {
            "Heizkreise": "heating_circuits.json",
            "Pufferspeicher": "buffer_storage.json",
            "Brauchwasserspeicher": "dhw_storage.json",
            "Zweitwärmequellen": "secondary_heat_sources.json",
            "Zirkulation": "circulation.json",
            "Solar": "solar.json",
            "Kesselfolgeschaltung": "boiler_sequence.json",
            "Wärmemengenzähler": "heat_meters.json",
            "Übergabestation": "transfer_station.json"
        }
        
        filename = equipment_file_mapping.get(equipment_type)
        if not filename:
            _LOGGER.warning("Unknown equipment type: %s", equipment_type)
            self._equipment_cache[equipment_type] = []
            return []
        
        equipment_path = self.config_dir / "equipment" / filename
        try:
            async with aiofiles.open(equipment_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                equipment_data = json.loads(content)
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

    async def get_device_specific_registers(self, device_type: str, access_level: str) -> list[dict]:
        """Get device-specific registers for the access level."""
        registers = []
        
        device_registers = await self._load_device_registers(device_type)
        for register in device_registers:
            if self._register_allowed_for_access_level(register, access_level):
                registers.append(self._normalize_register(register))
        
        return registers

    async def get_equipment_registers(self, equipment_type: str, access_level: str, count: int | None = None) -> list[dict]:
        """Get equipment-specific registers for the access level, limited by count."""
        registers = []
        
        equipment_registers = await self._load_equipment_registers(equipment_type)
        
        # If count is specified and > 0, filter by index patterns
        if count is not None and count > 0:
            filtered_registers = []
            
            if equipment_type == "Heizkreise":
                # For heating circuits, filter by HK index pattern (HK 1.x, HK 2.x, etc.)
                for i in range(1, count + 1):
                    pattern = f"HK {i}."
                    for register in equipment_registers:
                        index = register.get("index", "")
                        if index.startswith(pattern):
                            filtered_registers.append(register)
            elif equipment_type == "Pufferspeicher":
                # For buffer storage, filter by PUF index pattern (PUF 0, PUF 1, etc.)
                for i in range(count):  # PUF starts at 0
                    pattern = f"PUF {i}"
                    for register in equipment_registers:
                        index = register.get("index", "")
                        if index == pattern:  # Exact match for PUF
                            filtered_registers.append(register)
            else:
                # For other equipment types, use simple count-based filtering
                # This assumes the first 'count' instances are what we want
                instances_seen = set()
                for register in equipment_registers:
                    index = register.get("index", "")
                    if index:
                        # Extract instance identifier (e.g., "Something 1" -> "1")
                        instance_id = index.split()[-1] if index.split() else "1"
                        if instance_id not in instances_seen and len(instances_seen) < count:
                            instances_seen.add(instance_id)
                        if instance_id in instances_seen:
                            filtered_registers.append(register)
                    
            limited_registers = filtered_registers
        else:
            limited_registers = equipment_registers

        for register in limited_registers:
            if self._register_allowed_for_access_level(register, access_level):
                registers.append(self._normalize_register(register))
        
        _LOGGER.info("Selected %d %s registers for access level %s (count: %s)", 
                    len(registers), equipment_type, access_level, count)
        return registers

    async def get_all_registers(self, access_level: str, equipment_config: dict = None, device_type: str | None = None) -> list[dict]:
        """Get all registers for the access level, selected equipment, and device type."""
        await self.initialize()  # Ensure async initialization

        registers = []
        seen_addresses: set[int] = set()  # Track addresses to prevent duplicates

        def add_registers(new_registers: list[dict]) -> int:
            """Add registers while preventing duplicates by address."""
            added = 0
            for reg in new_registers:
                addr = reg.get("starting_address")
                if addr is not None and addr not in seen_addresses:
                    seen_addresses.add(addr)
                    registers.append(reg)
                    added += 1
                elif addr in seen_addresses:
                    _LOGGER.debug("Skipping duplicate register at address %s: %s", addr, reg.get("name"))
            return added

        # Universal registers (added first, take priority)
        universal_regs = self.get_registers_for_access_level(access_level)
        add_registers(universal_regs)

        # Device-specific registers (skip duplicates already in universal)
        if device_type:
            device_registers = await self.get_device_specific_registers(device_type, access_level)
            added = add_registers(device_registers)
            _LOGGER.info("Added %d device-specific registers for %s (skipped %d duplicates)",
                        added, device_type, len(device_registers) - added)

        # Equipment-specific registers based on configuration (using counts)
        if equipment_config:
            heating_circuits_count = equipment_config.get("heating_circuits", 0)
            if heating_circuits_count > 0:
                equipment_regs = await self.get_equipment_registers("Heizkreise", access_level, heating_circuits_count)
                add_registers(equipment_regs)

            buffer_storage_count = equipment_config.get("buffer_storage", 0)
            if buffer_storage_count > 0:
                equipment_regs = await self.get_equipment_registers("Pufferspeicher", access_level, buffer_storage_count)
                add_registers(equipment_regs)

            dhw_storage_count = equipment_config.get("dhw_storage", 0)
            if dhw_storage_count > 0:
                equipment_regs = await self.get_equipment_registers("Brauchwasserspeicher", access_level, dhw_storage_count)
                add_registers(equipment_regs)

            secondary_heat_sources_count = equipment_config.get("secondary_heat_sources", 0)
            if secondary_heat_sources_count > 0:
                equipment_regs = await self.get_equipment_registers("Zweitwärmequellen", access_level, secondary_heat_sources_count)
                add_registers(equipment_regs)

            circulation_count = equipment_config.get("circulation", 0)
            if circulation_count > 0:
                equipment_regs = await self.get_equipment_registers("Zirkulation", access_level, circulation_count)
                add_registers(equipment_regs)

            solar_count = equipment_config.get("solar", 0)
            if solar_count > 0:
                equipment_regs = await self.get_equipment_registers("Solar", access_level, solar_count)
                add_registers(equipment_regs)

            boiler_sequence_count = equipment_config.get("boiler_sequence", 0)
            if boiler_sequence_count > 0:
                equipment_regs = await self.get_equipment_registers("Kesselfolgeschaltung", access_level, boiler_sequence_count)
                add_registers(equipment_regs)

            heat_meters_count = equipment_config.get("heat_meters", 0)
            if heat_meters_count > 0:
                equipment_regs = await self.get_equipment_registers("Wärmemengenzähler", access_level, heat_meters_count)
                add_registers(equipment_regs)

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
        
        # Add equipment prefix to name for better identification
        index = normalized.get("index", "")
        name = normalized.get("name", "")
        
        if index and name:
            # Map equipment indices to friendly names
            equipment_prefixes = {
                "HK": "Heizkreis",
                "PUF": "Pufferspeicher", 
                "BWS": "Brauchwasserspeicher",
                "ZWQ": "Zweitwärmequelle",
                "ZIR": "Zirkulation",
                "SOL": "Solar",
                "KFS": "Kesselfolge", 
                "WMZ": "Wärmemengenzähler"
            }
            
            # Extract equipment type and number from index
            for prefix, friendly_name in equipment_prefixes.items():
                if index.startswith(prefix):
                    # Extract the equipment number/identifier
                    equipment_id = index[len(prefix):].strip()
                    
                    # Special handling for different equipment types
                    if prefix == "HK":
                        # HK 1.1 -> Heizkreis 1.1
                        new_name = f"{friendly_name} {equipment_id}: {name}"
                    elif prefix == "PUF":
                        # PUF 0 -> Pufferspeicher 1 (user-friendly numbering starts at 1)
                        try:
                            puf_num = int(equipment_id) + 1
                            new_name = f"{friendly_name} {puf_num}: {name}"
                        except ValueError:
                            new_name = f"{friendly_name} {equipment_id}: {name}"
                    else:
                        # Default: BWS 1 -> Brauchwasserspeicher 1
                        new_name = f"{friendly_name} {equipment_id}: {name}"
                    
                    normalized["name"] = new_name
                    break
        
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
        
        # Set access field based on user_level and expert_level for entity creation
        user_level = normalized.get("user_level", "read")
        expert_level = normalized.get("expert_level", "read")
        
        if "readwrite" in user_level.lower() or "readwrite" in expert_level.lower():
            normalized["access"] = "RW"
        elif "write" in user_level.lower() or "write" in expert_level.lower():
            normalized["access"] = "RW"
        else:
            normalized["access"] = "R"
        
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

    async def reload_for_version_language(self, version: str, language: str) -> None:
        """Reload configuration for a different version and language.

        Args:
            version: Software version
            language: Language code
        """
        _LOGGER.info("Reloading configuration for version %s, language %s", version, language)

        # Update version and language
        self._version = version
        self._language = language

        # Update config directory if version manager is available
        if self._version_manager:
            try:
                self.config_dir = self._version_manager.get_config_path(version, language)
                _LOGGER.info("Updated config path to: %s", self.config_dir)
            except Exception as exc:
                _LOGGER.error("Could not update config path: %s", exc)
                return

        # Clear all caches
        self._universal_registers = []
        self._value_tables = {}
        self._alarm_codes = []
        self._device_cache.clear()
        self._equipment_cache.clear()

        # Mark as uninitialized and reload
        self._initialized = False
        await self.initialize()

        _LOGGER.info("Configuration reloaded successfully")

    @property
    def current_version(self) -> str | None:
        """Get current version."""
        return self._version

    @property
    def current_language(self) -> str:
        """Get current language."""
        return self._language
