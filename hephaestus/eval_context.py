"""Unified evaluation context passed to every rule layer.

REUSABLE — the object every check reads (okf documents, trace, contract, actor,
scope). Provider-/rule-agnostic; user-authored gates read the same context.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from hephaestus.index import OKFContext
from hephaestus.store.trace import TraceEvent
from hephaestus.store.threads import Turn


@dataclass
class EvaluationContext:
    okf: OKFContext
    turns: list[Turn] = field(default_factory=list)
    trace: list[TraceEvent] = field(default_factory=list)
    contract: dict = field(default_factory=dict)
    actor: str = ""
    scope: str = ""
