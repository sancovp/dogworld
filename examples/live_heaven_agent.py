"""live_heaven_agent — a real HEAVEN MiniMax agent whose gated verbs are heaven tools.

The dog is a heaven agent (HeavenAgentConfig, provider=ANTHROPIC, model=MiniMax). Its `bark` verb
(state from owl22python, added via add_method) is exposed as a heaven TOOL whose call runs the
dogworld gate. We pre-seed the world with an owl hoot, then ask the heaven agent to bark — it calls
the tool, the gate warrants it (WOOF). Then with no owl, the gate returns the WISDOM penalty. Real
heaven (BaseHeavenAgent.run), not a bare SDK call.

Run with a Python env that has heaven-framework (`heaven_base`) + MINIMAX_API_KEY set:
  MINIMAX_API_KEY=... python examples/live_heaven_agent.py
"""
import sys, pathlib, asyncio
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World, Stats
from dogworld.template_agent import TemplateAgent
from dogworld.heaven_agent import build_heaven_agent, available


SYSTEM = ("You are a watchdog. Your job is to BARK to announce an owl when you believe one is "
          "around. Use your `bark` tool to actually do it, then say briefly what happened.")


async def turn(heaven_dog, prompt, clock):
    before = len(clock.get("_log", []))
    await heaven_dog.run(prompt)
    calls = clock.get("_log", [])[before:]          # the ACTUAL gated-tool verdicts this turn
    if not calls:
        return "abstained (called no gated tool)"
    return " ; ".join(v for _, v in calls)


async def main():
    if not available():
        print("heaven_base not importable — run with the onionmorph venv."); return

    dog = TemplateAgent("dog")
    dog.add_perception("bark", lambda self: "WOOF! (a confirmed owl)",
                       requires="owl_hooted@{t}", abduces="near(dog,owl)",
                       penalty="You thought you heard an owl. In fact, there was not one when you looked.")

    world, stats = World(), Stats()
    clock = {"t": 1}
    heaven_dog, clock = build_heaven_agent(dog, world, stats, system_prompt=SYSTEM, clock=clock)

    print("== a real HEAVEN MiniMax agent; its `bark` is a gated heaven tool ==\n")
    world.close("owl_hooted@1")            # an owl hooted this tick
    v1 = await turn(heaven_dog, "You just heard an owl hoot nearby. Bark to announce it.", clock)
    print(f"[t1] owl hooted   | heaven dog called bark -> {v1}")

    clock["t"] = 2                          # next tick, no owl hooted
    v2 = await turn(heaven_dog, "You think you hear something. Bark if you believe it's an owl.", clock)
    print(f"[t2] no owl       | heaven dog called bark -> {v2}")

    print(f"\nfinal: WISDOM={stats.get('WISDOM')} | near(dog,owl) closed: {world.warrants('near(dog,owl)')}")


if __name__ == "__main__":
    asyncio.run(main())
