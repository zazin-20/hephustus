"""Pipeline dashboard derivation (spec/architecture.md §3.2).

Pure functions that turn an OKFContext into JSON-serializable data for the UI.
Each issue's pipeline state is inferred from file presence + frontmatter — no
separate database. `snapshot()` is the single payload the desktop bridge serves
and pushes.
"""
from __future__ import annotations

import re
from pathlib import Path

from hephaestus.core import Violation
from hephaestus.index import OKFContext, build_context
from hephaestus.models import IssueStatus
from hephaestus.rules.registry import run_all

_ISSUE_RE = re.compile(r"issue-\w+")

STAGE_OK = "ok"
STAGE_PENDING = "pending"
STAGE_NONE = "none"


def issue_id_from(v: Violation) -> str | None:
    """Best-effort map a violation back to an issue id via its artifact or message."""
    stem = Path(v.artifact).stem
    if _ISSUE_RE.fullmatch(stem):
        return stem
    m = _ISSUE_RE.search(v.message)
    return m.group(0) if m else None


def _pipeline_state(status: IssueStatus, has_handoff: bool, has_qa: bool, has_log: bool) -> str:
    if status == IssueStatus.OPEN:
        return "OPEN"
    if status == IssueStatus.IN_PROGRESS:
        return "IN_PROGRESS"
    # done / handoff-pending
    if has_qa and has_log:
        return "DONE"
    if not has_handoff:
        return "HANDOFF_PENDING"
    return "QA_PENDING"


def build_dashboard(ctx: OKFContext, violations: list[Violation]) -> list[dict]:
    handoffs = {h.issue_id: h for h in ctx.handoffs}
    qa = {e.issue_id for e in ctx.qa_evidence}
    logs = {e.issue_id for e in ctx.log_entries}

    by_issue: dict[str, list[str]] = {}
    for v in violations:
        iid = issue_id_from(v)
        if iid:
            by_issue.setdefault(iid, []).append(v.rule_id)

    rows = []
    for issue in sorted(ctx.issues, key=lambda i: i.id):
        h = handoffs.get(issue.id)
        has_h = h is not None
        reviewed = bool(h and "architect" in h.reviewed_by)
        has_qa = issue.id in qa
        has_log = issue.id in logs
        is_done = issue.status == IssueStatus.DONE
        rows.append({
            "id": issue.id,
            "title": issue.title or issue.id,
            "status": issue.status.value,
            "sprint": issue.sprint,
            "state": _pipeline_state(issue.status, has_h, has_qa, has_log),
            "stages": {
                "spec": STAGE_OK,
                "handoff": STAGE_OK if has_h else (STAGE_PENDING if is_done else STAGE_NONE),
                "review": STAGE_OK if reviewed else (STAGE_PENDING if has_h else STAGE_NONE),
                "qa": STAGE_OK if has_qa else (STAGE_PENDING if has_h else STAGE_NONE),
                "log": STAGE_OK if has_log else (STAGE_PENDING if is_done else STAGE_NONE),
            },
            "violations": sorted(set(by_issue.get(issue.id, []))),
        })
    return rows


def snapshot(root: str | Path) -> dict:
    """Full UI payload: dashboard rows + violations + summary counts."""
    ctx = build_context(root)
    violations = run_all(ctx)

    counts = {"error": 0, "warning": 0, "info": 0}
    for v in violations:
        counts[v.severity.value] = counts.get(v.severity.value, 0) + 1

    return {
        "root": str(Path(root)),
        "issues": build_dashboard(ctx, violations),
        "violations": [
            {
                "rule_id": v.rule_id,
                "severity": v.severity.value,
                "message": v.message,
                "artifact": v.artifact,
                "fix_hint": v.fix_hint,
                "issue_id": issue_id_from(v),
            }
            for v in violations
        ],
        "summary": {"issues": len(ctx.issues), "violations": len(violations), **counts},
    }
