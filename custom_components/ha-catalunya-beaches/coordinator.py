"""DataUpdateCoordinator for ha-catalunya-beaches."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

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
