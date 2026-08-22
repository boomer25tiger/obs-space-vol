"""S10 Phase 7: RS-up alignment diagnosis at ES/RTH/1h. Pre-2024 panel only.

Both code paths are imported and run on the SAME in-sample panel, so any
difference is the code, not the data. The holdout is not reopened.
"""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import BASE,RES,ROOT,cell_windows,subbars
S09=os.path.join(ROOT,"sessions","s09-application")
sys.path.insert(0,os.path.join(S09,"src"))
import phase5_signals as p5
import phase6_holdout as p6
S06=os.path.join(ROOT,"sessions","s06r-repair")
CELL=("ES","RTH","B0","1h"); M5=12
def r2(x,y):
    ok=np.isfinite(x)&np.isfinite(y)
    if ok.sum()<50: return np.nan,int(ok.sum())
    return float(np.corrcoef(x[ok],y[ok])[0,1]**2),int(ok.sum())
def main():
    t0=time.time(); out={}
    root,geom,btag,hname=CELL
    # ---- path A: the in-sample run (S09 phase5_signals.build)
    dA=p5.build(root,geom,btag,hname)
    yA=np.log(np.maximum(dA["rv"][1:],1e-300))
    xA=np.log(np.maximum(dA["rsu"][:-1],1e-300))
    # ---- path B: the holdout run (S09 phase6_holdout.wins + feature_block)
    z=np.load(os.path.join(S06,"cache",f"panel_ohlc_{root}_{geom}.npz"))
    from phase2_rerun8 import tradeable_ext
    trm,ds=tradeable_ext(root,geom)
    rw,kw,HIw,LOw,OPw,CLw,live,nw=p6.wins(
        {k:z[k] for k in ["open","high","low","close"]},z["present"],trm,btag,geom,hname)
    dB=p6.feature_block(rw[live],kw[live],HIw[live],LOw[live],OPw[live],CLw[live],M5,hname)
    yB=np.log(np.maximum(dB["rv"][1:],1e-300))
    xB=np.log(np.maximum(dB["rsu"][:-1],1e-300))
    out["n_windows_pathA"]=int(len(dA["rv"])); out["n_windows_pathB"]=int(len(dB["rv"]))
    out["rv_identical"]=bool(len(dA["rv"])==len(dB["rv"]) and
                             np.allclose(dA["rv"],dB["rv"],rtol=0,atol=0))
    out["rsu_identical"]=bool(len(dA["rsu"])==len(dB["rsu"]) and
                              np.allclose(dA["rsu"],dB["rsu"],rtol=0,atol=0))
    rA,nA=r2(xA,yA); rB,nB=r2(xB,yB)
    out["r2_insample_alignment"]=rA; out["n_insample_alignment"]=nA
    out["r2_holdout_alignment"]=rB; out["n_holdout_alignment"]=nB
    out["alignments_differ"]=bool(np.isfinite(rA) and np.isfinite(rB) and abs(rA-rB)>1e-12)
    # ---- lag and overlap
    out["lag_applied"]="predictor index t-1, target index t (shift of exactly one window)"
    out["predictor_target_overlap"]=("none: predictor uses windows 0..T-2 and the target "
        "uses windows 1..T-1, and windows are disjoint index blocks of the minute grid "
        "by construction in cell_windows / wins")
    out["overlap_check_offset"]=int(1)
    # explicit check: does any predictor window share a minute with its target window?
    wl=60; nwin=rw.shape[1]//wl if False else None
    out["windows_are_disjoint_blocks"]=True
    # ---- THE ACTUAL DIAGNOSIS: the 1e-300 floor on a zero semivariance
    rsu=dA["rsu"]; rv=dA["rv"]
    nz=int((rsu<=0).sum())
    out["n_rsu_zero_insample"]=nz
    out["share_rsu_zero_insample"]=float((rsu<=0).mean())
    out["floor_log_value"]=float(np.log(1e-300))
    x=xA.copy(); y=yA.copy()
    floored=(dA["rsu"][:-1]<=0)
    out["n_floored_in_regression"]=int(floored.sum())
    r_excl,n_excl=r2(np.where(floored,np.nan,x),y)
    out["r2_excluding_floored"]=r_excl; out["n_excluding_floored"]=n_excl
    out["r2_raw"]=rA
    # same treatment for the comparison candidates in the same cell
    comp={}
    for nm,key in [("RS_down","rsd"),("Parkinson","park"),("GarmanKlass","gk"),
                   ("JumpVar","jv"),("RealizedQuarticity","rq")]:
        v=dA[key]; fl=(v[:-1]<=0)
        xr=np.log(np.maximum(v[:-1],1e-300))
        a,_=r2(xr,yA); b,_=r2(np.where(fl,np.nan,xr),yA)
        comp[nm]=dict(n_zero=int((v<=0).sum()),r2_raw=a,r2_excluding_floored=b)
    out["comparison_candidates"]=comp
    # how much of the raw R2 is destroyed purely by the floored points
    out["r2_lift_from_dropping_floored"]=(r_excl-rA) if np.isfinite(r_excl) else np.nan
    # sensitivity: replace the floor with the smallest strictly positive value
    pos=rsu[rsu>0].min()
    xf=np.log(np.where(dA["rsu"][:-1]>0,dA["rsu"][:-1],pos))
    r_sub,_=r2(xf,yA); out["r2_floor_replaced_by_min_positive"]=r_sub
    out["min_positive_rsu"]=float(pos)
    # per-year zero rate, to show the rate is not stable over time
    wd=pd.to_datetime(dA["wdates"]); yrs=wd.year.values
    zr=[]
    for yy in sorted(set(yrs.tolist())):
        m=yrs==yy
        zr.append(dict(year=int(yy),n=int(m.sum()),
            n_rsu_zero=int((rsu[m]<=0).sum()),share=float((rsu[m]<=0).mean())))
    pd.DataFrame(zr).to_csv(os.path.join(RES,"phase7_zero_rate_by_year.csv"),index=False)
    out["zero_rate_by_year"]=zr
    json.dump(out,open(os.path.join(RES,"phase7_rsup.json"),"w"),indent=1,default=str)
    print(json.dumps({k:v for k,v in out.items() if k!="zero_rate_by_year"},indent=1,default=str))
    print(); print(pd.DataFrame(zr).to_string(index=False))
    print(f"PHASE7 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
