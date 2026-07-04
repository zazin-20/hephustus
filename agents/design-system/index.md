---
title: Design System
role: design-system
updated: 2026-07-03
owner: architect
---

# Design System

Navigation page for the Design System role.

Owns **design tokens and component/UI guidance** — not product scope. It defines
how the UI should look and behave so Workers implement against a shared language.

## Contents

| Path | Holds |
|---|---|
| `claude.md` | The Design System directive |
| `DESIGN.md` | Design tokens, component guidance, UI language |
| _preview/reference files_ | Visual references and previews |

## Current UI language

The frontend uses a dark **Tailwind v4** language in `frontend/src/`. Preserve it;
changes to tokens or components are described in `DESIGN.md` first.

See [../index.md](../index.md) for the full pipeline.
