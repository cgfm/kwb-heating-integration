#!/usr/bin/env python3
"""Validation helpers for finalized or generated KWB configuration trees."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ENTITY_ID_PATTERN = re.compile(r"^[a-z0-9_]+$")
SUPPORTED_LANGUAGES = {"de", "en"}
LOCALIZED_REGISTER_FIELDS = {"name", "index"}


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object and give callers a path-specific failure."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return data


def registers_from(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return either supported register-list shape."""
    registers = data.get("registers", data.get("universal_registers", []))
    return registers if isinstance(registers, list) else []


def logical_register_key(
    relative_path: Path, register: dict[str, Any]
) -> tuple[str, str, str] | None:
    """Build a stable key from file context, parameter, and technical equipment key."""
    parameter = register.get("parameter")
    if not isinstance(parameter, str) or not parameter.strip():
        return None
    equipment_group = register.get("equipment_group")
    equipment_instance = register.get("equipment_instance")
    equipment_subindex = register.get("equipment_subindex")
    if equipment_group is not None or equipment_instance is not None:
        context = f"{equipment_group}:{equipment_instance}"
        if equipment_subindex is not None:
            context += f":{equipment_subindex}"
    else:
        context = ""
    return relative_path.as_posix(), parameter.strip(), context


def _equipment_index_valid(index: Any, expected_instance: Any) -> bool:
    if index in (None, ""):
        return True
    if not isinstance(index, str) or " " not in index:
        return False
    _prefix, identifier = index.split(" ", 1)
    try:
        instance = int(identifier.split(".", 1)[0])
    except ValueError:
        return False
    return expected_instance is None or instance == expected_instance


def _localized_value_errors(value: Any, location: str, required: bool) -> list[str]:
    errors: list[str] = []
    if value is None and not required:
        return errors
    if not isinstance(value, dict):
        return [f"{location}: must be a localized object"]
    unknown = set(value) - SUPPORTED_LANGUAGES
    if unknown:
        errors.append(f"{location}: unsupported language keys {sorted(unknown)}")
    usable = [item for item in value.values() if isinstance(item, str) and item.strip()]
    if required and not usable:
        errors.append(f"{location}: requires at least one usable translation")
    for language, item in value.items():
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{location}.{language}: translation must be a non-empty string")
    return errors


def validate_config_tree(root: Path) -> list[str]:
    """Validate one language-neutral technical tree per firmware version."""
    root = Path(root)
    errors: list[str] = []
    for version_dir in sorted(root.glob("v*")):
        if not version_dir.is_dir():
            continue
        legacy_languages = [
            language for language in SUPPORTED_LANGUAGES if (version_dir / language).is_dir()
        ]
        if legacy_languages:
            errors.append(
                f"{version_dir}: obsolete language directories remain: "
                f"{sorted(legacy_languages)}"
            )
            continue

        value_tables_path = version_dir / "value_tables.json"
        try:
            value_tables_data = load_json(value_tables_path)
            value_tables = value_tables_data.get("value_tables", {})
            if not isinstance(value_tables, dict):
                errors.append(f"{value_tables_path}: value_tables must be an object")
                value_tables = {}
        except ValueError as exc:
            errors.append(str(exc))
            value_tables = {}

        for table_name, table in value_tables.items():
            if not isinstance(table_name, str) or not table_name:
                errors.append(f"{value_tables_path}: invalid value-table name {table_name!r}")
                continue
            if not isinstance(table, dict):
                errors.append(f"{value_tables_path}: table {table_name!r} must be an object")
                continue
            for raw_value, labels in table.items():
                try:
                    int(raw_value)
                except (TypeError, ValueError):
                    errors.append(
                        f"{value_tables_path}: table {table_name!r} has invalid raw key "
                        f"{raw_value!r}"
                    )
                errors.extend(
                    _localized_value_errors(
                        labels,
                        f"{value_tables_path}: table {table_name!r}[{raw_value!r}]",
                        required=True,
                    )
                )

        logical: dict[tuple[str, str, str], dict[str, Any]] = {}
        referenced_tables: set[str] = set()
        for path in sorted(version_dir.rglob("*.json")):
            if path == value_tables_path or path.name == "alarm_codes.json":
                continue
            try:
                data = load_json(path)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            registers = registers_from(data)
            if not registers:
                continue

            seen_ids: dict[str, Any] = {}
            seen_addresses: dict[int, dict[str, Any]] = {}
            relative_path = path.relative_to(version_dir)
            for number, register in enumerate(registers):
                location = f"{path}:{number}"
                if not isinstance(register, dict):
                    errors.append(f"{location}: register must be an object")
                    continue
                address = register.get("starting_address")
                if isinstance(address, bool) or not isinstance(address, int) or address < 0:
                    errors.append(f"{location}: invalid starting_address {address!r}")
                elif address in seen_addresses:
                    errors.append(
                        f"{location}: duplicate address {address} in one register file"
                    )
                else:
                    seen_addresses[address] = register

                entity_id = register.get("entity_id")
                if not isinstance(entity_id, str) or not ENTITY_ID_PATTERN.fullmatch(
                    entity_id
                ):
                    errors.append(f"{location}: invalid entity_id {entity_id!r}")
                elif entity_id in seen_ids:
                    errors.append(
                        f"{location}: duplicate entity_id {entity_id!r} at "
                        f"addresses {seen_ids[entity_id]!r} and {address!r}"
                    )
                else:
                    seen_ids[entity_id] = address

                errors.extend(
                    _localized_value_errors(
                        register.get("name"), f"{location}: name", required=True
                    )
                )
                if "index" in register:
                    errors.extend(
                        _localized_value_errors(
                            register.get("index"), f"{location}: index", required=True
                        )
                    )
                for field, value in register.items():
                    if field not in LOCALIZED_REGISTER_FIELDS and isinstance(value, dict):
                        errors.append(
                            f"{location}: structural field {field!r} cannot be localized"
                        )

                if relative_path.parts[:1] == ("equipment",):
                    index = register.get("index", {})
                    if index:
                        group = register.get("equipment_group")
                        instance = register.get("equipment_instance")
                        if not isinstance(group, str) or not group:
                            errors.append(f"{location}: missing technical equipment_group")
                        if (
                            isinstance(instance, bool)
                            or not isinstance(instance, int)
                            or instance < 0
                        ):
                            errors.append(
                                f"{location}: invalid equipment_instance {instance!r}"
                            )
                        if isinstance(index, dict):
                            for language, localized_index in index.items():
                                if not _equipment_index_valid(localized_index, instance):
                                    errors.append(
                                        f"{location}: malformed {language} equipment index "
                                        f"{localized_index!r}"
                                    )
                    subindex = register.get("equipment_subindex")
                    if subindex is not None and (
                        isinstance(subindex, bool)
                        or not isinstance(subindex, int)
                        or subindex < 0
                    ):
                        errors.append(f"{location}: invalid equipment_subindex {subindex!r}")

                table = register.get("unit_value_table")
                if isinstance(table, str) and table.endswith("_t"):
                    referenced_tables.add(table)

                key = logical_register_key(relative_path, register)
                if key is None:
                    errors.append(f"{location}: missing stable parameter")
                elif key in logical:
                    errors.append(f"{location}: duplicate logical register key {key!r}")
                else:
                    logical[key] = register

        for table in sorted(referenced_tables - set(value_tables)):
            errors.append(
                f"{version_dir}: referenced value table {table!r} does not exist"
            )

        alarm_path = version_dir / "alarm_codes.json"
        try:
            alarms = load_json(alarm_path).get("alarm_codes", [])
            if not isinstance(alarms, list):
                errors.append(f"{alarm_path}: alarm_codes must be a list")
                alarms = []
        except ValueError as exc:
            errors.append(str(exc))
            alarms = []
        seen_alarms: set[tuple[Any, Any]] = set()
        for number, alarm in enumerate(alarms):
            location = f"{alarm_path}:{number}"
            if not isinstance(alarm, dict):
                errors.append(f"{location}: alarm must be an object")
                continue
            alarm_key = (alarm.get("starting_address"), alarm.get("alarm_id"))
            if alarm_key in seen_alarms:
                errors.append(f"{location}: duplicate alarm identity {alarm_key!r}")
            seen_alarms.add(alarm_key)
            errors.extend(
                _localized_value_errors(
                    alarm.get("description"), f"{location}: description", required=True
                )
            )
            for field, value in alarm.items():
                if field != "description" and isinstance(value, dict):
                    errors.append(
                        f"{location}: structural alarm field {field!r} cannot be localized"
                    )

    return errors


def validate_or_raise(root: Path) -> None:
    """Raise one readable exception when a tree fails validation."""
    errors = validate_config_tree(root)
    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(errors))
