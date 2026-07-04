"""Handoff marker parsing and gated Spawn evaluation.

REUSABLE — the transition-gate primitive. `evaluate_spawn_gate` / `SpawnCard`
(GREEN/AMBER) is the gate-at-an-edge for the gatekeeper posture (choice A); its
`exit_rules` become user-authored.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from itertools import chain
from typing import Any, Iterable

from hephaestus.core import Violation
from hephaestus.rules.base import HephaestusRule

# Matches JSON objects anywhere in a string (greedy outer braces)
_JSON_OBJECT_RE = re.compile(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}", re.DOTALL)
_MARKER_SENTINEL = "@@HEPHAESTUS@@"
_MARKER_LINE_RE = re.compile(
    rf"(?m)^[ \t]*{re.escape(_MARKER_SENTINEL)}[ \t]+(.+)$"
)
_DISTILLATION_SCOPES = {"global", "machine", "workflow", "tag", "node"}


@dataclass(frozen=True)
class HandoffMarker:
    role: str
    task: str
    issue_id: str


@dataclass(frozen=True)
class SkillCompleteMarker:
    skill: str
    ok: bool


@dataclass(frozen=True)
class DistillationCandidateMarker:
    topic_key: str
    scope: str
    directive: str


Marker = HandoffMarker | SkillCompleteMarker | DistillationCandidateMarker


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
    candidates: list[tuple[int, str, str]] = []
    candidates.extend((match.start(), "protocol", match.group(1)) for match in _MARKER_LINE_RE.finditer(text))
    candidates.extend((match.start(), "legacy", match.group(0)) for match in _JSON_OBJECT_RE.finditer(text))

    for _, kind, raw in sorted(candidates, key=lambda item: item[0]):
        if kind == "protocol":
            marker = _parse_protocol_marker(raw)
            if isinstance(marker, HandoffMarker):
                return marker
            continue
        marker = _parse_legacy_handoff(raw)
        if marker is not None:
            return marker
    return None


def parse_marker(text: str) -> Marker | None:
    """Extract the first valid protocol marker from *text*."""
    return next(iter_markers(text), None)


def parse_marker_from_turns(turns: Iterable[Any]) -> Marker | None:
    """Scan assistant text turns for the first valid protocol marker."""
    return next(iter_markers_from_turns(turns), None)


def iter_markers(text: str) -> Iterable[Marker]:
    """Yield every valid protocol marker in *text* in encounter order."""
    for match in _MARKER_LINE_RE.finditer(text):
        marker = _parse_protocol_marker(match.group(1))
        if marker is not None:
            yield marker


def iter_markers_from_turns(turns: Iterable[Any]) -> Iterable[Marker]:
    """Yield protocol markers from assistant text turns, ignoring thinking."""
    for turn in turns:
        if getattr(turn, "role", None) != "assistant":
            continue
        if getattr(turn, "kind", None) == "thinking":
            continue
        text = getattr(turn, "text", None)
        if not isinstance(text, str):
            continue
        yield from iter_markers(text)


def parse_marker_from_trace(trace: Iterable[Any]) -> Marker | None:
    """Scan tool-call command strings for the first valid protocol marker."""
    return next(iter_markers_from_trace(trace), None)


def iter_markers_from_trace(trace: Iterable[Any]) -> Iterable[Marker]:
    """Yield protocol markers from tool-call command strings."""
    for event in trace:
        for command in _iter_trace_command_strings(getattr(event, "raw", None)):
            yield from iter_markers(command)


def iter_trace_markers(trace: Iterable[Any]) -> Iterable[tuple[Any, Marker]]:
    """Yield ``(trace_event, marker)`` tuples for protocol markers in trace commands."""
    for event in trace:
        for command in _iter_trace_command_strings(getattr(event, "raw", None)):
            for marker in iter_markers(command):
                yield event, marker


def has_skill_completion(
    skill: str,
    *,
    turns: Iterable[Any],
    trace: Iterable[Any],
) -> bool:
    """Return True when the trace contains a successful completion marker."""
    for marker in chain(iter_markers_from_turns(turns), iter_markers_from_trace(trace)):
        if isinstance(marker, SkillCompleteMarker) and marker.skill == skill and marker.ok:
            return True
    return False


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


def _parse_legacy_handoff(raw: str) -> HandoffMarker | None:
    try:
        obj: Any = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict):
        return None
    return _handoff_marker_from_payload(obj.get("handoff"))


def _parse_protocol_marker(raw: str) -> Marker | None:
    obj = _parse_strict_json_object(raw)
    if obj is None:
        return None

    version = obj.get("v")
    marker_type = obj.get("type")
    if version != 1 or not isinstance(marker_type, str):
        return None

    if marker_type == "handoff":
        return _handoff_marker_from_payload(obj)
    if marker_type == "skill_complete":
        skill = obj.get("skill")
        ok = obj.get("ok")
        if isinstance(skill, str) and skill and isinstance(ok, bool):
            return SkillCompleteMarker(skill=skill, ok=ok)
        return None
    if marker_type == "distillation_candidate":
        topic_key = obj.get("topic_key")
        scope = obj.get("scope")
        directive = obj.get("directive")
        if (
            isinstance(topic_key, str)
            and topic_key
            and isinstance(scope, str)
            and scope in _DISTILLATION_SCOPES
            and isinstance(directive, str)
            and directive
        ):
            return DistillationCandidateMarker(
                topic_key=topic_key,
                scope=scope,
                directive=directive,
            )
        return None
    return None


def _parse_strict_json_object(raw: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    try:
        obj, end = decoder.raw_decode(raw)
    except json.JSONDecodeError:
        return None
    if raw[end:].strip():
        return None
    if not isinstance(obj, dict):
        return None
    return obj


def _handoff_marker_from_payload(payload: Any) -> HandoffMarker | None:
    if not isinstance(payload, dict):
        return None
    role = payload.get("role")
    task = payload.get("task")
    issue_id = payload.get("issue_id")
    if not (isinstance(role, str) and isinstance(task, str) and isinstance(issue_id, str)):
        return None
    if not (role and task and issue_id):
        return None
    return HandoffMarker(role=role, task=task, issue_id=issue_id)


def _iter_trace_command_strings(raw: Any) -> Iterable[str]:
    if isinstance(raw, dict):
        for key, value in raw.items():
            if key == "command" and isinstance(value, str):
                yield value
            else:
                yield from _iter_trace_command_strings(value)
        return
    if isinstance(raw, list):
        for item in raw:
            yield from _iter_trace_command_strings(item)
