"""Constants for the Carbu BE integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "carbu_be"

CONF_POSTAL_CODE = "postal_code"
CONF_TOWN_ID = "town_id"
CONF_TOWN_NAME = "town_name"
CONF_FUELS = "fuels"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_MAX_DISTANCE = "max_distance"
DEFAULT_MAX_DISTANCE_KM = 10

DEFAULT_SCAN_INTERVAL_MIN = 60
MIN_SCAN_INTERVAL_MIN = 30
DEFAULT_UPDATE_INTERVAL = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MIN)

BASE_URL = "https://carbu.com"
LOCATION_URL = (
    BASE_URL
    + "/commonFunctions/getlocation/controller.getlocation_JSON.php"
    "?location={postal_code}&SHRT=1"
)
STATIONS_URL = (
    BASE_URL + "/belgique/liste-stations-service/{fuel_code}/{town}/{postal_code}/{town_id}"
)

# key -> (carbu.com URL code, display name)
FUELS: dict[str, tuple[str, str]] = {
    "super95": ("E10", "Super 95 (E10)"),
    "super98": ("SP98", "Super 98 (E5)"),
    "diesel": ("GO", "Diesel (B7)"),
    "lpg": ("GPL", "LPG"),
}
DEFAULT_FUELS = ["super95", "diesel"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/129.0 Safari/537.36"
    ),
    "Accept-Language": "fr-BE,fr;q=0.9,en;q=0.8",
}

ATTR_STATIONS = "stations"
MAX_STATIONS_IN_ATTR = 10
