"""Config flow for Carbu BE."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import CarbuClient, CarbuError, Town
from .const import (
    CONF_FUELS,
    CONF_MAX_DISTANCE,
    CONF_POSTAL_CODE,
    DEFAULT_MAX_DISTANCE_KM,
    CONF_SCAN_INTERVAL,
    CONF_TOWN_ID,
    CONF_TOWN_NAME,
    DEFAULT_FUELS,
    DEFAULT_SCAN_INTERVAL_MIN,
    DOMAIN,
    FUELS,
    MIN_SCAN_INTERVAL_MIN,
)


def _fuel_selector() -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=[SelectOptionDict(value=k, label=v[1]) for k, v in FUELS.items()],
            multiple=True,
            mode=SelectSelectorMode.LIST,
        )
    )


class CarbuConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._postal_code: str = ""
        self._towns: list[Town] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            pc = str(user_input[CONF_POSTAL_CODE]).strip()
            if not (pc.isdigit() and len(pc) == 4):
                errors[CONF_POSTAL_CODE] = "invalid_postal_code"
            else:
                client = CarbuClient(async_get_clientsession(self.hass))
                try:
                    self._towns = await client.async_get_towns(pc)
                except CarbuError:
                    errors["base"] = "cannot_connect"
                else:
                    if not self._towns:
                        errors[CONF_POSTAL_CODE] = "no_town"
                    else:
                        self._postal_code = pc
                        return await self.async_step_town()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_POSTAL_CODE, default="1480"): str}
            ),
            errors=errors,
        )

    async def async_step_town(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_FUELS):
                errors[CONF_FUELS] = "no_fuel"
            else:
                town = next(t for t in self._towns if t.id == user_input[CONF_TOWN_ID])
                await self.async_set_unique_id(town.id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Carbu {town.name} ({town.postal_code})",
                    data={
                        CONF_POSTAL_CODE: town.postal_code,
                        CONF_TOWN_ID: town.id,
                        CONF_TOWN_NAME: town.name,
                        CONF_FUELS: user_input[CONF_FUELS],
                    },
                )

        # Prefer the main commune (province != commune name) as default
        default_town = next(
            (t for t in self._towns if t.province and t.province != t.name
             and not any(o.name == t.province for o in self._towns)),
            self._towns[0],
        )
        town_selector = SelectSelector(
            SelectSelectorConfig(
                options=[SelectOptionDict(value=t.id, label=t.name) for t in self._towns],
                mode=SelectSelectorMode.DROPDOWN,
            )
        )
        return self.async_show_form(
            step_id="town",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TOWN_ID, default=default_town.id): town_selector,
                    vol.Required(CONF_FUELS, default=DEFAULT_FUELS): _fuel_selector(),
                }
            ),
            errors=errors,
            description_placeholders={"postal_code": self._postal_code},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return CarbuOptionsFlow()


class CarbuOptionsFlow(OptionsFlow):
    """Change fuels and refresh interval."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_FUELS):
                errors[CONF_FUELS] = "no_fuel"
            else:
                user_input[CONF_SCAN_INTERVAL] = int(user_input[CONF_SCAN_INTERVAL])
                user_input[CONF_MAX_DISTANCE] = float(user_input[CONF_MAX_DISTANCE])
                return self.async_create_entry(data=user_input)

        entry = self.config_entry
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_FUELS,
                        default=entry.options.get(CONF_FUELS, entry.data[CONF_FUELS]),
                    ): _fuel_selector(),
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MIN
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL_MIN,
                            max=1440,
                            step=5,
                            unit_of_measurement="min",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        CONF_MAX_DISTANCE,
                        default=entry.options.get(
                            CONF_MAX_DISTANCE, DEFAULT_MAX_DISTANCE_KM
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=50,
                            step=1,
                            unit_of_measurement="km",
                            mode=NumberSelectorMode.SLIDER,
                        )
                    ),
                }
            ),
            errors=errors,
        )
