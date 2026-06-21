"""Rule interface. Every built-in or custom rule implements `check`."""
from __future__ import annotations

from abc import ABC, abstractmethod

from hephaestus.core import Severity, ViolationResult
from hephaestus.index import OKFContext


class HephaestusRule(ABC):
    id: str
    name: str
    layer: str = "structural"
    severity: Severity = Severity.ERROR
    roles_involved: list[str] = []
    auto_fixable: bool = False
    fix_hint: str = ""

    @abstractmethod
    def check(self, ctx: OKFContext) -> ViolationResult:
        ...
