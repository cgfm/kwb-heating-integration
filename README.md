# KWB Heating Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/cgfm/kwb-heating-integration)](https://github.com/cgfm/kwb-heating-integration/releases)
[![GitHub](https://img.shields.io/github/license/cgfm/kwb-heating-integration)](LICENSE)

A comprehensive Home Assistant Custom Component for **KWB heating systems** with Modbus TCP/RTU support.

> **⚠️ Testing Status**: This integration has been tested primarily with **KWB CF2**, **2 heating circuits**, and **1 buffer storage**. Testing with other KWB models and configurations is very welcome! Please help expand compatibility by testing with your setup and reporting results via [GitHub Issues](https://github.com/cgfm/kwb-heating-integration/issues).

## ⚠️ Breaking Changes (v0.4.0)

**If you are upgrading from a previous version, please read this section carefully.**

### Entity ID Changes for Equipment

Equipment index prefixes have been standardized to German across all language configurations. This ensures entity IDs remain stable regardless of language selection, but requires migration for existing users.

| Equipment Type | Old Prefix (EN) | New Prefix (All) |
|----------------|-----------------|------------------|
| Heating Circuits | `HC` | `HK` |
| Buffer Storage | `BUF` | `PUF` |
| DHW Storage | `DHWC` | `BWS` |
| Secondary Heat | `SHS` | `ZWQ` |
| Circulation | `CIR` | `ZIR` |
| Boiler Sequence | `BS` | `KFS` |
| Heat Meters | `HM` | `WMZ` |

**Example change**:
- Old: `sensor.easyfire_heating_circuit_1_1_forward_flow_temp`
- New: `sensor.easyfire_heizkreis_1_1_forward_flow_temp`

**Why German?** KWB is an Austrian company and their internal Modbus register definitions use German naming. Using German prefixes ensures entity IDs are consistent and don't change when switching languages. Display names in the UI are still localized.

**Migration**: Update any automations, scripts, dashboards, or Lovelace cards that reference the old entity IDs.

See [CHANGELOG.md](CHANGELOG.md) for full details.

## 🔥 Features

- **Complete Modbus TCP/RTU integration** for KWB heating systems
- **Multi-version & multi-language support** - Automatic version detection and language selection
- **UI-based configuration** via Home Assistant Config Flow
- **Access Level System** - UserLevel vs. ExpertLevel for different user groups
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
- **Network connection** to the heating system (TCP) or USB/RS485 adapter (RTU)

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
- **Slave ID**: Modbus Slave ID (default: 1)
- **Device Type**: Select your KWB model
- **Access Level**: 
  - **UserLevel**: Basic functions for end users
  - **ExpertLevel**: Full access for service personnel

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
| German | `{Prefix} Letztes Stückholzfeuer` | `sensor.{prefix}_letztes_stueckholzfeuer` |
| English | `{Prefix} Last Firewood Fire` | `sensor.{prefix}_last_firewood_fire` |

**Supported devices**: KWB CF 1, KWB CF 1.5, KWB CF 2, KWB Combifire, KWB Multifire

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

The integration supports **automatic version detection** and **multi-language configurations**:

### Supported Languages & Versions
- **German (de)** - Complete support for v21.4.0, v22.7.1, v24.7.1 and v25.7.1
- **English (en)** - Complete support for v21.4.0, v22.7.1, v24.7.1 and v25.7.1

### Auto-Detection
1. **Version Detection**: Automatically detects KWB firmware version via Modbus register 8192
2. **Language Selection**: Three modes available during setup
   - **Automatic**: Uses Home Assistant language setting (recommended)
   - **German (de)**: Force German configuration
   - **English (en)**: Force English configuration

### Configuration File Structure
The integration uses version and language-specific configuration files:
```
config/versions/
├── v21.4.0/
│   ├── de/  # German version 21.4.0
│   └── en/  # English version 21.4.0
├── v22.7.1/
│   ├── de/  # German version 22.7.1
│   └── en/  # English version 22.7.1
├── v24.7.1/
│   ├── de/  # German version 24.7.1
│   └── en/  # English version 24.7.1
└── v25.7.1/
    ├── de/  # German version 25.7.1
    └── en/  # English version 25.7.1
```

**Note**: Register names, equipment labels, and status values within the configuration files are in their respective language (German or English), as provided by KWB's ModbusInfo documentation.

## 🔄 ModbusInfo Converter

The **modbusinfoConverter** tool converts KWB's official ModbusInfo Excel files into JSON configuration format.

### Key Features
- Multi-version support (v22.7.1, v25.7.1, etc.)
- Multi-language processing (German & English Excel files)
- Automatic device categorization (universal, device-specific, equipment)
- Combifire inheritance (CF models inherit from Combifire base)
- Consistent English filenames for cross-language compatibility

### Quick Start
```bash
cd modbusinfoConverter
# Place ModbusInfo-{lang}-V{version}.xlsx files in modbusinfo/ directory
python3 convert_modbusinfo.py
# Generated files appear in config/versions/
```

### Documentation
For detailed usage instructions, see [modbusinfoConverter/README.md](modbusinfoConverter/README.md)

### Use Cases
- **Add new KWB firmware versions**: Convert new ModbusInfo Excel files
- **Add language support**: Convert English/other language Excel files
- **Update existing configs**: Re-generate from updated Excel files
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
3. Generated JSON configs appear in `modbusinfoConverter/config/versions/`
4. Copy to integration: `cp -r config/versions/ custom_components/kwb_heating/config/`

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
