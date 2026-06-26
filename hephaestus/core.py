"""Shared primitives used by both the validation pipeline and the rule engine.

REUSABLE — gate-result vocabulary. `Severity` / `Violation` / `ViolationResult`
are how every check (a user-authored artifact predicate, a governance rule, a
schema load error) reports a failure. The whole engine speaks this.


Kept dependency-free (no imports from models/index/rules) so everything else can
import from here without creating cycles.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    ERROR = "error"      # blocks pipeline progression
    WARNING = "warning"  # drift; should be resolved but does not block
    INFO = "info"        # informational


@dataclass(frozen=True)
class Violation:
    """A single rule or schema failure tied to a concrete artifact."""

    rule_id: str
    severity: Severity
    message: str
    artifact: str
    fix_hint: str = ""
    auto_fixable: bool = False


@dataclass
class ViolationResult:
    passed: bool
    violations: list[Violation] = field(default_factory=list)

    @classmethod
    def of(cls, violations: list[Violation]) -> "ViolationResult":
        return cls(passed=len(violations) == 0, violations=list(violations))
