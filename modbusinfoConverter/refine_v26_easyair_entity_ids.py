#!/usr/bin/env python3
"""Refine only unpublished v26.6.1 EasyAir entity IDs."""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
from typing import Any

try:
    from config_validation import logical_register_key
except ImportError:  # Imported as a package by regression tests.
    from .config_validation import logical_register_key


VERSION = "v26.6.1"
EASYAIR_FILE = Path("devices/kwb_easyair_plus.json")

# Explicitly reviewed from the German name, parameter, unit/type, neighboring
# registers, and established English vocabulary in the canonical tree. The
# instance prefix is added mechanically; mappings never depend on addresses.
APPROVED_SUFFIXES = {
    "EAP.eigener_kuehlpuffer": "dedicated_cooling_buffer",
    "EAP.kuehlfunktion": "cooling_function",
    "EAP.sg_pufferladung_modbus": "smart_grid_buffer_charging_via_modbus",
    "EAP.sg_rtemp_ueberh_modbus": (
        "smart_grid_room_temperature_increase_via_modbus"
    ),
    "EAPDEV.anforderung_ursache": "demand_cause",
    "EAPDEV.ansauglufttemperatur": "intake_air_temperature",
    "EAPDEV.aufgenommene_elektr_leistung": "electrical_power_consumption",
    "EAPDEV.cop": "cop",
    "EAPDEV.drehzahl_ist": "compressor_speed_actual",
    "EAPDEV.drehzahl_soll": "compressor_speed_setpoint",
    "EAPDEV.drehzahl_ventilator": "fan_speed",
    "EAPDEV.erweiterter_betriebsstatus": "extended_operating_status",
    "EAPDEV.fluester1_beginn": "quiet_mode_1_start_time",
    "EAPDEV.fluester1_ende": "quiet_mode_1_end_time",
    "EAPDEV.fluester2_beginn": "quiet_mode_2_start_time",
    "EAPDEV.fluester2_ende": "quiet_mode_2_end_time",
    "EAPDEV.fluester_max_drehzahl": "quiet_mode_maximum_speed",
    "EAPDEV.heissgastemperatur": "hot_gas_temperature",
    "EAPDEV.hochdruck": "high_pressure_relative",
    "EAPDEV.kondensationstemperatur": "condensation_temperature",
    "EAPDEV.leistungsbegrenzung": "power_limit",
    "EAPDEV.max_leistung_heizen": "maximum_heating_power",
    "EAPDEV.max_leistung_kuehlen": "maximum_cooling_power",
    "EAPDEV.max_leistung_warmwasser": "maximum_hot_water_power",
    "EAPDEV.min_elekt_leistung_mb_begrenzung": (
        "minimum_electrical_power_modbus_limit"
    ),
    "EAPDEV.min_leistung_heizen": "minimum_heating_power",
    "EAPDEV.min_leistung_kuehlen": "minimum_cooling_power",
    "EAPDEV.min_leistung_warmwasser": "minimum_hot_water_power",
    "EAPDEV.modbus_el_leistungsbegr_aktiv": (
        "modbus_electrical_power_limit_active"
    ),
    "EAPDEV.modbus_max_elektr_leistung_heiz": (
        "modbus_maximum_electrical_power_heating"
    ),
    "EAPDEV.modbus_max_elektr_leistung_ww": (
        "modbus_maximum_electrical_power_hot_water"
    ),
    "EAPDEV.modbus_max_verdichterdrehz_soll": (
        "modbus_maximum_compressor_speed_setpoint"
    ),
    "EAPDEV.modbus_vorlauf_soll": "modbus_forward_flow_temperature_setpoint",
    "EAPDEV.momentanleistung": "current_heat_output",
    "EAPDEV.niederdruck": "low_pressure_relative",
    "EAPDEV.position_erstes_expansionsventil": (
        "first_expansion_valve_position"
    ),
    "EAPDEV.position_zweites_expansionsventi": (
        "second_expansion_valve_position"
    ),
    "EAPDEV.sauggastemperatur": "suction_gas_temperature",
    "EAPDEV.sollwert_heizkreisbetrieb": "heating_setpoint",
    "EAPDEV.sollwert_kuehlbetrieb": "cooling_setpoint",
    "EAPDEV.sollwert_speicherbetrieb": "hot_water_setpoint",
    "EAPDEV.temperatur_fluessigkeitsleitung": "liquid_line_temperature",
    "EAPDEV.ueberhitzung": "superheat",
    "EAPDEV.unterkuehlung": "subcooling",
    "EAPDEV.verdampfungstemperatur": "evaporation_temperature",
    "EAPDEV.volumenstrom": "flow_rate",
    "EAPDEV.volumenstrom_gemittelt": "average_flow_rate",
    "EAPDEV.vorlauftemperatur_soll": "forward_flow_temperature_setpoint",
    "EAPDEV.zustand_waermepumpe": "heat_pump_state",
}

# Repository evidence does not expand CP/ELH or fully explain the combined
# hot-gas/utility/electrical-limiting signal. Misleading names would be worse
# than retaining these unreleased review candidates.
MANUAL_REVIEW_REASONS = {
    "EAPDEV.bivalenz_elh": (
        "ELH is not expanded by canonical data; the boolean's exact equipment "
        "meaning cannot be named confidently."
    ),
    "EAPDEV.drehzahl_cp": (
        "CP is not expanded by canonical data, so the driven component is "
        "ambiguous despite the percent/speed unit."
    ),
    "EAPDEV.heissgas_evu_abschaltung_el_begr": (
        "The name and truncated parameter do not establish whether this means "
        "hot-gas shutdown, utility shutdown, or electrical limiting."
    ),
}


def _registers(data: dict[str, Any]) -> list[dict[str, Any]]:
    return data.get("registers", data.get("universal_registers", []))


def _prior_logical_keys(canonical_root: Path) -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    for version_dir in sorted(canonical_root.glob("v*")):
        if version_dir.name == VERSION:
            continue
        for path in version_dir.rglob("*.json"):
            relative = path.relative_to(version_dir)
            for register in _registers(json.loads(path.read_text(encoding="utf-8"))):
                key = logical_register_key(relative, register)
                if key is not None:
                    keys.add(key)
    return keys


def eligible_easyair_keys(
    canonical_root: Path,
) -> dict[tuple[str, str, str], dict[str, Any]]:
    """Return v26-only EasyAir identities lacking English source metadata."""
    prior = _prior_logical_keys(canonical_root)
    path = canonical_root / VERSION / EASYAIR_FILE
    result: dict[tuple[str, str, str], dict[str, Any]] = {}
    for register in _registers(json.loads(path.read_text(encoding="utf-8"))):
        key = logical_register_key(EASYAIR_FILE, register)
        name = register.get("name")
        if (
            key is not None
            and key not in prior
            and isinstance(name, dict)
            and not name.get("en")
        ):
            result[key] = register
    return result


def _proposed_entity_id(register: dict[str, Any], suffix: str) -> str:
    instance = register.get("equipment_instance")
    return f"eap_{instance}_{suffix}" if isinstance(instance, int) else f"eap_{suffix}"


def _original_pr_entity_id(register: dict[str, Any]) -> str:
    """Reconstruct the reviewed PR candidate independently of current output."""
    suffix = register["parameter"].split(".", 1)[1].lower()
    instance = register.get("equipment_instance")
    if isinstance(instance, int):
        return f"eap_{instance}_eapdev_{suffix}"
    return f"eap_{suffix}"


def refine_trees(
    project_root: Path, *, write: bool = False
) -> dict[str, Any]:
    """Build the review audit and optionally update generated/canonical trees."""
    canonical_root = project_root / "custom_components/kwb_heating/config/versions"
    generated_root = project_root / "modbusinfoConverter/config/versions"
    eligible = eligible_easyair_keys(canonical_root)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for register in eligible.values():
        groups[register["parameter"]].append(register)

    entries = []
    refined_ids = 0
    review_ids = 0
    for parameter, registers in sorted(groups.items()):
        registers.sort(key=lambda item: (item.get("equipment_instance", -1), item["starting_address"]))
        suffix = APPROVED_SUFFIXES.get(parameter)
        reason = MANUAL_REVIEW_REASONS.get(parameter)
        if suffix is None and reason is None:
            raise ValueError(f"Unreviewed eligible EasyAir parameter: {parameter}")
        proposed = (
            [_proposed_entity_id(register, suffix) for register in registers]
            if suffix is not None
            else [None] * len(registers)
        )
        if suffix is not None:
            refined_ids += len(registers)
        else:
            review_ids += len(registers)
        first = registers[0]
        entries.append(
            {
                "parameter": parameter,
                "current_entity_ids": [
                    _original_pr_entity_id(item) for item in registers
                ],
                "proposed_entity_ids": proposed,
                "proposed_suffix": suffix,
                "german_name": first.get("name", {}).get("de"),
                "supporting_context": {
                    "unit_or_value_table": first.get("unit_value_table"),
                    "type": first.get("type"),
                    "user_level": first.get("user_level"),
                    "expert_level": first.get("expert_level"),
                    "min": first.get("min"),
                    "max": first.get("max"),
                },
                "confidence": "reviewed" if suffix is not None else "manual_review",
                "review_status": "approved" if suffix is not None else "unresolved",
                "review_reason": reason,
                "affected_equipment_instances": [
                    item.get("equipment_instance") for item in registers
                ],
            }
        )

    if write:
        for tree_root in (generated_root, canonical_root):
            path = tree_root / VERSION / EASYAIR_FILE
            data = json.loads(path.read_text(encoding="utf-8"))
            for register in _registers(data):
                key = logical_register_key(EASYAIR_FILE, register)
                suffix = APPROVED_SUFFIXES.get(register.get("parameter"))
                if key in eligible and suffix is not None:
                    register["entity_id"] = _proposed_entity_id(register, suffix)
            path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    return {
        "firmware_version": VERSION,
        "scope": "v26-only EasyAir identities without English source metadata",
        "eligibility": (
            "No matching logical identity in canonical firmware before v26.6.1 "
            "and no English localized name in the v26.6.1 source."
        ),
        "summary": {
            "eligible_entity_ids": len(eligible),
            "eligible_parameter_groups": len(groups),
            "refined_entity_ids": refined_ids,
            "approved_parameter_groups": len(APPROVED_SUFFIXES),
            "manual_review_entity_ids": review_ids,
            "manual_review_parameter_groups": len(MANUAL_REVIEW_REASONS),
        },
        "entries": entries,
    }


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    report = refine_trees(project_root, write=True)
    audit_path = project_root / "modbusinfoConverter/v26_6_1_entity_id_refinement_audit.json"
    audit_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
