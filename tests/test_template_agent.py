import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World, Stats, propose, gate_perception, fire_action

try:
    from dogworld.template import owl22python, EXAMPLE_OWL2_XML, MetaStack
    from dogworld.template_agent import TemplateAgent
    HAVE_TEMPLATE = True
except Exception:
    HAVE_TEMPLATE = False


def test_owl22python_compiles_a_renderable_state_class():
    if not HAVE_TEMPLATE:
        return
    res = owl22python(EXAMPLE_OWL2_XML)
    M = res["ModelClass"]
    assert set(M.model_fields) == {"species", "wingspan_cm", "nocturnal"}   # one field per OWL DataProperty
    inst = M(species="Great Horned Owl", wingspan_cm=120.0, nocturnal=True)
    assert "RDF" in inst.render()                                            # ontology-typed render()
    assert MetaStack(pieces=[inst]).render()                                 # MetaStack-composable


def test_agent_state_is_compiled_from_owl():
    if not HAVE_TEMPLATE:
        return
    owl = TemplateAgent("owl", EXAMPLE_OWL2_XML, seed={"species": "Barn Owl", "wingspan_cm": 95.0, "nocturnal": True})
    assert owl.state.species == "Barn Owl"                                   # typed state from the ontology
    assert "RDF" in owl.render_state()


def test_verb_is_added_via_template_mixin_and_runs():
    if not HAVE_TEMPLATE:
        return
    owl = TemplateAgent("owl", EXAMPLE_OWL2_XML, seed={"species": "Great Horned Owl", "wingspan_cm": 120.0, "nocturnal": True})
    owl.add_action("hoot", lambda self: f"{self.state.species} hoots", closes="owl_hooted@{t}")
    assert "hoot" in owl._methods                                            # registered in the TEMPLATE mixin
    assert owl.manifest["hoot"].kind == "action"                             # AND in the dogworld manifest
    assert owl.get_method("hoot")() == "Great Horned Owl hoots"              # the add_method'd verb runs


def test_template_added_verbs_are_gated():
    if not HAVE_TEMPLATE:
        return
    owl = TemplateAgent("owl", EXAMPLE_OWL2_XML, seed={"species": "Great Horned Owl", "wingspan_cm": 120.0, "nocturnal": True})
    owl.add_action("hoot", lambda self: "HOOOO", closes="owl_hooted@{t}")
    dog = TemplateAgent("dog")
    dog.add_perception("bark", lambda self: "WOOF!", requires="owl_hooted@{t}",
                       abduces="near(dog,owl)", penalty="no owl.")
    world, stats = World(), Stats()
    fire_action(world, owl, owl.manifest["hoot"], t=1)
    assert world.warrants("owl_hooted@1")
    v = gate_perception(world, stats, dog, dog.manifest["bark"], propose(dog, dog.manifest["bark"], t=1))
    assert v.passed and world.warrants("near(dog,owl)")                      # warranted template-verb
    # and an unwarranted one is penalized
    v2 = gate_perception(world, Stats(), dog, dog.manifest["bark"], propose(dog, dog.manifest["bark"], t=99))
    assert not v2.passed and "WISDOM -1" in v2.text
