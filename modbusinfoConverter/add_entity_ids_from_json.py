#!/usr/bin/env python3
"""Add entity_id fields to generated template JSON using English data.

This script is useful when Excel source files are unavailable but a unified
multilingual generated JSON config exists. It generates language-independent
entity_id values from inline English metadata. It is not a production finalizer;
use import_generated_config.py for canonical config.
"""

import json
import re
from pathlib import Path


# Character replacements for entity ID sanitization (same as coordinator.py)
_ENTITY_ID_REPLACEMENTS = str.maketrans({
    " ": "_",
    ".": "_",
    "/": "_",
    "-": "_",
    ":": "_",
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",
    "Ä": "ae",
    "Ö": "oe",
    "Ü": "ue",
    "ß": "ss",
    "&": "and",
    "@": "at",
    "%": " percent ",
    "(": "",
    ")": "",
    "#": "",
    "!": "",
    "?": "",
    ",": "",
    ";": "",
    "'": "",
    '"': "",
})

# Equipment prefixes that are 0-indexed (need +1 for entity_id)
# Includes both English and German variants
ZERO_INDEXED_PREFIXES = {"PUF", "BUF", "ZIR", "Circ", "WMZ", "HQM", "Zirk"}

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


def sanitize_for_entity_id(name: str) -> str:
    """Sanitize a string for use in Home Assistant entity IDs."""
    if not name:
        return ""

    result = name.translate(_ENTITY_ID_REPLACEMENTS)
    result = result.lower()
    result = re.sub(r'[^a-z0-9_]', '', result)
    result = re.sub(r'_+', '_', result)
    result = result.strip('_')

    return result


def sanitize_index_for_entity_id(index: str) -> str | None:
    """Sanitize an index string for use in entity_id.

    Converts index like "SOL 1", "PUF 0", "HK 1.1" to entity_id format
    like "sol_1", "puf_1", "hk_1_1". Handles 0-indexed equipment by converting to 1-based.

    Args:
        index: The index string (e.g., "SOL 1", "PUF 0", "HK 1.1")

    Returns:
        Sanitized index string like "sol_1", "hk_1_1", or None if not applicable
    """
    if not index:
        return None

    # Split into prefix and number part
    parts = index.split(" ", 1)
    if len(parts) != 2:
        return None

    prefix = parts[0].strip()
    number_part = parts[1].strip()

    # Convert 0-indexed equipment to 1-based
    if prefix in ZERO_INDEXED_PREFIXES:
        try:
            num = int(number_part)
            number_part = str(num + 1)
        except ValueError:
            pass  # Keep original if not a simple number

    # Replace dots with underscores for heating circuits (HK 1.1 -> hk_1_1)
    sanitized_number = number_part.replace(".", "_")

    # Use a canonical prefix so fallback IDs remain language-independent.
    canonical_prefix = INDEX_PREFIX_MAP.get(prefix, prefix)
    sanitized_prefix = sanitize_for_entity_id(canonical_prefix)

    return f"{sanitized_prefix}_{sanitized_number}"


def load_english_data_from_json(
    version_dir: Path,
) -> dict[str, dict[int, dict[str, str]]]:
    """Load inline English register data from one unified version tree.

    Returns a mapping of relative filename -> starting_address -> register data.
    Addresses are not globally unique across device and equipment files.
    """
    english_data: dict[str, dict[int, dict[str, str]]] = {}

    for json_file in version_dir.rglob("*.json"):
        if json_file.name in ["value_tables.json", "alarm_codes.json"]:
            continue  # Skip non-register files

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle different JSON structures
            registers = []
            if "universal_registers" in data:
                registers = data["universal_registers"]
            elif "registers" in data:
                registers = data["registers"]

            file_data: dict[int, dict[str, str]] = {}
            for reg in registers:
                address = reg.get("starting_address")
                name_value = reg.get("name")
                index_value = reg.get("index")
                name = (
                    name_value.get("en")
                    if isinstance(name_value, dict)
                    else name_value
                )
                index = (
                    index_value.get("en")
                    if isinstance(index_value, dict)
                    else index_value
                )
                if address is not None and name:
                    entry = {"name": str(name).strip()}
                    if index:
                        entry["index"] = str(index).strip()
                    file_data[int(address)] = entry

            relative_path = json_file.relative_to(version_dir).as_posix()
            english_data[relative_path] = file_data

        except Exception as e:
            print(f"  Warning: Could not process {json_file}: {e}")

    return english_data


def add_entity_ids_to_registers(registers: list[dict], english_data: dict[int, dict[str, str]]) -> int:
    """Add or update entity_id field to registers list (includes index prefix).

    Also removes deprecated entity_index field if present.

    Returns count of registers updated.
    """
    updated = 0
    for reg in registers:
        address = reg.get("starting_address")
        if address is None:
            continue

        # Get English data, fall back to current register data
        en_data = english_data.get(int(address), {})
        english_name = en_data.get("name", "")
        english_index = en_data.get("index", "")
        if not english_name:
            print(
                "    REVIEW REQUIRED: no English name for entity_id generation "
                f"at address {address}; parameter={reg.get('parameter')!r}"
            )
            continue

        # Generate base entity_id from English name
        base_entity_id = sanitize_for_entity_id(english_name)

        # Include English index in entity_id if present
        if english_index:
            index_prefix = sanitize_index_for_entity_id(english_index)
            if index_prefix:
                entity_id = f"{index_prefix}_{base_entity_id}"
            else:
                entity_id = base_entity_id
        else:
            entity_id = base_entity_id

        # Check if update is needed
        current_entity_id = reg.get("entity_id", "")
        has_entity_index = "entity_index" in reg
        needs_update = (current_entity_id != entity_id) or has_entity_index

        if entity_id and needs_update:
            # Rebuild register with updated entity_id and without entity_index
            new_reg = {}
            for key, value in reg.items():
                if key == "entity_index":
                    continue  # Remove deprecated field
                if key == "entity_id":
                    continue  # Skip old entity_id, we'll insert the new one
                new_reg[key] = value
                if key == "name":
                    new_reg["entity_id"] = entity_id
            reg.clear()
            reg.update(new_reg)
            updated += 1

    return updated + make_entity_ids_unique(registers)


def make_entity_ids_unique(registers: list[dict]) -> int:
    """Give ambiguous duplicates review IDs without leaking parameter text."""
    seen: set[str] = set()
    updated = 0

    for reg in registers:
        entity_id = reg.get("entity_id")
        if not entity_id or entity_id not in seen:
            if entity_id:
                seen.add(entity_id)
            continue

        replacement = f"{entity_id}_review_register_{reg['starting_address']}"
        sequence = 2
        while replacement in seen:
            replacement = (
                f"{entity_id}_review_register_{reg['starting_address']}_{sequence}"
            )
            sequence += 1
        print(
            "    REVIEW REQUIRED: ambiguous English entity_id "
            f"{entity_id!r} at address {reg.get('starting_address')}; "
            f"parameter={reg.get('parameter')!r}, candidate={replacement!r}"
        )
        reg["entity_id"] = replacement
        seen.add(replacement)
        updated += 1

    return updated


def process_json_file(json_file: Path, english_data: dict[int, dict[str, str]]) -> bool:
    """Process a single JSON file to add entity_id fields.

    Returns True if file was modified.
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        modified = False

        # Handle different JSON structures
        if "universal_registers" in data:
            count = add_entity_ids_to_registers(data["universal_registers"], english_data)
            if count > 0:
                modified = True
                print(f"    Updated {count} universal registers")

        if "registers" in data:
            count = add_entity_ids_to_registers(data["registers"], english_data)
            if count > 0:
                modified = True
                print(f"    Updated {count} registers")

        if modified:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True

    except Exception as e:
        print(f"  Error processing {json_file}: {e}")

    return False


def process_version(version_dir: Path) -> None:
    """Process a version directory to add entity_id fields."""
    print(f"  Loading inline English data from {version_dir}...")
    english_data_by_file = load_english_data_from_json(version_dir)
    entry_count = sum(len(entries) for entries in english_data_by_file.values())
    print(f"  Loaded {entry_count} English entries")

    for json_file in version_dir.rglob("*.json"):
        if json_file.name in ["value_tables.json", "alarm_codes.json"]:
            continue

        relative = json_file.relative_to(version_dir)
        print(f"    {relative}...")
        english_data = english_data_by_file.get(relative.as_posix(), {})
        process_json_file(json_file, english_data)


def main():
    """Main entry point."""
    import sys

    # Operate only on non-canonical converter templates by default.
    script_dir = Path(__file__).parent
    config_dir = script_dir / "config" / "versions"

    # Allow specifying a specific version
    if len(sys.argv) > 1:
        version = sys.argv[1]
        version_dirs = [config_dir / f"v{version}"]
    else:
        # Process all versions
        version_dirs = sorted(config_dir.glob("v*"))

    print("Adding entity_id fields to JSON configs")
    print(f"Config directory: {config_dir}")
    print("=" * 60)

    for version_dir in version_dirs:
        if not version_dir.is_dir():
            continue

        print(f"\nProcessing {version_dir.name}...")
        process_version(version_dir)

    print("\n" + "=" * 60)
    print("Done!")


if __name__ == "__main__":
    main()
