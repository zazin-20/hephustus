"""The OKF index — a derived read cache over the `agents/` tree.

REUSABLE — generic artifact-store reader. `build_context` scans the tree and
returns an `OKFContext` (parsed documents + schema load errors) that rules/gates
read from; nothing here touches the issue-lifecycle. The hardcoded typed
collections (issues/handoffs/qa/log) were removed when governance moved to
user-authored specs — the scan→parse→collect-errors mechanism (and the
disk-is-never-touched-by-rules property, spec/architecture.md §6.1) is what's
kept. See docs/design/governance-engine.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from hephaestus.core import Severity, Violation
from hephaestus.frontmatter import FrontmatterError, ParsedDocument, load
from hephaestus.okf_layout import OKFLayout


@dataclass
class OKFContext:
    """A read-only view of the OKF tree: parsed documents + schema load errors."""

    root: Path
    documents: list[ParsedDocument] = field(default_factory=list)
    load_errors: list[Violation] = field(default_factory=list)


def build_context(root: str | Path) -> OKFContext:
    """Build an OKFContext from a repo root or an `agents/` directory directly.

    Every markdown file under the agents tree is parsed for frontmatter. Files with
    no frontmatter fence are kept as all-body documents (not errors); only a
    malformed frontmatter fence becomes a `schema` load error.
    """
    root = Path(root)
    layout = OKFLayout.for_existing_root(root)
    documents: list[ParsedDocument] = []
    errors: list[Violation] = []

    agents = layout.agents_root
    if agents.is_dir():
        for path in sorted(agents.rglob("*.md")):
            try:
                documents.append(load(path))
            except FrontmatterError as exc:
                errors.append(
                    Violation(
                        rule_id="schema",
                        severity=Severity.ERROR,
                        message=str(exc),
                        artifact=str(path),
                        fix_hint="Fix the frontmatter so it is a valid, terminated YAML mapping.",
                    )
                )

    return OKFContext(root=root, documents=documents, load_errors=errors)
