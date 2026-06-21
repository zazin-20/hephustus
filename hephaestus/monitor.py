"""Compliance monitor — stateful rescan + violation diff.

`ComplianceMonitor` is pure and watcher-agnostic: feed it `refresh()` calls from
any source (the file watcher, a manual "re-check" button, a test) and it reports
what changed since the last scan. This is the engine behind both compliance loops
in spec/architecture.md §3.3 / §6.3.

It rebuilds the OKF index on each refresh. At MVP scale (dozens of files) a full
rescan per debounced batch is negligible; incremental index updates (§6.1) are a
deferred optimization that won't change this interface.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hephaestus.core import Violation
from hephaestus.index import build_context
from hephaestus.rules.registry import run_all


def _key(v: Violation) -> tuple[str, str, str]:
    return (v.rule_id, v.artifact, v.message)


@dataclass(frozen=True)
class ViolationDelta:
    added: list[Violation]
    resolved: list[Violation]
    current: list[Violation]

    @property
    def changed(self) -> bool:
        return bool(self.added or self.resolved)


class ComplianceMonitor:
    def __init__(self, root: str | Path, enabled: set[str] | None = None):
        self.root = Path(root)
        self.enabled = enabled
        self._current: set[Violation] = set()

    @property
    def current(self) -> list[Violation]:
        return sorted(self._current, key=_key)

    def scan(self) -> list[Violation]:
        """Stateless full scan: Tier-1 schema errors + Tier-2 rule violations."""
        ctx = build_context(self.root)
        return run_all(ctx, enabled=self.enabled)

    def refresh(self) -> ViolationDelta:
        """Rescan and diff against the previous result, updating internal state."""
        new = set(self.scan())
        added = sorted(new - self._current, key=_key)
        resolved = sorted(self._current - new, key=_key)
        self._current = new
        return ViolationDelta(added=added, resolved=resolved, current=sorted(new, key=_key))
