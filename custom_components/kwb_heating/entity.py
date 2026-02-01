"""Base entity for KWB Heating integration."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from .coordinator import KWBDataUpdateCoordinator


class KWBBaseEntity(CoordinatorEntity):
    """Base class for KWB heating system entities.

    Provides common functionality for all entity types including:
    - Entity name and unique ID generation
    - Device info assignment
    - Entity ID sanitization
    """

    def __init__(
        self,
        coordinator: "KWBDataUpdateCoordinator",
        register: dict[str, Any],
        platform: str,
    ) -> None:
        """Initialize the base entity.

        Args:
            coordinator: The data update coordinator
            register: Register configuration dictionary
            platform: Platform name (sensor, switch, select, number)
        """
        super().__init__(coordinator)
        self._register = register
        self._address = register["starting_address"]

        # Generate structured entity name and unique ID
        self._attr_name, self._attr_unique_id = self._generate_entity_name_and_id(
            register, coordinator
        )

        # Set explicit entity_id to ensure device name prefix is included
        device_prefix = coordinator.sanitize_for_entity_id(coordinator.device_name_prefix)
        register_name = coordinator.sanitize_for_entity_id(register["name"])
        self.entity_id = f"{platform}.{device_prefix}_{register_name}"

        # Set device info
        self._attr_device_info = coordinator.device_info

    def _generate_entity_name_and_id(
        self, register: dict[str, Any], coordinator: "KWBDataUpdateCoordinator"
    ) -> tuple[str, str]:
        """Generate proper entity name and unique ID.

        Args:
            register: Register configuration dictionary
            coordinator: The data update coordinator

        Returns:
            Tuple of (entity_name, unique_id)
        """
        # Get base name from register
        base_name = register["name"]

        # Add device name prefix to entity name
        device_prefix = coordinator.device_name_prefix
        entity_name = f"{device_prefix} {base_name}"

        # Use coordinator's centralized unique ID generation
        unique_id = coordinator.generate_entity_unique_id(register)

        return entity_name, unique_id
