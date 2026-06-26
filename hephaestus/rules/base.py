"""Rule interface. Every built-in or custom rule implements `check`.

REUSABLE — the check interface user-authored rules (artifact predicates,
behavioral constraints) implement. The hardcoded structural rules are gone; this
contract is what the generic gate-runner executes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from hephaestus.core import Severity, ViolationResult

if TYPE_CHECKING:
    from hephaestus.eval_context import EvaluationContext


class HephaestusRule(ABC):
    id: str
    name: str
    layer: str = "structural"
    trigger: str = "on_change"
    scope: str = "workspace"
    severity: Severity = Severity.ERROR
    roles_involved: list[str] = []
    auto_fixable: bool = False
    fix_hint: str = ""

    @abstractmethod
    def check(self, ctx: "EvaluationContext") -> ViolationResult:
        ...
