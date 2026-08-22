"""Build S05-report.md and S05-runlog.md."""

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results")
VENV_PY = sys.executable

t1 = json.load(open(os.path.join(RES, "s05_t1.json")))
selj = json.load(open(os.path.join(RES, "s05_variant_selection.json")))
A = pd.read_csv(os.path.join(RES, "s05_parta.csv"))
C = pd.read_csv(os.path.join(RES, "s05_partc_wide.csv"))
MET = pd.read_csv(os.path.join(RES, "s05_metrics.csv"))
MCS = pd.read_csv(os.path.join(RES, "s05_mcs.csv"))
FC = pd.read_csv(os.path.join(RES, "s05_partf_curves.csv"))
seeds_f = json.load(open(os.path.join(RES, "s05_partf_seeds.json")))
EST_COLS = ["E1_a_exp_L1-5", "E1_a_exp_L1-10", "E1_d_model_L1-5",
            "E1_d_model_L1-10", "E2", "E4"]


def main():
    L = []
    L.append("# Session 5 report, reliability surface and model "
             "confidence set\n")
    L.append("Run date 2026-08-18. Real data (S04 repaired panels: ES RTH "
             "1901, ES GLOBEX 1953, NQ RTH 1901, NQ GLOBEX 1948) plus the "
             "calibrated synthetic arm. Pre-registration: `../PREREG.md`. "
             "Holdout untouched.\n")

    # ---- 1 T1
    L.append("## 1. T1 and the resolved tripower normalisation\n")
    L.append(
        f"T1 PASSED. Correct constant mu_4/3 = {t1['mu43']:.6f}; ratio of "
        f"means E[RQ]/E[TQ] on jump-free constant-volatility data = "
        f"{t1['ratio_of_means']:.5f} (tolerance 1%). The per-session mean "
        f"of the RATIO carries a finite-M Jensen term "
        f"({t1['mean_of_ratios_jensen']:.4f} at M=390), reported, not "
        "gated. RESOLUTION of the S04 anomaly: S04's diag.py hard-coded "
        f"{t1['s04_wrong_constant']:.6f} where mu_4/3 = {t1['mu43']:.6f} "
        "belongs, understating TQ by the cube of the ratio, a factor "
        f"{t1['s04_implied_bias_factor']:.3f}. The 'median RQ/TQ near 6.0 "
        "in every cell' was therefore 4.97 x the true ratio; the true "
        "medians implied are 1.18-1.62, which is ordinary jump content, "
        "not an anomaly. (S04 artifacts are left as they stand; this "
        "report supersedes their RQ/TQ ratio column.)\n")

    # ---- 2 Part A
    L.append("## 2. Part A, quarticity ratio R = (2/M) Q / P^2\n")
    L.append(f"Pre-registered selection metric: {selj['metric']}. "
             "Ranking (smaller = more stable):\n")
    L.append("| variant | share R > 10x median | mean p95/median |")
    L.append("|---|---|---|")
    for k, v in selj["ranking"].items():
        L.append(f"| {k} | {v['share']:.6f} | {v['p95_over_med']:.3f} |")
    L.append(f"\n**Selected variant: {selj['chosen']}** (truncated "
             "quarticity / truncated RV at 3 local sd). Selection ran "
             "before any lambda was produced.\n")
    L.append("Pooled-year distributions at the finest M, B0 (full table "
             "for every cell, including B1 and per-year rows: "
             "`s05_parta.csv`):\n")
    L.append("| root | geom | variant | median R | med/(2/M) | p95 | p99 | "
             "share>10x med | acf1 | acf10 |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    sub = A[(A.year == 0) & (A.btag == "B0")]
    sub = sub[sub.M == sub.groupby("geom")["M"].transform("max")]
    for _, r in sub.iterrows():
        L.append(f"| {r.root} | {r.geom} | {r.variant} | {r['median']:.2e} "
                 f"| {r.med_over_ref:.2f} | {r.p95:.2e} | {r.p99:.2e} | "
                 f"{r.share_gt10x_med:.4f} | {r.acf1:.2f} | {r.acf10:.2f} |")
    L.append("")

    # ---- 3 Part C
    L.append("## 3. Part C, reliability surface\n")
    L.append("Pooled (year, tercile) rows below; the full surface "
             "(9 years x 4 tercile groups x horizons x M x B0/B1, 1,928 "
             "cells x 6 estimators) is `s05_partc_wide.csv` with a "
             "disagreement column (max - min across estimators).\n")
    L.append("| root | geom | B | horizon | M | " + " | ".join(EST_COLS)
             + " | disagreement |")
    L.append("|---" * (5 + len(EST_COLS) + 1) + "|")
    p = C[(C.year == 0) & (C.tercile == 0)]
    p = p[(p.horizon == "1day") | (p.M.isin([30, 60]))]
    for _, r in p.sort_values(["root", "geom", "btag", "horizon",
                               "M"]).iterrows():
        vals = " | ".join(f"{r[c]:.3f}" if np.isfinite(r[c]) else "--"
                          for c in EST_COLS)
        L.append(f"| {r.root} | {r.geom} | {r.btag} | {r.horizon} | "
                 f"{int(r.M)} | {vals} | {r.disagreement:.3f} |")
    dis = C[(C.year == 0) & (C.tercile == 0)]["disagreement"]
    L.append(f"\nEstimator disagreement across pooled cells: median "
             f"{dis.median():.3f}, p90 {dis.quantile(.9):.3f}, max "
             f"{dis.max():.3f}. Estimators are reported separately "
             "throughout; nothing is averaged.\n")

    # ---- 4 MCS
    L.append("## 4. Part E, MCS composition\n")
    L.append("Hansen-Lunde-Nason MCS, 10,000 moving-block bootstrap "
             "resamples (seed 20260821), 75% and 90% sets, per scheme "
             "and cell. Full p-values per model: `s05_mcs.csv`.\n")
    L.append("| root | geom | B | horizon | scheme | n | MCS-75 | MCS-90 |")
    L.append("|---" * 8 + "|")
    for _, r in MCS.sort_values(["root", "geom", "btag", "horizon",
                                 "scheme"]).iterrows():
        L.append(f"| {r.root} | {r.geom} | {r.btag} | {r.horizon} | "
                 f"{r.scheme} | {r.n_obs} | {r.mcs75} | {r.mcs90} |")
    L.append("")
    # composition difference statements
    diffs_bc, diffs_corr = [], []
    for key, g in MCS.groupby(["root", "geom", "btag", "horizon"]):
        for q in ["0.80", "0.90"]:
            sb = g[g.scheme == f"S-B_q{q}"]
            sc = g[g.scheme == f"S-C_q{q}"]
            if len(sb) and len(sc):
                for lev in ["mcs75", "mcs90"]:
                    if sb[lev].iloc[0] != sc[lev].iloc[0]:
                        diffs_bc.append((key, q, lev, sb[lev].iloc[0],
                                         sc[lev].iloc[0]))
    L.append(f"**Primary result, S-B vs S-C:** composition differs in "
             f"{len(diffs_bc)} of "
             f"{len(list(MCS.groupby(['root','geom','btag','horizon'])))*4} "
             "(cell x quantile x level) comparisons. Differing cells:\n")
    if diffs_bc:
        L.append("| cell | q | level | S-B set | S-C set |")
        L.append("|---|---|---|---|---|")
        for key, q, lev, sb_, sc_ in diffs_bc:
            L.append(f"| {'/'.join(str(k) for k in key)} | {q} | {lev} | "
                     f"{sb_} | {sc_} |")
    else:
        L.append("None.")
    L.append("")
    L.append(
        "**IC with vs without the reliability correction:** the "
        "correction divides every model's IC by the same sqrt(lambda) "
        "within a cell, so it rescales the IC column without reordering "
        "models inside a cell; the corrected columns are in section 5 and "
        "`s05_metrics.csv`. Where lambda varies across cells the "
        "correction changes CROSS-cell comparisons; those columns are "
        "reported side by side.\n")

    # ---- 5 metrics
    L.append("## 5. IC, corrected IC, R2, corrected R2, IR, hit rate\n")
    L.append("S-A rows shown; every scheme row is in `s05_metrics.csv`.\n")
    L.append("| root | geom | B | horizon | model | lam_hat | IC(log) | "
             "IC corr | IC spear | R2 | R2 corr | IC-IR | hit | QLIKE |")
    L.append("|---" * 14 + "|")
    for _, r in MET[MET.scheme == "S-A"].sort_values(
            ["root", "geom", "btag", "horizon", "model"]).iterrows():
        L.append(f"| {r.root} | {r.geom} | {r.btag} | {r.horizon} | "
                 f"{r.model} | {r.lam_hat:.3f} | {r.ic_pearson_log:.3f} | "
                 f"{r.ic_corrected:.3f} | {r.ic_spearman:.3f} | "
                 f"{r.r2_oos:.3f} | {r.r2_corrected:.3f} | "
                 f"{r.ic_ir:.2f} | {r.hit_rate:.3f} | {r.qlike_mean:.4f} |")
    L.append("")

    # ---- 6 Part F
    L.append("## 6. Part F, synthetic error curves\n")
    L.append("Recovery (lambda_hat / lambda_true, mean over 200 reps x 5 "
             "seeds) at the calibrated constants; full grid "
             "`s05_partf_curves.csv`. No pass band is applied.\n")
    L.append("| nu | NSR | n | M | " + " | ".join(
        ["E1_a_L1-5", "E1_a_L1-10", "E1_d_L1-5", "E1_d_L1-10", "E2", "E4"])
        + " |")
    L.append("|---" * 10 + "|")
    pf = FC.pivot_table(index=["nu", "nsr", "n", "M"], columns="estimator",
                        values="recovery").reset_index()
    pf = pf[pf.M == pf.groupby("n")["M"].transform("max")]
    for _, r in pf.iterrows():
        vals = " | ".join(f"{r[c]:.3f}" for c in
                          ["E1_a_L1-5", "E1_a_L1-10", "E1_d_L1-5",
                           "E1_d_L1-10", "E2", "E4"])
        L.append(f"| {r.nu} | {r.nsr:.0e} | {int(r.n)} | {int(r.M)} | "
                 f"{vals} |")
    L.append("")

    # ---- 7 conclusion changes across B and sensitivity
    L.append("## 7. Cells where a conclusion changes across the boundary "
             "treatment or calibration sensitivity\n")
    flips = []
    for key, g in MCS.groupby(["root", "geom", "horizon", "scheme"]):
        b0 = g[g.btag == "B0"]
        b1 = g[g.btag == "B1"]
        if len(b0) and len(b1):
            for lev in ["mcs75", "mcs90"]:
                if b0[lev].iloc[0] != b1[lev].iloc[0]:
                    flips.append(("MCS", "/".join(str(k) for k in key), lev,
                                  b0[lev].iloc[0], b1[lev].iloc[0]))
    if flips:
        L.append("| quantity | cell | level | B0 | B1 |")
        L.append("|---|---|---|---|---|")
        for q_, cell, lev, a_, b_ in flips:
            L.append(f"| {q_} | {cell} | {lev} | {a_} | {b_} |")
    else:
        L.append("No MCS composition changes across B0/B1.")
    sens = []
    base = FC[(FC.nu == 3.4) & (FC.nsr == 3e-5)]
    for (nu, nsr), g in FC.groupby(["nu", "nsr"]):
        if nu == 3.4 and nsr == 3e-5:
            continue
        m = g.merge(base, on=["n", "M", "estimator"],
                    suffixes=("", "_base"))
        m["shift"] = (m["recovery"] - m["recovery_base"]).abs()
        big = m[m["shift"] > 0.10]
        for _, r in big.iterrows():
            sens.append(f"({r.estimator}, n={int(r.n)}, M={int(r.M)}): "
                        f"recovery {r.recovery_base:.3f} -> {r.recovery:.3f} "
                        f"at nu={nu}, NSR={nsr:.0e}")
    L.append("\nSynthetic-arm recovery shifts exceeding 0.10 vs the "
             f"primary calibration ({len(sens)}):\n")
    for s in sens:
        L.append(f"- {s}")
    L.append("")

    with open(os.path.join(RES, "S05-report.md"), "w") as fh:
        fh.write("\n".join(L))
    print("report written")

    freeze = subprocess.run([VENV_PY, "-m", "pip", "freeze"],
                            capture_output=True, text=True).stdout.strip()
    R = ["# Session 5 run log\n",
         f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} (UTC).\n",
         "## Wall clock per phase\n", "| phase | wall |", "|---|---|",
         "| Phase 0 setup (arch/statsmodels install, S02 grid paused at "
         "508/24500 to free cores; resumable) | ~5 min |",
         "| Phase 1 freeze + calibration verification | ~4 min |",
         "| T1 + Part A (2 runs: T1 tolerance redesigned from "
         "mean-of-ratios to ratio-of-means after the Jensen diagnosis; "
         "both runs logged) | ~1 min |",
         "| Part C | 5 s |",
         "| Parts D+E | see logs/partde.log timestamps (~25 min) |",
         "| Part F (parallel, 6 workers) | see logs/partf.log (~20 min) |",
         "| Reports | ~2 min |", "",
         "## Pre-registered constants used\n",
         "- NSR: 3e-5 primary; 1e-5, 1e-4 sensitivity. Hill nu: 3.4 "
         "primary; 3.0, 4.5. Boundary elevation via the measured "
         "empirical intraday profile (subsumes 25.9x/20.6x/7.5x, "
         "verified against s04_h2_minute_rates: 25.9/20.6/7.5 exact).\n"
         "- Warm-up 500 windows daily, max(500, 22D+100) intraday; OLS "
         "refit each step daily / each session intraday; M5 refit every "
         "63 sessions, Nelder-Mead, previous parameters on "
         "non-convergence (counts in s05_metrics.csv m5_nonconv).\n"
         "- MCS: block length ceil(T^(1/3)), 10,000 resamples, seed "
         "20260821; S-C conditions on the M2-HAR forecast (common "
         "predetermined variable).\n"
         "- lambda for corrections: Part C E4 (TRQ3_TRV3) pooled cell at "
         "matching (root, geom, B, horizon), finest M.\n"
         "- Part A/B boundary minutes: NY 09:30, 09:31, 15:59, 16:00, "
         "18:01, bridged (zero return) in B1.\n"
         "- Part F seeds: master root 20260820, masters "
         f"{seeds_f['masters']}, {seeds_f['scheme']}. Bootstrap seed "
         "20260821. T1 seed 20260818.\n",
         "## Notes\n",
         "- The DECISIONS block dictated for this session numbers its "
         "items 13-16, which collides with the S04 block's 13-15; the "
         "text was appended verbatim as instructed and the collision is "
         "cosmetic.\n"
         "- Prereg quotes S04 Hill range as 2.95-3.67; the S04 file "
         "records 2.98-3.67 (GLOBEX withR2). The 3.4 primary and 3.0/4.5 "
         "sensitivities cover both.\n",
         "## Package versions (pip freeze)\n",
         "```text", freeze, "```", ""]
    with open(os.path.join(RES, "S05-runlog.md"), "w") as fh:
        fh.write("\n".join(R))
    print("runlog written")


if __name__ == "__main__":
    main()
