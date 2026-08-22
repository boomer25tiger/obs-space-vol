"""S17 Phases 1 and 2: lag alignment of A2 (item 123), and the 30min inversion
(item 124). Pre-2024 panels and persisted S16 artifacts only."""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy import stats
from concurrent.futures import ProcessPoolExecutor, as_completed
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common17 import (BASE,RES,CACHE,S16,CELLS8,MA_LEN,WINDOW,build_cell,roll,metrics)
MAXLAG=10
def ma(v,k=MA_LEN): return pd.Series(v).rolling(k,min_periods=k).mean().values
def job_ref_ma(j):
    """Reference smoothed IDENTICALLY to A2, so filter and reference are
    phase-matched. In sample and holdout tail."""
    root,geom,hname=j
    x,r,n_is,Hk=build_cell(root,geom,hname,with_holdout=True)
    st_is,pr_is,_,d1=roll(ma(r)[:n_is])
    st_ho,pr_ho,_,d2=roll(ma(r),start=n_is-1)
    return dict(root=root,geom=geom,horizon=hname,n_is=n_is,
                ref_ma_is=st_is,ref_ma_ho=st_ho,diag=(d1,d2))
def job_params(j):
    """Per-window emission parameters for the 30min cells."""
    root,geom,hname=j
    x,r,n_is,Hk=build_cell(root,geom,hname,with_holdout=True)
    st_is,pr_is,par_is,_=roll(x[:n_is],record_params=True)
    st_ho,pr_ho,par_ho,_=roll(x,start=n_is-1,record_params=True)
    rst_is,_,_,_=roll(r[:n_is]); rst_ho,_,_,_=roll(r,start=n_is-1)
    return dict(root=root,geom=geom,horizon=hname,n_is=n_is,
                par_is=np.array(par_is),par_ho=np.array(par_ho),
                st_is=st_is,st_ho=st_ho,ref_is=rst_is,ref_ho=rst_ho)
def main():
    t0=time.time(); timers={}; out={}
    # ============ PHASE 1
    t=time.time()
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs={ex.submit(job_ref_ma,c):c for c in CELLS8}
        refma={}
        for f in as_completed(futs):
            d=f.result(); refma[(d["root"],d["geom"],d["horizon"])]=d
            print(f"  refMA {d['root']}/{d['geom']}/{d['horizon']} done",flush=True)
    timers["phase1_refma"]=round(time.time()-t,1)
    rows=[]
    for root,geom,hname in CELLS8:
        R=refma[(root,geom,hname)]; n_is=R["n_is"]
        z16i=np.load(os.path.join(S16,"cache",f"is_{root}_{geom}_{hname}_A2_ma5.npz"))
        z16h=np.load(os.path.join(S16,"cache",f"hofix_{root}_{geom}_{hname}_A2_ma5.npz"))
        a1i=np.load(os.path.join(S16,"cache",f"is_{root}_{geom}_{hname}_A1_raw.npz"))
        a1h=np.load(os.path.join(S16,"cache",f"hofix_{root}_{geom}_{hname}_A1_raw.npz"))
        for tag,a2,a1,ref_orig,ref_ma,sl in [
            ("insample",z16i["states"],a1i["states"],a1i["ref_states"],
             R["ref_ma_is"],slice(0,None)),
            ("holdout",z16h["states"][z16h["n_is"]:],a1h["states"][a1h["n_is"]:],
             a1h["ref_states"][a1h["n_is"]:],R["ref_ma_ho"][n_is:],slice(0,None))]:
            n=min(len(a2),len(ref_orig),len(ref_ma),len(a1))
            a2,a1,ro,rm=a2[:n],a1[:n],ref_orig[:n],ref_ma[:n]
            m_s16=metrics(a2,ro,tag).get("misclass",np.nan)
            m_pm=metrics(a2,rm,tag).get("misclass",np.nan)
            m_a1=metrics(a1,ro,tag).get("misclass",np.nan)
            best=(None,np.inf)
            for L in range(0,MAXLAG+1):
                if L==0: aa,rr=a2,ro
                else: aa,rr=a2[L:],ro[:-L]
                mm=metrics(aa,rr,tag).get("misclass",np.nan)
                if np.isfinite(mm) and mm<best[1]: best=(L,mm)
            # is the rate distinguishable from chance at this sample size?
            ok=(a2>=0)&(ro>=0); nn=int(ok.sum()); k=int((a2[ok]!=ro[ok]).sum())
            p_chance=float(stats.binomtest(k,nn,0.5).pvalue) if nn>0 else np.nan
            rows.append(dict(root=root,geom=geom,horizon=hname,sample=tag,n=nn,
                mis_A1=m_a1,mis_A2_s16=m_s16,
                mis_A2_phase_matched=m_pm,
                best_lag=best[0],mis_A2_best_lag=best[1],
                gap_s16_pp=100*(m_s16-m_a1),
                gap_phase_matched_pp=100*(m_pm-m_a1),
                gap_best_lag_pp=100*(best[1]-m_a1),
                p_vs_chance=p_chance,
                distinguishable_from_chance=bool(p_chance<0.05)))
        np.savez_compressed(os.path.join(CACHE,f"refma_{root}_{geom}_{hname}.npz"),
            ref_ma_is=R["ref_ma_is"],ref_ma_ho=R["ref_ma_ho"],n_is=n_is)
    P1=pd.DataFrame(rows); P1.to_csv(os.path.join(RES,"phase1_lag_alignment.csv"),index=False)
    pd.set_option("display.width",280)
    print("\n=== PHASE 1: A2 lag alignment ===")
    print(P1[["root","geom","horizon","sample","n","mis_A1","mis_A2_s16",
              "mis_A2_phase_matched","best_lag","mis_A2_best_lag","gap_s16_pp",
              "gap_phase_matched_pp","gap_best_lag_pp","p_vs_chance",
              "distinguishable_from_chance"]].round(5).to_string(index=False))
    ho=P1[P1["sample"]=="holdout"]
    out["phase1"]=dict(
        gap_s16_pp_range=[float(ho.gap_s16_pp.min()),float(ho.gap_s16_pp.max())],
        gap_phase_matched_pp_range=[float(ho.gap_phase_matched_pp.min()),
                                    float(ho.gap_phase_matched_pp.max())],
        gap_best_lag_pp_range=[float(ho.gap_best_lag_pp.min()),
                               float(ho.gap_best_lag_pp.max())],
        n_cells_gap_positive_phase_matched=int((ho.gap_phase_matched_pp>0).sum()),
        n_cells_gap_positive_best_lag=int((ho.gap_best_lag_pp>0).sum()),
        n_cells=int(len(ho)),
        best_lags=[int(v) for v in ho.best_lag],
        n_cells_indistinguishable_from_chance=int((~ho.distinguishable_from_chance).sum()))
    # ============ PHASE 2
    t=time.time()
    with ProcessPoolExecutor(max_workers=4) as ex:
        futs={ex.submit(job_params,(r,g,"30min")):r for r,g in [("ES","RTH"),("NQ","RTH")]}
        pr={}
        for f in as_completed(futs):
            d=f.result(); pr[(d["root"],d["geom"])]=d
            print(f"  params {d['root']}/{d['geom']}/30min done",flush=True)
    timers["phase2_params"]=round(time.time()-t,1)
    rows2=[]; fix=[]
    for root,geom in [("ES","RTH"),("NQ","RTH")]:
        D=pr[(root,geom)]; n_is=D["n_is"]
        for tag,par,st,ref in [("insample",D["par_is"],D["st_is"][:n_is],D["ref_is"][:n_is]),
                               ("holdout",D["par_ho"],D["st_ho"][n_is:],D["ref_ho"][n_is:])]:
            if not len(par): continue
            sep=par[:,5]
            rows2.append(dict(root=root,geom=geom,horizon="30min",sample=tag,
                n_windows=len(par),mu_lo_mean=float(par[:,1].mean()),
                mu_hi_mean=float(par[:,2].mean()),
                sd_lo_mean=float(par[:,3].mean()),sd_hi_mean=float(par[:,4].mean()),
                separation_mean=float(sep.mean()),separation_median=float(np.median(sep)),
                share_separation_below_0p5=float((sep<0.5).mean()),
                share_separation_below_1p0=float((sep<1.0).mean()),
                mis=metrics(st,ref,tag).get("misclass",np.nan),
                switches=int(np.abs(np.diff(st[st>=0])).sum()) if (st>=0).sum()>1 else 0))
        # label-swap frequency: sign flips in mu_hi - mu_lo ordering are removed by
        # the mean-ordering rule, so instability shows as the ordering gap collapsing
        for tag,par in [("insample",D["par_is"]),("holdout",D["par_ho"])]:
            if not len(par): continue
            gap=par[:,2]-par[:,1]
            fix.append(dict(root=root,geom=geom,sample=tag,n=len(par),
                min_mu_gap=float(gap.min()),share_gap_below_0p1=float((gap<0.1).mean()),
                share_gap_below_0p25=float((gap<0.25).mean())))
        np.savez_compressed(os.path.join(CACHE,f"params30_{root}_{geom}.npz"),
            par_is=D["par_is"],par_ho=D["par_ho"],st_is=D["st_is"],st_ho=D["st_ho"],
            ref_is=D["ref_is"],ref_ho=D["ref_ho"],n_is=n_is)
    P2=pd.DataFrame(rows2); P2.to_csv(os.path.join(RES,"phase2_30min_params.csv"),index=False)
    F2=pd.DataFrame(fix); F2.to_csv(os.path.join(RES,"phase2_label_stability.csv"),index=False)
    print("\n=== PHASE 2: 30min emission parameters ===")
    print(P2.round(5).to_string(index=False))
    print("\n=== label stability ==="); print(F2.round(5).to_string(index=False))
    out["phase2"]=dict(rows=P2.to_dict("records"),stability=F2.to_dict("records"))
    out["timers"]=timers
    json.dump(out,open(os.path.join(RES,"phase12_summary.json"),"w"),indent=1,default=str)
    print(f"\nPHASE1+2 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
