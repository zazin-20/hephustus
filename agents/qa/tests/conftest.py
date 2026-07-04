"""Shared fixtures for the QA-owned test suite.

These tests are NOT on the default pytest ``testpaths`` (which is repo-root
``tests/`` only), so run them with an explicit path from the repo root::

    agents/.venv/Scripts/python.exe -m pytest agents/qa/tests -q

``hephaestus`` is importable because the shared venv has the package installed
editable — no ``sys.path`` surgery is needed.
"""
from __future__ import annotations

from pathlib import Path

import pytest

# agents/qa/tests/conftest.py -> parents[3] is the repo root that holds sample/.
REPO_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_ROOT = REPO_ROOT / "sample"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def sample_root() -> Path:
    """The read-only OKF fixture tree shipped in the repo."""
    assert SAMPLE_ROOT.is_dir(), f"sample tree missing at {SAMPLE_ROOT}"
    return SAMPLE_ROOT


@pytest.fixture
def sample_bridge(sample_root: Path):
    """A Bridge over the sample tree with NO app bound (read-only surface).

    With ``app=None`` the dashboard/codeview/pure methods still work; the
    store-backed node/thread methods raise ``RuntimeError`` (see TC-DESK-011).
    """
    from hephaestus.desktop import Bridge

    return Bridge(sample_root, [sample_root])


@pytest.fixture
def app(tmp_path: Path):
    """A DesktopApp over a fresh temp workspace (safe for writes).

    Constructing DesktopApp does not require pywebview (only ``.run()`` does),
    so store round-trips through the real Bridge work headless.
    """
    from hephaestus.desktop import DesktopApp

    return DesktopApp(tmp_path)
