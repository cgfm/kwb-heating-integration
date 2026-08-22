"""Stable identities and registry migration for FuelSplit sensor entities."""
from __future__ import annotations

import logging
from typing import Any

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

FUEL_SPLIT_ENTITY_ID_SUFFIXES = {
    "pellet": "pellet_energy_total",
    "log_wood": "log_wood_energy_total",
    "unattributed": "fuel_energy_unattributed",
}


def fuel_split_entity_identity(coordinator: Any, kind: str) -> tuple[str, str]:
    """Return the existing unique ID and desired entity ID for a split sensor."""
    suffix = FUEL_SPLIT_ENTITY_ID_SUFFIXES[kind]
    device_prefix = coordinator.sanitize_for_entity_id(
        coordinator.device_name_prefix
    )
    device_identifier = f"{coordinator.host}_{coordinator.slave_id}"
    unique_id = f"kwb_heating_{device_identifier}_{device_prefix}_{suffix}"
    return unique_id, f"sensor.{device_prefix}_{suffix}"


def async_migrate_fuel_split_entity_ids(
    hass: Any, config_entry: Any, coordinator: Any
) -> None:
    """Rename only automatic beta FuelSplit registry IDs to their stable IDs."""
    # Imported lazily so lightweight config tests do not need the complete
    # Home Assistant entity-registry runtime.
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)

    for kind in FUEL_SPLIT_ENTITY_ID_SUFFIXES:
        unique_id, target_entity_id = fuel_split_entity_identity(coordinator, kind)
        current_entity_id = registry.async_get_entity_id(
            "sensor", DOMAIN, unique_id
        )
        if current_entity_id is None:
            continue

        registry_entry = registry.async_get(current_entity_id)
        if (
            registry_entry is None
            or registry_entry.domain != "sensor"
            or registry_entry.platform != DOMAIN
            or registry_entry.unique_id != unique_id
            or registry_entry.config_entry_id != config_entry.entry_id
        ):
            _LOGGER.debug(
                "Skipping FuelSplit entity ID migration for %s: registry identity "
                "does not match sensor/%s/%s/config entry %s",
                current_entity_id,
                DOMAIN,
                unique_id,
                config_entry.entry_id,
            )
            continue

        if current_entity_id == target_entity_id:
            continue

        # HA's own regeneration logic accounts for the registry's stored area,
        # device, entity-name, suggested-object-ID, and object-ID-base metadata.
        # A differing result means the current ID was customized, or that its
        # provenance is uncertain; both cases must be preserved.
        try:
            automatic_entity_id = registry.async_regenerate_entity_id(
                registry_entry
            )
        except Exception:  # noqa: BLE001 - setup must survive uncertain metadata
            _LOGGER.info(
                "Preserving FuelSplit entity ID %s because Home Assistant could "
                "not reliably determine its automatic entity ID",
                current_entity_id,
                exc_info=True,
            )
            continue

        if automatic_entity_id != current_entity_id:
            _LOGGER.info(
                "Preserving FuelSplit entity ID %s because its current ID does "
                "not match Home Assistant's automatic ID %s",
                current_entity_id,
                automatic_entity_id,
            )
            continue

        target_entry = registry.async_get(target_entity_id)
        if target_entry is not None:
            if (
                target_entry.domain == "sensor"
                and target_entry.platform == DOMAIN
                and target_entry.unique_id == unique_id
                and target_entry.config_entry_id == config_entry.entry_id
            ):
                _LOGGER.debug(
                    "FuelSplit target entity ID %s already belongs to the same "
                    "registry identity",
                    target_entity_id,
                )
            else:
                _LOGGER.warning(
                    "Cannot migrate FuelSplit entity %s to %s because the target "
                    "entity ID belongs to another registry entry",
                    current_entity_id,
                    target_entity_id,
                )
            continue

        target_object_id = target_entity_id.partition(".")[2]
        available_entity_id = registry.async_get_available_entity_id(
            "sensor",
            target_object_id,
            current_entity_id=current_entity_id,
        )
        if available_entity_id != target_entity_id:
            _LOGGER.warning(
                "Cannot migrate FuelSplit entity %s to %s because the target "
                "entity ID is already occupied",
                current_entity_id,
                target_entity_id,
            )
            continue

        registry.async_update_entity(
            current_entity_id, new_entity_id=target_entity_id
        )
        _LOGGER.info(
            "Migrated automatic FuelSplit entity ID %s to %s",
            current_entity_id,
            target_entity_id,
        )
