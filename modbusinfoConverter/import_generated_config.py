#!/usr/bin/env python3
"""Safely finalize generated templates into canonical integration configuration."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import tempfile
from typing import Any

try:
    from config_validation import (
        load_json,
        logical_register_key,
        registers_from,
        validate_or_raise,
    )
except ImportError:  # Imported as modbusinfoConverter.import_generated_config.
    from .config_validation import (
        load_json,
        logical_register_key,
        registers_from,
        validate_or_raise,
    )


REGISTER_CONTAINER_KEYS = ("registers", "universal_registers")
VERSION_PATTERN = re.compile(
    r"^(?:v)?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)

# Canonical history is compatibility history, not a source of technical metadata.
COMPATIBILITY_FIELDS = ("entity_id",)
TECHNICAL_COMPARISON_FIELDS = (
    "starting_address",
    "data_type",
    "register_type",
    "type",
    "unit",
    "unit_value_table",
    "multiplier",
    "scale",
    "scaling",
    "min",
    "max",
    "user_level",
    "expert_level",
    "access",
    "access_level",
    "write_mode",
    "read_write",
    "writable",
    "read_only",
    "register_length",
    "length",
    "functions",
    "function_code",
    "word_order",
    "byte_order",
    "id",
    "equipment_group",
    "equipment_instance",
    "equipment_subindex",
)


def _register_container(data: dict[str, Any]) -> str | None:
    return next((key for key in REGISTER_CONTAINER_KEYS if key in data), None)


def parse_firmware_version(version: str) -> tuple[int, int, int]:
    """Parse the strict firmware version format used by canonical directories."""
    match = VERSION_PATTERN.fullmatch(str(version).strip())
    if match is None:
        raise ValueError(
            f"Malformed firmware version {version!r}; expected MAJOR.MINOR.PATCH"
        )
    return tuple(int(component) for component in match.groups())


def _normalize_version(version: str) -> str:
    parsed = parse_firmware_version(version)
    return "v" + ".".join(str(component) for component in parsed)


def _canonical_versions(canonical_root: Path) -> dict[tuple[int, int, int], str]:
    """Return strict canonical versions, failing instead of guessing malformed names."""
    versions: dict[tuple[int, int, int], str] = {}
    if not canonical_root.exists():
        return versions
    for path in canonical_root.iterdir():
        if not path.is_dir() or not path.name.startswith("v"):
            continue
        try:
            parsed = parse_firmware_version(path.name)
        except ValueError as exc:
            raise ValueError(
                f"Malformed canonical version directory {path}; cannot select a baseline"
            ) from exc
        if parsed in versions:
            raise ValueError(
                "Ambiguous canonical firmware versions "
                f"{versions[parsed]!r} and {path.name!r}"
            )
        versions[parsed] = path.name
    return versions


def _select_baseline_version(
    canonical_root: Path,
    target_version: str,
    requested_base_version: str | None,
) -> tuple[str | None, str]:
    """Select same-version history, an explicit base, or the newest older base."""
    target = parse_firmware_version(target_version)
    target_name = _normalize_version(target_version)
    target_path = canonical_root / target_name
    if target_path.exists() and not target_path.is_dir():
        raise ValueError(f"Canonical target is not a directory: {target_path}")
    if target_path.is_dir():
        if requested_base_version is not None:
            requested_name = _normalize_version(requested_base_version)
            if requested_name != target_name:
                raise ValueError(
                    f"Canonical target {target_name} already exists; its own published "
                    "IDs must be used instead of a different base version"
                )
        return target_name, "same_version"

    if requested_base_version is not None:
        requested = parse_firmware_version(requested_base_version)
        requested_name = _normalize_version(requested_base_version)
        if requested >= target:
            raise ValueError(
                f"Base version {requested_name} must be older than target {target_name}"
            )
        requested_path = canonical_root / requested_name
        if not requested_path.is_dir():
            raise ValueError(
                f"Canonical base version does not exist: {requested_path}"
            )
        return requested_name, "explicit"

    older = {
        parsed: name
        for parsed, name in _canonical_versions(canonical_root).items()
        if parsed < target
    }
    if not older:
        return None, "none"
    return older[max(older)], "automatic"


def _meaningful_technical_changes(
    old: dict[str, Any], new: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Compare focused register properties without reporting formatting-only changes."""
    changes: dict[str, dict[str, Any]] = {}
    for field in TECHNICAL_COMPARISON_FIELDS:
        old_value = old.get(field)
        new_value = new.get(field)
        normalized_old = old_value.strip() if isinstance(old_value, str) else old_value
        normalized_new = new_value.strip() if isinstance(new_value, str) else new_value
        if normalized_old != normalized_new:
            changes[field] = {"old": old_value, "new": new_value}
    return changes


def _change_classification(changes: dict[str, dict[str, Any]]) -> str:
    if set(changes) == {"starting_address"}:
        return "register_moved"
    return "technical_metadata_changed"


def _localized_texts(value: Any) -> set[str]:
    """Return normalized non-empty display strings used as matching evidence."""
    values = value.values() if isinstance(value, dict) else (value,)
    return {
        item.strip().casefold()
        for item in values
        if isinstance(item, str) and item.strip()
    }


def _confident_parameter_rename(
    canonical: dict[str, Any], generated: dict[str, Any]
) -> bool:
    """Recognize a unique vendor rename without relying on address alone."""
    canonical_id = canonical.get("id")
    generated_id = generated.get("id")
    if not canonical_id or str(canonical_id) != str(generated_id):
        return False
    if canonical.get("entity_id") != generated.get("entity_id"):
        return False
    if any(
        canonical.get(field) != generated.get(field)
        for field in (
            "equipment_group",
            "equipment_instance",
            "equipment_subindex",
        )
    ):
        return False
    return bool(
        _localized_texts(canonical.get("name"))
        & _localized_texts(generated.get("name"))
    )


def _merge_register_file(
    relative_path: Path,
    generated: dict[str, Any],
    canonical: dict[str, Any],
    report: dict[str, Any],
    preserve_canonical_only: bool,
) -> dict[str, Any]:
    """Use generated registers while carrying forward only published entity IDs."""
    generated_key = _register_container(generated)
    canonical_key = _register_container(canonical)
    if generated_key is None or canonical_key is None:
        return deepcopy(generated)

    generated_registers = registers_from(generated)
    canonical_registers = registers_from(canonical)
    canonical_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    canonical_by_parameter: dict[str, list[dict[str, Any]]] = {}
    canonical_by_address: dict[Any, list[dict[str, Any]]] = {}
    canonical_by_entity_id: dict[str, list[dict[str, Any]]] = {}
    for register in canonical_registers:
        key = logical_register_key(relative_path, register)
        if key is not None:
            canonical_by_key.setdefault(key, []).append(register)
            canonical_by_parameter.setdefault(key[1], []).append(register)
        address = register.get("starting_address")
        if address is not None:
            canonical_by_address.setdefault(address, []).append(register)
        entity_id = register.get("entity_id")
        if isinstance(entity_id, str) and entity_id:
            canonical_by_entity_id.setdefault(entity_id, []).append(register)

    canonical_contexts_by_parameter: dict[str, set[str]] = {}
    generated_contexts_by_parameter: dict[str, set[str]] = {}
    for register in canonical_registers:
        key = logical_register_key(relative_path, register)
        if key is not None and key[2]:
            canonical_contexts_by_parameter.setdefault(key[1], set()).add(key[2])
    for register in generated_registers:
        key = logical_register_key(relative_path, register)
        if key is not None and key[2]:
            generated_contexts_by_parameter.setdefault(key[1], set()).add(key[2])
    expanded_equipment_parameters = {
        parameter
        for parameter, canonical_contexts in canonical_contexts_by_parameter.items()
        if canonical_contexts
        and canonical_contexts
        < generated_contexts_by_parameter.get(parameter, set())
    }

    matched_canonical: set[int] = set()
    entries: list[dict[str, Any]] = []
    for generated_register in generated_registers:
        merged_register = deepcopy(generated_register)
        entry = {
            "register": merged_register,
            "generated_entity_id": generated_register.get("entity_id"),
            "canonical": None,
            "technical_changes": {},
        }
        entries.append(entry)
        key = logical_register_key(relative_path, generated_register)
        matches = canonical_by_key.get(key, []) if key is not None else []
        if len(matches) == 1:
            existing = matches[0]
            matched_canonical.add(id(existing))
            changes = _meaningful_technical_changes(existing, generated_register)
            if {
                "equipment_group",
                "equipment_instance",
                "equipment_subindex",
            } & set(changes):
                report["items"].append(
                    {
                        "kind": "incompatible_equipment_context",
                        "blocking": True,
                        "target_version": report["target_version"],
                        "base_version": report["base_version"],
                        "file": relative_path.as_posix(),
                        "parameter": generated_register.get("parameter"),
                        "canonical": existing,
                        "generated": generated_register,
                        "context_changes": {
                            field: detail
                            for field, detail in changes.items()
                            if field
                            in {
                                "equipment_group",
                                "equipment_instance",
                                "equipment_subindex",
                            }
                        },
                    }
                )
                continue
            entry["canonical"] = existing
            entry["technical_changes"] = changes
            for field in COMPATIBILITY_FIELDS:
                if existing.get(field):
                    merged_register[field] = deepcopy(existing[field])
            continue
        if len(matches) > 1:
            matched_canonical.update(id(match) for match in matches)
            report["items"].append(
                {
                    "kind": "ambiguous_logical_match",
                    "blocking": True,
                    "target_version": report["target_version"],
                    "base_version": report["base_version"],
                    "file": relative_path.as_posix(),
                    "generated": generated_register,
                    "conflicting_entities": matches,
                }
            )
            continue

        parameter = generated_register.get("parameter")
        parameter_matches = (
            canonical_by_parameter.get(parameter.strip(), [])
            if isinstance(parameter, str) and parameter.strip()
            else []
        )
        if parameter_matches:
            parameter_key = parameter.strip()
            canonical_contexts = canonical_contexts_by_parameter.get(
                parameter_key, set()
            )
            if (
                key is not None
                and key[2]
                and parameter_key in expanded_equipment_parameters
                and key[2] not in canonical_contexts
                and not canonical_by_address.get(
                    generated_register.get("starting_address")
                )
            ):
                report["summary"]["new_registers_added"] += 1
                report["summary"]["new_equipment_instances_added"] += 1
                report["items"].append(
                    {
                        "kind": "new_equipment_instance",
                        "blocking": False,
                        "target_version": report["target_version"],
                        "base_version": report["base_version"],
                        "file": relative_path.as_posix(),
                        "parameter": parameter,
                        "equipment_group": generated_register.get(
                            "equipment_group"
                        ),
                        "equipment_instance": generated_register.get(
                            "equipment_instance"
                        ),
                        "equipment_subindex": generated_register.get(
                            "equipment_subindex"
                        ),
                        "matching_evidence": (
                            "All canonical equipment contexts remain present and "
                            "the generated context is a unique additional instance."
                        ),
                    }
                )
                continue
            matched_canonical.update(id(match) for match in parameter_matches)
            report["items"].append(
                {
                    "kind": "incompatible_equipment_index_context",
                    "blocking": True,
                    "target_version": report["target_version"],
                    "base_version": report["base_version"],
                    "file": relative_path.as_posix(),
                    "parameter": parameter,
                    "generated_index": generated_register.get("index"),
                    "generated": generated_register,
                    "conflicting_entities": parameter_matches,
                }
            )
            continue

        address_matches = canonical_by_address.get(
            generated_register.get("starting_address"), []
        )
        if (
            len(address_matches) == 1
            and _confident_parameter_rename(address_matches[0], generated_register)
        ):
            existing = address_matches[0]
            matched_canonical.add(id(existing))
            changes = _meaningful_technical_changes(existing, generated_register)
            entry["canonical"] = existing
            entry["technical_changes"] = changes
            for field in COMPATIBILITY_FIELDS:
                if existing.get(field):
                    merged_register[field] = deepcopy(existing[field])
            report["summary"]["parameter_identity_changes_reported"] += 1
            report["items"].append(
                {
                    "kind": "parameter_identity_changed",
                    "blocking": False,
                    "target_version": report["target_version"],
                    "base_version": report["base_version"],
                    "file": relative_path.as_posix(),
                    "old_parameter": existing.get("parameter"),
                    "new_parameter": generated_register.get("parameter"),
                    "entity_id": existing.get("entity_id"),
                    "starting_address": generated_register.get("starting_address"),
                    "vendor_register_id": generated_register.get("id"),
                    "matching_evidence": [
                        "unique_same_file_address",
                        "same_vendor_register_id",
                        "same_generated_and_published_entity_id",
                        "same_equipment_context",
                        "shared_localized_name",
                    ],
                }
            )
            continue
        if address_matches:
            matched_canonical.update(id(match) for match in address_matches)
            report["items"].append(
                {
                    "kind": "unmatched_register_address_conflict",
                    "blocking": True,
                    "target_version": report["target_version"],
                    "base_version": report["base_version"],
                    "file": relative_path.as_posix(),
                    "generated": generated_register,
                    "conflicting_entities": address_matches,
                }
            )
            continue

        entity_matches = canonical_by_entity_id.get(
            str(generated_register.get("entity_id")), []
        )
        if entity_matches:
            matched_canonical.update(id(match) for match in entity_matches)
            report["items"].append(
                {
                    "kind": "entity_id_logical_identity_conflict",
                    "blocking": True,
                    "target_version": report["target_version"],
                    "base_version": report["base_version"],
                    "file": relative_path.as_posix(),
                    "generated": generated_register,
                    "conflicting_entities": entity_matches,
                }
            )
            continue

        report["summary"]["new_registers_added"] += 1

    # Carrying an old ID can expose a collision with another generated register.
    # Keep the generated IDs in the blocked proposal so validation and dry-run finish.
    entries_by_entity_id: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        entity_id = entry["register"].get("entity_id")
        if isinstance(entity_id, str):
            entries_by_entity_id.setdefault(entity_id, []).append(entry)
    for entity_id, conflicting_entries in entries_by_entity_id.items():
        if len(conflicting_entries) < 2:
            continue
        report["items"].append(
            {
                "kind": "conflicting_published_entity_ids",
                "blocking": True,
                "target_version": report["target_version"],
                "base_version": report["base_version"],
                "file": relative_path.as_posix(),
                "entity_id": entity_id,
                "parameters": [
                    entry["register"].get("parameter") for entry in conflicting_entries
                ],
            }
        )
        for entry in conflicting_entries:
            entry["register"]["entity_id"] = entry["generated_entity_id"]
            entry["canonical"] = None

    for entry in entries:
        existing = entry["canonical"]
        if existing is None or not existing.get("entity_id"):
            continue
        report["summary"]["published_entity_ids_preserved"] += 1
        changes = entry["technical_changes"]
        generated_entity_id = entry["generated_entity_id"]
        if existing["entity_id"] != generated_entity_id or changes:
            report["summary"]["compatibility_actions_reported"] += 1
            if changes:
                report["summary"]["technical_register_changes_reported"] += 1
            report["items"].append(
                {
                    "kind": "preserve_entity_id",
                    "action": "preserve_entity_id",
                    "blocking": False,
                    "target_version": report["target_version"],
                    "base_version": report["base_version"],
                    "file": relative_path.as_posix(),
                    "parameter": entry["register"].get("parameter"),
                    "index": entry["register"].get("index"),
                    "entity_id": existing["entity_id"],
                    "generated_entity_id": generated_entity_id,
                    "technical_changes": changes,
                    "classification": (
                        _change_classification(changes)
                        if changes
                        else "published_identity_preserved"
                    ),
                }
            )

    merged_registers = [entry["register"] for entry in entries]
    if preserve_canonical_only:
        for register in canonical_registers:
            if id(register) in matched_canonical:
                continue
            merged_registers.append(deepcopy(register))
            key = logical_register_key(relative_path, register)
            report["items"].append(
                {
                    "kind": "canonical_only_register_preserved",
                    "blocking": False,
                    "target_version": report["target_version"],
                    "base_version": report["base_version"],
                    "file": relative_path.as_posix(),
                    "parameter": key[1] if key else register.get("parameter"),
                    "index": key[2] if key else register.get("index"),
                    "canonical_entity": register,
                }
            )

    result = deepcopy(generated)
    result[generated_key] = merged_registers
    return result


def _merge_value_tables(
    relative_path: Path,
    generated: dict[str, Any],
    canonical: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, Any]:
    """Use generated localized labels while blocking raw-key structural changes."""
    result = deepcopy(generated)
    canonical_tables = canonical.get("value_tables", {})
    generated_tables = generated.get("value_tables", {})
    for name, table in generated_tables.items():
        if name not in canonical_tables:
            report["summary"]["new_value_tables_added"] += 1
        elif set(canonical_tables[name]) != set(table):
            report["items"].append(
                {
                    "kind": "value_table_raw_keys_changed",
                    "blocking": True,
                    "target_version": report["target_version"],
                    "base_version": report["base_version"],
                    "file": relative_path.as_posix(),
                    "value_table": name,
                    "canonical_raw_keys": sorted(canonical_tables[name]),
                    "generated_raw_keys": sorted(table),
                    "decision": "Generated proposal retained; raw-key change requires review.",
                }
            )
        elif canonical_tables[name] != table:
            report["items"].append(
                {
                    "kind": "localized_value_table_labels_changed",
                    "blocking": False,
                    "target_version": report["target_version"],
                    "base_version": report["base_version"],
                    "file": relative_path.as_posix(),
                    "value_table": name,
                    "canonical": canonical_tables[name],
                    "generated": table,
                    "decision": "Generated target-firmware labels used.",
                }
            )
    for name in canonical_tables.keys() - generated_tables.keys():
        result.setdefault("value_tables", {})[name] = deepcopy(canonical_tables[name])
        report["items"].append(
            {
                "kind": "canonical_only_value_table_preserved",
                "blocking": False,
                "target_version": report["target_version"],
                "base_version": report["base_version"],
                "file": relative_path.as_posix(),
                "value_table": name,
            }
        )
    return result


def _merge_alarm_codes(
    relative_path: Path,
    generated: dict[str, Any],
    canonical: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, Any]:
    """Use generated alarm metadata and labels for matched alarm identities."""
    result = deepcopy(generated)
    canonical_alarms = canonical.get("alarm_codes", [])
    generated_alarms = generated.get("alarm_codes", [])
    existing = {
        (alarm.get("starting_address"), alarm.get("alarm_id")): alarm
        for alarm in canonical_alarms
    }
    generated_keys: set[tuple[Any, Any]] = set()
    for alarm in generated_alarms:
        key = (alarm.get("starting_address"), alarm.get("alarm_id"))
        generated_keys.add(key)
        if key not in existing:
            report["summary"]["new_alarm_codes_added"] += 1
        else:
            old_technical = {
                field: value
                for field, value in existing[key].items()
                if field != "description"
            }
            new_technical = {
                field: value for field, value in alarm.items() if field != "description"
            }
            if old_technical != new_technical:
                report["items"].append(
                    {
                        "kind": "alarm_code_structural_change",
                        "blocking": True,
                        "target_version": report["target_version"],
                        "base_version": report["base_version"],
                        "file": relative_path.as_posix(),
                        "canonical": existing[key],
                        "generated": alarm,
                        "decision": "Generated proposal retained; structure requires review.",
                    }
                )
            elif existing[key].get("description") != alarm.get("description"):
                report["items"].append(
                    {
                        "kind": "localized_alarm_description_changed",
                        "blocking": False,
                        "target_version": report["target_version"],
                        "base_version": report["base_version"],
                        "file": relative_path.as_posix(),
                        "alarm_id": alarm.get("alarm_id"),
                        "canonical": existing[key].get("description"),
                        "generated": alarm.get("description"),
                        "decision": "Generated target-firmware description used.",
                    }
                )
    result_alarms = result.setdefault("alarm_codes", [])
    for key, alarm in existing.items():
        if key not in generated_keys:
            result_alarms.append(deepcopy(alarm))
            report["items"].append(
                {
                    "kind": "canonical_only_alarm_preserved",
                    "blocking": False,
                    "target_version": report["target_version"],
                    "base_version": report["base_version"],
                    "file": relative_path.as_posix(),
                    "canonical": alarm,
                }
            )
    return result


def _conversion_review_items(generated_root: Path, version: str) -> list[dict]:
    report_path = generated_root / "conversion_review.json"
    if not report_path.exists():
        return []
    data = load_json(report_path)
    return [
        item
        for item in data.get("items", [])
        if str(item.get("firmware_version", "")).removeprefix("v")
        == version.removeprefix("v")
    ]


def build_finalized_version(
    generated_root: Path,
    canonical_root: Path,
    version: str,
    base_version: str | None = None,
) -> tuple[dict[Path, dict[str, Any]], dict[str, Any]]:
    """Build a validated proposal without mutating canonical configuration."""
    version = _normalize_version(version)
    generated_root = Path(generated_root)
    canonical_root = Path(canonical_root)
    generated_version = Path(generated_root) / version
    canonical_version = Path(canonical_root) / version
    if not generated_version.is_dir():
        raise ValueError(f"Generated version does not exist: {generated_version}")
    selected_base, baseline_selection = _select_baseline_version(
        canonical_root, version, base_version
    )
    compatibility_version = (
        canonical_root / selected_base if selected_base is not None else None
    )
    target_exists = canonical_version.is_dir()

    report: dict[str, Any] = {
        "version": version,
        "target_version": version,
        "base_version": selected_base,
        "baseline_selection": baseline_selection,
        "generated_root": str(generated_root),
        "canonical_root": str(canonical_root),
        "items": [],
        "summary": {
            "published_entity_ids_preserved": 0,
            "compatibility_actions_reported": 0,
            "technical_register_changes_reported": 0,
            "parameter_identity_changes_reported": 0,
            "new_registers_added": 0,
            "new_equipment_instances_added": 0,
            "new_value_tables_added": 0,
            "new_alarm_codes_added": 0,
            "files_added": 0,
        },
    }
    if selected_base is None:
        report["items"].append(
            {
                "kind": "no_compatibility_baseline",
                "blocking": False,
                "target_version": version,
                "base_version": None,
                "message": (
                    "No older canonical firmware version was available; generated "
                    "entity IDs require first-version review."
                ),
            }
        )
    for item in _conversion_review_items(generated_root, version):
        report["items"].append(
            {
                "kind": "converter_review_required",
                "blocking": bool(item.get("blocking", True)),
                "detail": item,
            }
        )

    proposed: dict[Path, dict[str, Any]] = {}
    canonical_files = (
        {path.relative_to(canonical_version) for path in canonical_version.rglob("*.json")}
        if target_exists
        else set()
    )
    generated_files = {
        path.relative_to(generated_version) for path in generated_version.rglob("*.json")
    }

    for relative_path in sorted(canonical_files | generated_files):
        generated_path = generated_version / relative_path
        canonical_path = canonical_version / relative_path
        if not generated_path.exists():
            proposed[relative_path] = load_json(canonical_path)
            report["items"].append(
                {
                    "kind": "canonical_only_file_preserved",
                    "blocking": False,
                    "file": relative_path.as_posix(),
                }
            )
            continue
        generated_data = load_json(generated_path)
        if not canonical_path.exists():
            report["summary"]["files_added"] += 1
        compatibility_path = (
            compatibility_version / relative_path
            if compatibility_version is not None
            else None
        )
        compatibility_data = (
            load_json(compatibility_path)
            if compatibility_path is not None and compatibility_path.exists()
            else None
        )

        # A previous-version baseline only contributes register identity. Other
        # files and all register metadata come from the generated target version.
        if canonical_path.exists() and relative_path.name == "value_tables.json":
            proposed[relative_path] = _merge_value_tables(
                relative_path, generated_data, compatibility_data, report
            )
        elif canonical_path.exists() and relative_path.name == "alarm_codes.json":
            proposed[relative_path] = _merge_alarm_codes(
                relative_path, generated_data, compatibility_data, report
            )
        elif (
            _register_container(generated_data) is not None
            and compatibility_data is not None
            and _register_container(compatibility_data) is not None
        ):
            proposed[relative_path] = _merge_register_file(
                relative_path,
                generated_data,
                compatibility_data,
                report,
                preserve_canonical_only=target_exists,
            )
        elif canonical_path.exists() and compatibility_data != generated_data:
            proposed[relative_path] = deepcopy(compatibility_data)
            if _register_container(generated_data) is not None:
                report["items"].append(
                    {
                        "kind": "incompatible_register_file_structure",
                        "blocking": True,
                        "target_version": version,
                        "base_version": selected_base,
                        "file": relative_path.as_posix(),
                    }
                )
            else:
                report["items"].append(
                    {
                        "kind": "unrecognized_file_changed",
                        "blocking": True,
                        "target_version": version,
                        "base_version": selected_base,
                        "file": relative_path.as_posix(),
                    }
                )
        else:
            proposed[relative_path] = deepcopy(generated_data)

    with tempfile.TemporaryDirectory(prefix="kwb-config-finalize-") as temp_dir:
        validation_root = Path(temp_dir)
        for relative_path, data in proposed.items():
            destination = validation_root / version / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        validate_or_raise(validation_root)

    report["blocking_review_required"] = any(
        item.get("blocking", False) for item in report["items"]
    )
    report["summary"]["blocking_review_items"] = sum(
        bool(item.get("blocking", False)) for item in report["items"]
    )
    return proposed, report


def write_finalized_version(
    canonical_root: Path,
    version: str,
    proposed: dict[Path, dict[str, Any]],
) -> None:
    """Write a fully validated proposal to the canonical tree."""
    version = _normalize_version(version)
    for relative_path, data in proposed.items():
        destination = Path(canonical_root) / version / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(destination)


def main() -> int:
    """CLI entry point; dry-run is the safe default."""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    parser = argparse.ArgumentParser(
        description=(
            "Finalize generated KWB templates while preserving published production IDs."
        )
    )
    parser.add_argument("version", help="Firmware version, for example 25.7.1")
    parser.add_argument(
        "--generated-root",
        type=Path,
        default=script_dir / "config" / "versions",
    )
    parser.add_argument(
        "--canonical-root",
        type=Path,
        default=(
            project_root
            / "custom_components"
            / "kwb_heating"
            / "config"
            / "versions"
        ),
    )
    parser.add_argument(
        "--base-version",
        help=(
            "Older canonical firmware version used only for published-ID matching "
            "when the target does not exist"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Review-report path (default: generated root/import_review_<version>.json)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the validated proposal; without this flag the command is dry-run only.",
    )
    args = parser.parse_args()

    try:
        proposed, report = build_finalized_version(
            args.generated_root,
            args.canonical_root,
            args.version,
            base_version=args.base_version,
        )
    except ValueError as exc:
        parser.error(str(exc))
    report_path = args.report or (
        args.generated_root / f"import_review_{report['target_version']}.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    if args.write:
        if report["blocking_review_required"]:
            print(f"Refusing to write: blocking review items are listed in {report_path}")
            return 2
        write_finalized_version(args.canonical_root, args.version, proposed)
        print(f"Finalized v{args.version.removeprefix('v')} into {args.canonical_root}")
    else:
        print(f"Dry run only; review report written to {report_path}")
    if report["base_version"] is None:
        print("Compatibility baseline: none available")
    else:
        print(
            "Compatibility baseline: "
            f"{report['base_version']} ({report['baseline_selection']})"
        )
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
