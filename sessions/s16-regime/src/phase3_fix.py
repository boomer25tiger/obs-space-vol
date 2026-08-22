"""S16 Phase 3, corrected: the holdout at the CORRECT horizon for every cell.

DEFECT FOUND AND CORRECTED. The first Phase 3 run built the holdout portion of
every cell through S11's `ho_series`, which is the S07 `series()` body at
wlen=None and therefore produces DAILY windows only. The four 1day cells were
correct; the 1h and 30min cells had 621 daily windows appended to their intraday
in-sample series. This rebuilds the holdout with `phase6_holdout.wins` at the
cell's own horizon, the same wlen-aware path S11 Phase 1 used.

Only windows ENDING in the holdout region are refitted; the roll is warm-started
from a cold fit on the last fully in-sample window, so every holdout window still
sees a full 441-observation history that begins in sample.
"""
import json, os, sys, time
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common16 import (BASE,RES,CACHE,S09,CELLS8,CELLS4,FIVEMIN,WINDOW,MA_LEN,ARMS,
                      TICKS,TICKVAL,MULT,NDAY,gauss_hmm_fit)
from common import cell_windows,subbars
from proxies_robust import p1_rv,p3_kernel_flattop,kernel_H
import phase6_holdout as p6
def observables(x,lam,mu_is):
    ma=pd.Series(x).rolling(MA_LEN,min_periods=MA_LEN).mean().values
    return {"A1_raw":x,"A2_ma5":ma,"A3_shrunk":(1.0-lam)*mu_is+lam*x}
def build(root,geom,hname):
    M5=FIVEMIN[(geom,hname)]
    rw,kw,ds=cell_windows(root,geom,hname)
    rv=p1_rv(subbars(rw,M5)); pos=rv>0
    Mf=rw.shape[1]
    om2=float((rw**2).sum(axis=1).mean()/(2.0*Mf))
    Hk=kernel_H(Mf,om2,float(rv[pos].mean()))
    rk=np.maximum(p3_kernel_flattop(rw,Hk),1e-300)
    x_is=np.log(rv[pos]); r_is=np.log(rk[pos])
    z=np.load(os.path.join(S09,"cache",f"ho_panel_{root}_{geom}.npz"))
    rwh,kwh,HIw,LOw,OPw,CLw,live,nw=p6.wins(
        {k:z[k] for k in ["open","high","low","close"]},z["present"],z["tradeable"],
        "B0",geom,hname)                                  # wlen-aware, S11 Phase 1 path
    rwh=rwh[live]
    rvh=p1_rv(subbars(rwh,M5)); posh=rvh>0
    rkh=np.maximum(p3_kernel_flattop(rwh,Hk),1e-300)
    x=np.concatenate([x_is,np.log(rvh[posh])])
    r=np.concatenate([r_is,np.log(rkh[posh])])
    return x,r,len(x_is),int(Hk),int(posh.sum()),int(nw)
def roll_tail(v,n_is):
    """Refit only windows ending in the holdout; warm-start from the last
    fully in-sample window so history is identical to a full roll."""
    T=len(v); st=np.full(T,-1,np.int8); pr=np.full(T,np.nan)
    if n_is<WINDOW: return st,pr
    w0=v[n_is-WINDOW:n_is]
    if not np.isfinite(w0).all() or w0.std()<=0: return st,pr
    init,_=gauss_hmm_fit((w0-w0.mean())/w0.std())
    for e in range(n_is+1,T+1):
        w=v[e-WINDOW:e]
        if not np.isfinite(w).all(): continue
        s=w.std()
        if s<=0: continue
        p,g=gauss_hmm_fit((w-w.mean())/s,init=init); init=p
        st[e-1]=int(g[-1,1]>0.5); pr[e-1]=float(g[-1,1])
    return st,pr
def task(job):
    root,geom,hname,arm,lam=job
    x,r,n_is,Hk,n_ho,nw=build(root,geom,hname)
    mu_is=float(x[:n_is].mean())
    st,pr=roll_tail(observables(x,lam,mu_is)[arm],n_is)
    rst,rpr=roll_tail(r,n_is) if arm=="A1_raw" else (None,None)
    return dict(root=root,geom=geom,horizon=hname,arm=arm,states=st,probs=pr,
                ref_states=rst,n_is=n_is,n_ho=n_ho,windows_per_session=nw,H=Hk,x=x)
def metrics(st,ref,tag):
    ok=(st>=0)&(ref>=0); n=int(ok.sum())
    if n<10: return dict(sample=tag,n=n)
    a,b=st[ok],ref[ok]; dis=a!=b
    runs=[];cur=1
    for i in range(1,len(a)):
        if a[i]==a[i-1]: cur+=1
        else: runs.append(cur); cur=1
    runs.append(cur)
    return dict(sample=tag,n=n,misclass=float(dis.mean()),
        both_high=int(((a==1)&(b==1)).sum()),spurious_high=int(((a==1)&(b==0)).sum()),
        spurious_low=int(((a==0)&(b==1)).sum()),both_low=int(((a==0)&(b==0)).sum()),
        switches=int(np.abs(np.diff(a)).sum()),
        mean_regime_duration=float(np.mean(runs)),share_high=float(a.mean()))
def main():
    t0=time.time()
    P3=pd.read_csv(os.path.join(S09,"results","phase3_sizing_params.csv"))
    LAM={(r,g,h):float(P3[(P3.root==r)&(P3.geom==g)&(P3.btag=="B0")&(P3.horizon==h)&
         (P3["range"]=="extended")].lam_intercept.iloc[0]) for r,g,h in CELLS8}
    jobs=[(r,g,h,a,LAM[(r,g,h)]) for r,g,h in CELLS8 for a in ARMS]
    res={}
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs={ex.submit(task,j):j for j in jobs}
        for f in as_completed(futs):
            d=f.result(); res[(d["root"],d["geom"],d["horizon"],d["arm"])]=d
            print(f"  HOFIX {d['root']}/{d['geom']}/{d['horizon']} {d['arm']} "
                  f"n_ho={d['n_ho']} done",flush=True)
    rows=[]
    for root,geom,hname in CELLS8:
        ref=res[(root,geom,hname,"A1_raw")]["ref_states"]
        n_is=res[(root,geom,hname,"A1_raw")]["n_is"]
        for arm in ARMS:
            d=res[(root,geom,hname,arm)]
            m=metrics(d["states"][n_is:],ref[n_is:],"holdout")
            rows.append(dict(root=root,geom=geom,horizon=hname,arm=arm,
                windows_per_session=d["windows_per_session"],
                n_holdout_windows=d["n_ho"],**m))
            np.savez_compressed(os.path.join(CACHE,
                f"hofix_{root}_{geom}_{hname}_{arm}.npz"),
                states=d["states"],probs=d["probs"],ref_states=ref,n_is=n_is,x=d["x"])
    H=pd.DataFrame(rows); H.to_csv(os.path.join(RES,"phase3_classification_fixed.csv"),
                                   index=False)
    # identity check survives the fix
    ident=[]
    for root,geom,hname in CELLS8:
        n_is=res[(root,geom,hname,"A1_raw")]["n_is"]
        a1=res[(root,geom,hname,"A1_raw")]["states"][n_is:]
        a3=res[(root,geom,hname,"A3_shrunk")]["states"][n_is:]
        ok=(a1>=0)&(a3>=0)
        ident.append(dict(root=root,geom=geom,horizon=hname,n=int(ok.sum()),
            n_differ=int((a1[ok]!=a3[ok]).sum())))
    ID=pd.DataFrame(ident); ID.to_csv(os.path.join(RES,"phase3_identity_fixed.csv"),
                                      index=False)
    pd.set_option("display.width",270)
    print("\n=== PHASE 3 CORRECTED: holdout at the right horizon ===")
    print(H[["root","geom","horizon","arm","windows_per_session","n","misclass",
             "switches","mean_regime_duration","share_high"]].round(5).to_string(index=False))
    print("\n=== A1 vs A3 identity, holdout ==="); print(ID.to_string(index=False))
    json.dump(dict(timers=dict(phase3_fix=round(time.time()-t0,1)),
        n_a1_a3_differ_total=int(ID.n_differ.sum()),
        defect=("first run built the holdout via ho_series, which is wlen=None and "
                "yields daily windows only; the 1h and 30min cells were affected and "
                "the four 1day cells were not")),
        open(os.path.join(RES,"phase3_fix_summary.json"),"w"),indent=1)
    print(f"PHASE3-FIX DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
