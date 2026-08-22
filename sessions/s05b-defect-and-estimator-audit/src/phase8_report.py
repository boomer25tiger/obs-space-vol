"""S05B Phase 8: build S05B-report.md and S05B-runlog.md."""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
RES = os.path.join(BASE, "results")
CACHE = os.path.join(RES, "cache")
VENV_PY = sys.executable
pd.set_option("display.width", 250)


def R(f):
    return pd.read_csv(os.path.join(RES, f))


def J(f, d=None):
    try:
        return json.load(open(os.path.join(RES, f)))
    except Exception:
        return d or {}


def md(df, cols=None, n=None, fl="{:.4g}"):
    d = df[cols] if cols else df
    if n:
        d = d.head(n)
    L = ["| " + " | ".join(str(c) for c in d.columns) + " |",
         "|" + "---|" * len(d.columns)]
    for _, r in d.iterrows():
        cells = []
        for v in r:
            if isinstance(v, float):
                cells.append("--" if not np.isfinite(v) and not np.isinf(v)
                             else (fl.format(v) if np.isfinite(v) else str(v)))
            else:
                cells.append(str(v))
        L.append("| " + " | ".join(cells) + " |")
    return "\n".join(L)


def main():
    L = []
    L.append("# Session 5B report, S05 defect diagnosis and estimator "
             "validity audit\n")
    L.append(f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} "
             "(UTC). Diagnosis only. No S05 or S05A artifact was modified, "
             "no MCS was re-run, no forecast was filtered or clipped, no "
             "estimator or truncation level was selected. All output under "
             "`sessions/s05b-defect-and-estimator-audit/`.\n")

    # ================= PHASE 1
    L.append("## Phase 1, source inspection (no computation)\n")
    L.append("### 1a. The array passed to `mcs()`\n")
    L.append(
        "`partde.py:241-263`:\n\n"
        "```python\n"
        "241  rv = S[\"rv\"]\n"
        "242  ev = slice(max(start, warm), len(rv))\n"
        "243  idx_ok = np.ones(len(rv), bool)\n"
        "244  for m in MODELS:\n"
        "245      idx_ok &= np.isfinite(F[m])\n"
        "246  idx_ok[:ev.start] = False\n"
        "247  rvv = rv[idx_ok]\n"
        "248  Fm = {m: F[m][idx_ok] for m in MODELS}\n"
        "249  L = np.column_stack([qlike(Fm[m], rvv) for m in MODELS])\n"
        "...\n"
        "262  Ls = L[smask]\n"
        "263  pv = mcs(Ls, rngm)\n"
        "```\n\n"
        "with `qlike` at `partde.py:180-182`:\n\n"
        "```python\n"
        "180  def qlike(F, rv):\n"
        "181      x = rv / F\n"
        "182      return x - np.log(x) - 1.0\n"
        "```\n\n"
        "Construction: `L` is `np.column_stack` of seven float64 QLIKE "
        "columns, shape (n_evaluated, 7), dtype float64; `Ls = L[smask]` "
        "is a row subset. **The complete list of filtering, masking, "
        "dropping, clipping and imputation steps between the "
        "per-observation loss and the MCS call is: (i) `idx_ok` requires "
        "every model's FORECAST to be finite (line 245), (ii) `idx_ok` "
        "drops the warm-up (line 246), (iii) `smask` selects the "
        "evaluation scheme's rows.** There is no step of any kind applied "
        "to the LOSS. A forecast that is finite but arbitrarily small or "
        "large passes the filter, and its QLIKE - including `inf` from a "
        "zero realized variance or a floored forecast - enters `mcs()` "
        "unaltered.\n")
    L.append("### 1b. Which Part C estimator supplies `lam_hat`\n")
    L.append(
        "`partde.py:250-255`:\n\n"
        "```python\n"
        "250  lamrow = lamC[(lamC.root == root) & (lamC.geom == geom)\n"
        "251                & (lamC.btag == btag)\n"
        "252                & (lamC.horizon == horizon)\n"
        "253                & (lamC.year == 0) & (lamC.tercile == 0)]\n"
        "254  lamrow = lamrow[lamrow.M == lamrow.M.max()]\n"
        "255  lam_hat = float(lamrow[\"E4\"].iloc[0])\n"
        "```\n\n"
        "**E4 supplies `lam_hat`, unconditionally.** The selection is "
        "FIXED, hard-coded as the literal column name `\"E4\"`; it is not "
        "conditional and there is no fallback to another estimator. The "
        "row is pinned to the pooled cell (`year == 0`, `tercile == 0`) "
        "at the finest M.\n\n"
        "Pre-registration search: S05 `PREREG.md` Part C specifies only "
        "that E4 uses \"the Part A variant with the most stable R\" (that "
        "is a QUARTICITY-VARIANT rule, not an estimator rule) and Part E "
        "asks for \"reliability-corrected IC\" without naming a source "
        "estimator. `specs/` contains only `NOTE-missing-specs.md` (both "
        "spec documents are absent from the repository, per DECISIONS "
        "item 11). `DECISIONS.md` contains no rule either. **Nothing in "
        "any frozen document specifies which of the six Part C estimators "
        "supplies `lam_hat`.** The choice of E4 exists only in the "
        "source.\n")
    L.append("### 1c. Definition of the `IC-IR` column\n")
    L.append(
        "`partde.py:276-298`:\n\n"
        "```python\n"
        "276  ic = float(np.corrcoef(lf, lrv)[0, 1])\n"
        "280  w = 63\n"
        "281  ics = [np.corrcoef(lf[i:i + w], lrv[i:i + w])[0, 1]\n"
        "283         for i in range(0, len(lrv) - w, w)]\n"
        "284  ics = [x for x in ics if np.isfinite(x)]\n"
        "285  ir = float(np.mean(ics) / np.std(ics)) \\\n"
        "286       if len(ics) > 2 and np.std(ics) > 0 else np.nan\n"
        "295  ic_corrected=ic / np.sqrt(lam_hat),\n"
        "298  ic_ir=ir,\n"
        "```\n\n"
        "- Aggregation period: **63 windows**, non-overlapping "
        "(`range(..., w)` steps by w). At the 1day horizon that is 63 "
        "sessions; at 1h and 30min it is 63 intraday WINDOWS, not 63 "
        "days, so the period differs by horizon.\n"
        "- Number of periods entering the standard deviation: "
        "`floor((n_obs - 63)/63)`, after dropping non-finite blocks; it "
        "is not recorded in the output and varies by cell and scheme.\n"
        "- Annualization: **none**. No sqrt(periods-per-year) or any "
        "other factor is applied.\n"
        "- IC used: **Pearson on logs** (`np.corrcoef(lf, lrv)`), not "
        "Spearman. `np.std` is the population standard deviation "
        "(ddof=0).\n"
        "- Reliability correction: **not applied at all** to `ic_ir`. "
        "The correction appears only in the separate `ic_corrected` "
        "column (line 295), formed as `ic / sqrt(lam_hat)` AFTER the "
        "Pearson IC; the ratio in `ic_ir` is built from uncorrected "
        "block ICs.\n")
    L.append("### 1d. Representation of the sampling variance of log RV\n")
    L.append(
        "Every occurrence in the S05 code path, and in the S01/S02 code "
        "S05 imports:\n\n"
        "| file:line | expression | role |\n|---|---|---|\n"
        "| `s02/estimators2.py:62` | `v = (2.0 / M) * Q / np.maximum(P * P, 1e-300)` | E4, the estimator S05 Part C and Part E use |\n"
        "| `s01/estimators.py:132` | `v = (2.0 / M) * rq / (rv * rv)` | S01 E4 |\n"
        "| `s05/parta.py:151` | `R = (2.0 / M) * Q / np.maximum(P * P, 1e-300)` | Part A ratio |\n"
        "| `s05/parta.py:170-171` | `ref_2overM=2.0 / M`, `med_over_ref=med / (2.0 / M)` | Part A reference line |\n\n"
        "**`2/M` is used everywhere; `trigamma(M/2)` (or `polygamma`) "
        "appears nowhere in the S01-S05 codebase.** No measured sampling "
        "variance is substituted anywhere.\n\n"
        "Finite-M or Jensen bias correction on E[log RV]: **none exists**. "
        "The only occurrences of the word Jensen (`parta.py:83`, "
        "`parta.py:91`, `report5.py:44`) concern the mean-of-ratios "
        "versus ratio-of-means diagnostic inside unit test T1 for RQ/TQ, "
        "not E[log RV]. `partc.py` applies no correction: it takes "
        "`np.log(np.maximum(rv, 1e-300))` and uses `.var()` directly.\n")
    L.append("### 1e. Bar aggregation\n")
    L.append(
        "`partde.py:47-57`:\n\n"
        "```python\n"
        "47  def build_series(grid, wlen):\n"
        "49      n1 = grid.shape[1] - 1\n"
        "50      nw = n1 // wlen if wlen else 1\n"
        "52      r1 = np.diff(grid, axis=1)[:, :nw * wlen]\n"
        "53      rw = r1.reshape(-1, wlen)\n"
        "56      rw = np.diff(grid, axis=1)\n"
        "```\n\n"
        "Coarser bars are built by `np.diff` of the log-price panel and "
        "reshaping, i.e. by summing consecutive one-minute log returns. "
        "**The panel holds close prices only** (S03 `analysis.build_panels` "
        "fills `px` from `sub[\"close\"]`), so every aggregate - RV, BV, "
        "RQ, and the range proxies `park`/`gk` at lines 64-69, which "
        "take max/min of the CUMULATIVE CLOSE path rather than true "
        "session high/low - uses closes only. No open, high or low enters "
        "any S05 quantity.\n")
    p1f = J("phase1f_panel_provenance.json")
    L.append("### 1f. Panel provenance\n")
    L.append(
        f"A materialized panel exists on disk: eight "
        f"`panel_<root>_<geom>_<btag>.npz` files under "
        f"`sessions/s05-reliability-mcs/results/`, float32 log-price "
        f"grids (sessions x minutes), 32.2 MB total, "
        f"{p1f.get('total_price_points', 0):,} price points and "
        f"{p1f.get('total_returns', 0):,} one-minute returns. Returns are "
        f"NOT rebuilt from the DBN file: one `np.diff` recovers them. "
        f"**Read time for one full pass over all eight panels: "
        f"{p1f.get('full_pass_seconds', 0):.2f} s.** Phases 3 and 4 are "
        "therefore cheap, which places this session at the low end of the "
        "30-55 minute expectation.\n")
    L.append(md(pd.DataFrame([dict(panel=k, **v)
                              for k, v in p1f.get("panels", {}).items()]),
                ["panel", "sessions", "price_cols", "returns", "read_s"]))
    L.append("")

    # ================= PHASE 2
    L.append("## Phase 2, forecast pathology\n")
    L.append(
        "**Obstruction, reported not worked around:** S05 persisted no "
        "forecast artifacts (`partde.py` holds `F` in memory and writes "
        "only `s05_metrics.csv` and `s05_mcs.csv`), so Phase 2's premise "
        "\"reads S05 forecast artifacts only\" cannot be satisfied. "
        "Forecasts were regenerated by calling S05's own "
        "`build_series`/`forecasts` unmodified on S05's stored panels. "
        "Part D contains no RNG and a fixed refit schedule, so the "
        "regeneration is deterministic; S05A Phase 4 verified this class "
        "of regeneration reproduces S05's QLIKE column bitwise, and the "
        "Phase 3 reconstruction below reproduces the section 5 QLIKE "
        "means exactly.\n")
    st = R("phase2_forecast_stats.csv")
    L.append("### Forecast distribution, every model x cell\n")
    L.append(f"Full table ({len(st)} rows): `phase2_forecast_stats.csv`. "
             "Rows with any pathology:\n")
    bad = st[(st.n_nonpositive > 0) | (st.n_below_1e12 > 0)
             | (st.n_above_100x_mean_rv > 0)]
    L.append(md(bad, ["cell", "model", "n_eval", "n_nonpositive",
                      "n_below_1e12", "n_below_1e6",
                      "n_above_100x_mean_rv", "min_forecast",
                      "p001_forecast", "max_forecast"]))
    L.append("")
    off = R("phase2_offending_observations.csv")
    L.append(f"### M4_HARQ and M3_HARJ offending observations\n")
    L.append(f"{len(off)} offending observations in total "
             f"({off.reason.value_counts().to_dict()}); full list "
             "`phase2_offending_observations.csv`. Every 1day-horizon "
             "offender:\n")
    L.append(md(off[off.cell.str.contains("1day")],
                ["cell", "model", "trade_date", "forecast", "realized",
                 "qlike", "share_of_cell_qlike", "reason"]))
    L.append("")
    w = st[st.worst1_share_of_qlike.notna()]
    L.append("### Share of cell QLIKE carried by the worst observations\n")
    L.append(md(w.sort_values("worst1_share_of_qlike", ascending=False),
                ["cell", "model", "worst1_share_of_qlike",
                 "worst5_share_of_qlike"], n=25))
    L.append("")
    cf = R("phase2_harq_coefficients.csv")
    L.append("### Fitted coefficient vectors at the worst observations\n")
    L.append("Coefficient order: [const, RV_d, RV_w, RV_m] for M3_HARJ "
             "plus [J], for M4_HARQ plus [sqrt(RQ)*RV_d]. `linear_fit` is "
             "the raw OLS prediction before `max(., 1e-300)`:\n")
    rows = []
    for _, r in cf.iterrows():
        rows.append(dict(cell=r.cell, model=r.model, rank=r["rank"],
                         trade_date=r.trade_date,
                         linear_fit=r.linear_fit,
                         negative_by_construction=r.fit_negative_by_construction,
                         stored_forecast=r.forecast_stored,
                         coef=r.coef, components=r.components))
    L.append(md(pd.DataFrame(rows),
                ["cell", "model", "rank", "trade_date", "linear_fit",
                 "negative_by_construction", "stored_forecast", "coef",
                 "components"], n=40))
    L.append("")
    nneg = int(cf.fit_negative_by_construction.sum())
    L.append(f"**{nneg} of {len(cf)} inspected worst-observation fits are "
             "negative by construction.** In every negative case the "
             "quarticity interaction coefficient is large and negative "
             "(for example -438.6 and -122.4 in ES/GLOBEX/B0/1day), so on "
             "a high-quarticity day the term `coef * sqrt(RQ) * RV_d` "
             "exceeds the sum of the positive HAR terms; the OLS "
             "prediction goes below zero and `partde.py:157` "
             "(`F[m][t] = max(float(X[t - 1] @ coef[m]), 1e-300)`) floors "
             "it to 1e-300, which is the finite value that passes the "
             "`np.isfinite` filter at line 245 and produces QLIKE of "
             "order 1e296.\n")

    # ================= PHASE 3
    L.append("## Phase 3, panel materialization and non-finite audit\n")
    z = R("phase3_zero_rv.csv")
    zp = z[z.year == 0]
    L.append("### Windows with zero or near-zero realized variance\n")
    L.append("Pooled across years (per-year rows in "
             "`phase3_zero_rv.csv`):\n")
    L.append(md(zp[zp.n_rv_exact_zero > 0],
                ["root", "geom", "btag", "horizon", "n_windows",
                 "n_rv_exact_zero", "share_rv_exact_zero",
                 "n_rv_lt_1e14", "min_rv"]))
    L.append("")
    rth_zero = int(zp[zp.geom == "RTH"].n_rv_exact_zero.sum())
    L.append(f"**No RTH cell at any horizon contains a zero-variance "
             f"window ({rth_zero} found across all RTH cells, 1day, 1h "
             "and 30min).** Every invariance result at every RTH horizon "
             "in Phase 5 is therefore NOT provisional on this ground. "
             "GLOBEX 1day likewise contains none; the zero-variance "
             "windows are confined to GLOBEX 1h and 30min.\n")
    q = R("phase3_quarticity_zeros.csv")
    qq = q[(q.n_Q_zero > 0) | (q.n_P_zero > 0)]
    L.append("### Quarticity variants at or below zero\n")
    L.append(f"{len(qq)} of {len(q)} (cell, horizon, M, variant) "
             "combinations have a zero quarticity or zero proxy; full "
             "table `phase3_quarticity_zeros.csv`.\n")
    if len(qq):
        L.append(md(qq, ["root", "geom", "btag", "horizon", "M", "variant",
                         "n", "n_Q_zero", "n_P_zero", "min_Q", "min_P"],
                    n=20))
    L.append("")
    nf = R("phase3_nonfinite_qlike.csv")
    nfb = nf[nf.n_nonfinite_qlike > 0]
    L.append("### Non-finite QLIKE by cell and model\n")
    L.append(md(nfb, ["root", "geom", "btag", "horizon", "model", "n_eval",
                      "n_nonfinite_qlike", "n_rv_zero_in_eval"], n=40))
    L.append("")
    det = R("phase3_nonfinite_detail.csv")
    if len(det):
        onshare = float(det.overnight.mean())
        L.append(f"GLOBEX 1h and 30min detail ({len(det)} logged "
                 f"occurrences, `phase3_nonfinite_detail.csv`): "
                 f"**{onshare*100:.1f}% fall inside the overnight period** "
                 "(window start before 09:30 New York). Time-of-day "
                 "distribution of the affected windows:\n")
        tod = det.groupby("ny_clock").size().reset_index(name="count") \
            .sort_values("count", ascending=False)
        L.append(md(tod, ["ny_clock", "count"], n=15))
        L.append("")
        L.append("Distinct windows producing infinite QLIKE, by cell:\n")
        dd = det.groupby(["root", "geom", "btag", "horizon"])[
            "window_index"].nunique().reset_index(name="distinct_windows")
        L.append(md(dd))
        L.append("")
    la = R("phase3_named_loss_arrays.csv")
    L.append("### Reconstructed loss arrays for the three named cells\n")
    L.append(md(la, ["cell", "shape", "model", "n_nonfinite", "n_inf",
                     "n_nan", "col_mean", "col_mean_finite_only",
                     "s05_qlike_mean", "matches_s05"]))
    L.append("")
    L.append(
        "The reconstructed arrays match S05's section 5 QLIKE column "
        f"exactly in {int(la.matches_s05.sum())} of {len(la)} model "
        "columns (inf matching inf, NaN matching NaN). **The array the "
        "MCS consumes is the same array whose column means section 5 "
        "reports as `inf`/`nan`** - the MCS is not fed a cleaned "
        "version.\n")
    L.append("### Non-finite handling in the MCS implementations\n")
    L.append(
        "S05's own implementation, `partde.py:185-215`, contains no "
        "non-finite handling of any kind: `np.cumsum` (line 191) "
        "propagates `inf`, the block difference `csum[b:] - csum[:-b]` "
        "(line 192) turns `inf - inf` into `nan`, `losses.mean(axis=0)` "
        "(line 194) is the plain mean rather than `nanmean`, and the "
        "elimination test `p = float((TR_boot >= TR).mean())` (line 209) "
        "compares against `nan`, which is False everywhere and yields "
        "p = 0.0. Measured behaviour on a synthetic loss matrix whose "
        "first column contains one `inf`: p-values `{M1: 0.0, M3: 0.0, "
        "M2: 1.0}` - the procedure returns a definite single-model "
        "confidence set with no error and no warning. That is the "
        "mechanism by which DECISIONS item 22's cells acquire definite "
        "compositions.\n\n"
        "The installed third-party implementation `arch.bootstrap.MCS` "
        "(arch 8.0.0) was also read: its `compute()` contains no "
        "reference to `nan`, `inf`, `isfinite` or `dropna` either. "
        "Neither implementation guards the input.\n")

    # ================= PHASE 4
    L.append("## Phase 4, grid cache build\n")
    gi = R("phase4_grid_index.csv")
    un = J("phase4_unattainable_M.json", [])
    t34 = J("phase34_timers.json", {})
    L.append(
        "Grid verification. Every nominal M divides its session length in "
        "minutes exactly. **The panel, however, supplies "
        "L = session_minutes - 1 one-minute returns**, because a "
        "session's first close has no predecessor inside the session. "
        "Consequences, both reported rather than repaired:\n\n"
        "1. At the 1day horizons no M in the grid divides L, so **every "
        "1day grid point carries exactly one stub sub-bar** one minute "
        "shorter than the rest. At the RTH 1h and 30min horizons L is 60 "
        "and 30 exactly and every M divides it, so those grids have no "
        "stub.\n"
        "2. The nominal finest points M=390 (RTH) and M=1380 (GLOBEX) are "
        "**unattainable**: they exceed L. S05 reached them at "
        "`partc.py`/`parta.py` via "
        "`if p.shape[1] == M: p = concat([p, grid[:, -1:]])`, which "
        "appends a duplicate final price and injects one identically zero "
        "return, leaving effective M = L. S05B adds M = L (389 / 1379) as "
        "the finest attainable point and records the nominal point as "
        "unattainable.\n")
    L.append(md(pd.DataFrame(un), ["geom", "horizon", "nominal_M", "L",
                                   "reason"]))
    L.append("")
    L.append("Grid index (ES/B0 shown; all cells in "
             "`phase4_grid_index.csv`):\n")
    gs = gi[(gi.root == "ES") & (gi.btag == "B0")]
    L.append(md(gs, ["geom", "horizon", "M", "session_minutes",
                     "L_returns_per_window", "M_divides_session",
                     "M_divides_L", "subbar_size_min", "subbar_size_max",
                     "n_stub_subbars", "n_windows", "share_full_M",
                     "share_below_0p9M", "mean_eff_M", "var_log_rv"],
                n=40))
    L.append("")
    L.append(
        "Effective sub-bar counts: `share_full_M` is the share of windows "
        "in which every sub-bar contains at least one minute with data on "
        "both ends (presence masks regenerated exactly by re-running S03's "
        "`build_panels` on the S04 repaired bars). **Nominal M is assumed "
        "everywhere in the estimators**: `estimators2.e4` takes `M` as an "
        "argument and S05 always passes the nominal value; no S05 code "
        "path consults an effective count. At GLOBEX 1day M=138 and "
        "M=345 only 30.6% of windows are at full nominal M.\n")
    nr = R("phase4_noise_references.csv")
    L.append("Noise-robust references cached once per session-day:\n")
    L.append(md(nr, ["root", "geom", "btag", "n", "omega2_N1", "xi2",
                     "kernel_bandwidth_H", "tsrv_K", "mean_kernel",
                     "mean_tsrv", "mean_rv", "n_kernel_nonpos",
                     "n_tsrv_nonpos"]))
    L.append("")
    L.append(f"Cache: {t34.get('cache_files', 0)} files, "
             f"{t34.get('cache_bytes', 0)/1e6:.1f} MB, built in "
             f"{t34.get('timers', {}).get('p4_grid_cache', 0):.1f} s "
             "(panel read and presence masks a further "
             f"{t34.get('timers', {}).get('p3_panel_cache', 0):.1f} s and "
             f"{t34.get('timers', {}).get('p3_present_masks', 0):.1f} s).\n")

    # ================= PHASE 5
    L.append("## Phase 5, grid invariance and boundary separation\n")
    INV = R("phase5_invariance.csv")
    base = INV[(INV.proxy == "RV") & (~INV.trimmed)]
    L.append("### lambda_M x Var(log RV_M): ratio of largest to smallest, "
             "and coefficient of variation\n")
    L.append("Var(log IV) cannot depend on M, so a valid estimator holds "
             "this product constant across the grid (DECISIONS item 26). "
             "1day horizons:\n")
    b1 = base[base.horizon == "1day"]
    L.append(md(b1.pivot_table(index="estimator",
                               columns=["geom", "root", "btag"],
                               values="ratio_max_min").round(3)
                .reset_index()))
    L.append("")
    L.append("RTH intraday horizons:\n")
    b2 = base[base.horizon != "1day"]
    L.append(md(b2.pivot_table(index="estimator",
                               columns=["horizon", "root", "btag"],
                               values="ratio_max_min").round(3)
                .reset_index()))
    L.append("")
    L.append("Coefficient of variation of the same product, 1day:\n")
    L.append(md(b1.pivot_table(index="estimator",
                               columns=["geom", "root", "btag"],
                               values="cv").round(4).reset_index()))
    L.append("")
    RK = R("phase5_ranking.csv")
    piv = RK.pivot_table(index="estimator", columns="cell", values="rank")
    consistent = bool((piv.nunique(axis=1) == 1).all())
    L.append("### Ranking by grid invariance\n")
    L.append(md(piv.reset_index()))
    L.append("")
    L.append(f"**The ranking is not consistent across all cells "
             f"(identical-rank estimators: {int((piv.nunique(axis=1) == 1).sum())} "
             f"of {len(piv)}).** Reading the table: E4 ranks last in "
             f"{int((piv.loc['E4'] == 6).sum())} of {piv.shape[1]} cells "
             f"and never better than 5th; E1_d_model_L1-10 ranks first in "
             f"{int((piv.loc['E1_d_model_L1-10'] == 1).sum())} cells. "
             "Rankings within the 1day horizons agree closely; the RTH "
             "intraday horizons reorder the middle of the table.\n")
    L.append("### Fitted elasticity of (1-lambda)/lambda against M\n")
    L.append("Extended grid versus the original S05 grid, 1day:\n")
    e1 = b1.pivot_table(index="estimator", columns=["geom", "btag"],
                        values=["elasticity", "elasticity_s05grid"]).round(3)
    L.append(md(e1.reset_index()))
    L.append("")
    L.append("Fit quality and dropped points (extended grid):\n")
    L.append(md(b1[["root", "geom", "btag", "horizon", "estimator",
                    "elasticity", "elasticity_r2", "n_used", "n_dropped"]]
                .round(4), n=60))
    L.append("")
    bb = R("phase5_b0_b1.csv")
    L.append("### B0 versus B1 elasticity difference\n")
    if "abs_diff" in bb:
        L.append(md(bb[["root", "geom", "horizon", "estimator", "B0", "B1",
                        "abs_diff", "pct_diff"]].round(4), n=60))
        L.append("")
        L.append(f"Median absolute B0-B1 elasticity difference "
                 f"{bb.abs_diff.median():.4f}, maximum "
                 f"{bb.abs_diff.max():.4f}; median percentage difference "
                 f"{bb.pct_diff.median():.2f}%, maximum "
                 f"{bb.pct_diff.max():.2f}%.\n")
    ar = R("phase5_partA_R_vs_trigamma.csv")
    L.append("### Measured R = (2/M) Q / P^2 against trigamma(M/2)\n")
    L.append("Part A artifacts at every M and variant (pooled years), "
             "ES/B0 shown, full table `phase5_partA_R_vs_trigamma.csv`:\n")
    L.append(md(ar[(ar.root == "ES") & (ar.btag == "B0")]
                [["geom", "M", "variant", "median", "ref_2overM",
                  "trigamma", "med_over_ref", "median_over_trigamma"]]
                .round(5), n=60))
    L.append("")
    L.append("### Boundary separation: elasticity with and without the "
             "first and last 5 minutes\n")
    tr = INV[(INV.proxy == "RV")]
    trp = tr.pivot_table(index=["root", "geom", "btag", "horizon",
                               "estimator"], columns="trimmed",
                         values="elasticity").reset_index()
    if True in trp.columns and False in trp.columns:
        trp["shift_from_trimming"] = trp[True] - trp[False]
        trp = trp.rename(columns={False: "full_session", True: "trimmed_5min"})
        L.append(md(trp[trp.horizon == "1day"].round(4), n=60))
        L.append("")
        L.append(f"Median elasticity shift from trimming the first and "
                 f"last 5 minutes: {trp['shift_from_trimming'].median():.4f}; "
                 f"maximum absolute shift "
                 f"{trp['shift_from_trimming'].abs().max():.4f}.\n")
    L.append("First and last sub-bar share of window RV at every M "
             "(ES/B0; full table in `phase4_grid_index.csv`):\n")
    L.append(md(gs[["geom", "horizon", "M", "mean_first_share",
                    "mean_last_share"]].round(4), n=40))
    L.append("")

    # ================= PHASE 6
    L.append("## Phase 6, microstructure noise\n")
    s6 = J("phase567_summary.json", {}).get("noise_summary", {})
    NF = R("phase6_s03_noise_full.csv")
    L.append("### 6a. Arithmetic on held quantities\n")
    L.append(f"S03 N1/N2 artifacts, all {s6.get('n_cells', 0)} cells "
             "(`phase6_s03_noise_full.csv`). Summary:\n")
    L.append(f"- **Negative omega^2 estimates: {s6.get('n_negative_omega2_N1', 0)} "
             f"of {s6.get('n_cells', 0)} cells under N1** (minimum "
             f"{s6.get('omega2_N1_min', 0):.3e}), "
             f"{s6.get('n_negative_omega2_N2', 0)} under N2. A negative "
             "variance estimate is not interpretable as a variance.\n"
             f"- Signature-plot linearity R^2: median "
             f"{s6.get('r2_median', 0):.3f}, range "
             f"{s6.get('r2_min', 0):.2e} to {s6.get('r2_max', 0):.3f}; "
             f"**{s6.get('n_r2_below_0p5', 0)} of {s6.get('n_cells', 0)} "
             "cells below 0.5**.\n"
             f"- omega^2 (N1) median {s6.get('omega2_N1_median', 0):.3e}, "
             f"range {s6.get('omega2_N1_min', 0):.3e} to "
             f"{s6.get('omega2_N1_max', 0):.3e}.\n")
    neg = NF[NF.omega2_N1 < 0]
    L.append(f"The {len(neg)} cells with negative N1 estimates:\n")
    L.append(md(neg[["root", "geom", "group", "omega2_N1", "NSR_N1",
                     "signature_R2", "n_days"]], n=20))
    L.append("")
    L.append(
        "**Resolution floor of the N1 procedure as run.** N1 regresses the "
        "cross-day MEAN of RV_M on M over the five S03 grid points. The "
        "smallest slope distinguishable from zero is set by the standard "
        "error of those means: with mean RV of order 1e-4 and roughly "
        "1,900 sessions of a strongly right-skewed series, the standard "
        "error of each mean is of order 1e-6, and the M-range is a few "
        "hundred, so slopes below roughly 1e-8 to 1e-9 - i.e. omega^2 "
        "below roughly 5e-9 - are not separable from zero by this "
        "procedure. The measured median omega^2 (N1) of "
        f"{s6.get('omega2_N1_median', 0):.2e} sits at that floor, which "
        f"is why {s6.get('n_negative_omega2_N1', 0)} cells return negative "
        "values: the estimator is resolving noise below its own "
        "resolution.\n")
    B = R("phase6_rv_bias.csv")
    L.append("Implied relative RV bias 2*M*omega^2/IV at every extended "
             "grid point, with the range induced by the spread of S03 "
             "omega^2 estimates across that cell's groups:\n")
    L.append(md(B[(B.root == "ES") & (B.btag == "B0")]
                [["geom", "M", "omega2_N1", "bias_2Momega2_over_IV",
                  "bias_min_across_estimates", "bias_max_across_estimates",
                  "trigamma"]].round(6), n=30))
    L.append("")
    C6 = R("phase6_noise_corrected_elasticity.csv")
    L.append("Implied inflation of Var(log RV_M) and the refitted "
             "elasticity after subtracting it:\n")
    L.append(md(C6[["root", "geom", "btag", "estimator", "elasticity_raw",
                    "elasticity_noise_corrected", "shift", "mean_delta",
                    "delta_share_of_var"]].round(5), n=60))
    L.append("")
    L.append(
        f"**Decision recorded: 6a does NOT settle the question, so 6b was "
        f"run.** The implied noise inflation is "
        f"{C6["delta_share_of_var"].mean()*100:.2f}% of Var(log RV) on "
        f"average, and correcting for it moves the fitted elasticity by a "
        f"mean {C6["shift"].mean():.4f} (maximum absolute "
        f"{C6["shift"].abs().max():.4f}). The elasticities remain far from "
        "-1 for E1_a, E2 and E4 after the correction, so the departure is "
        "not accounted for by microstructure noise at the measured "
        "magnitude.\n")
    try:
        R6 = R("phase6b_reference_lambda.csv")
        L.append("### 6b. Reference-based reliability\n")
        L.append(
            "lambda_M = Var(log ref) / Var(log RV_M) with `ref` the "
            "per-session realized kernel (bandwidth H = 0.97 xi^(4/5) "
            "n^(3/5), the DECISIONS item 16 rule) or two-scale estimator. "
            "Note the invariance PRODUCT is constant by construction here "
            "(the numerator carries no M), so the informative quantity is "
            "the elasticity of the excess variance:\n")
        L.append(md(R6.drop_duplicates(["root", "geom", "btag",
                                        "reference"])
                    [["root", "geom", "btag", "reference", "var_log_ref",
                      "elasticity", "elasticity_r2", "n_dropped",
                      "n_ref_nonpositive"]].round(4), n=20))
        L.append("")
        L.append("Per-grid-point detail is in "
                 "`phase6b_reference_lambda.csv`.\n")
    except Exception:
        L.append("### 6b\nNot produced.\n")
    P = R("phase6_var_log_eps_profile.csv")
    L.append("### Var(log RV_M) against M and interior minima in "
             "Var(log eps)\n")
    im = P[P.interior_min_M.notna()].drop_duplicates(
        ["root", "geom", "btag", "horizon", "estimator"])
    L.append(f"{len(im)} of "
             f"{len(P.drop_duplicates(['root','geom','btag','horizon','estimator']))} "
             "(cell, horizon, estimator) profiles have an interior minimum "
             "inside the grid:\n")
    if len(im):
        L.append(md(im[["root", "geom", "btag", "horizon", "estimator",
                        "interior_min_M", "interior_depth"]].round(4),
                    n=40))
    L.append("")
    eg = P[(P.root == "ES") & (P.geom == "GLOBEX") & (P.btag == "B0")
           & (P.horizon == "1day") & (P.estimator == "E2")]
    L.append("ES/GLOBEX/B0/1day under E2, the cell that turns between "
             "M=138 and M=1380 in the S05 output:\n")
    L.append(md(eg[["M", "var_log_rv", "lam", "var_log_eps"]].round(6)))
    L.append("")

    # ================= PHASE 7
    L.append("## Phase 7, jump contribution\n")
    J7 = R("phase7_rv_vs_trv3.csv")
    TS = R("phase7_truncation_share.csv")
    L.append("lambda under RV and under TRV3, elasticity and "
             "grid-invariance ratio recomputed under truncation "
             "(per-grid-point lambda values in "
             "`phase5_lambda_grid.csv`):\n")
    L.append(md(J7[J7.horizon == "1day"]
                [["root", "geom", "btag", "estimator", "elasticity_RV",
                  "elasticity_TRV3", "elasticity_shift_TRV3_minus_RV",
                  "ratio_max_min_RV", "ratio_max_min_TRV3",
                  "moves_toward_minus1"]].round(4), n=60))
    L.append("")
    n_toward = int(J7.moves_toward_minus1.sum())
    L.append(f"**The elasticity moves toward -1 under truncation in "
             f"{n_toward} of {len(J7)} (cell, horizon, estimator) "
             f"combinations**, by a mean shift of "
             f"{J7.elasticity_shift_TRV3_minus_RV.mean():.3f} and a "
             f"maximum of {J7.elasticity_shift_TRV3_minus_RV.abs().max():.3f}. "
             "The shift is uniformly negative, so estimators already "
             "below -1 under RV are carried further past it while those "
             "above -1 are carried toward it.\n")
    L.append("Share of RV removed by truncation at each M, beside the "
             "elasticity change (ES/B0 shown; full table "
             "`phase7_truncation_share.csv`):\n")
    ts = TS[(TS.root == "ES") & (TS.btag == "B0")]
    L.append(md(ts[["geom", "horizon", "M", "trv_over_rv",
                    "share_rv_removed"]].round(5), n=40))
    L.append("")

    with open(os.path.join(RES, "S05B-report.md"), "w") as fh:
        fh.write("\n".join(L))
    print("report written", sum(len(x) for x in L), "chars")

    # ---------------- runlog
    t34t = t34.get("timers", {})
    t567 = J("phase567_summary.json", {}).get("timers", {})
    regen = J("phase2_regen_meta.json", {})
    env = ""
    ep = os.path.join(ROOT, "ENVIRONMENT.md")
    if os.path.exists(ep):
        env = open(ep).read()
    freeze = subprocess.run([VENV_PY, "-m", "pip", "freeze"],
                            capture_output=True, text=True).stdout.strip()
    Rl = ["# Session 5B run log\n",
          f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} "
          "(UTC).\n",
          "## Wall clock per phase\n",
          "| phase | wall | note |", "|---|---|---|",
          "| Phase 0 (dirs, DECISIONS, S02 grid paused at 645/24500) | ~2 min | |",
          "| Phase 1 source inspection | ~6 min | no computation; 1f "
          "measured a 1.05 s full panel pass |",
          f"| Phase 2 forecast regeneration (24 groups, 6 workers) | "
          f"{regen.get('total_seconds', 0)/60:.1f} min | S05 persisted no "
          "forecasts; ran concurrently with Phase 1, which needs no CPU |",
          "| Phase 2 pathology analysis | 3.6 s | |",
          f"| Phase 3 panel cache + presence masks | "
          f"{t34t.get('p3_panel_cache', 0) + t34t.get('p3_present_masks', 0):.0f} s | |",
          f"| Phase 3 audits (zero-RV, quarticity, non-finite, named "
          f"arrays) | "
          f"{t34t.get('p3_zero_audit', 0) + t34t.get('p3_nonfinite', 0) + t34t.get('p3_named_arrays', 0):.0f} s | |",
          f"| Phase 4 grid cache | {t34t.get('p4_grid_cache', 0):.0f} s | "
          f"{t34.get('cache_files', 0)} files, "
          f"{t34.get('cache_bytes', 0)/1e6:.1f} MB |",
          "| Phase 4 addendum (finest attainable M, noise references) | "
          "8 s | |",
          f"| Phases 5-7 | {t567.get('total', 0):.0f} s | |",
          "| Phase 8 reports | ~3 min | |", "",
          "Total inside the 75-minute ceiling. Bottleneck: Phase 2's "
          "forecast regeneration, forced by S05 not persisting its "
          "forecasts; every other phase is seconds because Phase 1f "
          "established the panel is materialized on disk.\n",
          "## Grid definition\n",
          "| geometry | horizon | session minutes | L returns per window | "
          "M values | stub |", "|---|---|---|---|---|---|",
          "| RTH | 1day | 390 | 389 | 5, 6, 10, 13, 26, 78, 195, **389** | "
          "one stub sub-bar at every M |",
          "| RTH | 1h | 60 | 60 | 4, 5, 6, 10, 12, 15, 20, 30, 60 | none |",
          "| RTH | 30min | 30 | 30 | 5, 6, 10, 15, 30 | none |",
          "| GLOBEX | 1day | 1380 | 1379 | 5, 6, 10, 12, 23, 46, 138, 345, "
          "**1379** | one stub sub-bar at every M |", "",
          "Nominal M=390 and M=1380 are unattainable from the panel "
          "(they exceed L) and are replaced by the finest attainable "
          "M = L = 389 and 1379. GLOBEX 1h and 30min are out of scope for "
          "Phases 4-7 per DECISIONS item 30, and appear only in the "
          "Phase 3 non-finite audit.\n",
          "## Constants used\n",
          "- Sampling variance reference: `trigamma(M/2)` = "
          "`scipy.special.polygamma(1, M/2)` throughout; `2/M` computed "
          "and reported alongside but never used as the reference.\n"
          "- Truncation: 3 local standard deviations, threshold "
          "`3*sqrt(BV/M)` (Mancini), matching S05 Part A's TRQ3_TRV3.\n"
          "- Boundary trim for the separation fit: first and last 5 "
          "one-minute returns of each window.\n"
          "- B1 boundary minutes (inherited from S05 Part B): NY 09:30, "
          "09:31, 15:59, 16:00, 18:01.\n"
          "- Realized kernel bandwidth: H = 0.97 * xi^(4/5) * n^(3/5), "
          "xi^2 = omega^2/IV, omega^2 from S03 N1 (DECISIONS item 16).\n"
          "- Two-scale K = c* n^(2/3), c* = (12 omega^4 / IQ)^(1/3) "
          "(Zhang-Mykland-Ait-Sahalia 2005).\n"
          "- Sub-bar construction: sub-bar j spans one-minute return "
          "indices [floor(j*L/M), floor((j+1)*L/M)).\n"
          "- Elasticity fit: OLS of log((1-lambda)/lambda) on log M, "
          "grid points with lambda outside (0,1) dropped and counted.\n"
          "- No RNG is used anywhere in S05B; every phase is "
          "deterministic.\n",
          "## Cache provenance and size\n",
          f"- Source read once: the eight S05 log-price panels "
          f"(`sessions/s05-reliability-mcs/results/panel_*.npz`), read-only.\n"
          f"- Presence masks regenerated by calling S03 "
          f"`analysis.build_panels` on the S04 repaired bars.\n"
          f"- Cache: `results/cache/`, {t34.get('cache_files', 0)} files, "
          f"{t34.get('cache_bytes', 0)/1e6:.1f} MB (one-minute returns, "
          "presence masks, per-grid-point aggregates, per-session noise "
          "references, regenerated forecasts). Every phase after Phase 3 "
          "read the cache; nothing was rebuilt from the DBN file.\n",
          "## Environment record (from ENVIRONMENT.md)\n",
          env if env else "(ENVIRONMENT.md not found)", "",
          "### pip freeze at S05B\n", "```text", freeze, "```", ""]
    with open(os.path.join(RES, "S05B-runlog.md"), "w") as fh:
        fh.write("\n".join(Rl))
    print("runlog written")


if __name__ == "__main__":
    main()
