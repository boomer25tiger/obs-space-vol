"""S10 Phase 3: how much of the pooled-to-reference gap is a pooling artifact."""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import (BASE,RES,CELLS,GRID_EXT,trig,fitf,fit_diag,screen_old,screen_tight,
                    cell_windows,logrv_matrix,var_cols,subbars,NPAR)
CACHE=os.path.join(BASE,"cache")
MINWIN=60          # a sub-fit needs enough windows for a variance to mean anything
def subfit(name,stratum,key,Ms,L,rows):
    n=int(np.isfinite(L).all(axis=1).sum())
    if L.shape[0]<MINWIN:
        rows.append(dict(cell=name,stratum=stratum,key=key,n_windows=int(L.shape[0]),
            n_grid=len(Ms),b=np.nan,c=np.nan,A=np.nan,rmse=np.nan,cond=np.nan,
            degenerate=True,reason=f"n_windows {L.shape[0]} < {MINWIN}")); return None
    y=var_cols(L); f=fitf(Ms,y); d=fit_diag(Ms,y,f)
    # A sub-fit counts only if it passes the S08 screen AND the S10 tightened
    # criteria: |b| > 0.01 (the flat-power pathology) and a condition number
    # below 1e8 (c and A M^b separately identified).
    why=[]
    if f is None: why.append("no fit")
    else:
        if f["A"]<=0: why.append(f"A={f['A']:.3g} <= 0")
        if f["b"]>=0: why.append(f"b={f['b']:.3g} >= 0")
        if abs(f["b"])<=0.01: why.append(f"|b|={abs(f['b']):.3g} <= 0.01")
        if not np.isfinite(d["cond"]) or d["cond"]>1e8: why.append(f"cond={d['cond']:.3g} > 1e8")
    deg=bool(why)
    rows.append(dict(cell=name,stratum=stratum,key=key,n_windows=int(L.shape[0]),
        n_grid=len(Ms),b=f["b"] if f else np.nan,c=f["c"] if f else np.nan,
        A=f["A"] if f else np.nan,rmse=f["rmse"] if f else np.nan,cond=d["cond"],
        degenerate=deg,reason="; ".join(why)))
    return None if deg else f["b"]
def main():
    t0=time.time(); rows=[]; summ=[]
    for root,geom,btag,hname in CELLS:
        name=f"{root}/{geom}/{btag}/{hname}"
        rw,kw,ds=cell_windows(root,geom,hname)
        Ms=[m for m in GRID_EXT[(geom,hname)] if m<=rw.shape[1]]
        L,Ms=logrv_matrix(rw,Ms)
        yrs=pd.to_datetime(ds).year.values
        b_pool=subfit(name,"pooled","all",Ms,L,rows)
        b_ref=fitf(Ms,trig(Ms))["b"]
        # volatility tercile on the coarsest grid point, the S07 convention
        rvc=(subbars(rw,Ms[0])**2).sum(axis=1)
        vc=np.sqrt(np.maximum(rvc,0.0))
        q=np.quantile(vc[vc>0],[1/3,2/3]); tc=np.searchsorted(q,vc)
        by=[];  bt=[]
        for y in sorted(set(yrs.tolist())):
            v=subfit(name,"year",str(y),Ms,L[yrs==y],rows)
            if v is not None: by.append(v)
        for k in [0,1,2]:
            v=subfit(name,"vol_tercile",str(k+1),Ms,L[tc==k],rows)
            if v is not None: bt.append(v)
        by=np.array(by); bt=np.array(bt)
        gap=b_pool-b_ref if b_pool is not None else np.nan     # positive: pooled flatter
        shy=(b_pool-by.mean())/gap if (len(by) and np.isfinite(gap) and gap!=0) else np.nan
        sht=(b_pool-bt.mean())/gap if (len(bt) and np.isfinite(gap) and gap!=0) else np.nan
        summ.append(dict(cell=name,b_pooled=b_pool,b_ref=b_ref,gap_pooled_to_ref=gap,
            n_years=len(by),b_year_mean=float(by.mean()) if len(by) else np.nan,
            b_year_sd=float(by.std(ddof=1)) if len(by)>1 else np.nan,
            b_year_min=float(by.min()) if len(by) else np.nan,
            b_year_max=float(by.max()) if len(by) else np.nan,
            year_steeper_than_pooled=int((by<b_pool).sum()) if len(by) else 0,
            share_gap_from_year_pooling=shy,
            n_terciles=len(bt),b_tercile_mean=float(bt.mean()) if len(bt) else np.nan,
            b_tercile_sd=float(bt.std(ddof=1)) if len(bt)>1 else np.nan,
            tercile_steeper_than_pooled=int((bt<b_pool).sum()) if len(bt) else 0,
            share_gap_from_tercile_pooling=sht))
        print(f"  {name:26s} pooled={b_pool:+.4f} year_mean={summ[-1]['b_year_mean']:+.4f}"
              f" (sd {summ[-1]['b_year_sd']:.3f}, {summ[-1]['year_steeper_than_pooled']}/{len(by)} steeper)"
              f" ref={b_ref:+.4f} share={shy:+.3f}",flush=True)
    R=pd.DataFrame(rows); R.to_csv(os.path.join(RES,"phase3_subfits.csv"),index=False)
    S=pd.DataFrame(summ); S.to_csv(os.path.join(RES,"phase3_pooling.csv"),index=False)
    o=dict(n_cells=len(S),
        n_degenerate_subfits=int(R.degenerate.sum()),n_subfits=len(R),
        cells_year_steeper_all=int((S.year_steeper_than_pooled==S.n_years).sum()),
        mean_year_minus_pooled=float((S.b_year_mean-S.b_pooled).mean()),
        mean_tercile_minus_pooled=float((S.b_tercile_mean-S.b_pooled).mean()),
        share_year_mean=float(S.share_gap_from_year_pooling.mean()),
        share_year_median=float(S.share_gap_from_year_pooling.median()),
        share_year_min=float(S.share_gap_from_year_pooling.min()),
        share_year_max=float(S.share_gap_from_year_pooling.max()),
        n_tercile_subfits_usable=int((~R[R.stratum=="vol_tercile"].degenerate).sum()),
        n_tercile_subfits=int((R.stratum=="vol_tercile").sum()),
        share_tercile_mean=(float(S.share_gap_from_tercile_pooling.mean())
                            if S.n_terciles.sum() else None),
        residual_gap_mean=float((S.b_year_mean-S.b_ref).mean()),
        timers=dict(phase3=round(time.time()-t0,1)))
    json.dump(o,open(os.path.join(RES,"phase3_summary.json"),"w"),indent=1)
    print(); print(json.dumps(o,indent=1))
    print(f"PHASE3 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
