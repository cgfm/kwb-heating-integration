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
CONF_CONNECTION_TYPE = "connection_type"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_SERIAL_PORT = "serial_port"
CONF_BAUDRATE = "baudrate"
CONF_PARITY = "parity"
CONF_STOPBITS = "stopbits"
CONF_BYTESIZE = "bytesize"
CONF_SLAVE_ID = "slave_id"
CONF_ACCESS_LEVEL = "access_level"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_DEVICE_TYPE = "device_type"
CONF_DEVICE_NAME = "device_name"
CONF_LANGUAGE = "language"

# Connection types
CONNECTION_TYPE_TCP = "tcp"
CONNECTION_TYPE_SERIAL = "serial"

# System Register Configuration (with slider in Config Flow)
CONF_HEATING_CIRCUITS = "heating_circuits"           # Heating circuits
CONF_BUFFER_STORAGE = "buffer_storage"               # Buffer storage
CONF_DHW_STORAGE = "dhw_storage"                     # DHW storage
CONF_SECONDARY_HEAT_SOURCES = "secondary_heat_sources" # Secondary heat sources
CONF_CIRCULATION = "circulation"                     # Circulation
CONF_SOLAR = "solar"                                 # Solar
CONF_BOILER_SEQUENCE = "boiler_sequence"             # Boiler sequence control
CONF_HEAT_METERS = "heat_meters"                     # Heat meters
CONF_TRANSFER_STATIONS = "transfer_stations"         # Transfer stations

# System Register Mapping (JSON key -> Config constant)
SYSTEM_REGISTER_MAPPING = {
    "Heizkreise": CONF_HEATING_CIRCUITS,
    "Pufferspeicher": CONF_BUFFER_STORAGE,
    "Brauchwasserspeicher": CONF_DHW_STORAGE,
    "Zweitwärmequellen": CONF_SECONDARY_HEAT_SOURCES,
    "Zirkulation": CONF_CIRCULATION,
    "Solar": CONF_SOLAR,
    "Kesselfolgeschaltung": CONF_BOILER_SEQUENCE,
    "Wärmemengenzähler": CONF_HEAT_METERS,
    "Übergabestation": CONF_TRANSFER_STATIONS,
}

# Access Levels
ACCESS_LEVELS = {
    "UserLevel": "Standard functions for end users",
    "ExpertLevel": "Full access for experts/service"
}

# Default values
DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 1
DEFAULT_UPDATE_INTERVAL = 30
DEFAULT_ACCESS_LEVEL = "UserLevel"
DEFAULT_BAUDRATE = 19200
DEFAULT_PARITY = "N"
DEFAULT_STOPBITS = 1
DEFAULT_BYTESIZE = 8

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

# Icon mapping for different entity types based on register names/types
ENTITY_ICONS = {
    # Order matters: more specific keywords should come first.

    # Temperature
    "forward_flow": "mdi:thermometer-chevron-up",
    "return_flow": "mdi:thermometer-chevron-down",
    "outdoor_temp": "mdi:thermometer",
    "outside_temp": "mdi:thermometer",
    "room_temp": "mdi:home-thermometer",
    "boiler_temp": "mdi:thermometer-lines",
    "buffer_temp": "mdi:storage-tank-thermometer",
    "dhw_temp": "mdi:water-thermometer",
    "temp_setpoint": "mdi:thermometer-auto",
    "temperature": "mdi:thermometer",
    "temp": "mdi:thermometer",

    # Heating/Boiler
    "heating_circuit": "mdi:heating-coil",
    "hc": "mdi:heating-coil",
    "boiler": "mdi:fire",
    "burner": "mdi:fire",
    "heating": "mdi:radiator",

    # Pumps and circulation
    "pump": "mdi:pump",
    "circulation": "mdi:rotate-3d-variant",
    "circ": "mdi:rotate-3d-variant",

    # Water/Storage
    "buffer": "mdi:storage-tank",
    "buf": "mdi:storage-tank",
    "dhw": "mdi:water-thermometer",
    "storage": "mdi:storage-tank",
    
    # Solar
    "collector": "mdi:solar-panel-large",
    "solar": "mdi:solar-power-variant",
    "sol": "mdi:solar-power-variant",
    
    # System/Status
    "fault": "mdi:alert-circle",
    "alarm": "mdi:alert",
    "status": "mdi:information-outline",
    "mode": "mdi:play-circle",
    "request": "mdi:gesture-tap",
    "release": "mdi:check-circle",
    
    # Power/Energy
    "power": "mdi:lightning-bolt",
    "energy": "mdi:flash",
    "current": "mdi:current-ac",

    # Time/Program
    "time": "mdi:clock",
    "timer": "mdi:timer",
    "program": "mdi:cog",
    
    # Default fallbacks
    "default_sensor": "mdi:gauge",
    "default_switch": "mdi:toggle-switch",
    "default_number": "mdi:numeric",
    "default_select": "mdi:format-list-bulleted",
}

# Icon mapping for device types
DEVICE_TYPE_ICONS = {
    "KWB Easyfire": "mdi:water-boiler",
    "KWB Multifire": "mdi:water-boiler", 
    "KWB Pelletfire+": "mdi:water-boiler",
    "KWB Combifire": "mdi:water-boiler",
    "KWB CF 2": "mdi:water-boiler",
    "KWB CF 1": "mdi:water-boiler",
    "KWB CF 1.5": "mdi:water-boiler",
    "default": "mdi:water-boiler",
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
