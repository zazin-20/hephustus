from __future__ import annotations

import json

from hephaestus.identity import (
    IdentityCard,
    append_session,
    default_capabilities,
    load_card,
    write_card,
)


def test_write_card_creates_file(tmp_path):
    card = IdentityCard(
        agent_id="arch-001",
        name="Architecture Lead",
        role="architect",
        created_at="2026-06-22T00:00:00Z",
        capabilities=["write_spec", "write_handoff"],
        sessions=[],
    )

    path = write_card(tmp_path, card)

    assert path == tmp_path / "agents" / "identities" / "arch-001.json"
    assert path.exists()


def test_load_card_roundtrips(tmp_path):
    card = IdentityCard(
        agent_id="work-001",
        name="Worker One",
        role="worker",
        created_at="2026-06-22T00:00:00Z",
        capabilities=["write_code", "run_tests"],
        sessions=[{"id": "session-001", "status": "done"}],
    )
    write_card(tmp_path, card)

    loaded = load_card(tmp_path, "work-001")

    assert loaded == card


def test_append_session_adds_to_sessions(tmp_path):
    card = IdentityCard(
        agent_id="qa-001",
        name="QA One",
        role="qa",
        created_at="2026-06-22T00:00:00Z",
        capabilities=["write_qa_evidence"],
        sessions=[],
    )
    write_card(tmp_path, card)

    append_session(tmp_path, "qa-001", {"id": "session-001", "result": "pass"})
    loaded = load_card(tmp_path, "qa-001")

    assert loaded.sessions == [{"id": "session-001", "result": "pass"}]


def test_write_card_creates_directory(tmp_path):
    card = IdentityCard(
        agent_id="orch-001",
        name="Coordinator",
        role="orchestrator",
        created_at="2026-06-22T00:00:00Z",
        capabilities=["write_handoff", "plan"],
        sessions=[],
    )

    write_card(tmp_path, card)

    assert (tmp_path / "agents" / "identities").is_dir()


def test_default_capabilities_by_role():
    assert default_capabilities("architect") == ["write_spec", "write_handoff"]
    assert default_capabilities("worker") == ["write_code", "run_tests"]
    assert default_capabilities("qa") == ["write_qa_evidence"]
    assert default_capabilities("orchestrator") == ["write_handoff", "plan"]
    assert default_capabilities("unknown") == []
