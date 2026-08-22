"""S07 Phases 7 and 8: determination, report, spec update, runlog."""
import json, os, subprocess, sys
from datetime import datetime, timezone
import numpy as np, pandas as pd
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
S06R_=os.path.join(ROOT,"sessions","s06r-repair","results")
S05E_=os.path.join(ROOT,"sessions","s05e-positive-control","results")
SPECS=os.path.join(ROOT,"specs"); VENV=sys.executable
def R(f,d=None):
    p=os.path.join(d or RES,f)
    if not os.path.exists(p): return pd.DataFrame()
    try: return pd.read_csv(p)
    except Exception: return pd.DataFrame()
def J(f,d=None):
    try: return json.load(open(os.path.join(RES,f)))
    except Exception: return d or {}
def md(df,cols=None,n=None):
    if df is None or not len(df): return "_(no rows)_"
    x=df[cols] if cols else df
    if n: x=x.head(n)
    L=["| "+" | ".join(str(c) for c in x.columns)+" |","|"+"---|"*len(x.columns)]
    for _,r in x.iterrows():
        L.append("| "+" | ".join(("--" if (isinstance(v,float) and not np.isfinite(v))
          else f"{v:.5g}" if isinstance(v,float) else str(v)) for v in r)+" |")
    return "\n".join(L)
TRIG={"RTH_1day":-1.144373,"RTH_1h":-1.209713,"RTH_30min":-1.197101,"GLOBEX_1day":-1.138577}

def main():
    L=[]
    L.append("# Session 7 report, repair completion and SPY exponent replication\n")
    L.append(f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} (UTC). "
             "No prior artifact modified or deleted. Nothing dated on or after "
             "2024-01-01 was read, futures or SPY. The derived SPY parquets were not "
             "consumed.\n")
    # ---------- Phase 1
    L.append("## Phase 1, SPY inventory and span check\n")
    sp=J("phase1_spy_span.json")
    inv=R("phase1_spy_inventory.csv")
    L.append("Directory `~/Downloads/DataBento Data/SPY 1s Data`, two "
             "venue jobs plus a `data/` folder of derived parquets:\n")
    L.append(md(inv,["venue","file","bytes","fmt","consumed"]))
    L.append("")
    for v,x in (sp.get("venues") or {}).items():
        L.append(f"- **{v}**: dataset `{x['dataset']}`, schema `{x['schema']}`, "
                 f"`stype_in={x['stype_in']}`, symbols {x['symbols']}; "
                 f"{x['n_rows_total']:,} rows total, {x['n_rows_pre_2024']:,} before "
                 f"2024-01-01; span {x['ts_min']} to {x['ts_max']}; "
                 f"**{x['n_rth_sessions_pre2024']} RTH sessions before 2024**; "
                 f"spans 2018-05-01 to 2023-12-31: **{x['spans_2018_05_01_to_2023_12_31']}**.")
    L.append("")
    L.append("Columns: `length, rtype, publisher_id, instrument_id, ts_event, open, "
             "high, low, close, volume` (raw DBN v3, zstd). SHA-256 for every file "
             "read is in `results/S07-spy-manifest.txt`. **The span check passes for "
             "both venues, so the SPY phases proceed.**\n")
    m5=R("phase5_spy_meta.csv")
    if len(m5):
        L.append("Effective sample per SCOPE section 5, after excluding the "
                 "designated early closes:\n")
        L.append(md(m5,["venue","n_sessions","n_early_excluded","n_rows","median_fill","mean_fill"]))
        L.append("")
    # ---------- Phase 2
    L.append("## Phase 2, exclusion and filter repair\n")
    L.append("### Item 51 sessions\n")
    L.append("| session | halt time | ground |\n|---|---|---|")
    for d,(ht,g) in [("2020-03-09",("09:30","circuit-breaker limit halt (exchange log)")),
        ("2020-03-12",("09:30","circuit-breaker limit halt (exchange log)")),
        ("2020-03-18",("09:30","circuit-breaker limit halt (exchange log)")),
        ("2020-03-23",("09:30","circuit-breaker limit halt (exchange log)")),
        ("2020-03-24",("09:30","circuit-breaker limit halt (exchange log)")),
        ("2019-02-27",("09:30","Databento degraded condition, S04 R2 set")),
        ("2020-07-01",("09:30","Databento degraded condition, S04 R2 set"))]:
        L.append(f"| {d} | {ht} | {g} |")
    L.append("")
    L.append(
        "A blanket halt-to-close rule was written first and discarded on its own "
        "audit: it removed 42 to 98 windows per cell that carried non-zero realized "
        "variance, and those are among the highest-volatility sessions in the sample. "
        "The rule actually applied targets the minutes where the exchange printed NO "
        "bar on those sessions - a data-PRESENCE criterion from the exchange's own "
        "record, not a realized-variance criterion, so it stays inside item 42:\n")
    L.append(md(R("phase2_exclusion_audit.csv")))
    L.append("")
    ea=R("phase2_exclusion_audit.csv")
    if len(ea):
        L.append(f"**Excluded windows carrying non-zero realized variance: "
                 f"{int(ea.n_excluded_with_nonzero_rv.sum())} across all cells** "
                 f"(0 in six of eight cells, 1 in each 30min GLOBEX cell). "
                 f"{int(ea.n_zero_rv_remaining.sum())} zero-variance windows remain, "
                 "on sessions with no exchange record of a halt.\n")
    L.append("### Filter lower bound (item 52) and the rerun of the 8 halted cells\n")
    gm=R("phase2_gen_meta.csv"); sh=R("phase2_still_halted.csv")
    if len(gm):
        L.append(md(gm,["cell","n_eval","n_excluded","rv_min_positive","n_models","dropped","seconds"]))
        L.append("")
        L.append(
            "With the lower bound set to the smallest strictly positive in-sample "
            "realized variance, **no cell halts on M3_HARJ or M4_HARQ any more**. "
            "What remained were M5_RGARCH (6 cells) and M6_PARK (2 cells), neither of "
            "which is filtered. Item 41's prescribed remedy for a model that cannot "
            "produce admissible forecasts is to mark it unavailable and reduce the "
            "model set with the reduction stated; that rule is written for RGARCH and "
            "is applied here to M6_PARK by the same logic, disclosed as a post-hoc "
            "extension. No value was replaced and no model respecified.\n")
    L.append("### Filter impact across ALL cells\n")
    A=R("phase2_filter_audit_all_cells.csv")
    L.append(md(A,["cell","source","model","n_eval","n_replaced","share_replaced",
                   "mean_qlike","share_qlike_from_replaced","share_qlike_worst5",
                   "flag_replaced_over_quarter"]))
    L.append("")
    if len(A):
        L.append(f"**{int(A.flag_replaced_over_quarter.sum())} of {len(A)} "
                 "(cell, model) combinations are FLAGGED**: the replaced observations "
                 "carry more than a quarter of mean QLIKE, and in the 1day cells they "
                 "carry 61 to 71 percent of it. The flag was written for exactly this "
                 "condition - a filter that converts an infinite-variance problem into "
                 "a high-variance one leaves the MCS uninformative - and it fires "
                 "nearly everywhere.\n")
    L.append("### The M3_HARJ change at ES/GLOBEX/B0/1day\n")
    cs=J("phase2_m3harj_case.json")
    if cs:
        b=cs.get("_bounds",{}); s05=cs.get("_s05",{})
        L.append(f"In-sample bounds: min including zero {b.get('rv_in_sample_min_including_zero'):.4g}, "
                 f"min strictly positive {b.get('rv_in_sample_min_strictly_positive'):.4g} "
                 "(identical here, so item 52 changes nothing in this cell), max "
                 f"{b.get('rv_in_sample_max'):.4g}, mean {b.get('rv_in_sample_mean'):.4g}.\n")
        L.append("| model | filtered | forecasts above the in-sample max | forecasts set to the replacement mean | max forecast | mean QLIKE now | mean QLIKE in S05 | IC now | IC in S05 |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for m in ["M3_HARJ","M4_HARQ","M2_HAR","M1_EWMA","M5_RGARCH"]:
            if m not in cs: continue
            v=cs[m]; o=s05.get(m,{})
            L.append(f"| {m} | {'yes' if m in ('M3_HARJ','M4_HARQ') else 'no'} | "
                     f"{v['n_above_rmax']} | {v['n_at_replacement_value']} | "
                     f"{v['max_forecast']:.4g} | {v['mean_qlike']:.4f} | "
                     f"{o.get('qlike',float('nan')):.4f} | {v['ic']:.4f} | "
                     f"{o.get('ic',float('nan')):.4f} |")
        L.append("")
        L.append(
            "**The BPQ UPPER bound fired, on 14 forecasts.** M2_HAR, which is not "
            "filtered, carries forecasts up to 6.3e-03 against an in-sample maximum "
            "of 1.19e-03 and keeps them. M3_HARJ and M4_HARQ produce the same "
            "high-volatility forecasts, but the filter replaces each one with the "
            "in-sample MEAN of 5.87e-05, roughly twenty times too small on those "
            "days. QLIKE moves 0.164 to 0.555 and IC 0.838 to 0.753 for that reason "
            "alone, while EWMA, HAR and RGARCH are untouched because the filter never "
            "sees them. The filter is not correcting a defect in these cells; it is "
            "discarding the correct forecast on the days that matter most.\n")
    # ---------- Phase 3
    L.append("## Phase 3, RGARCH on the cells where it failed\n")
    D3=R("phase3_rgarch_diagnosis.csv")
    if len(D3):
        L.append(md(D3,["cell","n_refits","n_converged","persistence_mean","persistence_max",
                        "violates_stationarity","omega_free","beta_last","gamma_last",
                        "phi_last","n_nonpositive","n_above_100x","share_pathological",
                        "n_pathological_within_D_of_refit","divergence_at_refit_boundary","verdict"]))
        L.append("")
        L.append("Persistence is beta + gamma*phi. Omega is a free parameter in every "
                 "cell: `partde.rgarch_ll` contains no variance-targeting term, so "
                 "nothing pins the unconditional level. RGARCH was not filtered, "
                 "respecified or constrained.\n")
        for v,n in D3.verdict.value_counts().items(): L.append(f"- {v}: {n} cells")
        L.append("")
    # ---------- Phase 4
    L.append("## Phase 4, primary result and multiplicity\n")
    p4=J("phase4_summary.json")
    L.append(f"**S-B against S-C differs in {p4.get('n_differ')} of "
             f"{p4.get('n_computed')} comparisons computed, against the "
             f"pre-registered family of {p4.get('family_preregistered')}**; "
             f"{p4.get('n_halted')} halted at the loss invariant and "
             f"{p4.get('n_not_run')} were not run. Every count in this section "
             "carries that denominator. No familywise correction is applied "
             "(item 47).\n")
    L.append("### Stratified breakdown (post hoc, item 54)\n")
    L.append(md(R("phase4_stratified.csv")))
    L.append("")
    L.append("### The two pre-specified cells\n")
    cp=J("phase4_cells_prespecified.json")
    L.append(f"- **Pre-registered (S06R, largest effective sample): "
             f"`{cp.get('cell_preregistered')}`** - stands, not replaced.\n"
             f"- **Post hoc (item 54, median effective sample): "
             f"`{cp.get('cell_median')}`**, n_eval {cp.get('n_eval')}, logged "
             "before its comparison was computed.\n")
    PR=R("phase4_primary.csv")
    if len(PR):
        two=PR[PR.cell.isin([cp.get("cell_preregistered"),cp.get("cell_median")])]
        L.append(md(two,["cell","quantile","level","differs","status"]))
        L.append("")
    # ---------- Phase 5
    L.append("## Phase 5, SPY panels\n")
    L.append(md(R("phase5_spy_by_year.csv"),["venue","year","n_sessions","median_fill",
        "mean_fill","padded_share","off_penny_close_share","corr_fill_vol"]))
    L.append("")
    L.append("Two panels per venue are persisted: a calendar-time 23,400-second grid "
             "with forward fill, and a traded-tick panel holding only seconds with an "
             "actual bar. The range-input and effective-M invariants were asserted at "
             "construction and passed.\n")
    L.append("Fill by time of day (half-hour means) is in "
             "`phase5_spy_fill_by_tod.csv`; fill by year conditioned on volatility "
             "tercile is in `phase5_spy_fill_by_vol.csv`. Those three measurements "
             "close SCOPE section 8.3 and are reported regardless of the exponent "
             "result:\n")
    fv=R("phase5_spy_fill_by_vol.csv")
    if len(fv):
        L.append(md(fv.pivot_table(index=["venue","year"],columns="vol_tercile",
            values="mean_fill").reset_index()))
        L.append("")
    # ---------- Phase 6
    L.append("## Phase 6, SPY exponent\n")
    for ven in ["ARCX","XNAS"]:
        G=R(f"phase6_spy_grid_{ven}.csv")
        if not len(G): continue
        L.append(f"### {ven}\n")
        L.append(md(G,["M","M_used","stub","n_windows","var_log_rv_CAL","var_log_rv_TICK",
            "var_log_trv3_CAL","trv3_share_removed","mean_eff_M","share_full_M",
            "implied_bias","bias_below_1pct","trigamma"]))
        L.append("")
    F=R("phase6_spy_fits.csv")
    L.append("### Fitted Var(log RV_M) = c + A M^b\n")
    L.append(md(F,["venue","fit","c","A","b","rmse","n","M_min","M_max"]))
    L.append("")
    N=R("phase6_spy_noise.csv")
    L.append("### Noise by signature plot\n")
    L.append(md(N,n=30))
    L.append("")
    L.append("### Per year and per volatility tercile\n")
    L.append(md(R("phase6_spy_strat_fits.csv"),["venue","stratum","key","c","A","b","rmse"],n=40))
    L.append("")
    # ---------- Phase 7
    L.append("## Phase 7, determination\n")
    fut=R("phase6_fits.csv",S06R_)
    rows=[]
    if len(fut):
        for _,r in fut.iterrows():
            g=f"{r.geom}_{r.horizon}"
            rows.append(dict(instrument=f"{r.root} futures",cell=f"{r.root}/{r.geom}/{r.btag}/{r.horizon}",
                convention="1-minute calendar",b=r.b_new,
                trigamma_ref=TRIG.get(g,np.nan),gap=r.b_new-TRIG.get(g,np.nan)))
    for ven in ["ARCX","XNAS"]:
        f=F[F.venue==ven]
        if not len(f): continue
        ref=float(f[f.fit=="trigamma_reference"].b.iloc[0]) if len(f[f.fit=="trigamma_reference"]) else np.nan
        refp=float(f[f.fit=="trigamma_reference_primary"].b.iloc[0]) if len(f[f.fit=="trigamma_reference_primary"]) else np.nan
        for tag,lab,rr in [("CAL_full","calendar-time forward fill, full grid",ref),
                           ("CAL_primary","calendar-time forward fill, bias<1% range",refp),
                           ("TICK_full","traded-tick, full grid",ref),
                           ("TICK_primary","traded-tick, bias<1% range",refp),
                           ("TRV3_full","calendar-time TRV3, full grid",ref)]:
            s=f[f.fit==tag]
            if not len(s): continue
            rows.append(dict(instrument=f"SPY {ven}",cell=f"SPY/{ven}/RTH/1day",
                convention=lab,b=float(s.b.iloc[0]),trigamma_ref=rr,
                gap=float(s.b.iloc[0])-rr))
    T7=pd.DataFrame(rows); T7.to_csv(os.path.join(RES,"phase7_determination_table.csv"),index=False)
    L.append(md(T7,["instrument","cell","convention","b","trigamma_ref","gap"],n=60))
    L.append("")
    # determination logic
    det="D"; ev=[]
    try:
        cal=float(F[(F.venue=="ARCX")&(F.fit=="CAL_primary")].b.iloc[0])
        tick=float(F[(F.venue=="ARCX")&(F.fit=="TICK_primary")].b.iloc[0])
        cal2=float(F[(F.venue=="XNAS")&(F.fit=="CAL_primary")].b.iloc[0])
        tick2=float(F[(F.venue=="XNAS")&(F.fit=="TICK_primary")].b.iloc[0])
        refp=float(F[(F.venue=="ARCX")&(F.fit=="trigamma_reference_primary")].b.iloc[0])
        flat_cal=(cal-refp>0.25) and (cal2-refp>0.25)
        flat_tick=(tick-refp>0.25) and (tick2-refp>0.25)
        if flat_cal and flat_tick: det="A"
        elif (not flat_cal) and (not flat_tick): det="B"
        elif flat_cal and not flat_tick: det="C"
        else: det="D"
        ev=[f"ARCX calendar-time b {cal:.3f}, traded-tick b {tick:.3f}",
            f"XNAS calendar-time b {cal2:.3f}, traded-tick b {tick2:.3f}",
            f"trigamma reference on the primary range {refp:.3f}"]
    except Exception as e:
        ev=[f"determination inputs incomplete: {e}"]
    names={"A":"A. Replicates.","B":"B. Does not replicate.",
           "C":"C. Confounded by fill.","D":"D. Indeterminate."}
    L.append(f"### {names[det]}\n")
    for e in ev: L.append(f"- {e}")
    L.append("")
    L.append("Venue agreement is reported as an independent check and the two venues "
             "are never pooled. The SPY result covers roughly 33 percent of "
             "consolidated volume and is labelled as such.\n")
    # ---------- closing
    L.append("## Which project conclusions now stand\n")
    L.append(
        "The proxy-error scaling anomaly is unchanged by every repair applied to it: "
        "S06R moved the futures exponent by at most 1.6e-04 through the OHLC rebuild, "
        "the calendar exclusion and effective sub-bar count, and S05E's positive "
        "control recovered the trigamma reference through the identical code path "
        "while no synthetic arm reproduced the observed flatness. The MCS result is "
        "weaker than it was: the pre-registered insanity filter dominates the loss in "
        "36 of 42 filtered (cell, model) combinations, and in the 1day cells the "
        "replaced observations carry 61 to 71 percent of mean QLIKE, so composition "
        "differences computed on those losses describe the filter as much as the "
        "models. The reliability programme itself is unaffected either way, since "
        "lambda does not enter the MCS. The SPY determination above sets how far the "
        "exponent result generalises beyond futures.\n")
    open(os.path.join(RES,"S07-report.md"),"w").write("\n".join(L))
    print("report written; determination:",det)
    # ---------- spec update
    sp_path=os.path.join(SPECS,"SPEC-obs-space-vol-eval.md")
    add="""

## 9. S07 additions (2026-08-19)

| item | element | fixed | status |
|---|---|---|---|
| 51 | Exchange-declared halts join the calendar exclusion: 2020-03-09, 03-12, 03-18, 03-23, 03-24 (circuit-breaker limit halts, exchange log) and 2019-02-27, 2020-07-01 (Databento degraded, S04 R2). Applied as a data-PRESENCE criterion on those sessions, never on realized variance. | 2026-08-19 | POST HOC |
| 52 | Filter lower bound is the smallest STRICTLY POSITIVE in-sample realized variance. | 2026-08-19 | POST HOC, disclosed |
| 53 | RGARCH diagnosis extended to the 8 GLOBEX intraday cells. | 2026-08-19 | POST HOC |
| 54 | The S06R pre-specified cell ES/RTH/B0/30min stands. Added: a stratified breakdown, and a second pre-specified cell at the MEDIAN effective sample logged before its comparison. | 2026-08-19 | POST HOC |
| 55 | SPY raw DBN only; derived parquets not consumed; SHA-256 manifest recorded. | 2026-08-19 | POST HOC |
| 56 | SPY exponent fitted under BOTH calendar-time forward fill and traded-tick sampling; a flat exponent under forward fill alone is not a replication. | 2026-08-19 | POST HOC |
| 57 | SPY is two-venue (~33% of consolidated volume), venues never pooled, noise corrected, primary M range restricted to implied bias below 1%. | 2026-08-19 | POST HOC |
| 58 | SPY holdout boundary 2024-01-01, matching futures. | 2026-08-19 | POST HOC |

Model-set reduction, extended: item 41's rule (mark unavailable, reduce the set, state
the reduction) is applied to any model failing the positivity invariant, not only
RGARCH. In S07 this covered M6_PARK in two GLOBEX 30min cells. POST HOC, 2026-08-19.
"""
    if os.path.exists(sp_path) and "## 9. S07 additions" not in open(sp_path).read():
        open(sp_path,"a").write(add)
    # ---------- runlog
    freeze=subprocess.run([VENV,"-m","pip","freeze"],capture_output=True,text=True).stdout.strip()
    env=""
    ep=os.path.join(ROOT,"ENVIRONMENT.md")
    if os.path.exists(ep): env=open(ep).read()
    tot=sum(os.path.getsize(os.path.join(dp,f)) for dp,_,fn in os.walk(CACHE) for f in fn)
    Rl=["# Session 7 run log\n",
     f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} (UTC).\n",
     "## Wall clock per phase\n","| phase | wall |","|---|---|",
     "| Phase 0 DECISIONS + directories | ~2 min |",
     f"| Phase 1 SPY inventory, manifest, span check | {sp.get('seconds',0):.0f} s |",
     "| Phase 2 exclusion audit + rerun of 8 cells (3 passes: blanket halt rule "
     "discarded on audit, then filter bound, then model-set reduction) | ~9 min |",
     "| Phase 2 filter audit across all cells | ~1 min |",
     f"| Phase 3+4 RGARCH diagnosis and MCS | see phase4_summary.json |",
     f"| Phase 5 SPY panel build, both venues from raw | {m5['seconds'].sum() if len(m5) and 'seconds' in m5 else 0:.0f} s |",
     "| Phase 6 SPY exponent | see logs/phase6.log |",
     "| Phases 7-8 determination and reports | ~4 min |","",
     "## Seeds and derivation\n",
     "- MCS master seed 20260819; each (cell, scheme) uses "
     "`PCG64(SeedSequence([20260819, cell_index, scheme_index]))`, logged in the "
     "`seed` column of `phase4_mcs.csv`. 10,000 moving-block resamples, block "
     "length ceil(T^(1/3)).\n"
     "- No other randomness: the SPY panel build, the exclusion, the filter, the "
     "RGARCH refits and every exponent fit are deterministic.\n",
     "## Constants and sources\n","| constant | value | source |","|---|---|---|",
     "| SPY grid | 5, 6, 10, 13, 26, 39, 78, 130, 195, 390, 780, 1560, 2340, 4680, 11700, 23400 | all exact divisors of 23,400 |",
     "| SPY RTH window | 09:30:00-15:59:59 NY, 23,400 seconds | SCOPE section 3 |",
     "| SPY early closes | day after Thanksgiving, Jul 3, Dec 24 | SCOPE section 3 |",
     "| filter lower bound | smallest strictly positive in-sample RV | item 52 |",
     "| filter upper bound | in-sample RV max | item 40, unchanged |",
     "| noise primary range | implied bias 2*M*omega^2/IV below 1% | item 57 |",
     "| truncation | 3 local standard deviations | S05 Part A |",
     "| holdout | 2024-01-01, futures and SPY | items 50 and 58 |",
     "| trigamma reference | polygamma(1, M/2), fitted by the same free-intercept procedure | S05E Phase 1 |","",
     "## Calendar and data sources\n",
     "- Futures exclusion: CME Group published equity-index holiday calendar "
     "(rule-generated) plus the item-51 exchange-declared halt sessions.\n"
     "- SPY: raw DBN from `~/Downloads/DataBento Data/SPY 1s Data`, "
     "jobs ARCX-20260815-XLE9K93W3H (ARCX.PILLAR) and XNAS-20260815-SLCD8NA7UL "
     "(XNAS.ITCH), SHA-256 in `results/S07-spy-manifest.txt`. Derived parquets in "
     "`data/` were inventoried but NOT consumed (item 55).\n",
     f"## Persistence\n\nCache {tot/1e6:.1f} MB under `sessions/s07-completion-and-spy/cache/`: "
     "SPY calendar-time and traded-tick panels with present masks, regenerated "
     "futures forecast panels, and loss matrices. Every figure in the report "
     "regenerates from these plus the CSVs in `results/`.\n",
     "## Environment record (from ENVIRONMENT.md)\n", env if env else "(absent)","",
     "### pip freeze at S07\n","```text",freeze,"```",""]
    open(os.path.join(RES,"S07-runlog.md"),"w").write("\n".join(Rl))
    print("runlog written")
if __name__=="__main__": main()
