from __future__ import annotations

from hephaestus.store.frozen_rules import (
    ScopeAddress,
    list_frozen_rules_for_address,
    upsert_frozen_rule,
)


def make_db(tmp_path):
    return tmp_path / ".hephaestus" / "state.db"


def test_upsert_frozen_rule_supersedes_same_scope_and_topic(tmp_path):
    db = make_db(tmp_path)

    first = upsert_frozen_rule(
        db,
        scope="workflow",
        topic_key="shell-prelude",
        body="Use npm --prefix frontend.",
        workflow_id="wf-018",
    )
    second = upsert_frozen_rule(
        db,
        scope="workflow",
        topic_key="shell-prelude",
        body="Use npm --prefix frontend and pnpm nowhere.",
        workflow_id="wf-018",
    )

    rules = list_frozen_rules_for_address(
        db,
        ScopeAddress(
            machine="workspace-a",
            workflow_id="wf-018",
            workflow_run_id="run-001",
            placement_id="implement",
            node_id="node-001",
            tags=["worker"],
        ),
    )

    assert len(rules) == 1
    assert rules[0].id == second.id
    assert rules[0].body == "Use npm --prefix frontend and pnpm nowhere."
    assert rules[0].scope == "workflow"
    assert rules[0].scope_key == "wf-018"
    assert rules[0].workflow_id == "wf-018"
    assert rules[0].updated_at >= first.updated_at


def test_list_frozen_rules_for_address_collects_scope_ladder(tmp_path):
    db = make_db(tmp_path)
    upsert_frozen_rule(db, scope="global", topic_key="tone", body="Stay concise.")
    upsert_frozen_rule(
        db,
        scope="machine",
        topic_key="python",
        body="Use the workspace venv interpreter.",
        machine="workspace-a",
    )
    upsert_frozen_rule(
        db,
        scope="workflow",
        topic_key="artifact",
        body="Issue specs live under agents/architect/issues.",
        workflow_id="wf-018",
    )
    upsert_frozen_rule(
        db,
        scope="tag",
        topic_key="tdd",
        body="Write the failing test first.",
        tag="worker",
    )
    upsert_frozen_rule(
        db,
        scope="node",
        topic_key="handoff",
        body="Finish with a handoff note.",
        workflow_id="wf-018",
        placement_id="implement",
        node_id="node-001",
    )

    rules = list_frozen_rules_for_address(
        db,
        ScopeAddress(
            machine="workspace-a",
            workflow_id="wf-018",
            workflow_run_id="run-001",
            placement_id="implement",
            node_id="node-001",
            tags=["worker", "backend"],
        ),
    )

    assert [(rule.scope, rule.topic_key) for rule in rules] == [
        ("global", "tone"),
        ("machine", "python"),
        ("workflow", "artifact"),
        ("tag", "tdd"),
        ("node", "handoff"),
    ]
    assert rules[-1].scope_key == "wf-018:implement"


def test_node_scope_falls_back_to_node_id_for_standalone_nodes(tmp_path):
    db = make_db(tmp_path)
    upsert_frozen_rule(
        db,
        scope="node",
        topic_key="artifact",
        body="Ad-hoc runs still write a handoff.",
        node_id="node-standalone",
    )

    rules = list_frozen_rules_for_address(
        db,
        ScopeAddress(
            machine="workspace-a",
            workflow_id=None,
            workflow_run_id=None,
            placement_id=None,
            node_id="node-standalone",
            tags=["worker"],
        ),
    )

    assert len(rules) == 1
    assert rules[0].scope == "node"
    assert rules[0].scope_key == "node-standalone"
