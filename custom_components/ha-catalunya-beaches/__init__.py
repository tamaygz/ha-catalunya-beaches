"""
Custom integration to integrate ha-catalunya-beaches with Home Assistant.

For more details about this integration, please refer to
https://github.com/tamaygz/ha-catalunya-beaches
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import CatalunyaBeachesApiClient
from .const import CONF_LANGUAGE, DOMAIN, LOGGER
from .coordinator import BeachDataUpdateCoordinator
from .data import CatalunyaBeachesData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import CatalunyaBeachesConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CatalunyaBeachesConfigEntry,
) -> bool:
    """Set up Catalunya Beaches from a config entry."""
    language = entry.data.get(CONF_LANGUAGE, "en")
    
    # Create API client
    client = CatalunyaBeachesApiClient(
        session=async_get_clientsession(hass),
        language=language,
    )
    
    # Create data update coordinator
    coordinator = BeachDataUpdateCoordinator(
        hass=hass,
        config_entry=entry,
    )
    
    # Store runtime data
    entry.runtime_data = CatalunyaBeachesData(
        client=client,
        coordinator=coordinator,
        integration=async_get_loaded_integration(hass, entry.domain),
    )

    # Perform first refresh
    await coordinator.async_config_entry_first_refresh()

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: CatalunyaBeachesConfigEntry,
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: CatalunyaBeachesConfigEntry,
) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(
    hass: HomeAssistant,
    entry: CatalunyaBeachesConfigEntry,
) -> None:
    """Handle removal of an entry.
    
    This is called when the entry is being removed. We don't need to do anything
    special here as Home Assistant will automatically clean up entities.
    """
    LOGGER.debug("Removing beach entry: %s", entry.title)
