"""Async client for carbu.com."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import logging
from urllib.parse import quote

import aiohttp

from .const import FUELS, HEADERS, LOCATION_URL, STATIONS_URL
from .parser import Station, parse_stations

_LOGGER = logging.getLogger(__name__)
TIMEOUT = aiohttp.ClientTimeout(total=30)


class CarbuError(Exception):
    """Generic carbu.com error."""


@dataclass
class Town:
    id: str
    name: str
    postal_code: str
    province: str


class CarbuClient:
    """Minimal carbu.com scraper."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _get(self, url: str) -> str:
        _LOGGER.debug("GET %s", url)
        try:
            async with self._session.get(url, headers=HEADERS, timeout=TIMEOUT) as resp:
                if resp.status != 200:
                    raise CarbuError(f"HTTP {resp.status} for {url}")
                return await resp.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise CarbuError(f"Request failed for {url}: {err}") from err

    async def async_get_towns(self, postal_code: str) -> list[Town]:
        """Belgian towns matching a postal code."""
        raw = await self._get(LOCATION_URL.format(postal_code=quote(postal_code)))
        try:
            data = json.loads(raw)
        except ValueError as err:
            raise CarbuError("Invalid location JSON") from err
        return [
            Town(id=i["id"], name=i["n"], postal_code=i["pc"], province=i.get("pn", ""))
            for i in data
            if i.get("c") == "BE" and str(i.get("pc")) == str(postal_code)
        ]

    async def async_get_stations(
        self, fuel: str, town_name: str, postal_code: str, town_id: str
    ) -> list[Station]:
        """Stations around the town for a fuel, cheapest first."""
        code = FUELS[fuel][0]
        url = STATIONS_URL.format(
            fuel_code=code,
            town=quote(town_name.replace(" ", "-")),
            postal_code=postal_code,
            town_id=town_id,
        )
        html = await self._get(url)
        stations = parse_stations(html)
        if not stations:
            _LOGGER.warning(
                "No station/price found on %s — carbu.com layout may have changed", url
            )
        return stations
