"""S09 Phase 5: signal status on the item-70 candidate set, pre-holdout only.

Nothing here reads data dated on or after 2024-01-01: the panels are the S06R
repaired panels, which end 2023-12-31, and the volume series is read from the
S04 bars parquet, which is likewise pre-2024.
"""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy.special import polygamma
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
S06=os.path.join(ROOT,"sessions","s06r-repair")
S04=os.path.join(ROOT,"sessions","s04-repairs-diagnostics","results")
sys.path.insert(0,os.path.join(ROOT,"sessions","s07-completion-and-spy","src"))
sys.path.insert(0,os.path.join(ROOT,"sessions","s05-reliability-mcs","src"))
from phase2_rerun8 import tradeable_ext, BOUNDARY, OFF
HOR={"1day":None,"1h":60,"30min":30}
GRID_SIG={"1day":[13,26,78,195],"1h":[6,10,15,30],"30min":[5,6,10,15]}
FIVEMIN={("RTH","1day"):78,("RTH","1h"):12,("RTH","30min"):6,("GLOBEX","1day"):276}
THRESH=0.02
CANDS=["RS_up","RS_down","JumpVar","Parkinson","GarmanKlass","VolumeSurprise",
       "CrossLeadLag","RealizedQuarticity","SignatureSlope"]
def trig(M): return float(polygamma(1,M/2.0))
def subbars(rw,M):
    N,L=rw.shape; e=(np.arange(M+1)*L)//M
    cs=np.concatenate([np.zeros((N,1)),np.cumsum(rw,axis=1)],axis=1)
    return cs[:,e[1:]]-cs[:,e[:-1]]
def build(root,geom,btag,hname):
    z=np.load(os.path.join(S06,"cache",f"panel_ohlc_{root}_{geom}.npz"))
    cl=z["close"].astype(np.float64); hi=z["high"].astype(np.float64)
    lo=z["low"].astype(np.float64); op=z["open"].astype(np.float64)
    pres=z["present"]; ds=np.array(z["dates"],dtype="U10")
    trm,_=tradeable_ext(root,geom)
    r1=np.diff(cl,axis=1)
    if btag=="B1":
        for m in BOUNDARY[geom]:
            sl=(m-OFF[geom])%1440 if geom=="GLOBEX" else m-OFF[geom]
            if 0<sl<=r1.shape[1]: r1[:,sl-1]=0.0
    r1=np.where(trm[:,1:]&trm[:,:-1],r1,0.0)
    keep=trm[:,1:]&trm[:,:-1]&pres[:,1:]&pres[:,:-1]
    wl=HOR[hname]
    if wl is None:
        rw,kw=r1,keep; nw=1
        HIw,LOw,OPw,CLw=hi,lo,op,cl
    else:
        nw=r1.shape[1]//wl
        rw=r1[:,:nw*wl].reshape(-1,wl); kw=keep[:,:nw*wl].reshape(-1,wl)
        HIw=hi[:,1:1+nw*wl].reshape(-1,wl); LOw=lo[:,1:1+nw*wl].reshape(-1,wl)
        OPw=op[:,1:1+nw*wl].reshape(-1,wl); CLw=cl[:,1:1+nw*wl].reshape(-1,wl)
    live=kw.any(axis=1)
    kmask=kw if wl else np.ones_like(HIw,bool)   # 1day: full-width price grid (series())
    M5=FIVEMIN[(geom,hname)]
    sb=subbars(rw,M5)
    rv=(sb**2).sum(axis=1)
    a=np.abs(sb); Mo=max(M5,3)
    bv=(np.pi/2)*(Mo/max(Mo-1,1))*(a[:,1:]*a[:,:-1]).sum(axis=1)
    rq=(Mo/3.0)*((sb**2)**2).sum(axis=1)
    rsu=(np.where(sb>0,sb,0.0)**2).sum(axis=1)
    rsd=(np.where(sb<0,sb,0.0)**2).sum(axis=1)
    jv=np.maximum(rv-bv,0.0)
    HIm=np.where(kmask,HIw,-np.inf).max(axis=1); LOm=np.where(kmask,LOw,np.inf).min(axis=1)
    okr=np.isfinite(HIm)&np.isfinite(LOm); HIm=np.where(okr,HIm,0.0); LOm=np.where(okr,LOm,0.0)
    park=(HIm-LOm)**2/(4*np.log(2))
    gk=np.maximum(0.5*(HIm-LOm)**2-(2*np.log(2)-1)*(CLw[:,-1]-OPw[:,0])**2,1e-300)
    slopes=[]
    for M in GRID_SIG[hname]:
        s=subbars(rw,M); slopes.append((s**2).sum(axis=1))
    Ms=np.array(GRID_SIG[hname],float); Y=np.column_stack(slopes)
    sig_slope=((Ms-Ms.mean())@ (Y-Y.mean(axis=1,keepdims=True)).T)/((Ms-Ms.mean())**2).sum()
    wdates=np.repeat(ds,nw)
    return dict(rv=rv[live],rsu=rsu[live],rsd=rsd[live],jv=jv[live],park=park[live],
                gk=gk[live],rq=rq[live],slope=sig_slope[live],wdates=wdates[live],
                nw=nw,dates=ds)
def volume_series(root,geom):
    df=pd.read_parquet(os.path.join(S04,f"bars_{geom}.parquet"),columns=["root","tdate","ny_min","volume"])
    df=df[df.root==root]
    v=df.groupby("tdate")["volume"].sum()
    return v
def main():
    t0=time.time(); rows=[]
    P3=pd.read_csv(os.path.join(RES,"phase3_sizing_params.csv"))
    VOL={}
    for geom in ["GLOBEX","RTH"]:
        for root in ["ES","NQ"]:
            VOL[(root,geom)]=volume_series(root,geom)
    CROSS={}
    for geom in ["GLOBEX","RTH"]:
        for root in ["ES","NQ"]:
            for h in (["1day"] if geom=="GLOBEX" else ["1day","1h","30min"]):
                CROSS[(root,geom,h)]=build(root,geom,"B0",h)
    for geom in ["GLOBEX","RTH"]:
        for root in ["ES","NQ"]:
            other="NQ" if root=="ES" else "ES"
            for btag in ["B0","B1"]:
                for hname in (["1day"] if geom=="GLOBEX" else ["1day","1h","30min"]):
                    d=build(root,geom,btag,hname)
                    n=len(d["rv"])
                    y=np.log(np.maximum(d["rv"][1:],1e-300))          # forward RV
                    feats={}
                    for k,v in [("RS_up","rsu"),("RS_down","rsd"),("JumpVar","jv"),
                                ("Parkinson","park"),("GarmanKlass","gk"),
                                ("RealizedQuarticity","rq")]:
                        feats[k]=np.log(np.maximum(d[v][:-1],1e-300))
                    feats["SignatureSlope"]=d["slope"][:-1]
                    vs=VOL[(root,geom)]
                    wd=pd.to_datetime(d["wdates"][:-1])
                    vv=pd.Series(wd).map(vs).astype(float).values
                    lv=np.log(np.maximum(vv,1.0))
                    norm=pd.Series(lv).rolling(22,min_periods=5).mean().values
                    feats["VolumeSurprise"]=np.nan_to_num(lv-norm,nan=0.0)
                    oc=CROSS[(other,geom,hname)]
                    m=min(len(oc["rv"])-1,len(y))
                    cl_=np.full(len(y),np.nan); cl_[:m]=np.log(np.maximum(oc["rv"][:m],1e-300))
                    feats["CrossLeadLag"]=np.nan_to_num(cl_,nan=np.nanmean(cl_))
                    sub=P3[(P3.root==root)&(P3.geom==geom)&(P3.btag==btag)&(P3.horizon==hname)]
                    for rng_tag in ["restricted_S05","extended"]:
                        rr=sub[sub.range==rng_tag]
                        if not len(rr) or not bool(rr.iloc[0].valid): continue
                        lam_t=float(rr.iloc[0].lam_theory); lam_m=float(rr.iloc[0].lam_intercept)
                        for c in CANDS:
                            x=feats[c]
                            ok=np.isfinite(x)&np.isfinite(y)
                            if ok.sum()<100: continue
                            ic=float(np.corrcoef(x[ok],y[ok])[0,1]); r2=ic*ic
                            rows.append(dict(root=root,geom=geom,btag=btag,horizon=hname,
                                range=rng_tag,candidate=c,n=int(ok.sum()),
                                ic_raw=ic,r2_raw=r2,lam_theory=lam_t,lam_intercept=lam_m,
                                r2_corr_theory=r2/lam_t,r2_corr_measured=r2/lam_m,
                                ic_corr_theory=ic/np.sqrt(lam_t),
                                ic_corr_measured=ic/np.sqrt(lam_m),
                                keep_raw=bool(r2>=THRESH),
                                keep_theory=bool(r2/lam_t>=THRESH),
                                keep_measured=bool(r2/lam_m>=THRESH),
                                band_lo=THRESH*lam_m,band_hi=THRESH,
                                in_flip_band=bool(THRESH*lam_m<=r2<THRESH)))
    P5=pd.DataFrame(rows); P5.to_csv(os.path.join(RES,"phase5_signals.csv"),index=False)
    P5["lam_in_unit"]=(P5.lam_intercept>0)&(P5.lam_intercept<=1)
    P5.to_csv(os.path.join(RES,"phase5_signals.csv"),index=False)
    part=[]
    for rng_tag in ["restricted_S05","extended"]:
      for lu in [True,False]:
        s=P5[(P5.range==rng_tag)&(P5.lam_in_unit==lu)]
        if not len(s): continue
        both=int((s.keep_raw&s.keep_measured).sum())
        only=int(((~s.keep_raw)&s.keep_measured).sum())
        neither=int(((~s.keep_raw)&(~s.keep_measured)).sum())
        lost=int((s.keep_raw&(~s.keep_measured)).sum())
        part.append(dict(range=rng_tag,lam_in_unit=lu,n=len(s),clears_under_both=both,
            clears_only_after_measured=only,clears_neither=neither,
            clears_raw_but_not_measured=lost,
            n_status_change=only+lost,in_flip_band=int(s.in_flip_band.sum())))
    PT=pd.DataFrame(part); PT.to_csv(os.path.join(RES,"phase5_partition.csv"),index=False)
    ch=P5[P5.keep_raw!=P5.keep_measured]
    ch.to_csv(os.path.join(RES,"phase5_status_changes.csv"),index=False)
    print(PT.to_string(index=False)); print()
    print("status changes by horizon:"); print(ch.groupby(["range","horizon"]).size().to_string())
    print(f"PHASE5 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
