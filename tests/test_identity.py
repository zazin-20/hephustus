from __future__ import annotations

import json

from hephaestus.identity import (
    IdentityCard,
    append_session,
    default_capabilities,
    load_card,
    write_card,
)
from hephaestus.okf_layout import OKFLayout


def test_write_card_creates_file(tmp_path):
    card = IdentityCard(
        node_id="node-001",
        name="Architecture Lead",
        tags=["architect"],
        created_at="2026-06-22T00:00:00Z",
        capabilities=["write_spec", "write_handoff"],
        sessions=[],
    )

    path = write_card(tmp_path, card)

    assert path == tmp_path / "agents" / "identities" / "node-001.json"
    assert path.exists()


def test_load_card_roundtrips(tmp_path):
    card = IdentityCard(
        node_id="node-002",
        name="Worker One",
        tags=["worker"],
        created_at="2026-06-22T00:00:00Z",
        capabilities=["write_code", "run_tests"],
        sessions=[{"id": "session-001", "status": "done"}],
    )
    write_card(tmp_path, card)

    loaded = load_card(tmp_path, "node-002")

    assert loaded == card


def test_append_session_adds_to_sessions(tmp_path):
    card = IdentityCard(
        node_id="node-003",
        name="QA One",
        tags=["qa"],
        created_at="2026-06-22T00:00:00Z",
        capabilities=["write_qa_evidence"],
        sessions=[],
    )
    write_card(tmp_path, card)

    append_session(tmp_path, "node-003", {"id": "session-001", "result": "pass"})
    loaded = load_card(tmp_path, "node-003")

    assert loaded.sessions == [{"id": "session-001", "result": "pass"}]


def test_write_card_creates_directory(tmp_path):
    card = IdentityCard(
        node_id="node-004",
        name="Coordinator",
        tags=["orchestrator"],
        created_at="2026-06-22T00:00:00Z",
        capabilities=["plan", "write_handoff"],
        sessions=[],
    )

    write_card(tmp_path, card)

    assert (tmp_path / "agents" / "identities").is_dir()


def test_write_card_accepts_agents_root(tmp_path):
    agents_root = tmp_path / "agents"
    card = IdentityCard(
        node_id="node-005",
        name="Coordinator",
        tags=["orchestrator"],
        created_at="2026-06-22T00:00:00Z",
        capabilities=["plan", "write_handoff"],
        sessions=[],
    )

    path = write_card(agents_root, card)

    assert path == agents_root / "identities" / "node-005.json"
    assert path.exists()


def test_load_card_accepts_agents_root(tmp_path):
    agents_root = tmp_path / "agents"
    card = IdentityCard(
        node_id="node-006",
        name="Worker One",
        tags=["worker"],
        created_at="2026-06-22T00:00:00Z",
        capabilities=["write_code", "run_tests"],
        sessions=[],
    )

    write_card(tmp_path, card)

    assert load_card(agents_root, "node-006") == card
    assert OKFLayout.for_existing_root(agents_root).identity_card_path("node-006").exists()

def test_default_capabilities_by_tags():
    assert default_capabilities("architect") == ["write_spec", "write_handoff"]
    assert default_capabilities("worker") == ["write_code", "run_tests"]
    assert default_capabilities("qa") == ["write_qa_evidence"]
    assert default_capabilities("orchestrator") == ["plan", "write_handoff"]
    assert default_capabilities(["planner", "orchestrator"]) == ["plan", "write_handoff"]
    assert default_capabilities("unknown") == []
