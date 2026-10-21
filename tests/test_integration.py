import json, re
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from custom_components.carbu_be.const import DOMAIN
import pytest

@pytest.fixture(autouse=True)
def _enable(enable_custom_integrations):
    yield

HTML = """<div class="stationItem" data-id="1122" data-name="Shell Saintes" data-price="1.789" data-lat="50.70" data-lng="4.17" data-distance="3.2" data-logo="shell.gif" data-address="Chaussée 1&lt;br/&gt;1480 Saintes"></div>
<div class="stationItem" data-id="2335" data-name="Esso Tubize" data-price="1.829" data-lat="50.69" data-lng="4.20" data-distance="1.1" data-logo="esso.gif" data-address="Rue 4&lt;br/&gt;1480 Tubize"></div>
<div class="stationItem" data-id="9" data-name="Far Away" data-price="1.500" data-lat="50.9" data-lng="4.4" data-distance="25" data-logo="q8.gif" data-address="X&lt;br/&gt;1000 Bruxelles"></div>"""
LOC = json.dumps([
 {"id":"BE_bw_190","n":"Clabecq","pn":"Tubize","c":"BE","pc":"1480"},
 {"id":"BE_bw_193","n":"Tubize","pn":"Brabant Wallon","c":"BE","pc":"1480"},
 {"id":"LU_lx_3143","n":"Luxembourg","pn":"Luxembourg","c":"LU","pc":"1480"}])
HTML_OLD = """<div><a href="/belgique/index.php/station/shell/saintes/1480/1122"><b>Shell Saintes</b> Chaussée 1 1480 Saintes</a>
<div>Diesel (B7) 1,789 €/L</div></div>
<div><a href="/belgique/index.php/station/esso/tubize/1480/2335"><b>Esso Tubize</b> Rue 4 1480 Tubize</a>
<div>Diesel (B7) 1,829 €/L</div></div>"""

async def test_full_flow(hass, aioclient_mock):
    aioclient_mock.get(re.compile(r".*getlocation_JSON.*"), text=LOC)
    aioclient_mock.get(re.compile(r".*liste-stations-service.*"), text=HTML)

    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert r["type"] == FlowResultType.FORM
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"postal_code": "1480"})
    assert r["step_id"] == "town"
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"town_id": "BE_bw_193", "fuels": ["diesel"]})
    assert r["type"] == FlowResultType.CREATE_ENTRY, r
    assert r["title"] == "Carbu Tubize (1480)"
    await hass.async_block_till_done()

    states = {s.entity_id: s for s in hass.states.async_all("sensor")}
    print(list(states))
    cheap = next(s for k, s in states.items() if k.endswith("moins_cher"))
    avg = next(s for k, s in states.items() if k.endswith("moyenne"))
    assert cheap.state == "1.789" and cheap.attributes["station"] == "Shell Saintes"
    assert cheap.attributes["latitude"] == 50.70 and cheap.attributes["longitude"] == 4.17
    assert cheap.attributes["distance_km"] == 3.2 and "maps_url" in cheap.attributes
    assert cheap.attributes["full_address"] == "Chaussée 1, 1480 Saintes"
    assert cheap.attributes["station_count"] == 2  # 25 km station filtered (10 km default)
    assert float(avg.state) == 1.809
    assert any("GO/Tubize/1480/BE_bw_193" in str(c[1]) for c in aioclient_mock.mock_calls)

async def test_bad_postal(hass, aioclient_mock):
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"postal_code": "abc"})
    assert r["errors"] == {"postal_code": "invalid_postal_code"}
