---
title: Worker Mocking Conventions
role: worker
updated: 2026-07-03
owner: architect
---

# Worker — Mocking & Fixture Conventions

How to fake dependencies without hiding real behavior.

## Principles

- Prefer real objects and `tmp_path` fixtures over mocks where cheap.
- Mock only at seams you own: the DB entry point
  (`hephaestus.store.db.connect(path)`), external CLIs (Codex, gh), and network.
- Use `dumps_json` / `loads_json` from `hephaestus.store.db` for JSON columns
  rather than hand-rolled serialization in tests.
- In browser-preview mode without `window.pywebview`, the UI falls back to mock
  data — keep that fallback path working.

## Do not

- Do not mock the unit under test.
- Do not assert on mock internals when a behavioral assertion is available.
