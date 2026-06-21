"""Handoff marker parsing and gated Spawn evaluation."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from hephaestus.core import Violation
from hephaestus.rules.base import HephaestusRule

# Matches JSON objects anywhere in a string (greedy outer braces)
_JSON_OBJECT_RE = re.compile(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}", re.DOTALL)


@dataclass(frozen=True)
class HandoffMarker:
    role: str
    task: str
    issue_id: str


class SpawnGating(str, Enum):
    GREEN = "green"
    AMBER = "amber"


@dataclass
class SpawnCard:
    marker: HandoffMarker
    gating: SpawnGating
    failures: list[Violation] = field(default_factory=list)

    @property
    def prefill_role(self) -> str:
        return self.marker.role

    @property
    def prefill_task(self) -> str:
        return self.marker.task


def parse_handoff(text: str) -> HandoffMarker | None:
    """Extract the first valid handoff marker from *text*.

    A valid marker is a JSON object with a "handoff" key whose value has
    "role", "task", and "issue_id" string fields.  Non-JSON text and JSON
    objects that don't match the schema are silently ignored.
    """
    for match in _JSON_OBJECT_RE.finditer(text):
        raw = match.group(0)
        try:
            obj: Any = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        inner = obj.get("handoff")
        if not isinstance(inner, dict):
            continue
        role = inner.get("role")
        task = inner.get("task")
        issue_id = inner.get("issue_id")
        if not (isinstance(role, str) and isinstance(task, str) and isinstance(issue_id, str)):
            continue
        if not (role and task and issue_id):
            continue
        return HandoffMarker(role=role, task=task, issue_id=issue_id)
    return None


def evaluate_spawn_gate(
    marker: HandoffMarker,
    ctx,
    *,
    exit_rules: list[HephaestusRule],
) -> SpawnCard:
    """Run exit rules against *ctx* and return a SpawnCard.

    All pass → GREEN.  Any failure → AMBER (force-spawn is still allowed by
    the caller).
    """
    failures: list[Violation] = []
    for rule in exit_rules:
        if rule.layer != "exit":
            continue
        result = rule.check(ctx)
        failures.extend(result.violations)

    gating = SpawnGating.GREEN if not failures else SpawnGating.AMBER
    return SpawnCard(marker=marker, gating=gating, failures=failures)
