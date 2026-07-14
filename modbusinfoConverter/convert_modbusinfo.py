#!/usr/bin/env python3
"""Convert KWB ModbusInfo Excel files to JSON configuration format."""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

try:
    import openpyxl
except ImportError:
    print("Error: openpyxl library is required. Install with: pip install openpyxl")
    sys.exit(1)

from entity_id_generation import compute_entity_id

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class ModbusInfoConverter:
    """Converts ModbusInfo Excel files to JSON configuration.

    German and English source files for a version are processed together and
    merged into a single output tree: every register's "name" and "index"
    become {"de": ..., "en": ...}, and everything else (which is already
    identical between languages) stays flat. This is the single source of
    truth for a version - there is no more separate de/ and en/ output tree,
    so "this register exists in German but not English" (or vice versa) is
    something the merge step must decide and log, not something that can
    silently happen.
    """

    # Sheet categories
    #UNIVERSAL_SHEET = "Universal"
    # WMM Autonom is NOT a device - it contains universal Modbus lifetick registers
    UNIVERSAL_SHEETS = ["Universal"]

    DEVICE_SHEETS = [
        "KWB Easyfire", "KWB EF3", "KWB Multifire", "KWB Pelletfire+",
        "KWB Combifire", "KWB CF 2", "KWB CF 1", "KWB CF 1.5",
        "KWB EasyAir Plus"
    ]

    # Equipment sheet names (German and English)
    EQUIPMENT_SHEETS = {
        # German: English
        "Heizkreise": "Heating circuits",
        "Pufferspeicher": "Buffer storage tank",
        "Brauchwasserspeicher": "DHWC",
        "Zweitwärmequellen": "Secondary heating sources",
        "Zirkulation": "Circulation",
        "Solar": "Solar",
        "Kesselfolgeschaltung": "Boiler master-and-slave circuit",
        "Wärmemengenzähler": "Heat quantity meter",
        "Übergabestation": "Transfer station",
    }

    ALARMS_SHEET = "Alarms"
    VALUE_TABLES_SHEET = "ValueTables"

    # Required value tables that must always be present (may be missing from Excel)
    # Format: {table_name: {language: {value: translation}}}
    REQUIRED_VALUE_TABLES = {
        "system_ein_aus_t": {
            "en": {"0": "Off", "1": "On"},
            "de": {"0": "Aus", "1": "Ein"},
        }
    }

    # Use consistent English filenames for equipment
    EQUIPMENT_FILE_MAP = {
        "Heizkreise": "heating_circuits.json",
        "Heating circuits": "heating_circuits.json",
        "Pufferspeicher": "buffer_storage.json",
        "Buffer storage tank": "buffer_storage.json",
        "Brauchwasserspeicher": "dhw_storage.json",
        "DHWC": "dhw_storage.json",
        "Zweitwärmequellen": "secondary_heat_sources.json",
        "Secondary heating sources": "secondary_heat_sources.json",
        "Zirkulation": "circulation.json",
        "Circulation": "circulation.json",
        "Solar": "solar.json",
        "Kesselfolgeschaltung": "boiler_sequence.json",
        "Boiler master-and-slave circuit": "boiler_sequence.json",
        "Wärmemengenzähler": "heat_meters.json",
        "Heat quantity meter": "heat_meters.json",
        "Übergabestation": "transfer_station.json",
        "Transfer station": "transfer_station.json",
    }

    # Map device sheet names to filenames
    DEVICE_FILE_MAP = {
        "KWB Easyfire": "kwb_easyfire.json",
        "KWB EF3": "kwb_ef3.json",
        "KWB Multifire": "kwb_multifire.json",
        "KWB Pelletfire+": "kwb_pelletfire_plus.json",
        "KWB Combifire": "kwb_combifire.json",
        "KWB CF 2": "kwb_cf2.json",
        "KWB CF 1": "kwb_cf1.json",
        "KWB CF 1.5": "kwb_cf1_5.json",
        "KWB EasyAir Plus": "kwb_easyair_plus.json",
    }

    def __init__(self, input_dir: Path, output_dir: Path):
        """Initialize converter."""
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)

    def parse_filename(self, filename: str) -> dict[str, str]:
        """Parse ModbusInfo filename to extract version and language."""
        match = re.match(r'ModbusInfo-(\w+)-V(\d+\.\d+\.\d+)\.xlsx', filename, re.IGNORECASE)
        if match:
            language = match.group(1).lower()
            version = match.group(2)
            return {"language": language, "version": version}
        return {}

    def read_register_sheet(self, workbook: openpyxl.Workbook, sheet_name: str) -> list[dict]:
        """Read register data from an Excel sheet (single language, flat name/index)."""
        if sheet_name not in workbook.sheetnames:
            return []

        sheet = workbook[sheet_name]
        registers = []

        # Get header row
        headers = [cell.value for cell in sheet[1]]

        # Read data rows (skip header)
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not any(row) or row[0] is None:  # Skip empty rows or rows without address
                continue

            row_dict = {}
            for i, value in enumerate(row):
                if i < len(headers) and headers[i]:
                    row_dict[headers[i]] = value

            register = self.normalize_register(row_dict)
            if register:
                registers.append(register)

        return registers

    def normalize_register(self, data: dict) -> dict | None:
        """Normalize a single register row to standard format (single language,
        flat name/index - the bilingual merge happens later in
        merge_bilingual_registers())."""
        # Skip if no address
        address = data.get("StartingAddress")
        if address is None:
            return None

        address_int = int(address)
        name = str(data.get("Name", "")).strip() if data.get("Name") else ""

        # Build normalized register
        register = {
            "starting_address": address_int,
            "name": name,
            "data_type": self._parse_function_code(data.get("Functions")),
            "type": str(data.get("Type", "u16")).strip().lower(),
            "user_level": self._parse_access_level(data.get("UserLevel")),
            "expert_level": self._parse_access_level(data.get("ExpertLevel")),
        }

        # Keep the original index field for display purposes
        if data.get("Index"):
            register["index"] = str(data.get("Index")).strip()

        if data.get("Unit/ValueTable"):
            unit_or_table = str(data.get("Unit/ValueTable")).strip()
            register["unit_value_table"] = unit_or_table

        if data.get("Min") is not None:
            register["min"] = data.get("Min")

        if data.get("Max") is not None:
            register["max"] = data.get("Max")

        if data.get("NumberOfRegisters"):
            num_regs = data.get("NumberOfRegisters")
            if num_regs and num_regs != 1:
                register["number_of_registers"] = int(num_regs)

        if data.get("ID"):
            register["id"] = str(data.get("ID"))

        if data.get("Parameter"):
            register["parameter"] = str(data.get("Parameter"))

        # Remove empty string values
        register = {k: v for k, v in register.items() if v not in [None, ""]}

        return register if register.get("starting_address") and register.get("name") else None

    def _parse_function_code(self, functions: Any) -> str:
        """Parse Modbus function code(s)."""
        if not functions:
            return "04"

        func_str = str(functions).strip()

        # Check for common function codes
        if "04" in func_str:
            return "04"  # Input registers (read-only)
        if "03" in func_str:
            return "03"  # Holding registers (read-write potential)

        return "04"  # Default to input registers

    def _parse_access_level(self, access: Any) -> str:
        """Parse access level."""
        if not access:
            return "read"

        access_str = str(access).lower().strip()

        if "readwrite" in access_str or "rw" in access_str:
            return "readwrite"
        elif "write" in access_str:
            return "write"
        elif "read" in access_str:
            return "read"

        return "read"

    def read_value_tables(self, workbook: openpyxl.Workbook) -> dict:
        """Read value tables from Excel (single language)."""
        if self.VALUE_TABLES_SHEET not in workbook.sheetnames:
            return {}

        sheet = workbook[self.VALUE_TABLES_SHEET]
        value_tables = {}

        # Read rows (skip header)
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not any(row) or row[0] is None:
                continue

            table_name = str(row[0]).strip() if row[0] else None
            value = row[1]
            translation = str(row[2]).strip() if len(row) > 2 and row[2] else None

            if table_name and value is not None and translation:
                if table_name not in value_tables:
                    value_tables[table_name] = {}
                value_tables[table_name][str(value)] = translation

        return value_tables

    def ensure_required_value_tables(self, value_tables: dict, language: str) -> dict:
        """Ensure all required value tables are present.

        Some value tables (like system_ein_aus_t) are referenced in equipment files
        but may be missing from the Excel ValueTables sheet. This method adds them
        if they're not present.

        Args:
            value_tables: The value tables read from Excel
            language: The language code ('en' or 'de')

        Returns:
            Updated value_tables dict with required tables added if missing
        """
        for table_name, translations in self.REQUIRED_VALUE_TABLES.items():
            if table_name not in value_tables:
                if language in translations:
                    value_tables[table_name] = translations[language]
                    logger.info(f"    Added missing required value table: {table_name}")
                elif "en" in translations:
                    # Fallback to English if language not found
                    value_tables[table_name] = translations["en"]
                    logger.info(f"    Added missing required value table: {table_name} (fallback to en)")

        return value_tables

    def read_alarm_codes(self, workbook: openpyxl.Workbook) -> list[dict]:
        """Read alarm codes from Excel (single language)."""
        if self.ALARMS_SHEET not in workbook.sheetnames:
            return []

        sheet = workbook[self.ALARMS_SHEET]
        alarm_codes = []

        # Read rows (skip header)
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not any(row) or row[0] is None:
                continue

            alarm = {
                "starting_address": int(row[0]) if row[0] is not None else None,
                "function_code": str(row[1]).strip() if len(row) > 1 and row[1] else "02",
                "alarm_id": str(row[2]).strip() if len(row) > 2 and row[2] else "",
                "description": str(row[3]).strip() if len(row) > 3 and row[3] else "",
            }

            if alarm["starting_address"] is not None:
                alarm_codes.append(alarm)

        return alarm_codes

    def merge_registers(self, base_registers: list[dict], override_registers: list[dict]) -> list[dict]:
        """Merge two same-language register lists, override wins by address.

        Used for Combifire base + CF-model-specific overrides, both still in
        a single language at this point (bilingual merging happens later).
        """
        merged = {reg["starting_address"]: reg for reg in base_registers}
        for reg in override_registers:
            merged[reg["starting_address"]] = reg
        return sorted(merged.values(), key=lambda x: x["starting_address"])

    # Fields expected to stay flat (identical between languages) even if a
    # future version's data disagrees - "parameter" is the manufacturer's own
    # key and the others are structural, so a mismatch there is a data
    # problem worth surfacing loudly rather than silently becoming a
    # per-language dict.
    _STRUCTURAL_FIELDS = {
        "starting_address", "parameter", "data_type", "type",
        "user_level", "expert_level", "id",
    }

    def merge_bilingual_registers(
        self, de_registers: list[dict], en_registers: list[dict], context: str
    ) -> list[dict]:
        """Merge German and English register lists into one, keyed by address.

        Any field whose value actually differs between languages (typically
        "name" and "index", but e.g. "unit_value_table" can too - German
        "Upm" vs English "rpm" for the same rpm register) becomes
        {"de": ..., "en": ...}; fields that are identical (the common case)
        stay flat. A register present in only one language is kept, with the
        other language's per-field values left absent - this is exactly the
        gap that used to cause silent entity_id collisions (e.g. EasyAir
        Plus), so it's logged here instead of hidden.
        """
        de_by_addr = {r["starting_address"]: r for r in de_registers}
        en_by_addr = {r["starting_address"]: r for r in en_registers}
        all_addrs = sorted(set(de_by_addr) | set(en_by_addr))

        merged: list[dict] = []
        for addr in all_addrs:
            de_reg = de_by_addr.get(addr)
            en_reg = en_by_addr.get(addr)

            if de_reg is None:
                logger.warning(
                    f"{context}: address {addr} ('{en_reg.get('name')}') present in "
                    f"English only - missing from the German sheet"
                )
            if en_reg is None:
                logger.warning(
                    f"{context}: address {addr} ('{de_reg.get('name')}') present in "
                    f"German only - missing from the English sheet"
                )

            base = de_reg or en_reg
            all_keys = set(de_reg or {}) | set(en_reg or {})
            combined: dict[str, Any] = {}

            for key in all_keys:
                de_val = de_reg.get(key) if de_reg else None
                en_val = en_reg.get(key) if en_reg else None

                if key in self._STRUCTURAL_FIELDS:
                    if de_reg and en_reg and de_val != en_val:
                        logger.warning(
                            f"{context}: address {addr} has different {key!r} between "
                            f"languages (de={de_val!r}, en={en_val!r}) - using "
                            f"{'de' if base is de_reg else 'en'}"
                        )
                    combined[key] = base.get(key)
                elif de_val == en_val:
                    combined[key] = de_val
                else:
                    combined[key] = {"de": de_val, "en": en_val}

            entity_id = compute_entity_id(combined)
            if entity_id:
                combined["entity_id"] = entity_id

            combined = {
                k: v for k, v in combined.items()
                if v not in (None, "") and v != {"de": None, "en": None}
            }
            merged.append(combined)

        return merged

    def merge_bilingual_value_tables(self, de_tables: dict, en_tables: dict, context: str) -> dict:
        """Merge German/English value tables into {table: {value: {de, en}}}."""
        all_table_names = sorted(set(de_tables) | set(en_tables))
        merged: dict[str, dict[str, dict[str, str]]] = {}

        for table_name in all_table_names:
            de_values = de_tables.get(table_name, {})
            en_values = en_tables.get(table_name, {})
            all_values = sorted(set(de_values) | set(en_values), key=lambda v: (len(v), v))

            merged_table = {}
            for value in all_values:
                de_text = de_values.get(value)
                en_text = en_values.get(value)
                if de_text is None:
                    logger.warning(
                        f"{context}: value table '{table_name}' value {value!r} missing German translation"
                    )
                if en_text is None:
                    logger.warning(
                        f"{context}: value table '{table_name}' value {value!r} missing English translation"
                    )
                merged_table[value] = {"de": de_text, "en": en_text}

            merged[table_name] = merged_table

        return merged

    def merge_bilingual_alarm_codes(
        self, de_alarms: list[dict], en_alarms: list[dict], context: str
    ) -> list[dict]:
        """Merge German/English alarm codes by starting_address; description
        becomes {"de": ..., "en": ...}."""
        de_by_addr = {a["starting_address"]: a for a in de_alarms}
        en_by_addr = {a["starting_address"]: a for a in en_alarms}
        all_addrs = sorted(set(de_by_addr) | set(en_by_addr))

        merged = []
        for addr in all_addrs:
            de_alarm = de_by_addr.get(addr)
            en_alarm = en_by_addr.get(addr)
            base = de_alarm or en_alarm

            combined = dict(base)
            combined["description"] = {
                "de": de_alarm["description"] if de_alarm else None,
                "en": en_alarm["description"] if en_alarm else None,
            }
            combined = {k: v for k, v in combined.items() if v not in (None, "")}
            merged.append(combined)

        return merged

    def _read_all_sheets(self, workbook: openpyxl.Workbook, language: str) -> dict[str, Any]:
        """Read every sheet of a single-language workbook into raw (unmerged)
        per-category register/value-table/alarm data."""
        universal_registers = []
        for sheet_name in self.UNIVERSAL_SHEETS:
            if sheet_name in workbook.sheetnames:
                registers = self.read_register_sheet(workbook, sheet_name)
                universal_registers.extend(registers)
                logger.info(f"  [{language}] {sheet_name}: {len(registers)} registers")

        combifire_base_registers = []
        if "KWB Combifire" in workbook.sheetnames:
            combifire_base_registers = self.read_register_sheet(workbook, "KWB Combifire")
            logger.info(f"  [{language}] KWB Combifire (base): {len(combifire_base_registers)} registers")

        cf_models = ["KWB CF 1", "KWB CF 1.5", "KWB CF 2"]
        device_registers: dict[str, list[dict]] = {}
        for sheet_name in self.DEVICE_SHEETS:
            if sheet_name == "KWB Combifire":
                continue
            if sheet_name not in workbook.sheetnames:
                continue

            regs = self.read_register_sheet(workbook, sheet_name)
            if sheet_name in cf_models and combifire_base_registers:
                regs = self.merge_registers(combifire_base_registers, regs)
            if regs:
                device_registers[sheet_name] = regs
                logger.info(f"  [{language}] {sheet_name}: {len(regs)} registers")

        if combifire_base_registers:
            device_registers["KWB Combifire"] = combifire_base_registers

        equipment_registers: dict[str, list[dict]] = {}
        all_equipment_sheets = list(self.EQUIPMENT_SHEETS.keys()) + list(self.EQUIPMENT_SHEETS.values())
        processed_equipment_files = set()
        for sheet_name in all_equipment_sheets:
            if sheet_name not in workbook.sheetnames:
                continue
            filename = self.EQUIPMENT_FILE_MAP.get(sheet_name)
            if not filename or filename in processed_equipment_files:
                continue
            regs = self.read_register_sheet(workbook, sheet_name)
            if regs:
                equipment_registers[filename] = regs
                processed_equipment_files.add(filename)
                logger.info(f"  [{language}] {sheet_name}: {len(regs)} registers")

        value_tables = self.read_value_tables(workbook)
        value_tables = self.ensure_required_value_tables(value_tables, language)
        alarm_codes = self.read_alarm_codes(workbook)

        return {
            "universal_registers": universal_registers,
            "device_registers": device_registers,  # sheet_name -> registers
            "equipment_registers": equipment_registers,  # filename -> registers
            "value_tables": value_tables,
            "alarm_codes": alarm_codes,
        }

    def convert_version(self, version: str, de_file: Path | None, en_file: Path | None) -> None:
        """Convert a version's German and English Excel files together into
        one merged output tree. Either file may be absent (converts what's
        available, with the missing language's name/index left blank)."""
        logger.info(f"Converting v{version} (de={de_file.name if de_file else None}, "
                    f"en={en_file.name if en_file else None})...")

        version_dir = self.output_dir / f"v{version}"
        version_dir.mkdir(parents=True, exist_ok=True)
        (version_dir / "devices").mkdir(exist_ok=True)
        (version_dir / "equipment").mkdir(exist_ok=True)

        data_by_lang: dict[str, dict[str, Any]] = {}
        for lang, xlsx_file in (("de", de_file), ("en", en_file)):
            if xlsx_file is None:
                data_by_lang[lang] = {
                    "universal_registers": [], "device_registers": {},
                    "equipment_registers": {}, "value_tables": {}, "alarm_codes": [],
                }
                continue
            try:
                workbook = openpyxl.load_workbook(xlsx_file, data_only=True)
            except Exception as exc:
                logger.error(f"Error loading workbook {xlsx_file}: {exc}")
                continue
            data_by_lang[lang] = self._read_all_sheets(workbook, lang)
            workbook.close()

        de_data = data_by_lang.get("de", {})
        en_data = data_by_lang.get("en", {})

        # Universal registers
        universal = self.merge_bilingual_registers(
            de_data.get("universal_registers", []), en_data.get("universal_registers", []),
            f"v{version}/modbus_registers.json"
        )
        with open(version_dir / "modbus_registers.json", 'w', encoding='utf-8') as f:
            json.dump({"universal_registers": universal}, f, indent=2, ensure_ascii=False)
        logger.info(f"  Created modbus_registers.json with {len(universal)} universal registers")

        # Device registers
        de_devices = de_data.get("device_registers", {})
        en_devices = en_data.get("device_registers", {})
        for sheet_name in sorted(set(de_devices) | set(en_devices)):
            filename = self.DEVICE_FILE_MAP.get(sheet_name, f"{sheet_name.lower().replace(' ', '_')}.json")
            merged = self.merge_bilingual_registers(
                de_devices.get(sheet_name, []), en_devices.get(sheet_name, []),
                f"v{version}/devices/{filename}"
            )
            with open(version_dir / "devices" / filename, 'w', encoding='utf-8') as f:
                json.dump({"registers": merged}, f, indent=2, ensure_ascii=False)
            logger.info(f"  Created devices/{filename} with {len(merged)} registers")

        # Equipment registers
        de_equipment = de_data.get("equipment_registers", {})
        en_equipment = en_data.get("equipment_registers", {})
        for filename in sorted(set(de_equipment) | set(en_equipment)):
            merged = self.merge_bilingual_registers(
                de_equipment.get(filename, []), en_equipment.get(filename, []),
                f"v{version}/equipment/{filename}"
            )
            with open(version_dir / "equipment" / filename, 'w', encoding='utf-8') as f:
                json.dump({"registers": merged}, f, indent=2, ensure_ascii=False)
            logger.info(f"  Created equipment/{filename} with {len(merged)} registers")

        # Value tables
        value_tables = self.merge_bilingual_value_tables(
            de_data.get("value_tables", {}), en_data.get("value_tables", {}),
            f"v{version}/value_tables.json"
        )
        with open(version_dir / "value_tables.json", 'w', encoding='utf-8') as f:
            json.dump({"value_tables": value_tables}, f, indent=2, ensure_ascii=False)
        logger.info(f"  Created value_tables.json with {len(value_tables)} tables")

        # Alarm codes
        alarm_codes = self.merge_bilingual_alarm_codes(
            de_data.get("alarm_codes", []), en_data.get("alarm_codes", []),
            f"v{version}/alarm_codes.json"
        )
        with open(version_dir / "alarm_codes.json", 'w', encoding='utf-8') as f:
            json.dump({"alarm_codes": alarm_codes}, f, indent=2, ensure_ascii=False)
        logger.info(f"  Created alarm_codes.json with {len(alarm_codes)} alarms")

        logger.info(f"✓ Successfully converted v{version}\n")

    def convert_all(self) -> None:
        """Convert all ModbusInfo Excel file pairs in the input directory,
        one version at a time (German + English together)."""
        xlsx_files = list(self.input_dir.glob("ModbusInfo*.xlsx"))

        if not xlsx_files:
            logger.error(f"No ModbusInfo*.xlsx files found in {self.input_dir}")
            return

        by_version: dict[str, dict[str, Path]] = {}
        for xlsx_file in xlsx_files:
            info = self.parse_filename(xlsx_file.name)
            if not info:
                logger.error(f"Could not parse filename: {xlsx_file.name}")
                continue
            by_version.setdefault(info["version"], {})[info["language"]] = xlsx_file

        logger.info(f"Found {len(xlsx_files)} files across {len(by_version)} version(s)\n")

        for version in sorted(by_version):
            files = by_version[version]
            if "de" not in files:
                logger.warning(f"v{version}: no German file found, converting English only")
            if "en" not in files:
                logger.warning(f"v{version}: no English file found, converting German only")
            try:
                self.convert_version(version, files.get("de"), files.get("en"))
            except Exception:
                logger.error(f"Error converting v{version}")
                import traceback
                traceback.print_exc()
                continue

        logger.info("=" * 60)
        logger.info("Conversion complete!")
        logger.info(f"Output directory: {self.output_dir}")


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    input_dir = script_dir / "modbusinfo"
    # Write directly into the integration's own config tree - this is the
    # single source of truth for register JSON. Do not also write to a
    # modbusinfoConverter-local config/versions/ copy; a second copy drifts
    # out of sync silently (as it did before this was consolidated).
    output_dir = script_dir.parent / "custom_components" / "kwb_heating" / "config" / "versions"

    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        sys.exit(1)

    logger.info("KWB ModbusInfo to JSON Converter")
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("=" * 60)
    logger.info("")

    converter = ModbusInfoConverter(input_dir, output_dir)
    converter.convert_all()


if __name__ == "__main__":
    main()
