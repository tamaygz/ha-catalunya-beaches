"""Button platform for Catalunya Beaches."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory

from .const import LOGGER
from .entity import CatalunyaBeachEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import BeachDataUpdateCoordinator
    from .data import CatalunyaBeachesConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CatalunyaBeachesConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Catalunya Beaches button platform."""
    coordinator = entry.runtime_data.coordinator

    # Create refresh button (diagnostic entity)
    button = CatalunyaBeachRefreshButton(
        coordinator=coordinator,
        beach_id=entry.data["beach_id"],
        beach_name=entry.data["beach_name"],
    )

    LOGGER.debug("Setting up refresh button for beach %s", entry.data["beach_name"])
    async_add_entities([button])


class CatalunyaBeachRefreshButton(CatalunyaBeachEntity, ButtonEntity):
    """Button to refresh beach data."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:refresh"

    def __init__(
        self,
        coordinator: BeachDataUpdateCoordinator,
        beach_id: int,
        beach_name: str,
    ) -> None:
        """Initialize the refresh button."""
        super().__init__(coordinator, beach_id, beach_name)
        self._attr_unique_id = f"{beach_id}_refresh"
        self._attr_name = "Refresh"

    async def async_press(self) -> None:
        """Handle the button press - trigger a refresh."""
        LOGGER.debug("Refresh button pressed for beach %s", self._beach_name)
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attributes = {}

        if self.coordinator.last_fetched:
            attributes["last_fetched"] = self.coordinator.last_fetched.isoformat()

        if self.coordinator.last_update_success_time:
            attributes["last_update_success"] = (
                self.coordinator.last_update_success_time.isoformat()
            )

        return attributes
