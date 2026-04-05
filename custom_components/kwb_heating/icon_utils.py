"""Icon utilities for KWB Heating integration."""
from __future__ import annotations

from .const import ENTITY_ICONS


def get_entity_icon(register: dict, entity_type: str = "sensor") -> str:
    """Determine the appropriate icon for an entity based on the register data.

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
