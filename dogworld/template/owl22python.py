#!/usr/bin/env python3
"""
owl22python demo
================

Demonstrates THREE things, in order:

  PART 3 (combine example): template_mixin (class-level templating) + MetaStack
          (typed RenderablePiece composition) used together — a class whose
          *fields* are MetaStack RenderablePieces, generated at the class level.

  PART 4 (owl22python): OWL2 XML  ->  Python (a RenderablePiece class per OWL
          class, one field per OWL restriction)  ->  instantiate with data  ->
          render/serialize back to an ontology-typed result (RDF/XML triples +
          OWL individual assertions). A closed loop.

template_mixin source : dogworld/template/template_mixins.py (TemplateAttributeMixin / TemplateMethodMixin)
                        + dogworld/template/templated_class.py (the class-level TemplatedClass that USES them)
MetaStack source      : dogworld/template/pydantic_stack.py (RenderablePiece, MetaStack)

Both the mixins and MetaStack are imported/vendored faithfully; nothing is faked.
"""

import sys
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Type, Callable

from pydantic import BaseModel, Field, create_model

# ---- RenderablePiece / MetaStack (vendored from pydantic_stack_core) -------
from .pydantic_stack import RenderablePiece, MetaStack

# ---- the two template mixins (vendored from the legacy-heaven progenitor) ---
from .template_mixins import TemplateAttributeMixin, TemplateMethodMixin


# ===========================================================================
# PART 3 — COMBINE EXAMPLE
# A class TEMPLATED via the mixins, whose FIELDS are MetaStack RenderablePieces.
# ===========================================================================

class Heading(RenderablePiece):
    """A MetaStack piece: a markdown heading."""
    text: str
    level: int = 1
    def render(self) -> str:
        return f"{'#' * self.level} {self.text}"

class Para(RenderablePiece):
    """A MetaStack piece: a paragraph."""
    body: str
    def render(self) -> str:
        return self.body


class TemplatedDocClass(BaseModel, TemplateAttributeMixin, TemplateMethodMixin):
    """
    A class TEMPLATED at the class level (via the legacy template mixins),
    whose state is a MetaStack of RenderablePieces. The render method is
    ADDED dynamically via the mixin (class-level metaprogramming): the method
    is not hand-written on the class, it is composed in.
    """
    stack: MetaStack = Field(default_factory=MetaStack)
    class Config:
        arbitrary_types_allowed = True
        extra = "allow"


def part3_combine_example() -> str:
    out = []
    out.append("=== PART 3: template_mixin + MetaStack combine example ===\n")

    doc = TemplatedDocClass(stack=MetaStack(separator="\n\n"))

    # MetaStack composition: typed RenderablePiece fields.
    doc.stack.add_piece(Heading(text="Owls", level=1))
    doc.stack.add_piece(Para(body="An owl is a bird of prey."))
    doc.stack.add_piece(Heading(text="Habitat", level=2))
    doc.stack.add_piece(Para(body="Owls live in forests."))

    # template_mixin: ADD A METHOD to the class instance dynamically (class-level
    # templating of behavior — the method did not exist on the class).
    doc.add_method(
        "render_doc",
        lambda self: self.stack.render(),
        description="Render the embedded MetaStack",
        add_to_sequence=True,
    )
    # template_mixin: ADD A COMPUTED ATTRIBUTE (derived field) dynamically.
    doc.add_attribute(
        "piece_count",
        lambda self: len(self.stack.pieces),
        computed=True,
        dependencies=["stack"],
        description="number of pieces in the embedded MetaStack",
    )

    rendered = doc.get_method("render_doc")()
    out.append("templated method render_doc() output:\n" + rendered)
    out.append(f"\ncomputed attribute piece_count = {doc.get_attribute('piece_count')}")
    out.append("\n--> CLASS-LEVEL templating (mixin adds method+attr) wrapping "
               "TYPED MetaStack piece composition. Both combined.\n")
    return "\n".join(out)


# ===========================================================================
# PART 4 — owl22python : OWL2 XML -> Python -> ontology-typed result (roundtrip)
# ===========================================================================

# A tiny hand-written OWL2 ontology in OWL/XML syntax: one class `Owl` with two
# data restrictions (wingspan_cm: a decimal, nocturnal: a boolean) and a
# species name string. (OWL2 DataHasValue/DataSomeValuesFrom-style restrictions
# distilled to a class with typed data properties, which is what a Pydantic
# class models.)
EXAMPLE_OWL2_XML = """<?xml version="1.0"?>
<Ontology xmlns="http://www.w3.org/2002/07/owl#"
          ontologyIRI="http://example.org/birds">
  <Class IRI="#Owl"/>
  <DataProperty IRI="#species"/>
  <DataProperty IRI="#wingspan_cm"/>
  <DataProperty IRI="#nocturnal"/>

  <DataPropertyDomain><DataProperty IRI="#species"/><Class IRI="#Owl"/></DataPropertyDomain>
  <DataPropertyRange><DataProperty IRI="#species"/><Datatype IRI="xsd:string"/></DataPropertyRange>

  <DataPropertyDomain><DataProperty IRI="#wingspan_cm"/><Class IRI="#Owl"/></DataPropertyDomain>
  <DataPropertyRange><DataProperty IRI="#wingspan_cm"/><Datatype IRI="xsd:decimal"/></DataPropertyRange>

  <DataPropertyDomain><DataProperty IRI="#nocturnal"/><Class IRI="#Owl"/></DataPropertyDomain>
  <DataPropertyRange><DataProperty IRI="#nocturnal"/><Datatype IRI="xsd:boolean"/></DataPropertyRange>
</Ontology>
"""

_XSD_TO_PY: Dict[str, Type] = {
    "xsd:string": str,
    "xsd:decimal": float,
    "xsd:float": float,
    "xsd:integer": int,
    "xsd:int": int,
    "xsd:boolean": bool,
}
_PY_TO_XSD = {str: "xsd:string", float: "xsd:decimal", int: "xsd:integer", bool: "xsd:boolean"}


def _strip(iri: str) -> str:
    return iri.lstrip("#")


def _parse_owl2(xml_str: str) -> Dict[str, Any]:
    """Parse OWL2/XML -> {class_name, fields:{name:(py_type, xsd)}, iri}."""
    # tolerant parse: ElementTree keeps the default-namespace, so match by localname
    root = ET.fromstring(xml_str)
    def lname(el): return el.tag.split("}")[-1]

    onto_iri = root.attrib.get("ontologyIRI", "http://example.org/onto")
    classes = []
    ranges: Dict[str, str] = {}
    domains: Dict[str, str] = {}

    for el in root.iter():
        ln = lname(el)
        if ln == "Class" and el.attrib.get("IRI"):
            classes.append(_strip(el.attrib["IRI"]))
        elif ln == "DataPropertyRange":
            kids = list(el)
            prop = _strip(kids[0].attrib["IRI"])
            dtype = kids[1].attrib["IRI"]
            ranges[prop] = dtype
        elif ln == "DataPropertyDomain":
            kids = list(el)
            prop = _strip(kids[0].attrib["IRI"])
            domains[prop] = _strip(kids[1].attrib["IRI"])

    # take the first declared class as the modeled class
    class_name = classes[0] if classes else "Thing"
    fields: Dict[str, tuple] = {}
    for prop, dtype in ranges.items():
        if domains.get(prop) == class_name:
            fields[prop] = (_XSD_TO_PY.get(dtype, str), dtype)
    return {"class_name": class_name, "fields": fields, "iri": onto_iri}


def owl22python(xml_str: str) -> Dict[str, Any]:
    """
    THE DELIVERABLE.

    OWL2/XML  ->  GENERATE a Pydantic/RenderablePiece class (template_mixin +
    MetaStack)  ->  return {ModelClass, source, roundtrip(data)->ontology-typed-result}.

    The generated class:
      * is a RenderablePiece subclass (MetaStack-composable),
      * one Pydantic field per OWL data restriction,
      * its render() emits an ONTOLOGY-TYPED result (OWL individual + RDF triples).
    """
    spec = _parse_owl2(xml_str)
    cname, fields, onto_iri = spec["class_name"], spec["fields"], spec["iri"]

    # --- (a) GENERATE the class via create_model (pydantic class-level metaprogramming),
    #         basing it on RenderablePiece so it is MetaStack-composable.
    pyfields = {fname: (ftype, Field(..., description=f"OWL DataProperty {fname} ({xsd})"))
                for fname, (ftype, xsd) in fields.items()}

    def _render(self) -> str:
        """render() emits the ontology-typed result: OWL2 individual + triples."""
        return _to_ontology_typed(self, cname, fields, onto_iri)

    Model = create_model(
        cname,
        __base__=RenderablePiece,
        __validators__={},
        **pyfields,
    )
    # attach the ontology-typed renderer (class-level) and clear the abstract
    # marker inherited from RenderablePiece.render (@abstractmethod) so the
    # generated class is concrete/instantiable.
    Model.render = _render
    Model.__abstractmethods__ = frozenset()

    # --- (b) generate readable SOURCE for the class (the templated text), using
    #         the legacy template_mixin TemplatedClass style: a per-field template.
    src = _generate_source(cname, fields, onto_iri)

    return {"ModelClass": Model, "source": src, "spec": spec}


def _generate_source(cname: str, fields: Dict[str, tuple], onto_iri: str) -> str:
    """Emit human-readable generated Python source (the template projection)."""
    lines = [
        "from pydantic_stack_core.core import RenderablePiece",
        "from pydantic import Field",
        "",
        f"class {cname}(RenderablePiece):",
        f'    """Generated from OWL2 class <{onto_iri}#{cname}>."""',
    ]
    for fname, (ftype, xsd) in fields.items():
        lines.append(f'    {fname}: {ftype.__name__} = Field(..., description="OWL DataProperty {fname} ({xsd})")')
    lines += [
        "",
        "    def render(self) -> str:",
        '        """Emit OWL2 individual + RDF/XML triples (ontology-typed result)."""',
        "        ...  # -> RDF/XML asserting an Owl individual with each data property",
    ]
    return "\n".join(lines)


def _to_ontology_typed(inst, cname: str, fields: Dict[str, tuple], onto_iri: str) -> str:
    """Python instance -> ontology-typed result (OWL2/RDF individual + triples)."""
    indiv = f"{cname.lower()}_individual"
    base = onto_iri.rstrip("/#")
    triples = [(f"{base}#{indiv}", "rdf:type", f"{base}#{cname}")]
    prop_xml = []
    for fname, (ftype, xsd) in fields.items():
        val = getattr(inst, fname)
        # serialize python value back into a typed literal
        if ftype is bool:
            lit = "true" if val else "false"
        else:
            lit = str(val)
        triples.append((f"{base}#{indiv}", f"{base}#{fname}", f'"{lit}"^^{xsd}'))
        prop_xml.append(f'    <{fname} rdf:datatype="{xsd}">{lit}</{fname}>')

    rdfxml = (
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
        f'  <{cname} rdf:about="{base}#{indiv}">\n'
        + "\n".join(prop_xml) + "\n"
        f'  </{cname}>\n'
        '</rdf:RDF>'
    )
    triple_lines = "\n".join(f"  {s}  {p}  {o}" for (s, p, o) in triples)
    return f"OWL INDIVIDUAL (RDF/XML):\n{rdfxml}\n\nTRIPLES:\n{triple_lines}"


def part4_owl22python_roundtrip() -> str:
    out = ["=== PART 4: owl22python  OWL2 -> Python -> ontology-typed result ===\n"]

    out.append(">>> INPUT OWL2 XML:")
    out.append(EXAMPLE_OWL2_XML.strip())

    result = owl22python(EXAMPLE_OWL2_XML)
    Model = result["ModelClass"]

    out.append("\n>>> GENERATED PYTHON CLASS (source projection):")
    out.append(result["source"])

    out.append("\n>>> GENERATED CLASS (live): fields = "
               + str({k: v.annotation.__name__ for k, v in Model.model_fields.items()}))

    # instantiate with data
    inst = Model(species="Great Horned Owl", wingspan_cm=120.0, nocturnal=True)
    out.append("\n>>> INSTANTIATED with data: "
               + str(inst.model_dump()))

    # ROUNDTRIP: render back to ontology-typed result
    out.append("\n>>> ROUNDTRIP (Python instance -> ontology-typed result):")
    out.append(inst.render())

    # prove MetaStack-composability of the GENERATED class (closes loop to Part 3)
    stack = MetaStack(pieces=[inst], separator="\n")
    out.append("\n>>> The generated class is MetaStack-composable "
               "(MetaStack.render() over the generated owl class):")
    out.append(stack.render()[:200] + " ...[truncated]")

    return "\n".join(out)


if __name__ == "__main__":
    print(part3_combine_example())
    print()
    print(part4_owl22python_roundtrip())
