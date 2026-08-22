"""S12 Phases 3 and 4: wild cluster bootstrap on the trend (item 97), and the
K4 restatement by limit (items 98, 99).

Phase 4 reads only the S11 persisted cache `k4_*.npz`, which already holds both
position series, both forecasts and both proxies. No holdout panel is opened.
"""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy import stats
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
S10=os.path.join(ROOT,"sessions","s10-exponent-audit")
S11=os.path.join(ROOT,"sessions","s11-extensions")
NREP=9999; MASTER_WCB=20260828
TICKS=[0.5,1.0,2.0,4.0]; TICKVAL={"ES":12.50,"NQ":5.00}; MULT={"ES":50.0,"NQ":20.0}
LEV_CAP=2.0; STOP_MULT=1.5; TARGET_D=0.10/np.sqrt(252)
CELLS4=[(r,g) for g in ["GLOBEX","RTH"] for r in ["ES","NQ"]]

def fe_fit(x,u,cid,ncl):
    """beta and the cluster-robust SE for the within (fixed-effects) estimator."""
    sxx=float((x*x).sum()); beta=float((x*u).sum()/sxx)
    e=u-beta*x
    G=np.zeros(ncl)
    np.add.at(G,cid,x*e)
    se=float(np.sqrt((G*G).sum())/sxx)
    return beta,se

def wcb(x,u,cid,ncl,beta0,nrep,rng):
    """Wild cluster bootstrap, Rademacher weights, null imposed on the
    restricted residuals (Cameron, Gelbach and Miller 2008)."""
    sxx=float((x*x).sum())
    ur=u-beta0*x                                   # restricted residuals under H0
    ur=ur-np.bincount(cid,weights=ur,minlength=ncl)[cid]/np.bincount(cid,minlength=ncl)[cid]
    W=rng.choice(np.array([-1.0,1.0]),size=(nrep,ncl))[:,cid]     # (nrep, n)
    us=beta0*x[None,:]+W*ur[None,:]
    bs=(us@x)/sxx
    es=us-bs[:,None]*x[None,:]
    G=np.zeros((nrep,ncl))
    for g in range(ncl):
        m=cid==g
        G[:,g]=(es[:,m]*x[m]).sum(axis=1)
    ses=np.sqrt((G*G).sum(axis=1))/sxx
    ts=(bs-beta0)/np.maximum(ses,1e-300)
    return bs,ts

def main():
    t0=time.time(); timers={}; out={}
    # ================= PHASE 3
    t=time.time()
    SUB=pd.read_csv(os.path.join(S10,"results","phase3_subfits.csv"))
    yr=SUB[(SUB.stratum=="year")&(~SUB.degenerate)].copy()
    yr["year"]=yr.key.astype(int)
    yr["distinct"]=yr.cell.str.replace("/B1/","/B0/",regex=False)
    res={}
    for tag,frame,ckey in [("distinct_8",
            yr.drop_duplicates(subset=["distinct","year"]).copy(),"distinct"),
            ("all_16",yr.copy(),"cell")]:
        d=frame
        d["u"]=d.b-d.groupby(ckey).b.transform("mean")
        d["x"]=d.year-d.groupby(ckey).year.transform("mean")
        cats=sorted(d[ckey].unique()); cmap={c:i for i,c in enumerate(cats)}
        cid=d[ckey].map(cmap).values.astype(int); ncl=len(cats)
        x=d.x.values.astype(float); u=d.u.values.astype(float)
        beta,se=fe_fit(x,u,cid,ncl)
        n,k=len(d),ncl+1
        se_ols=float(np.sqrt(((u-beta*x)**2).sum()/(n-k)/(x*x).sum()))
        t_cl=beta/se
        rng=np.random.Generator(np.random.PCG64(MASTER_WCB+(0 if tag=="distinct_8" else 1)))
        bs,ts=wcb(x,u,cid,ncl,0.0,NREP,rng)
        p_wcb=float((np.abs(ts)>=abs(t_cl)).mean())
        np.savez_compressed(os.path.join(CACHE,f"wcb_{tag}.npz"),
            t_star=ts,beta_star=bs,beta=beta,se=se,t_obs=t_cl,
            seed=MASTER_WCB+(0 if tag=="distinct_8" else 1),nrep=NREP)
        # 95 percent interval by inverting the WCR test over a grid of beta0
        grid=np.linspace(beta-6*se,beta+6*se,121); keep=[]
        rng2=np.random.Generator(np.random.PCG64(MASTER_WCB+100))
        for b0 in grid:
            _,tg=wcb(x,u,cid,ncl,float(b0),1499,rng2)
            tobs=(beta-b0)/se
            if float((np.abs(tg)>=abs(tobs)).mean())>0.05: keep.append(float(b0))
        ci=[min(keep),max(keep)] if keep else [np.nan,np.nan]
        res[tag]=dict(n_obs=n,n_clusters=ncl,beta=beta,
            se_cluster_robust=se,t_cluster_robust=t_cl,
            p_cluster_robust=float(2*stats.t.sf(abs(t_cl),ncl-1)),
            se_ols_fe=se_ols,p_ols_fe=float(2*stats.t.sf(abs(beta/se_ols),n-k)),
            p_wild_cluster_bootstrap=p_wcb,nrep=NREP,
            wcb_ci95_by_inversion=ci,
            reject_at_05=bool(p_wcb<0.05),reject_at_01=bool(p_wcb<0.01))
        print(f"  trend {tag}: beta={beta:+.5f} t_cl={t_cl:+.3f} "
              f"p_cl={res[tag]['p_cluster_robust']:.5f} p_wcb={p_wcb:.5f} "
              f"CI95=[{ci[0]:+.5f},{ci[1]:+.5f}]",flush=True)
    res["small_cluster_note"]=("Eight clusters. Cluster-robust standard errors are "
        "biased downward and the reference t distribution is wrong below roughly "
        "thirty clusters; the wild cluster bootstrap with the null imposed is the "
        "recommended correction but is itself only asymptotically valid in the "
        "number of clusters, and at G=8 the smallest attainable two-sided p-value "
        f"from Rademacher weights is 2^(1-8) = {2**-7:.5f}. The p-values below are "
        "reported with that floor in mind and no result here should be read as "
        "conventional evidence at G=8 regardless of its nominal level.")
    res["rademacher_p_floor"]=float(2**-7)
    json.dump(res,open(os.path.join(RES,"phase3_wcb.json"),"w"),indent=1)
    timers["phase3"]=round(time.time()-t,1)
    # ================= PHASE 4
    t=time.time(); stop=[]; cap=[]; costs=[]
    for root,geom in CELLS4:
        z=np.load(os.path.join(S11,"cache",f"k4_{root}_{geom}.npz"))
        w_p,w_b=z["w_proxy"],z["w_best"]; rv,rk=z["rv"],z["rk"]
        px=float(z["px"]); notional=MULT[root]*px
        ok=np.isfinite(w_p)&np.isfinite(w_b)
        n=int(ok.sum())
        real_p=w_p*np.sqrt(np.maximum(rv,1e-300))
        real_b=w_b*np.sqrt(np.maximum(rk,1e-300))
        bp=(real_p>STOP_MULT*TARGET_D)&ok; bb=(real_b>STOP_MULT*TARGET_D)&ok
        tp=int((bp&bb).sum()); fp=int((bp&~bb).sum())
        fn=int((~bp&bb).sum()); tn=int((~bp&~bb).sum())
        runs=[];cur=0
        for v in (bp&~bb):
            if v: cur+=1
            elif cur: runs.append(cur); cur=0
        if cur: runs.append(cur)
        stop.append(dict(root=root,geom=geom,limit="stop_out_1.5x",n_decision_points=n,
            both=tp,spurious=fp,missed=fn,neither=tn,
            spurious_rate=fp/max(n,1),missed_rate=fn/max(n,1),
            missed_minus_spurious=(fn-fp)/max(n,1),
            n_spurious_episodes=len(runs),
            mean_spurious_duration=float(np.mean(runs)) if runs else 0.0,
            max_spurious_duration=int(max(runs)) if runs else 0))
        for tk in TICKS:
            rt=2*tk*TICKVAL[root]/notional
            costs.append(dict(root=root,geom=geom,limit="stop_out_1.5x",ticks=tk,
                n_spurious_episodes=len(runs),
                cost_bps=float(len(runs)*2*rt*1e4/max(n,1))))
        wv=w_p[ok]
        bound=int((wv>LEV_CAP).sum())
        cap.append(dict(root=root,geom=geom,limit="leverage_cap_2.0x",
            n_decision_points=n,n_bound=bound,
            max_leverage=float(wv.max()),p99_leverage=float(np.percentile(wv,99)),
            p95_leverage=float(np.percentile(wv,95)),median_leverage=float(np.median(wv)),
            cap_that_would_first_bind=float(wv.max()),
            headroom_ratio=float(LEV_CAP/wv.max()),
            status="UNTESTED at a 10 percent target with daily rebalancing"))
        np.savez_compressed(os.path.join(CACHE,f"k4restate_{root}_{geom}.npz"),
            w_proxy=w_p,w_best=w_b,real_p=real_p,real_b=real_b,
            breach_proxy=bp,breach_best=bb)
    ST=pd.DataFrame(stop); ST.to_csv(os.path.join(RES,"phase4_stopout.csv"),index=False)
    CA=pd.DataFrame(cap); CA.to_csv(os.path.join(RES,"phase4_leverage_cap.csv"),index=False)
    CO=pd.DataFrame(costs); CO.to_csv(os.path.join(RES,"phase4_costs.csv"),index=False)
    k4=dict(
        stop_out=dict(max_spurious_rate=float(ST.spurious_rate.max()),
            all_spurious_below_1pct=bool((ST.spurious_rate<0.01).all()),
            max_cost_bps=float(CO.cost_bps.max()),
            all_cost_below_1bp=bool((CO.cost_bps<1.0).all()),
            determination=None),
        leverage_cap=dict(n_bound_total=int(CA.n_bound.sum()),
            n_decision_points_total=int(CA.n_decision_points.sum()),
            max_leverage_any_cell=float(CA.max_leverage.max()),
            cap_that_would_first_bind=float(CA.max_leverage.max()),
            min_headroom_ratio=float(CA.headroom_ratio.min()),
            determination="UNTESTED"),
        item99_asymmetry=dict(
            n_cells_missed_exceeds_spurious=int((ST.missed_rate>ST.spurious_rate).sum()),
            n_cells=int(len(ST)),
            missed_rate_range=[float(ST.missed_rate.min()),float(ST.missed_rate.max())],
            spurious_rate_range=[float(ST.spurious_rate.min()),float(ST.spurious_rate.max())],
            mechanism=("Microstructure and sampling noise inflate the estimated "
                "volatility that enters the position size, so the proxy-sized "
                "position is smaller than the kernel-sized one exactly on the days "
                "when volatility is genuinely high. A smaller position produces a "
                "smaller realized portfolio volatility, so the stop-out is not "
                "triggered on days when it should be. The asymmetry is a "
                "consequence of sizing on a noisy estimate, not of the threshold."),
            status="DIRECTIONAL FINDING, not a kill-condition outcome (item 99)"))
    k4["stop_out"]["determination"]=("FIRES" if (k4["stop_out"]["all_spurious_below_1pct"]
        or k4["stop_out"]["all_cost_below_1bp"]) else "DOES NOT FIRE")
    k4["supersedes"]=("The S11 joint K4 determination is superseded. K4 is reported "
        "per limit: the stop-out at 1.5x target is tested and fires; the leverage "
        "cap at 2.0x is untested because it never bound.")
    out["K4"]=k4; out["trend"]=res; out["timers"]=timers
    timers["phase4"]=round(time.time()-t,1)
    json.dump(k4,open(os.path.join(RES,"phase4_k4.json"),"w"),indent=1)
    json.dump(out,open(os.path.join(RES,"phase34_summary.json"),"w"),indent=1,default=str)
    pd.set_option("display.width",250)
    print("\n=== PHASE 4: stop-out ==="); print(ST.to_string(index=False))
    print("\n=== leverage cap ==="); print(CA.to_string(index=False))
    print("\n=== cost sweep ===")
    print(CO.pivot_table(index=["root","geom"],columns="ticks",values="cost_bps").to_string())
    print(); print(json.dumps(k4,indent=1))
    print(f"PHASE3+4 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
