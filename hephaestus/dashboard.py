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
from hephaestus.store.nodes import list_nodes as list_node_records
from hephaestus.store.threads import list_turns
from hephaestus.store.trace import list_trace_events
from hephaestus.workspace import Workspace
from hephaestus.workflows import list_workflows


def snapshot(root: str | Path, *, workflow_sessions: dict[str, dict] | None = None) -> dict:
    """Full UI payload: work rows + violations + summary counts."""
    root_path = Path(root)
    ctx = build_context(root_path)
    violations = run_all(ctx)

    counts = {"error": 0, "warning": 0, "info": 0}
    for v in violations:
        counts[v.severity.value] = counts.get(v.severity.value, 0) + 1

    rows: list[dict] = []  # awaiting the user-authored workflow/node model
    workflow_canvas = _workflow_canvas_state(root_path, workflow_sessions or {})

    return {
        "root": str(root_path),
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
        "workflow_canvas": workflow_canvas,
        "summary": {"issues": len(rows), "violations": len(violations), **counts},
    }


def _workflow_canvas_state(root: Path, workflow_sessions: dict[str, dict]) -> dict:
    workspace = Workspace.open(root)
    nodes = {node.node_id: node for node in list_node_records(workspace.state_db_path)}
    workflows = [
        _workflow_payload(
            root,
            workspace.state_db_path,
            workflow,
            nodes=nodes,
            session=workflow_sessions.get(workflow.workflow_id, {}),
        )
        for workflow in list_workflows(root)
    ]
    notifications: list[dict] = []
    for session in workflow_sessions.values():
        notifications.extend(session.get("notifications", []))
    return {
        "available_nodes": [
            {
                "node_id": node.node_id,
                "name": node.name,
                "provider": node.provider,
                "model": node.model,
                "effort": node.effort,
                "tags": list(node.tags),
                "inputs": list(node.inputs),
                "outputs": list(node.outputs),
                "executor": _executor_payload(node),
            }
            for node in nodes.values()
        ],
        "workflows": workflows,
        "notifications": notifications,
    }


def _workflow_payload(root: Path, db_path: Path, workflow, *, nodes: dict[str, object], session: dict) -> dict:
    session_nodes = session.get("nodes", {})
    edges_by_source: dict[str, list] = {}
    for edge in workflow.edges:
        edges_by_source.setdefault(edge.from_placement_id, []).append(edge)

    placements = []
    for placement in workflow.placements:
        node = nodes.get(placement.node_id)
        live = session_nodes.get(placement.placement_id, {})
        placements.append(
            {
                "placement_id": placement.placement_id,
                "node_id": placement.node_id,
                "name": getattr(node, "name", placement.node_id),
                "x": placement.x,
                "y": placement.y,
                "interactivity": placement.interactivity.value,
                "executor": _executor_payload(node),
                "status": live.get("status", "not_started"),
                "detail": _placement_detail(
                    root,
                    db_path,
                    placement=placement,
                    node=node,
                    edges=edges_by_source.get(placement.placement_id, []),
                    live=live,
                ),
            }
        )

    return {
        "workflow_id": workflow.workflow_id,
        "version": workflow.version,
        "run": {
            "workflow_run_id": session.get("workflow_run_id"),
            "status": session.get("status"),
        },
        "placements": placements,
        "edges": [
            {
                "from_placement_id": edge.from_placement_id,
                "from_output": edge.from_output,
                "to_placement_id": edge.to_placement_id,
                "to_input": edge.to_input,
                "advance": edge.advance.value,
                "guard": (
                    {"condition": edge.guard.condition, "label": edge.guard.label}
                    if edge.guard is not None
                    else None
                ),
                "label": edge.guard.label if edge.guard and edge.guard.label else edge.guard.condition if edge.guard else None,
                "state": _edge_state(edge, session_nodes),
            }
            for edge in workflow.edges
        ],
    }


def _executor_payload(node) -> dict:
    if node is None:
        return {"kind": "engine", "provider": "unknown", "model": None, "effort": None}
    if getattr(node, "provider", None) == "builtin" or "builtin" in getattr(node, "tags", []):
        return {"kind": "builtin", "name": getattr(node, "name", "builtin").lower()}
    return {
        "kind": "engine",
        "provider": getattr(node, "provider", None),
        "model": getattr(node, "model", None),
        "effort": getattr(node, "effort", None),
    }


def _placement_detail(root: Path, db_path: Path, *, placement, node, edges: list, live: dict) -> dict:
    transcript = []
    trace = []
    if live.get("thread_id"):
        transcript = [
            {
                "id": turn.id,
                "role": turn.role,
                "kind": turn.kind,
                "text": turn.text,
                "created_at": turn.created_at,
            }
            for turn in list_turns(db_path, live["thread_id"])
        ]
        trace = [
            {
                "id": event.id,
                "run_id": event.run_id,
                "node_id": event.node_id,
                "ts": event.ts,
                "action": event.action,
                "target_path": event.target_path,
                "raw": event.raw,
            }
            for event in list_trace_events(db_path, thread_id=live["thread_id"])
        ]

    artifact_paths = []
    seen: set[str] = set()
    for edge in edges:
        if edge.from_output not in seen:
            artifact_paths.append(edge.from_output)
            seen.add(edge.from_output)

    return {
        "gates": _gate_checklist(root, node=node, artifact_paths=artifact_paths, live=live),
        "artifacts": [
            _artifact_payload(root, declared_path)
            for declared_path in artifact_paths
        ],
        "transcript": transcript,
        "trace": trace,
        "failures": list(live.get("failures", [])),
        "spawn_card": live.get("spawn_card"),
    }


def _gate_checklist(root: Path, *, node, artifact_paths: list[str], live: dict) -> list[dict]:
    if node is None:
        return []
    failures = live.get("failures", [])
    items: list[dict] = []
    status = live.get("status", "not_started")
    for declared in getattr(node, "inputs", []):
        path = _resolve_path(root, declared)
        items.append(
            {
                "kind": "entry",
                "label": declared,
                "status": _gate_status(
                    path=str(path),
                    live_status=status,
                    failures=failures,
                    default_ok=path.is_file(),
                ),
            }
        )
    for declared in artifact_paths:
        path = _resolve_path(root, declared)
        items.append(
            {
                "kind": "artifact",
                "label": declared,
                "status": _gate_status(
                    path=str(path),
                    live_status=status,
                    failures=failures,
                    default_ok=path.is_file(),
                ),
            }
        )
    for skill in getattr(node, "skill_obligations", []):
        items.append(
            {
                "kind": "skill",
                "label": skill,
                "status": _skill_gate_status(skill, status, failures),
            }
        )
    return items


def _artifact_payload(root: Path, declared_path: str) -> dict:
    path = _resolve_path(root, declared_path)
    preview = None
    if path.is_file():
        preview = path.read_text(encoding="utf-8")[:400]
    return {"path": str(path), "exists": path.is_file(), "preview": preview}


def _gate_status(*, path: str, live_status: str, failures: list[dict], default_ok: bool) -> str:
    if any(failure.get("artifact") == path for failure in failures):
        return "fail"
    if default_ok and live_status in {"done", "awaiting_confirm", "running"}:
        return "pass"
    if live_status in {"blocked", "waiting_human", "not_started"} and not default_ok:
        return "pending"
    return "pass" if default_ok else "pending"


def _skill_gate_status(skill: str, live_status: str, failures: list[dict]) -> str:
    if any(failure.get("artifact") == skill or failure.get("rule_id", "").startswith("WF-SKILL-") for failure in failures):
        return "fail"
    if live_status in {"done", "awaiting_confirm"}:
        return "pass"
    return "pending"


def _edge_state(edge, session_nodes: dict[str, dict]) -> str:
    source = session_nodes.get(edge.from_placement_id, {})
    target = session_nodes.get(edge.to_placement_id, {})
    source_status = source.get("status", "not_started")
    target_status = target.get("status", "not_started")

    if source_status == "blocked":
        return "blocked"
    if source_status == "awaiting_confirm" and edge.advance.value == "ask":
        return "awaiting_confirm"
    if target_status == "running":
        return "active"
    if source_status in {"done", "awaiting_confirm"} and target_status in {
        "done",
        "running",
        "waiting_human",
        "blocked",
        "awaiting_confirm",
    }:
        return "done"
    return "idle"


def _resolve_path(root: Path, declared: str) -> Path:
    path = Path(declared)
    if path.is_absolute():
        return path
    return root / path
