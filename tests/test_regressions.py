"""Regression tests for configuration and connection bugs."""
from __future__ import annotations

import asyncio
import ast
from collections import defaultdict
import enum
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_ROOT = PROJECT_ROOT / "custom_components" / "kwb_heating"
CONFIG_ROOT = INTEGRATION_ROOT / "config" / "versions"
CONVERTER_CONFIG_ROOT = PROJECT_ROOT / "modbusinfoConverter" / "config" / "versions"

# The integration deliberately retains these three legacy IDs rather than using
# the converter's newer parameter-derived variants. They are part of the public
# Home Assistant identity contract, so parity checks allow only these exact pairs.
INTENTIONAL_ENTITY_ID_OVERRIDES = {
    ("boiler_pump_percent", "boiler_pump_kesselpumpe_steuerstufe"),
    ("boiler_temperature_setpoint_setting", "boiler_temperature_setpoint_kesseltemp_soll_1"),
    ("full_load_hours_pm", "full_load_hours_pm_betriebsminuten_summe"),
}
INTENTIONAL_VALUE_TABLE_ADDITIONS_BY_VERSION = {
    "v21.4.0": {"system_ein_aus_t", "system_yes_no_t"},
    "v22.7.1": {"system_ein_aus_t", "system_yes_no_t"},
    "v24.7.1": set(),
    "v25.4.0": {"system_ein_aus_t", "system_yes_no_t"},
    "v25.7.1": {"system_ein_aus_t", "system_yes_no_t"},
}
LEGACY_TREE_FILE = Path("v25.7.1/de/equipment/uebergabestation.json")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_registers(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("registers", data.get("universal_registers", []))


class RegisterConfigurationTests(unittest.TestCase):
    """Validate entity IDs in every shipped register map."""

    def test_entity_ids_are_unique_in_each_register_file(self) -> None:
        roots = [
            CONFIG_ROOT,
            PROJECT_ROOT / "modbusinfoConverter" / "config" / "versions",
        ]
        errors = []

        for root in roots:
            for path in root.rglob("*.json"):
                registers = _load_registers(path)
                seen: dict[str, int] = {}
                for register in registers:
                    entity_id = register.get("entity_id")
                    address = register.get("starting_address")
                    if entity_id in seen:
                        errors.append(
                            f"{path.relative_to(PROJECT_ROOT)}: {entity_id} at "
                            f"{seen[entity_id]} and {address}"
                        )
                    elif entity_id:
                        seen[entity_id] = address

        self.assertEqual([], errors, "\n".join(errors))

    def test_runtime_duplicate_addresses_are_semantically_equivalent(self) -> None:
        """The address-keyed coordinator may only receive equivalent duplicates."""
        significant_fields = (
            "entity_id", "parameter", "data_type", "register_type", "type", "unit",
            "unit_value_table", "user_level", "expert_level", "access_level", "index",
        )
        errors = []

        for language_dir in sorted(CONFIG_ROOT.glob("v*/*")):
            if not language_dir.is_dir():
                continue
            common_files = [language_dir / "modbus_registers.json"]
            common_files.extend(
                path
                for path in sorted((language_dir / "equipment").glob("*.json"))
                if path.relative_to(CONFIG_ROOT) != LEGACY_TREE_FILE
            )

            # A real coordinator loads one device map at a time, so intentionally
            # overlapping device maps are not treated as runtime collisions.
            for device_file in sorted((language_dir / "devices").glob("*.json")):
                by_address: dict[object, list[tuple[Path, dict]]] = defaultdict(list)
                for path in [*common_files, device_file]:
                    for register in _load_registers(path):
                        by_address[register.get("starting_address")].append((path, register))

                for address, definitions in by_address.items():
                    if len(definitions) < 2:
                        continue
                    signatures = {
                        tuple(register.get(field) for field in significant_fields)
                        for _path, register in definitions
                    }
                    if len(signatures) > 1:
                        details = "; ".join(
                            f"{path.relative_to(language_dir)}: "
                            f"{register.get('entity_id')!r}/{register.get('parameter')!r}"
                            for path, register in definitions
                        )
                        errors.append(
                            f"{language_dir.relative_to(CONFIG_ROOT)} address {address}: {details}"
                        )

        self.assertEqual([], errors, "\n".join(errors))

    def test_converter_tree_matches_integration_semantics(self) -> None:
        """Detect drift from converter output while documenting identity exceptions."""
        integration_files = {
            path.relative_to(CONFIG_ROOT)
            for path in CONFIG_ROOT.rglob("*.json")
        }
        converter_files = {
            path.relative_to(CONVERTER_CONFIG_ROOT)
            for path in CONVERTER_CONFIG_ROOT.rglob("*.json")
        }

        self.assertEqual(
            {LEGACY_TREE_FILE}, integration_files - converter_files,
            "Unexpected integration-only config files",
        )
        self.assertEqual(
            set(), converter_files - integration_files,
            "Unexpected converter-only config files",
        )

        # The legacy German filename is unused by the manager (which uses the
        # canonical English filename) but remains checked in for compatibility.
        legacy_registers = _load_registers(CONFIG_ROOT / LEGACY_TREE_FILE)
        canonical_registers = _load_registers(
            CONVERTER_CONFIG_ROOT / LEGACY_TREE_FILE.with_name("transfer_station.json")
        )
        self.assertEqual(len(legacy_registers), len(canonical_registers))
        for legacy, canonical in zip(legacy_registers, canonical_registers):
            legacy = dict(legacy)
            canonical = dict(canonical)
            # The unused legacy file retains its historic ugs_* IDs; its
            # addresses and register semantics must still mirror the canonical file.
            legacy.pop("entity_id", None)
            canonical.pop("entity_id", None)
            self.assertEqual(legacy, canonical)

        errors = []
        for relative_path in sorted(integration_files & converter_files):
            integration_data = json.loads((CONFIG_ROOT / relative_path).read_text(encoding="utf-8"))
            converter_data = json.loads(
                (CONVERTER_CONFIG_ROOT / relative_path).read_text(encoding="utf-8")
            )

            if relative_path.name == "value_tables.json":
                integration_tables = integration_data["value_tables"]
                converter_tables = converter_data["value_tables"]
                extra_tables = set(integration_tables) - set(converter_tables)
                expected_extra_tables = INTENTIONAL_VALUE_TABLE_ADDITIONS_BY_VERSION[
                    relative_path.parts[0]
                ]
                if extra_tables != expected_extra_tables:
                    errors.append(
                        f"{relative_path}: unexpected extra value tables {sorted(extra_tables)}"
                    )
                if {
                    key: value for key, value in integration_tables.items()
                    if key not in expected_extra_tables
                } != converter_tables:
                    errors.append(f"{relative_path}: value table content differs")
                continue

            integration_registers = _load_registers(CONFIG_ROOT / relative_path)
            converter_registers = _load_registers(CONVERTER_CONFIG_ROOT / relative_path)
            if len(integration_registers) != len(converter_registers):
                errors.append(f"{relative_path}: register count differs")
                continue
            for number, (integration_register, converter_register) in enumerate(
                zip(integration_registers, converter_registers)
            ):
                if integration_register == converter_register:
                    continue
                integration_without_id = dict(integration_register)
                converter_without_id = dict(converter_register)
                integration_id = integration_without_id.pop("entity_id", None)
                converter_id = converter_without_id.pop("entity_id", None)
                if (
                    integration_without_id != converter_without_id
                    or (integration_id, converter_id) not in INTENTIONAL_ENTITY_ID_OVERRIDES
                ):
                    errors.append(
                        f"{relative_path} register {number}: "
                        f"{integration_register!r} != {converter_register!r}"
                    )

        self.assertEqual([], errors, "\n".join(errors))

    def test_selected_device_maps_have_no_cross_file_id_collisions(self) -> None:
        errors = []

        for language_dir in CONFIG_ROOT.glob("v*/*"):
            if not language_dir.is_dir():
                continue
            common_files = [language_dir / "modbus_registers.json"]
            common_files.extend((language_dir / "equipment").glob("*.json"))

            for device_file in (language_dir / "devices").glob("*.json"):
                ids: dict[str, set[int]] = defaultdict(set)
                for path in [*common_files, device_file]:
                    for register in _load_registers(path):
                        if register.get("entity_id"):
                            ids[register["entity_id"]].add(register["starting_address"])

                for entity_id, addresses in ids.items():
                    if len(addresses) > 1:
                        errors.append(
                            f"{language_dir.relative_to(CONFIG_ROOT)}/{device_file.name}: "
                            f"{entity_id} -> {sorted(addresses)}"
                        )

        self.assertEqual([], errors, "\n".join(errors))


class EquipmentSelectionTests(unittest.TestCase):
    """Cover data-driven equipment prefixes and instance selection."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.previous_aiofiles = sys.modules.get("aiofiles")
        sys.modules["aiofiles"] = types.SimpleNamespace(open=None)
        cls.manager_module = _load_module(
            "kwb_register_manager_test",
            INTEGRATION_ROOT / "async_modular_register_manager.py",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        sys.modules.pop("kwb_register_manager_test", None)
        if cls.previous_aiofiles is None:
            sys.modules.pop("aiofiles", None)
        else:
            sys.modules["aiofiles"] = cls.previous_aiofiles

    def test_first_available_circulation_slot_is_selected(self) -> None:
        cases = [
            ("v21.4.0", "de", "Zirk 1"),
            ("v21.4.0", "en", "Circ 1"),
            ("v25.4.0", "de", "Zirk 0"),
            ("v25.4.0", "en", "Circ 0"),
        ]

        for version, language, expected_index in cases:
            with self.subTest(version=version, language=language):
                config_dir = CONFIG_ROOT / version / language
                registers = _load_registers(
                    config_dir / "equipment" / "circulation.json"
                )
                manager = self.manager_module.AsyncModularRegisterManager(
                    config_path=str(config_dir), language=language
                )
                manager._equipment_cache["circulation"] = registers

                selected = asyncio.run(
                    manager.get_equipment_registers(
                        "circulation", "UserLevel", count=1
                    )
                )

                self.assertTrue(selected)
                self.assertEqual({expected_index}, {reg["index"] for reg in selected})

    def test_every_shipped_equipment_prefix_selects_first_instance(self) -> None:
        errors = []

        for language_dir in sorted(CONFIG_ROOT.glob("v*/*")):
            if not language_dir.is_dir():
                continue
            language = language_dir.name

            for equipment_key, config in (
                self.manager_module.AsyncModularRegisterManager.EQUIPMENT_KEY_CONFIG.items()
            ):
                path = language_dir / "equipment" / config["filename"]
                if not path.exists():
                    continue

                source_registers = _load_registers(path)
                manager = self.manager_module.AsyncModularRegisterManager(
                    config_path=str(language_dir), language=language
                )
                manager._equipment_cache[equipment_key] = source_registers
                selected = asyncio.run(
                    manager.get_equipment_registers(
                        equipment_key, "UserLevel", count=1
                    )
                )

                source_prefixes = {
                    register["index"].split(" ", 1)[0]
                    for register in source_registers
                    if " " in register.get("index", "")
                }
                selected_prefixes = {
                    register["index"].split(" ", 1)[0]
                    for register in selected
                    if " " in register.get("index", "")
                }
                if not selected or source_prefixes != selected_prefixes:
                    errors.append(
                        f"{language_dir.relative_to(CONFIG_ROOT)}/{equipment_key}: "
                        f"{source_prefixes} -> {selected_prefixes}"
                    )

        self.assertEqual([], errors, "\n".join(errors))

    def test_english_equipment_aliases_and_transfer_stations(self) -> None:
        config_dir = CONFIG_ROOT / "v25.4.0" / "en"
        expected = {
            "boiler_sequence": {"B 1"},
            "dhw_storage": {"DHWC 1"},
            "heat_meters": {"HQM 0"},
            "buffer_storage": {"BUF 0", "FP 0"},
            "transfer_stations": {"TS 1"},
        }

        for equipment_key, expected_indices in expected.items():
            with self.subTest(equipment_key=equipment_key):
                config = (
                    self.manager_module.AsyncModularRegisterManager
                    .EQUIPMENT_KEY_CONFIG[equipment_key]
                )
                source_registers = _load_registers(
                    config_dir / "equipment" / config["filename"]
                )
                manager = self.manager_module.AsyncModularRegisterManager(
                    config_path=str(config_dir), language="en"
                )
                manager._equipment_cache[equipment_key] = source_registers
                selected = asyncio.run(
                    manager.get_equipment_registers(
                        equipment_key, "UserLevel", count=1
                    )
                )

                self.assertEqual(
                    expected_indices,
                    {register.get("index", "") for register in selected if register.get("index")},
                )

    def test_feature_level_equipment_registers_are_not_dropped(self) -> None:
        """Blank indexes are feature-level entries, not missing equipment slots."""
        for version, language in (("v21.4.0", "de"), ("v25.7.1", "en")):
            with self.subTest(version=version, language=language):
                config_dir = CONFIG_ROOT / version / language
                source_registers = _load_registers(
                    config_dir / "equipment" / "boiler_sequence.json"
                )
                manager = self.manager_module.AsyncModularRegisterManager(
                    config_path=str(config_dir), language=language
                )
                manager._equipment_cache["boiler_sequence"] = source_registers
                selected = asyncio.run(
                    manager.get_equipment_registers(
                        "boiler_sequence", "UserLevel", count=1
                    )
                )

                feature_level_addresses = {
                    register["starting_address"]
                    for register in source_registers
                    if not register.get("index")
                    and "read" in register.get("user_level", "").lower()
                }
                self.assertTrue(feature_level_addresses)
                self.assertTrue(
                    feature_level_addresses.issubset(
                        {register["starting_address"] for register in selected}
                    )
                )

    def test_shipped_equipment_indexes_are_instance_indexes_or_blank(self) -> None:
        """Non-blank malformed indexes would otherwise hide equipment entities."""
        errors = []
        for path in sorted(CONFIG_ROOT.glob("v*/*/equipment/*.json")):
            for register in _load_registers(path):
                index = register.get("index", "")
                if not index:
                    continue
                if (
                    self.manager_module.AsyncModularRegisterManager
                    ._parse_equipment_index(index)
                    is None
                ):
                    errors.append(
                        f"{path.relative_to(CONFIG_ROOT)} address "
                        f"{register.get('starting_address')}: {index!r}"
                    )
        self.assertEqual([], errors, "\n".join(errors))

    def test_address_zero_is_valid_and_source_registers_are_not_mutated(self) -> None:
        manager = self.manager_module.AsyncModularRegisterManager()
        source_registers = [
            {"starting_address": 0, "user_level": "read"},
            {"starting_address": "0", "user_level": "read"},
            {"starting_address": 42, "user_level": "read"},
            {"starting_address": "43", "user_level": "read"},
            {"starting_address": None, "user_level": "read"},
            {"starting_address": "not-an-address", "user_level": "read"},
        ]
        manager._universal_registers = source_registers

        selected = manager.get_registers_for_access_level("UserLevel")

        self.assertEqual([0, 0, 42, 43], [reg["starting_address"] for reg in selected])
        self.assertEqual("0", source_registers[1]["starting_address"])
        self.assertEqual("43", source_registers[3]["starting_address"])

    def test_runtime_entity_id_collisions_are_repaired_deterministically(self) -> None:
        manager = self.manager_module.AsyncModularRegisterManager()
        manager._initialized = True
        manager._universal_registers = [
            {"starting_address": 10, "entity_id": "shared", "name": "First", "user_level": "read"},
        ]
        manager._device_cache["KWB Easyfire"] = [
            {"starting_address": 20, "entity_id": "shared", "name": "Second", "user_level": "read"},
            # This collides with the fallback above and must get a distinct ID.
            {
                "starting_address": 30,
                "entity_id": "shared_register_20",
                "name": "Third",
                "user_level": "read",
            },
        ]

        with self.assertLogs(self.manager_module.__name__, "WARNING") as logs:
            first_run = asyncio.run(
                manager.get_all_registers("UserLevel", device_type="KWB Easyfire")
            )
            second_run = asyncio.run(
                manager.get_all_registers("UserLevel", device_type="KWB Easyfire")
            )

        self.assertEqual([10, 20, 30], [reg["starting_address"] for reg in first_run])
        self.assertEqual(
            ["shared", "shared_register_20", "shared_register_20_register_30"],
            [reg["entity_id"] for reg in first_run],
        )
        self.assertEqual(3, len({reg["entity_id"] for reg in first_run}))
        self.assertEqual(first_run, second_run)
        self.assertIn("using 'shared_register_20'", "\n".join(logs.output))
        self.assertIn("using 'shared_register_20_register_30'", "\n".join(logs.output))
        # The repair must not rewrite source configuration that may be reused.
        self.assertEqual("shared", manager._device_cache["KWB Easyfire"][0]["entity_id"])

    def test_conflicting_duplicate_addresses_are_reported_and_deduplicated(self) -> None:
        manager = self.manager_module.AsyncModularRegisterManager()
        manager._initialized = True
        manager._universal_registers = [
            {
                "starting_address": 10,
                "entity_id": "first",
                "parameter": "A",
                "name": "First",
                "user_level": "read",
            },
        ]
        manager._device_cache["KWB Easyfire"] = [
            {
                "starting_address": 10,
                "entity_id": "second",
                "parameter": "B",
                "name": "Second",
                "user_level": "read",
            },
        ]

        with self.assertLogs(self.manager_module.__name__, "WARNING") as logs:
            registers = asyncio.run(
                manager.get_all_registers("UserLevel", device_type="KWB Easyfire")
            )

        self.assertEqual(["first"], [register["entity_id"] for register in registers])
        self.assertIn("conflicting duplicate register at address 10", "\n".join(logs.output))


class IdentityCompatibilityTests(unittest.TestCase):
    """Execute the production identity paths without a Home Assistant install."""

    def test_existing_noncolliding_entity_and_unique_ids_are_unchanged(self) -> None:
        module_names = (
            "custom_components",
            "custom_components.kwb_heating",
            "custom_components.kwb_heating.const",
            "custom_components.kwb_heating.data_conversion",
            "custom_components.kwb_heating.modbus_client",
            "custom_components.kwb_heating.async_modular_register_manager",
            "custom_components.kwb_heating.version_manager",
            "custom_components.kwb_heating.language_manager",
            "homeassistant",
            "homeassistant.config_entries",
            "homeassistant.const",
            "homeassistant.core",
            "homeassistant.helpers",
            "homeassistant.helpers.update_coordinator",
        )
        saved_modules = {name: sys.modules.get(name) for name in module_names}

        try:
            custom_components = types.ModuleType("custom_components")
            custom_components.__path__ = []
            integration_package = types.ModuleType("custom_components.kwb_heating")
            integration_package.__path__ = [str(INTEGRATION_ROOT)]
            sys.modules["custom_components"] = custom_components
            sys.modules["custom_components.kwb_heating"] = integration_package

            homeassistant = types.ModuleType("homeassistant")
            config_entries = types.ModuleType("homeassistant.config_entries")
            config_entries.ConfigEntry = object
            ha_const = types.ModuleType("homeassistant.const")
            ha_const.CONF_HOST = "host"
            ha_const.CONF_PORT = "port"
            ha_core = types.ModuleType("homeassistant.core")
            ha_core.HomeAssistant = object
            ha_helpers = types.ModuleType("homeassistant.helpers")
            ha_coordinator = types.ModuleType("homeassistant.helpers.update_coordinator")

            class DataUpdateCoordinator:
                pass

            class CoordinatorEntity:
                def __init__(self, coordinator):
                    self.coordinator = coordinator

            ha_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
            ha_coordinator.CoordinatorEntity = CoordinatorEntity
            ha_coordinator.UpdateFailed = RuntimeError
            sys.modules.update({
                "homeassistant": homeassistant,
                "homeassistant.config_entries": config_entries,
                "homeassistant.const": ha_const,
                "homeassistant.core": ha_core,
                "homeassistant.helpers": ha_helpers,
                "homeassistant.helpers.update_coordinator": ha_coordinator,
            })

            constants = types.ModuleType("custom_components.kwb_heating.const")
            for name, value in {
                "DOMAIN": "kwb_heating", "CONF_CONNECTION_TYPE": "connection_type",
                "CONF_SLAVE_ID": "slave_id", "CONF_ACCESS_LEVEL": "access_level",
                "CONF_UPDATE_INTERVAL": "update_interval", "CONF_DEVICE_TYPE": "device_type",
                "CONF_DEVICE_NAME": "device_name", "CONF_SERIAL_PORT": "serial_port",
                "CONF_BAUDRATE": "baudrate", "CONF_PARITY": "parity",
                "CONF_STOPBITS": "stopbits", "CONF_BYTESIZE": "bytesize",
                "EQUIPMENT_KEYS": [], "CONNECTION_TYPE_TCP": "tcp",
                "CONNECTION_TYPE_SERIAL": "serial", "DEFAULT_PORT": 502,
                "DEFAULT_UPDATE_INTERVAL": 30, "DEFAULT_BAUDRATE": 19200,
                "DEFAULT_PARITY": "N", "DEFAULT_STOPBITS": 1, "DEFAULT_BYTESIZE": 8,
            }.items():
                setattr(constants, name, value)
            sys.modules[constants.__name__] = constants

            for module_name, class_name in (
                ("custom_components.kwb_heating.data_conversion", "KWBDataConverter"),
                ("custom_components.kwb_heating.modbus_client", "KWBModbusClient"),
                (
                    "custom_components.kwb_heating.async_modular_register_manager",
                    "AsyncModularRegisterManager",
                ),
                ("custom_components.kwb_heating.version_manager", "VersionManager"),
                ("custom_components.kwb_heating.language_manager", "LanguageManager"),
            ):
                module = types.ModuleType(module_name)
                setattr(module, class_name, object)
                sys.modules[module_name] = module

            coordinator_module = _load_module(
                "custom_components.kwb_heating.coordinator_identity_test",
                INTEGRATION_ROOT / "coordinator.py",
            )
            entity_module = _load_module(
                "custom_components.kwb_heating.entity_identity_test",
                INTEGRATION_ROOT / "entity.py",
            )
            coordinator = types.SimpleNamespace(
                connection_type="tcp",
                host="192.0.2.10",
                slave_id=1,
                config={},
                device_name_prefix="KWB",
                device_info={},
                last_update_success=True,
                data={},
                generate_entity_unique_id=lambda register: (
                    coordinator_module.KWBDataUpdateCoordinator.generate_entity_unique_id(
                        coordinator, register
                    )
                ),
                sanitize_for_entity_id=lambda value: value.lower(),
            )
            register = {
                "starting_address": 8192,
                "entity_id": "software_major",
                "name": "Software (major)",
            }

            entity = entity_module.KWBBaseEntity(coordinator, register, "sensor")

            self.assertEqual("sensor.kwb_software_major", entity.entity_id)
            self.assertEqual("192.0.2.10_1_software_major", entity._attr_unique_id)
        finally:
            sys.modules.pop("custom_components.kwb_heating.coordinator_identity_test", None)
            sys.modules.pop("custom_components.kwb_heating.entity_identity_test", None)
            for name, module in saved_modules.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module


class WiringRegressionTests(unittest.TestCase):
    """Cover integration wiring without importing Home Assistant."""

    def test_transfer_stations_are_a_canonical_equipment_key(self) -> None:
        tree = ast.parse((INTEGRATION_ROOT / "const.py").read_text(encoding="utf-8"))
        equipment_keys = next(
            node.value
            for node in tree.body
            if (
                isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name)
                    and target.id == "EQUIPMENT_KEYS"
                    for target in node.targets
                )
            )
            or (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == "EQUIPMENT_KEYS"
            )
        )
        key_names = {
            element.id
            for element in equipment_keys.elts
            if isinstance(element, ast.Name)
        }
        self.assertIn("CONF_TRANSFER_STATIONS", key_names)

    def test_duplicate_abort_is_not_swallowed_by_config_flow(self) -> None:
        tree = ast.parse(
            (INTEGRATION_ROOT / "config_flow.py").read_text(encoding="utf-8")
        )
        functions = {
            node.name: node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        for function_name in ("_async_step_network", "async_step_serial"):
            function = functions[function_name]
            abort_calls = [
                node
                for node in ast.walk(function)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "_abort_if_unique_id_configured"
            ]
            swallowed_calls = {
                call
                for try_node in ast.walk(function)
                if isinstance(try_node, ast.Try)
                for call in ast.walk(try_node)
                if call in abort_calls
            }

            self.assertEqual(1, len(abort_calls), function_name)
            self.assertFalse(swallowed_calls, function_name)


class RtuOverTcpTests(unittest.TestCase):
    """Ensure RTU over TCP uses a TCP transport with an RTU framer."""

    def test_rtu_over_tcp_client_uses_rtu_framer(self) -> None:
        saved_modules = {
            name: sys.modules.get(name)
            for name in (
                "custom_components",
                "custom_components.kwb_heating",
                "custom_components.kwb_heating.const",
                "custom_components.kwb_heating.modbus_client",
                "pymodbus",
                "pymodbus.client",
                "pymodbus.exceptions",
                "pymodbus.framer",
            )
        }

        try:
            package = types.ModuleType("custom_components")
            package.__path__ = []
            sys.modules["custom_components"] = package
            integration_package = types.ModuleType("custom_components.kwb_heating")
            integration_package.__path__ = [str(INTEGRATION_ROOT)]
            sys.modules["custom_components.kwb_heating"] = integration_package

            constants = types.ModuleType("custom_components.kwb_heating.const")
            constants.CONNECTION_TYPE_TCP = "tcp"
            constants.CONNECTION_TYPE_RTU_TCP = "rtu_tcp"
            constants.CONNECTION_TYPE_SERIAL = "serial"
            constants.DEFAULT_BAUDRATE = 19200
            constants.DEFAULT_PARITY = "N"
            constants.DEFAULT_STOPBITS = 1
            constants.DEFAULT_BYTESIZE = 8
            sys.modules["custom_components.kwb_heating.const"] = constants

            class FramerType(enum.Enum):
                RTU = "rtu"

            class FakeTcpClient:
                def __init__(self, **kwargs):
                    self.kwargs = kwargs

            class FakeModbusException(Exception):
                pass

            pymodbus = types.ModuleType("pymodbus")
            pymodbus.FramerType = FramerType
            pymodbus_client = types.ModuleType("pymodbus.client")
            pymodbus_client.AsyncModbusTcpClient = FakeTcpClient
            pymodbus_exceptions = types.ModuleType("pymodbus.exceptions")
            pymodbus_exceptions.ModbusException = FakeModbusException
            sys.modules["pymodbus"] = pymodbus
            sys.modules["pymodbus.client"] = pymodbus_client
            sys.modules["pymodbus.exceptions"] = pymodbus_exceptions

            module = _load_module(
                "custom_components.kwb_heating.modbus_client",
                INTEGRATION_ROOT / "modbus_client.py",
            )
            client = module.KWBModbusClient(
                connection_type="rtu_tcp", host="127.0.0.1", port=4001
            )._create_client()

            self.assertEqual("127.0.0.1", client.kwargs["host"])
            self.assertEqual(4001, client.kwargs["port"])
            self.assertIs(FramerType.RTU, client.kwargs["framer"])

            # pymodbus 3.6-3.8 exposes Framer instead of FramerType.
            del pymodbus.FramerType
            pymodbus.Framer = FramerType
            self.assertIs(FramerType.RTU, module._get_rtu_framer())

            # pymodbus 3.5 expects the concrete RTU framer class.
            del pymodbus.Framer

            class LegacyRtuFramer:
                pass

            pymodbus_framer = types.ModuleType("pymodbus.framer")
            pymodbus_framer.ModbusRtuFramer = LegacyRtuFramer
            sys.modules["pymodbus.framer"] = pymodbus_framer
            self.assertIs(LegacyRtuFramer, module._get_rtu_framer())

            class SlaveOnlyClient:
                def __init__(self):
                    self.read_kwargs = []
                    self.write_kwargs = []

                async def read_holding_registers(
                    self, address, *, count, **kwargs
                ):
                    self.read_kwargs.append(kwargs)
                    if "slave" not in kwargs:
                        raise TypeError("slave keyword required")
                    return "read"

                async def write_register(self, address, value, **kwargs):
                    self.write_kwargs.append(kwargs)
                    if "slave" not in kwargs:
                        raise TypeError("slave keyword required")
                    return "write"

            fake_client = SlaveOnlyClient()
            kwb_client = module.KWBModbusClient(slave_id=7)
            kwb_client._client = fake_client
            kwb_client._unit_kwarg = "unit"

            self.assertEqual(
                "read",
                asyncio.run(
                    kwb_client._invoke_read(
                        "read_holding_registers", address=100, count=1
                    )
                ),
            )
            self.assertEqual(
                "read",
                asyncio.run(
                    kwb_client._invoke_read(
                        "read_holding_registers", address=101, count=1
                    )
                ),
            )
            self.assertEqual(
                [{"unit": 7}, {"slave": 7}, {"slave": 7}],
                fake_client.read_kwargs,
            )

            kwb_client._unit_kwarg = "unit"
            self.assertEqual(
                "write",
                asyncio.run(
                    kwb_client._invoke_write(
                        "write_register", address=100, value=1
                    )
                ),
            )
            self.assertEqual(
                "write",
                asyncio.run(
                    kwb_client._invoke_write(
                        "write_register", address=101, value=0
                    )
                ),
            )
            self.assertEqual(
                [{"unit": 7}, {"slave": 7}, {"slave": 7}],
                fake_client.write_kwargs,
            )
        finally:
            for name, previous in saved_modules.items():
                if previous is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = previous


if __name__ == "__main__":
    unittest.main()
