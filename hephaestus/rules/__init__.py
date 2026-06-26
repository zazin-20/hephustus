"""Compliance rule engine.

REUSABLE — generic gate engine: `base` (the check interface), `registry` (the
runner), `governance` (the kept G-rules). There is no built-in structural rule
set anymore; user-authored rules/predicates are passed in. See
docs/design/governance-engine.md.
"""
