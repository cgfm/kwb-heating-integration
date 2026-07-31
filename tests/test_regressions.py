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
                    {register["index"] for register in selected},
                )


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
