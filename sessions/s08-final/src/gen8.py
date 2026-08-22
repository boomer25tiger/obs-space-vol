"""S08 Phase 1: regeneration under the revised item-60 filter.

Filter: LOWER BOUND ONLY, applied identically to ALL SEVEN models. A forecast
that is non-positive or at or below the 1e-300 floor is replaced by the
smallest strictly positive in-sample realized variance. No upper bound.
Exclusion set is S07's (calendar + presence-based exchange halts).
"""
import json, os, sys, time
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
S07=os.path.join(ROOT,"sessions","s07-completion-and-spy")
S06=os.path.join(ROOT,"sessions","s06r-repair")
sys.path.insert(0,os.path.join(S06,"tests"))
sys.path.insert(0,os.path.join(S07,"src"))
sys.path.insert(0,os.path.join(ROOT,"sessions","s05-reliability-mcs","src"))
from test_invariants import assert_forecasts_positive, InvariantViolation
import partde as pd5
from phase2_rerun8 import series, HOR
MODELS=pd5.MODELS; FLOOR=1e-300
CELLS=[(r,g,b,h) for g in ["GLOBEX","RTH"] for r in ["ES","NQ"]
       for b in ["B0","B1"] for h in ["1day","1h","30min"]]
def run_cell(job):
    root,geom,btag,hname=job; cell=f"{root}/{geom}/{btag}/{hname}"; t0=time.time()
    S=series(root,geom,btag,HOR[hname]); D=S["nw"]; rv=S["rv"]
    warm=500 if hname=="1day" else max(500,22*D+100); refit=1 if hname=="1day" else D
    F,start,nonconv=pd5.forecasts(S,D,warm,refit,hname=="1day")
    ok=np.ones(len(rv),bool)
    for m in MODELS: ok&=np.isfinite(F[m])
    ok[:max(start,warm)]=False; ok&=S["tradeable"]
    rvv=rv[ok]; ins=rv[:max(start,warm)]; posi=ins[ins>0]
    lower=float(posi.min()) if len(posi) else 1e-12
    filt=[]; Ff={}; repmask={}
    for m in MODELS:
        x=F[m][ok].copy()
        bad=(x<=FLOOR)|(x<=0)|~np.isfinite(x)          # item 60: lower bound only
        xf=np.where(bad,lower,x)
        Ff[m]=xf; repmask[m]=bad
        ql=pd5.qlike(xf,rvv); tot=float(np.nansum(ql[np.isfinite(ql)]))
        filt.append(dict(cell=cell,model=m,n_eval=int(ok.sum()),
            n_replaced=int(bad.sum()),share_replaced=float(bad.mean()),
            replacement_value=lower,mean_qlike=float(np.nanmean(ql)),
            share_qlike_from_replaced=float(ql[bad].sum()/tot) if tot>0 and bad.any() else 0.0,
            share_qlike_worst5=float(np.sort(ql[np.isfinite(ql)])[-5:].sum()/tot) if tot>0 else np.nan,
            flag_replaced_over_quarter=bool((ql[bad].sum()/tot if tot>0 and bad.any() else 0.0)>0.25),
            ic=float(np.corrcoef(np.log(xf),np.log(rvv))[0,1])))
        assert_forecasts_positive(xf,cell,m)
    L=np.column_stack([pd5.qlike(Ff[m],rvv) for m in MODELS])
    np.savez_compressed(os.path.join(CACHE,f"gen_{root}_{geom}_{btag}_{hname}.npz"),
        rv=rv,ok=ok,L=L,rvv=rvv,Meff=S["Meff"],wdates=S["wdates"],
        tradeable=S["tradeable"],D=D,start=start,warm=warm,nonconv=nonconv,
        ret=S["ret"],models=np.array(MODELS),lower_bound=lower,
        **{f"F_{m}":Ff[m] for m in MODELS},
        **{f"REP_{m}":repmask[m] for m in MODELS})
    return dict(cell=cell,n_eval=int(ok.sum()),lower_bound=lower,
                seconds=round(time.time()-t0,1)),filt
def main():
    t0=time.time(); meta=[];filt=[];halts=[]
    todo=[c for c in CELLS if not os.path.exists(
        os.path.join(CACHE,f"gen_{c[0]}_{c[1]}_{c[2]}_{c[3]}.npz"))]
    print(f"regenerating {len(todo)} cells under the revised filter",flush=True)
    with ProcessPoolExecutor(max_workers=6) as ex:
        futs={ex.submit(run_cell,c):c for c in todo}
        for f in as_completed(futs):
            try: m,fr=f.result()
            except InvariantViolation as e:
                halts.append(dict(cell="/".join(futs[f]),message=str(e)))
                print("HALT:",e,flush=True); continue
            meta.append(m); filt.extend(fr)
            print(f"  {len(meta)}/{len(todo)} {m['cell']} ({m['seconds']}s)",flush=True)
    pd.DataFrame(meta).to_csv(os.path.join(RES,"phase1_gen_meta.csv"),index=False)
    pd.DataFrame(filt).to_csv(os.path.join(RES,"phase1_filter.csv"),index=False)
    pd.DataFrame(halts).to_csv(os.path.join(RES,"phase1_halts.csv"),index=False)
    print(f"GEN DONE {time.time()-t0:.0f}s",flush=True)
if __name__=="__main__": main()
