"""Dashboard snapshot derivation.

REUSABLE — the status-surface shape. `snapshot()` is the single JSON payload the
desktop bridge serves/pushes: a list of work rows + violations + summary counts.
This envelope and the per-row stage-chip rendering are exactly the
**node-level visual feedback** surface for user-authored workflows (PRD ✓, ADR ✓,
issues ✓, handoff ✓, verified) — issue→workflow-node, hardcoded stages→the
workflow's gates.

The hardcoded issue→handoff→qa→log pipeline derivation (`build_dashboard`,
`_pipeline_state`) was removed when governance moved to user-authored specs, so
`rows` is empty until a workflow model feeds it. Violations still flow (currently
Tier-1 schema load errors via `run_all`). See docs/design/governance-engine.md.
"""
from __future__ import annotations

from pathlib import Path

from hephaestus.index import build_context
from hephaestus.rules.registry import run_all


def snapshot(root: str | Path) -> dict:
    """Full UI payload: work rows + violations + summary counts."""
    ctx = build_context(root)
    violations = run_all(ctx)

    counts = {"error": 0, "warning": 0, "info": 0}
    for v in violations:
        counts[v.severity.value] = counts.get(v.severity.value, 0) + 1

    rows: list[dict] = []  # awaiting the user-authored workflow/node model

    return {
        "root": str(Path(root)),
        "issues": rows,
        "violations": [
            {
                "rule_id": v.rule_id,
                "severity": v.severity.value,
                "message": v.message,
                "artifact": v.artifact,
                "fix_hint": v.fix_hint,
                "issue_id": None,
            }
            for v in violations
        ],
        "summary": {"issues": len(rows), "violations": len(violations), **counts},
    }
