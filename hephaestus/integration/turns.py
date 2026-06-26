"""Normalized turn metadata shared across agent runners, service, and UI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TurnDescriptor:
    category: str
    transcript_role: str | None
    label: str
    conversation: bool
    always_persist: bool = False


_USER = TurnDescriptor(
    category="user",
    transcript_role="user",
    label="user",
    conversation=True,
)

_ASSISTANT_TEXT = TurnDescriptor(
    category="content",
    transcript_role="assistant",
    label="agent",
    conversation=True,
)

_ASSISTANT_THINKING = TurnDescriptor(
    category="thinking",
    transcript_role="assistant",
    label="think",
    conversation=True,
)

_ASSISTANT_ERROR = TurnDescriptor(
    category="error",
    transcript_role="assistant",
    label="err",
    conversation=True,
)

_TOOL = TurnDescriptor(
    category="tool",
    transcript_role="tool",
    label="tool",
    conversation=False,
    always_persist=True,
)

_LIFECYCLE = TurnDescriptor(
    category="lifecycle",
    transcript_role="assistant",
    label="agent",
    conversation=False,
)

_BY_KIND = {
    "text": _ASSISTANT_TEXT,
    "thinking": _ASSISTANT_THINKING,
    "error": _ASSISTANT_ERROR,
    "tool": _TOOL,
    "tool_call": _TOOL,
    "system": _LIFECYCLE,
    "result": _LIFECYCLE,
}


def describe_turn(kind: str | None, *, role: str | None = None) -> TurnDescriptor:
    """Return normalized metadata for a transcript/event turn."""
    if role == "user":
        return _USER
    if role == "tool":
        return _TOOL
    if kind in _BY_KIND:
        return _BY_KIND[kind]
    if role == "assistant":
        return _ASSISTANT_TEXT
    return _LIFECYCLE


def turn_payload(kind: str | None, *, text: str = "", role: str | None = None) -> dict[str, object]:
    descriptor = describe_turn(kind, role=role)
    return {
        "category": descriptor.category,
        "transcript_role": descriptor.transcript_role,
        "label": descriptor.label,
        "conversation": descriptor.conversation,
        "persist": bool(text.strip()) or descriptor.always_persist,
    }
