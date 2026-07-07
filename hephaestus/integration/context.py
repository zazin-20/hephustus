"""OKF context assembly for a node run."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hephaestus.integration.routing import TAG_DIRECTIVE
from hephaestus.skills import resolve_skill_refs
from hephaestus.integration.turns import describe_turn
from hephaestus.okf_layout import OKFLayout
from hephaestus.store.artifacts import get_artifact
from hephaestus.store.frozen_rules import ScopeAddress, list_frozen_rules_for_address
from hephaestus.store.threads import compile_context

_ISSUE_CONSUMER_TAGS = {"worker", "qa", "architect"}


@dataclass(frozen=True)
class SessionContext:
    node_id: str
    tags: list[str]
    issue_id: str | None
    files: list[Path]      # existing files injected
    missing: list[Path]    # referenced but absent (surfaced, not fatal)
    system_prompt: str


def _resolve_declared_path(
    layout: OKFLayout,
    declared: str,
    *,
    db_path: str | Path | None = None,
) -> Path:
    if db_path is not None:
        try:
            artifact = get_artifact(db_path, declared)
        except KeyError:
            pass
        else:
            return _resolve_declared_path(layout, artifact.path)
    return _resolve_literal_path(layout, declared)


def _resolve_literal_path(layout: OKFLayout, declared: str) -> Path:
    path = Path(declared)
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "agents":
        return layout.workspace_root / path
    return layout.resolve(path)


def _candidate_paths(
    layout: OKFLayout,
    db_path: str | Path | None,
    tags: list[str],
    issue_id: str | None,
    skills: list[str],
    inputs: list[str],
    outputs: list[str],
) -> tuple[list[Path], list[Path], list[Path], list[Path]]:
    constitution_paths: list[Path] = []
    for tag in tags:
        relative = TAG_DIRECTIVE.get(tag)
        if relative is not None:
            constitution_paths.append(layout.resolve(relative))
    if "worker" in tags:
        constitution_paths.append(layout.worker_tdd_path())

    skill_paths = [skill.path for skill in resolve_skill_refs(layout, skills)]
    input_paths = [_resolve_declared_path(layout, declared, db_path=db_path) for declared in inputs]
    if issue_id and _ISSUE_CONSUMER_TAGS.intersection(tags):
        input_paths.append(layout.issue_path(issue_id))

    spec_paths = [_resolve_declared_path(layout, declared, db_path=db_path) for declared in outputs]
    return constitution_paths, skill_paths, input_paths, spec_paths


def _render_file_contents(root: Path, files: list[Path]) -> list[str]:
    parts: list[str] = []
    for p in files:
        try:
            rel = p.relative_to(root).as_posix()
        except ValueError:
            rel = p.name
        parts.append(f"## {rel}\n{p.read_text(encoding='utf-8').strip()}")
    return parts


def _render_section(root: Path, heading: str, files: list[Path]) -> str:
    if not files:
        return ""
    parts = [f"# {heading}"]
    parts.extend(_render_file_contents(root, files))
    return "\n\n".join(parts)


def _render_constitution(
    root: Path,
    files: list[Path],
    *,
    db_path: str | Path | None,
    machine: str,
    workflow_id: str | None,
    workflow_run_id: str | None,
    placement_id: str | None,
    node_id: str,
    tags: list[str],
) -> str:
    parts = _render_file_contents(root, files)
    if db_path is not None:
        rules = list_frozen_rules_for_address(
            db_path,
            ScopeAddress(
                machine=machine,
                workflow_id=workflow_id,
                workflow_run_id=workflow_run_id,
                placement_id=placement_id,
                node_id=node_id,
                tags=tags,
            ),
        )
        for rule in rules:
            if rule.kind != "directive":
                continue
            parts.append(f"## {rule.scope}:{rule.topic_key}\n{rule.body}")
    if not parts:
        return ""
    return "\n\n".join(["# Constitution", *parts])


def _render_skills(root: Path, files: list[Path]) -> str:
    return _render_section(root, "Skills", files)


def _render_replay(db_path: str | Path | None, thread_id: str | None) -> str:
    if db_path is None or thread_id is None:
        return ""

    lines: list[str] = []
    for turn in compile_context(db_path, thread_id):
        descriptor = describe_turn(turn.kind, role=turn.role)
        if not descriptor.conversation and turn.role != "tool":
            continue
        if not turn.text.strip():
            continue
        label = descriptor.transcript_role or turn.role
        lines.append(f"{label}: {turn.text}")

    if not lines:
        return ""
    return "\n\n".join(["# Prior context", *lines])


def build_session_context(
    root: str | Path,
    *,
    node_id: str,
    tags: list[str],
    issue_id: str | None = None,
    skills: list[str] | None = None,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    db_path: str | Path | None = None,
    workflow_id: str | None = None,
    workflow_run_id: str | None = None,
    placement_id: str | None = None,
    thread_id: str | None = None,
    machine: str | None = None,
) -> SessionContext:
    render_root = Path(root)
    layout = OKFLayout.for_existing_root(render_root)

    constitution_candidates, skill_candidates, input_candidates, spec_candidates = _candidate_paths(
        layout,
        db_path,
        tags,
        issue_id,
        list(skills or []),
        list(inputs or []),
        list(outputs or []),
    )
    candidates = constitution_candidates + skill_candidates + input_candidates + spec_candidates
    files = [p for p in candidates if p.is_file()]
    missing = [p for p in candidates if not p.is_file()]

    constitution_files = [p for p in constitution_candidates if p.is_file()]
    skill_files = [p for p in skill_candidates if p.is_file()]
    input_files = [p for p in input_candidates if p.is_file()]
    spec_files = [p for p in spec_candidates if p.is_file()]

    sections = [
        _render_constitution(
            render_root,
            constitution_files,
            db_path=db_path,
            machine=machine or str(render_root.resolve()),
            workflow_id=workflow_id,
            workflow_run_id=workflow_run_id,
            placement_id=placement_id,
            node_id=node_id,
            tags=tags,
        ),
        _render_skills(render_root, skill_files),
        _render_section(render_root, "Input artifacts", input_files),
        _render_section(render_root, "Artifact specs", spec_files),
        _render_replay(db_path, thread_id),
    ]

    return SessionContext(
        node_id=node_id,
        tags=list(tags),
        issue_id=issue_id,
        files=files,
        missing=missing,
        system_prompt="\n\n".join(section for section in sections if section),
    )
