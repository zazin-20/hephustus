from __future__ import annotations

import json

import pytest

from hephaestus.okf_layout import OKFLayout
from hephaestus.workflows import (
    AdvanceMode,
    Edge,
    Guard,
    NodeInteractivity,
    Placement,
    Workflow,
    WorkflowValidationError,
    list_workflows,
    load_workflow,
    save_workflow,
    workflow_from_dict,
    workflow_to_dict,
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


def test_workflow_dict_roundtrip_preserves_canvas_fields():
    payload = {
        "workflow_id": "issue-025",
        "version": 2,
        "placements": [
            {
                "placement_id": "draft",
                "node_id": "node-001",
                "x": 120,
                "y": 80,
                "interactivity": "hitl",
            },
            {
                "placement_id": "review",
                "node_id": "node-002",
                "x": 360,
                "y": 80,
                "interactivity": "afk",
            }
        ],
        "edges": [
            {
                "from_placement_id": "draft",
                "from_output": "agents/artifacts/draft.md",
                "to_placement_id": "review",
                "to_input": "agents/artifacts/draft.md",
                "advance": "ask",
                "guard": {"condition": "needs_review()", "label": "review"},
            }
        ],
    }

    workflow = workflow_from_dict(payload)

    assert workflow == Workflow(
        workflow_id="issue-025",
        version=2,
        placements=[
            Placement(
                placement_id="draft",
                node_id="node-001",
                x=120,
                y=80,
                interactivity=NodeInteractivity.HITL,
            ),
            Placement(
                placement_id="review",
                node_id="node-002",
                x=360,
                y=80,
            ),
        ],
        edges=[
            Edge(
                from_placement_id="draft",
                from_output="agents/artifacts/draft.md",
                to_placement_id="review",
                to_input="agents/artifacts/draft.md",
                advance=AdvanceMode.ASK,
                guard=Guard(condition="needs_review()", label="review"),
            )
        ],
    )
    assert workflow_to_dict(workflow) == payload


def test_list_workflows_returns_saved_graphs_in_stable_order(tmp_path):
    alpha = Workflow(
        workflow_id="issue-024",
        placements=[Placement(placement_id="draft", node_id="node-001", x=0, y=0)],
        edges=[],
    )
    beta = Workflow(
        workflow_id="issue-025",
        placements=[Placement(placement_id="review", node_id="node-002", x=1, y=0)],
        edges=[],
    )

    save_workflow(tmp_path, beta, suffix=".json")
    save_workflow(tmp_path, alpha)

    listed = list_workflows(tmp_path)

    assert [item.workflow_id for item in listed] == ["issue-024", "issue-025"]
