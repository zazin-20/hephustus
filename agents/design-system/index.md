---
title: Design System
role: design-system
updated: 2026-07-09
owner: architect
---

# Design System

Navigation page for the Design System role.

Owns **design tokens and component/UI guidance** - not product scope. It defines
how the UI should look and behave so Workers implement against a shared language.

## Contents

| Path | Holds |
|---|---|
| `claude.md` | The Design System directive |
| `DESIGN_LANGUAGE.md` | The entrypoint and index for the linked design-language system |
| `DESIGN_LANGUAGE_PRODUCT.md` | Product shape, hero surfaces, tone, and surface boundaries |
| `DESIGN_LANGUAGE_VISUAL.md` | Direction, principles, visual language, materials, and atmosphere |
| `DESIGN_LANGUAGE_VOCABULARY.md` | Product voice, naming rules, copy posture, and thematic language boundaries |
| `DESIGN_LANGUAGE_INTERACTIONS.md` | Interaction inventory and behavior rules |
| `DESIGN_LANGUAGE_MOTION.md` | Motion system, families, timing, easing, and animation mapping |
| `DESIGN_LANGUAGE_STATUS.md` | Gallery status, rollout order, anti-goals, and next steps |
| `DESIGN.md` | Design tokens, component guidance, UI language |
| `log.md` | Design-system decisions and change history |
| _preview/reference files_ | Visual references and previews |

## Authority Order

When there is any ambiguity, read this folder in the following order:

1. `DESIGN_LANGUAGE.md` is the cornerstone and entrypoint to the canonical design-language system.
2. The linked `DESIGN_LANGUAGE_*` documents hold the detailed rules by topic.
3. `DESIGN.md` translates that direction into tokens and reusable component guidance.
4. Preview files such as `component-gallery.html` visualize the direction but do not override it.

## Current UI language

The frontend uses a dark **Tailwind v4** language in `frontend/src/`. Preserve it;
changes to design direction start in `DESIGN_LANGUAGE.md` and the linked
language documents, and token or component changes are described in `DESIGN.md`
before implementation.

Current direction:

- cyber-brutalism for AI operations
- graph-first command surfaces
- placeholder gallery to be refined into a true component library

See [../index.md](../index.md) for the full pipeline.
