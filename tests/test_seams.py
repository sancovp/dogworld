import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World
from dogworld.seams import owl22python_adapter as owl_seam
from dogworld.seams import cave_bridge
from dogworld.seams import bigdog_persona

OWL_XML = """<?xml version="1.0"?>
<Ontology xmlns="http://www.w3.org/2002/07/owl#" ontologyIRI="http://example.org/birds">
  <Class IRI="#Owl"/>
  <DataProperty IRI="#species"/><DataProperty IRI="#wingspan_cm"/>
  <DataPropertyDomain><DataProperty IRI="#species"/><Class IRI="#Owl"/></DataPropertyDomain>
  <DataPropertyRange><DataProperty IRI="#species"/><Datatype IRI="xsd:string"/></DataPropertyRange>
  <DataPropertyDomain><DataProperty IRI="#wingspan_cm"/><Class IRI="#Owl"/></DataPropertyDomain>
  <DataPropertyRange><DataProperty IRI="#wingspan_cm"/><Datatype IRI="xsd:decimal"/></DataPropertyRange>
</Ontology>"""


def test_owl_adapter_host_fallback_reads_fields():
    spec = owl_seam.owl_to_agentspec(OWL_XML)
    assert spec["class_name"] == "Owl"
    assert spec["fields"]["species"] is str
    assert spec["fields"]["wingspan_cm"] is float


def test_cave_make_phi_uses_world_warrant():
    w = World(); w.close("owl_hooted@1")
    phi = cave_bridge.make_phi(w, warrant_of=lambda msg: msg["warrant"])
    assert phi({"warrant": "owl_hooted@1"}) is True
    assert phi({"warrant": "owl_hooted@2"}) is False


def test_bigdog_persona_seam_if_available():
    """If the prompt-engineering skill is installed, the persona seam must produce a prompt and
    the per-token gate must lint. If not installed, the seam reports unavailable (no crash)."""
    if not bigdog_persona.available():
        return  # seam absent in this env; core is unaffected
    prompt = bigdog_persona.build_arbiter_persona(
        name="Arbiter", role="an urge-arbitrating agent",
        foci=["Sense", "Dog", "Bitch", "BigDog", "Commit"], held="Actualize",
        decision="which urge to act on", rules=["Grade every correspondence."])
    assert isinstance(prompt, str) and len(prompt) > 0
    verdict = bigdog_persona.lint_reasoning(
        "[Sense] ⇒ [Dog] ⇒ |Actualize|",
        exemplars=["[Sense] ⇒ [Dog] ⇒ [Bitch] ⇒ |Actualize|"])
    assert isinstance(verdict, dict) and "ok" in verdict
