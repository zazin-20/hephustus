"""Identity card persistence for agent provenance."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from hephaestus.okf_layout import OKFLayout


@dataclass(slots=True)
class IdentityCard:
    node_id: str
    name: str
    tags: list[str]
    created_at: str
    capabilities: list[str]
    sessions: list[dict]


def default_capabilities(tags: list[str] | str) -> list[str]:
    tag_list = [tags] if isinstance(tags, str) else list(tags)
    mapping = {
        "architect": ["write_spec", "write_handoff"],
        "worker": ["write_code", "run_tests"],
        "qa": ["write_qa_evidence"],
        "orchestrator": ["plan", "write_handoff"],
        "planner": ["plan"],
    }
    capabilities: list[str] = []
    for tag in tag_list:
        for capability in mapping.get(tag, []):
            if capability not in capabilities:
                capabilities.append(capability)
    return capabilities


def write_card(okf_root: Path, card: IdentityCard) -> Path:
    path = _card_path(okf_root, card.node_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(card), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def load_card(okf_root: Path, node_id: str) -> IdentityCard:
    payload = json.loads(_card_path(okf_root, node_id).read_text(encoding="utf-8"))
    return IdentityCard(**payload)


def append_session(okf_root: Path, node_id: str, session: dict) -> None:
    card = load_card(okf_root, node_id)
    card.sessions.append(session)
    write_card(okf_root, card)


def _card_path(okf_root: Path, node_id: str) -> Path:
    return OKFLayout.for_existing_root(okf_root).identity_card_path(node_id)
