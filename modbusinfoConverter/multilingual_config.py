"""Build one explicit multilingual KWB configuration from DE/EN source trees."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any


LANGUAGES = ("de", "en")
LOCALIZED_REGISTER_FIELDS = ("name", "index")
CONVERTER_METADATA_FIELDS = ("_english_name", "_source_file", "_source_context")
INDEX_PREFIX_MAP = {
    "HK": "HC",
    "PUF": "BUF",
    "ZUB": "FP",
    "BWS": "DHWC",
    "ZWQ": "SHS",
    "Zirk": "Circ",
    "KFK": "B",
    "WMZ": "HQM",
    "ÜGS": "TS",
}
UNIT_NORMALIZATION = {"Upm": "rpm", "RPM": "rpm"}
REQUIRED_VALUE_TABLES = {
    "system_ein_aus_t": {
        "0": {"de": "Aus", "en": "Off"},
        "1": {"de": "Ein", "en": "On"},
    },
    "system_yes_no_t": {
        "0": {"de": "Nein", "en": "No"},
        "1": {"de": "Ja", "en": "Yes"},
    },
}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return data


def _registers(data: dict[str, Any]) -> list[dict[str, Any]]:
    values = data.get("registers", data.get("universal_registers", []))
    return values if isinstance(values, list) else []


def _container_key(*documents: dict[str, Any]) -> str:
    for document in documents:
        if "universal_registers" in document:
            return "universal_registers"
        if "registers" in document:
            return "registers"
    return "registers"


def _nonempty(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _localized(de_value: Any, en_value: Any) -> dict[str, str]:
    result: dict[str, str] = {}
    if value := _nonempty(de_value):
        result["de"] = value
    if value := _nonempty(en_value):
        result["en"] = value
    return result


def _normalized_unit(value: Any) -> Any:
    return UNIT_NORMALIZATION.get(value, value)


def _technical_index(index: Any) -> tuple[str, int, int | None] | None:
    """Derive a language-neutral equipment key from either localized index."""
    value = _nonempty(index)
    if value is None or " " not in value:
        return None
    prefix, identifier = value.split(" ", 1)
    parts = identifier.split(".", 1)
    try:
        instance = int(parts[0])
        subindex = int(parts[1]) if len(parts) == 2 else None
    except ValueError:
        return None
    return INDEX_PREFIX_MAP.get(prefix, prefix), instance, subindex


def _pair_identity(register: dict[str, Any]) -> tuple[str, Any]:
    return str(register.get("parameter", "")).strip(), register.get("starting_address")


def _secondary_identity(register: dict[str, Any]) -> tuple[str, Any] | None:
    parameter = str(register.get("parameter", "")).strip()
    if not parameter:
        return None
    return parameter, _technical_index(register.get("index"))


def _technical_data(register: dict[str, Any]) -> dict[str, Any]:
    data = {
        key: value
        for key, value in register.items()
        if key not in LOCALIZED_REGISTER_FIELDS + CONVERTER_METADATA_FIELDS
    }
    if "unit_value_table" in data:
        data["unit_value_table"] = _normalized_unit(data["unit_value_table"])
    return data


def _source_detail(register: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_file": register.get("_source_file"),
        "source_context": register.get("_source_context"),
    }


def _review_item(
    report: dict[str, Any], kind: str, blocking: bool, **detail: Any
) -> None:
    report["items"].append({"kind": kind, "blocking": blocking, **detail})
    if blocking:
        report["summary"]["blocking_items"] += 1


def _match_registers(
    de_registers: list[dict[str, Any]],
    en_registers: list[dict[str, Any]],
    version: str,
    context: str,
    report: dict[str, Any],
) -> tuple[list[tuple[dict[str, Any], dict[str, Any]]], list[dict], list[dict]]:
    """Pair records by exact logical identity, then deterministic supporting keys."""
    unmatched_de = set(range(len(de_registers)))
    unmatched_en = set(range(len(en_registers)))
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    reported_ambiguities: set[tuple[tuple[int, ...], tuple[int, ...]]] = set()

    def pair_unique(key_function, evidence_name: str) -> None:
        de_by_key: dict[Any, list[int]] = {}
        en_by_key: dict[Any, list[int]] = {}
        for number in unmatched_de:
            key = key_function(de_registers[number])
            if key is not None:
                de_by_key.setdefault(key, []).append(number)
        for number in unmatched_en:
            key = key_function(en_registers[number])
            if key is not None:
                en_by_key.setdefault(key, []).append(number)
        for key in de_by_key.keys() & en_by_key.keys():
            de_matches = de_by_key[key]
            en_matches = en_by_key[key]
            if len(de_matches) == len(en_matches) == 1:
                de_number, en_number = de_matches[0], en_matches[0]
                pairs.append((de_registers[de_number], en_registers[en_number]))
                unmatched_de.remove(de_number)
                unmatched_en.remove(en_number)
            else:
                ambiguity = (tuple(de_matches), tuple(en_matches))
                if ambiguity in reported_ambiguities:
                    continue
                reported_ambiguities.add(ambiguity)
                _review_item(
                    report,
                    "ambiguous_language_pair",
                    True,
                    firmware_version=version,
                    context=context,
                    candidate_matching_evidence={evidence_name: key},
                    german_registers=[de_registers[number] for number in de_matches],
                    english_registers=[en_registers[number] for number in en_matches],
                )

    pair_unique(_pair_identity, "parameter_and_address")
    pair_unique(_secondary_identity, "parameter_and_equipment_context")

    # Address is supporting evidence only. Pairing by address is retained as a
    # blocked proposal so both records and the disagreement remain reviewable.
    pair_unique(lambda register: register.get("starting_address"), "address")
    return (
        pairs,
        [de_registers[number] for number in sorted(unmatched_de)],
        [en_registers[number] for number in sorted(unmatched_en)],
    )


def _merge_register(
    de_register: dict[str, Any] | None,
    en_register: dict[str, Any] | None,
    version: str,
    context: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    base = deepcopy(en_register or de_register or {})
    de_register = de_register or {}
    en_register = en_register or {}
    de_technical = _technical_data(de_register)
    en_technical = _technical_data(en_register)

    if de_register and en_register:
        fields = sorted(
            field
            for field in de_technical.keys() | en_technical.keys()
            if de_technical.get(field) != en_technical.get(field)
        )
        if fields:
            _review_item(
                report,
                "structural_conflict",
                True,
                firmware_version=version,
                context=context,
                fields=fields,
                german_register=de_register,
                english_register=en_register,
                candidate_matching_evidence={
                    "parameter": de_register.get("parameter"),
                    "german_address": de_register.get("starting_address"),
                    "english_address": en_register.get("starting_address"),
                    "german_index": de_register.get("index"),
                    "english_index": en_register.get("index"),
                },
                german_source=_source_detail(de_register),
                english_source=_source_detail(en_register),
            )

    for field in LOCALIZED_REGISTER_FIELDS + CONVERTER_METADATA_FIELDS:
        base.pop(field, None)
    if "unit_value_table" in base:
        base["unit_value_table"] = _normalized_unit(base["unit_value_table"])

    names = _localized(de_register.get("name"), en_register.get("name"))
    if names:
        base["name"] = names
    indexes = _localized(de_register.get("index"), en_register.get("index"))
    if indexes:
        base["index"] = indexes

    technical_index = _technical_index(en_register.get("index")) or _technical_index(
        de_register.get("index")
    )
    if technical_index is not None:
        group, instance, subindex = technical_index
        base["equipment_group"] = group
        base["equipment_instance"] = instance
        if subindex is not None:
            base["equipment_subindex"] = subindex

    present = "de" if de_register else "en"
    missing = "en" if de_register else "de"
    if not (de_register and en_register):
        report["summary"][f"{present}_only_registers"] += 1
        report["summary"]["missing_register_translations"] += 1
        _review_item(
            report,
            "missing_translation",
            False,
            firmware_version=version,
            context=context,
            field="name",
            available_language=present,
            missing_language=missing,
            parameter=base.get("parameter"),
            starting_address=base.get("starting_address"),
            entity_id=base.get("entity_id"),
        )
    else:
        report["summary"]["registers_in_both"] += 1
    return base


def merge_register_documents(
    de_data: dict[str, Any],
    en_data: dict[str, Any],
    version: str,
    context: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    pairs, de_only, en_only = _match_registers(
        _registers(de_data), _registers(en_data), version, context, report
    )
    merged = [
        _merge_register(de_register, en_register, version, context, report)
        for de_register, en_register in pairs
    ]
    merged.extend(
        _merge_register(register, None, version, context, report)
        for register in de_only
    )
    merged.extend(
        _merge_register(None, register, version, context, report)
        for register in en_only
    )
    merged.sort(
        key=lambda register: (
            register.get("starting_address", -1),
            str(register.get("parameter", "")),
            str(register.get("entity_id", "")),
        )
    )
    return {_container_key(de_data, en_data): merged}


def merge_value_table_documents(
    de_data: dict[str, Any],
    en_data: dict[str, Any],
    version: str,
    context: str,
    report: dict[str, Any],
    resolve_key_gaps: bool,
) -> dict[str, Any]:
    de_tables = de_data.get("value_tables", {})
    en_tables = en_data.get("value_tables", {})
    merged: dict[str, dict[str, dict[str, str]]] = {}
    for table_name in sorted(de_tables.keys() | en_tables.keys()):
        de_table = de_tables.get(table_name, {})
        en_table = en_tables.get(table_name, {})
        if set(de_table) != set(en_table):
            _review_item(
                report,
                "technical_metadata_difference",
                not resolve_key_gaps,
                firmware_version=version,
                context=context,
                value_table=table_name,
                field="raw_keys",
                german_keys=sorted(de_table),
                english_keys=sorted(en_table),
                resolution=(
                    "existing canonical raw-key union retained; absent labels are "
                    "recorded as missing translations"
                    if resolve_key_gaps
                    else None
                ),
            )
        merged_table: dict[str, dict[str, str]] = {}
        for raw_value in sorted(
            de_table.keys() | en_table.keys(), key=lambda value: (len(str(value)), str(value))
        ):
            labels = _localized(de_table.get(raw_value), en_table.get(raw_value))
            merged_table[str(raw_value)] = labels
            for language in LANGUAGES:
                if language not in labels:
                    report["summary"]["missing_value_table_translations"] += 1
                    _review_item(
                        report,
                        "missing_translation",
                        False,
                        firmware_version=version,
                        context=context,
                        field="value_table_label",
                        value_table=table_name,
                        raw_value=str(raw_value),
                        missing_language=language,
                    )
        merged[table_name] = merged_table
    for table_name, table in REQUIRED_VALUE_TABLES.items():
        if table_name not in merged:
            merged[table_name] = deepcopy(table)
    return {"value_tables": merged}


def merge_alarm_documents(
    de_data: dict[str, Any],
    en_data: dict[str, Any],
    version: str,
    context: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    key = lambda alarm: (alarm.get("starting_address"), alarm.get("alarm_id"))
    de_alarms = {key(alarm): alarm for alarm in de_data.get("alarm_codes", [])}
    en_alarms = {key(alarm): alarm for alarm in en_data.get("alarm_codes", [])}
    merged: list[dict[str, Any]] = []
    for alarm_key in sorted(de_alarms.keys() | en_alarms.keys()):
        de_alarm = de_alarms.get(alarm_key, {})
        en_alarm = en_alarms.get(alarm_key, {})
        de_technical = {key: value for key, value in de_alarm.items() if key != "description"}
        en_technical = {key: value for key, value in en_alarm.items() if key != "description"}
        if de_alarm and en_alarm and de_technical != en_technical:
            _review_item(
                report,
                "structural_conflict",
                True,
                firmware_version=version,
                context=context,
                fields=sorted(de_technical.keys() | en_technical.keys()),
                german_alarm=de_alarm,
                english_alarm=en_alarm,
            )
        result = deepcopy(en_alarm or de_alarm)
        descriptions = _localized(
            de_alarm.get("description"), en_alarm.get("description")
        )
        if not descriptions:
            descriptions["en"] = f"Alarm {result.get('alarm_id', 'unknown')}"
            for language in LANGUAGES:
                report["summary"]["missing_alarm_translations"] += 1
                _review_item(
                    report,
                    "missing_translation",
                    False,
                    firmware_version=version,
                    context=context,
                    field="alarm_description",
                    alarm_id=result.get("alarm_id"),
                    missing_language=language,
                    fallback=descriptions["en"],
                )
        result["description"] = descriptions
        for language, alarm in (("de", de_alarm), ("en", en_alarm)):
            if not alarm:
                report["summary"]["missing_alarm_translations"] += 1
                _review_item(
                    report,
                    "missing_translation",
                    False,
                    firmware_version=version,
                    context=context,
                    field="alarm_description",
                    alarm_id=result.get("alarm_id"),
                    missing_language=language,
                )
        merged.append(result)
    return {"alarm_codes": merged}


def new_report(description: str) -> dict[str, Any]:
    return {
        "description": description,
        "items": [],
        "versions": {},
        "summary": {
            "registers_in_both": 0,
            "de_only_registers": 0,
            "en_only_registers": 0,
            "missing_register_translations": 0,
            "missing_value_table_translations": 0,
            "missing_alarm_translations": 0,
            "blocking_items": 0,
        },
    }


def merge_language_version(
    source_version: Path,
    destination_version: Path,
    report: dict[str, Any],
    *,
    resolve_existing_table_key_gaps: bool = False,
) -> dict[str, int]:
    """Merge one legacy DE/EN version directory into one unified directory."""
    version = source_version.name
    before = dict(report["summary"])
    de_root = source_version / "de"
    en_root = source_version / "en"
    files = {
        path.relative_to(de_root) for path in de_root.rglob("*.json")
    } | {path.relative_to(en_root) for path in en_root.rglob("*.json")}
    for relative_path in sorted(files):
        de_data = _load_json(de_root / relative_path)
        en_data = _load_json(en_root / relative_path)
        context = relative_path.as_posix()
        if relative_path.name == "value_tables.json":
            result = merge_value_table_documents(
                de_data,
                en_data,
                version,
                context,
                report,
                resolve_existing_table_key_gaps,
            )
        elif relative_path.name == "alarm_codes.json":
            result = merge_alarm_documents(de_data, en_data, version, context, report)
        else:
            result = merge_register_documents(de_data, en_data, version, context, report)
        destination = destination_version / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    version_summary = {
        key: report["summary"][key] - before.get(key, 0)
        for key in report["summary"]
    }
    report["versions"][version] = version_summary
    return version_summary
