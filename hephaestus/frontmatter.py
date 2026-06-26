"""YAML frontmatter parsing for OKF markdown documents.

REUSABLE — the artifact-spec layout (frontmatter scalars + named `## Sections`)
parses through here; the predicate library checks against the result.


Deliberately small and self-contained (uses PyYAML directly) so it can be swapped
for the `python-frontmatter` package later without touching callers — see
spec/architecture.md §8.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_FENCE = "---"


class FrontmatterError(ValueError):
    def __init__(self, message: str, path: Path | None = None):
        self.path = path
        super().__init__(f"{path}: {message}" if path else message)


@dataclass(frozen=True)
class ParsedDocument:
    frontmatter: dict
    body: str
    path: Path | None = None


def parse(text: str, path: Path | None = None) -> ParsedDocument:
    """Split markdown text into (frontmatter dict, body).

    Documents with no leading `---` fence are treated as all-body with empty
    frontmatter (e.g. an append-only prose log).
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FENCE:
        return ParsedDocument(frontmatter={}, body=text, path=path)

    for i in range(1, len(lines)):
        if lines[i].strip() == _FENCE:
            raw = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1:])
            try:
                data = yaml.safe_load(raw) or {}
            except yaml.YAMLError as exc:
                raise FrontmatterError(f"invalid YAML frontmatter: {exc}", path) from exc
            if not isinstance(data, dict):
                raise FrontmatterError(
                    f"frontmatter must be a mapping, got {type(data).__name__}", path
                )
            return ParsedDocument(frontmatter=data, body=body, path=path)

    raise FrontmatterError("unterminated frontmatter fence", path)


def load(path: str | Path) -> ParsedDocument:
    p = Path(path)
    return parse(p.read_text(encoding="utf-8"), path=p)
