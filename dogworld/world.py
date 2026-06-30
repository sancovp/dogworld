"""World — the constraint store of CLOSED facts (the only certifier).

Facts are predicate strings: `pred(arg1,arg2,...)`, e.g. `near(dog,owl)`, `owl_hooted@3`.
Negation convention: a leading `!` (`!near(dog,owl)`). Contradiction is detected two ways:

  1. negation     — F and !F cannot both be closed.
  2. functional   — a predicate declared functional in its first k "subject" args may hold
                    only ONE value-tuple per subject (e.g. `at(dog, _)`: the dog is at one
                    place). Closing `at(dog,field)` when `at(dog,barn)` is closed = contradiction.

This is the decidable fragment the gate is SOUND over: `warrants` = exact membership,
`consistent_with` = negation + functional checks. No external DB; in-memory, with optional sqlite
snapshotting for persistence (local file only).
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field

_PRED_RE = re.compile(r"^(?P<neg>!?)(?P<pred>[A-Za-z_][\w]*)(?:\((?P<args>.*)\))?(?P<tail>@\w+)?$")


@dataclass(frozen=True)
class Fact:
    raw: str
    neg: bool
    pred: str
    args: tuple[str, ...]
    tail: str  # e.g. "@3" tick suffix, kept as part of identity

    @staticmethod
    def parse(s: str) -> "Fact":
        s = s.strip()
        m = _PRED_RE.match(s)
        if not m:
            raise ValueError(f"unparseable fact: {s!r}")
        args_s = m.group("args")
        args = tuple(a.strip() for a in args_s.split(",")) if args_s else ()
        return Fact(raw=s, neg=bool(m.group("neg")), pred=m.group("pred"),
                    args=args, tail=m.group("tail") or "")

    @property
    def positive(self) -> str:
        """The raw fact without its leading negation."""
        return self.raw[1:] if self.neg else self.raw


class World:
    def __init__(self) -> None:
        self.facts: set[str] = set()
        self.events: list[str] = []
        # functional[pred] = k : the first k args are the subject; the rest must be unique per subject
        self._functional: dict[str, int] = {}
        # catalysis bookkeeping (the enablement DAG): which closed fact ENABLED which other
        self.enables: dict[str, set[str]] = {}      # f -> {g : f enabled g}   (catalysis edges)
        self.enabler_of: dict[str, set[str]] = {}   # g -> {f : f enabled g}
        self.food: set[str] = set()                 # facts closed spontaneously (by actions = the food set)
        self.closed_by: dict[str, str] = {}         # fact -> agent.method that closed it (for fitness)

    # ---- schema ----------------------------------------------------------------
    def declare_functional(self, pred: str, subject_arity: int = 1) -> None:
        """Declare `pred` functional: one value-tuple per subject (the first `subject_arity` args)."""
        self._functional[pred] = subject_arity

    # ---- the consistency check (the |= over the decidable fragment) -------------
    def consistent_with(self, fact: str) -> tuple[bool, str]:
        """Return (ok, reason). ok=False means closing `fact` would contradict closed facts."""
        f = Fact.parse(fact)
        # 1. negation conflict
        if f.neg:
            if f.positive in self.facts:
                return False, f"negation conflict: {f.positive!r} is already closed"
        else:
            if ("!" + f.raw) in self.facts:
                return False, f"negation conflict: {'!' + f.raw!r} is already closed"
        # 2. functional conflict
        k = self._functional.get(f.pred)
        if k is not None and not f.neg:
            subj = f.args[:k]
            for other in self.facts:
                of = Fact.parse(other)
                if of.neg or of.pred != f.pred or of.tail != f.tail:
                    continue
                if of.args[:k] == subj and of.args != f.args:
                    return False, (f"functional conflict on {f.pred}({','.join(subj)}): "
                                   f"{other!r} already closed, cannot also close {fact!r}")
        return True, "ok"

    # ---- closure (reify on warrant) --------------------------------------------
    def close(self, fact: str, *, note: str = "", enablers: tuple[str, ...] = (),
              food: bool = False, by: str = "") -> tuple[bool, str]:
        """Close a fact iff consistent. Returns (closed, reason).

        `enablers` = the already-closed facts that warranted this one (the catalysis edges
        f -> fact). `food=True` marks a spontaneous close (by an action) = the food set that
        grounds the autocatalytic set. `by` = the agent.method that closed it (for fitness).
        """
        ok, reason = self.consistent_with(fact)
        if not ok:
            self.events.append(f"REJECT close({fact}) :: {reason}")
            return False, reason
        if fact not in self.facts:
            self.facts.add(fact)
            self.events.append(f"close({fact})" + (f" :: {note}" if note else ""))
            if food:
                self.food.add(fact)
            if by:
                self.closed_by[fact] = by
            for e in enablers:
                self.enables.setdefault(e, set()).add(fact)
                self.enabler_of.setdefault(fact, set()).add(e)
        return True, "ok"

    def warrants(self, fact: str) -> bool:
        """Does the world KNOW this fact (Mode-B 'when you looked')? Exact membership."""
        return fact in self.facts

    def copy(self) -> "World":
        """A deep-enough copy (facts + catalysis bookkeeping) — for non-mutating diagnosis/repair."""
        w = World()
        w.facts = set(self.facts)
        w.events = list(self.events)
        w._functional = dict(self._functional)
        w.enables = {k: set(v) for k, v in self.enables.items()}
        w.enabler_of = {k: set(v) for k, v in self.enabler_of.items()}
        w.food = set(self.food)
        w.closed_by = dict(self.closed_by)
        return w

    def log(self, msg: str) -> None:
        self.events.append(msg)

    def dump(self) -> str:
        facts = ", ".join(sorted(self.facts)) or "(none)"
        return f"WORLD facts: {facts}\n  trace:\n    " + "\n    ".join(self.events)

    # ---- optional local sqlite snapshot (persistence; local file only) ----------------
    def snapshot_sqlite(self, path: str) -> None:
        con = sqlite3.connect(path)
        con.execute("CREATE TABLE IF NOT EXISTS facts(fact TEXT PRIMARY KEY)")
        con.execute("CREATE TABLE IF NOT EXISTS events(i INTEGER PRIMARY KEY, msg TEXT)")
        con.execute("DELETE FROM facts"); con.execute("DELETE FROM events")
        con.executemany("INSERT OR IGNORE INTO facts VALUES(?)", [(f,) for f in sorted(self.facts)])
        con.executemany("INSERT INTO events(msg) VALUES(?)", [(e,) for e in self.events])
        con.commit(); con.close()
