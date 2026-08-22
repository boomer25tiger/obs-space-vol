"""Build S01-runlog.md: wall-clock per phase, package versions, every seed."""

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run import BASE, MASTER_ROOT, N_MASTERS

import numpy as np

LOG_DIR = os.path.join(BASE, "logs")
RES_DIR = os.path.join(BASE, "results")
VENV_PY = os.path.join(BASE, "..", "..", ".venv", "bin", "python3")


def phase_timings_block(manual_rows):
    L = ["| phase | wall clock |", "|---|---|"]
    for name, val in manual_rows:
        L.append(f"| {name} | {val} |")
    return "\n".join(L)


def main():
    prog = []
    with open(os.path.join(LOG_DIR, "progress.jsonl")) as fh:
        for line in fh:
            prog.append(json.loads(line))
    # De-duplicate on tag (restart artifacts): keep the last entry.
    by_tag = {}
    for p in prog:
        by_tag[p["tag"]] = p
    prog = sorted(by_tag.values(), key=lambda p: p["ds_index"])

    total_ds = len(prog)
    elapsed = np.array([p["elapsed"] for p in prog])
    neg = [p for p in prog if p.get("neg_eig_count", 0) > 0]
    floor_tot = sum(p.get("floor_hits", 0) for p in prog)

    freeze = subprocess.run([VENV_PY, "-m", "pip", "freeze"],
                            capture_output=True, text=True).stdout.strip()

    masters = np.random.SeedSequence(MASTER_ROOT).generate_state(N_MASTERS)

    L = []
    L.append("# Session 1 run log\n")
    L.append(f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} "
             "(UTC). Synthetic data only; no market data touched.\n")

    L.append("## Wall clock per phase\n")
    L.append(phase_timings_block(PHASES))
    L.append("")
    L.append(f"Grid statistics: {total_ds} datasets completed; per-dataset "
             f"compute time median {np.median(elapsed):.1f}s, "
             f"p90 {np.percentile(elapsed, 90):.1f}s, max {elapsed.max():.1f}s "
             "(under 6-way parallelism on a heavily loaded host, see "
             "bottleneck notes).\n")

    L.append("## Runtime notes and bottleneck\n")
    L.append(NOTES)

    L.append("## Environment\n")
    L.append(f"- Python {platform.python_version()} on {platform.platform()}\n"
             f"- Host: 8 logical CPUs (4 performance), 8 GB RAM\n")
    L.append("### Package versions (pip freeze)\n")
    L.append("```text\n" + freeze + "\n```\n")

    L.append("## Seeds\n")
    L.append(
        f"- Master root: {MASTER_ROOT}. The 5 independent master seeds are "
        f"`SeedSequence({MASTER_ROOT}).generate_state(5)` = "
        f"{[int(m) for m in masters]}.\n"
        "- Per-dataset generator: `PCG64(SeedSequence([master_seed, "
        "ds_index]))`, where ds_index enumerates (DGP combo, geometry, seed "
        "slot) in the fixed order of `run.build_jobs()`. All 200 "
        "replications of a dataset consume one stream sequentially.\n"
        "- Bootstrap seed (aggregation): 777. Unit-test seeds: 101, 202, "
        "303, 404, 505, 606, 999 (diagnostic).\n")
    L.append("### Every dataset seed (tag: [master_seed, ds_index])\n")
    L.append("```text")
    for p in prog:
        L.append(f"{p['tag']}: {p['seed_entropy']}")
    L.append("```\n")

    L.append("## Embedding eigenvalue report\n")
    if neg:
        L.append(f"{len(neg)} datasets had negative circulant-embedding "
                 "eigenvalues (clipped to zero, magnitudes below):\n")
        for p in neg[:50]:
            L.append(f"- {p['tag']}: count {p['neg_eig_count']}, "
                     f"min eig {p['min_eig']:.3e}")
    else:
        L.append("No dataset produced a negative circulant-embedding "
                 "eigenvalue (Davies-Harte embeddings were all "
                 "nonnegative-definite as constructed).")
    L.append("")
    L.append(f"## Log-floor events\n")
    L.append(f"Total proxy values floored at 1e-14 before logging, across "
             f"all datasets and replications: {floor_tot}.\n")

    with open(os.path.join(RES_DIR, "S01-runlog.md"), "w") as fh:
        fh.write("\n".join(L))
    print("runlog written", total_ds, "datasets,", len(neg), "neg-eig,",
          floor_tot, "floor hits")


PHASES = [
    ("Phase 0 setup (venv, installs, import check)", "~4 min"),
    ("Phase 1 reconciliation (DECISIONS.md; spec files absent, noted)", "~2 min"),
    ("Phase 2 pre-registration freeze", "~1 min"),
    ("Phase 3 build (fbm/dgp/proxies/estimators/tests/run/aggregate)", "~50 min"),
    ("Phase 3 unit tests, final passing run (16/16)", "46 s"),
    ("Phase 4 grid, 1050 datasets, 6 workers (2 segments, see notes)",
     "149 min end to end (09:41 launch, first npz 10:31 after a killed "
     "first segment was relaunched, last npz 13:00)"),
    ("Phase 5 aggregation (bootstrap, 15,960 cells)", "47 s"),
    ("Phase 5 report generation", "90 s"),
]

NOTES = """- TOTAL RUNTIME EXCEEDED THE 90-MINUTE BUDGET (grid alone ~149 min
  wall, whole session several hours). Per the pre-registered stop
  conditions, replications (200), master seeds (5), and sweep points were
  NOT reduced. Bottleneck: the host, not the code. During the first ~90
  minutes the machine ran at load average 74-77 on 8 logical cores with
  13.6/14.3 GB of swap consumed by unrelated applications (Chrome at
  ~180% CPU across processes); the simulation workers were paged down to
  2-4 MB RSS and starved, yielding ~2 datasets/min. When the external
  load eased, throughput rose to ~9-13 datasets/min and the remaining
  ~1000 datasets completed in ~2 hours. Median per-dataset compute was
  seconds-scale serially (7.8 s for n=390, ~25-40 s for n=1380, 200
  replications each).
- The first grid launch was killed at the 10-minute mark by the session
  harness's background-task timeout after 22 datasets; the run was
  relaunched detached (nohup) and resumed idempotently by skipping
  completed dataset files. File integrity of all 1050 outputs was
  verified before aggregation (no corruption).
- Unit-test history (all before any Phase-4 data was generated):
  (1) first U5 run exposed a divide-by-zero in the arm-(d) shape fit at
  the degenerate H=0.5 grid row (fGn acf identically zero at lags >= 1);
  fixed by excluding zero-information shape rows. An implementation bug,
  fixed, not an estimator failure. (2) U5's original single-realization
  5% tolerance for arm (d) was tighter than the estimator's own sampling
  noise under exact specification (per-draw sd 4.5-13% at T = 1e5;
  bias diagnostic over 30 independent realizations: mean recovery
  1.004-1.027). The test was redesigned to assert mean recovery over 15
  realizations with MC-error-based tolerances; no estimator code was
  changed by this revision. Final suite: 16/16 passed.
- The two spec files named in Phase 1 (SPEC-obs-space-vol-eval.md,
  SPEC-addendum-A-mc-and-metrics.md) were absent from the working
  directory; the in-place edits could not be applied and are deferred
  (see specs/NOTE-missing-specs.md). DECISIONS.md records the decisions.
- Performance changes made between the pilot and the full run (before
  any grid results were inspected, estimator math unchanged): power-law
  arm vectorized over its alpha grid; intraday simulation chunked over
  250-day blocks in float32 with float64 accumulation of daily sums;
  noise draws generated natively in float32. Unit tests were re-run and
  passed after these changes; the 12 pilot datasets were deleted and
  regenerated under the final code.
- Implementation constants fixed a priori: fOU kappa = 0.03/day; jump
  intensity 1 per day; bipower variation at the finest M per geometry;
  log floor 1e-14.
"""

if __name__ == "__main__":
    main()
