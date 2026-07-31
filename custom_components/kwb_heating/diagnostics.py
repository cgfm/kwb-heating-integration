"""Diagnostics support for KWB Heating integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

# Keys to redact from config entry data and diagnostics output
TO_REDACT = {
    "host",
    "serial_port",
    "configuration_url",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    diag: dict[str, Any] = {
        "config_entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "device_info": async_redact_data(coordinator.device_info, TO_REDACT),
        "detected_version": coordinator.detected_version,
        "register_count": len(coordinator._registers) if hasattr(coordinator, "_registers") and coordinator._registers else 0,
        "last_update_success": coordinator.last_update_success,
    }

    return diag
