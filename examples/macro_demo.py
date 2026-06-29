"""macro_demo — retrieve a learned circuit from the RAG and conduct it as ONE macro-action.

The agent has a library of learned routes. Given a goal, it retrieves the best-matching circuit and,
IF its input terminals hold in the current world, conducts the whole gated route in a single move —
instead of re-deriving move→see→bark step by step. If nothing is conductable, it falls back.

Run: pip install dogworld[circuits]; python3 examples/macro_demo.py   (offline, no API)
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World
from dogworld.sop import FlowStep, extrude
from dogworld.macro import CircuitLibrary, HAVE_UCO


def main():
    if not HAVE_UCO:
        print("Macro-actions need UCO: pip install dogworld[circuits].")
        return

    # the agent has learned two routes (its circuit library / RAG)
    confirm_bark = extrude("Confirm-then-bark", "Canine", [
        FlowStep("dog", "move to forest", place="forest", passed=True),
        FlowStep("dog", "see (borrowed)", warrant="owl_present(forest)",
                 produces="confirmed_owl(forest)", place="forest", passed=True),
        FlowStep("dog", "bark", warrant="confirmed_owl(forest)", produces="near(dog,owl)",
                 place="forest", passed=True),
    ], subdomain="Alerting", tags=("owl", "bark", "alert"), fitness=3)
    fetch = extrude("Fetch-the-ball", "Canine", [
        FlowStep("dog", "grab ball", warrant="ball_in_sight", produces="has_ball", passed=True),
    ], tags=("ball", "fetch"), fitness=1)

    lib = CircuitLibrary([confirm_bark, fetch])

    print("== retrieve for goal 'alert about an owl' (RAG over learned routes) ==")
    for s in lib.retrieve("alert owl"):
        print(f"   {s.name}  (fitness {s.fitness})")

    # case 1: the world satisfies the circuit's input terminal -> conduct the whole route as one move
    w1 = World(); w1.close("owl_present(forest)")
    circuit, res = lib.run_macro("alert owl", w1)
    print(f"\n== MACRO-ACTION (input terminal holds) ==")
    print(f"   invoked '{circuit.name}' as one move → {res.status}")
    print(f"   conducted in one step: {res.context.get('conducted')}")
    print(f"   produced output terminal near(dog,owl): {w1.warrants('near(dog,owl)')}")

    # case 2: the input terminal does NOT hold -> nothing conductable -> fall back to atomic
    w2 = World()
    circuit2, res2 = lib.run_macro("alert owl", w2)
    print(f"\n== input terminal MISSING ==")
    print(f"   conductable circuit: {circuit2}  → agent falls back to deriving atomic actions")
    print("   -> the macro fires only when its precondition is warranted; soundness all the way up.")


if __name__ == "__main__":
    main()
