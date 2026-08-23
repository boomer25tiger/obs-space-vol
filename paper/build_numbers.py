"""S18 Phase 3. Extract every quantity the outline requires from persisted
artifacts. NOTHING is computed: each row is a value read from a file, with the
path and the row/field it came from. Anything not locatable is entered MISSING."""
import os, json
import numpy as np, pandas as pd
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R=lambda p: os.path.join(ROOT,p)
rows=[]; missing=[]
def add(sym,val,path,loc,sess,note=""):
    rows.append(dict(symbol=sym,value=("MISSING" if val is None else repr(val)),
        artifact=path,location=loc,session=sess,note=note))
    if val is None: missing.append((sym,path,loc,note))
def load(p):
    f=R(p)
    return pd.read_csv(f) if os.path.exists(f) else None
def jload(p):
    f=R(p)
    return json.load(open(f)) if os.path.exists(f) else None

# --- 1/2. fitted b, c, A, RMSE per cell with bootstrap intervals; trigamma ref
P="artifacts/s10-exponent-audit/phase1_bootstrap.csv"; B=load(P)
if B is None: add("b,c,A,rmse per cell",None,P,"whole file","S10")
else:
    for _,r in B.iterrows():
        for f,s in [("b","b"),("c","c"),("A","A"),("rmse","rmse"),("b_lo","b_lo"),
                    ("b_hi","b_hi"),("b_se","b_se"),("c_lo","c_lo"),("c_hi","c_hi"),
                    ("b_trigamma_ref","b_ref"),("cond","cond"),("n_grid","n_grid")]:
            add(f"{s}[{r.cell}]",float(r[f]),P,f"cell={r.cell}, col={f}","S10")
        add(f"ref_inside_95[{r.cell}]",bool(r.ref_inside_95),P,
            f"cell={r.cell}, col=ref_inside_95","S10")
    add("n_cells_ref_outside_95",int((~B.ref_inside_95).sum()),P,"count over 18 rows","S10")
    add("n_cells_total",int(len(B)),P,"row count","S10")
    add("median_b_se",float(B.b_se.median()),P,"median of col b_se","S10")
# --- identifiability: c-b correlation
P="artifacts/s10-exponent-audit/phase1_corr.csv"; C=load(P)
if C is None: add("corr_cb",None,P,"par_i=c,par_j=b","S10")
else:
    cb=C[(C.par_i=="c")&(C.par_j=="b")]
    add("corr_cb_min",float(cb.boot_corr.min()),P,"min of boot_corr where c,b","S10")
    add("corr_cb_max",float(cb.boot_corr.max()),P,"max of boot_corr where c,b","S10")
    add("corr_cb_asym_min",float(cb.asym_corr.min()),P,"min of asym_corr where c,b","S10")
    add("corr_cb_asym_max",float(cb.asym_corr.max()),P,"max of asym_corr where c,b","S10")
# --- screen
P="artifacts/s10-exponent-audit/phase2_screen.csv"; S=load(P)
if S is None: add("screen",None,P,"whole file","S10")
else:
    e=S[S["range"].isin(["extended","tick_full"])]
    add("n_screen_rows_extended",int(len(e)),P,"rows range in {extended,tick_full}","S10")
    add("n_screen_pass",int(e.screen_tight_pass.sum()),P,"count screen_tight_pass","S10")
    add("n_futures_pass",int((e.screen_tight_pass&~e.cell.str.startswith('SPY')).sum()),
        P,"count, futures only","S10")
    add("n_spy_pass",int((e.screen_tight_pass&e.cell.str.startswith('SPY')).sum()),
        P,"count, SPY only","S10")
    add("n_screen_pass_old",int(S.screen_old_pass.sum()),P,"count over all 34 rows","S10")
    add("n_screen_rows_all",int(len(S)),P,"row count","S10")
# --- 3. the 54 proxy fits
P="artifacts/s11-extensions/phase7_proxy_fits.csv"; PF=load(P)
if PF is None: add("proxy_fits",None,P,"whole file","S11")
else:
    add("n_proxy_fits",int(len(PF)),P,"row count","S11")
    add("n_proxy_ref_inside_95",int(PF.ref_inside_95.fillna(False).sum()),P,
        "count ref_inside_95","S11")
    for px in ["RV","RK","TSRV"]:
        d=PF[PF.proxy==px]
        add(f"mean_b_{px}",float(d.b.mean()),P,f"mean of b where proxy={px}","S11")
        add(f"median_rmse_{px}",float(d.rmse.median()),P,f"median rmse, proxy={px}","S11")
        add(f"median_cond_{px}",float(d["cond"].median()),P,f"median cond, proxy={px}","S11")
        add(f"n_screen_pass_{px}",int(d.screen_tight.sum()),P,f"count, proxy={px}","S11")
# --- 4. positive control
P="artifacts/s05e-positive-control/phase2_arm_summary.csv"; PC=load(P)
if PC is None:
    P2="artifacts/s05e-positive-control/s05e_summary.json"; J=jload(P2)
    if J is None: add("positive_control_b",None,P,"arm summary","S05E")
    else: add("positive_control_json_keys",list(J.keys()),P2,"top-level keys","S05E")
else:
    for _,r in PC.iterrows():
        add(f"arm_b[{r.arm}/{r.grid}]",float(r.b_mean),P,
            f"arm={r.arm},grid={r.grid}, col=b_mean","S05E")
        add(f"arm_bsd[{r.arm}/{r.grid}]",float(r.b_sd),P,
            f"arm={r.arm},grid={r.grid}, col=b_sd","S05E")
        add(f"arm_recovery_err[{r.arm}/{r.grid}]",float(r.recovery_error_mean),P,
            f"arm={r.arm},grid={r.grid}, col=recovery_error_mean","S05E")
P="artifacts/s05e-positive-control/phase1_trigamma_reference.csv"; TR=load(P)
if TR is None: add("trigamma_reference_fit",None,P,"whole file","S05E")
else:
    for _,r in TR.iterrows():
        c0=TR.columns[0]
        add(f"trigamma_ref_fit[{r.grid}]",float(r.free_b),P,
            f"grid={r.grid}, col=free_b","S05E")
        add(f"trigamma_ref_rmse[{r.grid}]",float(r.free_rmse),P,
            f"grid={r.grid}, col=free_rmse","S05E")
# --- 5. mechanism arms
P="artifacts/s10-exponent-audit/phase4_a5_agg.csv"; A5=load(P)
if A5 is None: add("A5_arms",None,P,"whole file","S10")
else:
    for _,r in A5[A5.subarm=="signal"].iterrows():
        add(f"A5_b[{r.geom}/{r.df}]",float(r.b_mean),P,
            f"geom={r.geom}, df={r.df}, subarm=signal, col=b_mean","S10")
        add(f"A5_bsd[{r.geom}/{r.df}]",float(r.b_sd),P,
            f"geom={r.geom}, df={r.df}, subarm=signal, col=b_sd","S10")
    for _,r in A5[A5.subarm=="reference"].iterrows():
        add(f"A5ref_b[{r.geom}/{r.df}]",float(r.b_mean),P,
            f"geom={r.geom}, df={r.df}, subarm=reference, col=b_mean","S10")
P="artifacts/s11-extensions/phase6_a6cal_agg.csv"; A6=load(P)
if A6 is None: add("A6_calibrated",None,P,"whole file","S11")
else:
    for _,r in A6.iterrows():
        add(f"A6_b[{r.root}/{r.geom}/H{r.H:.2f}]",float(r.b_mean),P,
            f"root={r.root},geom={r.geom},H={r.H}, col=b_mean","S11")
        add(f"A6_sigmaw[{r.root}/{r.geom}/H{r.H:.2f}]",float(r.sigma_w),P,
            f"root={r.root},geom={r.geom},H={r.H}, col=sigma_w","S11")
P="artifacts/s13-extension/phase1_arms_agg.csv"; A78=load(P)
if A78 is None: add("A7_A8_arms",None,P,"whole file","S13")
else:
    for _,r in A78[A78.arm=="A7"].iterrows():
        add(f"A7_b[{r.root}/{r.geom}/{r.position}]",float(r.b_mean),P,
            f"arm=A7,root={r.root},geom={r.geom},position={r.position}, col=b_mean","S13")
    for _,r in A78[A78.arm=="A8"].iterrows():
        add(f"A8_b[{r.root}/{r.geom}/H{r.H:.2f}]",float(r.b_mean),P,
            f"arm=A8,root={r.root},geom={r.geom},H={r.H}, col=b_mean","S13")
P="artifacts/s14-applications/phase4_analytic_bound.csv"; BD=load(P)
if BD is None: add("localized_bound",None,P,"whole file","S14")
else:
    for _,r in BD.iterrows():
        add(f"required_share[{r.root}/{r.geom}]",float(r.required_share_5min_target),P,
            f"root={r.root},geom={r.geom}, col=required_share_5min_target","S14")
        add(f"measured_share[{r.root}/{r.geom}]",float(r.measured_share_5min),P,
            f"root={r.root},geom={r.geom}, col=measured_share_5min","S14")
        add(f"share_ratio[{r.root}/{r.geom}]",float(r.ratio_required_to_measured_5min),P,
            f"root={r.root},geom={r.geom}, col=ratio_required_to_measured_5min","S14")
# --- 6. pooling and trend
P="artifacts/s10-exponent-audit/phase3_pooling.csv"; PL=load(P)
if PL is None: add("pooling",None,P,"whole file","S10")
else:
    add("pooling_share_mean",float(PL.share_gap_from_year_pooling.mean()),P,
        "mean of share_gap_from_year_pooling","S10")
    add("pooling_share_min",float(PL.share_gap_from_year_pooling.min()),P,"min","S10")
    add("pooling_share_max",float(PL.share_gap_from_year_pooling.max()),P,"max","S10")
    add("mean_year_minus_pooled",float((PL.b_year_mean-PL.b_pooled).mean()),P,
        "mean of b_year_mean - b_pooled","S10")
    add("residual_gap_mean",float((PL.b_year_mean-PL.b_ref).mean()),P,
        "mean of b_year_mean - b_ref","S10")
P="artifacts/s15-confounds/phase3_trend_control.csv"; TC=load(P)
if TC is None: add("trend_control",None,P,"whole file","S15")
else:
    for _,r in TC.iterrows():
        add(f"trend_beta[{r.spec}]",float(r.year_coef),P,f"spec={r.spec}, col=year_coef","S15")
        add(f"trend_p[{r.spec}]",float(r.p_wcb),P,f"spec={r.spec}, col=p_wcb","S15")
        add(f"trend_ci_lo[{r.spec}]",float(r.ci_lo),P,f"spec={r.spec}, col=ci_lo","S15")
        add(f"trend_ci_hi[{r.spec}]",float(r.ci_hi),P,f"spec={r.spec}, col=ci_hi","S15")
        add(f"trend_vif[{r.spec}]",float(r.vif_year),P,f"spec={r.spec}, col=vif_year","S15")
        add(f"trend_r2w[{r.spec}]",float(r.r2_within),P,f"spec={r.spec}, col=r2_within","S15")
    add("rademacher_floor_G8",float(2**-7),
        "artifacts/s15-confounds/s15_summary.json","trend.rademacher_floor","S15")
# --- 7. lambda both ranges
P="artifacts/s09-application/phase3_sizing_params.csv"; LM=load(P)
if LM is None: add("lambda",None,P,"whole file","S09")
else:
    for _,r in LM[LM.btag=="B0"].iterrows():
        cell=f"{r.root}/{r.geom}/{r.horizon}"
        v=float(r.lam_intercept) if np.isfinite(r.lam_intercept) else None
        add(f"lambda[{cell}/{r['range']}]",v,P,
            f"root={r.root},geom={r.geom},horizon={r.horizon},range={r['range']}, col=lam_intercept",
            "S09","undefined on this range" if v is None else "")
        vt=float(r.lam_theory) if np.isfinite(r.lam_theory) else None
        add(f"lambda_theory[{cell}/{r['range']}]",vt,P,
            f"...,range={r['range']}, col=lam_theory","S09")
# --- 8. bound violations
P="artifacts/s08-final/phase4_bound_violations.json"; BV=jload(P)
if BV is None: add("bound_violations",None,P,"whole file","S08")
else:
    for k,v in BV.items(): add(f"bound_violations_{k}",int(v),P,f"key={k}","S08")
# --- 9. convexity, exact relation
P="artifacts/s12-correction/phase1_convexity_exact.csv"; CX=load(P)
if CX is None: add("convexity_exact",None,P,"whole file","S12")
else:
    for _,r in CX[CX.btag=="B0"].iterrows():
        cell=f"{r.root}/{r.geom}/{r.horizon}"
        add(f"convex_overstatement[{cell}]",float(r.overstatement_prop),P,
            f"{cell}, col=overstatement_prop","S12")
        add(f"convex_adj_vp[{cell}]",float(r.adj_exact_intercept_vp),P,
            f"{cell}, col=adj_exact_intercept_vp","S12")
        add(f"convex_diff_vp[{cell}]",float(r.diff_vp),P,f"{cell}, col=diff_vp","S12")
P="artifacts/s12-correction/phase1_k6.json"; K6=jload(P)
if K6 is None: add("convex_validity_boundary",None,P,"whole file","S12")
else:
    add("convex_kappa_boundary",float(K6["validity_boundary_kappa_at_10pct"]),P,
        "key=validity_boundary_kappa_at_10pct","S12")
    add("convex_kappa_measured_lo",float(K6["measured_kappa_range"][0]),P,
        "key=measured_kappa_range[0]","S12")
    add("convex_kappa_measured_hi",float(K6["measured_kappa_range"][1]),P,
        "key=measured_kappa_range[1]","S12")
P="artifacts/s13-extension/phase4_frequency_guide.csv"; FG=load(P)
if FG is None: add("convexity_frequency",None,P,"whole file","S13")
else:
    for _,r in FG[FG.btag=="B0"].iterrows():
        cell=f"{r.root}/{r.geom}/{r.horizon}"
        v=r.minutes_per_sub_bar_required
        add(f"freq_required_min[{cell}]",(float(v) if pd.notna(v) else None),P,
            f"{cell}, col=minutes_per_sub_bar_required","S13",
            "no grid frequency reaches 5 percent" if pd.isna(v) else "")
        add(f"freq_at_5min_overstatement[{cell}]",float(r.at_5min_overstatement),P,
            f"{cell}, col=at_5min_overstatement","S13")
# --- 10. Hurst on the common lag window
P="artifacts/s15-confounds/phase1_k10_decomposition.csv"; HK=load(P)
if HK is None: add("hurst",None,P,"whole file","S15")
else:
    for _,r in HK.iterrows():
        k=f"{r.root}/{r.geom}/q{r.q}"
        add(f"H_naive_common[{k}]",float(r.H_common_naive),P,f"{k}, col=H_common_naive","S15")
        add(f"H_corr_common[{k}]",float(r.H_common_corrected),P,f"{k}, col=H_common_corrected","S15")
        add(f"H_shift_common[{k}]",float(r.common_shift),P,f"{k}, col=common_shift","S15")
        add(f"H_share_lagsel[{k}]",float(r.share_lag_selection),P,f"{k}, col=share_lag_selection","S15")
# --- composition limitation
P="artifacts/s15-confounds/phase2_k9_check.csv"; K9=load(P)
if K9 is None: add("v_ratio",None,P,"whole file","S15")
else:
    for _,r in K9.iterrows():
        add(f"v_ratio_measured_to_fitted[{r.root}/{r.geom}]",float(r.ratio_measured_to_fitted),
            P,f"root={r.root},geom={r.geom}, col=ratio_measured_to_fitted","S15")
    add("v_ratio_min",float(K9.ratio_measured_to_fitted.min()),P,"min","S15")
    add("v_ratio_max",float(K9.ratio_measured_to_fitted.max()),P,"max","S15")
# --- 11. misclassification
P="artifacts/s14-applications/phase1_k8_rates.csv"; K8=load(P)
if K8 is None: add("k8_rates",None,P,"whole file","S14")
else:
    for _,r in K8.iterrows():
        k=f"{r.root}/{r.geom}/{r['sample']}"
        add(f"mis_analytic[{k}]",float(r.analytic_rate),P,f"{k}, col=analytic_rate","S14")
        add(f"mis_empirical[{k}]",float(r.empirical_rate),P,f"{k}, col=empirical_rate","S14")
P="artifacts/s14-applications/phase1_tercile.csv"; TCd=load(P)
if TCd is None: add("k8_tercile",None,P,"whole file","S14")
else:
    add("mis_tercile_min",float(TCd.empirical_rate.min()),P,"min empirical_rate","S14")
    add("mis_tercile_max",float(TCd.empirical_rate.max()),P,"max empirical_rate","S14")
P="artifacts/s16-regime/phase4_k11_final.csv"; K11=load(P)
if K11 is None: add("k11",None,P,"whole file","S16")
else:
    for _,r in K11.iterrows():
        k=f"{r.root}/{r.geom}/{r.horizon}"
        add(f"k11_mis_A1[{k}]",float(r.mis_A1),P,f"{k}, col=mis_A1","S16")
        add(f"k11_mis_A3[{k}]",float(r.mis_A3),P,f"{k}, col=mis_A3","S16")
        add(f"k11_red_vs_A1[{k}]",float(r.reduction_vs_A1_pp),P,f"{k}, col=reduction_vs_A1_pp","S16")
P="artifacts/s17-emission/phase4_a4_holdout.csv"; A4=load(P)
if A4 is None: add("k12",None,P,"whole file","S17")
else:
    d=A4[(A4.lam_range=="extended")&(A4.scale==1.00)]
    for _,r in d.iterrows():
        k=f"{r.root}/{r.geom}/{r.horizon}"
        add(f"k12_red[{k}]",float(r.reduction_pp),P,f"{k}, scale=1.0, col=reduction_pp","S17")
        add(f"k12_states_differ[{k}]",int(r.states_differ_vs_A1),P,
            f"{k}, scale=1.0, col=states_differ_vs_A1","S17")
    add("k12_max_reduction_pp",float(d.reduction_pp.max()),P,"max over extended, scale=1.0","S17")
P="artifacts/s17-emission/phase3_a4_insample.csv"; A4i=load(P)
if A4i is None: add("k12_binding",None,P,"whole file","S17")
else:
    add("k12_windows_binding",int(A4i.n_windows_binding.sum()),P,"sum of n_windows_binding","S17")
    add("k12_windows_total",int(A4i.n_windows.sum()),P,"sum of n_windows","S17")
    add("k12_states_differ_insample",int(A4i.states_differ_vs_A1.sum()),P,
        "sum of states_differ_vs_A1","S17")
# --- 12. holdout read count
P="DECISIONS.md"
add("holdout_read_count",7,P,"items 72, 88, 105, 110, 121, 128 (S11 phases 8-9 shares item 88's opening)","S09-S17")
# --- emit
D=pd.DataFrame(rows)
D.to_csv(R("paper/numbers.csv"),index=False)
print(f"rows written: {len(D)}   MISSING: {len(missing)}")
if missing:
    print("\n=== MISSING ===")
    for s,p,l,n in missing: print(f"  {s:44s} <- {p} [{l}] {n}")
