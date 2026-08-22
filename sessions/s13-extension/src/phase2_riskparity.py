"""S13 Phase 2: K7, inverse-volatility risk parity (items 102, 103, 105).

Derivation. Let the proxy volatility estimate satisfy log sigma_hat = log sigma
+ e with e ~ N(0, v), which follows from log RV = log IV + eta with eta ~ N(0, w)
and sigma_hat = sqrt(RV), giving v = w/4. Then

    EXACT (lognormal):     E[1/sigma_hat] = (1/sigma) * exp(v/2)
    SECOND ORDER:          E[1/sigma_hat] ~ (1/sigma) * (1 + v/2)

The exact relation is used throughout, per item 95 and the S12 precedent; the
expansion is reported only as a labelled sensitivity with its validity boundary.
The single assumption is lognormality of the estimation error, the same
assumption the intercept route makes in reading c as Var(log IV).

An asset measured with more proxy noise carries a larger v, so 1/sigma_hat is
inflated more and the asset is systematically OVERWEIGHTED by an inverse-
volatility rule.

HOLDOUT: this phase performs the programme's FOURTH holdout read (item 105),
after S09 Phase 6, S11 Phase 1 and S11 Phases 8-9. No parameter, threshold, rule
or specification is changed.
"""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy.optimize import brentq
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common13 import BASE,RES,CACHE,S09,S11,TICKS,TICKVAL,MULT,FIVEMIN
from common import subbars
from phase8910_apps import ho_series                     # S11, equivalence-asserted
LOOKBACK=21          # trailing sessions for a monthly-rebalanced estimate
REBAL=21             # monthly rebalance, in sessions
THRESH_W=0.02; THRESH_TE=0.05                            # item 103, fixed
def bias_exact(v):  return float(np.exp(v/2.0))
def bias_2nd(v):    return float(1.0+v/2.0)
def main():
    t0=time.time(); timers={}; out={}
    # ---- validity boundary of the expansion
    f=lambda v: (bias_exact(v)-1.0)/max(bias_2nd(v)-1.0,1e-300)-1.10
    v10=float(brentq(f,1e-8,3.0))
    out["expansion_boundary_var_log_sigma_hat_at_10pct"]=v10
    P7=pd.read_csv(os.path.join(S11,"results","phase7_proxy_fits.csv"))
    P3=pd.read_csv(os.path.join(S09,"results","phase3_sizing_params.csv"))
    # ---- noise variance of log sigma_hat per asset, RTH daily
    NOISE={}
    for root in ["ES","NQ"]:
        r=P7[(P7.cell==f"{root}/RTH/B0/1day")&(P7.proxy=="RV")].iloc[0]
        M=FIVEMIN[("RTH","1day")]
        w=float(r.A*np.power(M,r.b))                    # Var(log RV_M) noise term
        lam=float(P3[(P3.root==root)&(P3.geom=="RTH")&(P3.btag=="B0")&
                     (P3.horizon=="1day")&(P3.range=="extended")].lam_intercept.iloc[0])
        NOISE[root]=dict(noise_var_logRV=w,v_single_day=w/4.0,
            v_lookback=w/(4.0*LOOKBACK),lam_intercept=lam,
            bias_exact_single=bias_exact(w/4.0),bias_exact_lookback=bias_exact(w/(4.0*LOOKBACK)),
            bias_2nd_single=bias_2nd(w/4.0),
            expansion_valid_single=bool(w/4.0<v10))
    out["noise"]=NOISE
    print("=== noise and bias per asset ===")
    print(json.dumps(NOISE,indent=1))
    print(f"expansion departs from exact by 10 percent at Var(log sigma_hat) = {v10:.4f}")
    # ---- build the book: in sample then holdout
    t=time.time()
    M5=FIVEMIN[("RTH","1day")]
    SER={}
    for root in ["ES","NQ"]:
        Sis=ho_series(root,"RTH","B0",holdout=False)
        Sho=ho_series(root,"RTH","B0",holdout=True)
        SER[root]=dict(
            rv_is=(subbars(Sis["rw"],M5)**2).sum(axis=1),
            rv_ho=(subbars(Sho["rw"],M5)**2).sum(axis=1),
            ret_is=Sis["ret"],ret_ho=Sho["ret"],
            d_is=Sis["wdates"],d_ho=Sho["wdates"])
    n=min(len(SER["ES"]["rv_ho"]),len(SER["NQ"]["rv_ho"]))
    m_is=min(len(SER["ES"]["rv_is"]),len(SER["NQ"]["rv_is"]))
    timers["build"]=round(time.time()-t,1)
    def weights(rv,v,lb=LOOKBACK):
        """Trailing-mean volatility estimate and its inverse, exact-bias corrected."""
        T=len(rv); s=np.full(T,np.nan)
        cs=np.concatenate([[0.0],np.cumsum(rv)])
        s[lb:]=np.sqrt((cs[lb:-0 or None][:T-lb]-cs[:T-lb])/lb) if False else np.nan
        for t_ in range(lb,T): s[t_]=np.sqrt(rv[t_-lb:t_].mean())
        inv_naive=1.0/np.maximum(s,1e-12)
        inv_corr=inv_naive*np.exp(-v/2.0)
        return s,inv_naive,inv_corr
    def run(sample,lb,v_key):
        rv={r:SER[r][f"rv_{sample}"] for r in ["ES","NQ"]}
        rt={r:SER[r][f"ret_{sample}"] for r in ["ES","NQ"]}
        T=min(len(rv["ES"]),len(rv["NQ"]))
        S={};IN={};IC={}
        for r in ["ES","NQ"]:
            S[r],IN[r],IC[r]=weights(rv[r][:T],NOISE[r][v_key],lb)
        wn={};wc={}
        dn=IN["ES"]+IN["NQ"]; dc=IC["ES"]+IC["NQ"]
        for r in ["ES","NQ"]:
            wn[r]=IN[r]/dn; wc[r]=IC[r]/dc
        # monthly rebalance: hold the weight fixed between rebalance dates
        def hold(w):
            out_=np.full_like(w,np.nan); last=np.nan
            for t_ in range(len(w)):
                if np.isfinite(w[t_]) and (t_%REBAL==0 or not np.isfinite(last)):
                    last=w[t_]
                out_[t_]=last
            return out_
        wnh={r:hold(wn[r]) for r in ["ES","NQ"]}
        wch={r:hold(wc[r]) for r in ["ES","NQ"]}
        ok=np.isfinite(wnh["ES"])&np.isfinite(wch["ES"])
        res={}
        for tag,W in [("naive",wnh),("corrected",wch)]:
            rp=sum(W[r][:T]*rt[r][:T] for r in ["ES","NQ"])
            rp=np.where(ok,rp,np.nan)
            vol=float(np.nanstd(rp,ddof=1)*np.sqrt(252))
            # realized risk contributions
            rcs={}
            for r in ["ES","NQ"]:
                cov=float(np.nanmean((W[r][:T]*rt[r][:T]-np.nanmean(W[r][:T]*rt[r][:T]))
                                     *(rp-np.nanmean(rp))))
                rcs[r]=cov
            tot=sum(rcs.values())
            imb=float(abs(rcs["ES"]-rcs["NQ"])/max(abs(tot),1e-300))
            turn=float(np.nanmean([np.abs(np.diff(W[r][ok])).sum()/max(ok.sum()/REBAL,1)
                                   for r in ["ES","NQ"]]))
            px={r:1.0 for r in ["ES","NQ"]}
            res[tag]=dict(realized_vol_ann=vol,risk_imbalance=imb,turnover_per_rebalance=turn,
                w_ES_mean=float(np.nanmean(W["ES"][ok])),
                w_NQ_mean=float(np.nanmean(W["NQ"][ok])),n=int(ok.sum()))
        dev=np.abs(wnh["ES"]-wch["ES"])[ok]
        res["weight_deviation"]=dict(mean=float(np.nanmean(dev)),
            max=float(np.nanmax(dev)),
            overweighted_asset=("ES" if np.nanmean(wnh["ES"]-wch["ES"])>0 else "NQ"),
            mean_signed_ES=float(np.nanmean(wnh["ES"]-wch["ES"])))
        res["rel_vol_diff_pct"]=100*abs(res["naive"]["realized_vol_ann"]-
            res["corrected"]["realized_vol_ann"])/res["corrected"]["realized_vol_ann"]
        np.savez_compressed(os.path.join(CACHE,f"k7_{sample}_{v_key}.npz"),
            w_naive_ES=wnh["ES"],w_naive_NQ=wnh["NQ"],
            w_corr_ES=wch["ES"],w_corr_NQ=wch["NQ"],ok=ok)
        return res
    t=time.time(); books={}
    for sample in ["is","ho"]:
        for v_key,lb in [("v_lookback",LOOKBACK),("v_single_day",1)]:
            books[f"{sample}_{v_key}"]=run(sample,lb,v_key)
    timers["book"]=round(time.time()-t,1)
    out["books"]=books
    # ---- cost sweep on the holdout, base case
    base=books["ho_v_lookback"]
    costs=[]
    for tk in TICKS:
        for tag in ["naive","corrected"]:
            turn=base[tag]["turnover_per_rebalance"]
            # two legs, ES and NQ, priced at their own tick values on a unit book
            c=float(turn*sum(2*tk*TICKVAL[r]/(MULT[r]*(4800 if r=="ES" else 16000))
                             for r in ["ES","NQ"])*1e4*(252/REBAL))
            costs.append(dict(ticks=tk,weighting=tag,turnover_per_rebalance=turn,
                              annual_cost_bps=c))
    CO=pd.DataFrame(costs); CO.to_csv(os.path.join(RES,"phase2_costs.csv"),index=False)
    pv=CO.pivot_table(index="ticks",columns="weighting",values="annual_cost_bps")
    pv["rel_diff_pct"]=100*(pv.naive-pv.corrected).abs()/pv.corrected
    out["cost_sweep"]=pv.reset_index().to_dict("records")
    k7=dict(threshold_weight=THRESH_W,threshold_vol=THRESH_TE,
        mean_abs_weight_deviation=base["weight_deviation"]["mean"],
        max_abs_weight_deviation=base["weight_deviation"]["max"],
        overweighted_asset=base["weight_deviation"]["overweighted_asset"],
        weight_criterion_met=bool(base["weight_deviation"]["mean"]<THRESH_W),
        rel_vol_diff_pct=base["rel_vol_diff_pct"],
        vol_criterion_met=bool(base["rel_vol_diff_pct"]<100*THRESH_TE),
        vol_criterion_met_all_sweep_points=bool(base["rel_vol_diff_pct"]<100*THRESH_TE),
        single_day_bound=dict(
            mean_abs_weight_deviation=books["ho_v_single_day"]["weight_deviation"]["mean"],
            rel_vol_diff_pct=books["ho_v_single_day"]["rel_vol_diff_pct"]),
        lookback=LOOKBACK,rebalance=REBAL)
    k7["K7"]=("FIRES" if (k7["weight_criterion_met"] or k7["vol_criterion_met"])
              else "DOES NOT FIRE")
    out["K7"]=k7
    # ---- illustration: the widest reliability pair in the cell set
    ill=[]
    L=P3[(P3.range=="extended")&(P3.valid==True)]
    lo=L.loc[L.lam_intercept.idxmin()]; hi=L.loc[L.lam_intercept.idxmax()]
    for nm,r in [("lowest_lambda",lo),("highest_lambda",hi)]:
        cell=f"{r.root}/{r.geom}/{r.btag}/{r.horizon}"
        p=P7[(P7.cell==cell)&(P7.proxy=="RV")]
        M=FIVEMIN[(r.geom,r.horizon)]
        w=float(p.A.iloc[0]*np.power(M,p.b.iloc[0])) if len(p) else np.nan
        ill.append(dict(leg=nm,cell=cell,lam_intercept=float(r.lam_intercept),
            noise_var_logRV=w,v_single_day=w/4,v_lookback=w/(4*LOOKBACK),
            bias_exact_single=bias_exact(w/4),bias_exact_lookback=bias_exact(w/(4*LOOKBACK))))
    IL=pd.DataFrame(ill)
    bs=float(IL[IL.leg=="lowest_lambda"].bias_exact_single.iloc[0]/
             IL[IL.leg=="highest_lambda"].bias_exact_single.iloc[0])
    bl=float(IL[IL.leg=="lowest_lambda"].bias_exact_lookback.iloc[0]/
             IL[IL.leg=="highest_lambda"].bias_exact_lookback.iloc[0])
    IL.to_csv(os.path.join(RES,"phase2_illustration.csv"),index=False)
    out["illustration"]=dict(rows=IL.to_dict("records"),
        bias_ratio_single_day=bs,bias_ratio_lookback=bl,
        implied_weight_deviation_single_day=float(bs/(1+bs)-0.5),
        implied_weight_deviation_lookback=float(bl/(1+bl)-0.5),
        label=("ILLUSTRATION on measured reliabilities, not a backtest. These two "
               "cells are not a tradeable pair; the calculation bounds how large "
               "the inverse-volatility bias can get given the reliability spread "
               "this programme actually measured."))
    out["holdout_read_count"]=dict(this_session=1,running_total=4,
        prior=["S09 Phase 6","S11 Phase 1","S11 Phases 8-9"])
    out["timers"]=timers
    json.dump(out,open(os.path.join(RES,"phase2_k7.json"),"w"),indent=1,default=str)
    pd.set_option("display.width",250)
    print("\n=== books ===")
    for k,v in books.items():
        print(f"-- {k}: naive vol {v['naive']['realized_vol_ann']:.4f} "
              f"corrected {v['corrected']['realized_vol_ann']:.4f} "
              f"rel {v['rel_vol_diff_pct']:.4f}% | mean|dw| "
              f"{v['weight_deviation']['mean']:.6f} max {v['weight_deviation']['max']:.6f} "
              f"| overweighted {v['weight_deviation']['overweighted_asset']}")
    print("\n=== cost sweep (holdout, base case) ==="); print(pv.to_string())
    print("\n=== illustration ==="); print(IL.to_string(index=False))
    print(f"bias ratio single-day {bs:.5f}, lookback {bl:.5f}")
    print("\n"+json.dumps(k7,indent=1))
    print(f"PHASE2 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
