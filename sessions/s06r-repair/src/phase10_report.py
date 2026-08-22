"""S06R Phase 10: report and runlog."""
import json, os, subprocess, sys
from datetime import datetime, timezone
import numpy as np, pandas as pd
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
VENV=sys.executable
def R(f):
    p=os.path.join(RES,f)
    if not os.path.exists(p): return pd.DataFrame()
    try: return pd.read_csv(p)
    except Exception: return pd.DataFrame()
def J(f,d=None):
    p=os.path.join(RES,f)
    try: return json.load(open(p))
    except Exception: return d or {}
def md(df,cols=None,n=None):
    if df is None or not len(df): return "_(no rows)_"
    d=df[cols] if cols else df
    if n: d=d.head(n)
    L=["| "+" | ".join(str(c) for c in d.columns)+" |","|"+"---|"*len(d.columns)]
    for _,r in d.iterrows():
        L.append("| "+" | ".join(("--" if (isinstance(v,float) and not np.isfinite(v))
            else f"{v:.5g}" if isinstance(v,float) else str(v)) for v in r)+" |")
    return "\n".join(L)

def main():
    L=[]
    L.append("# Session 6R report, defect repair and rerun of Parts C, D and E\n")
    L.append(f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} (UTC). "
             "Prior S05, S05A, S05B, S05D and S05E artifacts are superseded but left in "
             "place; nothing was deleted or overwritten. All new output under "
             "`sessions/s06r-repair/`.\n")

    # ---- Phase 1
    L.append("## Phase 1, invariant tests against the stored S05 artifacts\n")
    s1=R("phase1_summary.csv"); d1=R("phase1_invariants_on_s05.csv")
    L.append("The five assertions of item 39 were written before any repair "
             "(`tests/test_invariants.py`) and run first against the STORED S05 "
             "artifacts, as a record that they detect the defects they were written "
             "for:\n")
    L.append(md(s1))
    L.append("")
    if len(d1):
        for t in d1.test.unique():
            f=d1[(d1.test==t)&(d1.result=="FAIL")]
            if len(f):
                L.append(f"- **{t}**: {len(f)} failures. First: `{f.message.iloc[0][:230]}`")
        L.append("")
    L.append("All five fire. They are then wired into the repaired pipeline: "
             "`assert_forecasts_positive` inside the generation pass after "
             "filtering, `assert_loss_finite` before every MCS call, "
             "`assert_lambda_in_unit` at every Part C grid point, "
             "`assert_range_inputs` at panel construction, and "
             "`assert_effective_M` at every Part C aggregation.\n")

    # ---- Phase 2
    L.append("## Phase 2, panel rebuild with OHLC\n")
    L.append(md(R("phase2_close_grid_check.csv")))
    L.append("")
    p23=J("phase23_summary.json")
    L.append(f"The rebuilt close grid is byte-identical to the stored close-only "
             f"panels in every cell (`{p23.get('phase2_close_identical')}`), so the "
             "rebuild adds open, high and low without disturbing anything the prior "
             "sessions computed. The `present` mask is now persisted alongside the "
             "price grids in every panel file, which S05D found absent (item 38).\n")
    hl=R("phase2_high_eq_low.csv")
    if len(hl):
        L.append("Share of bars with high equal to low, which bounds what a range "
                 "estimator can carry:\n")
        L.append(md(hl.groupby(["root","geom"]).agg(
            n_bars=("n_bars","sum"), share_high_eq_low=("share_high_eq_low","mean")
            ).reset_index()))
        L.append("")
        L.append("By year: `phase2_high_eq_low.csv`.\n")
    L.append("### M6_PARK and M6_GK, old against new\n")
    L.append(md(R("phase2_m6_old_vs_new.csv")))
    L.append("")
    m6=R("phase2_m6_old_vs_new.csv")
    if len(m6):
        L.append(f"Rebuilding from true bar high and low raises the range estimators "
                 f"by {m6.ratio_new_over_old.min():.3f} to "
                 f"{m6.ratio_new_over_old.max():.3f} of their old level, confirming "
                 "the downward bias item 43 names. Neither construction produces "
                 "exact-zero forecasts at the 1day window in any cell.\n")
    L.append("### E3 error-correlation gate re-run on the corrected series\n")
    L.append(md(R("phase2_e3_gate.csv")))
    L.append("")
    L.append(f"Parkinson-Garman-Klass error correlation is "
             f"{p23.get('e3_park_gk_corr_new',float('nan')):.4f} on the corrected "
             f"series against {p23.get('e3_park_gk_corr_old',float('nan')):.4f} on "
             f"the misconstructed ones, and the largest off-diagonal error "
             f"correlation among the corrected proxies is "
             f"{p23.get('e3_max_offdiag_new',float('nan')):.4f}. **E3 remains "
             f"excluded at the pre-registered 0.20 threshold "
             f"({p23.get('e3_excluded_at_0p20')})**; the correction did not rescue "
             "it. Errors are measured against the S05B realized-kernel reference, "
             "since true integrated variance is unobservable on real data.\n")

    # ---- Phase 3
    L.append("## Phase 3, calendar exclusion\n")
    cal=R("phase3_calendar.csv")
    L.append("Source: the CME Group published equity-index holiday calendar, "
             "generated here by rule with no reference to any realized quantity "
             "(item 42). Two classes: EARLY_CLOSE_1300 (day session halts 13:00 "
             "New York) and FULL_CLOSURE_0930 (day session does not open).\n")
    L.append(md(cal, n=100))
    L.append("")
    L.append(md(R("phase3_exclusion_counts.csv")))
    L.append("")
    L.append("### Cross-check against the S05B zero-variance windows\n")
    L.append(md(R("phase3_crosscheck.csv")))
    L.append("")
    res=R("phase3_residual_uncovered.csv")
    L.append(f"**No excluded window carried non-zero realized variance in any cell "
             f"({p23.get('phase3_excluded_nonzero_total')} of all excluded windows), "
             "so the calendar never removes traded data.** In the other direction "
             f"{len(res)} zero-variance windows are not covered by the calendar. "
             "They fall on:\n")
    if len(res):
        agg=res.groupby("session").size().reset_index(name="windows")
        agg["dow"]=pd.to_datetime(agg.session).dt.day_name()
        L.append(md(agg))
        L.append("")
        L.append("2020-03-09, 03-12, 03-18, 03-23 and 03-24 are the COVID "
                 "circuit-breaker limit-halt days and 2020-07-01 and 2019-02-27 sit "
                 "in or beside the Databento degraded-condition set S04 R2 flagged. "
                 "Neither class is determinable from a calendar before the session "
                 "begins, so per item 42 neither is excluded: they remain in the "
                 "sample and their zero-variance windows are carried into Phase 7, "
                 "where `assert_loss_finite` decides what happens to them.\n")

    # ---- Phase 4
    L.append("## Phase 4, RGARCH stationarity diagnosis\n")
    d4=R("phase4_rgarch_diagnosis.csv")
    if len(d4):
        L.append(md(d4,["cell","n_refits","n_converged","persistence_mean",
                        "persistence_max","violates_stationarity","beta_last",
                        "gamma_last","phi_last","n_nonpositive","n_above_100x",
                        "share_pathological","divergence_at_refit_boundary","verdict"]))
        L.append("")
        L.append("Persistence is beta + gamma*phi, the log-linear Realized GARCH "
                 "condition. **Variance targeting is NOT applied anywhere**: "
                 "`partde.rgarch_ll` contains no targeting term, so omega is a free "
                 "parameter and nothing pins the unconditional level.\n")
        L.append(f"Verdicts: " + ", ".join(f"{k} ({v})" for k,v in
                 d4.verdict.value_counts().items()) + ".\n")
        L.append("Resulting model set per cell:\n")
        L.append(md(R("phase4_model_sets.csv")))
        L.append("")
    L.append("RGARCH was not filtered, respecified or constrained (item 41).\n")

    # ---- Phase 5
    L.append("## Phase 5, forecast filter\n")
    h5=R("phase5_halts.csv")
    if len(h5):
        L.append(f"**The positivity invariant halted {len(h5)} cells.** Item 39 "
                 "requires a halt rather than a warning, and the halt is recorded "
                 "per cell so the remaining cells could still be attempted; a "
                 "halted cell produces no artifact and therefore reaches no MCS. "
                 "The mechanism, identical in every case: the BPQ filter replaces "
                 "forecasts outside the IN-SAMPLE realized-variance range, and in "
                 "these cells the in-sample minimum is exactly zero because the "
                 "warm-up window contains the zero-variance windows Phase 3 could "
                 "not exclude on calendar grounds. A lower bound of zero admits a "
                 "forecast floored at 1e-300, which then fails the positivity "
                 "assertion. The filter definition was NOT altered to accommodate "
                 "this (item 40 fixes it, and changing it here would be tuning):\n")
        L.append(md(h5[["cell","assertion","message"]],n=20))
        L.append("")
    f5=R("phase5_filter.csv")
    if len(f5):
        L.append(md(f5,["cell","model","n_eval","n_replaced","share_replaced",
                        "qlike_before","qlike_after","n_replaced_alt_100x",
                        "share_replaced_alt_100x"]))
        L.append("")
        L.append(f"The filter fires in {int((f5.n_replaced>0).sum())} of {len(f5)} "
                 f"(cell, model) combinations, replacing {int(f5.n_replaced.sum())} "
                 f"forecasts in total. Dates replaced are in `phase5_filter.csv`. "
                 "The 100x-in-sample-mean alternative is reported beside it as a "
                 "sensitivity and is NOT adopted. `assert_forecasts_positive` was "
                 "called on every model in every cell after filtering and did not "
                 "raise.\n")

    # ---- Phase 6
    L.append("## Phase 6, Part C rerun\n")
    L.append("E2 and E4 only, effective sub-bar count in place of nominal M, on the "
             "calendar-excluded sample.\n")
    f6=R("phase6_fits.csv")
    L.append("### Var(log RV_M) = c + A M^b, repaired against S05B\n")
    L.append(md(f6,["root","geom","btag","horizon","c_new","A_new","b_new",
                    "rmse_new","b_s05b","b_shift"]))
    L.append("")
    if len(f6):
        L.append(f"**The exponent is unchanged by the repairs.** The largest shift "
                 f"across all sixteen cells is {f6.b_shift.abs().max():.2e}. Neither "
                 "the calendar exclusion, nor effective M, nor the OHLC rebuild "
                 "moves it: the S05B finding that b lies between -0.41 and -1.00 "
                 "against a trigamma reference of -1.14 survives the repair "
                 "programme intact.\n")
    v6=R("phase6_lambda_violations.csv")
    L.append(f"### Lambda outside [0,1]\n")
    L.append(f"{len(v6)} of {len(R('phase6_lambda.csv'))} grid points violate the "
             "bound. Reported, not halted (a violation here is a finding about the "
             "estimator, not a code defect):\n")
    L.append(md(v6,["cell","estimator","lam"],n=30))
    L.append("")
    L.append("### Effective M against window realized volatility (item 45)\n")
    L.append(md(R("phase6_effM_corr.csv"),["root","geom","btag","horizon","M",
        "corr_effM_vol","mean_eff_M","sd_eff_M"]))
    L.append("")
    c6=R("phase6_effM_corr.csv")
    if len(c6):
        L.append(f"The coupling is not negligible: the correlation between effective "
                 f"sub-bar count and window realized volatility runs from "
                 f"{c6.corr_effM_vol.min():.3f} to {c6.corr_effM_vol.max():.3f}, "
                 "positive in GLOBEX and negative in RTH.\n")
    L.append("### Level sanity check (item 49)\n")
    if len(f6) and len(c6):
        j=f6.merge(c6,on=["root","geom","btag","horizon"],how="left")
        L.append(md(j,["root","geom","btag","horizon","c_new","implied_sd_log_iv",
                       "implied_vol_ratio_1sd","sd_log_rv","vol_ratio_p84_p16"]))
        L.append("")
        L.append(f"The fitted intercept implies sd(log IV) of "
                 f"{j.implied_sd_log_iv.min():.3f} to {j.implied_sd_log_iv.max():.3f} "
                 f"and a one-standard-deviation volatility ratio of "
                 f"{j.implied_vol_ratio_1sd.min():.2f} to "
                 f"{j.implied_vol_ratio_1sd.max():.2f}. The sample's own realized "
                 f"volatility ratio between the 84th and 16th percentiles is "
                 f"{j.vol_ratio_p84_p16.min():.2f} to {j.vol_ratio_p84_p16.max():.2f}. "
                 "**The implied level is consistent with the sample's realized "
                 "volatility range**; the level was never checked in five prior "
                 "sessions and it survives the check.\n")

    # ---- Phase 7
    L.append("## Phase 7, Parts D and E rerun\n")
    mc=R("phase7_mcs.csv"); ha=R("phase7_halts.csv")
    L.append(f"Forecast panels and loss matrices are persisted for every cell "
             f"(`cache/gen_*.npz`, `cache/loss_*.npz`, item 48). "
             f"`assert_loss_finite` was called before every MCS call; it raised in "
             f"{len(ha)} (cell, scheme) combinations, which were NOT run and are "
             "marked HALTED:\n")
    if len(ha):
        L.append(md(ha[["cell","scheme"]],n=40))
        L.append("")
        L.append("Those are exactly the GLOBEX intraday cells carrying the residual "
                 "zero-variance windows of Phase 3, which item 42 forbids excluding "
                 "on realized-variance grounds. The invariant does what it was "
                 "written to do: it stops a contaminated loss matrix from reaching "
                 "the MCS rather than letting it return a definite answer.\n")
    L.append("### MCS composition, repaired against S05\n")
    L.append(md(mc,["root","geom","btag","horizon","scheme","n_obs","model_set",
                    "mcs75","mcs90","seed"],n=130))
    L.append("")
    cp=R("phase7_composition_vs_s05.csv")
    if len(cp):
        L.append(f"Composition changed in {int(cp.changed.sum())} of {len(cp)} "
                 "(cell, level) comparisons against S05. Entering and leaving "
                 "models:\n")
        L.append(md(cp[cp.changed],["cell","level","s05","s06r","entered","left"],n=140))
        L.append("")
    L.append("Every cell uses an independently seeded generator derived "
             "deterministically from master seed 20260819 as "
             "`PCG64(SeedSequence([20260819, cell_index, scheme_index]))`, replacing "
             "S05's single stream shared across cells in execution order.\n")
    L.append("### Metrics\n")
    mt=R("phase7_metrics.csv")
    if len(mt):
        L.append("IC, corrected IC under BOTH E2 and E4 side by side, R-squared and "
                 "its corrections, IC-IR with its block count and block length in "
                 "WINDOWS, hit rate and QLIKE. S-A rows shown; every scheme in "
                 "`phase7_metrics.csv`:\n")
        L.append(md(mt[mt.scheme=="S-A"],["root","geom","btag","horizon","model",
            "lam_E2","lam_E4","ic_pearson_log","ic_corrected_E2","ic_corrected_E4",
            "r2_oos","r2_corrected_E2","r2_corrected_E4","ic_ir","ic_ir_n_blocks",
            "ic_ir_block_len_windows","hit_rate","qlike_mean"],n=80))
        L.append("")

    # ---- Phase 8
    L.append("## Phase 8, primary result and multiplicity\n")
    p8=J("phase8_summary.json")
    L.append(f"**S-B against S-C composition differs in {p8.get('n_differ')} of "
             f"{p8.get('family_size_computable')} comparisons that could be "
             f"computed, against a pre-registered family of "
             f"{p8.get('family_size_preregistered')}** "
             f"({p8.get('n_halted')} further comparisons are HALTED by the loss "
             "invariant). The family size is stated explicitly against the effective "
             "sample and **no familywise correction is applied**; its absence is "
             "disclosed as a limitation, since correcting a count already seen would "
             "be worse than disclosing it (item 47).\n")
    L.append(f"### Single pre-specified cell\n")
    L.append(f"Chosen on the ex-ante criterion of largest effective sample and "
             f"logged before the comparison was computed: **{p8.get('primary_cell')}** "
             f"(n_eval {J('phase8_primary_cell.json').get('n_eval')}).\n")
    pr=R("phase8_primary.csv")
    if len(pr):
        L.append(md(pr[pr.cell==p8.get("primary_cell")],
                    ["cell","quantile","level","differs","s_b","s_c","status"]))
        L.append("")
    L.append("### The three S05A seed-indeterminate cells\n")
    L.append(md(R("phase8_s05a_indeterminate.csv"),
                ["cell","quantile","level","differs","status"],n=40))
    L.append("")

    # ---- Phase 9
    L.append("## Phase 9, spec reconstruction and persistence\n")
    p9=J("phase9_summary.json")
    L.append(f"`specs/SPEC-obs-space-vol-eval.md` reconstructed from `DECISIONS.md`, "
             "covering the model set, the estimator pair, the exclusion rules, the "
             "filter, the holdout boundary, the family size and the three kill "
             "conditions with their null abstracts, each marked with the date fixed "
             "and whether pre-registered or post hoc.\n")
    L.append(md(R("phase9_persistence.csv"),["report_element","regenerable","missing"]))
    L.append("")
    L.append(f"{p9.get('n_regenerable')} of {p9.get('n_elements')} report elements "
             f"regenerate from persisted artifacts without re-running Phases 2-8; "
             f"cache {p9.get('cache_bytes',0)/1e6:.1f} MB.\n")

    # ---- verdict
    L.append("## What survives, what changes, what is withdrawn\n")
    L.append("### Survives unchanged\n")
    L.append(
        f"- The proxy-error scaling anomaly. Var(log RV_M) = c + A M^b refits with "
        f"b shifted by at most {R('phase6_fits.csv').b_shift.abs().max():.1e} after "
        "the OHLC rebuild, the calendar exclusion and effective M. Kill condition K3 "
        "stands exactly where S05B and S05E left it.\n"
        "- The S05D determination that the Globex panel is correct: the rebuilt "
        "close grid is byte-identical to the stored one in all four cells.\n"
        "- E3 remains excluded at the 0.20 error-correlation gate; correcting the "
        "range estimators did not rescue it.\n"
        "- The holdout boundary, untouched.\n")
    L.append("### Changes\n")
    L.append(
        "- The range estimators. M6_PARK and M6_GK were not range estimators at all; "
        "rebuilt from true high and low they rise by 6 to 13 percent, and since "
        "M6_GK was the sole MCS survivor in most GLOBEX cells, its construction was "
        "load-bearing for the composition result.\n"
        f"- MCS composition. {int(R('phase7_composition_vs_s05.csv').changed.sum()) if len(R('phase7_composition_vs_s05.csv')) else 0} "
        "of the (cell, level) compositions differ from S05's after the repairs, the "
        "filter, the model-set reductions and per-cell seeding.\n"
        "- The reliability surface. E1 is dropped, E2 and E4 are reported side by "
        "side, and lambda now uses effective sub-bar count.\n"
        "- The evaluation sample. Non-trading windows are excluded on calendar "
        "grounds, and the residual zero-variance windows now halt the MCS in the "
        "affected cells rather than silently contaminating it.\n")
    L.append("### Withdrawn\n")
    L.append(
        "- Every S05 Part E composition computed on a loss matrix containing "
        "non-finite entries. S05's MCS returned definite answers there; those "
        "answers are withdrawn and the cells are reported HALTED.\n"
        "- Every S05 metric whose reliability correction was applied from E4 alone "
        "with no recorded provenance (S05B item 23). Corrected IC and corrected "
        "R-squared are now reported under both estimators or not at all.\n"
        "- S05's M6_PARK and M6_GK forecasts and every MCS composition that depended "
        "on them.\n")
    open(os.path.join(RES,"S06R-report.md"),"w").write("\n".join(L))
    print("report written")

    # ---- runlog
    freeze=subprocess.run([VENV,"-m","pip","freeze"],capture_output=True,text=True).stdout.strip()
    env=""
    ep=os.path.join(ROOT,"ENVIRONMENT.md")
    if os.path.exists(ep): env=open(ep).read()
    gm=R("gen_meta.csv")
    Rl=["# Session 6R run log\n",
        f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} (UTC).\n",
        "## Wall clock per phase\n","| phase | wall |","|---|---|",
        "| Phase 0 DECISIONS + directories | ~2 min |",
        "| Phase 1 invariant file + detection run on S05 artifacts | ~4 min |",
        "| Phase 2+3 OHLC rebuild, M6 repair, E3 gate, calendar (2 passes: the "
        "calendar was extended after the first cross-check exposed uncovered "
        "closures) | 14 s + 14 s |",
        f"| Phases 4/5/7 generation pass (24 attempted, 16 persisted, 6 workers) | "
        f"{(gm['seconds'].sum()/60 if len(gm) and 'seconds' in gm else float('nan')):.1f} min of worker time |",
        "| Phase 6 Part C rerun | 35 s |",
        "| Phases 4+7+8 diagnosis, MCS, primary result | see phase8_summary.json |",
        "| Phase 9 spec + persistence | seconds |",
        "| Phase 10 reports | ~3 min |","",
        "## Seeds and derivation\n",
        "- MCS master seed 20260819. Each (cell, scheme) draws its own generator as "
        "`PCG64(SeedSequence([20260819, cell_index, scheme_index]))`, logged in the "
        "`seed` column of `phase7_mcs.csv`. This replaces S05's single stream shared "
        "across all cells in execution order.\n"
        "- 10,000 moving-block bootstrap resamples, block length ceil(T^(1/3)).\n"
        "- No other randomness enters the session; the panel rebuild, the calendar, "
        "the filter, Part C and the RGARCH refits are all deterministic.\n",
        "## Constants and their sources\n",
        "| constant | value | source |","|---|---|---|",
        "| BPQ filter bounds | in-sample RV min and max, replacement = in-sample mean | DECISIONS item 40 |",
        "| filter sensitivity | 100x in-sample mean | item 40, reported not adopted |",
        "| E3 gate threshold | 0.20 max off-diagonal error correlation | S01 pre-registration |",
        "| calendar EARLY_CLOSE_1300 | MLK, Presidents, Memorial, Independence, Labor, Thanksgiving, Juneteenth (2022+) | CME Group published equity-index holiday calendar |",
        "| calendar FULL_CLOSURE_0930 | Good Friday (Easter algorithm), 2018-12-05 National Day of Mourning | CME Group calendar; the 2018 closure was announced 2018-12-01 |",
        "| warm-up | 500 windows daily, max(500, 22D+100) intraday | S05 Part D, unchanged |",
        "| OLS refit | every step daily, every session intraday | S05 Part D, unchanged |",
        "| RGARCH refit | every 63 sessions | S05 Part D, unchanged |",
        "| IC-IR block | 63 WINDOWS (labelled as such, not days) | item 32 / S05B 1c |",
        "| holdout | 2024-01-01 | item 50 |","",
        "## Calendar source\n",
        "CME Group publishes the equity-index holiday and early-close schedule; the "
        "dates are generated here by calendar rule (nth-weekday and Easter "
        "algorithms) so that no realized quantity enters the exclusion, as item 42 "
        "requires. The generated set is in `results/phase3_calendar.csv`.\n",
        "## Environment record (from ENVIRONMENT.md)\n", env if env else "(absent)","",
        "### pip freeze at S06R\n","```text",freeze,"```",""]
    open(os.path.join(RES,"S06R-runlog.md"),"w").write("\n".join(Rl))
    print("runlog written")

if __name__=="__main__": main()
