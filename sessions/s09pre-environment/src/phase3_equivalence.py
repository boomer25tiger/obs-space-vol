"""S09-PRE Phase 3: equivalence verification of the rebuilt environment.

Recomputes the ES/GLOBEX/B0/1day intercept fit and the Var(log RV_M) grid
from persisted artifacts, and re-runs the five invariants against the
pre-repair S05 artifacts. Writes ONLY under sessions/s09pre-environment/.
"""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy.optimize import curve_fit
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES=os.path.join(BASE,"results")
S06=os.path.join(ROOT,"sessions","s06r-repair")
S07=os.path.join(ROOT,"sessions","s07-completion-and-spy")
S08=os.path.join(ROOT,"sessions","s08-final")
S05R=os.path.join(ROOT,"sessions","s05-reliability-mcs","results")
S05A=os.path.join(ROOT,"sessions","s05a-reproducibility","results","cache")
S05B=os.path.join(ROOT,"sessions","s05b-defect-and-estimator-audit","results")
sys.path.insert(0,os.path.join(S06,"tests")); sys.path.insert(0,os.path.join(S07,"src"))
sys.path.insert(0,os.path.join(ROOT,"sessions","s05-reliability-mcs","src"))
from test_invariants import (InvariantViolation, assert_forecasts_positive,
    assert_loss_finite, assert_lambda_in_unit, assert_range_inputs, assert_effective_M)
from parta import quart_suite
from phase2_rerun8 import series, tradeable_ext
MODELS=["M1_EWMA","M2_HAR","M3_HARJ","M4_HARQ","M5_RGARCH","M6_PARK","M6_GK"]
GRID_G1D=[5,6,10,12,23,46,138,276,345,1379]
STORED=dict(c=1.033910,A=2.058452,b=-0.442672,rmse=0.049894)
def subbars_masked(rw,kw,M):
    N,L=rw.shape; e=(np.arange(M+1)*L)//M
    cs=np.concatenate([np.zeros((N,1)),np.cumsum(rw,axis=1)],axis=1)
    sb=cs[:,e[1:]]-cs[:,e[:-1]]
    kc=np.concatenate([np.zeros((N,1)),np.cumsum(kw.astype(np.int32),axis=1)],axis=1)
    kb=kc[:,e[1:]]-kc[:,e[:-1]]
    return sb,(kb>0).sum(axis=1).astype(float)
def fitf(M,y):
    M=np.asarray(M,float); y=np.asarray(y,float); ok=np.isfinite(y)
    p,_=curve_fit(lambda x,c,A,b: c+A*np.power(x,b),M[ok],y[ok],
                  p0=[y[ok].min(),1.0,-0.5],maxfev=80000)
    pred=p[0]+p[1]*np.power(M[ok],p[2])
    return dict(c=float(p[0]),A=float(p[1]),b=float(p[2]),
                rmse=float(np.sqrt(np.mean((y[ok]-pred)**2))))
def main():
    t0=time.time(); out={}
    root,geom,btag,hname="ES","GLOBEX","B0","1day"
    z=np.load(os.path.join(S06,"cache",f"panel_ohlc_{root}_{geom}.npz"))
    cl=z["close"].astype(np.float64); pres=z["present"]
    trm,_=tradeable_ext(root,geom)
    r1=np.diff(cl,axis=1); keep=trm[:,1:]&trm[:,:-1]&pres[:,1:]&pres[:,:-1]
    r1=np.where(trm[:,1:]&trm[:,:-1],r1,0.0)
    rw,kw=r1,keep
    live=kw.any(axis=1); rw,kw=rw[live],kw[live]
    Ms,varlogs=[],[]
    for M in GRID_G1D:
        if M>rw.shape[1]: continue
        sb,meff=subbars_masked(rw,kw,M)
        q=quart_suite(sb,M); rq,rv=q["RQ_RV"]; pos=rv>0
        varlogs.append(float(np.log(rv[pos]).var())); Ms.append(M)
    f=fitf(Ms,varlogs)
    rows=[]
    for k in ["c","A","b","rmse"]:
        new,old=f[k],STORED[k]
        rows.append(dict(quantity=k,recomputed=new,stored=old,
            abs_dev=abs(new-old),rel_dev=abs(new-old)/abs(old) if old else np.nan))
    FIT=pd.DataFrame(rows); FIT.to_csv(os.path.join(RES,"phase3_intercept_fit.csv"),index=False)
    out["fit"]={r["quantity"]:dict(recomputed=r["recomputed"],stored=r["stored"],
        abs_dev=r["abs_dev"],rel_dev=r["rel_dev"]) for _,r in FIT.iterrows()}
    # ---- Var(log RV_M) at every grid point vs stored S08 lambda file
    L8=pd.read_csv(os.path.join(S08,"results","phase4_lambda.csv"))
    s=L8[(L8.root==root)&(L8.geom==geom)&(L8.btag==btag)&(L8.horizon==hname)]
    cmp_=[]
    for M,v in zip(Ms,varlogs):
        st=s[s.M==M]
        sv=float(st.var_log_rv.iloc[0]) if len(st) else np.nan
        cmp_.append(dict(M=M,recomputed=v,stored=sv,abs_dev=abs(v-sv) if sv==sv else np.nan))
    VC=pd.DataFrame(cmp_); VC.to_csv(os.path.join(RES,"phase3_varlog_grid.csv"),index=False)
    out["varlog_max_abs_dev"]=float(np.nanmax(VC.abs_dev.values))
    # ---- invariants against pre-repair S05 artifacts
    inv=[]
    for f_ in sorted(os.listdir(os.path.join(S05B,"cache"))):
        if not f_.startswith("fc_"): continue
        cell=f_[3:-4]; zz=np.load(os.path.join(S05B,"cache",f_)); ok=zz["ok"]
        for m in MODELS:
            try: assert_forecasts_positive(zz[f"F_{m}"][ok],cell,m); inv.append(("assert_forecasts_positive","PASS"))
            except InvariantViolation: inv.append(("assert_forecasts_positive","FAIL"))
    for f_ in sorted(os.listdir(S05A)):
        if not f_.startswith("loss_"): continue
        cell=f_[5:-4]; zz=np.load(os.path.join(S05A,f_)); Lm=zz["L"]
        for k in [k for k in zz.files if k.startswith("mask_")]:
            try: assert_loss_finite(Lm[zz[k]],f"{cell}/{k[5:]}",MODELS); inv.append(("assert_loss_finite","PASS"))
            except InvariantViolation: inv.append(("assert_loss_finite","FAIL"))
    C=pd.read_csv(os.path.join(S05R,"s05_partc.csv")); nlam=0
    for _,rr in C.iterrows():
        try: assert_lambda_in_unit(rr["lam"],"x",rr["estimator"])
        except InvariantViolation: nlam+=1
    for f_ in sorted(os.listdir(S05R)):
        if not f_.startswith("panel_"): continue
        zz=np.load(os.path.join(S05R,f_))
        try: assert_range_inputs({k:zz[k] for k in zz.files},f_[:-4]); inv.append(("assert_range_inputs","PASS"))
        except InvariantViolation: inv.append(("assert_range_inputs","FAIL"))
    G=pd.read_csv(os.path.join(S05B,"phase4_grid_index.csv")); nem=0; nemp=0
    for _,rr in G.iterrows():
        if rr.share_full_M>=1.0: nemp+=1
        else: nem+=1
    d=pd.DataFrame(inv,columns=["test","result"]).groupby(["test","result"]).size().unstack(fill_value=0)
    S06_REF={"assert_forecasts_positive":(46,122),"assert_loss_finite":(35,85),
             "assert_lambda_in_unit":(3683,len(C)),"assert_range_inputs":(8,0),
             "assert_effective_M":(88,36)}
    irows=[]
    for t,(f6,p6) in S06_REF.items():
        if t=="assert_lambda_in_unit": fnew,pnew=nlam,len(C)
        elif t=="assert_effective_M": fnew,pnew=nem,nemp
        else:
            fnew=int(d.loc[t,"FAIL"]) if t in d.index and "FAIL" in d.columns else 0
            pnew=int(d.loc[t,"PASS"]) if t in d.index and "PASS" in d.columns else 0
        irows.append(dict(test=t,fail_S06R=f6,fail_now=fnew,pass_S06R=p6,pass_now=pnew,
                          fires_now=bool(fnew>0),matches_S06R=bool(fnew==f6)))
    IV=pd.DataFrame(irows); IV.to_csv(os.path.join(RES,"phase3_invariants.csv"),index=False)
    out["invariants_all_fire"]=bool(IV.fires_now.all())
    out["invariants_all_match"]=bool(IV.matches_S06R.all())
    out["seconds"]=round(time.time()-t0,1)
    json.dump(out,open(os.path.join(RES,"phase3_summary.json"),"w"),indent=1,default=str)
    print(FIT.to_string(index=False)); print()
    print("max abs dev Var(log RV_M):",out["varlog_max_abs_dev"]); print()
    print(IV.to_string(index=False))
if __name__=="__main__": main()
