"""DataUpdateCoordinator for ha-catalunya-beaches."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import (
    CatalunyaBeachesApiClientCommunicationError,
    CatalunyaBeachesApiClientDataError,
    CatalunyaBeachesApiClientError,
)
from .const import CONF_BEACH_ID, DEFAULT_UPDATE_INTERVAL, DOMAIN, LOGGER
from .data import BeachInfo

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import CatalunyaBeachesConfigEntry


class BeachDataUpdateCoordinator(DataUpdateCoordinator[BeachInfo]):
    """Class to manage fetching beach data from the API."""

    config_entry: CatalunyaBeachesConfigEntry
    _STATIC_URL_PREFIX = "/local/" + DOMAIN
    _STATIC_DIR_NAME = DOMAIN
    _HTTP_OK_STATUS = 200
    _ASSET_REQUEST_TIMEOUT_SECONDS = 15
    _MAX_ASSET_BYTES = 5 * 1024 * 1024
    _ASSET_BASE_URLS = (
        "https://aca-web.gencat.cat/images/platges/",
        "http://aca-web.gencat.cat/images/platges/",
        "https://aplicacions.aca.gencat.cat/platges/AppJava/images/platges/",
        "http://aplicacions.aca.gencat.cat/platges/AppJava/images/platges/",
        "https://aplicacions.aca.gencat.cat/platges/AppJava/images/iconos/",
        "http://aplicacions.aca.gencat.cat/platges/AppJava/images/iconos/",
    )

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: CatalunyaBeachesConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        self.beach_id = config_entry.data[CONF_BEACH_ID]
        self.last_fetched: datetime | None = None

        # Get update interval from config or use default
        update_interval = config_entry.options.get(
            "update_interval",
            config_entry.data.get("update_interval", DEFAULT_UPDATE_INTERVAL),
        )

        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_{self.beach_id}",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> BeachInfo:
        """Fetch beach data from API.

        Returns:
            BeachInfo object with current beach data

        Raises:
            UpdateFailed: When update fails
        """
        try:
            client = self.config_entry.runtime_data.client
            beach_info = await client.async_get_beach_detail(self.beach_id)
            await self._async_cache_assets(beach_info)

            LOGGER.debug(
                "Successfully updated data for beach %s (%s)",
                beach_info.nombre,
                self.beach_id,
            )

            # Update last fetched timestamp
            self.last_fetched = dt_util.now()

            return beach_info

        except CatalunyaBeachesApiClientCommunicationError as exception:
            # Communication errors should trigger retry
            LOGGER.warning(
                "Communication error updating beach %s: %s",
                self.beach_id,
                exception,
            )
            raise UpdateFailed(
                f"Error communicating with API: {exception}"
            ) from exception

        except CatalunyaBeachesApiClientDataError as exception:
            # Data parsing errors might be temporary
            LOGGER.warning(
                "Data parsing error for beach %s: %s",
                self.beach_id,
                exception,
            )
            raise UpdateFailed(f"Error parsing beach data: {exception}") from exception

        except CatalunyaBeachesApiClientError as exception:
            # General API errors
            LOGGER.error(
                "Unexpected API error for beach %s: %s",
                self.beach_id,
                exception,
            )
            raise UpdateFailed(f"Unexpected API error: {exception}") from exception

        except Exception as exception:  # pylint: disable=broad-except
            # Catch-all for unexpected errors
            LOGGER.exception(
                "Unexpected error updating beach %s",
                self.beach_id,
            )
            raise UpdateFailed(f"Unexpected error: {exception}") from exception

    async def async_force_refresh(self) -> None:
        """Force an immediate refresh of beach data."""
        await self.async_request_refresh()

    async def _async_cache_assets(self, beach_info: BeachInfo) -> None:
        """Cache remote beach assets locally and replace URLs with local static URLs."""
        if beach_info.imagenes:
            beach_info.imagenes = await asyncio.gather(
                *(
                    self._async_cache_single_asset(asset)
                    for asset in beach_info.imagenes
                )
            )

        if beach_info.iconos:
            icon_keys = list(beach_info.iconos.keys())
            icon_values = list(beach_info.iconos.values())
            cached_icons = await asyncio.gather(
                *(self._async_cache_single_asset(asset) for asset in icon_values)
            )
            beach_info.iconos = dict(zip(icon_keys, cached_icons, strict=True))

        if beach_info.calidad_playa and beach_info.calidad_playa.icono:
            beach_info.calidad_playa.icono = await self._async_cache_single_asset(
                beach_info.calidad_playa.icono
            )

        if beach_info.medusas and beach_info.medusas.icono:
            beach_info.medusas.icono = await self._async_cache_single_asset(
                beach_info.medusas.icono
            )

    async def _async_cache_single_asset(self, asset_reference: str) -> str:
        """Cache one remote asset locally and return a static `/local` URL."""
        if not asset_reference:
            return asset_reference
        if asset_reference.startswith(self._STATIC_URL_PREFIX):
            return asset_reference

        candidate_urls = self._build_candidate_urls(asset_reference)
        for candidate_url in candidate_urls:
            filename = Path(urlparse(candidate_url).path).name
            if not filename:
                continue
            filename = re.sub(r"[^A-Za-z0-9_.()-]", "_", filename)
            if (
                not filename
                or filename in {".", ".."}
                or ".." in filename
                or filename.startswith("-")
            ):
                continue

            static_root = (
                Path(self.hass.config.path("www"))
                / self._STATIC_DIR_NAME
                / str(self.beach_id)
            )
            local_path = static_root / filename
            if not local_path.resolve(strict=False).is_relative_to(
                static_root.resolve(strict=False)
            ):
                continue
            local_url = f"{self._STATIC_URL_PREFIX}/{self.beach_id}/{filename}"

            if local_path.exists():
                return local_url

            session = async_get_clientsession(self.hass)
            try:
                async with session.get(
                    candidate_url,
                    timeout=aiohttp.ClientTimeout(total=self._ASSET_REQUEST_TIMEOUT_SECONDS),
                ) as response:
                    if response.status != self._HTTP_OK_STATUS:
                        continue
                    content_length = response.headers.get("Content-Length")
                    if content_length:
                        try:
                            content_length_int = int(content_length)
                        except ValueError:
                            content_length_int = None
                        if (
                            content_length_int is not None
                            and content_length_int > self._MAX_ASSET_BYTES
                        ):
                            LOGGER.debug(
                                "Skipping oversized asset from %s (%s bytes)",
                                candidate_url,
                                content_length_int,
                            )
                            continue
                    content_type = response.headers.get("Content-Type", "")
                    if not content_type.startswith("image/"):
                        LOGGER.debug(
                            "Skipping non-image asset response from %s (%s)",
                            candidate_url,
                            content_type,
                        )
                        continue
                    content = await response.read()
            except (
                aiohttp.ClientError,
                OSError,
                TimeoutError,
            ) as exception:  # pragma: no cover - defensive network handling
                LOGGER.debug(
                    "Failed to cache asset from %s: %s",
                    candidate_url,
                    exception,
                )
                continue

            if not content:
                continue
            if len(content) > self._MAX_ASSET_BYTES:
                LOGGER.debug(
                    "Skipping oversized downloaded asset from %s (%s bytes)",
                    candidate_url,
                    len(content),
                )
                continue

            try:
                await asyncio.to_thread(
                    local_path.parent.mkdir,
                    parents=True,
                    exist_ok=True,
                )
                await asyncio.to_thread(local_path.write_bytes, content)
            except OSError as exception:  # pragma: no cover - fs protection
                LOGGER.debug(
                    "Failed to write cached asset %s: %s",
                    local_path,
                    exception,
                )
                continue

            return local_url

        return asset_reference

    def _build_candidate_urls(self, asset_reference: str) -> list[str]:
        """Build candidate absolute URLs for remote assets."""
        if asset_reference.startswith(("http://", "https://")):
            return [asset_reference]

        sanitized = asset_reference.lstrip("/")
        return [urljoin(base_url, sanitized) for base_url in self._ASSET_BASE_URLS]

    def update_interval_seconds(self, new_interval: int) -> None:
        """Update the polling interval.

        Args:
            new_interval: New interval in seconds
        """
        self.update_interval = timedelta(seconds=new_interval)
        LOGGER.debug(
            "Updated polling interval for beach %s to %s seconds",
            self.beach_id,
            new_interval,
        )
