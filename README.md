# KWB Heating Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/cgfm/kwb-heating-integration)](https://github.com/cgfm/kwb-heating-integration/releases)
[![GitHub](https://img.shields.io/github/license/cgfm/kwb-heating-integration)](LICENSE)

A comprehensive Home Assistant Custom Component for **KWB heating systems** with Modbus TCP/RTU support.

> **⚠️ Testing Status**: This integration has been tested primarily with **KWB CF2**, **2 heating circuits**, and **1 buffer storage**. Testing with other KWB models and configurations is very welcome! Please help expand compatibility by testing with your setup and reporting results via [GitHub Issues](https://github.com/cgfm/kwb-heating-integration/issues).

> **🇩🇪 Language**: Currently all created entitys and states are german only. If anyone could provide me with a english version of the modbus config a multilanguage support could become an option. 

## 🔥 Features

- **Complete Modbus TCP/RTU integration** for KWB heating systems
- **UI-based configuration** via Home Assistant Config Flow
- **Access Level System** - UserLevel vs. ExpertLevel for different user groups
- **Equipment-based configuration** - heating circuits, buffer storage, solar, etc.
- **All entity types** - sensors, switches, input fields and select menus
- **Robust communication** with automatic reconnection
- **Comprehensive device support** for all common KWB models

## 🏠 Supported KWB Devices

- **KWB Combifire** (all variants)
- **KWB Easyfire** (all variants) 
- **KWB Multifire** (all variants)
- **KWB Pelletfire Plus** (all variants)
- **KWB CF1** & **CF1.5** & **CF2** (all variants)
- Additional KWB devices via universal register configuration

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

- **Heating Circuits** (0-4)
- **Buffer Storage** (0-2) 
- **DHW Storage** (0-2)
- **Secondary Heat Sources** (0-2)
- **Circulation** (0-1)
- **Solar** (0-1)
- **Boiler Sequence** (0-1)
- **Heat Meters** (0-4)

## 📊 Entities

### Sensors (Read-Only)
- **Temperatures** (boiler, heating circuits, buffer storage, etc.)
- **Status information** (operating mode, faults, etc.) - displayed in German
- **Performance data** (modulation level, burner starts, etc.)
- **Alarm status** with German descriptions

### Control (Read-Write)
- **Target temperatures** for heating circuits
- **Operating modes** (automatic, manual, off) - labels in German
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

Currently supported languages:
- **German (de)** - Complete translations for all UI elements and alarm codes
- **English (en)** - UI translations available, alarm code translations in development

**Important Note**: All status messages, entity names, and equipment designations from the KWB system are displayed in **German**, as they come directly from the KWB heating system. This includes:
- Equipment names (Heizkreis, Pufferspeicher, etc.)
- Status values (Ein/Aus, Automatik/Handbetrieb, etc.)
- Alarm descriptions and error messages
- Operating mode descriptions

The integration automatically detects your Home Assistant language setting for the user interface. To contribute translations for additional languages, please see our [translation guidelines](https://github.com/cgfm/kwb-heating-integration/discussions).

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

# Run tests
pytest tests/
```

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- **KWB** for comprehensive Modbus documentation
- **Home Assistant Community** for continuous support
- All **beta testers** for valuable feedback

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/cgfm/kwb-heating-integration/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cgfm/kwb-heating-integration/discussions)
- **Home Assistant Community**: [HA Community Forum](https://community.home-assistant.io/)

---

**Made with ❤️ for the Home Assistant Community**
