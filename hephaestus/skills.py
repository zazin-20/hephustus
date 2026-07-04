"""Skill registry helpers for node playbooks.

REUSABLE — a skill reference is resolved through the canonical OKF registry
under ``agents/skills/`` instead of scattering path logic through callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from hephaestus.okf_layout import OKFLayout

_SKILL_REF_RE = re.compile(r"^skill:(?P<skill_id>[A-Za-z0-9][A-Za-z0-9._/-]*)$")


@dataclass(frozen=True, slots=True)
class SkillReference:
    ref: str
    skill_id: str
    path: Path


def resolve_skill_ref(layout: OKFLayout, ref: str) -> SkillReference:
    raw = ref.strip()
    if not raw:
        raise ValueError("skill reference must not be blank")

    match = _SKILL_REF_RE.match(raw)
    if match:
        skill_id = match.group("skill_id")
        return SkillReference(ref=raw, skill_id=skill_id, path=layout.skill_path(skill_id))

    declared = Path(raw)
    if raw.endswith(".md") or declared.is_absolute() or raw.startswith("agents/"):
        if declared.is_absolute():
            path = declared
        elif declared.parts and declared.parts[0] == "agents":
            path = layout.workspace_root / declared
        else:
            path = layout.resolve(declared)
        skill_id = declared.stem
        return SkillReference(ref=raw, skill_id=skill_id, path=path)

    return SkillReference(ref=raw, skill_id=raw, path=layout.skill_path(raw))


def resolve_skill_refs(layout: OKFLayout, refs: list[str]) -> list[SkillReference]:
    return [resolve_skill_ref(layout, ref) for ref in refs]
