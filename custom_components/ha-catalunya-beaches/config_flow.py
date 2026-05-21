"""Config flow for Catalunya Beaches."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    CatalunyaBeachesApiClient,
    CatalunyaBeachesApiClientCommunicationError,
    CatalunyaBeachesApiClientError,
)
from .const import (
    CONF_BEACH_ID,
    CONF_BEACH_LATITUDE,
    CONF_BEACH_LONGITUDE,
    CONF_BEACH_NAME,
    CONF_ENABLED_ENTITIES,
    CONF_LANGUAGE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_ENABLED_ENTITIES,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    ENTITY_AIR_TEMP,
    ENTITY_BEACH_INFO,
    ENTITY_DESCRIPTION,
    ENTITY_JELLYFISH_ALERT,
    ENTITY_JELLYFISH_STATUS,
    ENTITY_LAST_TEST_DATE,
    ENTITY_LIFEGUARD,
    ENTITY_OUT_OF_SEASON,
    ENTITY_RAIN_RISK,
    ENTITY_SKY_CONDITION,
    ENTITY_UV_INDEX,
    ENTITY_WATER_QUALITY,
    ENTITY_WATER_QUALITY_GOOD,
    ENTITY_WATER_TEMP,
    ENTITY_WAVE_HEIGHT,
    ENTITY_WIND_SPEED,
    LOGGER,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
)
from .data import BeachListItem
from .util import parse_coordinate


class CatalunyaBeachesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Catalunya Beaches."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._beaches: list[BeachListItem] = []
        self._selected_beach: BeachListItem | None = None
        self._language: str = "en"

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle the initial step - language selection."""
        errors = {}

        if user_input is not None:
            self._language = user_input[CONF_LANGUAGE]
            return await self.async_step_select_beach()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LANGUAGE, default="en"): vol.In(
                        {
                            "en": "English",
                            "ca": "Català",
                        }
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_select_beach(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle beach selection step."""
        errors = {}

        if not self._beaches:
            # Fetch beach list
            try:
                client = CatalunyaBeachesApiClient(
                    session=async_create_clientsession(self.hass),
                    language=self._language,
                )
                self._beaches = await client.async_get_beach_list()
            except CatalunyaBeachesApiClientCommunicationError as exception:
                LOGGER.error("Communication error fetching beach list: %s", exception)
                errors["base"] = "cannot_connect"
            except CatalunyaBeachesApiClientError as exception:
                LOGGER.exception("Error fetching beach list: %s", exception)
                errors["base"] = "unknown"

            if errors:
                return self.async_show_form(
                    step_id="select_beach",
                    data_schema=vol.Schema({}),
                    errors=errors,
                )

        if user_input is not None:
            beach_id = user_input[CONF_BEACH_ID]
            self._selected_beach = next(
                (beach for beach in self._beaches if beach.id == beach_id),
                None,
            )

            if self._selected_beach:
                # Check if already configured
                await self.async_set_unique_id(f"{DOMAIN}_{beach_id}")
                self._abort_if_unique_id_configured()

                return await self.async_step_configure_entities()

            errors["base"] = "invalid_beach"

        # Create beach selection options
        beach_options = {
            beach.id: f"{beach.nombre} ({beach.municipio}, {beach.costa})"
            for beach in sorted(self._beaches, key=lambda x: x.nombre)
        }

        return self.async_show_form(
            step_id="select_beach",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BEACH_ID): vol.In(beach_options),
                }
            ),
            errors=errors,
        )

    async def async_step_configure_entities(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Configure which entities to enable."""
        if user_input is not None:
            latitude = parse_coordinate(
                self._selected_beach.latitud if self._selected_beach else None
            )
            longitude = parse_coordinate(
                self._selected_beach.longitud if self._selected_beach else None
            )

            data = {
                CONF_BEACH_ID: self._selected_beach.id,
                CONF_BEACH_NAME: self._selected_beach.nombre,
                CONF_LANGUAGE: self._language,
                CONF_UPDATE_INTERVAL: user_input.get(
                    CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                ),
            }

            if latitude is not None:
                data[CONF_BEACH_LATITUDE] = latitude
            if longitude is not None:
                data[CONF_BEACH_LONGITUDE] = longitude

            # Create config entry
            return self.async_create_entry(
                title=self._selected_beach.nombre,
                data=data,
                options={
                    CONF_ENABLED_ENTITIES: user_input.get(
                        CONF_ENABLED_ENTITIES, DEFAULT_ENABLED_ENTITIES
                    ),
                },
            )

        # Entity selection schema
        return self.async_show_form(
            step_id="configure_entities",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=DEFAULT_UPDATE_INTERVAL,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                    vol.Optional(
                        CONF_ENABLED_ENTITIES,
                        default=DEFAULT_ENABLED_ENTITIES,
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {
                                    "value": ENTITY_WATER_TEMP,
                                    "label": "Water Temperature",
                                },
                                {"value": ENTITY_AIR_TEMP, "label": "Air Temperature"},
                                {
                                    "value": ENTITY_WATER_QUALITY,
                                    "label": "Water Quality Status",
                                },
                                {"value": ENTITY_UV_INDEX, "label": "UV Index"},
                                {"value": ENTITY_WAVE_HEIGHT, "label": "Wave Height"},
                                {"value": ENTITY_WIND_SPEED, "label": "Wind Speed"},
                                {
                                    "value": ENTITY_SKY_CONDITION,
                                    "label": "Sky Condition",
                                },
                                {
                                    "value": ENTITY_JELLYFISH_STATUS,
                                    "label": "Jellyfish Status",
                                },
                                {
                                    "value": ENTITY_LAST_TEST_DATE,
                                    "label": "Last Water Test Date",
                                },
                                {
                                    "value": ENTITY_DESCRIPTION,
                                    "label": "Beach Description",
                                },
                                {
                                    "value": ENTITY_BEACH_INFO,
                                    "label": "Beach Info",
                                },
                                {
                                    "value": ENTITY_LIFEGUARD,
                                    "label": "Lifeguard Present",
                                },
                                {
                                    "value": ENTITY_OUT_OF_SEASON,
                                    "label": "Out of Season",
                                },
                                {
                                    "value": ENTITY_WATER_QUALITY_GOOD,
                                    "label": "Water Quality Good",
                                },
                                {
                                    "value": ENTITY_JELLYFISH_ALERT,
                                    "label": "Jellyfish Alert",
                                },
                                {"value": ENTITY_RAIN_RISK, "label": "High Rain Risk"},
                            ],
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        ),
                    ),
                }
            ),
            description_placeholders={
                "beach_name": self._selected_beach.nombre,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> CatalunyaBeachesOptionsFlow:
        """Get the options flow for this handler."""
        return CatalunyaBeachesOptionsFlow()


class CatalunyaBeachesOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Catalunya Beaches."""

    def __init__(self) -> None:
        """Initialize the options flow."""
        super().__init__()
        self._pending_options: dict[str, Any] | None = None

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manage the options."""
        return await self.async_step_configure()

    async def async_step_configure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Configure beach options."""
        errors: dict[str, str] = {}

        current_interval = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL,
            self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        )
        current_entities = self.config_entry.options.get(
            CONF_ENABLED_ENTITIES,
            DEFAULT_ENABLED_ENTITIES,
        )

        if user_input is not None:
            options = {
                CONF_UPDATE_INTERVAL: user_input.get(
                    CONF_UPDATE_INTERVAL, current_interval
                ),
                CONF_ENABLED_ENTITIES: user_input.get(
                    CONF_ENABLED_ENTITIES, current_entities
                ),
            }

            if user_input.get("force_refresh"):
                # Trigger force refresh. The coordinator is created during setup of the
                # config entry and stored in `hass.data[DOMAIN][entry_id]`. It's possible
                # the integration is not fully set up yet, so guard against missing data.
                try:
                    coordinator = self.hass.data[DOMAIN][
                        self.config_entry.entry_id
                    ].coordinator
                    await coordinator.async_force_refresh()
                except Exception:  # pragma: no cover - defensive handling
                    LOGGER.exception(
                        "Coordinator not available for %s when forcing refresh",
                        self.config_entry.entry_id,
                    )
                    errors["base"] = "unknown"

            if user_input.get("delete_history") and not errors:
                # Preserve options while awaiting delete confirmation.
                self._pending_options = options
                return await self.async_step_confirm_delete()

            # If there were no errors (e.g. missing coordinator), update options.
            if not errors:
                return self.async_create_entry(title="", data=options)

        return self.async_show_form(
            step_id="configure",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=current_interval,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                    vol.Optional(
                        CONF_ENABLED_ENTITIES,
                        default=current_entities,
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {
                                    "value": ENTITY_WATER_TEMP,
                                    "label": "Water Temperature",
                                },
                                {"value": ENTITY_AIR_TEMP, "label": "Air Temperature"},
                                {
                                    "value": ENTITY_WATER_QUALITY,
                                    "label": "Water Quality Status",
                                },
                                {"value": ENTITY_UV_INDEX, "label": "UV Index"},
                                {"value": ENTITY_WAVE_HEIGHT, "label": "Wave Height"},
                                {"value": ENTITY_WIND_SPEED, "label": "Wind Speed"},
                                {
                                    "value": ENTITY_SKY_CONDITION,
                                    "label": "Sky Condition",
                                },
                                {
                                    "value": ENTITY_JELLYFISH_STATUS,
                                    "label": "Jellyfish Status",
                                },
                                {
                                    "value": ENTITY_LAST_TEST_DATE,
                                    "label": "Last Water Test Date",
                                },
                                {
                                    "value": ENTITY_DESCRIPTION,
                                    "label": "Beach Description",
                                },
                                {
                                    "value": ENTITY_BEACH_INFO,
                                    "label": "Beach Info",
                                },
                                {
                                    "value": ENTITY_LIFEGUARD,
                                    "label": "Lifeguard Present",
                                },
                                {
                                    "value": ENTITY_OUT_OF_SEASON,
                                    "label": "Out of Season",
                                },
                                {
                                    "value": ENTITY_WATER_QUALITY_GOOD,
                                    "label": "Water Quality Good",
                                },
                                {
                                    "value": ENTITY_JELLYFISH_ALERT,
                                    "label": "Jellyfish Alert",
                                },
                                {"value": ENTITY_RAIN_RISK, "label": "High Rain Risk"},
                            ],
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        ),
                    ),
                    vol.Optional("force_refresh", default=False): bool,
                    vol.Optional("delete_history", default=False): bool,
                }
            ),
        )

    async def async_step_confirm_delete(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Confirm deletion of historical data."""
        if self._pending_options is None:
            if user_input is None:
                return await self.async_step_configure()
            options = self.config_entry.options
        else:
            options = self._pending_options
        if user_input is not None:
            if user_input.get("confirm"):
                # Delete historical data
                # This would require calling recorder service to purge entity data
                # For now, we'll just acknowledge
                LOGGER.info(
                    "Historical data deletion requested for beach %s",
                    self.config_entry.data[CONF_BEACH_NAME],
                )
                # TODO: Implement actual history deletion via recorder service

            self._pending_options = None
            return self.async_create_entry(title="", data=options)

        return self.async_show_form(
            step_id="confirm_delete",
            data_schema=vol.Schema(
                {
                    vol.Required("confirm", default=False): bool,
                }
            ),
            description_placeholders={
                "beach_name": self.config_entry.data[CONF_BEACH_NAME],
            },
        )
