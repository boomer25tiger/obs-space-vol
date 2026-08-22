"""S10 Phase 7b: how far the floor-substitution defect reaches across the S09
signal set. Pre-2024 panel only."""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import BASE,RES,ROOT,CELLS
sys.path.insert(0,os.path.join(ROOT,"sessions","s09-application","src"))
import phase5_signals as p5
FIVEMIN={("RTH","1day"):78,("RTH","1h"):12,("RTH","30min"):6,("GLOBEX","1day"):276}
THRESH=0.02
KEYS=[("RS_up","rsu"),("RS_down","rsd"),("JumpVar","jv"),("Parkinson","park"),
      ("GarmanKlass","gk"),("RealizedQuarticity","rq")]
def r2(x,y):
    ok=np.isfinite(x)&np.isfinite(y)
    return (float(np.corrcoef(x[ok],y[ok])[0,1]**2),int(ok.sum())) if ok.sum()>50 else (np.nan,0)
def main():
    t0=time.time(); rows=[]
    P3=pd.read_csv(os.path.join(ROOT,"sessions","s09-application","results",
                                "phase3_sizing_params.csv"))
    for root,geom,btag,hname in CELLS:
        d=p5.build(root,geom,btag,hname)
        y=np.log(np.maximum(d["rv"][1:],1e-300))
        sub=P3[(P3.root==root)&(P3.geom==geom)&(P3.btag==btag)&(P3.horizon==hname)&
               (P3.range=="extended")]
        lam=float(sub.iloc[0].lam_intercept) if len(sub) else np.nan
        for nm,key in KEYS:
            v=d[key][:-1]; fl=v<=0
            xf=np.log(np.maximum(v,1e-300))
            a,n=r2(xf,y)
            pos=d[key][d[key]>0]
            xr=np.log(np.where(v>0,v,pos.min() if len(pos) else 1e-300))
            b,_=r2(xr,y)
            rows.append(dict(cell=f"{root}/{geom}/{btag}/{hname}",candidate=nm,
                n=n,n_zero=int(fl.sum()),share_zero=float(fl.mean()),
                r2_floored=a,r2_repaired=b,lift=b-a,lam_intercept=lam,
                keep_floored=bool(a>=THRESH),keep_repaired=bool(b>=THRESH),
                keep_floored_corr=bool(a/lam>=THRESH) if np.isfinite(lam) else None,
                keep_repaired_corr=bool(b/lam>=THRESH) if np.isfinite(lam) else None,
                status_changes=bool((a>=THRESH)!=(b>=THRESH))))
    R=pd.DataFrame(rows); R.to_csv(os.path.join(RES,"phase7b_floor_audit.csv"),index=False)
    aff=R[R.n_zero>0]
    o=dict(n_rows=len(R),n_affected=int((R.n_zero>0).sum()),
        affected_candidates=sorted(aff.candidate.unique().tolist()),
        n_status_changes=int(R.status_changes.sum()),
        max_lift=float(R.lift.max()),median_lift_affected=float(aff.lift.median()),
        n_cells_rsup_zero=int(((R.candidate=="RS_up")&(R.n_zero>0)).sum()),
        n_cells_rsdown_zero=int(((R.candidate=="RS_down")&(R.n_zero>0)).sum()),
        n_cells_jumpvar_zero=int(((R.candidate=="JumpVar")&(R.n_zero>0)).sum()),
        unaffected_candidates=sorted(R[R.n_zero==0].candidate.unique().tolist()),
        timers=dict(phase7b=round(time.time()-t0,1)))
    json.dump(o,open(os.path.join(RES,"phase7b_summary.json"),"w"),indent=1)
    print(R[R.status_changes][["cell","candidate","n_zero","share_zero","r2_floored",
                               "r2_repaired","lift"]].to_string(index=False))
    print(); print(json.dumps(o,indent=1))
    print(f"PHASE7b DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
