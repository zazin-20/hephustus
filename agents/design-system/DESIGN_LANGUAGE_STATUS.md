---
title: Hephaestus Design Language - Status
role: design-system
updated: 2026-07-09
owner: architect
---

# Design Language - Status

Back to [DESIGN_LANGUAGE.md](DESIGN_LANGUAGE.md)

## Current Status

[component-library.html](component-library.html) is the canonical component
library, rebuilt through this design language (2026-07-09). It contains 41
interactive units across ten groups and implements:

- the DESIGN.md token layer as live CSS custom properties
- hard-geometry surfaces, the surface ladder, HUD framing, scanline and
  wireframe-ground textures, and caution striping
- the motion families from DESIGN_LANGUAGE_MOTION.md as working CSS with the
  documented timing bands and family-aware reduced-motion behavior
- vocabulary-compliant status copy and restrained Hephaestus theming
- a per-component spec readout listing the tokens and motion families used

The older [component-gallery.html](component-gallery.html) remains an
exploration sandbox only. It predates the language and must not be used as an
implementation reference.

## What Must Happen Next

1. Review the library in a browser and file any seam-level corrections here
2. Extract the library's patterns into React + Tailwind v4 primitives in
   `frontend/src/` (Worker scope, guided by this library)
3. Keep the library and `frontend/src/` in lockstep: token or component
   changes land here first, then ship

## Recommended Rollout Order

Apply the language in this order:

1. Shell and global frame
2. Workflow canvas shell
3. Runtime nodes and artifact edges
4. Node drill-in inspector
5. Preflight dock
6. Context preview
7. Authoring forms and contract editors
8. Library and learning surfaces

## Anti-Goals

We are not building:

- a pastel AI app
- a purple-gradient productivity SaaS
- a generic node editor
- a friendly assistant chat product
- a soft enterprise dashboard
- an ironic retro-brutalist novelty

## Reference

Primary aesthetic reference for this phase:

- Nat Currier, "Brutalist Design Principles - Raw, Functional, and Unapologetic"
  https://nat.io/blog/brutalist-design-principles

Hephaestus is not copying that article literally. We are adapting its design
principles into a cyber-brutalist visual system appropriate for a graph-native
AI control plane.
