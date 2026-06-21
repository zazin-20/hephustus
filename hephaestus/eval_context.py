"""Unified evaluation context passed to every rule layer."""
from __future__ import annotations

from dataclasses import dataclass, field

from hephaestus.index import OKFContext
from hephaestus.store.trace import TraceEvent


@dataclass
class EvaluationContext:
    okf: OKFContext
    trace: list[TraceEvent] = field(default_factory=list)
    contract: dict = field(default_factory=dict)
    actor: str = ""
    scope: str = ""
