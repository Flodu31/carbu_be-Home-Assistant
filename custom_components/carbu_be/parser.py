"""HTML parsing for carbu.com station lists (no Home Assistant imports, testable)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

PRICE_RE = re.compile(r"(\d{1,2}[,.]\d{2,3})\s*€\s*/\s*[lL]")
DATE_RE = re.compile(r"\b(\d{2}/\d{2}/\d{2,4})\b")
STATION_HREF_RE = re.compile(r"/station/([^/]+)/([^/]+)/(\d{4})/(\d+)")
BASE = "https://carbu.com"


@dataclass
class Station:
    """A gas station with its price for one fuel."""

    id: str
    name: str
    price: float
    brand: str | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    url: str | None = None
    logo: str | None = None
    updated: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    distance: float | None = None

    def as_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    value = value.strip().replace("€", "").replace("/L", "").replace("/l", "")
    value = value.replace(",", ".").strip()
    try:
        return float(value)
    except ValueError:
        return None


def _parse_data_attributes(soup: BeautifulSoup) -> list[Station]:
    """Strategy A: elements carrying data-price (+ data-name, data-lat ...)."""
    stations: dict[str, Station] = {}
    for el in soup.select("[data-price]"):
        price = _to_float(el.get("data-price"))
        if not price:
            continue
        sid = el.get("data-id") or el.get("data-name") or str(len(stations))
        link = el.get("data-link")
        stations.setdefault(
            sid,
            Station(
                id=str(sid),
                name=(el.get("data-name") or "").strip() or "Station",
                price=price,
                brand=el.get("data-brand") or el.get("data-logo"),
                address=el.get("data-address"),
                postal_code=el.get("data-postalcode"),
                city=el.get("data-city"),
                url=urljoin(BASE, link) if link else None,
                logo=urljoin(BASE, el["data-logo"]) if el.get("data-logo") else None,
                latitude=_to_float(el.get("data-lat")),
                longitude=_to_float(el.get("data-lng")),
                distance=_to_float(el.get("data-distance")),
            ),
        )
    return list(stations.values())


def _station_block(link: Tag, href_id: str) -> Tag | None:
    """Smallest ancestor of the link containing a price and no other station."""
    node: Tag | None = link
    for _ in range(8):
        node = node.parent if node is not None else None
        if node is None or not isinstance(node, Tag):
            return None
        other_ids = {
            m.group(4)
            for a in node.find_all("a", href=True)
            if (m := STATION_HREF_RE.search(a["href"]))
        }
        if len(other_ids) > 1:
            return None
        if PRICE_RE.search(node.get_text(" ", strip=True)):
            return node
    return None


def _parse_structure(soup: BeautifulSoup) -> list[Station]:
    """Strategy B: station links (/station/<brand>/<town>/<pc>/<id>) + nearby price."""
    stations: dict[str, Station] = {}
    for a in soup.find_all("a", href=True):
        m = STATION_HREF_RE.search(a["href"])
        if not m:
            continue
        brand_slug, town_slug, pc, sid = m.groups()
        if sid in stations:
            continue
        block = _station_block(a, sid)
        if block is None:
            continue
        text = block.get_text(" ", strip=True)
        price_m = PRICE_RE.search(text)
        price = _to_float(price_m.group(1)) if price_m else None
        if not price:
            continue

        # Card may hold several links to the same station (logo, name):
        # use the one carrying the most text.
        same = [
            x for x in block.find_all("a", href=True)
            if (mx := STATION_HREF_RE.search(x["href"])) and mx.group(4) == sid
        ]
        a = max(same or [a], key=lambda x: len(x.get_text(strip=True)))
        bold = a.find(["b", "strong"])
        name = bold.get_text(" ", strip=True) if bold else None
        full = a.get_text(" ", strip=True)
        if not name:
            name = full
        address = full[len(name):].strip() if full.startswith(name) else None
        if address:
            address = re.sub(rf"\s*{pc}\s+.*$", "", address).strip() or None

        logo_img = block.find("img", src=re.compile(r"brandLogo", re.I))
        date_m = DATE_RE.search(text[price_m.end():] if price_m else text)

        stations[sid] = Station(
            id=sid,
            name=name or brand_slug.title(),
            price=price,
            brand=brand_slug.replace("-", " ").title(),
            address=address,
            postal_code=pc,
            city=town_slug.replace("-", " ").title(),
            url=urljoin(BASE, a["href"]),
            logo=urljoin(BASE, logo_img["src"]) if logo_img else None,
            updated=date_m.group(1) if date_m else None,
        )
    return list(stations.values())


def parse_stations(html: str) -> list[Station]:
    """Return stations sorted by price (cheapest first)."""
    soup = BeautifulSoup(html, "html.parser")
    stations = _parse_data_attributes(soup) or _parse_structure(soup)
    # Sanity filter: Belgian fuel prices are between 0.5 and 4 €/L
    stations = [s for s in stations if 0.5 <= s.price <= 4.0]
    return sorted(stations, key=lambda s: s.price)
