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

if __name__ == "__main__":
    test_structure(); test_data_attrs(); print("OK")
