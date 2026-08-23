"""S24, DECISIONS item 159. Regenerate the counts the README states about the
repository's own contents, so that no such figure is ever typed by hand.

The README once stated a decision-log entry count in the same commit that
appended a new entry, which made the figure wrong on arrival. Twice. Run this
after any append to DECISIONS.md; `tests/test_readme_counts.py` fails if it has
not been run.
"""
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "DECISIONS.md"
README = ROOT / "README.md"

ROW = re.compile(
    r"(\| `DECISIONS\.md` \| the decision log, )\d+( entries numbered to )\d+(, append-only \|)")


def counts():
    nums = [int(m.group(1)) for line in LOG.read_text().splitlines()
            if (m := re.match(r"^(\d+)\.\s+\S", line))]
    return len(nums), max(Counter(nums))


def render(text, n_entries, highest):
    new, k = ROW.subn(rf"\g<1>{n_entries}\g<2>{highest}\g<3>", text)
    if k != 1:
        raise SystemExit(f"expected exactly one DECISIONS.md row in README.md, found {k}")
    return new


def main(check_only=False):
    n, hi = counts()
    old = README.read_text()
    new = render(old, n, hi)
    if check_only:
        if old != new:
            print(f"STALE: README should read {n} entries numbered to {hi}")
            return 1
        print(f"current: {n} entries numbered to {hi}")
        return 0
    if old != new:
        README.write_text(new)
        print(f"updated: {n} entries numbered to {hi}")
    else:
        print(f"already current: {n} entries numbered to {hi}")
    return 0


if __name__ == "__main__":
    sys.exit(main(check_only="--check" in sys.argv))
