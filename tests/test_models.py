from __future__ import annotations

import pytest
from pydantic import ValidationError

from hephaestus.models import OKFModel


def test_okf_model_allows_extra_fields():
    m = OKFModel.model_validate({"title": "x", "owner": "alice"})
    assert m.model_extra["owner"] == "alice"


def test_okf_model_subclass_enforces_required_fields():
    class Spec(OKFModel):
        id: str

    ok = Spec.model_validate({"id": "a", "owner": "alice"})  # extra allowed
    assert ok.id == "a"
    assert ok.model_extra["owner"] == "alice"

    with pytest.raises(ValidationError):
        Spec.model_validate({})  # missing required id
