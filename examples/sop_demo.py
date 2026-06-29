"""sop_demo — learning: the dog's discovered route becomes a warranted, replayable SOP.

From the live skill-share run the dog found a route: move→see(borrowed)→bark. We record that flow
(including one SLOP step — a bark in the yard the gate rejected) and EXTRUDE a SOP. The gated
extrusion keeps only the WARRANTED steps (the slop bark is dropped). Then we search for it and
REPLAY it — soundly: against a world where the warrants still hold it replays; against a changed
world (the owl gone) it is rejected as STALE at the step whose warrant no longer holds.

Run: python3 examples/sop_demo.py   (offline, no API, no external DB)
"""
import sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World
from dogworld.sop import FlowStep, extrude, replay, SOPStore

# the dog's recorded flow (warrant = the fact the gate checked; passed = the gate's verdict)
flow = [
    FlowStep("dog", "move to the forest",      warrant="",                     place="yard",   passed=True),
    FlowStep("dog", "bark (yard, no owl)",     warrant="confirmed_owl(yard)",  place="yard",   passed=False),  # SLOP — gate rejected
    FlowStep("dog", "see (borrowed from owl)", warrant="owl_present(forest)",  place="forest", passed=True),
    FlowStep("dog", "bark at the confirmed owl", warrant="confirmed_owl(forest)", place="forest", passed=True),
]


def main() -> None:
    sop = extrude(
        "Confirm-then-bark", domain="Canine", subdomain="Alerting", flow=flow,
        input_signature={"place": {"example": "forest", "required": True},
                         "lender": {"example": "owl", "required": True}},
        tags=["owl", "bark", "confirm", "proximity"], fitness=2,
    )

    print("== extruded SOP (gated — only WARRANTED steps crystallize) ==")
    print(f"  {sop.name}  [{sop.domain}/{sop.subdomain}]  fitness={sop.fitness}  tags={sop.tags}")
    print(f"  input_signature: {list(sop.input_signature)}")
    for s in sop.steps:
        print(f"    {s.order}. {s.agent}: {s.action}" + (f"   ⟨warrant: {s.warrant}⟩" if s.warrant else ""))
    print(f"  -> {len(flow)} recorded, {len(sop.steps)} kept (the yard bark was SLOP — gate rejected → dropped)\n")

    with tempfile.TemporaryDirectory() as tmp:
        store = SOPStore(tmp)
        store.save(sop)
        hits = store.search("bark owl")
        print(f"== search 'bark owl' -> {[s.name for s in hits]} (fitness-ranked) ==\n")

        # sound replay: warrants still hold
        w_ok = World()
        w_ok.close("owl_present(forest)"); w_ok.close("confirmed_owl(forest)")
        r1 = replay(sop, w_ok)
        print(f"== replay against the SAME world: ok={r1.ok} ==")

        # the world changed — the owl is gone; the confirmation no longer holds
        w_stale = World()
        w_stale.close("owl_present(forest)")   # owl still 'present' but never re-confirmed
        r2 = replay(sop, w_stale)
        print(f"== replay against a CHANGED world: ok={r2.ok}  stale_at=step {r2.stale_at}  ({r2.reason}) ==")
        print("   -> a learned route is re-validated by the gate; you cannot replay a lie.")


if __name__ == "__main__":
    main()
