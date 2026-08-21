# KWB Heating Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/cgfm/kwb-heating-integration)](https://github.com/cgfm/kwb-heating-integration/releases)
[![GitHub](https://img.shields.io/github/license/cgfm/kwb-heating-integration)](LICENSE)
[![AI Assisted](https://img.shields.io/badge/AI-Assisted%20Development-blueviolet.svg?style=for-the-badge)](#ai-assisted-development)

A comprehensive Home Assistant Custom Component for **KWB heating systems** with Modbus TCP, RTU over TCP, and serial RTU support.

> **⚠️ Testing Status**: This integration has been tested primarily with **KWB CF2**, **2 heating circuits**, and **1 buffer storage**. Testing with other KWB models and configurations is very welcome! Please help expand compatibility by testing with your setup and reporting results via [GitHub Issues](https://github.com/cgfm/kwb-heating-integration/issues).

## ⚠️ Breaking Changes (v0.5.0)

**If you are upgrading from a previous version, please read this section carefully.**

### Entity ID Changes - Language-Independent with Equipment Index

Entity IDs have been redesigned to be **fully language-independent** and now include the **equipment index prefix** for multi-instance equipment. This ensures entity IDs remain stable regardless of language selection and prevents Home Assistant from appending `_2`, `_3` suffixes.

#### New Entity ID Format

Entity IDs now follow this pattern:
```
sensor.{device_prefix}_{equipment_index}_{register_name}
```

**Examples:**
| Old Entity ID | New Entity ID |
|---------------|---------------|
| `sensor.cf2_temperature_1_value` | `sensor.cf2_buf_1_temperature_1_value` |
| `sensor.cf2_temperature_1_value_2` | `sensor.cf2_buf_2_temperature_1_value` |
| `sensor.cf2_forward_flow_temp` | `sensor.cf2_hc_1_forward_flow_temp` |
| `sensor.cf2_temperature_actual_value` | `sensor.cf2_dhwc_1_temperature_actual_value` |

#### Equipment Index Prefixes

All entity IDs use English-derived prefixes (language-independent):

| Equipment Type | Entity ID Prefix | Example |
|----------------|------------------|---------|
| Buffer Storage | `buf_1`, `buf_2`, ... | `sensor.cf2_buf_1_temperature_1_value` |
| DHW Storage | `dhwc_1`, `dhwc_2`, ... | `sensor.cf2_dhwc_1_temperature_actual_value` |
| Heating Circuits | `hc_1`, `hc_1_1`, ... | `sensor.cf2_hc_1_forward_flow_temp` |
| Solar | `sol_1`, `sol_2`, ... | `sensor.cf2_sol_1_collector_temp` |
| Circulation | `zir_1`, `zir_2`, ... | `sensor.cf2_zir_1_temperature_value` |
| Heat Meters | `hqm_1`, `hqm_2`, ... | `sensor.cf2_hqm_1_power_value` |
| Boiler Sequence | `b_1`, `b_2`, ... | `sensor.cf2_b_1_status` |
| Secondary Heat | `shs_1`, `shs_2`, ... | `sensor.cf2_shs_1_temperature` |

**Note:** 0-indexed equipment in the source data (BUF 0, Circ 0, etc.) is automatically converted to 1-based indexing in entity IDs for user-friendliness.

#### Why This Change?

1. **Language Independence**: Entity IDs are always derived from English data, ensuring they never change when switching languages
2. **Unique Entity IDs**: Each equipment instance has a unique entity ID, preventing Home Assistant from appending numeric suffixes
3. **Predictable Naming**: You can now reliably reference entities in automations knowing the exact format
4. **Display Names**: The UI still shows localized names (German/English) - only the entity_id is standardized

#### Migration

Update any automations, scripts, dashboards, or Lovelace cards that reference the old entity IDs. The new format includes the equipment prefix before the register name.

**Find affected entities:**
```yaml
# Check Developer Tools → States for entities matching your device prefix
# Old pattern: sensor.cf2_temperature_1_value
# New pattern: sensor.cf2_buf_1_temperature_1_value
```

See [CHANGELOG.md](CHANGELOG.md) for full details.

## 🔥 Features

- **Complete Modbus TCP/RTU integration** for KWB heating systems, including RTU-over-TCP gateways such as ser2net
- **Multi-version & multi-language support** - Automatic version detection and language selection
- **UI-based configuration** via Home Assistant Config Flow
- **Access Level System** - User Level (Benutzerebene) vs. Expert Level (Fachkraftebene) for different user groups; Expert Level unlocks additional read/write controls (number/select/switch)
- **Equipment-based configuration** - heating circuits, buffer storage, solar, etc.
- **All entity types** - sensors, switches, input fields and select menus
- **Computed sensors** - "Last Firewood Fire" tracking for Combifire/Multifire devices
- **Robust communication** with automatic reconnection
- **Comprehensive device support** for all common KWB models
- **ModbusInfo Converter** - Tool to convert KWB Excel files to JSON configuration

## 🏠 Supported KWB Devices

- **KWB Combifire** (all variants)
- **KWB Easyfire** (all variants including EF3)
- **KWB Multifire** (all variants)
- **KWB Pelletfire Plus** (all variants)
- **KWB CF1** & **CF1.5** & **CF2** (all variants with Combifire base)
- **KWB EasyAir Plus** (heat pump, v25.7.1+)
- Additional KWB devices via universal register configuration

**Note**: CF models (CF 1, CF 1.5, CF 2) inherit all Combifire registers plus model-specific registers.

## 📋 Requirements

- **Home Assistant** 2023.1.0 or higher
- **KWB heating system** with Modbus TCP/RTU interface
- **Network connection** to the heating system (TCP), an RTU-over-TCP gateway, or a USB/RS485 adapter (RTU)

## 🚀 Installation

### Via HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cgfm&repository=kwb-heating-integration&category=integration)

**Manual HACS Installation:**

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the menu (⋮) and select "Custom repositories"
4. Add `https://github.com/cgfm/kwb-heating-integration` as repository
5. Select "Integration" as category
6. Search for "KWB Heating" and install it
7. Restart Home Assistant

### Manual Installation

1. Download the latest version from [Releases](https://github.com/cgfm/kwb-heating-integration/releases)
2. Extract the archive to your `custom_components` directory
3. Restart Home Assistant

## ⚙️ Configuration

### 1. Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **"Add Integration"**
3. Search for **"KWB Heating"**
4. Follow the configuration wizard

### 2. Connection Parameters

- **Host/IP Address**: IP address of your KWB system
- **Port**: Modbus TCP port (default: 502)
- **Connection type**: Modbus TCP, RTU over TCP (for gateways such as ser2net), or serial Modbus RTU
- **Slave ID**: Modbus Slave ID (default: 1)
- **Device Type**: Select your KWB model
- **Access Level / Zugriffsebene**:
  - **User Level / Benutzerebene**: Basic read access and writable controls available at the user level on the KWB control panel
  - **Expert Level / Fachkraftebene**: Full access — unlocks all readable registers and additional writable controls (number/select/switch) that are reserved for service personnel on the KWB unit
  - The selected level must match (or be authorized by) the access level configured on the KWB heating system itself; the integration only exposes entities according to the chosen level.

### 3. Equipment Configuration

Configure the number of your equipment components:

- **Heating Circuits** (0-14) - Up to 14 heating circuits supported
- **Buffer Storage** (0-15) - Up to 15 buffer storage tanks
- **DHW Storage** (0-14) - Domestic hot water storage tanks
- **Secondary Heat Sources** (0-14) - Additional heat sources
- **Circulation** (0-15) - Hot water circulation pumps
- **Solar** (0-14) - Solar thermal systems
- **Boiler Sequence** (0-8) - Boiler sequence control
- **Heat Meters** (0-36) - Heat quantity meters

**Note**: Actual limits depend on your KWB model and firmware version. The integration automatically filters registers based on equipment count.

## 📊 Entities

### Sensors (Read-Only)
- **Temperatures** (boiler, heating circuits, buffer storage, etc.)
- **Status information** (operating mode, faults, etc.) - displayed in configured language
- **Performance data** (modulation level, burner starts, etc.)
- **Alarm status** with localized descriptions

### Computed Sensors

#### Last Firewood Fire / Letztes Stückholzfeuer
For devices that support firewood operation (Stückholz), a special computed sensor tracks when the last firewood fire was active:

| Language | Sensor Name | Entity ID |
|----------|-------------|-----------|
| German | `{Prefix} Letztes Stückholzfeuer` | `sensor.{prefix}_last_firewood_fire` |
| English | `{Prefix} Last Firewood Fire` | `sensor.{prefix}_last_firewood_fire` |

**Capability detection**: The sensor is created whenever the loaded register set
contains `CF2.kesselstatus_anzeige_sh`. Device/model names and a fixed Modbus
address are not used to decide availability.

**Features**:
- **Device class**: `timestamp` - displays relative time (e.g., "2 hours ago")
- **Persistent**: Timestamp survives Home Assistant restarts
- **Automatic detection**: Only created for devices with firewood support

**Attributes** (German/English):
| German | English | Description |
|--------|---------|-------------|
| `stueckholz_aktiv` | `firewood_currently_active` | Boolean - is firewood mode currently active |
| `betriebsmodus_rohwert` | `operating_mode_raw` | Raw operating mode value (1=Stückholz, 3=Stückholz PM Nachlauf) |
| `betriebsmodus` | `operating_mode` | Display name of current operating mode |

**Example usage in automations**:
```yaml
# Notify when no firewood fire for 24 hours (German entity)
automation:
  - alias: "Stückholz Erinnerung"
    trigger:
      - platform: template
        value_template: >
          {{ (now() - states('sensor.cf2_letztes_stueckholzfeuer') | as_datetime).total_seconds() > 86400 }}
    action:
      - service: notify.mobile_app
        data:
          message: "Seit 24 Stunden kein Stückholzfeuer mehr!"
```

### Control (Read-Write)
- **Target temperatures** for heating circuits
- **Operating modes** (automatic, manual, off) - labels in configured language
- **Time programs** enable/disable
- **Pumps** manual control

> **Note**: Read-Write entities are only available with appropriate access level

## 🔢 Raw Value Attribute

- Purpose: Exposes the original Modbus register value before any conversion or localization.
- Available on: sensors, selects, and switches (attribute name: `raw_value`).
- Display vs. raw:
  - Sensors with value tables: state shows a localized text; `raw_value` holds the numeric status code.
  - Numeric sensors with scaling: state shows the converted/scaled value; `raw_value` holds the unscaled register value.
- Switch extras: switches also expose `value_description` (text mapped from the current `raw_value`).

Examples:
- Jinja template: `{{ state_attr('sensor.<your_device_prefix>_kessel_status_stuckholz', 'raw_value') }}`
- Lovelace (e.g., floorplan-card): `entity.attributes.raw_value`
- Template sensor:
  ```yaml
  template:
    - sensor:
        - name: "Kesselstatus (roh)"
          state: "{{ state_attr('sensor.<your_device_prefix>_kessel_status_stuckholz', 'raw_value') }}"
  ```

Migration from legacy "rohwert" entities:
- Older setups used separate entities like `sensor.*_rohwert`. These are no longer created.
- Replace them by reading the `raw_value` attribute from the corresponding base entity.
- Example: `sensor.kwb_combifire_cf2_kessel_status_stuckholz_rohwert` → `state_attr('sensor.heizungsanlage_kessel_status_stuckholz', 'raw_value')`.

## 🌍 Language Support

The integration supports **automatic version detection** and multilingual display
data without duplicating the physical register configuration:

### Supported Languages & Versions
- **German (de)** - Complete support for v21.4.0, v22.7.1, v24.7.1, v25.4.0, v25.7.1 and v26.6.1
- **English (en)** - Complete support for v21.4.0, v22.7.1, v24.7.1, v25.4.0, v25.7.1 and v26.6.1, with safe fallback for documented source translation gaps

### Auto-Detection
1. **Version Detection**: Automatically detects KWB firmware version via Modbus register 8192
2. **Language Selection**: Three modes available during setup
   - **Automatic**: Uses Home Assistant language setting (recommended)
   - **German (de)**: Force German configuration
   - **English (en)**: Force English configuration

### Configuration File Structure

Each firmware has one language-independent technical configuration. The tree
under `custom_components/kwb_heating/config/versions/` is the only canonical
production source and the only version tree loaded at runtime:

```
config/versions/
├── v21.4.0/
│   ├── devices/
│   ├── equipment/
│   ├── modbus_registers.json
│   ├── value_tables.json
│   └── alarm_codes.json
├── v22.7.1/
│   └── (same unified structure)
├── v25.7.1/
│   └── (same unified structure)
└── v26.6.1/
    └── (same unified structure)
```

Register `name` and `index` are explicit `{ "de": ..., "en": ... }`
objects. Value-table labels and alarm descriptions use the same localized-value
shape. Addresses, parameters, entity IDs, types, limits, access metadata,
scaling, register lengths, and value-table references are structural values and
must never vary by language. Equipment selection uses the language-neutral
`equipment_group`, `equipment_instance`, and optional `equipment_subindex`
fields; localized `index` is presentation data.

Localized values resolve in this order: requested language, English, German,
then any non-empty available value. A missing English translation therefore
never removes a physical register or entity. Changing the Home Assistant
language changes presentation only—not addresses, register membership, entity
IDs, or unique IDs.

Changing the integration's language option reloads its config entry so names,
indexes, value-table labels, and alarm descriptions are rebuilt consistently.
When the option is `auto`, the Home Assistant language is resolved during setup
or reload. A later global Home Assistant language change does not currently emit
a simple integration-specific reload callback; reload this config entry (or
re-save its options) to apply that global-language change.

## 🔄 ModbusInfo Converter

The **modbusinfoConverter** tool converts KWB's official ModbusInfo Excel files
into initial JSON templates. Its `config/versions/` tree is a non-canonical
development artifact; it is neither a runtime dependency nor a production mirror.

### Key Features
- Multi-version support (v21.4.0, v22.7.1, v24.7.1, v25.4.0, v25.7.1, v26.6.1, etc.)
- Merged German/English processing into one multilingual firmware template
- Language-independent entity_id generation (derived from English data)
- Equipment index prefixes included in entity_ids
- Automatic device categorization (universal, device-specific, equipment)
- Combifire inheritance (CF models inherit from Combifire base)
- Consistent English filenames in the one canonical tree

### Available Scripts

| Script | Purpose |
|--------|---------|
| `convert_modbusinfo.py` | Convert Excel files to JSON configs |
| `import_generated_config.py` | Dry-run/finalize a version while preserving published IDs |
| `json_to_excel.py` | Generate Excel files from existing JSON configs |
| `add_entity_ids_from_json.py` | Update IDs in generated templates when Excel is unavailable |

### Quick Start
```bash
cd modbusinfoConverter
# Place ModbusInfo-{lang}-V{version}.xlsx files in modbusinfo/ directory
python3 convert_modbusinfo.py
# Review config/versions/conversion_review.json
python3 import_generated_config.py 25.7.1
# Resolve blocking review items, then explicitly finalize:
python3 import_generated_config.py 25.7.1 --write
```

### Generate Excel from JSON
If you need to recreate Excel files from existing JSON configs (useful when original Excel is unavailable):
```bash
cd modbusinfoConverter
python3 json_to_excel.py [version]
# Example: python3 json_to_excel.py 24.7.1
```

### Documentation
For detailed usage instructions, see [modbusinfoConverter/README.md](modbusinfoConverter/README.md)

### Use Cases
- **Add new KWB firmware versions**: Convert new ModbusInfo Excel files
- **Improve translations**: Convert matching German/English Excel files
- **Update existing configs**: Generate a template, review it, then use safe finalization
- **Recreate missing Excel files**: Generate Excel from JSON when source is unavailable
- **Development**: Test with modified register definitions

## 🔧 Advanced Configuration

### Custom Registers

You can add custom registers via JSON configuration files:

```json
{
  "starting_address": 1000,
  "name": "Custom Sensor", 
  "data_type": "04",
  "access": "R",
  "access_level": "UserLevel",
  "type": "s16",
  "unit": "°C"
}
```

### Value Tables

For enum values you can define custom value tables:

```json
{
  "operating_mode": {
    "0": "Off",
    "1": "Manual", 
    "2": "Automatic"
  }
}
```

## 🐛 Troubleshooting

### Connection Issues

1. **Check network connection**:
   ```bash
   ping <heating-system-ip>
   ```

2. **Test Modbus connection**:
   ```bash
   telnet <ip-address> 502
   ```

3. **Check logs**:
   - Enable debug logging for `custom_components.kwb_heating`

### Common Problems

- **"Connection refused"**: Modbus TCP not enabled or wrong port
- **"No response from slave"**: Wrong slave ID or device not reachable  
- **"Permission denied"**: Insufficient access level for write operations

### Enable Debug Logging

Add to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.kwb_heating: debug
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Create a pull request

### 🧪 Help with Testing

**We especially need help testing with different KWB models and configurations!**

Currently tested:
- ✅ **KWB CF2** with 2 heating circuits and 1 buffer storage

**Wanted for testing:**
- 🔍 Other KWB models (Easyfire, Multifire, Pelletfire+, Combifire, CF1, CF1.5)
- 🔍 Different equipment configurations (more heating circuits, multiple buffers, solar, etc.)
- 🔍 Various access level scenarios (UserLevel vs ExpertLevel)

**How to help:**
1. Install the integration on your system
2. Test with your specific KWB model and configuration
3. Report your results via [GitHub Issues](https://github.com/cgfm/kwb-heating-integration/issues)
4. Include: KWB model, equipment setup, any errors or unexpected behavior

### Development Environment

```bash
# Clone repository
git clone https://github.com/cgfm/kwb-heating-integration.git
cd kwb-heating-integration

# Install dependencies
pip install -r requirements-dev.txt

# Convert ModbusInfo Excel files (optional)
cd modbusinfoConverter
pip install openpyxl
python3 convert_modbusinfo.py
```

### Working with ModbusInfo Files

If you have access to KWB's official ModbusInfo Excel files:

1. Place Excel files in `modbusinfoConverter/modbusinfo/`
2. Run `python3 convert_modbusinfo.py`
3. Review `modbusinfoConverter/config/versions/conversion_review.json`
4. Run `python3 import_generated_config.py <version>` for a dry-run report
5. Resolve ambiguous names, unusual tables, changed parameters, translations, and firmware anomalies
6. Run the finalizer with `--write` only after review and validation succeed
7. Review the canonical diff under `custom_components/kwb_heating/config/versions/` and run tests

Generated IDs are based on English data and must remain language-independent.
Public IDs must not normally contain German/internal KWB parameter fragments.
Already released IDs and their derived Home Assistant unique IDs are compatibility
data and must not be renamed merely because a fresh template suggests another ID.

See [modbusinfoConverter/README.md](modbusinfoConverter/README.md) for details.

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- **KWB** for comprehensive Modbus documentation (ModbusInfo Excel files)
- **Home Assistant Community** for continuous support
- All **beta testers** for valuable feedback
- **Contributors** who helped with multi-language support and version management

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/cgfm/kwb-heating-integration/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cgfm/kwb-heating-integration/discussions)
- **Home Assistant Community**: [HA Community Forum](https://community.home-assistant.io/)

---

**Made with ❤️ for the Home Assistant Community**
