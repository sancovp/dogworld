import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World, Stats
from dogworld.heaven_agent import available, gated_tool


def _dog():
    from dogworld.template_agent import TemplateAgent
    dog = TemplateAgent("dog")
    dog.add_perception("bark", lambda self: "WOOF!", requires="owl_hooted@{t}",
                       abduces="near(dog,owl)", penalty="no owl here.")
    return dog


def test_verb_wraps_as_a_heaven_tool():
    if not available():
        return                                  # heaven_base only in the onionmorph venv
    from heaven_base.baseheaventool import BaseHeavenTool
    dog, world, stats, clock = _dog(), World(), Stats(), {"t": 1}
    Tool = gated_tool(dog, dog.manifest["bark"], world, stats, clock)
    assert issubclass(Tool, BaseHeavenTool) and Tool.name == "bark"


def test_gated_tool_call_is_adjudicated_by_the_world():
    if not available():
        return
    dog, world, stats, clock = _dog(), World(), Stats(), {"t": 1}
    Tool = gated_tool(dog, dog.manifest["bark"], world, stats, clock)
    world.close("owl_hooted@1")
    assert "WOOF" in Tool.func()                # warranted -> the gate passes through the tool
    assert world.warrants("near(dog,owl)")
    clock["t"] = 2                              # no owl hooted at t=2
    assert "WISDOM -1" in Tool.func()          # unwarranted -> the gate penalizes through the tool
    assert clock["_log"]                        # the tool recorded its real verdicts
