import sys, pathlib, importlib.util
p = pathlib.Path(__file__).parents[1] / "custom_components/carbu_be/parser.py"
spec = importlib.util.spec_from_file_location("parser", p); parser = importlib.util.module_from_spec(spec)
sys.modules["parser"] = parser; spec.loader.exec_module(parser)

STRUCT = """
<div class="cards">
 <div class="card"><a href="/belgique/index.php/station/esso/tubize/1480/2335"><img src="/images/brandLogo/esso.gif"></a>
  <a href="https://carbu.com/belgique/index.php/station/esso/tubize/1480/2335"><b>Esso Tubize</b> 4 Rue De Nivelles 1480 Tubize</a>
  <div><span>Diesel (B7)</span><span>2,444 €/L</span></div><div>Mise à jour 19/10/26</div>
  <img src="/ads/banner.png"></div>
 <div class="card"><a href="/belgique/index.php/station/shell/saintes/1480/1122"><img src="/images/brandLogo/shell.gif"></a>
  <a href="/belgique/index.php/station/shell/saintes/1480/1122"><b>Shell Saintes</b> 294 Chaussée d'Enghien 1480 Saintes</a>
  <div>Diesel (B7)2,389 €/L</div><div>Mise à jour 20/10/26</div></div>
</div>
<ul>
 <li><a href="/belgique/index.php/station/esso/tubize/1480/2335"><b>Esso Tubize</b></a> 2,444 €/L</li>
 <li><a href="/belgique/index.php/station/q8/braine-le-chateau/1440/77"><b>Q8 Braine</b> Rue X 1 1440 Braine</a> 2,501 €/L</li>
</ul>
<p>Prix maximum officiel : 2,600 €/L</p>
"""
DATA = """<div class="stationItem" data-id="1" data-name="Total Tubize" data-price="1.789" data-lat="50.69" data-lng="4.2" data-link="/x/1"></div>
<div class="stationItem" data-id="2" data-name="Q8" data-price="1,759"></div>"""

def test_structure():
    s = parser.parse_stations(STRUCT)
    assert [x.id for x in s] == ["1122", "2335", "77"], s
    assert s[0].name == "Shell Saintes" and s[0].price == 2.389
    assert s[0].address == "294 Chaussée d'Enghien" and s[0].updated == "20/10/26"
    assert s[1].logo.endswith("esso.gif") and s[1].brand == "Esso"

def test_data_attrs():
    s = parser.parse_stations(DATA)
    assert [x.name for x in s] == ["Q8", "Total Tubize"]
    assert s[1].latitude == 50.69 and s[1].url == "https://carbu.com/x/1"


REAL = """<div id="item_2335" data-lat="50.694483178885" data-lng="4.2046174401978" data-id="2335" data-logo="esso.gif" data-name="Esso Tubize" data-fuelname="Diesel (B7)" data-price="2.444" data-distance="1.1916450040391" data-link="https://carbu.com/belgique/index.php/station/esso/tubize/1480/2335" data-address="Rue De Nivelles 4&lt;br/&gt;1480 Tubize" class="stationItem panel panel-default"><img src="https://carbucomstatic-5141.kxcdn.com//brandLogo/esso.gif"><span>2,444 €/L</span><span>21/10/26</span></div>
<div id="item_1578" data-lat="50.68871508666" data-lng="4.2009632516595" data-id="1578" data-logo="q8.gif" data-name="Q8 Tubize" data-fuelname="Diesel (B7)" data-price="2.399" data-distance="" data-link="https://carbu.com/belgique/index.php/station/q8/tubize/1480/1578" data-address="Rue de Mons 126&lt;br/&gt;1480 Tubize" class="stationItem panel panel-default"></div>"""

def test_real_page():
    s = parser.parse_stations(REAL)
    q8, esso = s
    assert esso.latitude == 50.694483178885 and esso.longitude == 4.2046174401978
    assert esso.address == "Rue De Nivelles 4" and esso.postal_code == "1480" and esso.city == "Tubize"
    assert esso.full_address == "Rue De Nivelles 4, 1480 Tubize"
    assert esso.distance == 1.19 and esso.updated == "21/10/26" and esso.brand == "Esso"
    assert esso.maps_url.endswith("query=50.694483178885,4.2046174401978")
    assert esso.logo.endswith("brandLogo/esso.gif")
    assert q8.distance is None and q8.logo.endswith("/brandLogo/q8.gif")

if __name__ == "__main__":
    test_structure(); test_data_attrs(); test_real_page(); print("OK")
