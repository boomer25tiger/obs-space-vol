"""S12 Phase 1: convexity on the EXACT lognormal relation (item 95).

Derivation, one assumption. Let integrated variance V be lognormal with
log V ~ N(mu, s2). Then
    E[V]      = exp(mu + s2/2)      so sqrt(E[V]) = exp(mu/2 + s2/4)
    E[sqrt V] = exp(mu/2 + s2/8)                          (MGF at t = 1/2)
A volatility swap pays realized volatility, so its fair strike is
    K_vol = E[sqrt V] = sqrt(E[V]) * exp(-s2/8).
No expansion is used. The single assumption is lognormality of V, which is the
same distributional assumption the intercept route already makes when it reads
c as Var(log IV).

The Brockhaus-Long (2000) second-order figure, K_vol ~ sqrt(E[V]) *
(1 - (exp(s2)-1)/8), is reported beside it as a sensitivity, together with the
value of Var(V)/E[V]^2 at which it departs from exact by 10 percent.
"""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy.optimize import brentq
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES=os.path.join(BASE,"results")
S11=os.path.join(ROOT,"sessions","s11-extensions")
K_VOL_ANN=0.20                     # sqrt(E[V]); a 20 percent variance-swap strike
THRESH=0.05                        # item 94, unchanged
def adj_exact(s2):  return 1.0-np.exp(-s2/8.0)          # as a fraction of sqrt(E[V])
def adj_bl(s2):     return (np.exp(s2)-1.0)/8.0
def main():
    t0=time.time()
    V=pd.read_csv(os.path.join(S11,"results","phase5_five_minute.csv"))
    rows=[]
    for _,r in V.iterrows():
        e_c,e_n=adj_exact(r.c),adj_exact(r.var_log_rv_naive)
        e_lo,e_hi=adj_exact(r.c_lo),adj_exact(r.c_hi)
        b_c,b_n=adj_bl(r.c),adj_bl(r.var_log_rv_naive)
        rows.append(dict(root=r.root,geom=r.geom,btag=r.btag,horizon=r.horizon,M=r.M,
            s2_intercept=r.c,s2_intercept_lo=r.c_lo,s2_intercept_hi=r.c_hi,
            s2_naive=r.var_log_rv_naive,
            kappa_intercept=float(np.exp(r.c)-1.0),
            kappa_naive=float(np.exp(r.var_log_rv_naive)-1.0),
            adj_exact_intercept_vp=100*K_VOL_ANN*e_c,
            adj_exact_intercept_vp_lo=100*K_VOL_ANN*e_lo,
            adj_exact_intercept_vp_hi=100*K_VOL_ANN*e_hi,
            adj_exact_naive_vp=100*K_VOL_ANN*e_n,
            diff_vp=100*K_VOL_ANN*(e_n-e_c),
            overstatement_prop=float(e_n/e_c-1.0),
            overstatement_lo=float(e_n/adj_exact(r.c_hi)-1.0),
            overstatement_hi=float(e_n/adj_exact(r.c_lo)-1.0),
            adj_BL_intercept_vp=100*K_VOL_ANN*b_c,
            adj_BL_naive_vp=100*K_VOL_ANN*b_n,
            ratio_exact_over_BL_intercept=float(e_c/b_c),
            ratio_exact_over_BL_naive=float(e_n/b_n),
            overstatement_BL=float(b_n/b_c-1.0),
            k_vol_factor_exact=float(np.exp(-r.c/8.0)),
            k_vol_factor_BL=float(1.0-b_c)))
    P=pd.DataFrame(rows); P.to_csv(os.path.join(RES,"phase1_convexity_exact.csv"),index=False)
    # validity boundary: kappa at which BL departs from exact by 10 percent
    f=lambda s2: adj_bl(s2)/adj_exact(s2)-1.10
    s2_10=float(brentq(f,1e-6,3.0)); kappa_10=float(np.exp(s2_10)-1.0)
    grid=[]
    for s2 in [0.05,0.1,0.2,0.3,0.4,0.5,0.75,1.0,1.5,2.0,2.5]:
        grid.append(dict(s2=s2,kappa=float(np.exp(s2)-1.0),
            adj_exact=adj_exact(s2),adj_BL=adj_bl(s2),
            BL_over_exact=float(adj_bl(s2)/adj_exact(s2)),
            k_vol_factor_exact=float(np.exp(-s2/8)),
            k_vol_factor_BL=float(1.0-adj_bl(s2))))
    G=pd.DataFrame(grid); G.to_csv(os.path.join(RES,"phase1_validity_boundary.csv"),index=False)
    k6=dict(relation_exact=("K_vol = E[sqrt V] = sqrt(E[V]) * exp(-s2/8), exact under "
            "lognormal V; no expansion, single assumption is lognormality of V."),
        relation_expansion=("Brockhaus and Long (2000) second order: "
            "K_vol ~ sqrt(E[V]) * (1 - (exp(s2)-1)/8)."),
        validity_boundary_s2_at_10pct=s2_10,
        validity_boundary_kappa_at_10pct=kappa_10,
        measured_kappa_range=[float(P.kappa_intercept.min()),float(P.kappa_naive.max())],
        expansion_valid_at_measured_kappa=bool(P.kappa_intercept.max()<kappa_10),
        max_overstatement_prop=float(P.overstatement_prop.max()),
        min_overstatement_prop=float(P.overstatement_prop.min()),
        max_diff_vp=float(P.diff_vp.max()),
        all_below_5pct=bool((P.overstatement_prop.abs()<THRESH).all()),
        n_cells_above_threshold=int((P.overstatement_prop.abs()>=THRESH).sum()),
        n_cells=int(len(P)),
        max_ratio_exact_over_BL=float(P[["ratio_exact_over_BL_intercept",
                                         "ratio_exact_over_BL_naive"]].max().max()),
        min_ratio_exact_over_BL=float(P[["ratio_exact_over_BL_intercept",
                                         "ratio_exact_over_BL_naive"]].min().min()),
        s11_void_figures=dict(overstatement_443pct=False,diff_13p96_vol_points=False,
            note="item 95: both are void and are replaced by the exact figures here"),
        direction=("Naive s2 exceeds the intercept-route s2 in every cell, so the naive "
            "convexity adjustment is too large and the implied volatility-swap strike "
            "too low. That favours the side long volatility at the quoted strike."),
        no_pnl_claim=("No options data is held. This is a pricing-bias calculation on "
            "the adjustment term only; no claim is made about executable P&L."),
        threshold=THRESH)
    k6["K6"]=("FIRES" if k6["all_below_5pct"] else "DOES NOT FIRE")
    json.dump(k6,open(os.path.join(RES,"phase1_k6.json"),"w"),indent=1)
    pd.set_option("display.width",250)
    print("=== exact vs expansion, validity ===")
    print(G.to_string(index=False))
    print(f"\nBL departs from exact by 10 percent at s2 = {s2_10:.4f}, "
          f"kappa = Var(V)/E[V]^2 = {kappa_10:.4f}")
    print(f"measured kappa runs {P.kappa_intercept.min():.2f} to {P.kappa_naive.max():.2f}")
    print("\n=== per cell, exact relation ===")
    print(P[["root","geom","btag","horizon","M","s2_intercept","s2_naive",
             "adj_exact_intercept_vp","adj_exact_intercept_vp_lo",
             "adj_exact_intercept_vp_hi","adj_exact_naive_vp","diff_vp",
             "overstatement_prop","adj_BL_intercept_vp",
             "ratio_exact_over_BL_intercept"]].to_string(index=False))
    print(); print(json.dumps(k6,indent=1))
    json.dump(dict(phase1=round(time.time()-t0,1)),
              open(os.path.join(RES,"phase1_timer.json"),"w"),indent=1)
    print(f"PHASE1 DONE {time.time()-t0:.1f}s")
if __name__=="__main__": main()
