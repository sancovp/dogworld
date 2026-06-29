import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld.places import PlaceWorld

WORLD = pathlib.Path(__file__).resolve().parents[1] / "examples" / "world"


def _pw():
    pw = PlaceWorld(WORLD)
    pw.spawn("owl", "forest")
    pw.spawn("dog", "yard")
    return pw


def test_loads_places_from_dirs():
    pw = _pw()
    assert set(pw.places) == {"forest", "yard"}
    assert "yard" in pw.places["forest"].exits
    assert "bark" in pw.places["forest"].affords


def test_move_only_through_exits():
    pw = _pw()
    ok, _ = pw.move("dog", "forest")
    assert ok and pw.here("dog").name == "forest"
    bad, msg = pw.move("dog", "moon")          # not an exit
    assert not bad and "no exit" in msg


def test_proximity_and_sharing():
    pw = _pw()
    pw.register_share("owl", ["see"])           # the owl lends night-vision to those near it
    assert not pw.co_located("dog", "owl")      # dog in yard, owl in forest
    assert pw.shared_with("dog") == {}          # nothing lent at a distance
    pw.move("dog", "forest")                     # now proximate
    assert pw.co_located("dog", "owl")
    assert pw.shared_with("dog") == {"owl": ["see"]}
    assert "see" in pw.chart_for("dog")          # the lent skill shows up in the chart


def test_capability_is_intrinsic_plus_place_plus_shares():
    pw = _pw()
    pw.register_share("owl", ["see"])
    pw.move("dog", "forest")
    cap = pw.capability("dog", intrinsic=["hear"])
    assert {"hear", "bark", "sniff", "see"} <= cap   # intrinsic ∪ forest affords ∪ owl's lent skill
