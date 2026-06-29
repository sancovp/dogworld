"""Agent — a self-describing entity. The class REFLECTS its own methods into a manifest.

Methods are tagged with `@action` or `@perception`. The agent introspects itself (no
hand-registration) and exposes each tagged method as a manifest entry carrying its kind, its
RngSpec (the soft prior), and — for perceptions — its abductive contract (`requires` warrant,
`abduces` fact, `penalty` re-narration). This is "the class should just reflect itself": the
tool-surface and the injectable urges both fall out of the class's own methods.

Templates may reference `{self}` (the agent's name), `{t}` (current tick), and any kwargs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from .rng import RngSpec


# ---- decorators: tag methods so the class can reflect them ----------------------
def action(*, rng: Optional[RngSpec] = None, closes: Optional[str] = None) -> Callable:
    """An action the agent DOES; on firing it may close a world fact (template `closes`)."""
    def deco(fn: Callable) -> Callable:
        fn._dw_meta = {"kind": "action", "rng": rng or RngSpec(), "closes": closes}
        return fn
    return deco


def perception(*, requires: str, abduces: str, penalty: str, urge: Optional[str] = None,
               rng: Optional[RngSpec] = None) -> Callable:
    """A perception (effect). On firing it ABDUCES `abduces`, warranted by `requires`.

    `urge` is the SUBJECTIVE percept injected into the arbiter's context (the soft prior as felt
    experience), e.g. 'You think you heard an owl hoot nearby (felt-strength {p}).' The agent does
    NOT see whether it's real — it decides whether to TRUST the percept. The gate checks reality:
    if the world does not warrant `requires` (or `abduces` is inconsistent), it applies option B —
    re-narrate `penalty` and dock WISDOM. `penalty` e.g. 'You thought you heard an owl. In fact,
    there was not one when you looked.'
    """
    def deco(fn: Callable) -> Callable:
        fn._dw_meta = {"kind": "perception", "rng": rng or RngSpec(), "urge": urge,
                       "requires": requires, "abduces": abduces, "penalty": penalty}
        return fn
    return deco


@dataclass
class MethodInfo:
    name: str
    kind: str                 # "action" | "perception"
    fn: Callable
    rng: RngSpec
    closes: Optional[str] = None
    requires: Optional[str] = None
    abduces: Optional[str] = None
    penalty: Optional[str] = None
    urge: Optional[str] = None

    def render_urge(self) -> str:
        """The subjective percept (if declared) else the generic strength line."""
        if self.urge:
            return self.urge.format(p=f"{self.rng.p:.2f}")
        return self.rng.render_urge(self.name)


class Agent:
    name: str = "agent"

    def __init__(self, name: Optional[str] = None) -> None:
        if name:
            self.name = name
        self._manifest: dict[str, MethodInfo] = self._reflect()

    # ---- the reflection: methods -> manifest (tools + urges), no hand-registration ----
    def _reflect(self) -> dict[str, MethodInfo]:
        # collect decorated NAMES from the class MRO (avoids triggering @property like manifest)
        names: list[str] = []
        for klass in type(self).__mro__:
            for attr, val in vars(klass).items():
                if callable(val) and hasattr(val, "_dw_meta") and attr not in names:
                    names.append(attr)
        manifest: dict[str, MethodInfo] = {}
        for attr in names:
            fn = getattr(self, attr)            # bound method (safe: attr is a known method)
            meta = fn._dw_meta
            # each agent instance gets its OWN RngSpec copy (so set_rng_* is per-instance)
            rng = RngSpec(method=meta["rng"].method, values=dict(meta["rng"].values))
            manifest[attr] = MethodInfo(
                name=attr, kind=meta["kind"], fn=fn, rng=rng,
                closes=meta.get("closes"), requires=meta.get("requires"),
                abduces=meta.get("abduces"), penalty=meta.get("penalty"),
                urge=meta.get("urge"),
            )
        return manifest

    @property
    def manifest(self) -> dict[str, MethodInfo]:
        return self._manifest

    def actions(self) -> list[MethodInfo]:
        return [m for m in self._manifest.values() if m.kind == "action"]

    def perceptions(self) -> list[MethodInfo]:
        return [m for m in self._manifest.values() if m.kind == "perception"]

    # ---- the RNG setters (the soft prior, set as data) ----------------------------
    def set_rng_method(self, method_name: str, policy: str) -> None:
        self._manifest[method_name].rng.set_method(policy)

    def set_rng_values(self, method_name: str, **values: float) -> None:
        self._manifest[method_name].rng.set_values(**values)

    # ---- template filling for warrant/abduces/closes ------------------------------
    def fill(self, template: str, *, t: int, **kwargs) -> str:
        return template.format(self=self.name, t=t, **kwargs)

    def render_urges(self) -> str:
        """Concatenate all method urges (the soft priors injected as prompt)."""
        return "\n".join(m.render_urge() for m in self._manifest.values())
