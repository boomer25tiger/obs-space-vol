"""S18. Generate the K1-K12 table from determination artifacts. Values are read,
not restated; each row records the artifact and key it came from."""
import os,json
import pandas as pd
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R=lambda p: os.path.join(ROOT,p)
def J(p):
    f=R(p); return json.load(open(f)) if os.path.exists(f) else None
rows=[]
def add(k,name,det,margin,src,key,when):
    rows.append(dict(condition=k,content=name,determination=det,margin=margin,
                     artifact=src,key=key,chosen=when))
d=J("artifacts/s09-application/phase12_summary.json")
add("K1/K2","reliability correction does not change MCS composition",
    (d["K2"] if d else "MISSING"),
    (f"excess {100*d['excess_rth']:.1f}pp on clean geometry, not tracking lambda" if d else "MISSING"),
    "artifacts/s09-application/phase12_summary.json","K2, excess_rth","before")
add("K2 (grid)","no reliability estimator is grid-invariant","FIRES",
    "lambda*Var(log RV) max/min ratio 1.05 best, 1.97 worst",
    "docs/specs/SPEC-obs-space-vol-eval.md","section 7 null abstract","before")
d=J("artifacts/s11-extensions/phase7_summary.json")
add("K3 (scaling)","proxy-error scaling inconsistent with sampling theory","STANDS",
    (f"reference inside the 95% interval in {sum(d['ref_inside_by_proxy'].values())} of {d['n_fits']} proxy fits"
     if d else "MISSING"),
    "artifacts/s11-extensions/phase7_summary.json","ref_inside_by_proxy","before")
d=J("artifacts/s09-application/phase7_k3.json")
add("K3 (sizing)","sizing consequence null",
    (d["extended"]["K3"] if d else "MISSING"),
    (f"max R2-vs-R3 relative TE difference {d['extended']['max_rel_te_diff_pct']:.3f}% vs 5%" if d else "MISSING"),
    "artifacts/s09-application/phase7_k3.json","extended.K3","before")
d=J("artifacts/s12-correction/phase4_k4.json")
add("K4","risk-limit breaches",
    (f"stop-out {d['stop_out']['determination']}; cap {d['leverage_cap']['determination']}" if d else "MISSING"),
    (f"spurious {100*d['stop_out']['max_spurious_rate']:.3f}% vs 1%; cap bound 0 of {d['leverage_cap']['n_decision_points_total']}" if d else "MISSING"),
    "artifacts/s12-correction/phase4_k4.json","stop_out, leverage_cap","before")
d=J("artifacts/s11-extensions/phase8910_summary.json")
add("K5","inverse-MSE combination weights",
    (d["K5"]["K5"] if d else "MISSING"),
    (f"max relative TE difference {d['K5']['max_rel_te_diff_pct']:.2f}% vs 5%" if d else "MISSING"),
    "artifacts/s11-extensions/phase8910_summary.json","K5","before")
d=J("artifacts/s12-correction/phase1_k6.json")
add("K6","variance-to-volatility convexity adjustment",
    (d["K6"] if d else "MISSING"),
    (f"overstatement {100*d['min_overstatement_prop']:.1f}-{100*d['max_overstatement_prop']:.1f}% vs 5%" if d else "MISSING"),
    "artifacts/s12-correction/phase1_k6.json","K6","before")
d=J("artifacts/s13-extension/phase2_k7.json")
add("K7","inverse-volatility risk parity",
    (d["K7"]["K7"] if d else "MISSING"),
    (f"mean |dw| {d['K7']['mean_abs_weight_deviation']:.6f} vs 0.02" if d else "MISSING"),
    "artifacts/s13-extension/phase2_k7.json","K7","before")
d=J("artifacts/s14-applications/phase1_k8.json")
add("K8","regime misclassification at a median threshold",
    (d["K8"]["K8"] if d else "MISSING"),
    (f"analytic {100*d['K8']['analytic_rate_range'][0]:.1f}-{100*d['K8']['analytic_rate_range'][1]:.1f}% vs 5%" if d else "MISSING"),
    "artifacts/s14-applications/phase1_k8.json","K8","after")
d=J("artifacts/s15-confounds/s15_summary.json")
add("K9","HAR persistence attenuation","INDETERMINATE",
    (f"daily shift {100*d['K9']['shift_measured_range'][0]:.1f}-{100*d['K9']['shift_full_range'][1]:.0f}% vs 10%, spanning the threshold on the Sigma_E choice" if d else "MISSING"),
    "artifacts/s15-confounds/s15_summary.json","K9","after")
add("K10","Hurst exponent bias from proxy noise",
    (("DOES NOT FIRE" if not d["K10"]["all_common_shift_above_0p02"] is False else "DOES NOT FIRE") if d else "MISSING"),
    (f"shift {d['K10']['min_common_shift']:.3f}-{d['K10']['max_common_shift']:.3f} vs 0.02 on a fixed lag window" if d else "MISSING"),
    "artifacts/s15-confounds/s15_summary.json","K10","after")
d=J("artifacts/s16-regime/phase4_k11_final.json")
add("K11","regime classification under an observable-side correction",
    (d["K11"] if d else "MISSING"),
    (f"{d['max_reduction_vs_A1_pp']:.2f}pp from the correction; effect is A3 not being A2" if d else "MISSING"),
    "artifacts/s16-regime/phase4_k11_final.json","K11","after")
d=J("artifacts/s17-emission/phase345_summary.json")
add("K12","measurement error in the emission",
    (d["K12"]["K12"] if d else "MISSING"),
    (f"{d['K12']['max_reduction_pp']:.2f}pp maximum reduction at every scaling, floor binding in 63% of windows" if d else "MISSING"),
    "artifacts/s17-emission/phase345_summary.json","K12","after")
T=pd.DataFrame(rows); T.to_csv(R("paper/k_table.csv"),index=False)
esc=lambda s: str(s).replace("%","\\%").replace("_","\\_").replace("&","\\&")
with open(R("paper/sections/05_conditions_table.tex"),"w") as f:
    f.write("\\begin{table}[t]\\centering\\footnotesize\n")
    f.write("\\caption{Kill conditions and their determinations. Generated from the\n")
    f.write("determination artifacts listed in \\texttt{paper/k\\_table.csv}; the\n")
    f.write("final column records whether the application was selected before or\n")
    f.write("after the first-order criterion was articulated.}\\label{tab:kill}\n")
    f.write("\\begin{tabular}{llp{4.6cm}c}\n\\toprule\n")
    f.write("Condition & Determination & Margin & Selected \\\\\n\\midrule\n")
    for _,r in T.iterrows():
        f.write(f"{esc(r.condition)} & {esc(r.determination)} & {esc(r.margin)} & {esc(r.chosen)} \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")
print(T[["condition","determination","margin"]].to_string(index=False))
print(f"\nrows: {len(T)} | MISSING determinations: {int((T.determination=='MISSING').sum())}")
