"""Icon utilities for KWB Heating integration."""
from __future__ import annotations

import re
from typing import Optional

from .const import ENTITY_ICONS, DEVICE_TYPE_ICONS


def get_entity_icon(register: dict, entity_type: str = "sensor") -> str:
    """
    Determine the appropriate icon for an entity based on the register data.
    This logic is language-independent.
    
    Args:
        register: The register definition dictionary.
        entity_type: The type of the entity (sensor, switch, number, select).
        
    Returns:
        An icon string in the format "mdi:icon-name".
    """
    # 1. If an icon is explicitly defined in the register config, it takes highest precedence.
    if "icon" in register and register["icon"]:
        return register["icon"]
    
    # 2. Use the stable, language-independent 'entity_id' for keyword matching.
    entity_id_str = register.get("entity_id", "")
    
    # Check for keywords from the ENTITY_ICONS dictionary within the entity_id string.
    # The dictionary in const.py is ordered from most to least specific to ensure the best match.
    for keyword, icon in ENTITY_ICONS.items():
        if keyword in entity_id_str:
            return icon
            
    # 3. If no keyword match is found, fall back to a default icon based on the entity type.
    fallback_icons = {
        "sensor": ENTITY_ICONS["default_sensor"],
        "switch": ENTITY_ICONS["default_switch"], 
        "number": ENTITY_ICONS["default_number"],
        "select": ENTITY_ICONS["default_select"],
    }
    
    return fallback_icons.get(entity_type, ENTITY_ICONS["default_sensor"])


def get_device_icon(device_type: str) -> str:
    """
    Determine the icon for a device type.
    
    Args:
        device_type: KWB device type (e.g., "KWB CF2", "KWB Easyfire")
        
    Returns:
        Icon string in the format "mdi:icon-name"
    """
    return DEVICE_TYPE_ICONS.get(device_type, DEVICE_TYPE_ICONS["default"])


def get_category_icon(category: str) -> str:
    """
    Determine the icon for an entity category.
    
    Args:
        category: Category like "heating", "temperature", "pump" etc.
        
    Returns:
        Icon string in the format "mdi:icon-name"
    """
    category_icons = {
        "heating": "mdi:radiator",
        "temperature": "mdi:thermometer",
        "pump": "mdi:pump",
        "storage": "mdi:storage-tank",
        "solar": "mdi:solar-power-variant",
        "system": "mdi:cog",
        "alarm": "mdi:alert-circle",
        "energy": "mdi:lightning-bolt",
    }
    
    return category_icons.get(category, "mdi:gauge")


def extract_equipment_info(register_name: str) -> tuple[Optional[str], Optional[int]]:
    """
    Extract equipment type and number from register names.
    
    Args:
        register_name: Register name like "HK 1 Pumpe", "BWS 2 Temperatur"
        
    Returns:
        Tuple of (equipment_type, equipment_number) or (None, None)
    """
    # Patterns for different equipment types
    patterns = [
        (r"HK\s*(\d+)", "heating_circuit"),
        (r"Heizkreis\s*(\d+)", "heating_circuit"),
        (r"BWS\s*(\d+)", "dhw_storage"),
        (r"Brauchwasser\s*(\d+)", "dhw_storage"),
        (r"PS\s*(\d+)", "buffer_storage"),
        (r"Puffer\s*(\d+)", "buffer_storage"),
        (r"Solar\s*(\d+)", "solar"),
        (r"WMZ\s*(\d+)", "heat_meter"),
        (r"Zirk\s*(\d+)", "circulation"),
    ]
    
    for pattern, equipment_type in patterns:
        match = re.search(pattern, register_name, re.IGNORECASE)
        if match:
            return equipment_type, int(match.group(1))
    
    return None, None
