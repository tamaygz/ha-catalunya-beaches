"""Base entity class for Catalunya Beaches."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import BeachDataUpdateCoordinator


class CatalunyaBeachEntity(CoordinatorEntity[BeachDataUpdateCoordinator]):
    """Base entity for Catalunya Beaches."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BeachDataUpdateCoordinator,
        beach_id: int,
        beach_name: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        
        self._beach_id = beach_id
        self._beach_name = beach_name
        
        # Create device info for the beach
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(beach_id))},
            name=beach_name,
            manufacturer="Agència Catalana de l'Aigua",
            model="Beach Monitoring Station",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None
