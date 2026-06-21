from __future__ import annotations

import json

import pytest

from hephaestus.store.db import connect
from hephaestus.store.profiles import (
    create_profile,
    delete_profile,
    get_profile,
    list_profiles,
)


def make_db_path(tmp_path):
    return tmp_path / ".hephaestus" / "state.db"


def test_create_profile_returns_profile_with_generated_id(tmp_path):
    db_path = make_db_path(tmp_path)

    profile = create_profile(
        db_path,
        tmp_path,
        name="Architecture Lead",
        role="architect",
        rules=["S-001", "S-002"],
    )

    assert profile.agent_id == "arch-001"
    assert profile.name == "Architecture Lead"
    assert profile.role == "architect"
    assert profile.rules == ["S-001", "S-002"]
    assert profile.created_at.endswith("Z")


def test_agent_id_increments_per_role(tmp_path):
    db_path = make_db_path(tmp_path)

    first_arch = create_profile(db_path, tmp_path, "Architect One", "architect", [])
    first_worker = create_profile(db_path, tmp_path, "Worker One", "worker", [])
    second_arch = create_profile(db_path, tmp_path, "Architect Two", "architect", [])

    assert first_arch.agent_id == "arch-001"
    assert first_worker.agent_id == "work-001"
    assert second_arch.agent_id == "arch-002"


def test_list_profiles_returns_all(tmp_path):
    db_path = make_db_path(tmp_path)
    first = create_profile(db_path, tmp_path, "Architect One", "architect", ["S-001"])
    second = create_profile(db_path, tmp_path, "Worker One", "worker", ["S-002"])

    profiles = list_profiles(db_path)

    assert [profile.agent_id for profile in profiles] == [first.agent_id, second.agent_id]


def test_get_profile_returns_correct(tmp_path):
    db_path = make_db_path(tmp_path)
    created = create_profile(db_path, tmp_path, "QA One", "qa", ["S-003"])

    profile = get_profile(db_path, created.agent_id)

    assert profile == created


def test_get_profile_raises_keyerror_for_missing(tmp_path):
    db_path = make_db_path(tmp_path)
    with connect(db_path):
        pass

    with pytest.raises(KeyError):
        get_profile(db_path, "arch-999")


def test_delete_removes_profile(tmp_path):
    db_path = make_db_path(tmp_path)
    created = create_profile(db_path, tmp_path, "Worker One", "worker", [])

    delete_profile(db_path, created.agent_id)

    assert list_profiles(db_path) == []


def test_optional_fields_default_to_none(tmp_path):
    db_path = make_db_path(tmp_path)

    profile = create_profile(db_path, tmp_path, "Worker One", "worker", [])

    assert profile.model is None
    assert profile.effort is None
    assert profile.working_dir is None


def test_rules_roundtrip_as_list(tmp_path):
    db_path = make_db_path(tmp_path)
    rules = ["alpha", "beta", "gamma"]
    created = create_profile(db_path, tmp_path, "Worker One", "worker", rules)

    fetched = get_profile(db_path, created.agent_id)

    assert fetched.rules == rules


def test_identity_card_written_on_create(tmp_path):
    db_path = make_db_path(tmp_path)

    created = create_profile(db_path, tmp_path, "Architect One", "architect", ["S-001"])
    card_path = tmp_path / "agents" / "identities" / f"{created.agent_id}.json"

    assert card_path.exists()


def test_identity_card_has_correct_fields(tmp_path):
    db_path = make_db_path(tmp_path)

    created = create_profile(
        db_path,
        tmp_path,
        name="Orchestrator One",
        role="orchestrator",
        rules=["S-009"],
    )
    card_path = tmp_path / "agents" / "identities" / f"{created.agent_id}.json"

    payload = json.loads(card_path.read_text(encoding="utf-8"))

    assert payload == {
        "agent_id": created.agent_id,
        "name": "Orchestrator One",
        "role": "orchestrator",
        "created_at": created.created_at,
        "capabilities": ["write_handoff", "plan"],
        "sessions": [],
    }
