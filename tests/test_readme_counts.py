"""S24, DECISIONS item 159. Fail if a count the README states about the
repository's own contents has drifted from the file it describes."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_readme", ROOT / "paper" / "build_readme.py")
br = importlib.util.module_from_spec(spec)
spec.loader.exec_module(br)


def test_readme_decision_log_count_is_current():
    n, hi = br.counts()
    text = (ROOT / "README.md").read_text()
    assert f"the decision log, {n} entries numbered to {hi}, append-only" in text, (
        f"README is stale; DECISIONS.md has {n} entries numbered to {hi}. "
        "Run: python paper/build_readme.py")
