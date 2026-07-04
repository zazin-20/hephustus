from __future__ import annotations

import json

from hephaestus.dashboard import snapshot
from hephaestus.integration.service import AgentService
from hephaestus.store.nodes import create_node
from hephaestus.store.runs import create_run
from hephaestus.store.threads import append_turn, get_or_create_thread
from hephaestus.store.trace import append_trace_event
from hephaestus.workflows import AdvanceMode, Edge, Placement, Workflow, save_workflow


def test_clean_snapshot_has_no_violations(clean_tree):
    snap = snapshot(clean_tree)
    assert snap["summary"]["violations"] == 0
    assert snap["issues"] == []  # no workflow/node model feeds rows yet


def test_schema_error_surfaces_in_snapshot(schema_error_tree):
    snap = snapshot(schema_error_tree)
    assert snap["summary"]["violations"] >= 1
    assert any(v["rule_id"] == "schema" for v in snap["violations"])


def test_snapshot_is_json_serializable(schema_error_tree):
    json.dumps(snapshot(schema_error_tree))  # must not raise


def test_snapshot_includes_workflow_canvas_with_live_overlay(tmp_path):
    service = AgentService(tmp_path)
    draft = create_node(
        service.state_db_path,
        tmp_path,
        name="Draft",
        provider="codex",
        tags=["worker"],
        rules=[],
        model="gpt-5.4",
        outputs=["agents/specs/draft-spec.md"],
    )
    review = create_node(
        service.state_db_path,
        tmp_path,
        name="Review",
        provider="builtin",
        tags=["builtin", "notify"],
        rules=[],
    )
    workflow = Workflow(
        workflow_id="issue-025",
        placements=[
            Placement(placement_id="draft", node_id=draft.node_id, x=120, y=80),
            Placement(placement_id="review", node_id=review.node_id, x=360, y=80),
        ],
        edges=[
            Edge(
                from_placement_id="draft",
                from_output="agents/artifacts/draft-output.md",
                to_placement_id="review",
                to_input="agents/artifacts/draft-output.md",
                advance=AdvanceMode.ASK,
            )
        ],
    )
    save_workflow(tmp_path, workflow)
    artifact_path = tmp_path / "agents" / "artifacts" / "draft-output.md"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("# Draft output\n", encoding="utf-8")
    thread = get_or_create_thread(
        service.state_db_path,
        node_id=draft.node_id,
        name="issue-025",
        workflow_id="issue-025",
        workflow_run_id="run-025",
        placement_id="draft",
        issue_id="issue-025",
    )
    run = create_run(
        service.state_db_path,
        thread_id=thread.id,
        node_id=draft.node_id,
        contract={"workflow_id": "issue-025"},
    )
    append_turn(service.state_db_path, thread.id, role="assistant", kind="text", text="Draft complete", run_id=run.id)
    append_trace_event(
        service.state_db_path,
        run_id=run.id,
        node_id=draft.node_id,
        action="shell",
        target_path=str(artifact_path),
        raw={"command": "write-file"},
    )

    snap = snapshot(
        tmp_path,
        workflow_sessions={
            "issue-025": {
                "workflow_run_id": "run-025",
                "status": "awaiting_confirm",
                "nodes": {
                    "draft": {
                        "placement_id": "draft",
                        "node_id": draft.node_id,
                        "status": "awaiting_confirm",
                        "run_id": run.id,
                        "thread_id": thread.id,
                        "failures": [],
                        "override_available": False,
                        "spawn_card": {
                            "gating": "green",
                            "failures": [],
                            "marker": {
                                "role": "review",
                                "task": "agents/artifacts/draft-output.md",
                                "issue_id": "issue-025",
                            },
                        },
                    }
                },
                "notifications": [
                    {
                        "id": "run-025:draft:done",
                        "kind": "node_done_green",
                        "severity": "ok",
                        "message": "Draft is done and awaiting confirmation.",
                    }
                ],
            }
        },
    )

    workflow_payload = snap["workflow_canvas"]["workflows"][0]
    draft_payload = next(item for item in workflow_payload["placements"] if item["placement_id"] == "draft")
    review_payload = next(item for item in workflow_payload["placements"] if item["placement_id"] == "review")

    assert draft_payload["executor"] == {
        "kind": "engine",
        "provider": "codex",
        "model": "gpt-5.4",
        "effort": None,
    }
    assert review_payload["executor"] == {"kind": "builtin", "name": "review"}
    assert draft_payload["status"] == "awaiting_confirm"
    assert draft_payload["detail"]["transcript"][0]["text"] == "Draft complete"
    assert draft_payload["detail"]["trace"][0]["action"] == "shell"
    assert draft_payload["detail"]["artifacts"][0]["exists"] is True
    assert workflow_payload["edges"][0]["state"] == "awaiting_confirm"
    assert snap["workflow_canvas"]["notifications"][0]["severity"] == "ok"
