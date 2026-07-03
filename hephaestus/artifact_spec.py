"""ArtifactSpec loading and deterministic predicate checking.

User-authored artifact specs are markdown documents with:

- YAML frontmatter for short scalar metadata
- `##` sections for prose/list content
- a `## Predicates` section listing shipped predicate calls
- a `## Good Looks Like` section with exemplars for generators

This module loads those specs and evaluates their predicates against another
artifact document through the shared rule registry.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from hephaestus.core import Severity, Violation, ViolationResult
from hephaestus.eval_context import EvaluationContext
from hephaestus.frontmatter import ParsedDocument, load
from hephaestus.index import OKFContext
from hephaestus.rules.base import HephaestusRule
from hephaestus.rules.registry import run_rules

_SECTION_RE = re.compile(r"^\s*##\s+(?P<title>.+?)\s*$")
_BULLET_RE = re.compile(r"^\s*-\s+(?P<expr>.+?)\s*$")
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+\.\s+)(?P<item>.+?)\s*$")
_NON_WORD_RE = re.compile(r"[^a-z0-9]+")
_TRIVIAL_VALUES = {
    "",
    "tbd",
    "todo",
    "none",
    "n/a",
    "na",
    "placeholder",
}


@dataclass(frozen=True)
class MarkdownArtifact:
    parsed: ParsedDocument
    sections: dict[str, str]


@dataclass(frozen=True)
class ArtifactSpec:
    path: Path
    document: MarkdownArtifact
    predicates: list["ArtifactPredicate"]
    good_looks_like: str


class ArtifactPredicate:
    def label(self) -> str:
        raise NotImplementedError

    def describe_failure(self, artifact: MarkdownArtifact) -> str:
        raise NotImplementedError

    def passes(self, artifact: MarkdownArtifact) -> bool:
        raise NotImplementedError


@dataclass(frozen=True)
class HasFieldPredicate(ArtifactPredicate):
    name: str

    def label(self) -> str:
        return f'has_field("{self.name}")'

    def describe_failure(self, artifact: MarkdownArtifact) -> str:
        return f'Artifact is missing non-trivial frontmatter field "{self.name}".'

    def passes(self, artifact: MarkdownArtifact) -> bool:
        value = _resolve_field(artifact, self.name)
        return _is_non_trivial(value)


@dataclass(frozen=True)
class HasSectionPredicate(ArtifactPredicate):
    name: str

    def label(self) -> str:
        return f'has_section("{self.name}")'

    def describe_failure(self, artifact: MarkdownArtifact) -> str:
        return f'Artifact is missing non-trivial section "{self.name}".'

    def passes(self, artifact: MarkdownArtifact) -> bool:
        value = _resolve_section(artifact, self.name)
        return _is_non_trivial(value)


@dataclass(frozen=True)
class HasValuePredicate(ArtifactPredicate):
    name: str

    def label(self) -> str:
        return f"has_{_normalize_name(self.name)}()"

    def describe_failure(self, artifact: MarkdownArtifact) -> str:
        label = _display_name(self.name)
        return (
            f'Artifact is missing non-trivial field or section matching "{label}".'
        )

    def passes(self, artifact: MarkdownArtifact) -> bool:
        value = _resolve_value(artifact, self.name)
        return _is_non_trivial(value)


@dataclass(frozen=True)
class NonEmptyPredicate(ArtifactPredicate):
    target: str

    def label(self) -> str:
        return f'non_empty("{self.target}")'

    def describe_failure(self, artifact: MarkdownArtifact) -> str:
        return f'Artifact target "{self.target}" must be present and non-trivial.'

    def passes(self, artifact: MarkdownArtifact) -> bool:
        value = _resolve_value(artifact, self.target)
        return _is_non_trivial(value)


@dataclass(frozen=True)
class MinItemsPredicate(ArtifactPredicate):
    target: str
    minimum: int

    def label(self) -> str:
        return f'min_items("{self.target}", {self.minimum})'

    def describe_failure(self, artifact: MarkdownArtifact) -> str:
        return (
            f'Artifact target "{self.target}" must contain at least {self.minimum} '
            "non-trivial list items."
        )

    def passes(self, artifact: MarkdownArtifact) -> bool:
        value = _resolve_value(artifact, self.target)
        return _count_items(value) >= self.minimum


@dataclass(frozen=True)
class MatchesPredicate(ArtifactPredicate):
    target: str
    pattern: str

    def label(self) -> str:
        return f'matches("{self.target}", "{self.pattern}")'

    def describe_failure(self, artifact: MarkdownArtifact) -> str:
        return f'Artifact target "{self.target}" must match /{self.pattern}/.'

    def passes(self, artifact: MarkdownArtifact) -> bool:
        value = _resolve_value(artifact, self.target)
        if not _is_non_trivial(value):
            return False
        text = _stringify(value)
        return re.search(self.pattern, text, flags=re.MULTILINE) is not None


class _PredicateRule(HephaestusRule):
    layer = "exit"
    scope = "artifact"
    severity = Severity.ERROR

    def __init__(self, *, index: int, predicate: ArtifactPredicate, artifact: MarkdownArtifact):
        self.id = f"A-{index:03d}"
        self.name = predicate.label()
        self.fix_hint = f"Update the artifact so `{predicate.label()}` passes."
        self._predicate = predicate
        self._artifact = artifact

    def check(self, ctx) -> ViolationResult:
        if self._predicate.passes(self._artifact):
            return ViolationResult.of([])
        path = self._artifact.parsed.path
        return ViolationResult.of(
            [
                Violation(
                    rule_id=self.id,
                    severity=self.severity,
                    message=self._predicate.describe_failure(self._artifact),
                    artifact=str(path) if path is not None else "",
                    fix_hint=self.fix_hint,
                )
            ]
        )


def load_artifact_spec(path: str | Path) -> ArtifactSpec:
    spec_path = Path(path)
    artifact = _load_markdown_artifact(spec_path)
    predicates_text = artifact.sections.get("Predicates", "")
    predicates = [_parse_predicate(expr) for expr in _extract_predicate_lines(predicates_text)]
    return ArtifactSpec(
        path=spec_path,
        document=artifact,
        predicates=predicates,
        good_looks_like=artifact.sections.get("Good Looks Like", ""),
    )


def check_artifact(spec: ArtifactSpec, artifact_path: str | Path) -> list[Violation]:
    artifact = _load_markdown_artifact(artifact_path)
    okf = OKFContext(root=artifact.parsed.path.parent if artifact.parsed.path else Path("."))
    ctx = EvaluationContext(okf=okf)
    rules = [
        _PredicateRule(index=index, predicate=predicate, artifact=artifact)
        for index, predicate in enumerate(spec.predicates, start=1)
    ]
    return run_rules(ctx, rules=rules)


def _load_markdown_artifact(path: str | Path) -> MarkdownArtifact:
    parsed = load(path)
    return MarkdownArtifact(parsed=parsed, sections=_parse_sections(parsed.body))


def _parse_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    buffer: list[str] = []
    for line in body.splitlines():
        match = _SECTION_RE.match(line)
        if match:
            if current is not None:
                sections[current] = "\n".join(buffer).strip()
            current = match.group("title").strip()
            buffer = []
            continue
        if current is not None:
            buffer.append(line)
    if current is not None:
        sections[current] = "\n".join(buffer).strip()
    return sections


def _extract_predicate_lines(section_text: str) -> list[str]:
    expressions: list[str] = []
    for line in section_text.splitlines():
        match = _BULLET_RE.match(line)
        if match:
            expressions.append(match.group("expr"))
    return expressions


def _parse_predicate(expr: str) -> ArtifactPredicate:
    try:
        node = ast.parse(expr, mode="eval").body
    except SyntaxError as exc:
        raise ValueError(f"Invalid predicate expression: {expr}") from exc
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
        raise ValueError(f"Predicate must be a function call: {expr}")
    name = node.func.id
    args = [_literal_argument(arg, expr) for arg in node.args]
    if name == "has_field":
        _expect_arity(name, args, 1)
        return HasFieldPredicate(_expect_string(name, args[0]))
    if name == "has_section":
        _expect_arity(name, args, 1)
        return HasSectionPredicate(_expect_string(name, args[0]))
    if name == "non_empty":
        _expect_arity(name, args, 1)
        return NonEmptyPredicate(_expect_string(name, args[0]))
    if name == "min_items":
        _expect_arity(name, args, 2)
        return MinItemsPredicate(
            _expect_string(name, args[0]),
            _expect_int(name, args[1]),
        )
    if name == "matches":
        _expect_arity(name, args, 2)
        return MatchesPredicate(
            _expect_string(name, args[0]),
            _expect_string(name, args[1]),
        )
    if name.startswith("has_"):
        _expect_arity(name, args, 0)
        return HasValuePredicate(name[4:])
    raise ValueError(f"Unsupported predicate function: {name}")


def _literal_argument(node: ast.AST, expr: str):
    try:
        return ast.literal_eval(node)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Predicate arguments must be literals: {expr}") from exc


def _expect_arity(name: str, args: list[object], expected: int) -> None:
    if len(args) != expected:
        raise ValueError(f"{name} expects {expected} arguments, got {len(args)}")


def _expect_string(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} expects string arguments")
    return value


def _expect_int(name: str, value: object) -> int:
    if not isinstance(value, int):
        raise ValueError(f"{name} expects an integer minimum")
    return value


def _resolve_field(artifact: MarkdownArtifact, target: str):
    wanted = _normalize_name(target)
    for key, value in artifact.parsed.frontmatter.items():
        if _normalize_name(str(key)) == wanted:
            return value
    return None


def _resolve_section(artifact: MarkdownArtifact, target: str):
    wanted = _normalize_name(target)
    for name, value in artifact.sections.items():
        if _normalize_name(name) == wanted:
            return value
    return None


def _resolve_value(artifact: MarkdownArtifact, target: str):
    field = _resolve_field(artifact, target)
    if field is not None:
        return field
    return _resolve_section(artifact, target)


def _normalize_name(value: str) -> str:
    return _NON_WORD_RE.sub("_", value.strip().lower()).strip("_")


def _display_name(value: str) -> str:
    return " ".join(part.capitalize() for part in _normalize_name(value).split("_"))


def _normalize_text(value: str) -> str:
    lines = []
    for raw in value.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        list_match = _LIST_ITEM_RE.match(stripped)
        if list_match:
            stripped = list_match.group("item").strip()
        lines.append(stripped)
    return " ".join(lines).strip().lower()


def _is_non_trivial(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        normalized = _normalize_text(value)
        return normalized not in _TRIVIAL_VALUES
    if isinstance(value, (list, tuple, set)):
        return any(_is_non_trivial(item) for item in value)
    if isinstance(value, dict):
        return any(_is_non_trivial(item) for item in value.values())
    return True


def _count_items(value) -> int:
    if isinstance(value, (list, tuple, set)):
        return sum(1 for item in value if _is_non_trivial(item))
    if isinstance(value, str):
        return sum(
            1
            for line in value.splitlines()
            if (match := _LIST_ITEM_RE.match(line)) and _is_non_trivial(match.group("item"))
        )
    return 0


def _stringify(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple, set)):
        return "\n".join(str(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(f"{key}: {val}" for key, val in value.items())
    return str(value)
