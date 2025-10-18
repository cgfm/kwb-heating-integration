# KWB ModbusInfo to JSON Converter

A powerful conversion tool that transforms KWB ModbusInfo Excel files (.xlsx) into structured JSON configuration files for the KWB Heating Home Assistant integration.

## 🎯 Features

- **Multi-version support** - Handles different KWB firmware versions (v22.7.1, v25.7.1, etc.)
- **Multi-language support** - Processes both German and English Excel files
- **Automatic device categorization** - Separates universal, device-specific, and equipment registers
- **Combifire inheritance** - CF models (CF 1, CF 1.5, CF 2) inherit from Combifire base with override support
- **Universal register aggregation** - Combines Universal and WMM Autonom (Modbus Lifetick) registers
- **Consistent naming** - Uses English filenames for all equipment files across languages
- **Value table extraction** - Converts enum value tables for state translations
- **Alarm code processing** - Extracts alarm/error code definitions with descriptions

## 📋 Prerequisites

Install the required Python library:

### Ubuntu/Debian
```bash
sudo apt install python3-openpyxl
```

### Using pip (recommended for virtual environments)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install openpyxl
```

## 📁 Input File Structure

### Expected Filename Format
```
ModbusInfo-{language}-V{version}.xlsx
```

Examples:
- `ModbusInfo-de-V22.7.1.xlsx` (German, Version 22.7.1)
- `ModbusInfo-en-V22.7.1.xlsx` (English, Version 22.7.1)
- `ModbusInfo-de-V25.7.1.xlsx` (German, Version 25.7.1)
- `ModbusInfo-en-V25.7.1.xlsx` (English, Version 25.7.1)

### Excel Sheet Structure

The converter expects the following sheets in the Excel file:

#### Universal Sheets
- **Universal** - Universal registers available on all KWB systems
- **WMM Autonom** - Modbus Lifetick registers (merged into universal)

#### Device Sheets (Device-Specific Registers)
- **KWB Easyfire** - Easyfire pellet boiler
- **KWB EF3** - Easyfire 3 variant (v25+)
- **KWB Multifire** - Multi-fuel boiler
- **KWB Pelletfire+** - Pelletfire Plus model
- **KWB Combifire** - Base registers for all CF models
- **KWB CF 1** - Combifire variant 1 (inherits from Combifire)
- **KWB CF 1.5** - Combifire variant 1.5 (inherits from Combifire)
- **KWB CF 2** - Combifire variant 2 (inherits from Combifire)
- **KWB EasyAir Plus** - Heat pump model (v25+)

#### Equipment Sheets (German / English)
- **Heizkreise** / **Heating circuits** - Heating circuit registers
- **Pufferspeicher** / **Buffer storage tank** - Buffer storage registers
- **Brauchwasserspeicher** / **DHWC** - Domestic hot water storage
- **Zweitwärmequellen** / **Secondary heating sources** - Secondary heat sources
- **Zirkulation** / **Circulation** - Hot water circulation
- **Solar** / **Solar** - Solar thermal system
- **Kesselfolgeschaltung** / **Boiler master-and-slave circuit** - Boiler sequence control
- **Wärmemengenzähler** / **Heat quantity meter** - Heat meters
- **Übergabestation** / **Transfer station** - Transfer station (v25+)

#### Additional Sheets
- **ValueTables** - Enum value mappings (state translations)
- **Alarms** - Alarm and error code definitions

### Excel Column Structure

Each register sheet must contain the following columns:

- **StartingAddress** - Modbus register address (decimal)
- **Name** - Register name/description
- **Functions** - Modbus function code (03, 04)
- **Type** - Data type (u16, s16, u32, s32, etc.)
- **UserLevel** - User access level (read, readwrite)
- **ExpertLevel** - Expert access level (read, readwrite)
- **NumberOfRegisters** - Number of registers (optional, default: 1)
- **Index** - Equipment index (e.g., "HK 1.1", "PUF 0")
- **Unit/ValueTable** - Unit or value table reference
- **Min** - Minimum value (optional)
- **Max** - Maximum value (optional)
- **ID** - KWB parameter ID
- **Parameter** - KWB parameter path

## 🚀 Usage

### 1. Prepare Input Files

Place your KWB ModbusInfo Excel files in the `modbusinfo/` subdirectory:

```bash
modbusinfoConverter/
├── modbusinfo/
│   ├── ModbusInfo-de-V22.7.1.xlsx
│   ├── ModbusInfo-en-V22.7.1.xlsx
│   ├── ModbusInfo-de-V25.7.1.xlsx
│   └── ModbusInfo-en-V25.7.1.xlsx
├── convert_modbusinfo.py
└── README.md
```

### 2. Run the Converter

```bash
cd modbusinfoConverter
python3 convert_modbusinfo.py
```

### 3. Conversion Output

The converter will display progress information:

```
INFO: KWB ModbusInfo to JSON Converter
INFO: Found 4 files to convert

INFO: Converting ModbusInfo-de-V22.7.1.xlsx...
INFO:   Reading Universal sheet...
INFO:     Found 9 registers
INFO:   Reading WMM Autonom sheet...
INFO:     Found 2 registers
INFO:   Created modbus_registers.json with 11 universal registers
INFO:   Reading KWB Combifire sheet (base for CF models)...
INFO:     Found 66 base registers
INFO:   Reading KWB CF 1 sheet...
INFO:     Merging 26 specific registers with 66 Combifire base registers...
INFO:     Result: 68 total registers
INFO:     Created devices/kwb_cf1.json with 68 registers
...
INFO: ✓ Successfully converted ModbusInfo-de-V22.7.1.xlsx
```

## 📂 Output Structure

The converter creates a version and language-specific directory structure:

```
config/versions/
├── v22.7.1/
│   ├── de/
│   │   ├── modbus_registers.json       # Universal + WMM Autonom registers
│   │   ├── value_tables.json           # Enum value mappings
│   │   ├── alarm_codes.json            # Alarm/error codes
│   │   ├── devices/
│   │   │   ├── kwb_easyfire.json       # Easyfire-specific registers
│   │   │   ├── kwb_multifire.json      # Multifire-specific registers
│   │   │   ├── kwb_pelletfire_plus.json
│   │   │   ├── kwb_combifire.json      # Combifire base registers
│   │   │   ├── kwb_cf1.json            # CF 1 (Combifire + specific)
│   │   │   ├── kwb_cf1_5.json          # CF 1.5 (Combifire + specific)
│   │   │   └── kwb_cf2.json            # CF 2 (Combifire + specific)
│   │   └── equipment/
│   │       ├── heating_circuits.json   # Heating circuit registers
│   │       ├── buffer_storage.json     # Buffer storage registers
│   │       ├── dhw_storage.json        # DHW storage registers
│   │       ├── secondary_heat_sources.json
│   │       ├── circulation.json
│   │       ├── solar.json
│   │       ├── boiler_sequence.json
│   │       └── heat_meters.json
│   └── en/
│       └── (same structure as de/)
└── v25.7.1/
    ├── de/
    │   ├── devices/
    │   │   ├── kwb_easyfire.json
    │   │   ├── kwb_ef3.json            # New in v25
    │   │   ├── kwb_easyair_plus.json   # New in v25
    │   │   └── ...
    │   └── equipment/
    │       ├── transfer_station.json   # New in v25
    │       └── ...
    └── en/
        └── (same structure as de/)
```

## 📄 Output File Formats

### modbus_registers.json
Contains universal registers applicable to all KWB systems:

```json
{
  "universal_registers": [
    {
      "starting_address": 8192,
      "name": "Software (major)",
      "data_type": "04",
      "type": "u16",
      "user_level": "read",
      "expert_level": "read",
      "id": "1163",
      "parameter": "SYSTEM.sw_version.major"
    },
    ...
  ]
}
```

### devices/*.json
Device-specific registers for each KWB model:

```json
{
  "registers": [
    {
      "starting_address": 8197,
      "name": "Kesseltemperatur Ist (value)",
      "data_type": "04",
      "type": "s16",
      "user_level": "read",
      "expert_level": "read",
      "unit_value_table": "1/10°C",
      "id": "589",
      "parameter": "KSM.i_kesseltemp_ist.value"
    },
    ...
  ]
}
```

### equipment/*.json
Equipment-specific registers with index information:

```json
{
  "registers": [
    {
      "starting_address": 8700,
      "name": "HK Programm",
      "data_type": "04",
      "type": "s16",
      "user_level": "read",
      "expert_level": "read",
      "unit_value_table": "hk_programm_t",
      "index": "HK 1.1",
      "id": "656",
      "parameter": "HK_<n>.programm"
    },
    ...
  ]
}
```

### value_tables.json
Enum value mappings for state translations:

```json
{
  "value_tables": {
    "hk_programm_t": {
      "0": "Automatik",
      "1": "Frostschutz",
      "2": "Aus",
      "3": "Komfort",
      "4": "Absenk"
    },
    ...
  }
}
```

### alarm_codes.json
Alarm and error code definitions:

```json
{
  "alarm_codes": [
    {
      "starting_address": 0,
      "function_code": "02",
      "alarm_id": "A000",
      "description": "Kesseltemperatur Sensor defekt"
    },
    ...
  ]
}
```

## 🔧 Special Features

### Combifire Inheritance

The converter implements intelligent register inheritance for CF models:

1. **Base Registers**: Reads all registers from "KWB Combifire" sheet
2. **Model-Specific Registers**: Reads CF 1, CF 1.5, CF 2 specific sheets
3. **Merging**: Combines base + specific, where specific registers override base by address
4. **Result**: Each CF model gets complete register set with model-specific overrides

**Example:**
- Combifire base: 66 registers
- CF 1 specific: 26 registers
- CF 1 result: 68 registers (66 from Combifire + 2 unique to CF 1)

### Universal Register Aggregation

- Combines "Universal" and "WMM Autonom" sheets
- WMM Autonom contains Modbus Lifetick registers (not device-specific)
- Both are merged into `modbus_registers.json`

### Consistent Equipment Filenames

Equipment files use English names regardless of Excel language:
- German "Heizkreise" → `heating_circuits.json`
- English "Heating circuits" → `heating_circuits.json`
- Both versions produce the same filename for compatibility

## 🔄 Integration with Home Assistant

After successful conversion, integrate the generated files:

### Method 1: Copy to Integration (Development)

```bash
# From modbusinfoConverter directory
cp -r config/versions/ ../custom_components/kwb_heating/config/
```

### Method 2: Replace Existing Config

```bash
# Backup existing config
mv ../custom_components/kwb_heating/config/versions \
   ../custom_components/kwb_heating/config/versions.backup

# Copy new config
cp -r config/versions ../custom_components/kwb_heating/config/
```

### Method 3: Update Specific Version/Language

```bash
# Update only German v25.7.1
cp -r config/versions/v25.7.1/de \
   ../custom_components/kwb_heating/config/versions/v25.7.1/
```

### After Integration

1. Restart Home Assistant
2. The integration will automatically use version-specific configs
3. Language is auto-detected from Home Assistant settings

## 🛠️ Customization

### Adding New Device Types

Edit `convert_modbusinfo.py`:

```python
DEVICE_SHEETS = [
    "KWB Easyfire",
    "KWB EF3",
    "KWB Multifire",
    "Your New Device",  # Add here
    ...
]

DEVICE_FILE_MAP = {
    ...
    "Your New Device": "your_new_device.json",  # Add mapping
}
```

### Adding New Equipment Types

```python
EQUIPMENT_SHEETS = {
    "German Name": "English Name",
    "Neue Ausstattung": "New Equipment",  # Add here
}

EQUIPMENT_FILE_MAP = {
    "German Name": "equipment_file.json",
    "English Name": "equipment_file.json",  # Same file for both
}
```

### Modifying Column Mappings

The `normalize_register()` method maps Excel columns to JSON fields:

```python
def normalize_register(self, data: dict) -> dict | None:
    register = {
        "starting_address": int(data.get("StartingAddress")),
        "name": str(data.get("Name", "")).strip(),
        # Modify or add fields here
    }
    return register
```

## 📊 Inspection Tool

For debugging Excel file structure, use the included inspection tool:

```bash
python3 inspect_excel.py
```

This displays:
- All available sheet names
- Sheet dimensions (rows/columns)
- Header row contents
- First 5 rows of data

## ⚠️ Important Notes

1. **Empty Rows**: Automatically skipped during conversion
2. **Address Format**: Only decimal addresses supported (not hexadecimal)
3. **Register Types**: Supports u16, s16, u32, s32, and other standard Modbus types
4. **Multi-register Values**: Use `NumberOfRegisters` column for 32-bit values
5. **Case Sensitivity**: Sheet names are case-sensitive
6. **Version Detection**: Version extracted from filename, not Excel content

## 🐛 Troubleshooting

### Problem: Empty JSON Files

**Symptom**: Generated JSON files have empty register arrays

**Solution**:
- Check Excel column names match expected format (StartingAddress, Name, etc.)
- Use `inspect_excel.py` to verify column headers
- Ensure data rows start at row 2 (row 1 is headers)

### Problem: Missing Device Files

**Symptom**: Some device files not created

**Solution**:
- Verify sheet name spelling in Excel matches `DEVICE_SHEETS` list
- Check that sheet contains data (not empty)
- Review console output for sheet processing messages

### Problem: Wrong Number of Registers for CF Models

**Symptom**: CF models have fewer registers than expected

**Solution**:
- Ensure "KWB Combifire" sheet exists in Excel
- Check that CF model sheet names match exactly ("KWB CF 1", not "CF1")
- Verify Combifire inheritance messages in converter output

### Problem: Equipment Files Not Created

**Symptom**: Equipment directory empty or missing files

**Solution**:
- For German Excel: Check sheet names match `EQUIPMENT_SHEETS` keys
- For English Excel: Check sheet names match `EQUIPMENT_SHEETS` values
- Verify equipment file mappings in `EQUIPMENT_FILE_MAP`

### Problem: Value Tables Not Working

**Symptom**: Enum values show as numbers instead of text

**Solution**:
- Verify "ValueTables" sheet exists
- Check ValueTables format: Column 1 = table name, Column 2 = value, Column 3 = translation
- Ensure value_tables.json is not empty

## 📝 Development Tips

### Testing Single File

Modify `convert_all()` to process specific files:

```python
def convert_all(self) -> None:
    xlsx_files = list(self.input_dir.glob("ModbusInfo-de-V22.7.1.xlsx"))
    # Only process German v22.7.1 for testing
```

### Verbose Output

Already enabled by default via logging. For more detail, modify log level:

```python
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
```

### Validating Output

Use Python to validate generated JSON:

```bash
python3 -m json.tool config/versions/v22.7.1/de/modbus_registers.json
```

## 🔄 Version History

### Latest Changes
- ✅ Combifire inheritance for CF models
- ✅ WMM Autonom merged into universal registers
- ✅ Consistent English equipment filenames
- ✅ Multi-language equipment sheet support
- ✅ KWB EasyAir Plus support (v25+)
- ✅ Transfer station equipment (v25+)

## 📞 Support

For issues or questions:
- **Integration Issues**: [KWB Heating Integration Issues](https://github.com/cgfm/kwb-heating-integration/issues)
- **Converter Issues**: Report in main integration repository with "[Converter]" prefix
- **Feature Requests**: Use GitHub Discussions

---

**Part of the KWB Heating Integration for Home Assistant**
