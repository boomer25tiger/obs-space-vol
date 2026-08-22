"""S13 Phase 3b: is the selected 2022 break a level shift or one anomalous year?

b reverts toward its pre-2022 level in 2023 in every cell, which a level shift
does not predict. Two direct checks: refit both specifications with 2022
excluded, and test a single-year 2022 dummy against the level shift.
"""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common13 import RES,CACHE,S10
NREP=9999; MASTER=20260834
def fe_rss(X,y,cid,ncl):
    yd=y-np.array([y[cid==g].mean() for g in range(ncl)])[cid]
    Xd=(X-np.vstack([X[cid==g].mean(axis=0) for g in range(ncl)])[cid]
        if X.shape[1] else X)
    if X.shape[1]==0: return float((yd*yd).sum()),np.zeros(0),yd
    beta,*_=np.linalg.lstsq(Xd,yd,rcond=None); r=yd-Xd@beta
    return float((r*r).sum()),beta,r
def main():
    t0=time.time()
    SUB=pd.read_csv(os.path.join(S10,"results","phase3_subfits.csv"))
    yr=SUB[(SUB.stratum=="year")&(~SUB.degenerate)].copy()
    yr["year"]=yr.key.astype(int)
    yr["distinct"]=yr.cell.str.replace("/B1/","/B0/",regex=False)
    d0=yr.drop_duplicates(subset=["distinct","year"]).copy()
    out={}
    # ---- reversion check: 2022 -> 2023 direction per cell
    rev=[]
    for c,g in d0.groupby("distinct"):
        g=g.set_index("year")
        rev.append(dict(cell=c,b_2021=float(g.b.get(2021,np.nan)),
            b_2022=float(g.b.get(2022,np.nan)),b_2023=float(g.b.get(2023,np.nan)),
            reverts_2023=bool(g.b.get(2023,np.nan)>g.b.get(2022,np.nan)),
            is_2022_min=bool(g.b.idxmin()==2022)))
    RV=pd.DataFrame(rev); RV.to_csv(os.path.join(RES,"phase3b_reversion.csv"),index=False)
    out["n_cells_2022_is_minimum"]=int(RV.is_2022_min.sum())
    out["n_cells_reverting_in_2023"]=int(RV.reverts_2023.sum())
    out["n_cells"]=int(len(RV))
    # ---- specifications, full sample and excluding 2022
    res={}
    for tag,d in [("full",d0),("excl_2022",d0[d0.year!=2022].copy())]:
        cats=sorted(d["distinct"].unique()); cm={c:i for i,c in enumerate(cats)}
        cid=d["distinct"].map(cm).values.astype(int); ncl=len(cats)
        y=d.b.values.astype(float); tv=d.year.values.astype(float)
        n=len(d)
        rss0,_,r0=fe_rss(np.zeros((n,0)),y,cid,ncl)
        rssl,bl,_=fe_rss(tv[:,None],y,cid,ncl)
        years=sorted(d.year.unique())
        adm=[yy for yy in years if years.index(yy)>=2 and years.index(yy)<=len(years)-2]
        best=(None,np.inf,None)
        for tau in adm:
            r_,bb,_=fe_rss((tv>=tau).astype(float)[:,None],y,cid,ncl)
            if r_<best[1]: best=(int(tau),r_,float(bb[0]))
        rssy=np.nan; by=np.nan
        if tag=="full":
            rssy,byy,_=fe_rss((tv==2022).astype(float)[:,None],y,cid,ncl)
            by=float(byy[0])
        Fl=((rss0-rssl)/1)/(rssl/(n-ncl-1))
        Fb=((rss0-best[1])/1)/(best[1]/(n-ncl-1))
        rng=np.random.Generator(np.random.PCG64(MASTER+(0 if tag=="full" else 1)))
        pl=fb=0
        supF=np.empty(NREP); linF=np.empty(NREP)
        for i in range(NREP):
            w=rng.choice(np.array([-1.0,1.0]),size=ncl)[cid]
            ys=y-r0+w*r0
            r0s,_,_=fe_rss(np.zeros((n,0)),ys,cid,ncl)
            rl,_,_=fe_rss(tv[:,None],ys,cid,ncl)
            linF[i]=((r0s-rl)/1)/(rl/(n-ncl-1))
            bb_=min(fe_rss((tv>=tau).astype(float)[:,None],ys,cid,ncl)[0] for tau in adm)
            supF[i]=((r0s-bb_)/1)/(bb_/(n-ncl-1))
        np.savez_compressed(os.path.join(CACHE,f"break_robust_{tag}.npz"),
            supF=supF,linF=linF,F_lin=Fl,F_break=Fb,seed=MASTER+(0 if tag=="full" else 1))
        res[tag]=dict(n_obs=n,years=[int(v) for v in years],admissible=[int(v) for v in adm],
            rss_intercept=rss0,rss_linear=rssl,rss_break=best[1],break_date=best[0],
            break_delta=best[2],linear_slope=float(bl[0]),
            F_linear=float(Fl),F_break_sup=float(Fb),
            p_linear=float((linF>=Fl).mean()),p_break_sup=float((supF>=Fb).mean()),
            rss_2022_dummy=(rssy if tag=="full" else None),
            delta_2022_dummy=(by if tag=="full" else None),
            share_residual_linear=float(1-rssl/rss0),
            share_residual_break=float(1-best[1]/rss0))
    out["specifications"]=res
    f=res["full"]
    out["dummy_2022_beats_break"]=bool(f["rss_2022_dummy"]<f["rss_break"])
    out["dummy_2022_beats_linear"]=bool(f["rss_2022_dummy"]<f["rss_linear"])
    e=res["excl_2022"]
    out["excl_2022_linear_survives_05"]=bool(e["p_linear"]<0.05)
    out["excl_2022_break_survives_05"]=bool(e["p_break_sup"]<0.05)
    out["rademacher_floor"]=float(2**-7)
    out["verdict"]=("INDETERMINATE" if (out["dummy_2022_beats_break"] or
        not (e["p_linear"]<0.05 or e["p_break_sup"]<0.05)) else
        ("LEVEL SHIFT at "+str(f["break_date"]) if f["rss_break"]<f["rss_linear"]
         else "CONTINUOUS"))
    json.dump(out,open(os.path.join(RES,"phase3b_robustness.json"),"w"),indent=1,default=str)
    pd.set_option("display.width",250)
    print(RV.to_string(index=False)); print()
    print(json.dumps(out,indent=1,default=str))
    print(f"PHASE3b DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
