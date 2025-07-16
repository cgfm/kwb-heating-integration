"""Constants for the KWB Heating integration."""
from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "kwb_heating"

# Platforms
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
]

# Configuration
CONF_HOST = "host"
CONF_PORT = "port"
CONF_SLAVE_ID = "slave_id"
CONF_ACCESS_LEVEL = "access_level"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_DEVICE_TYPE = "device_type"

# System Register Configuration (mit Slider im Config Flow)
CONF_HEATING_CIRCUITS = "heating_circuits"           # Heizkreise
CONF_BUFFER_STORAGE = "buffer_storage"               # Pufferspeicher  
CONF_DHW_STORAGE = "dhw_storage"                     # Brauchwasserspeicher
CONF_SECONDARY_HEAT_SOURCES = "secondary_heat_sources" # Zweitwärmequellen
CONF_CIRCULATION = "circulation"                     # Zirkulation
CONF_SOLAR = "solar"                                 # Solar
CONF_BOILER_SEQUENCE = "boiler_sequence"             # Kesselfolgeschaltung  
CONF_HEAT_METERS = "heat_meters"                     # Wärmemengenzähler

# System Register Mapping (JSON Schlüssel -> Config Konstante)
SYSTEM_REGISTER_MAPPING = {
    "Heizkreise": CONF_HEATING_CIRCUITS,
    "Pufferspeicher": CONF_BUFFER_STORAGE, 
    "Brauchwasserspeicher": CONF_DHW_STORAGE,
    "Zweitwärmequellen": CONF_SECONDARY_HEAT_SOURCES,
    "Zirkulation": CONF_CIRCULATION,
    "Solar": CONF_SOLAR,
    "Kesselfolgeschaltung": CONF_BOILER_SEQUENCE,
    "Wärmemengenzähler": CONF_HEAT_METERS,
}

# Access Levels
ACCESS_LEVELS = {
    "UserLevel": "Standardfunktionen für Endbenutzer",
    "ExpertLevel": "Vollzugriff für Experten/Service"
}

# Default values
DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 1
DEFAULT_UPDATE_INTERVAL = 30
DEFAULT_ACCESS_LEVEL = "UserLevel"

# Modbus configuration
MODBUS_FUNCTION_CODES = {
    "01": "read_coils",
    "02": "read_discrete_inputs", 
    "03": "read_holding_registers",
    "04": "read_input_registers",
    "06": "write_single_register",
    "15": "write_multiple_coils",
    "16": "write_multiple_registers"
}

# Data types
DATA_TYPES = {
    "u16": "unsigned 16-bit",
    "s16": "signed 16-bit",
    "u32": "unsigned 32-bit",
    "s32": "signed 32-bit",
    "f32": "32-bit float",
    "str": "string"
}

# Error codes
ERROR_CONNECTION = "connection_error"
ERROR_INVALID_DATA = "invalid_data"
ERROR_TIMEOUT = "timeout_error"
ERROR_CONFIG = "configuration_error"

# Entity categories for organization
ENTITY_CATEGORIES = {
    "system": "System Information",
    "heating": "Heating Control",
    "temperature": "Temperature Sensors",
    "pump": "Pump Control",
    "alarm": "Alarm System",
    "maintenance": "Maintenance"
}
