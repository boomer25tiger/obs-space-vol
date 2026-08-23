"""S24, DECISIONS item 160. The build check harness.

Every check runs against extracted, normalised text rather than against LaTeX
source. Four checks failed spuriously between S20 and S23D because a regex met
real typography: a typographic apostrophe in a subsection heading, an underscore
that OT1 draws as a rule rather than a glyph, and two phrases that wrap across a
line in the source. `norm` folds all three classes away before matching.

    python paper/check_build.py            run every check
    python paper/check_build.py --quiet    exit status only
"""
import re
import sys
import unicodedata
from pathlib import Path

import pypdf

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "paper" / "main.pdf"
LOG = ROOT / "paper" / "main.log"

_PUNCT = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"',
    "‐": "-", "‑": "-", "‒": "-", "–": "-",
    "—": "-", "―": "-", "−": "-",
    " ": " ", " ": " ", " ": " ", "ﬁ": "fi", "ﬂ": "fl",
}


def norm(s):
    """Fold unicode punctuation to ASCII and collapse all whitespace.

    Matching against this rather than against raw extracted text is what makes a
    check survive a typographic apostrophe or a line wrap.
    """
    s = unicodedata.normalize("NFKC", s)
    for a, b in _PUNCT.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s)


def pages():
    return [p.extract_text() or "" for p in pypdf.PdfReader(PDF).pages]


def run():
    P = pages()
    flat = norm("\n".join(P))          # whitespace collapsed: survives line wraps
    raw = "\n".join(P)                 # line structure preserved, for heading checks
    log = LOG.read_text() if LOG.exists() else ""
    readme = norm((ROOT / "README.md").read_text())
    out = []

    def chk(name, ok, detail=""):
        out.append((name, bool(ok), detail))

    # --- content ---------------------------------------------------------
    chk("Section 3 non-empty", len(re.findall(r"\b3\.\d\s", raw)) >= 5,
        f"{len(re.findall(chr(92)+'b3'+chr(92)+'.'+chr(92)+'d'+chr(92)+'s', raw))} subsection marks")
    subs = re.findall(r"^\s*(5\.\d)\s+(\S[^\n]{3,60})\s*$", raw, re.M)
    chk("Section 5 carries 5.1 to 5.5", len(subs) == 5,
        "; ".join(f"{a} {b}" for a, b in subs))
    chk("5.5 heading found despite its typographic apostrophe",
        "5.5 The criterion's record" in norm(raw),
        "matched after folding U+2019 to ASCII")
    chk("byline renders", "Cristian Gualy" in norm(P[0]))
    chk("date renders", bool(re.search(r"\d{1,2} \w+ \d{4}", norm(P[0]))))
    chk("'twelve kill conditions' absent",
        not re.search(r"twelve\s+(pre-registered\s+)?kill", flat, re.I))
    chk("'27 distinct values' absent", "27 distinct values" not in flat)
    chk("'roughly half subset variation' absent", "roughly half subset variation" not in flat)
    chk("Section 3.5 calibration caveat present",
        "We are less confident in the calibration than in the arm" in flat
        and "conditional on the parameterisation." in flat)

    # --- typography ------------------------------------------------------
    paths = set(re.findall(r"[a-z0-9_]*phase\d[a-z0-9_]*\.csv|k_table\.csv", flat))
    spaced = [x for x in re.findall(
        r"[A-Za-z0-9\-/]*(?:phase\d|k[_ ]table|spy[_ ]grid)[A-Za-z0-9_./\-{},]{0,45}", flat)
        if re.search(r"phase\d\s|k table|spy grid", x)]
    chk("artifact paths keep their underscores under T1", not spaced,
        f"{len(paths)} distinct paths, none with a space where an underscore belongs")
    chk("zero overfull boxes", log.count("Overfull") == 0, f"{log.count('Overfull')} overfull")
    chk("no multiply-defined labels", "multiply defined" not in log)
    chk("no stray '= MISSING' in typeset text", "= MISSING" not in flat)
    chk("no stray 'and companions' in typeset text", "and companions" not in flat)

    # --- README, matched against normalised text so a wrap cannot hide it --
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_readme", ROOT / "paper" / "build_readme.py")
    br = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(br)
    n, hi = br.counts()
    chk("README decision-log count is current",
        f"append-only, {n} entries numbered to {hi}" in readme,
        f"DECISIONS.md has {n} entries numbered to {hi}")
    chk("README MISSING-count phrase found despite wrapping",
        "twelve quantities are registered MISSING" in readme,
        "matched after collapsing the newline inside the phrase")
    chk("README states section 5 is written",
        "section 5 remains a stub" not in readme)
    return out


if __name__ == "__main__":
    res = run()
    bad = [r for r in res if not r[1]]
    if "--quiet" not in sys.argv:
        for name, ok, detail in res:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))
        print(f"\n  {len(res) - len(bad)} of {len(res)} passed")
    sys.exit(1 if bad else 0)
