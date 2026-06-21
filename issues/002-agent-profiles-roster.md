# 002 — Agent profiles → roster

**Type:** AFK · **Status:** ready-for-agent

## What to build

CRUD for **agent profiles** through a typed store DAL, exposed via the bridge and
surfaced in the Coordinator **roster** panel.

- Required fields: `name`, `role`, `rules`. Optional: `model`, `effort`, `working_dir`
  (NULL = whole workspace).
- `agent_id` auto-generated, role-prefixed, unique (e.g. `arch-001`).
- On create, write an A2A-shaped **identity card** to `agents/identities/{agent_id}.json`
  (the provenance anchor referenced by `authored_by`). Profile *config* lives in the
  store; profile *identity* lives in the card — linked by `agent_id`.
- Roster panel lists profiles with name, role, and a status badge.

Reference: `architecture-coordinator.md` §3, §4 (`profiles`).

## Acceptance criteria

- [ ] Create a profile from the UI; it persists and reappears after restart.
- [ ] `agent_id` is auto-generated, role-prefixed, and unique.
- [ ] Required fields enforced; optional fields default (`working_dir` NULL = workspace).
- [ ] Identity card written to `agents/identities/{agent_id}.json` with id/name/role/created_at/capabilities.
- [ ] Roster shows name, role, status badge; delete removes the profile.
- [ ] Tests: CRUD cycle, id generation, required-field enforcement, card written.

## Blocked by

- 001 — Workspace + operational store bootstrap
