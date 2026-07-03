from __future__ import annotations

from pathlib import Path

from hephaestus.artifact_spec import check_artifact, load_artifact_spec


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")
    return path


def test_artifact_spec_passes_valid_document(tmp_path):
    spec_path = _write(
        tmp_path / "prd-spec.md",
        """
        ---
        title: PRD
        owner: product
        ---
        ## Predicates
        - has_title()
        - has_field("owner")
        - has_problem_statement()

        ## Problem Statement
        Explain the user problem and why it matters.

        ## Good Looks Like
        Crisp scope, concrete user impact, and no placeholders.
        """,
    )
    artifact_path = _write(
        tmp_path / "prd.md",
        """
        ---
        title: Checkout improvements
        owner: alice
        ---
        ## Problem Statement
        Checkout abandonment is rising because saved addresses are unreliable.
        """,
    )

    spec = load_artifact_spec(spec_path)

    assert check_artifact(spec, artifact_path) == []


def test_artifact_spec_supports_predicate_library(tmp_path):
    spec_path = _write(
        tmp_path / "release-spec.md",
        """
        ---
        title: Release spec
        owner: product
        ---
        ## Predicates
        - has_field("owner")
        - has_section("Problem Statement")
        - non_empty("User Stories")
        - min_items("Release Criteria", 2)
        - matches("owner", "^[a-z]+$")

        ## Problem Statement
        Describe the user problem.

        ## User Stories
        Use concrete stories.

        ## Release Criteria
        List the shippable outcomes.

        ## Good Looks Like
        Concrete, specific, and ready to execute.
        """,
    )
    artifact_path = _write(
        tmp_path / "release.md",
        """
        ---
        title: Checkout reliability release
        owner: alice
        ---
        ## Problem Statement
        Users abandon checkout when address validation resets their forms.

        ## User Stories
        - As a shopper, I can keep my typed address when validation fails.

        ## Release Criteria
        - Saved addresses remain selected after validation errors.
        - Validation errors highlight only invalid fields.
        """,
    )

    spec = load_artifact_spec(spec_path)

    assert check_artifact(spec, artifact_path) == []


def test_artifact_spec_fails_trivial_sections_and_short_lists(tmp_path):
    spec_path = _write(
        tmp_path / "release-spec.md",
        """
        ---
        title: Release spec
        owner: product
        ---
        ## Predicates
        - has_problem_statement()
        - non_empty("User Stories")
        - min_items("Release Criteria", 2)
        - matches("owner", "^[a-z]+$")

        ## Problem Statement
        Describe the user problem.

        ## User Stories
        Use concrete stories.

        ## Release Criteria
        List the shippable outcomes.
        """,
    )
    artifact_path = _write(
        tmp_path / "release.md",
        """
        ---
        title: Checkout reliability release
        owner: TBD
        ---
        ## Problem Statement
        TBD

        ## User Stories
        - TBD

        ## Release Criteria
        - Saved addresses remain selected after validation errors.
        - TBD
        """,
    )

    spec = load_artifact_spec(spec_path)
    violations = check_artifact(spec, artifact_path)

    assert len(violations) == 4
    assert any("Problem Statement" in violation.message for violation in violations)
    assert any("User Stories" in violation.message for violation in violations)
    assert any("Release Criteria" in violation.message for violation in violations)
    assert any("owner" in violation.message for violation in violations)
