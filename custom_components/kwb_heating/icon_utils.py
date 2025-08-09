"""Icon utilities for KWB Heating integration."""
from __future__ import annotations

import re
from typing import Optional

from .const import ENTITY_ICONS, DEVICE_TYPE_ICONS


def get_entity_icon(register_name: str, entity_type: str = "sensor") -> str:
    """
    Bestimme das passende Icon für eine Entity basierend auf dem Register-Namen.
    
    Args:
        register_name: Name des Registers (z.B. "Kesseltemperatur", "Heizkreis 1 Pumpe")
        entity_type: Typ der Entity (sensor, switch, number, select)
        
    Returns:
        Icon string im Format "mdi:icon-name"
    """
    name_lower = register_name.lower()
    
    # Prüfe spezifische Begriffe im Namen
    for keyword, icon in ENTITY_ICONS.items():
        if keyword in name_lower:
            return icon
    
    # Fallback basierend auf Entity-Typ
    fallback_icons = {
        "sensor": ENTITY_ICONS["default_sensor"],
        "switch": ENTITY_ICONS["default_switch"], 
        "number": ENTITY_ICONS["default_number"],
        "select": ENTITY_ICONS["default_select"],
    }
    
    return fallback_icons.get(entity_type, ENTITY_ICONS["default_sensor"])


def get_device_icon(device_type: str) -> str:
    """
    Bestimme das Icon für einen Gerätetyp.
    
    Args:
        device_type: KWB Gerätetyp (z.B. "KWB CF2", "KWB Easyfire")
        
    Returns:
        Icon string im Format "mdi:icon-name"
    """
    return DEVICE_TYPE_ICONS.get(device_type, DEVICE_TYPE_ICONS["default"])


def get_category_icon(category: str) -> str:
    """
    Bestimme das Icon für eine Entity-Kategorie.
    
    Args:
        category: Kategorie wie "heating", "temperature", "pump" etc.
        
    Returns:
        Icon string im Format "mdi:icon-name"
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
    Extrahiere Equipment-Typ und -Nummer aus Register-Namen.
    
    Args:
        register_name: Register-Name wie "HK 1 Pumpe", "BWS 2 Temperatur"
        
    Returns:
        Tuple von (equipment_type, equipment_number) oder (None, None)
    """
    # Muster für verschiedene Equipment-Typen
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
