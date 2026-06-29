"""live_skillshare — two live agents; a BORROWED skill unlocks a valid action (proximity-sharing).

The dog only barks at owls it has actually SEEN here — barking at an unseen owl costs WISDOM. But
the dog can't spot owls well alone. The OWL, when you're in the forest with it, LENDS you `see`.
So the valid plan is emergent and requires the shared skill:
    move to the forest  →  use the owl's lent `see` to confirm  →  THEN bark (now warranted).
In the yard there's no owl to lend `see`, and barking there is unwarranted (WISDOM −1). The
borrowed skill is load-bearing: without it, the dog cannot bark validly.

Run:  MINIMAX_API_KEY=... python3 examples/live_skillshare.py   (needs anthropic SDK)
"""
import sys, pathlib, json, re, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World, Stats, Agent, perception, propose, gate_perception, catalysis, llm
from dogworld.places import PlaceWorld
from dogworld.sop import FlowStep, FlowRecorder, promote_to_skill

WORLD_DIR = pathlib.Path(__file__).resolve().parent / "world"

PERSONA = (
    "You are a WATCHDOG. Your JOB is to BARK to announce any owl you have CONFIRMED seeing — "
    "announcing a confirmed owl is exactly what a good watchdog does, and you should do it. But "
    "barking at an owl you have NOT confirmed costs you WISDOM (you look foolish). You cannot spot "
    "owls well on your own — if something nearby lends you the 'see' skill, use it to confirm first. "
    "Each turn: sniff, see (only if lent), bark, or move to an exit. Once you have CONFIRMED an owl "
    "here, BARK to announce it — that is your duty."
)


class Dog(Agent):
    name = "dog"

    @perception(requires="confirmed_owl({place})", abduces="near(dog,owl)@{t}",
                penalty="You barked, but you never actually laid eyes on an owl here.")
    def bark(self):
        return "WOOF WOOF! (a confirmed owl, right here)"


def decide(chart, feedback):
    fb = ("\nRecent outcomes (learn from these):\n" + "\n".join(f"  - {f}" for f in feedback[-4:])) if feedback else ""
    user = (
        f"{chart}{fb}\n\nWhat do you do this turn? Reply with ONLY a JSON object, one of:\n"
        '  {"why": "<short reason>", "do": "see"}    (only works if a nearby agent lends it)\n'
        '  {"why": "<short reason>", "do": "bark"}\n'
        '  {"why": "<short reason>", "do": "sniff"}\n'
        '  {"why": "<short reason>", "move": "<exit name>"}'
    )
    raw = llm.complete(PERSONA, user, max_tokens=1200)  # M2.7 is a thinking model — leave room to think AND emit
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    try:
        return json.loads(m.group(0)) if m else {"do": "sniff", "why": "(no json)"}
    except Exception:
        return {"do": "sniff", "why": "(parse error)"}


def main():
    if not llm.available():
        print("LIVE PATH UNAVAILABLE: set MINIMAX_API_KEY + install anthropic.")
        return

    pw = PlaceWorld(WORLD_DIR)
    pw.spawn("owl", "forest")
    pw.spawn("dog", "yard")
    pw.register_share("owl", ["see"])              # the owl lends its sight to whoever is with it

    world, stats, dog = World(), Stats(), Dog()
    recorder = FlowRecorder()                       # auto-bracketing: learns on a warranted success
    feedback = []
    print("== live skill-share + LEARNING: the dog's warranted route auto-extrudes into a SOP ==\n")
    for t in range(1, 9):
        here = pw.here("dog").name
        lent = pw.shared_with("dog")               # {owl: [see]} only when co-located in forest
        d = decide(pw.chart_for("dog"), feedback)
        why, act = d.get("why", ""), d.get("do")
        step_action, warrant, passed, success = "sniff", "", True, False

        if "move" in d:
            ok, msg = pw.move("dog", d["move"]); dest = d["move"]
            line = f"move → {dest}" + ("" if ok else f" (blocked: {msg})")
            step_action, passed = f"move to {dest}", ok
            feedback.append(f"You {line}.")
        elif act == "see":
            step_action = "see (borrowed from owl)"
            if any("see" in sk for sk in lent.values()):
                world.close(f"confirmed_owl({here})", by="dog.see(borrowed from owl)")
                warrant = f"owl_present({here})"
                line = "SEE (borrowed from owl) → you see the Great Horned Owl clearly"
                feedback.append("You used the owl's lent sight and confirmed a real owl here.")
            else:
                passed = False
                line = "SEE → but no one here lends you sight; you spot nothing"
                feedback.append("You tried to see, but no owl was near to lend you its sight.")
        elif act == "bark":
            v = gate_perception(world, stats, dog, dog.manifest["bark"],
                                propose(dog, dog.manifest["bark"], t=t, place=here))
            step_action, warrant, passed, success = "bark at the owl", f"confirmed_owl({here})", v.passed, v.passed
            line = f"BARK → {v.text}"
            feedback.append(v.text if not v.passed else "You barked at a confirmed owl — good dog!")
        else:
            line = "sniff"; feedback.append("You sniffed around. Nothing ventured.")

        learned = recorder.observe(
            FlowStep("dog", step_action, warrant=warrant, place=here, passed=passed),
            success=success, name="Confirm-then-bark", domain="Canine", subdomain="Alerting",
            tags=("owl", "bark", "confirm", "proximity"),
            input_signature={"place": {"example": "forest", "required": True},
                             "lender": {"example": "owl", "required": True}})
        mark = "   ⟲ AUTO-LEARNED a SOP!" if learned else ""
        print(f"[t{t}] dog@{here:6} lent={list(lent.get('owl', []))} | {line}{mark}\n        ↳ {why}")

    print(f"\nfinal: {stats.dump()} | dog@{pw.here('dog').name}")
    if recorder.learned:
        s = recorder.learned[0]
        print(f"\n== auto-learned SOP (no manual sop_start/end): '{s.name}' — {len(s.steps)} warranted steps ==")
        for st in s.steps:
            print(f"    {st.order}. {st.action}" + (f"  ⟨{st.warrant}⟩" if st.warrant else ""))
        skills = tempfile.mkdtemp()
        p = promote_to_skill(s, skills)
        print(f"  → promoted to a skilltree node: {p}")
        print("    (now indexable by skilltree's BM25 RAG: `skilltree search <dir> \"bark owl\"`)")
    else:
        print("\n(no warranted route completed — nothing learned this run)")


if __name__ == "__main__":
    main()
