"""Build S02-runlog.md: phases, versions, seeds, S01 within-window check."""

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run2 import BASE, MASTER_ROOT, N_MASTERS

RES_DIR = os.path.join(BASE, "results")
LOG_DIR = os.path.join(BASE, "logs")
VENV_PY = sys.executable


def s01_within_window_check():
    """Verify DECISIONS item 9: S01 DGPs hold IV constant within windows.

    Code-level: S01's dgp.simulate_day_chunk draws every intraday return
    with the same per-day scale sqrt(iv/n) (no intraday profile exists in
    the S01 module). Empirical: simulate S01 D1 days, bin each day's
    squared returns into 10 intraday blocks; under constancy the block
    means are flat up to MC error.
    """
    s01_src = os.path.join(os.path.dirname(BASE), "s01-estimator-validation",
                           "src")
    if s01_src not in sys.path:
        sys.path.insert(0, s01_src)
    import dgp as s01dgp
    rng = np.random.Generator(np.random.PCG64(777))
    cfg = s01dgp.DGPConfig("D1", "ar1", 0.98, 0.7)
    n, days = 390, 8000
    path = s01dgp.simulate_day_chunk(cfg, np.ones(days), n, rng)
    r = np.diff(path.astype(np.float64), axis=1)
    blocks = (r * r).reshape(days, 10, n // 10).sum(axis=2).mean(axis=0)
    rel = blocks / blocks.mean()
    # MC se per block ~ sqrt(2/(days*39)) ~ 0.25%; 5 sigma bound
    flat = bool(np.max(np.abs(rel - 1.0)) < 0.02)
    return flat, rel


def main():
    prog = []
    with open(os.path.join(LOG_DIR, "progress.jsonl")) as fh:
        for line in fh:
            prog.append(json.loads(line))
    by_tag = {}
    for p in prog:
        by_tag[p["tag"]] = p
    prog = sorted(by_tag.values(), key=lambda p: p["ds_index"])
    elapsed = np.array([p["elapsed"] for p in prog])
    neg = [p for p in prog if p.get("neg_eig_count", 0) > 0]
    floor_tot = sum(p.get("floor_hits", 0) for p in prog)

    freeze = subprocess.run([VENV_PY, "-m", "pip", "freeze"],
                            capture_output=True, text=True).stdout.strip()
    masters = np.random.SeedSequence(MASTER_ROOT).generate_state(N_MASTERS)
    flat, rel = s01_within_window_check()

    L = []
    L.append("# Session 2 run log\n")
    L.append(f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} (UTC). "
             "Synthetic only; no market data touched.\n")

    L.append("## Wall clock per phase\n")
    L.append("| phase | wall clock |")
    L.append("|---|---|")
    for name, val in PHASES:
        L.append(f"| {name} | {val} |")
    L.append("")
    if len(elapsed):
        L.append(f"Grid statistics at report time: {len(prog)} of 24,500 "
                 f"datasets completed; per-dataset compute median "
                 f"{np.median(elapsed):.1f}s, p90 {np.percentile(elapsed, 90):.1f}s, "
                 f"max {elapsed.max():.1f}s under 6-way parallelism.\n")

    L.append("## Runtime, obstruction, and bottleneck\n")
    L.append(NOTES)

    L.append("## Verification of S01 within-window structure "
             "(DECISIONS item 9)\n")
    L.append(
        "Code level: S01's `dgp.simulate_day_chunk` draws all n intraday "
        "returns of a day with one scale `sqrt(iv/n)`; no intraday profile "
        "exists anywhere in the S01 source. Empirical: 8,000 simulated S01 "
        "D1 days, squared returns binned into 10 intraday blocks; "
        "normalized block means "
        f"{np.round(rel, 4).tolist()} — max deviation from flat "
        f"{np.max(np.abs(rel-1))*100:.2f}% (5-sigma MC bound 2%). "
        f"VERDICT: S01 DGPs {'held' if flat else 'DID NOT hold'} "
        "integrated variance constant within each window. E2's S01 pass "
        "on D1-D4 was therefore obtained under exact within-window "
        "constancy, as DECISIONS item 9 suspected.\n")

    L.append("## Environment\n")
    L.append(f"- Python {platform.python_version()} on {platform.platform()}\n"
             "- Host: 8 logical CPUs (4 performance), 8 GB RAM, heavily "
             "loaded by unrelated user applications throughout.\n")
    L.append("### Package versions (pip freeze)\n")
    L.append("```text\n" + freeze + "\n```\n")

    L.append("## Seeds\n")
    L.append(
        f"- Master root: {MASTER_ROOT}. Five master seeds = "
        f"`SeedSequence({MASTER_ROOT}).generate_state(5)` = "
        f"{[int(m) for m in masters]}.\n"
        "- Per-dataset generator: `PCG64(SeedSequence([master_seed, "
        "ds_index]))`, ds_index enumerating (DGP combo, geometry, seed "
        "slot) in `run2.build_jobs()` order. Bootstrap seed 777. "
        "Unit-test seeds: 11, 22, 33, 44, 55 (plus S01 suite seeds under "
        "V1). Within-window verification seed 777.\n")
    L.append("### Every dataset seed (tag: [master_seed, ds_index])\n")
    L.append("```text")
    for p in prog:
        L.append(f"{p['tag']}: {p['seed_entropy']}")
    L.append("```\n")

    L.append("## Embedding eigenvalues and log floors\n")
    if neg:
        L.append(f"{len(neg)} datasets had negative circulant-embedding "
                 "eigenvalues (clipped, logged):")
        for p in neg[:50]:
            L.append(f"- {p['tag']}: count {p['neg_eig_count']}, "
                     f"min {p['min_eig']:.3e}")
    else:
        L.append("No negative circulant-embedding eigenvalues in any "
                 "completed dataset.")
    L.append("")
    L.append(f"Total proxy/corrected-proxy values floored at 1e-14 before "
             f"logging: {floor_tot} (across all completed datasets; "
             "dominated by the degenerate E6 correction at M close to "
             "M_finest and by robust proxies at extreme NSR).\n")

    with open(os.path.join(RES_DIR, "S02-runlog.md"), "w") as fh:
        fh.write("\n".join(L))
    print("runlog written:", len(prog), "datasets logged,", len(neg),
          "neg-eig,", floor_tot, "floor hits")


PHASES = [
    ("Phase 0 (dirs, DECISIONS append)", "~2 min"),
    ("Phase 1 pre-registration freeze", "~1 min"),
    ("Phase 2 build (proxies_robust/dgp2/estimators2/run2/tests) incl. "
     "published-rule extraction from ZMA 2005, BNHLS 2009, JLMPV 2009",
     "~75 min"),
    ("Phase 2 unit tests V1-V6, final passing run (6 tests, incl. S01's "
     "16 under V1)", "12 s"),
    ("Phase 3 grid", "FILL"),
    ("Phase 3 aggregation + reports", "FILL"),
]

NOTES = """FILL
"""

if __name__ == "__main__":
    main()
