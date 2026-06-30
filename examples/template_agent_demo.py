"""template_agent_demo — an agent whose STATE is owl22python-compiled and VERBS are add_method'd.

This is the foundation the engine tests: the owl's state (species/wingspan/nocturnal) is COMPILED
from an OWL2 ontology by owl22python (a RenderablePiece); its `hoot` verb is added dynamically via
the template mixin's add_method; the dog's `bark` likewise. Then the dogworld gate runs over those
template-defined verbs — a warranted bark passes, the owl's typed state renders ontology-typed.

Run: pip install dogworld[template]; python3 examples/template_agent_demo.py   (offline, no API)
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World, Stats, propose, gate_perception, fire_action
from dogworld.template import EXAMPLE_OWL2_XML
from dogworld.template_agent import TemplateAgent


def main():
    # STATE compiled from OWL (owl22python); VERB added via the template mixin (add_method)
    owl = TemplateAgent("owl", EXAMPLE_OWL2_XML,
                        seed={"species": "Great Horned Owl", "wingspan_cm": 120.0, "nocturnal": True})
    owl.add_action("hoot", lambda self: f"{self.state.species} hoots: HOOOO-HOOOO",
                   closes="owl_hooted@{t}")

    dog = TemplateAgent("dog")
    dog.add_perception("bark", lambda self: "WOOF! (a confirmed owl)",
                       requires="owl_hooted@{t}", abduces="near(dog,owl)",
                       penalty="You thought you heard an owl. In fact, there was not one when you looked.")

    print("== the owl agent: STATE compiled from OWL by owl22python ==")
    print(f"   typed fields (from OWL DataProperties): {list(owl.StateClass.model_fields)}")
    print(f"   ontology-typed render(): {owl.render_state()[:80].strip()} ...")
    print(f"   verb 'hoot' was added via TemplateMethodMixin.add_method: {owl.get_method('hoot') is not None}")

    world, stats = World(), Stats()
    print("\n== run the template-defined verbs through the dogworld gate ==")
    res = fire_action(world, owl, owl.manifest["hoot"], t=1)        # owl hoots -> closes owl_hooted@1
    print(f"   owl.hoot() -> {res}  | closed owl_hooted@1: {world.warrants('owl_hooted@1')}")

    v = gate_perception(world, stats, dog, dog.manifest["bark"],
                        propose(dog, dog.manifest["bark"], t=1))    # gated bark
    print(f"   dog.bark (gated) -> {v.text}")
    print(f"   warranted: {v.passed} | near(dog,owl) abduced: {world.warrants('near(dog,owl)')}")
    print("\n   -> STATE from owl22python, VERBS from add_method, ADJUDICATED by the dogworld gate.")


if __name__ == "__main__":
    main()
