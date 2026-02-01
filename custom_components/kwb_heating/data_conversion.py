"""Data conversion utilities for KWB Heating integration."""
from __future__ import annotations

import logging
import re
from typing import Any

_LOGGER = logging.getLogger(__name__)


class KWBDataConverter:
    """Handle data conversion between Modbus values and Home Assistant values."""
    
    def __init__(self, value_tables: dict[str, dict[str, str]]):
        """Initialize the data converter with value tables."""
        self.value_tables = value_tables
    
    def convert_from_modbus(self, raw_value: int, register_config: dict[str, Any]) -> Any:
        """Convert raw Modbus value to Home Assistant value."""
        # First, handle signed integers if the register type is s16 or s32
        data_type = register_config.get("type", register_config.get("unit", "u16"))
        converted_value = self._convert_signed_value(raw_value, data_type)

        unit_value_table = register_config.get("unit_value_table", "")

        if not unit_value_table:
            # No conversion needed - return converted value (might be negative now)
            return converted_value

        # Check if it's a value table reference
        if unit_value_table in self.value_tables:
            return self._convert_from_value_table(converted_value, unit_value_table)

        # Check if it's a scaling factor (like "1/10°C", "1/100bar", etc.)
        return self._convert_from_scaling_factor(converted_value, unit_value_table)
    
    def convert_to_modbus(self, ha_value: Any, register_config: dict[str, Any]) -> int:
        """Convert Home Assistant value to raw Modbus value."""
        unit_value_table = register_config.get("unit_value_table", "")

        # First convert the value (apply scaling or value table)
        if not unit_value_table:
            # No conversion needed - use value as is
            modbus_value = int(ha_value)
        elif unit_value_table in self.value_tables:
            # Convert using value table
            modbus_value = self._convert_to_value_table(ha_value, unit_value_table)
        else:
            # Convert using scaling factor
            modbus_value = self._convert_to_scaling_factor(ha_value, unit_value_table)

        # Then handle signed to unsigned conversion for s16/s32 types
        data_type = register_config.get("type", register_config.get("unit", "u16"))
        return self._convert_to_unsigned_value(modbus_value, data_type)
    
    def convert_to_ha_value(self, register: dict, raw_value: int) -> Any:
        """Convert raw Modbus value to Home Assistant value (new interface)."""
        return self.convert_from_modbus(raw_value, register)
    
    def convert_to_modbus_value(self, register: dict, ha_value: Any) -> int:
        """Convert Home Assistant value to Modbus value (new interface)."""
        return self.convert_to_modbus(ha_value, register)

    def _convert_signed_value(self, raw_value: int, data_type: str) -> int:
        """Convert unsigned Modbus value to signed value if needed.

        Modbus returns values as unsigned integers (0-65535 for 16-bit, 0-4294967295 for 32-bit),
        but some registers use signed integers. This method converts them properly.
        """
        if data_type == "s16":
            # Convert 16-bit unsigned to signed
            # If value > 32767, it represents a negative number in two's complement
            if raw_value > 32767:
                return raw_value - 65536
            return raw_value
        elif data_type == "s32":
            # Convert 32-bit unsigned to signed
            # If value > 2147483647, it represents a negative number in two's complement
            if raw_value > 2147483647:
                return raw_value - 4294967296
            return raw_value
        else:
            # For u16, u32, and unknown types, return as is
            return raw_value

    def _convert_to_unsigned_value(self, signed_value: int, data_type: str) -> int:
        """Convert signed value to unsigned Modbus value if needed.

        When writing to Modbus, we need to convert signed integers back to
        unsigned format that Modbus expects.
        """
        if data_type == "s16":
            # Convert 16-bit signed to unsigned
            if signed_value < 0:
                return signed_value + 65536
            return signed_value
        elif data_type == "s32":
            # Convert 32-bit signed to unsigned
            if signed_value < 0:
                return signed_value + 4294967296
            return signed_value
        else:
            # For u16, u32, and unknown types, return as is
            return signed_value

    def _convert_from_value_table(self, raw_value: int, table_name: str) -> str:
        """Convert using value table."""
        value_table = self.value_tables.get(table_name, {})
        return value_table.get(str(raw_value), f"Unknown ({raw_value})")
    
    def _convert_to_value_table(self, ha_value: str, table_name: str) -> int:
        """Convert back to raw value using value table."""
        value_table = self.value_tables.get(table_name, {})
        
        # Find the key for the given value
        for key, value in value_table.items():
            if value == ha_value:
                return int(key)
        
        # If not found, try to extract number from unknown format
        if "Unknown (" in ha_value and ")" in ha_value:
            try:
                return int(ha_value.split("(")[1].split(")")[0])
            except (ValueError, IndexError):
                pass
        
        return 0  # Default fallback
    
    def _convert_from_scaling_factor(self, converted_value: int | float, unit_value_table: str) -> float:
        """Convert using scaling factor like '1/10°C'.

        Note: converted_value may already be a signed integer (negative for s16/s32 types).
        """
        # Parse scaling factor pattern like "1/10°C", "1/100bar", etc.
        match = re.match(r"1/(\d+)", unit_value_table)
        if match:
            divisor = int(match.group(1))
            return round(converted_value / divisor, 3)

        # If no scaling factor found, return value as float
        return float(converted_value)
    
    def _convert_to_scaling_factor(self, ha_value: float, unit_value_table: str) -> int:
        """Convert back to raw value using scaling factor."""
        # Parse scaling factor pattern
        match = re.match(r"1/(\d+)", unit_value_table)
        if match:
            multiplier = int(match.group(1))
            return int(round(ha_value * multiplier))
        
        # If no scaling factor found, return as integer
        return int(ha_value)
    
    def get_unit_of_measurement(self, register_config: dict[str, Any]) -> str | None:
        """Extract unit of measurement from unit_value_table."""
        unit_value_table = register_config.get("unit_value_table", "")
        
        if not unit_value_table:
            return None
        
        # If it's a value table reference, no unit
        if unit_value_table in self.value_tables:
            return None
        
        # Common units to Home Assistant standards
        unit_mapping = {
            "°C": "°C",
            "°F": "°F", 
            "%": "%",
            "bar": "bar",
            "Pa": "Pa",
            "kW": "kW",
            "W": "W",
            "l": "L",
            "m³": "m³",
            "kg": "kg",
            "h": "h",
            "min": "min",
            "s": "s",
            "V": "V",
            "A": "A",
            "Hz": "Hz",
            "rpm": "rpm",
            "Upm": "RPM"
        }
        
        # Extract unit from scaling factor like "1/10°C" -> "°C"
        match = re.match(r"1/\d+(.+)", unit_value_table)
        if match:
            unit = match.group(1)
            return unit_mapping.get(unit, unit)
        
        # Check if the whole string is a known unit (e.g., "kg", "min", etc.)
        if unit_value_table in unit_mapping:
            return unit_mapping[unit_value_table]
        
        return None
    
    def get_device_class(self, register: dict) -> str | None:
        """Get device class for Home Assistant based on unit.

        Args:
            register: Register configuration dictionary

        Returns:
            Device class string or None if not applicable
        """
        unit = self.get_unit_of_measurement(register)

        if not unit:
            return None

        # Map units to device classes
        device_class_mapping = {
            "°C": "temperature",
            "°F": "temperature",
            "%": None,  # Could be humidity, battery, etc. - let HA decide
            "bar": "pressure",
            "Pa": "pressure",
            "kW": "power",
            "W": "power",
            "V": "voltage",
            "A": "current",
            "Hz": "frequency",
        }

        return device_class_mapping.get(unit)
    
    def is_read_write_register(self, register_config: dict[str, Any], access_level: str) -> bool:
        """Check if register is read-write for the given access level."""
        level_field = f"{access_level.lower()}_level"  # "user_level" or "expert_level"
        access_type = register_config.get(level_field, "")
        
        return access_type in ["read_write", "write", "rw"]
    
    def is_readable_register(self, register_config: dict[str, Any], access_level: str) -> bool:
        """Check if register is readable for the given access level."""
        level_field = f"{access_level.lower()}_level"  # "user_level" or "expert_level"
        access_type = register_config.get(level_field, "")
        
        return access_type in ["read", "read_write", "rw"]
    
    def is_numeric(self, register: dict) -> bool:
        """Check if register contains numeric data."""
        unit_value_table = register.get("unit_value_table", "")
        
        # If it has a value table (enum mapping), it's not numeric
        if self.has_value_table(register):
            return False
        
        # If it has scaling (like "1/10°C"), it's numeric
        if re.match(r"1/\d+", unit_value_table):
            return True
        
        # Common unit suffixes that indicate numeric values
        unit_suffixes = [
            "°C", "°F", "K", "bar", "mbar", "Pa", "kPa", "MPa",
            "W", "kW", "MW", "J", "kJ", "MJ", "Wh", "kWh", "MWh",
            "V", "A", "mA", "Hz", "Ohm", "kg", "g", "t", "l", "ml",
            "m", "cm", "mm", "km", "m²", "m³", "s", "min", "h", "%",
            "rpm", "1/min", "/min"
        ]
        
        # Check if it's a unit suffix (indicates numeric)
        for suffix in unit_suffixes:
            if unit_value_table == suffix or unit_value_table.endswith(suffix):
                return True
        
        # If no unit_value_table, it's numeric
        return not unit_value_table
    
    def has_value_table(self, register: dict) -> bool:
        """Check if register uses a value table."""
        unit_value_table = register.get("unit_value_table", "")
        
        # If empty, no value table
        if not unit_value_table:
            return False
        
        # First check if it's actually in the value tables
        if unit_value_table in self.value_tables:
            return True
        
        # Common unit suffixes that are NOT value tables
        unit_suffixes = [
            "°C", "°F", "K", "bar", "mbar", "Pa", "kPa", "MPa",
            "W", "kW", "MW", "J", "kJ", "MJ", "Wh", "kWh", "MWh",
            "V", "A", "mA", "Hz", "Ohm", "kg", "g", "t", "l", "ml",
            "m", "cm", "mm", "km", "m²", "m³", "s", "min", "h", "%",
            "rpm", "1/min", "/min", "1/10°C", "1/100°C", "Upm"
        ]
        
        # If it matches a unit suffix, it's not a value table
        for suffix in unit_suffixes:
            if unit_value_table == suffix or unit_value_table.endswith(suffix):
                return False
        
        # If it's not a known unit suffix and not in value_tables, 
        # it might be a missing value table - assume it's a value table if it ends with "_t"
        if unit_value_table.endswith("_t"):
            return True
        
        return False

    def is_boolean_value_table(self, register: dict) -> bool:
        """Check if value table represents boolean values (on/off, enabled/disabled).

        Args:
            register: Register configuration dictionary

        Returns:
            True if the value table has exactly 2 values matching boolean patterns
        """
        unit_value_table = register.get("unit_value_table", "")
        if not unit_value_table or unit_value_table not in self.value_tables:
            return False

        value_table = self.value_tables[unit_value_table]
        if not isinstance(value_table, dict):
            return False

        # Check if it's a simple boolean mapping (0/1, true/false, etc.)
        values = list(value_table.keys())
        if len(values) == 2:
            # Common boolean patterns
            boolean_patterns = [
                ["0", "1"],
                ["false", "true"],
                ["off", "on"],
                ["disabled", "enabled"],
                ["aus", "ein"],  # German
            ]

            values_lower = [str(v).lower() for v in sorted(values)]
            return any(sorted(pattern) == values_lower for pattern in boolean_patterns)

        return False

    def get_display_value(self, register: dict, raw_value: int) -> str | None:
        """Get display value from value table if available."""
        unit_value_table = register.get("unit_value_table", "")
        
        if unit_value_table in self.value_tables:
            return self._convert_from_value_table(raw_value, unit_value_table)
        
        return None
    
    def get_min_value(self, register: dict) -> float:
        """Get minimum value for numeric register."""
        data_type = register.get("type", register.get("unit", "u16"))
        
        if data_type == "s16":
            return -32768.0
        elif data_type in ["u16", "u32", "s32"]:
            return 0.0
        else:
            return 0.0
    
    def get_max_value(self, register: dict) -> float:
        """Get maximum value for numeric register."""
        data_type = register.get("type", register.get("unit", "u16"))
        
        if data_type == "u16":
            return 65535.0
        elif data_type == "s16":
            return 32767.0
        elif data_type in ["u32", "s32"]:
            return 4294967295.0
        else:
            return 1000000.0
    
    def get_step_value(self, register: dict) -> float:
        """Get step value for numeric register based on scaling."""
        unit_value_table = register.get("unit_value_table", "")
        
        # Check for scaling factor
        match = re.match(r"1/(\d+)", unit_value_table)
        if match:
            scale_factor = int(match.group(1))
            return 1.0 / scale_factor
        
        return 1.0
    
    def get_unit(self, register: dict) -> str | None:
        """Get unit for Home Assistant (alias for get_unit_of_measurement)."""
        return self.get_unit_of_measurement(register)
    
    def get_value_table_options(self, register: dict) -> dict[str, str]:
        """Get value table options for register."""
        unit_value_table = register.get("unit_value_table", "")
        
        if unit_value_table in self.value_tables:
            return self.value_tables[unit_value_table]
        
        return {}
