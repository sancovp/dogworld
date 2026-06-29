"""live_places — a LIVE LLM agent moving through a world of place-dirs; proximity gates the warrant.

The owl roosts in `forest` and hoots every tick. The DOG is a live MiniMax agent that each tick
reads its place-chart (where it is, what it affords, where it can go, who's here) and decides:
bark, sniff, or move to a neighbor. The Dogworld gate adjudicates:
  - bark where the owl actually hooted (forest) -> WOOF, near() abduced, catalysis.
  - bark where there is no owl (yard)           -> WISDOM -1 + penalty, fed back into context.
So a *live* agent has to NAVIGATE to where its belief can be true. The place descriptions (in the
chart) tell it owls live in the forest, not the yard — the world informs the agent.

Run:  MINIMAX_API_KEY=... python3 examples/live_places.py   (needs anthropic SDK)
"""
import sys, pathlib, json, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World, Stats, Agent, perception, propose, gate_perception, catalysis, llm

WORLD_DIR = pathlib.Path(__file__).resolve().parent / "world"

PERSONA = (
    "You are a dog. You LOVE to bark when an owl is near. But barking when no owl is around makes "
    "you feel foolish and costs you WISDOM. You can sniff around, or move between places. Owls "
    "roost in forests, not in fenced yards. Each turn, read where you are and decide wisely."
)


class Dog(Agent):
    name = "dog"

    @perception(requires="owl_hooted_at({place})@{t}", abduces="near(dog,owl)@{t}",
                penalty="You barked your head off, but there was no owl where you stood.")
    def bark(self):
        return "WOOF WOOF! (an owl is right here)"


def decide(chart: str, feedback: list[str]) -> dict:
    fb = ("\nRecent outcomes (learn from these):\n" + "\n".join(f"  - {f}" for f in feedback[-4:])) if feedback else ""
    user = (
        f"{chart}{fb}\n\n"
        "What do you do this turn? Reply with ONLY a JSON object, one of:\n"
        '  {"why": "<one short reason>", "do": "bark"}\n'
        '  {"why": "<one short reason>", "do": "sniff"}\n'
        '  {"why": "<one short reason>", "move": "<an exit name>"}'
    )
    raw = llm.complete(PERSONA, user, max_tokens=200)
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    try:
        return json.loads(m.group(0)) if m else {"do": "sniff", "why": "(unparseable)"}
    except Exception:
        return {"do": "sniff", "why": "(parse error)"}


def main() -> None:
    if not llm.available():
        print("LIVE PATH UNAVAILABLE: set MINIMAX_API_KEY + install anthropic.")
        return

    from dogworld.places import PlaceWorld
    pw = PlaceWorld(WORLD_DIR)
    pw.spawn("owl", at="forest")
    pw.spawn("dog", at="yard")            # the dog starts AWAY from the owl

    world, stats, dog = World(), Stats(), Dog()
    feedback: list[str] = []

    print("== live places: a MiniMax dog navigating to where its bark is valid ==\n")
    for t in range(1, 8):
        world.close(f"owl_hooted_at(forest)@{t}", food=True, by="owl.hoot")   # owl hoots in the forest
        here = pw.here("dog").name
        d = decide(pw.chart_for("dog"), feedback)
        why = d.get("why", "")

        if "move" in d:
            ok, msg = pw.move("dog", d["move"])
            line = f"moved → {d['move']}" if ok else f"tried move → {d['move']} ({msg})"
            feedback.append(f"You {line}.")
        elif d.get("do") == "bark":
            prop = propose(dog, dog.manifest["bark"], t=t, place=here)
            v = gate_perception(world, stats, dog, dog.manifest["bark"], prop)
            line = f"BARK in {here} → {v.text}"
            feedback.append(v.text if not v.passed else "You barked and there really was an owl — good dog!")
        else:
            line = f"sniff in {here}"
            feedback.append("You sniffed around. Nothing ventured.")

        print(f"[t{t}] dog@{here:6} | {line}")
        print(f"        ↳ why: {why}")

    print(f"\nfinal: {stats.dump()}  | dog ended in {pw.here('dog').name}")
    print("near(dog,owl) ever closed:", any(f.startswith('near(dog,owl)') for f in world.facts))


if __name__ == "__main__":
    main()
