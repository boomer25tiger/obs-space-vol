"""S14 Phase 1: K8, regime misclassification (items 107, 110).

DERIVATION. Let z = log IV and x = log RV = z + e with e ~ N(0, v) independent
of z, and let both series be classified against their own medians. Then u =
x - median(x) and w = z - median(z) are jointly normal, mean zero, with

    rho = Corr(x, z) = sd(z)/sqrt(Var(z) + v) = sqrt(lambda)

since lambda = Var(z)/Var(x) is exactly the reliability this programme measures.
By the bivariate normal orthant probability, P(u > 0, w < 0) = 1/4 -
arcsin(rho)/(2*pi), so

    MISCLASSIFICATION RATE = 2 * P(u>0, w<0) = arccos(sqrt(lambda)) / pi.

EXACT, not an expansion. Assumptions: joint normality of (log IV, noise),
independence of the noise from log IV, and thresholds at the respective medians.
The empirical rate is reported beside it throughout and the boundary at which
the two diverge by 10 percent is reported as a measured number.

CAVEAT stated in the report: the empirical rate compares two estimates, the
five-minute-equivalent RV and the finest-grid realized kernel, neither of which
is integrated variance. It therefore measures pairwise disagreement and is a
lower bound on disagreement with the truth if the kernel carries its own error.

HOLDOUT: this is the programme's FIFTH read (item 110).
"""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy.optimize import brentq
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common14 import (BASE,RES,CACHE,S09,S11,CELLS4,FIVEMIN,TICKS,TICKVAL,MULT,TARGET_D)
from common import subbars
from phase8910_apps import ho_series                      # S11, equivalence-asserted
from proxies_robust import p1_rv, p3_kernel_flattop, kernel_H, rq
def analytic_rate(lam):
    lam=float(np.clip(lam,0.0,1.0))
    return float(np.arccos(np.sqrt(lam))/np.pi)
def classify(v,thr): return (v>thr).astype(int)
def episodes(mask):
    runs=[];cur=0
    for b in mask:
        if b: cur+=1
        elif cur: runs.append(cur); cur=0
    if cur: runs.append(cur)
    return runs
def main():
    t0=time.time(); timers={}; out={}
    P3=pd.read_csv(os.path.join(S09,"results","phase3_sizing_params.csv"))
    rows=[]; cond=[]; costs=[]; terc=[]
    t=time.time()
    for root,geom in CELLS4:
        M5=FIVEMIN[(geom,"1day")]
        Sis=ho_series(root,geom,"B0",holdout=False)
        Sho=ho_series(root,geom,"B0",holdout=True)
        rv_is=p1_rv(subbars(Sis["rw"],M5)); rv_ho=p1_rv(subbars(Sho["rw"],M5))
        Mf_is=Sis["rw"].shape[1]; Mf_ho=Sho["rw"].shape[1]
        om2=float((Sis["rw"]**2).sum(axis=1).mean()/(2.0*Mf_is))
        ivh=float(rv_is.mean())
        H_is=kernel_H(Mf_is,om2,ivh); H_ho=kernel_H(Mf_ho,om2,ivh)
        rk_is=np.maximum(p3_kernel_flattop(Sis["rw"],H_is),1e-300)
        rk_ho=np.maximum(p3_kernel_flattop(Sho["rw"],H_ho),1e-300)
        lam=float(P3[(P3.root==root)&(P3.geom==geom)&(P3.btag=="B0")&
                     (P3.horizon=="1day")&(P3.range=="extended")].lam_intercept.iloc[0])
        # THRESHOLD FIXED IN SAMPLE, per item 107, and never re-estimated
        lx_is=np.log(np.maximum(rv_is,1e-300)); lz_is=np.log(rk_is)
        thr_x=float(np.median(lx_is)); thr_z=float(np.median(lz_is))
        ar=analytic_rate(lam)
        for tag,lx,lz in [("insample",lx_is,lz_is),
                          ("holdout",np.log(np.maximum(rv_ho,1e-300)),np.log(rk_ho))]:
            cp=classify(lx,thr_x); cb=classify(lz,thr_z)
            n=len(cp); dis=cp!=cb
            tp=int(((cp==1)&(cb==1)).sum()); fp=int(((cp==1)&(cb==0)).sum())
            fn=int(((cp==0)&(cb==1)).sum()); tn=int(((cp==0)&(cb==0)).sum())
            eps=episodes(dis)
            rows.append(dict(root=root,geom=geom,sample=tag,split="median",
                n=n,both_high=tp,spurious_high=fp,spurious_low=fn,both_low=tn,
                empirical_rate=float(dis.mean()),analytic_rate=ar,
                lam_intercept=lam,
                rate_gap_prop=float(dis.mean()/ar-1.0) if ar>0 else np.nan,
                n_episodes=len(eps),
                mean_episode_duration=float(np.mean(eps)) if eps else 0.0,
                max_episode_duration=int(max(eps)) if eps else 0,
                threshold_log_rv=thr_x,threshold_log_kernel=thr_z))
            # rate conditional on distance from the threshold
            d=np.abs(lx-thr_x); qs=np.quantile(d,[0.2,0.4,0.6,0.8])
            band=np.searchsorted(qs,d)
            for b in range(5):
                m=band==b
                if m.sum()<10: continue
                cond.append(dict(root=root,geom=geom,sample=tag,distance_quintile=b+1,
                    n=int(m.sum()),mean_abs_distance=float(d[m].mean()),
                    empirical_rate=float(dis[m].mean())))
            # tercile split, same in-sample cut points
            if tag=="insample":
                qx=np.quantile(lx_is,[1/3,2/3]); qz=np.quantile(lz_is,[1/3,2/3])
            tp3=np.searchsorted(qx,lx); tz3=np.searchsorted(qz,lz)
            d3=tp3!=tz3
            terc.append(dict(root=root,geom=geom,sample=tag,split="tercile",
                n=len(lx),empirical_rate=float(d3.mean()),
                n_off_by_two=int((np.abs(tp3-tz3)==2).sum()),
                analytic_rate_median_split=ar))
        # ---- priced illustration: two-state ES-style book, regime on / cash off
        lx=np.log(np.maximum(rv_ho,1e-300)); lz=np.log(rk_ho)
        cp=classify(lx,thr_x); cb=classify(lz,thr_z)
        # LOW-vol state invested, HIGH-vol state in cash
        inv_p=(cp==0).astype(float); inv_b=(cb==0).astype(float)
        sw_p=int(np.abs(np.diff(inv_p)).sum()); sw_b=int(np.abs(np.diff(inv_b)).sum())
        spurious_sw=int(np.abs(np.diff(inv_p)-np.diff(inv_b)).sum())
        px=float(np.exp(np.load(os.path.join(S09,"cache",
             f"ho_panel_{root}_{geom}.npz"))["close"].astype(np.float64)).mean())
        notional=MULT[root]*px
        w_typ=float(TARGET_D/np.sqrt(np.median(rv_ho)))
        for tk in TICKS:
            rt=2*tk*TICKVAL[root]/notional
            costs.append(dict(root=root,geom=geom,ticks=tk,
                switches_proxy=sw_p,switches_best=sw_b,excess_switches=spurious_sw,
                cost_proxy_bps=float(sw_p*w_typ*rt*1e4),
                cost_best_bps=float(sw_b*w_typ*rt*1e4),
                excess_cost_bps=float(spurious_sw*w_typ*rt*1e4),
                n_days=len(inv_p)))
        np.savez_compressed(os.path.join(CACHE,f"k8_{root}_{geom}.npz"),
            lx_is=lx_is,lz_is=lz_is,lx_ho=lx,lz_ho=lz,thr_x=thr_x,thr_z=thr_z,
            class_proxy_ho=cp,class_best_ho=cb,lam=lam,H_kernel_is=H_is,H_kernel_ho=H_ho)
    timers["k8"]=round(time.time()-t,1)
    K=pd.DataFrame(rows); K.to_csv(os.path.join(RES,"phase1_k8_rates.csv"),index=False)
    CD=pd.DataFrame(cond); CD.to_csv(os.path.join(RES,"phase1_by_distance.csv"),index=False)
    TC=pd.DataFrame(terc); TC.to_csv(os.path.join(RES,"phase1_tercile.csv"),index=False)
    CO=pd.DataFrame(costs); CO.to_csv(os.path.join(RES,"phase1_switch_costs.csv"),index=False)
    # analytic-vs-empirical boundary: lambda at which they diverge by 10 percent
    ins=K[K["sample"]=="insample"]
    lam_grid=np.linspace(0.30,0.99,400)
    fitgap=np.interp(lam_grid,ins.sort_values("lam_intercept").lam_intercept,
                     ins.sort_values("lam_intercept").rate_gap_prop)
    idx=np.where(np.abs(fitgap)>0.10)[0]
    bnd=float(lam_grid[idx[0]]) if len(idx) else None
    k8=dict(analytic_relation="misclassification rate = arccos(sqrt(lambda)) / pi, exact",
        assumptions=("joint normality of log IV and the proxy noise, independence of "
            "the noise from log IV, thresholds at the respective medians"),
        max_abs_analytic_vs_empirical_gap_prop=float(ins.rate_gap_prop.abs().max()),
        lambda_at_10pct_divergence=bnd,
        empirical_rate_range_insample=[float(ins.empirical_rate.min()),
                                       float(ins.empirical_rate.max())],
        analytic_rate_range=[float(ins.analytic_rate.min()),
                             float(ins.analytic_rate.max())],
        empirical_rate_range_holdout=[float(K[K["sample"]=="holdout"].empirical_rate.min()),
                                      float(K[K["sample"]=="holdout"].empirical_rate.max())],
        tercile_rate_range=[float(TC.empirical_rate.min()),float(TC.empirical_rate.max())],
        max_excess_cost_bps=float(CO.excess_cost_bps.max()),
        all_empirical_below_5pct=bool((K.empirical_rate<0.05).all()),
        all_analytic_below_5pct=bool((ins.analytic_rate<0.05).all()),
        threshold=0.05,
        caveat=("The empirical rate compares the five-minute-equivalent RV against "
            "the finest-grid realized kernel; neither is integrated variance, so it "
            "measures pairwise disagreement. If the kernel carries its own error the "
            "empirical rate understates disagreement with the truth, which is why "
            "the analytic rate, keyed to the measured reliability, is reported "
            "beside it."),
        illustration_label=("The two-state allocation is an ILLUSTRATION on measured "
            "misclassification, not a strategy backtest. No return series is claimed."))
    k8["K8"]=("FIRES" if (k8["all_empirical_below_5pct"] and k8["all_analytic_below_5pct"])
              else "DOES NOT FIRE")
    out["K8"]=k8; out["holdout_read"]=dict(this_session=1,running_total=5,
        prior=["S09 Phase 6","S11 Phase 1","S11 Phases 8-9","S13 Phase 2"])
    out["timers"]=timers
    json.dump(out,open(os.path.join(RES,"phase1_k8.json"),"w"),indent=1,default=str)
    pd.set_option("display.width",260)
    print("=== K8 median split ===")
    print(K[["root","geom","sample","n","empirical_rate","analytic_rate","lam_intercept",
             "rate_gap_prop","n_episodes","mean_episode_duration"]].to_string(index=False))
    print("\n=== confusion, holdout ===")
    print(K[K["sample"]=="holdout"][["root","geom","both_high","spurious_high",
        "spurious_low","both_low"]].to_string(index=False))
    print("\n=== rate by distance from threshold (in sample) ===")
    print(CD[CD["sample"]=="insample"].to_string(index=False))
    print("\n=== tercile split ==="); print(TC.to_string(index=False))
    print("\n=== switch cost illustration (holdout) ===")
    print(CO.pivot_table(index=["root","geom"],columns="ticks",
                         values="excess_cost_bps").to_string())
    print(); print(json.dumps(k8,indent=1))
    print(f"PHASE1 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
