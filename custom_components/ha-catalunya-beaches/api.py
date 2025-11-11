"""API Client for Catalunya Beaches."""

from __future__ import annotations

import socket
from typing import Any

import aiohttp
import async_timeout

from .const import API_BASE_URL, API_BEACH_DETAIL, API_BEACH_LIST, API_TIMEOUT, LOGGER
from .data import BeachInfo, BeachListItem


class CatalunyaBeachesApiClientError(Exception):
    """Exception to indicate a general API error."""


class CatalunyaBeachesApiClientCommunicationError(
    CatalunyaBeachesApiClientError,
):
    """Exception to indicate a communication error."""


class CatalunyaBeachesApiClientDataError(
    CatalunyaBeachesApiClientError,
):
    """Exception to indicate an error parsing data."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    response.raise_for_status()


class CatalunyaBeachesApiClient:
    """API Client for Catalunya Beaches."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        language: str = "en",
    ) -> None:
        """Initialize the API client.
        
        Args:
            session: aiohttp client session
            language: API language (en or ca)
        """
        self._session = session
        self._language = language

    async def async_get_beach_list(self) -> list[BeachListItem]:
        """Get list of all available beaches.
        
        Returns:
            List of BeachListItem objects
            
        Raises:
            CatalunyaBeachesApiClientCommunicationError: Communication error
            CatalunyaBeachesApiClientDataError: Data parsing error
        """
        url = f"{API_BASE_URL}{API_BEACH_LIST.format(language=self._language)}"
        
        try:
            data = await self._api_wrapper(method="get", url=url)
            
            if not isinstance(data, dict) or "playas" not in data:
                msg = "Invalid beach list response format"
                raise CatalunyaBeachesApiClientDataError(msg)
            
            beaches = []
            for beach_data in data["playas"]:
                try:
                    beaches.append(BeachListItem.from_dict(beach_data))
                except (KeyError, ValueError, TypeError) as err:
                    LOGGER.warning(
                        "Failed to parse beach %s: %s",
                        beach_data.get("id", "unknown"),
                        err,
                    )
                    continue
            
            return beaches
            
        except CatalunyaBeachesApiClientError:
            raise
        except Exception as exception:
            msg = f"Unexpected error parsing beach list - {exception}"
            raise CatalunyaBeachesApiClientDataError(msg) from exception

    async def async_get_beach_detail(self, beach_id: int) -> BeachInfo:
        """Get detailed information for a specific beach.
        
        Args:
            beach_id: Beach ID to fetch
            
        Returns:
            BeachInfo object with detailed information
            
        Raises:
            CatalunyaBeachesApiClientCommunicationError: Communication error
            CatalunyaBeachesApiClientDataError: Data parsing error
        """
        url = f"{API_BASE_URL}{API_BEACH_DETAIL.format(beach_id=beach_id, language=self._language)}"
        
        try:
            data = await self._api_wrapper(method="get", url=url)
            
            if not isinstance(data, dict):
                msg = f"Invalid beach detail response format for beach {beach_id}"
                raise CatalunyaBeachesApiClientDataError(msg)
            
            if data.get("error", False):
                msg = f"API returned error for beach {beach_id}"
                raise CatalunyaBeachesApiClientDataError(msg)
            
            # Check if beach exists in response
            items = data.get("items", {})
            playa = items.get("playa", {})
            if playa.get("existe") == "N":
                msg = f"Beach {beach_id} does not exist"
                raise CatalunyaBeachesApiClientDataError(msg)
            
            return BeachInfo.from_dict(data)
            
        except CatalunyaBeachesApiClientError:
            raise
        except Exception as exception:
            msg = f"Unexpected error parsing beach {beach_id} detail - {exception}"
            raise CatalunyaBeachesApiClientDataError(msg) from exception

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Execute API request with error handling.
        
        Args:
            method: HTTP method
            url: Request URL
            data: Optional request data
            headers: Optional request headers
            
        Returns:
            Parsed JSON response
            
        Raises:
            CatalunyaBeachesApiClientCommunicationError: Communication error
        """
        try:
            async with async_timeout.timeout(API_TIMEOUT):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                _verify_response_or_raise(response)
                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information from {url} - {exception}"
            raise CatalunyaBeachesApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information from {url} - {exception}"
            raise CatalunyaBeachesApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Unexpected error communicating with API - {exception}"
            raise CatalunyaBeachesApiClientCommunicationError(
                msg,
            ) from exception
