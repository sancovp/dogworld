"""owl22python adapter — delegates to the REAL owl22python now VENDORED in dogworld/template/.

(Was a stub that only read DataProperties → a dict. The actual compiler is now in the repo:
`dogworld.template.owl22python` compiles OWL2/XML → a `RenderablePiece` class via the template
system. Build agents on it with `dogworld.template_agent.TemplateAgent`.)
"""
from __future__ import annotations


def owl_to_agentspec(xml_str: str) -> dict:
    """OWL2/XML → {class_name, fields:{name:py_type}} using the vendored owl22python compiler."""
    from dogworld.template.owl22python import owl22python
    res = owl22python(xml_str)
    spec = res["spec"]
    return {"class_name": spec["class_name"],
            "fields": {k: v[0] for k, v in spec["fields"].items()},
            "ModelClass": res["ModelClass"], "via": "owl22python (vendored)"}
