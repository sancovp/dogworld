"""template_agent — a dogworld Agent built ON the TEMPLATE SYSTEM (the foundation this engine tests).

The agent's STATE is compiled from an OWL2 ontology by `owl22python` (one typed field per OWL
DataProperty → a `RenderablePiece`). The agent's VERBS are added dynamically via the template mixin
(`TemplateMethodMixin.add_method`) — GENERATED from a spec, not hand-decorated — and each verb
carries the dogworld gate metadata (requires/abduces/penalty for a perception, closes for an
action). So every template-added verb is gated by the warrant/WISDOM/catalysis machinery exactly
like a hand-written `@perception`/`@action`. owl22python + template_mixins ARE the foundation; the
gate runs on top.
"""
from __future__ import annotations

from typing import Callable, Optional

from .agent import Agent, MethodInfo
from .rng import RngSpec
from .template import owl22python
from .template.template_mixins import TemplateMethodMixin


class TemplateAgent(Agent, TemplateMethodMixin):
    """STATE from owl22python (OWL → RenderablePiece); VERBS from `add_method`; gated by dogworld."""

    def __init__(self, name: str, owl_xml: Optional[str] = None, seed: Optional[dict] = None) -> None:
        self.name = name
        self._methods: dict = {}            # TemplateMethodMixin state
        self._template_sequence: list = []
        self._manifest: dict[str, MethodInfo] = {}   # dogworld manifest (built by add_* below)
        self.StateClass = None
        self.spec = None
        self.state = None
        if owl_xml is not None:
            res = owl22python(owl_xml)       # COMPILE the agent's state FROM logic (the real owl22python)
            self.StateClass = res["ModelClass"]
            self.spec = res["spec"]
            self.state = self.StateClass(**(seed or {}))

    # ---- VERBS added via the TEMPLATE SYSTEM (add_method), registered as GATED dogworld methods ----
    def add_action(self, name: str, fn: Callable, *, closes: str = "",
                   rng: Optional[RngSpec] = None, urge: Optional[str] = None) -> "TemplateAgent":
        self.add_method(name, fn)            # template mixin: dynamically add the method
        self._manifest[name] = MethodInfo(name=name, kind="action", fn=self.get_method(name),
                                          rng=rng or RngSpec(), closes=closes or None, urge=urge)
        return self

    def add_perception(self, name: str, fn: Callable, *, requires: str, abduces: str, penalty: str,
                       rng: Optional[RngSpec] = None, urge: Optional[str] = None) -> "TemplateAgent":
        self.add_method(name, fn)            # template mixin: dynamically add the method
        self._manifest[name] = MethodInfo(name=name, kind="perception", fn=self.get_method(name),
                                          rng=rng or RngSpec(), requires=requires, abduces=abduces,
                                          penalty=penalty, urge=urge)
        return self

    def render_state(self) -> str:
        """The OWL-typed state rendered to its ontology-typed result (owl22python's render())."""
        return self.state.render() if self.state is not None else ""
