"""
Custom integration to integrate ha-catalunya-beaches with Home Assistant.

For more details about this integration, please refer to
https://github.com/tamaygz/ha-catalunya-beaches
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import voluptuous as vol

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, Platform
from homeassistant.core import ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import CatalunyaBeachesApiClient
from .const import CONF_BEACH_ID, CONF_LANGUAGE, DOMAIN, LOGGER
from .coordinator import BeachDataUpdateCoordinator
from .data import CatalunyaBeachesData

SERVICE_REFRESH_ALL = "refresh_all"
SERVICE_REFRESH_BEACH = "refresh_beach"

SERVICE_REFRESH_BEACH_SCHEMA = vol.Schema(
    {
        vol.Required("beach_id"): cv.positive_int,
    }
)

if TYPE_CHECKING:
    from homeassistant.core import ConfigType, HomeAssistant

    from .data import CatalunyaBeachesConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]

# Frontend resource constants
_CARD_STATIC_PATH = "/ha-catalunya-beaches-frontend"
_CARD_FILE_URL = f"{_CARD_STATIC_PATH}/catalunya-beaches-card.js"
# Bump whenever www/catalunya-beaches-card.js changes to force browser cache invalidation.
# Keep in sync with CARD_VERSION in www/catalunya-beaches-card.js.
_CARD_VERSION = "2"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the card JS file as a static HTTP endpoint (runs once per domain load)."""
    www_path = Path(__file__).parent / "www"
    if www_path.is_dir():
        hass.http.register_static_path(
            _CARD_STATIC_PATH,
            str(www_path),
            cache_headers=False,
        )
        LOGGER.debug(
            "Catalunya Beaches: serving frontend resources from %s at %s",
            www_path,
            _CARD_STATIC_PATH,
        )
    return True


async def _async_register_lovelace_resource(hass: HomeAssistant) -> None:
    """Auto-register the card as a Lovelace module resource if not already present."""
    versioned_url = f"{_CARD_FILE_URL}?v={_CARD_VERSION}"
    try:
        from homeassistant.components.lovelace.resources import (  # noqa: PLC0415
            ResourceStorageCollection,
        )

        lovelace_data = hass.data.get("lovelace")
        if lovelace_data is None:
            LOGGER.debug(
                "Catalunya Beaches: Lovelace not initialised; skipping auto-registration."
                " Add manually: type=module, URL=%s",
                versioned_url,
            )
            return

        resources = lovelace_data.get("resources")
        if not isinstance(resources, ResourceStorageCollection):
            LOGGER.debug(
                "Catalunya Beaches: Lovelace not in storage mode; skipping auto-registration."
                " Add manually: type=module, URL=%s",
                versioned_url,
            )
            return

        await resources.async_load()
        if any(
            item.get("url", "").startswith(_CARD_STATIC_PATH)
            for item in resources.async_items()
        ):
            LOGGER.debug("Catalunya Beaches: card resource already registered.")
            return

        await resources.async_create_item(
            {"res_type": "module", "url": versioned_url}
        )
        LOGGER.info("Catalunya Beaches: registered card resource %s", versioned_url)

    except Exception as err:  # noqa: BLE001
        LOGGER.warning(
            "Catalunya Beaches: could not auto-register Lovelace resource (%s)."
            " Add manually via Settings → Dashboards → ⋮ → Resources:"
            " type=module, URL=%s",
            err,
            versioned_url,
        )


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

    # Register services (only once for the domain)
    await async_setup_services(hass)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Schedule Lovelace resource registration once per domain (not once per beach entry).
    domain_data = hass.data.setdefault(DOMAIN, {})
    if not domain_data.get("card_registered"):
        domain_data["card_registered"] = True

        async def _do_register(_event: object = None) -> None:
            await _async_register_lovelace_resource(hass)

        if hass.is_running:
            hass.async_create_task(_do_register())
        else:
            hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED,
                lambda e: hass.async_create_task(_do_register()),
            )

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


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Catalunya Beaches integration."""
    # Only register services once
    if hass.services.has_service(DOMAIN, SERVICE_REFRESH_ALL):
        return

    async def async_refresh_all_beaches(call: ServiceCall) -> None:
        """Handle the refresh_all service call."""
        LOGGER.debug("Refreshing all beaches via service call")

        # Get all config entries for this domain
        entries = hass.config_entries.async_entries(DOMAIN)

        for entry in entries:
            if entry.runtime_data and entry.runtime_data.coordinator:
                coordinator = entry.runtime_data.coordinator
                await coordinator.async_request_refresh()
                LOGGER.debug("Refreshed beach: %s", entry.title)

    async def async_refresh_beach(call: ServiceCall) -> None:
        """Handle the refresh_beach service call."""
        beach_id = call.data["beach_id"]
        LOGGER.debug("Refreshing beach %s via service call", beach_id)

        # Find the config entry for this beach
        entries = hass.config_entries.async_entries(DOMAIN)

        for entry in entries:
            if entry.data.get(CONF_BEACH_ID) == beach_id:
                if entry.runtime_data and entry.runtime_data.coordinator:
                    coordinator = entry.runtime_data.coordinator
                    await coordinator.async_request_refresh()
                    LOGGER.info("Refreshed beach %s (%s)", entry.title, beach_id)
                    return

        LOGGER.warning("Beach with ID %s not found", beach_id)

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_ALL,
        async_refresh_all_beaches,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_BEACH,
        async_refresh_beach,
        schema=SERVICE_REFRESH_BEACH_SCHEMA,
    )
