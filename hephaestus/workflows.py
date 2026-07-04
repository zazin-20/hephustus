"""Workflow model persistence for OKF-authored node graphs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import yaml

from hephaestus.okf_layout import OKFLayout


class WorkflowValidationError(ValueError):
    """Raised when a workflow graph violates the authored workflow rules."""


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


@dataclass(frozen=True, slots=True)
class Edge:
    from_placement_id: str
    from_output: str
    to_placement_id: str
    to_input: str
    guard: Guard | None = None


@dataclass(frozen=True, slots=True)
class Workflow:
    workflow_id: str
    placements: list[Placement]
    edges: list[Edge]
    version: int = 1


def save_workflow(okf_root: Path, workflow: Workflow, *, suffix: str = ".yaml") -> Path:
    _validate_workflow(workflow)
    path = OKFLayout.for_existing_root(okf_root).workflow_path(workflow.workflow_id, suffix=suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(workflow)
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    else:
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def load_workflow(path: Path) -> Workflow:
    payload = _load_payload(path)
    placements = [Placement(**item) for item in payload.get("placements", [])]
    edges = [
        Edge(
            from_placement_id=item["from_placement_id"],
            from_output=item["from_output"],
            to_placement_id=item["to_placement_id"],
            to_input=item["to_input"],
            guard=Guard(**item["guard"]) if item.get("guard") is not None else None,
        )
        for item in payload.get("edges", [])
    ]
    workflow = Workflow(
        workflow_id=payload["workflow_id"],
        version=payload.get("version", 1),
        placements=placements,
        edges=edges,
    )
    _validate_workflow(workflow)
    return workflow


def _load_payload(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(raw)
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError("workflow payload must be a mapping")
    return data


def _validate_workflow(workflow: Workflow) -> None:
    placement_ids = {placement.placement_id for placement in workflow.placements}
    if len(placement_ids) != len(workflow.placements):
        raise WorkflowValidationError("workflow placements must have unique ids")
    for edge in workflow.edges:
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
