from __future__ import annotations

import json

import pytest

from hephaestus.okf_layout import OKFLayout
from hephaestus.workflows import (
    Edge,
    Guard,
    Placement,
    Workflow,
    WorkflowValidationError,
    load_workflow,
    save_workflow,
)


def test_save_workflow_writes_yaml_under_okf_and_loads_back(tmp_path):
    workflow = Workflow(
        workflow_id="issue-020",
        placements=[
            Placement(placement_id="author", node_id="node-001", x=120, y=80),
            Placement(placement_id="review", node_id="node-002", x=360, y=80),
        ],
        edges=[
            Edge(
                from_placement_id="author",
                from_output="artifact:adr",
                to_placement_id="review",
                to_input="artifact:adr",
                guard=Guard(condition="artifact_exists('qa')", label="qa-ready"),
            )
        ],
    )

    path = save_workflow(tmp_path, workflow)

    assert path == OKFLayout.for_workspace(tmp_path).workflow_path("issue-020")
    assert load_workflow(path) == workflow


def test_save_workflow_supports_json_roundtrip(tmp_path):
    workflow = Workflow(
        workflow_id="issue-020-json",
        placements=[Placement(placement_id="author", node_id="node-001", x=120, y=80)],
        edges=[],
    )

    path = save_workflow(tmp_path, workflow, suffix=".json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert path == OKFLayout.for_workspace(tmp_path).workflow_path("issue-020-json", suffix=".json")
    assert payload["placements"][0]["node_id"] == "node-001"
    assert load_workflow(path) == workflow


def test_save_workflow_rejects_edges_that_reference_unknown_placements(tmp_path):
    workflow = Workflow(
        workflow_id="issue-020",
        placements=[Placement(placement_id="author", node_id="node-001", x=120, y=80)],
        edges=[
            Edge(
                from_placement_id="author",
                from_output="artifact:adr",
                to_placement_id="review",
                to_input="artifact:adr",
            )
        ],
    )

    with pytest.raises(WorkflowValidationError, match="review"):
        save_workflow(tmp_path, workflow)


def test_save_workflow_rejects_unguarded_cycles(tmp_path):
    workflow = Workflow(
        workflow_id="issue-020",
        placements=[
            Placement(placement_id="author", node_id="node-001", x=120, y=80),
            Placement(placement_id="review", node_id="node-002", x=360, y=80),
        ],
        edges=[
            Edge(
                from_placement_id="author",
                from_output="artifact:adr",
                to_placement_id="review",
                to_input="artifact:adr",
            ),
            Edge(
                from_placement_id="review",
                from_output="artifact:feedback",
                to_placement_id="author",
                to_input="artifact:feedback",
            ),
        ],
    )

    with pytest.raises(WorkflowValidationError, match="cycle"):
        save_workflow(tmp_path, workflow)


def test_save_workflow_allows_cycles_when_an_edge_is_guarded(tmp_path):
    workflow = Workflow(
        workflow_id="issue-020",
        placements=[
            Placement(placement_id="author", node_id="node-001", x=120, y=80),
            Placement(placement_id="review", node_id="node-002", x=360, y=80),
        ],
        edges=[
            Edge(
                from_placement_id="author",
                from_output="artifact:adr",
                to_placement_id="review",
                to_input="artifact:adr",
            ),
            Edge(
                from_placement_id="review",
                from_output="artifact:feedback",
                to_placement_id="author",
                to_input="artifact:feedback",
                guard=Guard(condition="needs_revision()", label="revise"),
            ),
        ],
    )

    path = save_workflow(tmp_path, workflow)

    assert load_workflow(path) == workflow
