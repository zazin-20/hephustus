"""Identity card persistence for agent provenance."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from hephaestus.okf_layout import OKFLayout


@dataclass(slots=True)
class IdentityCard:
    agent_id: str
    name: str
    role: str
    created_at: str
    capabilities: list[str]
    sessions: list[dict]


def default_capabilities(role: str) -> list[str]:
    mapping = {
        "architect": ["write_spec", "write_handoff"],
        "worker": ["write_code", "run_tests"],
        "qa": ["write_qa_evidence"],
        "orchestrator": ["write_handoff", "plan"],
    }
    return list(mapping.get(role, []))


def write_card(okf_root: Path, card: IdentityCard) -> Path:
    path = _card_path(okf_root, card.agent_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(card), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def load_card(okf_root: Path, agent_id: str) -> IdentityCard:
    payload = json.loads(_card_path(okf_root, agent_id).read_text(encoding="utf-8"))
    return IdentityCard(**payload)


def append_session(okf_root: Path, agent_id: str, session: dict) -> None:
    card = load_card(okf_root, agent_id)
    card.sessions.append(session)
    write_card(okf_root, card)


def _card_path(okf_root: Path, agent_id: str) -> Path:
    return OKFLayout.for_existing_root(okf_root).identity_card_path(agent_id)
