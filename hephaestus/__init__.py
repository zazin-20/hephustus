"""Hephaestus — OKF system manager and agent compliance layer.

Phase 1 (MVP) core, built bottom-up:

    frontmatter  ->  models  ->  index (OKFContext)  ->  rules

The filesystem (`agents/` OKF tree) is the single source of truth; the in-memory
index is a derived read cache. See spec/architecture.md §6.
"""

__version__ = "0.2.0"
