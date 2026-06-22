"""Provider-sourced model + effort catalog for the Coordinator form.

Deliberately not hardcoded:
  - Codex models come from the codex CLI's own local cache
    (~/.codex/models_cache.json) — it refreshes that file itself, and it carries
    per-model reasoning levels.
  - Claude effort levels are read from `claude --help` (the `--effort` enum).
  - Claude models are exposed as the stable public aliases (opus/sonnet/haiku/
    fable). The server resolves each to the latest model, so they never go stale
    and need no API key (the claude CLI authenticates via OAuth, not a key).

Effort is per-model: Codex carries each model's `supported_reasoning_levels`;
Claude shares one flat effort list across its aliases (the `--effort` flag is a
session-level setting, not a per-model capability in the CLI path).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from hephaestus.integration.routing import Tool

_CODEX_CACHE = Path.home() / ".codex" / "models_cache.json"

# Stable public aliases; the server resolves each to the current model.
_CLAUDE_ALIASES = [
    ("opus", "Opus (latest)"),
    ("sonnet", "Sonnet (latest)"),
    ("haiku", "Haiku (latest)"),
    ("fable", "Fable (latest)"),
]
_CLAUDE_EFFORT_FALLBACK = ["low", "medium", "high", "xhigh", "max"]
_CODEX_MODEL_FALLBACK = [
    {"id": "gpt-5.4", "label": "GPT-5.4", "efforts": ["low", "medium", "high", "xhigh"]},
]


def _claude_efforts() -> list[str]:
    """Parse the effort enum from `claude --help` (`--effort <level> (a, b, ...)`)."""
    claude = shutil.which("claude")
    if claude:
        try:
            out = subprocess.run(
                [claude, "--help"], capture_output=True, text=True, timeout=10
            ).stdout
            match = re.search(r"--effort\s+<level>.*?\(([^)]*)\)", out, re.S)
            if match:
                levels = [x.strip() for x in match.group(1).split(",") if x.strip()]
                if levels:
                    return levels
        except Exception:
            pass
    return list(_CLAUDE_EFFORT_FALLBACK)


def discover_claude() -> dict:
    efforts = _claude_efforts()
    models = [
        {"id": alias, "label": label, "efforts": list(efforts)}
        for alias, label in _CLAUDE_ALIASES
    ]
    return {"provider": Tool.CLAUDE.value, "models": models}


def discover_codex() -> dict:
    try:
        data = json.loads(_CODEX_CACHE.read_text(encoding="utf-8"))
        models = []
        for m in data.get("models", []):
            if m.get("visibility") != "list" or not m.get("supported_in_api"):
                continue
            efforts = [
                e["effort"]
                for e in m.get("supported_reasoning_levels", [])
                if e.get("effort")
            ]
            models.append(
                {
                    "id": m["slug"],
                    "label": m.get("display_name") or m["slug"],
                    "efforts": efforts,
                }
            )
        if models:
            return {"provider": Tool.CODEX.value, "models": models}
    except Exception:
        pass
    return {"provider": Tool.CODEX.value, "models": list(_CODEX_MODEL_FALLBACK)}


def catalog() -> dict:
    """Serializable catalog for the bridge: providers -> models -> per-model efforts."""
    return {"providers": [discover_claude(), discover_codex()]}
