import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World
from dogworld.sop import FlowStep, extrude
from dogworld.macro import CircuitLibrary, HAVE_UCO

_BARK_FLOW = [
    FlowStep("dog", "move", place="forest", passed=True),
    FlowStep("dog", "see", warrant="owl_present(forest)", produces="confirmed_owl(forest)",
             place="forest", passed=True),
    FlowStep("dog", "bark", warrant="confirmed_owl(forest)", produces="near(dog,owl)",
             place="forest", passed=True),
]
_FETCH_FLOW = [FlowStep("dog", "grab", warrant="ball_in_sight", produces="has_ball", passed=True)]


def _lib():
    # FRESH SOPs each call — tests that reinforce/decay run_count must not pollute one another
    bark = extrude("Confirm-then-bark", "Canine", _BARK_FLOW, subdomain="Alerting",
                   tags=("owl", "alert"), fitness=3)
    fetch = extrude("Fetch", "Canine", _FETCH_FLOW, tags=("ball",), fitness=1)
    return CircuitLibrary([bark, fetch])


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


# --- self-curation ---
def test_score_combines_fitness_and_reuse():
    lib = _lib()
    s = lib.sops[0]                          # Confirm-then-bark, fitness 3
    assert lib.score(s) == 3.0
    s.run_count = 4
    assert lib.score(s) == 7.0               # fitness + reuse


def test_run_macro_reinforces_on_success():
    if not HAVE_UCO:
        return
    lib = _lib()
    bark = next(s for s in lib.sops if s.name == "Confirm-then-bark")
    assert bark.run_count == 0
    w = World(); w.close("owl_present(forest)")
    lib.run_macro("alert owl", w)
    assert bark.run_count == 1               # a successful macro promoted it


def test_reuse_promotes_a_low_fitness_route():
    if not HAVE_UCO:
        return
    lib = _lib()
    fetch = next(s for s in lib.sops if s.name == "Fetch")
    fetch.run_count = 5                        # heavily reused
    assert lib.top(1)[0].name == "Fetch"       # reuse lifts it above the higher-fitness one (fitness 3)


def test_decay_ages_and_prune_drops_dead():
    lib = _lib()
    bark = next(s for s in lib.sops if s.name == "Confirm-then-bark"); bark.run_count = 10
    lib.decay(0.5)
    assert bark.run_count == 5                  # aged
    # Fetch has fitness 1, run_count 0 -> score 1 (kept); add a dead route
    lib.add(extrude("Dead", "X", [FlowStep("a", "x", passed=True)], fitness=0))  # score 0
    dropped = lib.prune(min_score=0.5)
    assert [s.name for s in dropped] == ["Dead"]
    assert all(s.name != "Dead" for s in lib.sops)