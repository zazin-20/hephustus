---
title: Hephaestus Design Language - Interactions
role: design-system
updated: 2026-07-09
owner: architect
---

# Design Language - Interactions

Back to [DESIGN_LANGUAGE.md](DESIGN_LANGUAGE.md)

## Purpose

This document maps the interaction space of the current design system.

It covers:

- direct user actions
- immediate system responses
- persistent state changes the UI must make visible

If a component supports one of these interactions, the interaction should feel
consistent with the cyber-brutalist operating model.

## Interaction Inventory

### 1. Global Navigation And Orientation

Users can:

- switch between top-level surfaces or view tabs
- select any component from the gallery navigation
- filter the component navigation by typing
- scroll side rails, inspectors, code trees, and stacked evidence surfaces
- read sticky header context while navigating deeper content
- distinguish mounted vs unmounted surfaces

The system must show:

- current selection
- current location
- current filter effect
- whether a surface is available, deferred, or unmounted

### 2. View, Mode, And Scope Switching

Users can:

- switch between Author Mode and Run Mode
- switch between live snapshot and draft snapshot
- open and collapse legends
- toggle inventory vs template/update views
- toggle nodes vs artifacts catalogs
- toggle severity or status filters
- toggle live vs preview states
- move between pinned and live-follow inspection modes

The system must show:

- what mode the user is in
- what state changed because of the mode switch
- what controls are now active or inactive
- when a change affects only the current run vs the saved workflow

### 3. Selection, Focus, And Attention Control

Users can:

- select a node from a roster
- select a node on the canvas
- select a placement for inspection
- select an edge or edge-related surface
- select a toast action
- select a code tree entry
- select one surface among multiple summaries or rows

The system must show:

- one primary selection
- any secondary related selection
- whether the inspector is following live state or pinned state
- whether the inspected object is stale relative to the active runtime object

### 4. Expand, Collapse, And Reveal

Users can:

- open and close trace panels
- open and close trace rows
- expand and collapse context summaries
- expand and collapse file tree directories
- reveal or hide detailed evidence
- show or hide legends
- reveal correction modals and close them

The system must show:

- what is hidden vs expanded
- how much detail is available behind a collapsed summary
- whether expanded content is narrative, evidence, or configuration

### 5. Filtering, Toggling, And Inclusion Control

Users can:

- filter the gallery navigation by text
- toggle conversation turns into or out of context
- toggle rule pills on and off
- toggle catalog scopes such as nodes vs artifacts
- toggle severity views such as violations present vs all clear
- toggle readiness views such as green, mixed, and hard stop
- toggle edge-state simulations such as healthy, incompatible, missing input, and manual edit

The system must show:

- inclusion vs exclusion
- which toggles affect content, validation, or runtime behavior
- which toggles are simulation controls vs actual product controls

### 6. Creation, Authoring, And Editing

Users can:

- create or edit a node contract
- create or edit an artifact definition
- edit tags, prompts, headings, lists, providers, models, and working directories
- add and remove list items for skills, obligations, paths, and tools
- add and remove artifact bindings
- add and remove artifact heading rules
- choose required vs optional rules
- set minimum item counts for artifact predicates
- edit edge metadata such as advance mode, labels, and guard conditions

The system must show:

- which fields are editable
- which fields are reserved or intentionally disabled
- which edits alter runtime behavior
- which edits alter validation semantics
- which edits are still local draft changes

### 7. Graph Composition And Structural Editing

Users can:

- place nodes from a palette onto the canvas
- wire one placement to another
- choose which artifact flows through an edge
- choose allow vs ask edge behavior
- visually edit a wire presentation
- drag nodes to reposition them on the canvas
- observe live rerouting while dragging

The system must show:

- source and destination clearly
- artifact identity on the edge
- whether the graph is in authoring or runtime posture
- whether an edit is semantic or purely visual
- whether a graph is locked because a live run is active

### 8. Runtime Initiation And Execution Control

Users can:

- initiate a one-off agent run
- send a message to a selected node
- prefill a spawned task into the composer
- dismiss a spawn suggestion
- inspect run prompts
- inspect interactivity modes such as afk vs hitl
- observe a live output stream

The system must show:

- when execution starts
- what is currently running
- what is merely prepared but not yet executed
- what stream content is narrative, tool, thinking, or error

### 9. Preflight, Validation, And Compliance Review

Users can:

- inspect green, amber, and red readiness states
- inspect hard-stop failures
- inspect runnable-node lists
- inspect compatibility mismatches
- inspect missing input states
- inspect violations and suggested fixes
- inspect gate failures on spawnable work
- inspect blocked or degraded providers

The system must show:

- scope of the problem
- severity of the problem
- whether the problem blocks execution
- whether the problem can be overridden
- whether the problem belongs to authoring, runtime, or governance

### 10. Human Gates, Approval, And Override Actions

Users can:

- confirm an ask edge
- reject an ask edge
- provide a mandatory reject reason
- provide an optional note
- resume a paused workflow after revision
- inspect per-run override rationale

The system must show:

- whether human input is awaited
- whether the workflow is paused or resumed
- why a rejection occurred
- how the feedback will re-enter the next revision attempt
- that amber overrides are per run rather than permanently saved defaults

### 11. Context And Evidence Inspection

Users can:

- inspect assembled context summaries
- expand context into exact payload detail
- inspect transcript sections
- inspect trace and tool-call evidence
- inspect produced artifact details
- inspect gate checklists
- inspect prior related nodes or edges
- inspect copied conversation output
- inspect code browser file content

The system must show:

- what is summary vs exact payload
- what is transcript vs trace
- what is evidence vs interpretation
- what artifact or node the evidence belongs to

### 12. Correction And Learning Actions

Users can:

- open a correction action from a toast
- close a correction modal
- save a correction
- inspect pending correction candidates
- inspect frozen rules and their scope
- inspect provenance behind a learning
- inspect superseded or disabled rule history

The system must show:

- whether the interaction creates a candidate, a saved correction, or a promoted rule
- what scope the learning applies to
- what run or trace produced the learning
- whether the learning is active, superseded, or disabled

### 13. Inventory, Registry, And Library Management

Users can:

- browse typed inventory categories
- review provider or engine readiness
- inspect update-available markers
- inspect template placeholders
- inspect workflow-template update impact
- inspect reusable node and artifact definitions

The system must show:

- asset type
- readiness
- reuse status
- update status
- blocking unresolved placeholders

### 14. Destructive, Dismissive, And Exit Actions

Users can:

- delete a node card entry
- delete an artifact card entry
- remove chips and list items
- dismiss toasts
- cancel a node edit
- close modal overlays
- collapse expanded evidence

The system must show:

- what is being removed or dismissed
- whether the action is reversible
- whether the action is a local UI dismissal or a persistent deletion

## Interaction Behavior Rules

### Direct Manipulation Over Indirection

Whenever possible, users should act on the object itself:

- click the node
- inspect the edge
- toggle the rule pill
- drag the placement
- confirm the ask edge in place

Avoid forcing users into distant dialogs for interactions that belong directly
to the graph.

### One Primary Action Per Surface

Every surface should make the primary action obvious:

- node card: select
- spawn card: confirm or dismiss
- ask edge: confirm or reject
- trace row: expand
- artifact form: author and save

Secondary actions can exist, but they should not visually compete with the main
one.

### Visible Cause And Effect

Every user action should produce an immediate visible response:

- state change
- selection change
- reveal
- validation update
- toast
- stream event
- graph reroute

Silence after action should be treated as a design failure.

### State Must Survive Inspection

Interactions should not destroy user orientation.

If the user:

- pins an inspector
- expands context
- opens trace rows
- filters a list
- selects a node

the UI should preserve that state long enough for the user to reason about it.

### Runtime Interactions Must Feel Different From Authoring Interactions

The design must visually separate:

- editing a graph
- inspecting a running graph
- approving a runtime gate
- reviewing a violation
- authoring a contract

These are related behaviors, but they should not feel identical.
