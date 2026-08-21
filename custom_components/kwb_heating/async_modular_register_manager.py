"""Async modular register manager for KWB configuration."""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any
import aiofiles

try:
    from .config_localization import (
        localize_alarm_codes,
        localize_register,
        localize_value_tables,
    )
except ImportError:  # Loaded directly by isolated regression tests.
    from config_localization import (
        localize_alarm_codes,
        localize_register,
        localize_value_tables,
    )


_LOGGER = logging.getLogger(__name__)


class AsyncModularRegisterManager:
    """Manages KWB register definitions from modular configuration files (async)."""

    EQUIPMENT_KEY_CONFIG = {
        "heating_circuits": {
            "filename": "heating_circuits.json",
            "lang": {
                "de": {"name": "Heizkreise"},
                "en": {"name": "Heating Circuits"}
            }
        },
        "buffer_storage": {
            "filename": "buffer_storage.json",
            "lang": {
                "de": {"name": "Pufferspeicher"},
                "en": {"name": "Buffer Storage"}
            }
        },
        "dhw_storage": {
            "filename": "dhw_storage.json",
            "lang": {
                "de": {"name": "Brauchwasserspeicher"},
                "en": {"name": "DHW Storage"}
            }
        },
        "secondary_heat_sources": {
            "filename": "secondary_heat_sources.json",
            "lang": {
                "de": {"name": "Zweitwärmequellen"},
                "en": {"name": "Secondary Heat Sources"}
            }
        },
        "circulation": {
            "filename": "circulation.json",
            "lang": {
                "de": {"name": "Zirkulation"},
                "en": {"name": "Circulation"}
            }
        },
        "solar": {
            "filename": "solar.json",
            "lang": {
                "de": {"name": "Solar"},
                "en": {"name": "Solar"}
            }
        },
        "boiler_sequence": {
            "filename": "boiler_sequence.json",
            "lang": {
                "de": {"name": "Kesselfolgeschaltung"},
                "en": {"name": "Boiler Sequence"}
            }
        },
        "heat_meters": {
            "filename": "heat_meters.json",
            "lang": {
                "de": {"name": "Wärmemengenzähler"},
                "en": {"name": "Heat Meters"}
            }
        },
        "transfer_stations": {
            "filename": "transfer_station.json",
            "lang": {
                "de": {"name": "Übergabestation"},
                "en": {"name": "Transfer Station"}
            }
        }
    }

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
                self._universal_registers = [
                    localize_register(register, self._language)
                    for register in universal_data.get("universal_registers", [])
                ]
            
            # Load value tables
            value_tables_path = self.config_dir / "value_tables.json"
            if value_tables_path.exists():
                async with aiofiles.open(value_tables_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    value_tables_data = json.loads(content)
                    self._value_tables = localize_value_tables(
                        value_tables_data.get("value_tables", {}), self._language
                    )

            alarm_codes_path = self.config_dir / "alarm_codes.json"
            if alarm_codes_path.exists():
                async with aiofiles.open(alarm_codes_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    alarm_codes_data = json.loads(content)
                    self._alarm_codes = localize_alarm_codes(
                        alarm_codes_data.get("alarm_codes", []), self._language
                    )
            
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
                registers = [
                    localize_register(register, self._language)
                    for register in device_data.get("registers", [])
                ]
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

    async def _load_equipment_registers(self, equipment_key: str) -> list[dict]:
        """Load equipment-specific registers on demand asynchronously."""
        if equipment_key in self._equipment_cache:
            return self._equipment_cache[equipment_key]

        config = self.EQUIPMENT_KEY_CONFIG.get(equipment_key)
        if not config:
            _LOGGER.warning("Unknown equipment key: %s", equipment_key)
            self._equipment_cache[equipment_key] = []
            return []

        filename = config["filename"]
        equipment_path = self.config_dir / "equipment" / filename
        try:
            async with aiofiles.open(equipment_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                equipment_data = json.loads(content)
                registers = [
                    localize_register(register, self._language)
                    for register in equipment_data.get("registers", [])
                ]
                self._equipment_cache[equipment_key] = registers
                _LOGGER.info("Loaded %d registers for equipment key %s", len(registers), equipment_key)
                return registers

        except FileNotFoundError:
            _LOGGER.warning("Equipment configuration not found: %s", equipment_path)
            self._equipment_cache[equipment_key] = []
            return []
        except json.JSONDecodeError as exc:
            _LOGGER.error("Invalid JSON in equipment configuration %s: %s", equipment_path, exc)
            self._equipment_cache[equipment_key] = []
            return []

    def get_registers_for_access_level(self, access_level: str, limit: int = 1000) -> list[dict]:
        """Get limited universal registers for the specified access level."""
        registers = []
        count = 0
        
        for register in self._universal_registers:
            if count >= limit:
                break

            if self._register_allowed_for_access_level(register, access_level):
                # Final address validation is centralized in add_registers(),
                # which applies equally to universal, device, and equipment maps.
                registers.append(self._normalize_register(register))
                # Invalid entries still reach the final validation for a useful
                # warning, but must not consume the caller's valid-register limit.
                if self._normalize_starting_address(register.get("starting_address")) is not None:
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

    async def get_equipment_registers(self, equipment_key: str, access_level: str, count: int | None = None) -> list[dict]:
        """Get equipment-specific registers for the access level, limited by count."""
        registers = []

        equipment_registers = await self._load_equipment_registers(equipment_key)
        
        config = self.EQUIPMENT_KEY_CONFIG.get(equipment_key)
        if not config:
            return []

        index_groups = self._get_equipment_index_groups(equipment_registers)

        # If count is specified and > 0, filter by index patterns
        if count is not None and count > 0:
            selected_instances = {
                prefix: set(instances[:count])
                for prefix, instances in index_groups.items()
            }
            limited_registers = []
            for register in equipment_registers:
                parsed_index = self._technical_equipment_index(register)
                if not parsed_index:
                    # A blank index denotes a feature-level register. It is not
                    # tied to a particular equipment instance, so include it once
                    # when that feature is enabled. Non-blank unparseable indexes
                    # remain excluded because their instance association is unclear.
                    if not register.get("index"):
                        limited_registers.append(register)
                    else:
                        _LOGGER.warning(
                            "Skipping %s register with unparseable equipment index %r: %s",
                            equipment_key,
                            register.get("index"),
                            self._register_description(register),
                        )
                    continue
                prefix, instance = parsed_index
                if instance in selected_instances.get(prefix, set()):
                    limited_registers.append(register)

            if not index_groups:
                _LOGGER.warning(
                    "No indexed %s registers found for language %s",
                    equipment_key,
                    self._language,
                )
        else:
            limited_registers = equipment_registers

        for register in limited_registers:
            if self._register_allowed_for_access_level(register, access_level):
                registers.append(
                    self._normalize_register(register, equipment_key, index_groups)
                )

        _LOGGER.info("Selected %d %s registers for access level %s (count: %s)",
                    len(registers), equipment_key, access_level, count)
        return registers

    @staticmethod
    def _parse_equipment_index(index: str) -> tuple[str, int] | None:
        """Return the index prefix and physical instance number."""
        if not index or " " not in index:
            return None

        prefix, identifier = index.split(" ", 1)
        instance_text = identifier.split(".", 1)[0]
        try:
            return prefix, int(instance_text)
        except ValueError:
            return None

    @staticmethod
    def _technical_equipment_index(register: dict) -> tuple[str, int] | None:
        """Return the language-neutral equipment group and physical instance."""
        group = register.get("equipment_group")
        instance = register.get("equipment_instance")
        if isinstance(group, str) and group and isinstance(instance, int):
            return group, instance
        # Scalar indexes remain supported for isolated legacy test fixtures. The
        # canonical schema requires explicit technical equipment fields.
        return AsyncModularRegisterManager._parse_equipment_index(
            register.get("index", "")
        )

    @staticmethod
    def _normalize_starting_address(value: Any) -> int | None:
        """Return a non-negative Modbus address without changing source config."""
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value if value >= 0 else None
        if isinstance(value, str):
            normalized = value.strip()
            if normalized.isdigit():
                return int(normalized)
        return None

    @staticmethod
    def _register_semantic_signature(register: dict) -> tuple[Any, ...]:
        """Fields that must agree when two files define the same address."""
        fields = (
            "entity_id", "parameter", "data_type", "register_type", "type", "unit",
            "unit_value_table", "user_level", "expert_level", "access_level",
            "equipment_group", "equipment_instance", "equipment_subindex",
        )
        return tuple(register.get(field) for field in fields)

    @staticmethod
    def _register_description(register: dict) -> str:
        """Provide enough context to diagnose a duplicate definition."""
        return (
            f"name={register.get('name')!r}, entity_id={register.get('entity_id')!r}, "
            f"parameter={register.get('parameter')!r}, index={register.get('index')!r}"
        )

    def _get_equipment_index_groups(
        self, equipment_registers: list[dict]
    ) -> dict[str, list[int]]:
        """Derive every index prefix and its available slots from register data."""
        groups: dict[str, set[int]] = {}
        for register in equipment_registers:
            parsed_index = self._technical_equipment_index(register)
            if not parsed_index:
                continue
            prefix, instance = parsed_index
            groups.setdefault(prefix, set()).add(instance)

        return {
            prefix: sorted(instances)
            for prefix, instances in groups.items()
        }

    async def get_all_registers(self, access_level: str, equipment_config: dict = None, device_type: str | None = None) -> list[dict]:
        """Get all registers for the access level, selected equipment, and device type."""
        await self.initialize()  # Ensure async initialization

        registers = []
        seen_addresses: dict[int, dict] = {}
        seen_entity_ids: set[str] = set()

        def add_registers(new_registers: list[dict]) -> int:
            """Add registers, deduplicating addresses and repairing ID collisions."""
            added = 0
            for reg in new_registers:
                original_address = reg.get("starting_address")
                addr = self._normalize_starting_address(original_address)
                if addr is None:
                    _LOGGER.warning(
                        "Skipping register with invalid starting_address %r: %s",
                        original_address,
                        self._register_description(reg),
                    )
                    continue
                eid = reg.get("entity_id")
                if addr is not None and addr in seen_addresses:
                    previous = seen_addresses[addr]
                    if (
                        self._register_semantic_signature(previous)
                        == self._register_semantic_signature(reg)
                    ):
                        _LOGGER.debug(
                            "Skipping equivalent duplicate register at address %s: %s",
                            addr,
                            self._register_description(reg),
                        )
                    else:
                        _LOGGER.warning(
                            "Skipping conflicting duplicate register at address %s; "
                            "keeping [%s], ignoring [%s]",
                            addr,
                            self._register_description(previous),
                            self._register_description(reg),
                        )
                    continue
                if addr is not None and reg.get("starting_address") != addr:
                    reg = dict(reg)
                    reg["starting_address"] = addr
                if eid and eid in seen_entity_ids:
                    # Never discard a valid register because of a configuration
                    # mistake. The address is stable and unique within a Modbus map.
                    reg = dict(reg)
                    replacement = f"{eid}_register_{addr}"
                    suffix = 2
                    while replacement in seen_entity_ids:
                        replacement = f"{eid}_register_{addr}_{suffix}"
                        suffix += 1
                    _LOGGER.warning(
                        "Duplicate entity_id '%s' at address %s (%s); using '%s'",
                        eid, addr, reg.get("name"), replacement,
                    )
                    reg["entity_id"] = replacement
                    eid = replacement
                if addr is not None:
                    seen_addresses[addr] = reg
                if eid:
                    seen_entity_ids.add(eid)
                registers.append(reg)
                added += 1
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
            for key in self.EQUIPMENT_KEY_CONFIG:
                count = equipment_config.get(key, 0)
                if count > 0:
                    equipment_regs = await self.get_equipment_registers(key, access_level, count)
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

    def _normalize_register(
        self,
        register: dict,
        equipment_key: str | None = None,
        index_groups: dict[str, list[int]] | None = None,
    ) -> dict:
        """Normalize register definition."""
        normalized = register.copy()
        
        # Ensure starting_address is an integer without mutating the source map.
        if "starting_address" in normalized:
            addr = self._normalize_starting_address(normalized["starting_address"])
            if addr is not None:
                normalized["starting_address"] = addr
        
        # Add equipment prefix to name for better identification
        index = normalized.get("index", "")
        name = normalized.get("name", "")
        
        if index and name and equipment_key:
            config = self.EQUIPMENT_KEY_CONFIG.get(equipment_key)
            parsed_index = self._technical_equipment_index(normalized)
            if config and parsed_index:
                lang_config = (
                    config["lang"].get(self._language)
                    or config["lang"].get("en")
                    or config["lang"]["de"]
                )
                friendly_name = lang_config["name"]
                equipment_group, _instance = parsed_index
                equipment_id = index.split(" ", 1)[1]
                instances = (index_groups or {}).get(equipment_group, [])

                # Only simple numeric indices are shifted for display. Compound
                # values such as heating circuit 1.1 are already user-facing.
                if equipment_id.isdigit() and instances and instances[0] == 0:
                    equipment_id = str(int(equipment_id) + 1)

                normalized["name"] = f"{friendly_name} {equipment_id}: {name}"
        
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
