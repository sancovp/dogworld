import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World
from dogworld.sop import FlowStep, extrude
from dogworld.macro import CircuitLibrary, HAVE_UCO

_BARK = extrude("Confirm-then-bark", "Canine", [
    FlowStep("dog", "move", place="forest", passed=True),
    FlowStep("dog", "see", warrant="owl_present(forest)", produces="confirmed_owl(forest)",
             place="forest", passed=True),
    FlowStep("dog", "bark", warrant="confirmed_owl(forest)", produces="near(dog,owl)",
             place="forest", passed=True),
], subdomain="Alerting", tags=("owl", "alert"), fitness=3)
_FETCH = extrude("Fetch", "Canine", [
    FlowStep("dog", "grab", warrant="ball_in_sight", produces="has_ball", passed=True)], tags=("ball",))


def _lib():
    return CircuitLibrary([_BARK, _FETCH])


def test_retrieve_ranks_relevant_first():
    hits = _lib().retrieve("alert owl")
    assert hits and hits[0].name == "Confirm-then-bark"
    assert _lib().retrieve("kubernetes") == []


def test_macro_fires_when_input_terminal_holds():
    if not HAVE_UCO:
        return
    from uco import LinkStatus
    w = World(); w.close("owl_present(forest)")
    circuit, res = _lib().run_macro("alert owl", w)
    assert circuit is not None and res.status == LinkStatus.SUCCESS
    assert res.context.get("conducted") == ["dog.move", "dog.see", "dog.bark"]   # whole route, one move
    assert w.warrants("near(dog,owl)")                                            # output terminal produced


def test_macro_falls_back_when_input_terminal_missing():
    if not HAVE_UCO:
        return
    circuit, res = _lib().run_macro("alert owl", World())     # owl_present(forest) not closed
    assert circuit is None and res is None                    # nothing conductable -> caller derives atomically


def test_conductable_respects_input_terminals():
    if not HAVE_UCO:
        return
    w = World(); w.close("ball_in_sight")                     # satisfies Fetch, not Confirm-then-bark
    assert _lib().conductable("fetch the ball", w).name == "Fetch"
    assert _lib().conductable("alert owl", w) is None         # its input terminal owl_present(forest) absent