"""Catalog feeds the Coordinator form dropdowns — models grouped by provider,
with effort carried per-model. Sourced from the codex cache and `claude --help`,
so tests assert structure/invariants rather than a hardcoded model list."""

import json

import hephaestus.catalog as catalog_mod
import hephaestus.integration.providers as providers_mod
from hephaestus.catalog import catalog, discover_claude, discover_codex


def test_catalog_groups_models_by_provider():
    providers = {g["provider"] for g in catalog()["providers"]}
    assert "claude" in providers
    assert "codex" in providers


def test_every_model_carries_its_own_efforts():
    for group in catalog()["providers"]:
        for model in group["models"]:
            assert model["id"]
            assert isinstance(model["efforts"], list)


def test_claude_exposes_stable_aliases_with_effort():
    claude = discover_claude()
    ids = {m["id"] for m in claude["models"]}
    assert {"opus", "sonnet", "haiku", "fable"} <= ids
    # effort enum comes from `claude --help`; high is always offered
    assert all("high" in m["efforts"] for m in claude["models"])


def test_codex_reads_per_model_efforts_from_cache(tmp_path, monkeypatch):
    cache = tmp_path / "models_cache.json"
    cache.write_text(
        json.dumps(
            {
                "models": [
                    {
                        "slug": "gpt-5.4",
                        "display_name": "GPT-5.4",
                        "visibility": "list",
                        "supported_in_api": True,
                        "supported_reasoning_levels": [
                            {"effort": "low"},
                            {"effort": "high"},
                            {"effort": "xhigh"},
                        ],
                    },
                    {
                        "slug": "hidden-model",
                        "visibility": "hide",
                        "supported_in_api": True,
                        "supported_reasoning_levels": [],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(catalog_mod, "_CODEX_CACHE", cache)
    monkeypatch.setattr(providers_mod, "_CODEX_CACHE", cache)

    codex = discover_codex()
    ids = {m["id"] for m in codex["models"]}
    assert ids == {"gpt-5.4"}  # hidden model filtered out
    gpt = codex["models"][0]
    assert gpt["efforts"] == ["low", "high", "xhigh"]


def test_codex_falls_back_when_cache_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(catalog_mod, "_CODEX_CACHE", tmp_path / "nope.json")
    monkeypatch.setattr(providers_mod, "_CODEX_CACHE", tmp_path / "nope.json")
    codex = discover_codex()
    assert codex["provider"] == "codex"
    assert codex["models"]  # non-empty fallback
