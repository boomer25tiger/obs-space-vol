"""S24B, DECISIONS item 163. Guard the promoted copies against drift.

`artifacts/` holds the files the paper, its tables, its figures and its tests
read. Each is a copy of a file under `sessions/*/results/`, which stays tracked as
the audit trail. Two copies of a file can diverge, and a divergence here would put
a figure in the paper that no longer matches the run that produced it. This test
fails if any promoted copy stops being byte-identical to its origin.
"""
import hashlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"


def _digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _pairs():
    for copy in sorted(ARTIFACTS.rglob("*")):
        if copy.is_file():
            session = copy.parent.name
            yield copy, ROOT / "sessions" / session / "results" / copy.name


def test_artifacts_directory_is_populated():
    files = [p for p in ARTIFACTS.rglob("*") if p.is_file()]
    assert len(files) >= 40, f"artifacts/ holds only {len(files)} files"


@pytest.mark.parametrize("copy,origin", list(_pairs()),
                         ids=lambda p: str(p).split("/")[-2] + "/" + str(p).split("/")[-1]
                         if isinstance(p, Path) else str(p))
def test_promoted_copy_matches_its_origin(copy, origin):
    assert origin.exists(), f"{copy} has no origin at {origin}"
    assert _digest(copy) == _digest(origin), (
        f"{copy} has drifted from {origin}; the paper would cite a figure that no "
        "longer matches the run that produced it")
