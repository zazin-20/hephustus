from __future__ import annotations

from hephaestus.artifact_spec import load_artifact_spec
from hephaestus.store.artifacts import (
    ArtifactHeading,
    create_artifact,
    delete_artifact,
    get_artifact,
    list_artifacts,
    update_artifact,
)


def make_db_path(tmp_path):
    return tmp_path / ".hephaestus" / "state.db"


def test_artifact_dal_round_trips_and_composes_parseable_markdown(tmp_path):
    db_path = make_db_path(tmp_path)

    created = create_artifact(
        db_path,
        name="Release Checklist",
        tags=["release", "qa"],
        headings=[
            ArtifactHeading(heading="Acceptance Criteria", required=True, min_items=2),
            ArtifactHeading(heading="Rollout Plan", required=False, min_items=None),
        ],
        good_looks_like="Concrete, scoped, and testable.",
        antipatterns="Hand-wavy requirements.",
        examples="- Validate saved-address recovery.\n- Validate rollback steps.",
    )

    assert created.artifact_id == "artifact-001"
    assert created.path == "agents/artifacts/artifact-001.md"
    assert created.name == "Release Checklist"
    assert created.tags == ["release", "qa"]
    assert [heading.heading for heading in created.headings] == ["Acceptance Criteria", "Rollout Plan"]
    assert created.headings[0].required is True
    assert created.headings[0].min_items == 2
    assert created.created_at.endswith("Z")

    stored = get_artifact(db_path, created.artifact_id)
    listed = list_artifacts(db_path)
    spec = load_artifact_spec(tmp_path / created.path)

    assert stored == created
    assert listed == [created]
    assert [predicate.label() for predicate in spec.predicates] == [
        'has_section("Acceptance Criteria")',
        'non_empty("Acceptance Criteria")',
        'min_items("Acceptance Criteria", 2)',
    ]
    assert spec.good_looks_like == "Concrete, scoped, and testable."

    updated = update_artifact(
        db_path,
        created.artifact_id,
        name="Release Contract",
        tags=["release"],
        headings=[
            ArtifactHeading(heading="Acceptance Criteria", required=True, min_items=3),
            ArtifactHeading(heading="QA Notes", required=True, min_items=None),
        ],
        good_looks_like="Specific and ready to ship.",
        antipatterns="Missing examples.",
        examples="- Example artifact payload.",
    )

    assert updated.artifact_id == created.artifact_id
    assert updated.path == created.path
    assert updated.name == "Release Contract"
    assert updated.tags == ["release"]
    assert [heading.heading for heading in updated.headings] == ["Acceptance Criteria", "QA Notes"]
    assert updated.headings[0].min_items == 3
    assert updated.headings[1].required is True

    deleted = delete_artifact(db_path, created.artifact_id)

    assert deleted == updated
    assert list_artifacts(db_path) == []
    assert not (tmp_path / created.path).exists()
