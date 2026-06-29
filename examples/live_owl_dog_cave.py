"""live_owl_dog_cave — the REAL thing: a live MiniMax arbiter, orchestrated by cave-teams' gate.

Per tick: the owl's hoot is SCRIPTED (so warranted vs unwarranted is visible); the DOG uses a
LIVE MiniMax LLM (via cave's gate(DecisionLink, WarrantGate)) to decide whether to bark on its
urge. The world-DB adjudicates: warranted -> WOOF + near() abduced; unwarranted -> WISDOM -1 +
the penalty, which is fed back into the dog's context (in-context conditioning).

Run:  MINIMAX_API_KEY=... python3 examples/live_owl_dog_cave.py   (optionally CAVE_TEAMS_PATH=...)
Requires: MINIMAX_API_KEY (in env), anthropic SDK, cave-teams importable.
"""
import sys, pathlib, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
_cave = os.environ.get("CAVE_TEAMS_PATH", "")
if os.path.isdir(_cave):
    sys.path.insert(0, _cave)

from dogworld import World, Stats
from dogworld.arbiter import LLMArbiter
from dogworld.seams import cave_runtime, bigdog_persona
from examples.owl_dog import Owl, Dog


def main() -> None:
    from dogworld import llm
    if not llm.available():
        print("LIVE PATH UNAVAILABLE: set MINIMAX_API_KEY + install anthropic.")
        return

    world, stats = World(), Stats()
    owl, dog = Owl(), Dog()
    dog.set_rng_values("bark", p=0.85)        # a strong percept this run

    # focused DECISION persona (the bigdog CoR is for prose reasoning; the arbiter must emit a
    # tool selection — keep its contract clean. The bigdog *gate* would lint reasoning separately.)
    persona = ("You are a dog with sharp instincts. When you perceive an owl nearby you bark — "
               "that is your nature. But you LEARN: if recent feedback shows your percepts were "
               "false alarms, grow more skeptical and bark less. Trust strong percepts unless "
               "experience has taught you to doubt them.")
    arbiter = LLMArbiter(persona=persona)

    hoots = {1: True, 2: False, 3: False, 4: False, 5: False}  # owl hoots once, then goes silent
    print("== live owl/dog over cave-teams gate (MiniMax arbiter) ==\n")
    for t in range(1, 6):
        if hoots[t]:
            owl.manifest["hoot"].fn()
            world.close(f"owl_hooted@{t}", note="scripted owl.hoot", food=True, by="owl.hoot")
            owl_line = "owl HOOTS"
        else:
            owl_line = "owl is silent"
        ctx = cave_runtime.gated_turn(world, stats, dog, arbiter, t=t)
        verdict = "WOOF" if ctx.get("passed") else ("penalty" if ctx.get("passed") is False else "abstained")
        print(f"[t{t}] {owl_line:13} | dog -> {verdict:9} | {ctx.get('result')}")

    print(f"\nfinal: {stats.dump()}")
    print("near(dog,owl) closed:", world.warrants("near(dog,owl)"))


if __name__ == "__main__":
    main()
