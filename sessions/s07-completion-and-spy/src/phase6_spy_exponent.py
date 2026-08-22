"""S07 Phase 6: SPY exponent under both sampling conventions."""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy.optimize import curve_fit
from scipy.special import polygamma
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
sys.path.insert(0,os.path.join(ROOT,"sessions","s06r-repair","tests"))
from test_invariants import assert_effective_M
NSEC=23400
GRID=[5,6,10,13,26,39,78,130,195,390,780,1560,2340,4680,11700,23400]
def trig(M): return polygamma(1,np.asarray(M,float)/2.0)
def fitf(M,y):
    M=np.asarray(M,float); y=np.asarray(y,float); ok=np.isfinite(y)
    if ok.sum()<4: return dict(c=np.nan,A=np.nan,b=np.nan,rmse=np.nan,n=int(ok.sum()))
    try:
        p,_=curve_fit(lambda x,c,A,b: c+A*np.power(x,b),M[ok],y[ok],
                      p0=[y[ok].min(),1.0,-0.5],maxfev=80000)
        pred=p[0]+p[1]*np.power(M[ok],p[2])
        return dict(c=float(p[0]),A=float(p[1]),b=float(p[2]),
                    rmse=float(np.sqrt(np.mean((y[ok]-pred)**2))),n=int(ok.sum()))
    except Exception: return dict(c=np.nan,A=np.nan,b=np.nan,rmse=np.nan,n=int(ok.sum()))
def subbars_cal(r,k,M):
    N,L=r.shape; e=(np.arange(M+1)*L)//M
    cs=np.concatenate([np.zeros((N,1)),np.cumsum(r,axis=1)],axis=1)
    sb=cs[:,e[1:]]-cs[:,e[:-1]]
    kc=np.concatenate([np.zeros((N,1)),np.cumsum(k.astype(np.int32),axis=1)],axis=1)
    kb=kc[:,e[1:]]-kc[:,e[:-1]]
    return sb,(kb>0).sum(axis=1).astype(float)
def trv3(sb,M):
    a=np.abs(sb); Mo=max(M,3)
    bv=(np.pi/2)*(Mo/max(Mo-1,1))*(a[:,1:]*a[:,:-1]).sum(axis=1)
    u=3*np.sqrt(np.maximum(bv,1e-300)/Mo)
    return (np.where(a<=u[:,None],sb,0.0)**2).sum(axis=1)
def main():
    t0=time.time(); rows=[]; noise=[]; fits=[]; strat=[]
    for ven in ["ARCX","XNAS"]:
        fc=os.path.join(CACHE,f"spy_cal_{ven}.npz")
        if not os.path.exists(fc): print("missing",ven,flush=True); continue
        z=np.load(fc); cl=z["close"].astype(np.float64); pres=z["present"]
        dts=pd.to_datetime(np.array(z["dates"],dtype="U10")); yrs=dts.year.values
        r1=np.diff(cl,axis=1); keep=pres[:,1:]&pres[:,:-1]
        rcal=np.where(keep,r1,0.0)
        zt=np.load(os.path.join(CACHE,f"spy_tick_{ven}.npz"))
        trow,tpx,tcnt=zt["row"],zt["logpx"].astype(np.float64),zt["counts"]
        starts=np.concatenate([[0],np.cumsum(tcnt)])
        S=cl.shape[0]
        volcoarse=None
        for M in GRID:
            Meff_nominal=M
            if M>=r1.shape[1]: M_use=r1.shape[1]; stub=True
            else: M_use=M; stub=False
            sb,meff=subbars_cal(rcal,keep,M_use)
            assert_effective_M(meff,meff,f"SPY/{ven}/CAL/M{M}")
            rv=(sb**2).sum(axis=1); pos=rv>0
            vlog=float(np.log(rv[pos]).var())
            tr=trv3(sb,M_use); trshare=float(1-np.mean(tr[pos]/np.maximum(rv[pos],1e-300)))
            vlog_trv=float(np.log(np.maximum(tr[pos],1e-300)).var())
            if volcoarse is None: volcoarse=np.sqrt(np.maximum(rv,0))
            # ---- traded-tick: equal-count blocks of the traded sequence
            rv_t=np.full(S,np.nan)
            for i in range(S):
                a,b=starts[i],starts[i+1]
                n=b-a
                if n<M_use+1: continue
                px=tpx[a:b]; e=(np.arange(M_use+1)*(n-1))//M_use
                d=np.diff(px[e]); rv_t[i]=float((d*d).sum())
            post=np.isfinite(rv_t)&(rv_t>0)
            vlog_t=float(np.log(rv_t[post]).var()) if post.sum()>30 else np.nan
            rows.append(dict(venue=ven,M=M,M_used=M_use,stub=stub,
                n_windows=int(pos.sum()),var_log_rv_CAL=vlog,
                var_log_rv_TICK=vlog_t,n_tick=int(post.sum()),
                var_log_trv3_CAL=vlog_trv,trv3_share_removed=trshare,
                mean_eff_M=float(meff.mean()),share_full_M=float((meff==M_use).mean()),
                mean_rv=float(rv[pos].mean()),trigamma=float(trig(M_use))))
            for y in sorted(set(yrs.tolist())):
                m=(yrs==y)&pos
                if m.sum()>30:
                    strat.append(dict(venue=ven,M=M,stratum="year",key=str(y),
                        var_log_rv=float(np.log(rv[m]).var()),n=int(m.sum())))
            q=np.quantile(volcoarse[pos],[1/3,2/3]); tc=np.searchsorted(q,volcoarse)
            for k in [0,1,2]:
                m=pos&(tc==k)
                if m.sum()>30:
                    strat.append(dict(venue=ven,M=M,stratum="vol_tercile",key=str(k+1),
                        var_log_rv=float(np.log(rv[m]).var()),n=int(m.sum())))
        D=pd.DataFrame([r for r in rows if r["venue"]==ven])
        # ---- noise: signature plot per venue and per year
        for lab,mask in [("all",np.ones(S,bool))]+[(str(y),yrs==y) for y in sorted(set(yrs.tolist()))]:
            mr=[]
            for M in GRID:
                Mu=min(M,r1.shape[1])
                sb,_=subbars_cal(rcal[mask],keep[mask],Mu)
                mr.append(float((sb**2).sum(axis=1).mean()))
            Ms=np.array([min(M,r1.shape[1]) for M in GRID],float)
            slope,inter=np.polyfit(Ms,np.array(mr),1)
            om2=slope/2.0
            noise.append(dict(venue=ven,group=lab,omega2=float(om2),iv_intercept=float(inter),
                nsr=float(om2/inter) if inter>0 else np.nan))
        om2=float([n for n in noise if n["venue"]==ven and n["group"]=="all"][0]["omega2"])
        iv0=float([n for n in noise if n["venue"]==ven and n["group"]=="all"][0]["iv_intercept"])
        D["implied_bias"]=2*D.M_used*om2/max(iv0,1e-300)
        D["bias_below_1pct"]=D.implied_bias<0.01
        D["var_log_rv_CAL_noisecorr"]=D.var_log_rv_CAL-np.log1p(D.implied_bias)**2
        D.to_csv(os.path.join(RES,f"phase6_spy_grid_{ven}.csv"),index=False)
        prim=D[D.bias_below_1pct]
        for tag,sub,col in [("CAL_full",D,"var_log_rv_CAL"),("CAL_primary",prim,"var_log_rv_CAL"),
                            ("TICK_full",D,"var_log_rv_TICK"),("TICK_primary",prim,"var_log_rv_TICK"),
                            ("CAL_noisecorr_full",D,"var_log_rv_CAL_noisecorr"),
                            ("TRV3_full",D,"var_log_trv3_CAL")]:
            f=fitf(sub.M_used.values,sub[col].values)
            fits.append(dict(venue=ven,fit=tag,**f,
                M_min=float(sub.M_used.min()) if len(sub) else np.nan,
                M_max=float(sub.M_used.max()) if len(sub) else np.nan))
        ft=fitf(D.M_used.values,trig(D.M_used.values))
        fits.append(dict(venue=ven,fit="trigamma_reference",**ft,
            M_min=float(D.M_used.min()),M_max=float(D.M_used.max())))
        ftp=fitf(prim.M_used.values,trig(prim.M_used.values)) if len(prim)>=4 else dict(c=np.nan,A=np.nan,b=np.nan,rmse=np.nan,n=0)
        fits.append(dict(venue=ven,fit="trigamma_reference_primary",**ftp,
            M_min=float(prim.M_used.min()) if len(prim) else np.nan,
            M_max=float(prim.M_used.max()) if len(prim) else np.nan))
        print(ven,"done",f"{time.time()-t0:.0f}s",flush=True)
    pd.DataFrame(noise).to_csv(os.path.join(RES,"phase6_spy_noise.csv"),index=False)
    F=pd.DataFrame(fits); F.to_csv(os.path.join(RES,"phase6_spy_fits.csv"),index=False)
    ST=pd.DataFrame(strat)
    sf=[]
    for (ven,st,key),g in ST.groupby(["venue","stratum","key"]):
        f=fitf(g.M.values,g.var_log_rv.values)
        sf.append(dict(venue=ven,stratum=st,key=key,**f))
    pd.DataFrame(sf).to_csv(os.path.join(RES,"phase6_spy_strat_fits.csv"),index=False)
    ST.to_csv(os.path.join(RES,"phase6_spy_strat_raw.csv"),index=False)
    print(F.to_string(index=False))
    print(f"PHASE6 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
