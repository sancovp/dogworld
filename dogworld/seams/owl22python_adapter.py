"""Seam → owl22python (OWL2/XML -> agent definition; the "define agents from logic" layer).

The real compiler (owl22python.py + pydantic_stack_core RenderablePiece) lives in the
a separate container demo and is NOT importable here. So this seam:
  - imports `owl22python` IF it is importable (when run inside that env), and otherwise
  - falls back to a THIN host-side reader that extracts an `AgentSpec` (state fields + types +
    functional declarations) from OWL2/XML. The fallback is deliberately minimal — it does NOT
    reimplement owl22python's class generation; it only reads the ontology's DataProperties so
    Dogworld can scaffold an agent's STATE. Methods (the verbs) are added in Python via the
    @action/@perception decorators (or, ultimately, derived from OWL ObjectProperties — future).

Returns: {"class_name": str, "fields": {name: py_type}, "functional": [pred,...]}.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

_XSD_TO_PY = {"xsd:string": str, "xsd:decimal": float, "xsd:float": float,
              "xsd:integer": int, "xsd:int": int, "xsd:boolean": bool}


def _lname(el) -> str:
    return el.tag.split("}")[-1]


def _strip(iri: str) -> str:
    return iri.lstrip("#")


def owl_to_agentspec(xml_str: str) -> dict:
    """Thin OWL2/XML -> AgentSpec reader (host fallback). See module docstring for scope."""
    # prefer the real compiler if the env has it (e.g. inside the container)
    try:  # pragma: no cover - only in the container env
        import owl22python  # type: ignore
        res = owl22python.owl22python(xml_str)
        spec = res["spec"]
        return {"class_name": spec["class_name"],
                "fields": {k: v[0] for k, v in spec["fields"].items()},
                "functional": [], "via": "owl22python"}
    except Exception:
        pass  # host fallback below

    root = ET.fromstring(xml_str)
    classes, ranges, domains = [], {}, {}
    for el in root.iter():
        ln = _lname(el)
        if ln == "Class" and el.attrib.get("IRI"):
            classes.append(_strip(el.attrib["IRI"]))
        elif ln == "DataPropertyRange":
            kids = list(el); ranges[_strip(kids[0].attrib["IRI"])] = kids[1].attrib["IRI"]
        elif ln == "DataPropertyDomain":
            kids = list(el); domains[_strip(kids[0].attrib["IRI"])] = _strip(kids[1].attrib["IRI"])
    class_name = classes[0] if classes else "Thing"
    fields = {prop: _XSD_TO_PY.get(dtype, str)
              for prop, dtype in ranges.items() if domains.get(prop) == class_name}
    return {"class_name": class_name, "fields": fields, "functional": [], "via": "host-fallback"}
