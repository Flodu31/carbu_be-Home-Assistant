"""Data update coordinator for Carbu BE."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CarbuClient, CarbuError
from .const import (
    CONF_FUELS,
    CONF_POSTAL_CODE,
    CONF_SCAN_INTERVAL,
    CONF_TOWN_ID,
    CONF_TOWN_NAME,
    DEFAULT_SCAN_INTERVAL_MIN,
    DOMAIN,
)
from .parser import Station

_LOGGER = logging.getLogger(__name__)


class CarbuCoordinator(DataUpdateCoordinator[dict[str, list[Station]]]):
    """Fetch all configured fuels in one refresh."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        minutes = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MIN)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.data[CONF_POSTAL_CODE]}",
            update_interval=timedelta(minutes=minutes),
            config_entry=entry,
        )
        self.client = CarbuClient(async_get_clientsession(hass))
        self.entry = entry

    @property
    def fuels(self) -> list[str]:
        return self.entry.options.get(CONF_FUELS, self.entry.data[CONF_FUELS])

    async def _async_update_data(self) -> dict[str, list[Station]]:
        data: dict[str, list[Station]] = {}
        errors: list[str] = []
        for fuel in self.fuels:
            try:
                data[fuel] = await self.client.async_get_stations(
                    fuel,
                    self.entry.data[CONF_TOWN_NAME],
                    self.entry.data[CONF_POSTAL_CODE],
                    self.entry.data[CONF_TOWN_ID],
                )
            except CarbuError as err:
                errors.append(f"{fuel}: {err}")
                # keep previous values for this fuel if we had some
                if self.data and fuel in self.data:
                    data[fuel] = self.data[fuel]
        if errors and not data:
            raise UpdateFailed("; ".join(errors))
        for err in errors:
            _LOGGER.warning("Carbu update partially failed — %s", err)
        return data
