"""Regression tests for configuration and connection bugs."""
from __future__ import annotations

import asyncio
import ast
from collections import defaultdict
import enum
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
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
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def _load_registers(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("registers", data.get("universal_registers", []))


class RegisterConfigurationTests(unittest.TestCase):
    """Validate finalized production config independently of converter output."""

    def test_entity_ids_are_unique_in_each_register_file(self) -> None:
        errors = []

        for path in CONFIG_ROOT.rglob("*.json"):
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

        for version_dir in sorted(CONFIG_ROOT.glob("v*")):
            if not version_dir.is_dir():
                continue
            common_files = [version_dir / "modbus_registers.json"]
            common_files.extend(
                path for path in sorted((version_dir / "equipment").glob("*.json"))
            )

            # A real coordinator loads one device map at a time, so intentionally
            # overlapping device maps are not treated as runtime collisions.
            for device_file in sorted((version_dir / "devices").glob("*.json")):
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
                            f"{path.relative_to(version_dir)}: "
                            f"{register.get('entity_id')!r}/{register.get('parameter')!r}"
                            for path, register in definitions
                        )
                        errors.append(
                            f"{version_dir.relative_to(CONFIG_ROOT)} address {address}: {details}"
                        )

        self.assertEqual([], errors, "\n".join(errors))

    def test_canonical_tree_passes_standalone_validation(self) -> None:
        from modbusinfoConverter.config_validation import validate_config_tree

        self.assertEqual([], validate_config_tree(CONFIG_ROOT))

    def test_referenced_value_tables_exist_in_canonical_config(self) -> None:
        errors = []
        for version_dir in sorted(CONFIG_ROOT.glob("v*")):
            value_tables = json.loads(
                (version_dir / "value_tables.json").read_text(encoding="utf-8")
            )["value_tables"]
            references = {
                register["unit_value_table"]
                for path in version_dir.rglob("*.json")
                for register in _load_registers(path)
                if str(register.get("unit_value_table", "")).endswith("_t")
            }
            missing = references - set(value_tables)
            if missing:
                errors.append(f"{version_dir}: {sorted(missing)}")
        self.assertEqual([], errors, "\n".join(errors))

    def test_only_explicit_fields_are_localized(self) -> None:
        localized_fields = {"name", "index"}
        errors = []
        for path in CONFIG_ROOT.rglob("*.json"):
            for register in _load_registers(path):
                if not isinstance(register.get("name"), dict):
                    errors.append(f"{path}: name is not localized")
                for field, value in register.items():
                    if isinstance(value, dict) and field not in localized_fields:
                        errors.append(f"{path}: structural field {field} is localized")
        self.assertEqual([], errors, "\n".join(errors))

    def test_published_entity_id_examples_remain_finalized(self) -> None:
        expected = {
            "boiler_pump_percent",
            "boiler_temperature_setpoint_setting",
            "full_load_hours_pm",
        }
        ids = {
            register.get("entity_id")
            for path in (CONFIG_ROOT / "v22.7.1").rglob("*.json")
            for register in _load_registers(path)
        }
        self.assertTrue(expected.issubset(ids))

    def test_selected_device_maps_have_no_cross_file_id_collisions(self) -> None:
        errors = []

        for version_dir in CONFIG_ROOT.glob("v*"):
            if not version_dir.is_dir():
                continue
            common_files = [version_dir / "modbus_registers.json"]
            common_files.extend((version_dir / "equipment").glob("*.json"))

            for device_file in (version_dir / "devices").glob("*.json"):
                ids: dict[str, set[int]] = defaultdict(set)
                for path in [*common_files, device_file]:
                    for register in _load_registers(path):
                        if register.get("entity_id"):
                            ids[register["entity_id"]].add(register["starting_address"])

                for entity_id, addresses in ids.items():
                    if len(addresses) > 1:
                        errors.append(
                            f"{version_dir.relative_to(CONFIG_ROOT)}/{device_file.name}: "
                            f"{entity_id} -> {sorted(addresses)}"
                        )

        self.assertEqual([], errors, "\n".join(errors))


class ConverterWorkflowTests(unittest.TestCase):
    """Cover English template IDs, review reporting, and safe finalization."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.converter_module = _load_module(
            "kwb_converter_test",
            PROJECT_ROOT / "modbusinfoConverter" / "convert_modbusinfo.py",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        sys.modules.pop("kwb_converter_test", None)

    def _converter(self, root: Path):
        return self.converter_module.ModbusInfoConverter(root, root / "output")

    @staticmethod
    def _raw_register(address: int, name: str, parameter: str, **extra) -> dict:
        register = {
            "StartingAddress": address,
            "Name": name,
            "Functions": "04",
            "Type": "u16",
            "UserLevel": "read",
            "ExpertLevel": "read",
            "Parameter": parameter,
        }
        register.update(extra)
        return register

    def test_percent_is_preserved_as_english_entity_id_meaning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            converter = self._converter(Path(temp_dir))
            plain = converter.normalize_register(
                self._raw_register(1, "Boiler pump", "KSM.pump")
            )
            percent = converter.normalize_register(
                self._raw_register(2, "Boiler pump %", "KSM.pump_percent")
            )

        self.assertEqual("boiler_pump", plain["entity_id"])
        self.assertEqual("boiler_pump_percent", percent["entity_id"])
        self.assertEqual([], converter.review_items)

    def test_localized_register_uses_matched_english_name_and_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            converter = self._converter(Path(temp_dir))
            converter._current_language = "de"
            register = converter.normalize_register(
                self._raw_register(
                    20,
                    "Kesselpumpe %",
                    "KSM.Kesselpumpe.Steuerstufe",
                    Index="PUF 0",
                ),
                {20: {"name": "Boiler pump %", "index": "BUF 0"}},
            )

        self.assertEqual("buf_1_boiler_pump_percent", register["entity_id"])
        self.assertNotIn("kesselpumpe", register["entity_id"])
        self.assertNotIn("steuerstufe", register["entity_id"])

    def test_missing_english_match_creates_review_id_not_german_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            converter = self._converter(Path(temp_dir))
            converter._current_version = "25.7.1"
            converter._current_language = "de"
            register = converter.normalize_register(
                self._raw_register(
                    21,
                    "Kesselpumpe Steuerstufe",
                    "KSM.Kesselpumpe.Steuerstufe",
                ),
                {},
                source_name="KWB Easyfire",
            )

        self.assertEqual("review_register_21", register["entity_id"])
        self.assertNotIn("kesselpumpe", register["entity_id"])
        self.assertEqual("ambiguous_entity_id", converter.review_items[0]["kind"])
        self.assertTrue(converter.review_items[0]["blocking"])

    def test_read_write_collision_gets_deterministic_english_setting_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            converter = self._converter(Path(temp_dir))
            registers = [
                {
                    "starting_address": 10,
                    "name": "Boiler temperature setpoint",
                    "entity_id": "boiler_temperature_setpoint",
                    "user_level": "read",
                    "parameter": "KSM.actual",
                },
                {
                    "starting_address": 11,
                    "name": "Boiler temperature setpoint",
                    "entity_id": "boiler_temperature_setpoint",
                    "user_level": "readwrite",
                    "parameter": "KSM.Kesseltemp_Soll_1",
                },
            ]
            converter._make_entity_ids_unique(registers, "KWB Easyfire")

        self.assertEqual("boiler_temperature_setpoint_setting", registers[1]["entity_id"])
        self.assertEqual([], converter.review_items)

    def test_ambiguous_collision_is_reported_without_parameter_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            converter = self._converter(Path(temp_dir))
            converter._current_version = "25.7.1"
            converter._current_language = "en"
            converter._current_source_file = "ModbusInfo-en-V25.7.1.xlsx"
            registers = [
                {
                    "starting_address": 100,
                    "name": "Full load hours",
                    "entity_id": "full_load_hours",
                    "user_level": "read",
                    "parameter": "KSM.Betriebsstunden_Summe",
                },
                {
                    "starting_address": 101,
                    "name": "Full load hours",
                    "entity_id": "full_load_hours",
                    "user_level": "read",
                    "parameter": "KSM.Betriebsminuten_Summe",
                },
            ]
            with self.assertLogs(self.converter_module.__name__, "WARNING") as logs:
                converter._make_entity_ids_unique(registers, "KWB Combifire")
            report_path = converter.write_review_report()
            report = json.loads(report_path.read_text(encoding="utf-8"))

        candidate = registers[1]["entity_id"]
        self.assertEqual("full_load_hours_review_register_101", candidate)
        self.assertNotIn("betriebsminuten", candidate)
        self.assertTrue(report["review_required"])
        item = report["items"][0]
        self.assertEqual("25.7.1", item["firmware_version"])
        self.assertEqual("KWB Combifire", item["device_or_equipment"])
        self.assertEqual(101, item["address"])
        self.assertEqual("Full load hours", item["english_name"])
        self.assertEqual("KSM.Betriebsminuten_Summe", item["parameter"])
        self.assertIn("conflicting_entity", item)
        self.assertIn("requires review", "\n".join(logs.output))

    def test_required_boolean_value_tables_are_generated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            converter = self._converter(Path(temp_dir))
            tables = converter.ensure_required_value_tables({}, "en")

        self.assertEqual({"0": "Off", "1": "On"}, tables["system_ein_aus_t"])
        self.assertEqual({"0": "No", "1": "Yes"}, tables["system_yes_no_t"])

    def test_finalizer_preserves_published_ids_and_production_tables(self) -> None:
        from modbusinfoConverter.import_generated_config import build_finalized_version

        published_ids = (
            "boiler_pump_percent",
            "boiler_temperature_setpoint_setting",
            "full_load_hours_pm",
        )
        generated_ids = (
            "boiler_pump_kesselpumpe_steuerstufe",
            "boiler_temperature_setpoint_kesseltemp_soll_1",
            "full_load_hours_pm_betriebsminuten_summe",
        )
        parameters = ("KSM.pump", "KSM.setpoint", "KSM.full_load_minutes")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generated_root = root / "generated"
            canonical_root = root / "canonical"
            generated_dir = generated_root / "v1.0.0"
            canonical_dir = canonical_root / "v1.0.0"
            (generated_dir / "devices").mkdir(parents=True)
            (canonical_dir / "devices").mkdir(parents=True)
            generated_registers = [
                {
                    "starting_address": number,
                    "name": {"de": f"Register {number}", "en": f"Register {number}"},
                    "entity_id": generated_id,
                    "parameter": parameter,
                    "user_level": "read",
                }
                for number, generated_id, parameter in zip(
                    (10, 11, 12), generated_ids, parameters
                )
            ]
            generated_registers.append(
                {
                    "starting_address": 13,
                    "name": {"en": "New register"},
                    "entity_id": "new_register",
                    "parameter": "KSM.new",
                    "user_level": "read",
                }
            )
            canonical_registers = [
                {**register, "entity_id": published_id}
                for register, published_id in zip(
                    generated_registers[:3], published_ids
                )
            ]
            (generated_dir / "devices" / "kwb_test.json").write_text(
                json.dumps({"registers": generated_registers}), encoding="utf-8"
            )
            (canonical_dir / "devices" / "kwb_test.json").write_text(
                json.dumps({"registers": canonical_registers}), encoding="utf-8"
            )
            (generated_dir / "value_tables.json").write_text(
                json.dumps({"value_tables": {}}), encoding="utf-8"
            )
            finalized_tables = {
                "system_ein_aus_t": {
                    "0": {"de": "Aus", "en": "Off"},
                    "1": {"de": "Ein", "en": "On"},
                },
                "system_yes_no_t": {
                    "0": {"de": "Nein", "en": "No"},
                    "1": {"de": "Ja", "en": "Yes"},
                },
            }
            (canonical_dir / "value_tables.json").write_text(
                json.dumps({"value_tables": finalized_tables}), encoding="utf-8"
            )
            for directory in (generated_dir, canonical_dir):
                (directory / "alarm_codes.json").write_text(
                    json.dumps({"alarm_codes": []}), encoding="utf-8"
                )

            proposed, report = build_finalized_version(
                generated_root, canonical_root, "1.0.0"
            )

        registers = proposed[Path("devices/kwb_test.json")]["registers"]
        self.assertEqual(
            [*published_ids, "new_register"],
            [register["entity_id"] for register in registers],
        )
        tables = proposed[Path("value_tables.json")]["value_tables"]
        self.assertIn("system_ein_aus_t", tables)
        self.assertIn("system_yes_no_t", tables)
        self.assertEqual(3, report["summary"]["published_entity_ids_preserved"])
        self.assertEqual(1, report["summary"]["new_registers_added"])
        self.assertFalse(report["blocking_review_required"])


class FinalizerCompatibilityTests(unittest.TestCase):
    """Cover published-ID compatibility across canonical firmware versions."""

    @staticmethod
    def _write_version(root: Path, version: str, registers: list[dict]) -> None:
        version_dir = root / version
        device_dir = version_dir / "devices"
        device_dir.mkdir(parents=True)
        (device_dir / "kwb_test.json").write_text(
            json.dumps({"registers": registers}), encoding="utf-8"
        )
        (version_dir / "value_tables.json").write_text(
            json.dumps({"value_tables": {}}), encoding="utf-8"
        )
        (version_dir / "alarm_codes.json").write_text(
            json.dumps({"alarm_codes": []}), encoding="utf-8"
        )

    @staticmethod
    def _register(
        address: int,
        entity_id: str,
        parameter: str = "KSM.foo",
        **technical,
    ) -> dict:
        register = {
            "starting_address": address,
            "name": {"de": "Foo", "en": "Foo"},
            "entity_id": entity_id,
            "parameter": parameter,
            "data_type": "04",
            "type": "u16",
            "user_level": "read",
        }
        register.update(technical)
        return register

    def test_new_version_preserves_id_and_uses_all_generated_technical_data(self) -> None:
        from modbusinfoConverter.import_generated_config import build_finalized_version

        old = self._register(
            100,
            "pump_speed",
            min=0,
            max=100,
            unit="rpm",
            user_level="read",
        )
        generated = self._register(
            200,
            "pump_speed_generated",
            min=5,
            max=150,
            unit="percent",
            user_level="readwrite",
            type="u32",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generated_root = root / "generated"
            canonical_root = root / "canonical"
            self._write_version(canonical_root, "v1.0.0", [old])
            self._write_version(generated_root, "v2.0.0", [generated])

            proposed, report = build_finalized_version(
                generated_root, canonical_root, "2.0.0"
            )

        result = proposed[Path("devices/kwb_test.json")]["registers"][0]
        self.assertEqual({**generated, "entity_id": "pump_speed"}, result)
        self.assertEqual("v1.0.0", report["base_version"])
        self.assertEqual("automatic", report["baseline_selection"])
        action = next(item for item in report["items"] if item.get("action"))
        self.assertEqual("preserve_entity_id", action["action"])
        self.assertEqual("v2.0.0", action["target_version"])
        self.assertEqual("v1.0.0", action["base_version"])
        self.assertEqual("pump_speed", action["entity_id"])
        self.assertEqual(
            {"old": 100, "new": 200},
            action["technical_changes"]["starting_address"],
        )
        for field in ("min", "max", "unit", "user_level", "type"):
            self.assertIn(field, action["technical_changes"])
        self.assertFalse(report["blocking_review_required"])

    def test_explicit_base_version_selects_requested_canonical_history(self) -> None:
        from modbusinfoConverter.import_generated_config import build_finalized_version

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generated_root = root / "generated"
            canonical_root = root / "canonical"
            self._write_version(
                canonical_root,
                "v1.0.0",
                [self._register(100, "explicit_published")],
            )
            self._write_version(
                canonical_root,
                "v1.5.0",
                [self._register(100, "automatic_published")],
            )
            self._write_version(
                generated_root,
                "v2.0.0",
                [self._register(200, "generated_id")],
            )

            proposed, report = build_finalized_version(
                generated_root,
                canonical_root,
                "2.0.0",
                base_version="1.0.0",
            )

        result = proposed[Path("devices/kwb_test.json")]["registers"][0]
        self.assertEqual("explicit_published", result["entity_id"])
        self.assertEqual("v1.0.0", report["base_version"])
        self.assertEqual("explicit", report["baseline_selection"])

    def test_missing_explicit_base_version_fails_clearly(self) -> None:
        from modbusinfoConverter.import_generated_config import build_finalized_version

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generated_root = root / "generated"
            canonical_root = root / "canonical"
            self._write_version(
                generated_root,
                "v2.0.0",
                [self._register(200, "generated_id")],
            )

            with self.assertRaisesRegex(
                ValueError, "Canonical base version does not exist"
            ):
                build_finalized_version(
                    generated_root,
                    canonical_root,
                    "2.0.0",
                    base_version="1.0.0",
                )

    def test_automatic_base_is_highest_lower_semantic_version(self) -> None:
        from modbusinfoConverter.import_generated_config import build_finalized_version

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generated_root = root / "generated"
            canonical_root = root / "canonical"
            for version, entity_id in (
                ("v9.9.9", "id_9"),
                ("v10.0.0", "id_10"),
                ("v25.4.0", "id_25_4"),
                ("v25.7.1", "id_25_7"),
                ("v27.0.0", "newer_must_not_win"),
            ):
                self._write_version(
                    canonical_root, version, [self._register(100, entity_id)]
                )
            self._write_version(
                generated_root,
                "v26.6.1",
                [self._register(200, "generated_id")],
            )

            proposed, report = build_finalized_version(
                generated_root, canonical_root, "26.6.1"
            )

        result = proposed[Path("devices/kwb_test.json")]["registers"][0]
        self.assertEqual("id_25_7", result["entity_id"])
        self.assertEqual("v25.7.1", report["base_version"])

    def test_no_older_baseline_uses_generated_data_and_reports_it(self) -> None:
        from modbusinfoConverter.import_generated_config import build_finalized_version

        generated = self._register(200, "first_published_id")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generated_root = root / "generated"
            canonical_root = root / "canonical"
            self._write_version(
                canonical_root,
                "v3.0.0",
                [self._register(300, "newer_must_not_win")],
            )
            self._write_version(generated_root, "v2.0.0", [generated])

            proposed, report = build_finalized_version(
                generated_root, canonical_root, "2.0.0"
            )

        result = proposed[Path("devices/kwb_test.json")]["registers"][0]
        self.assertEqual(generated, result)
        self.assertIsNone(report["base_version"])
        self.assertEqual("none", report["baseline_selection"])
        self.assertTrue(
            any(item["kind"] == "no_compatibility_baseline" for item in report["items"])
        )
        self.assertFalse(report["blocking_review_required"])

    def test_ambiguous_baseline_match_blocks_write(self) -> None:
        from modbusinfoConverter.import_generated_config import build_finalized_version

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generated_root = root / "generated"
            canonical_root = root / "canonical"
            self._write_version(
                canonical_root,
                "v1.0.0",
                [
                    self._register(100, "published_one"),
                    self._register(101, "published_two"),
                ],
            )
            self._write_version(
                generated_root,
                "v2.0.0",
                [self._register(200, "generated_id")],
            )

            _proposed, report = build_finalized_version(
                generated_root, canonical_root, "2.0.0"
            )
            review_path = root / "review.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(
                        PROJECT_ROOT
                        / "modbusinfoConverter"
                        / "import_generated_config.py"
                    ),
                    "2.0.0",
                    "--generated-root",
                    str(generated_root),
                    "--canonical-root",
                    str(canonical_root),
                    "--base-version",
                    "1.0.0",
                    "--report",
                    str(review_path),
                    "--write",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertFalse((canonical_root / "v2.0.0").exists())

        self.assertTrue(report["blocking_review_required"])
        self.assertTrue(
            any(item["kind"] == "ambiguous_logical_match" for item in report["items"])
        )
        self.assertEqual(2, completed.returncode)
        self.assertIn("Refusing to write", completed.stdout)

    def test_changed_equipment_index_is_blocking_not_fuzzy_matched(self) -> None:
        from modbusinfoConverter.import_generated_config import build_finalized_version

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generated_root = root / "generated"
            canonical_root = root / "canonical"
            self._write_version(
                canonical_root,
                "v1.0.0",
                [
                    self._register(
                        100,
                        "published_id",
                        index={"de": "PUF 0", "en": "BUF 0"},
                        equipment_group="BUF",
                        equipment_instance=0,
                    )
                ],
            )
            self._write_version(
                generated_root,
                "v2.0.0",
                [
                    self._register(
                        200,
                        "generated_id",
                        index={"de": "PUF 1", "en": "BUF 1"},
                        equipment_group="BUF",
                        equipment_instance=1,
                    )
                ],
            )

            proposed, report = build_finalized_version(
                generated_root, canonical_root, "2.0.0"
            )

        result = proposed[Path("devices/kwb_test.json")]["registers"][0]
        self.assertEqual("generated_id", result["entity_id"])
        self.assertTrue(report["blocking_review_required"])
        self.assertTrue(
            any(
                item["kind"] == "incompatible_equipment_index_context"
                for item in report["items"]
            )
        )

    def test_existing_target_uses_generated_metadata_and_same_version_id(self) -> None:
        from modbusinfoConverter.import_generated_config import build_finalized_version

        old = self._register(100, "published_id", max=100)
        generated = self._register(200, "generated_id", max=150)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generated_root = root / "generated"
            canonical_root = root / "canonical"
            self._write_version(canonical_root, "v2.0.0", [old])
            self._write_version(generated_root, "v2.0.0", [generated])

            proposed, report = build_finalized_version(
                generated_root, canonical_root, "2.0.0"
            )

        result = proposed[Path("devices/kwb_test.json")]["registers"][0]
        self.assertEqual({**generated, "entity_id": "published_id"}, result)
        self.assertEqual("v2.0.0", report["base_version"])
        self.assertEqual("same_version", report["baseline_selection"])
        self.assertFalse(report["blocking_review_required"])

    def test_version_ordering_is_numeric_and_malformed_versions_fail(self) -> None:
        from modbusinfoConverter.import_generated_config import parse_firmware_version

        self.assertLess(
            parse_firmware_version("v25.7.1"), parse_firmware_version("v26.6.1")
        )
        self.assertLess(
            parse_firmware_version("v9.9.9"), parse_firmware_version("v10.0.0")
        )
        with self.assertRaisesRegex(ValueError, "Malformed firmware version"):
            parse_firmware_version("v25.7")


class MultilingualSchemaTests(unittest.TestCase):
    """Cover deterministic DE/EN merging and explicitly localized values."""

    @staticmethod
    def _source_register(address: int, name: str, entity_id: str = "foo") -> dict:
        return {
            "starting_address": address,
            "name": name,
            "entity_id": entity_id,
            "parameter": "KSM.foo",
            "data_type": "04",
            "type": "u16",
            "user_level": "read",
        }

    def test_german_only_register_survives_with_english_fallback(self) -> None:
        from modbusinfoConverter.multilingual_config import (
            merge_register_documents,
            new_report,
        )
        localization = _load_module(
            "kwb_localization_de_only_test",
            INTEGRATION_ROOT / "config_localization.py",
        )
        report = new_report("test")
        merged = merge_register_documents(
            {"registers": [self._source_register(1234, "Pumpe")]},
            {"registers": []},
            "v2.0.0",
            "devices/test.json",
            report,
        )["registers"][0]

        german = localization.localize_register(merged, "de")
        english = localization.localize_register(merged, "en")
        sys.modules.pop("kwb_localization_de_only_test", None)
        self.assertEqual("Pumpe", german["name"])
        self.assertEqual("Pumpe", english["name"])
        self.assertEqual(german["entity_id"], english["entity_id"])
        self.assertEqual(1, report["summary"]["de_only_registers"])
        self.assertFalse(report["items"][0]["blocking"])

    def test_english_only_register_survives_with_german_fallback(self) -> None:
        from modbusinfoConverter.multilingual_config import (
            merge_register_documents,
            new_report,
        )
        localization = _load_module(
            "kwb_localization_en_only_test",
            INTEGRATION_ROOT / "config_localization.py",
        )
        report = new_report("test")
        merged = merge_register_documents(
            {"registers": []},
            {"registers": [self._source_register(1234, "Pump")]},
            "v2.0.0",
            "devices/test.json",
            report,
        )["registers"][0]

        german = localization.localize_register(merged, "de")
        english = localization.localize_register(merged, "en")
        sys.modules.pop("kwb_localization_en_only_test", None)
        self.assertEqual("Pump", german["name"])
        self.assertEqual("Pump", english["name"])
        self.assertEqual(1, report["summary"]["en_only_registers"])

    def test_one_to_many_language_pair_is_blocking(self) -> None:
        from modbusinfoConverter.multilingual_config import (
            merge_register_documents,
            new_report,
        )

        report = new_report("test")
        german = self._source_register(100, "Pumpe")
        english_one = self._source_register(200, "Pump", "foo_one")
        english_two = self._source_register(300, "Pump duplicate", "foo_two")
        merge_register_documents(
            {"registers": [german]},
            {"registers": [english_one, english_two]},
            "v2.0.0",
            "devices/test.json",
            report,
        )

        ambiguity = next(
            item
            for item in report["items"]
            if item["kind"] == "ambiguous_language_pair"
        )
        self.assertTrue(ambiguity["blocking"])
        self.assertEqual(
            {"parameter_and_equipment_context": ("KSM.foo", None)},
            ambiguity["candidate_matching_evidence"],
        )

    def test_structural_language_conflict_blocks_finalizer_write(self) -> None:
        from modbusinfoConverter.import_generated_config import build_finalized_version
        from modbusinfoConverter.multilingual_config import (
            merge_register_documents,
            new_report,
        )

        report = new_report("test")
        german = self._source_register(100, "Pumpe")
        english = self._source_register(200, "Pump")
        english["type"] = "u32"
        merged = merge_register_documents(
            {"registers": [german]},
            {"registers": [english]},
            "v2.0.0",
            "devices/test.json",
            report,
        )
        conflict = next(item for item in report["items"] if item["blocking"])
        self.assertEqual("structural_conflict", conflict["kind"])
        self.assertEqual(["starting_address", "type"], conflict["fields"])

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generated_root = root / "generated"
            canonical_root = root / "canonical"
            version_dir = generated_root / "v2.0.0"
            (version_dir / "devices").mkdir(parents=True)
            (version_dir / "devices" / "test.json").write_text(
                json.dumps(merged), encoding="utf-8"
            )
            (version_dir / "value_tables.json").write_text(
                json.dumps({"value_tables": {}}), encoding="utf-8"
            )
            (version_dir / "alarm_codes.json").write_text(
                json.dumps({"alarm_codes": []}), encoding="utf-8"
            )
            (generated_root / "conversion_review.json").write_text(
                json.dumps(report), encoding="utf-8"
            )
            _proposal, import_report = build_finalized_version(
                generated_root, canonical_root, "2.0.0"
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_ROOT / "modbusinfoConverter/import_generated_config.py"),
                    "2.0.0",
                    "--generated-root",
                    str(generated_root),
                    "--canonical-root",
                    str(canonical_root),
                    "--report",
                    str(root / "import-review.json"),
                    "--write",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertTrue(import_report["blocking_review_required"])
        self.assertEqual(2, completed.returncode)
        self.assertIn("Refusing to write", completed.stdout)

    def test_value_table_and_alarm_labels_resolve_from_one_definition(self) -> None:
        localization = _load_module(
            "kwb_localization_values_test",
            INTEGRATION_ROOT / "config_localization.py",
        )
        tables = {
            "system_ein_aus_t": {
                "0": {"de": "Aus", "en": "Off"},
                "1": {"de": "Ein", "en": "On"},
            }
        }
        alarm = {
            "starting_address": 7,
            "alarm_id": "0.7",
            "description": {"de": "Batterie leer", "en": "Battery empty"},
        }

        self.assertEqual(
            {"0": "Aus", "1": "Ein"},
            localization.localize_value_tables(tables, "de")["system_ein_aus_t"],
        )
        self.assertEqual(
            {"0": "Off", "1": "On"},
            localization.localize_value_tables(tables, "en")["system_ein_aus_t"],
        )
        self.assertEqual(
            "Batterie leer",
            localization.localize_alarm_codes([alarm], "de")[0]["description"],
        )
        self.assertEqual(
            "Battery empty",
            localization.localize_alarm_codes([alarm], "en")[0]["description"],
        )
        sys.modules.pop("kwb_localization_values_test", None)


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
        cls.localization_module = _load_module(
            "kwb_config_localization_test",
            INTEGRATION_ROOT / "config_localization.py",
        )
        cls.version_module = _load_module(
            "kwb_version_manager_test",
            INTEGRATION_ROOT / "version_manager.py",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        sys.modules.pop("kwb_register_manager_test", None)
        sys.modules.pop("kwb_config_localization_test", None)
        sys.modules.pop("kwb_version_manager_test", None)
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
                config_dir = CONFIG_ROOT / version
                registers = [
                    self.localization_module.localize_register(register, language)
                    for register in _load_registers(
                        config_dir / "equipment" / "circulation.json"
                    )
                ]
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

    def test_version_config_path_is_language_neutral(self) -> None:
        manager = self.version_module.VersionManager(
            INTEGRATION_ROOT / "config"
        )
        german = manager.get_config_path("25.7.1", "de")
        english = manager.get_config_path("25.7.1", "en")
        self.assertEqual(german, english)
        self.assertEqual(CONFIG_ROOT / "v25.7.1", german)

    def test_runtime_register_membership_is_identical_in_german_and_english(self) -> None:
        version_dir = CONFIG_ROOT / "v25.7.1"
        universal = _load_registers(version_dir / "modbus_registers.json")
        easyair = _load_registers(version_dir / "devices/kwb_easyair_plus.json")

        def load(language: str) -> list[dict]:
            manager = self.manager_module.AsyncModularRegisterManager(
                config_path=str(version_dir), language=language
            )
            manager._initialized = True
            manager._universal_registers = [
                self.localization_module.localize_register(register, language)
                for register in universal
            ]
            manager._device_cache["KWB EasyAir Plus"] = [
                self.localization_module.localize_register(register, language)
                for register in easyair
            ]
            return asyncio.run(
                manager.get_all_registers(
                    "UserLevel", device_type="KWB EasyAir Plus"
                )
            )

        german = load("de")
        english = load("en")
        identity = lambda register: (
            register.get("parameter"),
            register.get("starting_address"),
            register.get("entity_id"),
            f"192.0.2.10_1_{register.get('entity_id')}",
        )
        self.assertEqual([identity(register) for register in german], [
            identity(register) for register in english
        ])
        self.assertEqual(len(german), len(english))
        self.assertTrue(
            any(
                de_register["name"] != en_register["name"]
                for de_register, en_register in zip(german, english)
            )
        )

        missing_english = next(
            register
            for register in easyair
            if set(register.get("name", {})) == {"de"}
        )
        address = missing_english["starting_address"]
        german_only_runtime = next(
            register for register in german if register["starting_address"] == address
        )
        english_fallback_runtime = next(
            register for register in english if register["starting_address"] == address
        )
        self.assertEqual(german_only_runtime["name"], english_fallback_runtime["name"])
        self.assertEqual(
            german_only_runtime["entity_id"], english_fallback_runtime["entity_id"]
        )

    def test_every_shipped_equipment_prefix_selects_first_instance(self) -> None:
        errors = []

        for version_dir in sorted(CONFIG_ROOT.glob("v*")):
            if not version_dir.is_dir():
                continue
            for language in ("de", "en"):
                for equipment_key, config in (
                    self.manager_module.AsyncModularRegisterManager.EQUIPMENT_KEY_CONFIG.items()
                ):
                    path = version_dir / "equipment" / config["filename"]
                    if not path.exists():
                        continue

                    source_registers = [
                        self.localization_module.localize_register(register, language)
                        for register in _load_registers(path)
                    ]
                    manager = self.manager_module.AsyncModularRegisterManager(
                        config_path=str(version_dir), language=language
                    )
                    manager._equipment_cache[equipment_key] = source_registers
                    selected = asyncio.run(
                        manager.get_equipment_registers(
                            equipment_key, "UserLevel", count=1
                        )
                    )

                    source_prefixes = {
                        register["equipment_group"]
                        for register in source_registers
                        if register.get("equipment_group")
                    }
                    selected_prefixes = {
                        register["equipment_group"]
                        for register in selected
                        if register.get("equipment_group")
                    }
                    if not selected or source_prefixes != selected_prefixes:
                        errors.append(
                            f"{version_dir.name}/{language}/{equipment_key}: "
                            f"{source_prefixes} -> {selected_prefixes}"
                        )

        self.assertEqual([], errors, "\n".join(errors))

    def test_english_equipment_aliases_and_transfer_stations(self) -> None:
        config_dir = CONFIG_ROOT / "v25.4.0"
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
                source_registers = [
                    self.localization_module.localize_register(register, "en")
                    for register in _load_registers(
                        config_dir / "equipment" / config["filename"]
                    )
                ]
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
                config_dir = CONFIG_ROOT / version
                source_registers = [
                    self.localization_module.localize_register(register, language)
                    for register in _load_registers(
                        config_dir / "equipment" / "boiler_sequence.json"
                    )
                ]
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
        for path in sorted(CONFIG_ROOT.glob("v*/equipment/*.json")):
            for register in _load_registers(path):
                for language in ("de", "en"):
                    index = register.get("index", {}).get(language, "")
                    if not index:
                        continue
                    if (
                        self.manager_module.AsyncModularRegisterManager
                        ._parse_equipment_index(index)
                        is None
                    ):
                        errors.append(
                            f"{path.relative_to(CONFIG_ROOT)} address "
                            f"{register.get('starting_address')} {language}: {index!r}"
                        )
        self.assertEqual([], errors, "\n".join(errors))

    def test_final_address_validation_applies_to_every_register_source(self) -> None:
        """Only add_registers() decides whether a source address is valid."""
        def collect(source: str, starting_address: object) -> tuple[list[dict], dict]:
            manager = self.manager_module.AsyncModularRegisterManager()
            manager._initialized = True
            register = {
                "starting_address": starting_address,
                "entity_id": f"{source}_register",
                "parameter": f"{source}.parameter",
                "name": f"{source} register",
                "user_level": "read",
            }
            if source == "equipment":
                register["index"] = "C 1"
            if source == "universal":
                manager._universal_registers = [register]
                registers = asyncio.run(manager.get_all_registers("UserLevel"))
            elif source == "device":
                manager._device_cache["KWB Easyfire"] = [register]
                registers = asyncio.run(
                    manager.get_all_registers("UserLevel", device_type="KWB Easyfire")
                )
            else:
                manager._equipment_cache["circulation"] = [register]
                registers = asyncio.run(
                    manager.get_all_registers(
                        "UserLevel", equipment_config={"circulation": 1}
                    )
                )
            return registers, register

        for source in ("universal", "device", "equipment"):
            for original, expected in ((0, 0), ("0", 0), ("123", 123)):
                with self.subTest(source=source, address=original):
                    registers, source_register = collect(source, original)
                    self.assertEqual([expected], [reg["starting_address"] for reg in registers])
                    self.assertEqual(original, source_register["starting_address"])

            for invalid in (None, "", "   ", "invalid", -1, "-1", {}):
                with self.subTest(source=source, address=invalid):
                    with self.assertLogs(self.manager_module.__name__, "WARNING") as logs:
                        registers, _source_register = collect(source, invalid)
                    self.assertEqual([], registers)
                    warning = "\n".join(logs.output)
                    self.assertIn("invalid starting_address", warning)
                    self.assertIn(repr(invalid), warning)

    def test_invalid_addresses_never_reach_entity_id_collision_repair(self) -> None:
        manager = self.manager_module.AsyncModularRegisterManager()
        manager._initialized = True
        manager._universal_registers = [
            {"starting_address": 10, "entity_id": "foo", "name": "Valid", "user_level": "read"},
            {"starting_address": None, "entity_id": "foo", "name": "Invalid", "user_level": "read"},
        ]

        with self.assertLogs(self.manager_module.__name__, "WARNING") as logs:
            registers = asyncio.run(manager.get_all_registers("UserLevel"))

        self.assertEqual(["foo"], [register["entity_id"] for register in registers])
        self.assertNotIn("foo_register_None", "\n".join(logs.output))

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

    def test_entity_id_collision_uses_register_address_suffix_when_needed(self) -> None:
        manager = self.manager_module.AsyncModularRegisterManager()
        manager._initialized = True
        manager._universal_registers = [
            {"starting_address": 10, "entity_id": "shared", "name": "First", "user_level": "read"},
            {
                "starting_address": 30,
                "entity_id": "shared_register_20",
                "name": "Existing fallback",
                "user_level": "read",
            },
        ]
        manager._device_cache["KWB Easyfire"] = [
            {"starting_address": 20, "entity_id": "shared", "name": "Third", "user_level": "read"},
        ]

        with self.assertLogs(self.manager_module.__name__, "WARNING") as logs:
            first_run = asyncio.run(
                manager.get_all_registers("UserLevel", device_type="KWB Easyfire")
            )
            second_run = asyncio.run(
                manager.get_all_registers("UserLevel", device_type="KWB Easyfire")
            )

        self.assertEqual([10, 30, 20], [reg["starting_address"] for reg in first_run])
        self.assertEqual(
            ["shared", "shared_register_20", "shared_register_20_2"],
            [reg["entity_id"] for reg in first_run],
        )
        self.assertEqual(first_run, second_run)
        self.assertIn("using 'shared_register_20_2'", "\n".join(logs.output))

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
            for address, published_id in (
                (8201, "boiler_pump_percent"),
                (8282, "boiler_temperature_setpoint_setting"),
                (8257, "full_load_hours_pm"),
            ):
                with self.subTest(entity_id=published_id):
                    register = {
                        "starting_address": address,
                        "entity_id": published_id,
                        "name": published_id.replace("_", " "),
                    }
                    entity = entity_module.KWBBaseEntity(
                        coordinator, register, "sensor"
                    )
                    self.assertEqual(f"sensor.kwb_{published_id}", entity.entity_id)
                    self.assertEqual(
                        f"192.0.2.10_1_{published_id}", entity._attr_unique_id
                    )
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

    def test_runtime_package_has_no_converter_dependency(self) -> None:
        references = []
        for path in INTEGRATION_ROOT.rglob("*.py"):
            if "modbusinfoConverter" in path.read_text(encoding="utf-8"):
                references.append(path.relative_to(PROJECT_ROOT).as_posix())
        self.assertEqual([], references)

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
