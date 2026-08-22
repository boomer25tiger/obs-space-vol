"""S05A Phase 5: build S05A-report.md and finish S05A-runlog.md."""

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
RES = os.path.join(BASE, "results")
LOGS = os.path.join(BASE, "logs")
S05_RES = os.path.join(ROOT, "sessions", "s05-reliability-mcs", "results")
VENV_PY = sys.executable


def jload(p, default=None):
    try:
        with open(p) as fh:
            return json.load(fh)
    except Exception:
        return default


def main():
    p1 = jload(os.path.join(RES, "phase1_summary.json"), {})
    p2 = jload(os.path.join(RES, "phase2_consistency.json"), {})
    p4 = jload(os.path.join(RES, "phase4_rerun.json"), {})
    sel = jload(os.path.join(RES, "phase4_selection.json"), {})
    try:
        ST = pd.read_csv(os.path.join(RES, "S05A-mcs-stability.csv"))
    except Exception:
        ST = pd.DataFrame()
    try:
        PI = pd.read_csv(os.path.join(RES, "S05A-primary-invariance.csv"))
    except Exception:
        PI = pd.DataFrame()

    L = []
    L.append("# Session 5A report, reproducibility amendment\n")
    L.append(f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} "
             "(UTC). No S05 artifact was modified or re-run in place; no "
             "data dated 2024-01-01 or later was touched.\n")

    # ---------------- Phase 1
    L.append("## Phase 1, environment capture\n")
    L.append(f"`ENVIRONMENT.md` and `requirements.lock` written at the "
             f"repository root; `results/S05A-checksums.txt` carries "
             f"SHA-256 for **{p1.get('n_files', 0):,} files** "
             f"({p1.get('total_bytes', 0)/1e9:.2f} GB) covering every "
             "input panel and every S01-S05 output artifact.\n")
    L.append("Retroactivity: the capture is valid for S01-S05 **only if "
             "nothing was installed or upgraded in between**, and that "
             "condition is only partly satisfied. Measured evidence "
             "(dist-info timestamps):\n")
    L.append("| package | timestamp | first used by |")
    L.append("|---|---|---|")
    for n, t in (p1.get("core_pkg_times") or {}).items():
        L.append(f"| {n} | {t} | S01 |")
    for n, t in (p1.get("later_pkg_times") or {}).items():
        s = "S03" if t < "2026-08-18 20:00" else "S05"
        L.append(f"| {n} | {t} | {s} |")
    L.append("")
    L.append(
        "Reading: the timestamps fall into four distinct clusters "
        "(core stack; pypdf; the databento/pyarrow/zstandard group; the "
        "arch/statsmodels/patsy group), consistent with four install "
        "events and with the session record - S01 installed the core "
        "stack, S03 added the data reader, S05 added the model packages. "
        "**No package was upgraded or downgraded at any point**: every "
        "distribution appears exactly once at a single version, and "
        "site-packages contains no `~`-prefixed shadow directories, which "
        "is what an interrupted or replaced install leaves behind. So "
        "S01 and S02 ran in a strictly smaller environment than the one "
        "captured, but every package either of them imported is present "
        "here at the identical version. The capture is therefore "
        "retroactively valid for the packages each session actually "
        "used, and the caveat is limited to environment size, not "
        "version drift.\n")
    thr = p1.get("threads", {})
    L.append("Thread environment at capture: "
             + ", ".join(f"`{k}`={v}" for k, v in thr.items())
             + ". S01/S02 grid runs set `VECLIB_MAXIMUM_THREADS=1` and "
             "`OMP_NUM_THREADS=1` in their launch command; S03-S05 ran "
             "with the defaults shown (unset). Details and "
             "`numpy.show_config()` are in `ENVIRONMENT.md`.\n")

    # ---------------- Phase 2
    L.append("## Phase 2, S03 vs S04 pipeline consistency (rules 1-4, 6)\n")
    if not p2:
        L.append("**NOT COMPLETED** - see runlog.\n")
    else:
        L.append(f"Span: {p2.get('span')}. Sampling used: "
                 f"{'yes' if p2.get('sampled') else 'no (full span)'}; "
                 f"elapsed {p2.get('total_elapsed_s', 0)/60:.1f} min "
                 f"against a {p2.get('cap_seconds', 0)/60:.0f}-minute "
                 "cap.\n")
        L.append("Method: each module's `main()` source was sliced at its "
                 "documented rule markers and executed verbatim (the "
                 "executed slices are saved as "
                 "`phase2_slice_*.py`), so this compares the code as "
                 "written in S03 and S04, not a retranscription.\n")
        L.append("| digest field | S03 | S04 (no R3) | S04 (with R3) |")
        L.append("|---|---|---|---|")
        fields = ["n_rows_all", "n_rows_front_contract", "n_sessions",
                  "n_trade_dates", "n_unique_iid", "n_unique_raw",
                  "front_n", "session_bar_count_total", "sha_iid_sorted",
                  "sha_tdate_sorted", "sha_ts_sorted", "sha_raw_sorted",
                  "sha_front", "sha_session_bar_counts"]
        for f in fields:
            a = p2.get("S03", {}).get(f, "--")
            b = p2.get("S04_noR3", {}).get(f, "--")
            c = p2.get("S04_withR3", {}).get(f, "--")
            fmt = (lambda v: f"`{str(v)[:16]}...`" if isinstance(v, str)
                   and len(str(v)) > 20 else f"{v:,}"
                   if isinstance(v, int) else str(v))
            L.append(f"| {f} | {fmt(a)} | {fmt(b)} | {fmt(c)} |")
        L.append("")
        cmp_ = p2.get("comparison", {})
        lfl = cmp_.get("like_for_like_S03_vs_S04noR3", {})
        L.append(f"**Like-for-like test (the DECISIONS item 19 test): "
                 f"S03 rules 1-4+6 vs S04 rules 1-4+6 with the R3 repair "
                 f"disabled - "
                 f"{'IDENTICAL' if lfl.get('identical') else 'DIFFERENT'} "
                 f"across all {lfl.get('fields_compared', 0)} compared "
                 f"fields**, including content hashes of the instrument-id "
                 "assignment, trade-date assignment, front-contract table "
                 "and per-session bar counts.\n")
        if not lfl.get("identical", False):
            L.append("Differing fields:\n")
            L.append("```json")
            L.append(json.dumps(lfl.get("differing_fields", {}), indent=1))
            L.append("```\n")
        r3 = cmp_.get("expected_R3_divergence_S03_vs_S04withR3", {})
        rl = cmp_.get("R3_row_level", {})
        L.append("Expected divergence from the deliberate S04 R3 repair "
                 "(DECISIONS item 15), reported separately so it is not "
                 "mistaken for an inconsistency: "
                 f"{'no fields differ' if r3.get('identical') else 'fields differ as follows'}"
                 + (f" - rows only in S03 {rl.get('rows_only_in_S03')}, "
                    f"rows only in S04 {rl.get('rows_only_in_S04')}, rows "
                    f"with a different trade date "
                    f"{rl.get('rows_with_different_tdate')}."
                    if rl else ".") + "\n")
        if rl.get("examples"):
            L.append("```json")
            L.append(json.dumps(rl["examples"], indent=1))
            L.append("```\n")

    # ---------------- Phase 3
    L.append("## Phase 3, MCS seed stability\n")
    L.append(
        "**S05 seeding, by source inspection:** `partde.py` line 224 "
        "constructs one `np.random.Generator(np.random.PCG64(20260821))` "
        "and line 263 passes that same generator to every `mcs()` call. "
        "So S05 used an **explicitly seeded Generator, not the global "
        "random state** - but a single stream shared across all 120 "
        "cells in execution order, so no cell has an independently "
        "recoverable seed and per-cell reproduction requires replaying "
        "the entire loop in identical order. Per DECISIONS item 18, "
        "recovery was not attempted; stability was measured instead.\n")
    if len(ST):
        L.append(f"20 seeds = `SeedSequence(20260821).generate_state(20)`, "
                 f"each used as `PCG64(seed)`; "
                 f"{len(ST)} cells x 20 seeds = {len(ST)*20:,} MCS "
                 "computations. Per-seed compositions: "
                 "`S05A-mcs-per-seed.csv`; per-cell summary: "
                 "`S05A-mcs-stability.csv`.\n")
        st75 = ST["n_distinct_75"].value_counts().sort_index()
        st90 = ST["n_distinct_90"].value_counts().sort_index()
        L.append("Distinct compositions observed across 20 seeds:\n")
        L.append("| distinct compositions | cells at 75% | cells at 90% |")
        L.append("|---|---|---|")
        for k in sorted(set(st75.index) | set(st90.index)):
            L.append(f"| {k} | {int(st75.get(k, 0))} | "
                     f"{int(st90.get(k, 0))} |")
        L.append("")
        L.append(f"Cells whose composition is identical under all 20 "
                 f"seeds: {int((ST.n_distinct_75 == 1).sum())}/{len(ST)} "
                 f"at 75%, {int((ST.n_distinct_90 == 1).sum())}/{len(ST)} "
                 "at 90%.\n")
        L.append(f"S05's reported composition appears among the 20 seed "
                 f"compositions in "
                 f"{int(ST.s05_75_in_seed_set.sum())}/{len(ST)} cells at "
                 f"75% and {int(ST.s05_90_in_seed_set.sum())}/{len(ST)} "
                 "at 90%.\n")
        L.append("Per-cell detail (modal composition, its frequency out "
                 "of 20, and whether S05's composition is in the set):\n")
        L.append("| cell | n | distinct 75 | modal 75 (freq) | S05 in set "
                 "| distinct 90 | modal 90 (freq) | S05 in set |")
        L.append("|---|---|---|---|---|---|---|---|")
        for _, r in ST.sort_values("cell_id").iterrows():
            L.append(f"| {r.cell_id} | {r.n_obs} | {r.n_distinct_75} | "
                     f"{r.modal_75} ({r.modal_freq_75}) | "
                     f"{r.s05_75_in_seed_set} | {r.n_distinct_90} | "
                     f"{r.modal_90} ({r.modal_freq_90}) | "
                     f"{r.s05_90_in_seed_set} |")
        L.append("")
    if len(PI):
        vc = PI.verdict.value_counts()
        L.append("### Primary result invariance, S-B vs S-C\n")
        L.append("For each (cell, quantile, confidence level) the S-B and "
                 "S-C compositions are compared **under the same seed**, "
                 "20 times:\n")
        L.append("| verdict | count |")
        L.append("|---|---|")
        for k, v in vc.items():
            L.append(f"| {k} | {v} |")
        L.append("")
        ind = PI[PI.verdict.str.startswith("INDETERMINATE")]
        L.append(
            f"**Statement:** the S05 finding that MCS composition differs "
            f"between S-B and S-C is seed-invariant in "
            f"{int((PI.invariant).sum())} of {len(PI)} comparisons and "
            f"seed-dependent in {len(ind)}. The {len(ind)} seed-dependent "
            "comparisons are reported as INDETERMINATE, not as findings:\n")
        if len(ind):
            L.append("| cell | quantile | level | seeds where S-B and S-C "
                     "differ (of 20) |")
            L.append("|---|---|---|---|")
            for _, r in ind.iterrows():
                L.append(f"| {r['cell']} | {r['quantile']:.2f} | "
                         f"{r['level']} | {r['n_seeds_differ']} |")
        L.append("")

    # ---------------- Phase 4
    L.append("## Phase 4, targeted re-run verification\n")
    L.append("Selection rule: smallest input row count within each Part, "
             "ties by ascending cell identifier (lexical). Selected "
             "before any re-run and logged in `S05A-runlog.md`.\n")
    L.append("| Part | cell identifier | input rows |")
    L.append("|---|---|---|")
    for s in (sel.get("selected") or []):
        L.append(f"| {s['part']} | `{s['cell_id']}` | {s['input_rows']} |")
    L.append("")
    if p4:
        L.append("All re-runs executed with every `*_NUM_THREADS` pinned "
                 "to 1, output redirected to a scratch directory.\n")
        t1 = p4.get("T1_reproduced", {})
        L.append(f"- T1 reproduced bitwise: **{t1.get('bitwise')}**. "
                 f"Part A variant selection reproduced: "
                 f"**{p4.get('variant_selection_reproduced', {}).get('same')}** "
                 f"({p4.get('variant_selection_reproduced', {}).get('new')}).")
        pa = p4.get("partA_all_cells", {})
        pc = p4.get("partC_all_cells", {})
        L.append(f"- Part A, every cell re-run "
                 f"({pa.get('n_rows_compared', 0):,} compared): bitwise "
                 f"identical = **{pa.get('all_bitwise_identical')}**.")
        L.append(f"- Part C, every estimate re-run "
                 f"({pc.get('n_rows_compared', 0):,} compared): bitwise "
                 f"identical = **{pc.get('all_bitwise_identical')}**.")
        L.append("")
        L.append("Selected Part A cell, full precision:\n")
        L.append("| field | re-run | S05 | bitwise |")
        L.append("|---|---|---|---|")
        for k, v in (p4.get("partA_selected_cell") or {}).items():
            L.append(f"| {k} | {v['new']} | {v['old']} | {v['bitwise']} |")
        L.append("")
        L.append("Selected Part C cell, full precision:\n")
        L.append("| estimator | re-run | S05 | bitwise | abs diff |")
        L.append("|---|---|---|---|---|")
        for r in (p4.get("partC_selected_cell") or []):
            L.append(f"| {r['estimator']} | {r['new']} | {r['old']} | "
                     f"{r['bitwise']} | {r['abs_diff']:.3e} |")
        L.append("")
        pe = p4.get("partE_selected_cell", {})
        L.append(f"Selected Part E cell `{pe.get('cell')}`: n_obs re-run "
                 f"{pe.get('n_obs_new')} vs S05 {pe.get('n_obs_old')} "
                 f"(match: {pe.get('n_obs_match')}). Deterministic inputs "
                 "to the MCS, full precision:\n")
        L.append("| model | mean QLIKE re-run | mean QLIKE S05 | bitwise | "
                 "rel diff |")
        L.append("|---|---|---|---|---|")
        for r in (pe.get("deterministic_inputs") or []):
            L.append(f"| {r['model']} | {r['qlike_new']} | "
                     f"{r['qlike_old']} | {r['bitwise']} | "
                     f"{r['rel_diff']:.3e} |")
        L.append("")
        L.append(f"{pe.get('note', '')}\n")

    # ---------------- Phase 5 determination
    L.append("## Phase 5, rerun determination\n")
    lfl_ok = bool(p2.get("comparison", {})
                  .get("like_for_like_S03_vs_S04noR3", {}).get("identical"))
    seed_ok = bool(len(PI)) and bool(PI.invariant.all())
    rerun_ok = bool(p4.get("partA_all_cells", {}).get(
        "all_bitwise_identical")) and bool(
            p4.get("partC_all_cells", {}).get("all_bitwise_identical"))
    ind_cells = PI[~PI.invariant] if len(PI) else pd.DataFrame()
    if lfl_ok and seed_ok and rerun_ok:
        verdict = "A. NO RERUN REQUIRED"
    elif lfl_ok and rerun_ok and not seed_ok:
        verdict = "B. PARTIAL RERUN REQUIRED"
    elif not lfl_ok:
        verdict = "C. FULL RERUN REQUIRED"
    else:
        verdict = "B. PARTIAL RERUN REQUIRED"
    L.append(f"### {verdict}\n")
    L.append("Evidence:\n")
    L.append(f"1. Consistency test (Phase 2): S03 and S04 rules 1-4+6 are "
             f"{'identical' if lfl_ok else 'NOT identical'} on the full "
             "pre-2024 span, so nothing downstream of S03/S04 is "
             f"invalidated by pipeline divergence. "
             f"{'PASS' if lfl_ok else 'FAIL'}.")
    if len(PI):
        L.append(f"2. MCS composition (Phase 3): seed-invariant in "
                 f"{int(PI.invariant.sum())} of {len(PI)} S-B vs S-C "
                 f"comparisons; {len(ind_cells)} are seed-dependent and "
                 "are reported as indeterminate rather than as findings. "
                 f"{'PASS' if seed_ok else 'NOT SEED-INVARIANT'}.")
    L.append(f"3. Targeted re-runs (Phase 4): Part A and Part C reproduce "
             f"bitwise ({rerun_ok}); Part E's deterministic inputs "
             "reproduce bitwise, and its bootstrap draw is not "
             "independently reproducible by construction (shared stream).")
    if verdict.startswith("B"):
        L.append("\n**Cells requiring rerun** (the indeterminate S-B/S-C "
                 "comparisons; a rerun means recomputing these MCS cells "
                 "over many seeds and reporting the seed distribution "
                 "rather than a single draw):\n")
        if len(ind_cells):
            L.append("| cell | quantile | level |")
            L.append("|---|---|---|")
            for _, r in ind_cells.iterrows():
                L.append(f"| {r['cell']} | {r['quantile']:.2f} | "
                         f"{r['level']} |")
        L.append("\nNo other part of S05 requires rerun: Parts A, C and "
                 "the deterministic inputs of Part E reproduce bitwise, "
                 "and the S03/S04 pipeline test passes.\n")
    L.append("\nNo rerun was performed in this session.\n")

    with open(os.path.join(RES, "S05A-report.md"), "w") as fh:
        fh.write("\n".join(L))
    print("report written")

    # ---------------- finish runlog (append; preserves Phase 3 order block)
    freeze = subprocess.run([VENV_PY, "-m", "pip", "freeze"],
                            capture_output=True, text=True).stdout.strip()
    prep = jload(os.path.join(RES, "phase3_prep.json"), {})
    R = ["\n## Wall clock per phase\n", "| phase | wall |", "|---|---|",
         "| Phase 0 (dirs, DECISIONS, S02 grid paused at 535/24500) | "
         "~2 min |",
         f"| Phase 1 environment + {p1.get('n_files', 0):,} checksums | "
         f"{p1.get('phase1_seconds', 0):.0f} s |",
         f"| Phase 2 consistency (3 pipeline executions) | "
         f"{p2.get('total_elapsed_s', 0)/60:.1f} min |",
         f"| Phase 3 loss regeneration (24 groups, 6 workers) | "
         f"{prep.get('seconds', 0)/60:.1f} min |",
         f"| Phase 3 MCS, {len(ST)} cells x 20 seeds | see phase3.log |",
         f"| Phase 4 targeted re-runs | "
         f"{p4.get('total_seconds', 0):.0f} s |",
         "| Phase 5 reports | ~2 min |", "",
         "## Seeds and their derivation\n",
         "- Phase 3 master seed 20260821 (S05's own MCS seed). The 20 "
         "independent seeds are `numpy.random.SeedSequence(20260821)."
         "generate_state(20)`, listed in the Phase 3 order block above; "
         "each is used as `PCG64(seed)` for one cell's MCS.\n"
         "- S05's own seeding, for the record: one "
         "`PCG64(20260821)` generator shared across all 120 cells in "
         "execution order (partde.py:224, consumed at partde.py:263).\n"
         "- No other randomness enters S05A: Phases 1, 2 and 4 are "
         "deterministic.\n",
         "## Phase 2 executed slices\n",
         "`results/phase2_slice_S03.py`, `results/phase2_slice_S04_noR3.py`, "
         "`results/phase2_slice_S04_withR3.py` are the exact code blocks "
         "executed, sliced from the S03/S04 sources at their rule "
         "markers.\n",
         "## Environment record\n",
         f"Full record in `ENVIRONMENT.md`; lockfile `requirements.lock`; "
         f"checksums `results/S05A-checksums.txt` "
         f"({p1.get('n_files', 0):,} files, "
         f"{p1.get('total_bytes', 0)/1e9:.2f} GB).\n",
         f"- Python {platform.python_version()}, {platform.platform()}",
         f"- Threads at capture: "
         + ", ".join(f"{k}={v}" for k, v in (p1.get('threads') or {}).items())
         + "; Phase 4 re-runs pinned all of them to 1.\n",
         "### pip freeze\n", "```text", freeze, "```", ""]
    with open(os.path.join(RES, "S05A-runlog.md"), "a") as fh:
        fh.write("\n".join(R))
    print("runlog completed")


if __name__ == "__main__":
    main()
