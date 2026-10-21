"""Sensors for Carbu BE."""

from __future__ import annotations

from statistics import mean
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CarbuConfigEntry
from .const import (
    ATTR_STATIONS,
    CONF_POSTAL_CODE,
    CONF_TOWN_NAME,
    DOMAIN,
    FUELS,
    MAX_STATIONS_IN_ATTR,
)
from .coordinator import CarbuCoordinator

UNIT = "EUR/L"


async def async_setup_entry(
    hass: HomeAssistant, entry: CarbuConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = []
    for fuel in coordinator.fuels:
        entities.append(CarbuCheapestSensor(coordinator, fuel))
        entities.append(CarbuAverageSensor(coordinator, fuel))
    async_add_entities(entities)


class _CarbuBase(CoordinatorEntity[CarbuCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UNIT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3
    _attr_icon = "mdi:gas-station"
    _attr_attribution = "Données carbu.com"

    def __init__(self, coordinator: CarbuCoordinator, fuel: str, kind: str) -> None:
        super().__init__(coordinator)
        self.fuel = fuel
        entry = coordinator.entry
        pc = entry.data[CONF_POSTAL_CODE]
        town = entry.data[CONF_TOWN_NAME]
        self._attr_unique_id = f"{entry.entry_id}_{fuel}_{kind}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Carbu {town} ({pc})",
            manufacturer="carbu.com",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://carbu.com/belgique/",
        )

    @property
    def _stations(self):
        return (self.coordinator.data or {}).get(self.fuel) or []

    @property
    def available(self) -> bool:
        return super().available and bool(self._stations)


class CarbuCheapestSensor(_CarbuBase):
    """Cheapest price around the town."""

    def __init__(self, coordinator: CarbuCoordinator, fuel: str) -> None:
        super().__init__(coordinator, fuel, "cheapest")
        self._attr_name = f"{FUELS[fuel][1]} moins cher"

    @property
    def native_value(self) -> float | None:
        return self._stations[0].price if self._stations else None

    @property
    def entity_picture(self) -> str | None:
        return self._stations[0].logo if self._stations else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self._stations:
            return {}
        best = self._stations[0]
        attrs = {
            "fuel": FUELS[self.fuel][1],
            "station": best.name,
            "brand": best.brand,
            "address": best.address,
            "postal_code": best.postal_code,
            "city": best.city,
            "full_address": best.full_address,
            "distance_km": best.distance,
            "maps_url": best.maps_url,
            "url": best.url,
            "price_updated": best.updated,
            "station_count": len(self._stations),
            ATTR_STATIONS: [s.as_dict() for s in self._stations[:MAX_STATIONS_IN_ATTR]],
        }
        if best.latitude is not None and best.longitude is not None:
            attrs["latitude"] = best.latitude
            attrs["longitude"] = best.longitude
        return {k: v for k, v in attrs.items() if v is not None}


class CarbuAverageSensor(_CarbuBase):
    """Average price of listed stations."""

    _attr_icon = "mdi:chart-line"

    def __init__(self, coordinator: CarbuCoordinator, fuel: str) -> None:
        super().__init__(coordinator, fuel, "average")
        self._attr_name = f"{FUELS[fuel][1]} moyenne"

    @property
    def native_value(self) -> float | None:
        return round(mean(s.price for s in self._stations), 3) if self._stations else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self._stations:
            return {}
        prices = [s.price for s in self._stations]
        return {
            "min": min(prices),
            "max": max(prices),
            "station_count": len(prices),
            "saving_50l_vs_max": round((max(prices) - min(prices)) * 50, 2),
        }
