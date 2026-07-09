---
title: Hephaestus Design Language
role: design-system
updated: 2026-07-09
owner: architect
---

# Hephaestus Design Language

This is the cornerstone design document for `agents/design-system/`.

This file is now the entrypoint to a linked design-language system. It should
stay short, directional, and easy to scan. Detailed rules live in the linked
documents below.

## What Hephaestus Is

Hephaestus is a graph-centered AI control plane.

It is the operating surface for authored AI systems whose runtime is expressed
as a graph of:

- nodes
- artifacts
- contracts
- gates
- traces
- corrections

It is not:

- a simple chat interface
- a generic workflow toy
- a soft enterprise dashboard

The product should let a user author, inspect, validate, run, pause, correct,
and learn from graph-based AI systems without losing visibility into what the
machine is doing.

Hephaestus should therefore feel:

- severe rather than friendly
- explicit rather than soft
- operational rather than decorative
- intelligent rather than magical
- inspectable rather than "trust us"

## Product Shape

The user should understand the application as:

1. A graph authoring surface
2. A graph runtime surface
3. A control-plane inventory
4. A governance and learning surface

## Design Direction

The chosen direction is:

**Cyber-brutalism for AI operations**

Our version is:

- brutalist in structure
- cybernetic in atmosphere
- editorial in hierarchy
- operational in tone

## Reading Order

Read the design language in this order:

1. [DESIGN_LANGUAGE.md](DESIGN_LANGUAGE.md)
   Start here for the product-level direction and document map.
2. [DESIGN_LANGUAGE_PRODUCT.md](DESIGN_LANGUAGE_PRODUCT.md)
   Product shape, hero surfaces, tone, and surface boundaries.
3. [DESIGN_LANGUAGE_VISUAL.md](DESIGN_LANGUAGE_VISUAL.md)
   Core principles, visual language, materials, density, and atmosphere.
4. [DESIGN_LANGUAGE_VOCABULARY.md](DESIGN_LANGUAGE_VOCABULARY.md)
   Product voice, naming rules, microcopy posture, and Hephaestus-themed language boundaries.
5. [DESIGN_LANGUAGE_INTERACTIONS.md](DESIGN_LANGUAGE_INTERACTIONS.md)
   Full interaction inventory and behavior rules.
6. [DESIGN_LANGUAGE_MOTION.md](DESIGN_LANGUAGE_MOTION.md)
   Motion principles, families, timings, easing, choreography, and animation mapping.
7. [DESIGN_LANGUAGE_STATUS.md](DESIGN_LANGUAGE_STATUS.md)
   Current gallery status, rollout order, anti-goals, and next steps.

## Companion Documents

Implementation-oriented companions:

- [DESIGN.md](DESIGN.md) for tokens and component guidance
- [component-gallery.html](component-gallery.html) for preview-only exploration

Authority order for this folder:

1. `DESIGN_LANGUAGE.md` and its linked language documents
2. `DESIGN.md`
3. preview files such as `component-gallery.html`

## Core Rule

The current [component-gallery.html](component-gallery.html) is a useful preview
surface, but its components are still **placeholders**. They demonstrate product
direction and interaction seams, not final reusable primitives.

Every reusable component in the gallery must be reworked through this linked
design-language system before it becomes the basis for frontend implementation.
