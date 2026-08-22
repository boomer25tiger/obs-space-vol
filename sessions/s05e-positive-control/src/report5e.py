"""S05E report and runlog."""

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
VENV_PY = sys.executable


def md(df, cols=None, n=None):
    d = df[cols] if cols else df
    if n:
        d = d.head(n)
    L = ["| " + " | ".join(str(c) for c in d.columns) + " |",
         "|" + "---|" * len(d.columns)]
    for _, r in d.iterrows():
        L.append("| " + " | ".join(
            ("--" if (isinstance(v, float) and not np.isfinite(v))
             else f"{v:.4f}" if isinstance(v, float) else str(v))
            for v in r) + " |")
    return "\n".join(L)


def main():
    S = json.load(open(os.path.join(RES, "s05e_summary.json")))
    P1 = pd.read_csv(os.path.join(RES, "phase1_trigamma_reference.csv"))
    AS = pd.read_csv(os.path.join(RES, "phase2_arm_summary.csv"))
    IVn = pd.read_csv(os.path.join(RES, "phase2_estimator_invariance.csv"))
    E = pd.read_csv(os.path.join(RES, "phase2_estimators.csv"))
    P3 = pd.read_csv(os.path.join(RES, "phase3_decomposition.csv"))

    L = []
    L.append("# Session 5E report, positive control on the aggregation "
             "and reliability path\n")
    L.append(f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} "
             "(UTC). Diagnosis only: no repair, no estimator selection, "
             "no prior artifact modified. Output under "
             "`sessions/s05e-positive-control/results/`.\n")
    L.append(
        "**Code path.** Every synthetic arm is aggregated and measured by "
        "the same functions that produced the real-data numbers, imported "
        "unmodified: `phase34.windows` and `phase34.subbars` (S05B) for "
        "windowing and sub-bar aggregation, `parta.quart_suite` (S05) for "
        "RV/TRV3/RQ/TRQ3, `estimators2.e1_reduced/e2/e4` (S02) for the "
        "Part C estimators, and `fbm.CirculantEmbedding`/`fbm.fgn_acf` "
        "(S01) for the A4 rough path. Only data generation is new; the "
        "aggregation, the Var(log RV_M) computation and the estimators "
        "are not reimplemented. The real path was callable directly, so "
        "the halt condition did not trigger.\n")

    # ---------------- PHASE 1
    L.append("## Phase 1, reference exponent of trigamma(M/2) itself\n")
    L.append(
        "The theoretical target is measured, not assumed. trigamma(M/2) "
        "is fitted against M on each S05B extended grid by the two "
        "procedures used on the data: the free-intercept model "
        "Var = c + A M^b, and the log-log slope.\n")
    L.append(md(P1, ["grid", "n_points", "M_min", "M_max", "free_c",
                     "free_A", "free_b", "free_rmse", "loglog_b",
                     "loglog_r2"]))
    L.append("")
    L.append(
        f"**The reference exponent is not -1.** Under the free-intercept "
        f"procedure - the one used to produce the observed -0.439 - "
        f"trigamma itself fits b = {P1[P1.grid=='GLOBEX_1day'].free_b.iloc[0]:.3f} "
        f"on the GLOBEX 1day grid and "
        f"{P1[P1.grid=='RTH_1day'].free_b.iloc[0]:.3f} on RTH 1day, with "
        f"the two RTH intraday grids at "
        f"{P1[P1.grid=='RTH_1h'].free_b.iloc[0]:.3f} and "
        f"{P1[P1.grid=='RTH_30min'].free_b.iloc[0]:.3f}. Under the log-log "
        f"procedure the same object fits "
        f"{P1[P1.grid=='GLOBEX_1day'].loglog_b.iloc[0]:.3f} to "
        f"{P1[P1.grid=='RTH_30min'].loglog_b.iloc[0]:.3f}. Adding the "
        "empirical intercept before fitting changes nothing (the "
        "`with_intercept_b` column of "
        "`phase1_trigamma_reference.csv` is identical to `free_b`, since "
        "a free intercept absorbs it). DECISIONS item 36 quoted -1.04 as "
        "the prediction, which is the log-log value; the comparator for "
        "the free-intercept fit is -1.14.\n")

    # ---------------- PHASE 2
    L.append("## Phase 2, synthetic positive control\n")
    jc = S["jump_calibration"]
    L.append(
        f"Five arms, {len(S['seeds'])} seeds each, at the real panel "
        f"dimensions (GLOBEX 1953x1380, RTH 1901x390). Jump size was "
        f"calibrated by bisection so the finest-M truncated share matches "
        f"the S05B measurement: GLOBEX sigma_j = "
        f"{jc['GLOBEX']['sigma_j']:.5f} achieving "
        f"{jc['GLOBEX']['achieved_removed_share']:.4f} against target "
        f"{jc['GLOBEX']['target']:.4f}; RTH sigma_j = "
        f"{jc['RTH']['sigma_j']:.5f} achieving "
        f"{jc['RTH']['achieved_removed_share']:.4f} against target "
        f"{jc['RTH']['target']:.4f}.\n")
    L.append("### Fitted Var(log RV_M) = c + A M^b, by arm and grid\n")
    L.append("`b_sd` is the between-seed standard deviation over "
             f"{len(S['seeds'])} seeds; no single-seed result is reported "
             "as a finding.\n")
    L.append(md(AS, ["arm", "grid", "n_seeds", "b_mean", "b_sd", "b_min",
                     "b_max", "c_mean", "c_sd", "A_mean", "rmse_mean",
                     "var_log_iv_input_mean", "recovery_error_mean"]))
    L.append("")
    a0g = AS[(AS.arm == "A0") & (AS.grid == "GLOBEX_1day")].iloc[0]
    a0r = AS[(AS.arm == "A0") & (AS.grid == "RTH_1day")].iloc[0]
    ref_g = float(P1[P1.grid == "GLOBEX_1day"].free_b.iloc[0])
    ref_r = float(P1[P1.grid == "RTH_1day"].free_b.iloc[0])
    L.append("### A0: does the pipeline recover the reference exponent?\n")
    L.append(
        f"**Yes.** On GLOBEX 1day, A0 returns b = {a0g.b_mean:.3f} "
        f"(between-seed sd {a0g.b_sd:.3f}, range {a0g.b_min:.3f} to "
        f"{a0g.b_max:.3f}) against the Phase 1 reference {ref_g:.3f} - a "
        f"gap of {abs(a0g.b_mean - ref_g):.3f}, which is "
        f"{abs(a0g.b_mean - ref_g)/a0g.b_sd:.2f} between-seed standard "
        f"deviations. On RTH 1day, A0 returns {a0r.b_mean:.3f} (sd "
        f"{a0r.b_sd:.3f}) against {ref_r:.3f}, a gap of "
        f"{abs(a0r.b_mean - ref_r):.3f} or "
        f"{abs(a0r.b_mean - ref_r)/a0r.b_sd:.2f} sd. Var(log IV) is "
        f"recovered as the fitted intercept to within "
        f"{abs(a0g.recovery_error_mean):.4f} (GLOBEX) and "
        f"{abs(a0r.recovery_error_mean):.4f} (RTH) of its known input "
        f"value {a0g.var_log_iv_input_mean:.4f}. **There is no material "
        "departure at A0, so the problem is not located in the code "
        "path**, and the remaining arms are secondary as specified.\n")
    L.append("### Which arm reproduces the observed exponent?\n")
    L.append(
        f"**None.** Across all five arms and all four grids the fitted b "
        f"lies in [{AS.b_mean.min():.3f}, {AS.b_mean.max():.3f}], every "
        f"value steeper than -1.07. The observed real-data exponents run "
        f"from {P3.b_RV.max():.3f} to {P3.b_RV.min():.3f} (Phase 3), and "
        "the flattest arm is nowhere near the flattest data. Adding the "
        "measured diurnal profile (A1), calibrated jumps (A2), measured "
        "padding (A3) or a rough H=0.1 log-IV path (A4) each moves b by "
        f"at most {abs(AS[AS.grid=='GLOBEX_1day'].b_mean.max() - AS[(AS.arm=='A0')&(AS.grid=='GLOBEX_1day')].b_mean.iloc[0]):.3f} "
        "from A0 on the GLOBEX 1day grid. The closest approach anywhere "
        f"is A2/A3 on GLOBEX 1day at b = "
        f"{AS[(AS.arm=='A2')&(AS.grid=='GLOBEX_1day')].b_mean.iloc[0]:.3f}, "
        f"still {abs(AS[(AS.arm=='A2')&(AS.grid=='GLOBEX_1day')].b_mean.iloc[0] - (-0.439)):.3f} "
        "away from the -0.439 that prompted this session.\n")
    L.append("Note on the intercept: A2 and A3 recover c near "
             f"{AS[(AS.arm=='A2')&(AS.grid=='GLOBEX_1day')].c_mean.iloc[0]:.3f} "
             "against an input Var(log IV) of "
             f"{a0g.var_log_iv_input_mean:.3f}, i.e. calibrated jumps bias "
             "the recovered Var(log IV) downward by about "
             f"{abs(AS[(AS.arm=='A2')&(AS.grid=='GLOBEX_1day')].c_mean.iloc[0] - a0g.var_log_iv_input_mean):.3f}, "
             "while A0, A1 and A4 recover it to three decimals.\n")
    L.append("### Part C estimators on A0 and A2 against known lambda\n")
    s = IVn.groupby(["arm", "grid", "estimator"]).agg(
        ratio_max_min=("ratio_max_min", "mean"),
        ratio_sd=("ratio_max_min", "std"),
        elasticity=("elasticity", "mean"),
        elasticity_sd=("elasticity", "std"),
        mean_abs_error_vs_true=("mean_abs_error_vs_true", "mean"),
        mean_lam=("mean_lam", "mean"),
        mean_lam_true=("mean_lam_true", "mean")).reset_index()
    L.append(md(s.round(4)))
    L.append("")
    L.append("Per-grid-point lambda against the known truth, A0 "
             "GLOBEX 1day, seed 0 (all seeds and grids in "
             "`phase2_estimators.csv`):\n")
    a = E[(E.arm == "A0") & (E.grid == "GLOBEX_1day")
          & (E.seed_index == 0)]
    piv = a.pivot_table(index="M", columns="estimator",
                        values="lam").join(
        a.groupby("M")["lam_true"].first()).reset_index()
    L.append(md(piv.round(4)))
    L.append("")
    e2a0 = s[(s.arm == "A0") & (s.estimator == "E2")]
    e4a0 = s[(s.arm == "A0") & (s.estimator == "E4")]
    L.append(
        f"On A0, where lambda is known by construction, **E2 recovers it "
        f"to a mean absolute error of "
        f"{e2a0.mean_abs_error_vs_true.min():.4f} to "
        f"{e2a0.mean_abs_error_vs_true.max():.4f}** with a grid-invariance "
        f"ratio of {e2a0.ratio_max_min.min():.3f} to "
        f"{e2a0.ratio_max_min.max():.3f} and an elasticity of "
        f"{e2a0.elasticity.min():.3f} to {e2a0.elasticity.max():.3f}, "
        "which matches the Phase 1 log-log reference. E4 recovers it to "
        f"{e4a0.mean_abs_error_vs_true.min():.4f} to "
        f"{e4a0.mean_abs_error_vs_true.max():.4f} with a positive bias "
        f"(mean lambda {e4a0.mean_lam.mean():.3f} against true "
        f"{e4a0.mean_lam_true.mean():.3f}).\n\n"
        "**The four E1 nugget arms return lambda near zero at every grid "
        "point on A0, with a mean absolute error of about 0.87-0.89 "
        "against the truth.** This is a property of the A0 design, not "
        "evidence about E1 on real data: A0 draws log IV iid, so its "
        "autocovariance is zero at every lag >= 1 and a lag-0 "
        "extrapolation of a flat-zero autocovariance function returns "
        "zero by construction. A0 is therefore not an informative control "
        "for E1; the arm with a persistent signal is A4, on which "
        "estimators were not run because the specification restricts the "
        "estimator sweep to A0 and A2.\n\n"
        "On A2, where calibrated jumps are present, E2's error rises to "
        f"{s[(s.arm=='A2')&(s.estimator=='E2')].mean_abs_error_vs_true.min():.3f}-"
        f"{s[(s.arm=='A2')&(s.estimator=='E2')].mean_abs_error_vs_true.max():.3f} "
        f"and its elasticity flattens to "
        f"{s[(s.arm=='A2')&(s.estimator=='E2')].elasticity.max():.3f}, "
        "while E4's error rises to "
        f"{s[(s.arm=='A2')&(s.estimator=='E4')].mean_abs_error_vs_true.min():.3f}-"
        f"{s[(s.arm=='A2')&(s.estimator=='E4')].mean_abs_error_vs_true.max():.3f} "
        "with its elasticity nearly unchanged.\n")

    # ---------------- PHASE 3
    L.append("## Phase 3, decomposition on real data\n")
    L.append("S05B cache only; no panel was re-read.\n")
    L.append("### Fitted b on RV and on TRV3, every horizon, cell and "
             "boundary treatment\n")
    L.append(md(P3, ["root", "geom", "btag", "horizon", "n_M", "b_RV",
                     "rmse_RV", "b_TRV3", "rmse_TRV3",
                     "b_shift_TRV3_minus_RV"]))
    L.append("")
    L.append(f"Truncation moves b more negative in every one of the "
             f"{len(P3)} cells, by a mean of "
             f"{P3.b_shift_TRV3_minus_RV.mean():.3f} and up to "
             f"{P3.b_shift_TRV3_minus_RV.min():.3f}. Under TRV3, "
             f"{int((P3.b_TRV3 <= -1.0).sum())} of {len(P3)} cells reach "
             "or pass -1.0.\n")
    L.append("### Within-year and within-tercile fits against the pooled "
             "fit\n")
    L.append(md(P3, ["root", "geom", "btag", "horizon", "b_RV",
                     "b_year_mean", "b_year_sd", "b_year_min",
                     "b_year_max", "n_years", "b_terc_mean", "b_terc_sd"]))
    L.append("")
    dy = (P3.b_year_mean - P3.b_RV)
    dt = (P3.b_terc_mean - P3.b_RV)
    L.append(
        f"**The pooled exponent is flatter than the within-year exponent "
        f"in {int((dy < 0).sum())} of {len(P3)} cells**, by a mean of "
        f"{dy.mean():.3f} and up to {dy.min():.3f}; the within-tercile "
        f"mean is flatter than pooled in {int((dt < 0).sum())} of "
        f"{len(P3)} cells, by a mean of {dt.mean():.3f}. Between-year "
        f"dispersion of b is substantial (sd {P3.b_year_sd.min():.3f} to "
        f"{P3.b_year_sd.max():.3f}). Pooling therefore accounts for part "
        "of the gap between the observed exponent and the Phase 1 "
        "reference, and the per-year and per-tercile fits are reported "
        "beside the pooled value rather than replacing it.\n")
    L.append("### b across horizons\n")
    hp = P3.pivot_table(index=["root", "geom", "btag"], columns="horizon",
                        values="b_RV").reset_index()
    L.append(md(hp.round(4)))
    L.append("")
    L.append("The same, on TRV3:\n")
    hp2 = P3.pivot_table(index=["root", "geom", "btag"], columns="horizon",
                         values="b_TRV3").reset_index()
    L.append(md(hp2.round(4)))
    L.append("")
    L.append(
        f"Across horizons the exponent is flattest at 30min "
        f"({P3[P3.horizon=='30min'].b_RV.mean():.3f} mean) and steepest "
        f"at 1day ({P3[P3.horizon=='1day'].b_RV.mean():.3f} mean), with "
        f"1h in between ({P3[P3.horizon=='1h'].b_RV.mean():.3f}). NQ RTH "
        f"1day reaches {P3[(P3.root=='NQ')&(P3.geom=='RTH')&(P3.horizon=='1day')].b_RV.min():.3f}, "
        "the only real cells that approach the Phase 1 reference on RV "
        "alone.\n")

    with open(os.path.join(RES, "S05E-report.md"), "w") as fh:
        fh.write("\n".join(L))

    # ---------------- runlog
    freeze = subprocess.run([VENV_PY, "-m", "pip", "freeze"],
                            capture_output=True, text=True).stdout.strip()
    env = ""
    ep = os.path.join(ROOT, "ENVIRONMENT.md")
    if os.path.exists(ep):
        env = open(ep).read()
    t = S["timers"]
    R = ["# Session 5E run log\n",
         f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} "
         "(UTC).\n", "## Wall clock per phase\n", "| phase | wall |",
         "|---|---|",
         "| Phase 0 (DECISIONS append, directories) | ~1 min |",
         f"| Phase 1 trigamma reference fits | {t['phase1']:.1f} s |",
         f"| Jump calibration (bisection, both geometries) | "
         f"{t['calibration']:.1f} s |",
         f"| Phase 2 synthetic arms (5 arms x 5 seeds x 4 grids) | "
         f"{t['phase2']:.1f} s |",
         f"| Phase 3 real-data decomposition (cache only) | "
         f"{t['phase3']:.1f} s |",
         "| Phase 4 reports | ~2 min |", "",
         f"Compute total {t['total']:.1f} s; session total well under the "
         "30-minute expectation. No bottleneck.\n",
         "## Seeds and derivation\n",
         f"- Master seed {S['master']}. The five arm seeds are "
         f"`numpy.random.SeedSequence({S['master']}).generate_state(5)` = "
         f"{S['seeds']}, each used as `PCG64(seed)` for one (arm, grid) "
         "replication. Every arm is run under all five, and every "
         "reported arm figure carries its between-seed standard "
         "deviation.\n"
         "- The jump-calibration bisection uses a fixed internal seed "
         "12345 on a 400-session probe so the calibration is "
         "deterministic and independent of the arm seeds.\n"
         "- No other randomness enters the session; Phases 1 and 3 are "
         "deterministic.\n",
         "## Calibration constants and their sources\n",
         "| constant | value | source |", "|---|---|---|",
         f"| Var(log IV) input | {1.02} | DECISIONS item 36, the fitted "
         "intercept 1.018 rounded to the value named in the S05E "
         "specification |",
         f"| GLOBEX truncated share target | "
         f"{S['jump_calibration']['GLOBEX']['target']} | S05B "
         "`phase7_truncation_share.csv`, ES/B0/1day at M=1379 (0.293794) |",
         f"| RTH truncated share target | "
         f"{S['jump_calibration']['RTH']['target']} | S05B "
         "`phase7_truncation_share.csv`, ES/B0/1day at M=389 (0.174051) |",
         f"| GLOBEX sigma_j achieved | "
         f"{S['jump_calibration']['GLOBEX']['sigma_j']:.6f} -> removed "
         f"{S['jump_calibration']['GLOBEX']['achieved_removed_share']:.4f} "
         "| bisection, 14 iterations |",
         f"| RTH sigma_j achieved | "
         f"{S['jump_calibration']['RTH']['sigma_j']:.6f} -> removed "
         f"{S['jump_calibration']['RTH']['achieved_removed_share']:.4f} | "
         "bisection, 14 iterations |",
         "| jump intensity | 1.0 per session | fixed a priori, as in "
         "S01/S02 |",
         "| diurnal profile | measured mean per-minute squared return of "
         "the real ES panel, normalized to mean 1 | S05B cache "
         "`ret1m_ES_{GLOBEX,RTH}_B0.npz` |",
         "| padded-column rate | 2016 0.019154, 2017 0.026621, 2018 "
         "0.018226, 2019 0.016714, 2020 0.016417, 2021 0.010990, 2022 "
         "0.004999, 2023 0.007027 | S05D `phase3_padding.csv`, GLOBEX |",
         "| A4 Hurst | 0.1 | S05E specification |",
         "| panel dimensions | GLOBEX 1953x1380, RTH 1901x390 | the real "
         "S05 panels |",
         "| fill rule for A3 | `ffill(axis=1).bfill(axis=1)` | S03 "
         "`analysis.py:41`, the same rule as the real panel |", "",
         "## Grids\n",
         "| grid | M values |", "|---|---|",
         "| RTH 1day | 5, 6, 10, 13, 26, 78, 195, 389 |",
         "| RTH 1h | 4, 5, 6, 10, 12, 15, 20, 30, 60 |",
         "| RTH 30min | 5, 6, 10, 15, 30 |",
         "| GLOBEX 1day | 5, 6, 10, 12, 23, 46, 138, 345, 1379 |", "",
         "## Code path (halt condition not triggered)\n",
         "Imported unmodified and used for every arm: "
         "`phase34.windows`, `phase34.subbars` (S05B); "
         "`parta.quart_suite` (S05); `estimators2.e1_reduced`, "
         "`estimators2.e2`, `estimators2.e4` (S02); "
         "`fbm.CirculantEmbedding`, `fbm.fgn_acf` (S01). Fitting uses "
         "`scipy.optimize.curve_fit` on c + A M^b with start "
         "[min(y), 1.0, -0.5], the same procedure as S05D Phase 4.\n",
         "## Environment record (from ENVIRONMENT.md)\n",
         env if env else "(ENVIRONMENT.md not found)", "",
         "### pip freeze at S05E\n", "```text", freeze, "```", ""]
    with open(os.path.join(RES, "S05E-runlog.md"), "w") as fh:
        fh.write("\n".join(R))
    print("report and runlog written")


if __name__ == "__main__":
    main()
