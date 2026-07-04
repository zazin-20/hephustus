"""Workflow model persistence for OKF-authored node graphs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import json
from pathlib import Path

import yaml

from hephaestus.okf_layout import OKFLayout


class WorkflowValidationError(ValueError):
    """Raised when a workflow graph violates the authored workflow rules."""


class AdvanceMode(str, Enum):
    ALLOW = "allow"
    ASK = "ask"


class NodeInteractivity(str, Enum):
    AFK = "afk"
    HITL = "hitl"


@dataclass(frozen=True, slots=True)
class Guard:
    condition: str
    label: str | None = None


@dataclass(frozen=True, slots=True)
class Placement:
    placement_id: str
    node_id: str
    x: int | float
    y: int | float
    interactivity: NodeInteractivity = NodeInteractivity.AFK


@dataclass(frozen=True, slots=True)
class Edge:
    from_placement_id: str
    from_output: str
    to_placement_id: str
    to_input: str
    guard: Guard | None = None
    advance: AdvanceMode = AdvanceMode.ALLOW


@dataclass(frozen=True, slots=True)
class Workflow:
    workflow_id: str
    placements: list[Placement]
    edges: list[Edge]
    version: int = 1


def workflow_to_dict(workflow: Workflow) -> dict:
    return _serialize_payload(asdict(workflow))


def workflow_from_dict(payload: dict) -> Workflow:
    edges = [
        Edge(
            from_placement_id=item["from_placement_id"],
            from_output=item["from_output"],
            to_placement_id=item["to_placement_id"],
            to_input=item["to_input"],
            guard=Guard(**item["guard"]) if item.get("guard") is not None else None,
            advance=AdvanceMode(item.get("advance", AdvanceMode.ALLOW)),
        )
        for item in payload.get("edges", [])
    ]
    placements = [
        Placement(
            placement_id=item["placement_id"],
            node_id=item["node_id"],
            x=item["x"],
            y=item["y"],
            interactivity=NodeInteractivity(item.get("interactivity", NodeInteractivity.AFK)),
        )
        for item in payload.get("placements", [])
    ]
    workflow = Workflow(
        workflow_id=payload["workflow_id"],
        version=payload.get("version", 1),
        placements=placements,
        edges=edges,
    )
    _validate_workflow(workflow)
    return workflow


def save_workflow(okf_root: Path, workflow: Workflow, *, suffix: str = ".yaml") -> Path:
    _validate_workflow(workflow)
    path = OKFLayout.for_existing_root(okf_root).workflow_path(workflow.workflow_id, suffix=suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = workflow_to_dict(workflow)
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    else:
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def load_workflow(path: Path) -> Workflow:
    payload = _load_payload(path)
    return workflow_from_dict(payload)


def list_workflows(okf_root: Path) -> list[Workflow]:
    workflows_dir = OKFLayout.for_existing_root(okf_root).workflows_dir
    if not workflows_dir.exists():
        return []
    paths = sorted(
        [
            path
            for path in workflows_dir.iterdir()
            if path.is_file() and path.suffix.lower() in {".yaml", ".yml", ".json"}
        ],
        key=lambda path: (path.stem.lower(), path.suffix.lower()),
    )
    return [load_workflow(path) for path in paths]


def _load_payload(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(raw)
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError("workflow payload must be a mapping")
    return data


def _serialize_payload(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _serialize_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_payload(item) for item in value]
    return value


def _validate_workflow(workflow: Workflow) -> None:
    placement_ids = {placement.placement_id for placement in workflow.placements}
    if len(placement_ids) != len(workflow.placements):
        raise WorkflowValidationError("workflow placements must have unique ids")
    for placement in workflow.placements:
        NodeInteractivity(placement.interactivity)
    for edge in workflow.edges:
        AdvanceMode(edge.advance)
        if edge.from_placement_id not in placement_ids:
            raise WorkflowValidationError(
                f"edge references unknown source placement: {edge.from_placement_id}"
            )
        if edge.to_placement_id not in placement_ids:
            raise WorkflowValidationError(
                f"edge references unknown target placement: {edge.to_placement_id}"
            )
    _reject_unguarded_cycles(workflow.edges)


def _reject_unguarded_cycles(edges: list[Edge]) -> None:
    adjacency: dict[str, list[str]] = {}
    for edge in edges:
        if edge.guard is not None:
            continue
        adjacency.setdefault(edge.from_placement_id, []).append(edge.to_placement_id)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(placement_id: str) -> bool:
        if placement_id in visiting:
            return True
        if placement_id in visited:
            return False
        visiting.add(placement_id)
        for target in adjacency.get(placement_id, []):
            if visit(target):
                return True
        visiting.remove(placement_id)
        visited.add(placement_id)
        return False

    for placement_id in adjacency:
        if visit(placement_id):
            raise WorkflowValidationError("workflow contains an unguarded cycle")
