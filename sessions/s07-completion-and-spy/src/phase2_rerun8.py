"""S07 Phase 2: extended exclusion + repaired filter bound; rerun the 8 halted cells."""
import json, os, sys, time
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
S06=os.path.join(ROOT,"sessions","s06r-repair")
S06C,S06R_=os.path.join(S06,"cache"),os.path.join(S06,"results")
sys.path.insert(0,os.path.join(S06,"tests"))
sys.path.insert(0,os.path.join(ROOT,"sessions","s05-reliability-mcs","src"))
from test_invariants import assert_forecasts_positive, InvariantViolation
import partde as pd5
MODELS=pd5.MODELS
HOR={"1day":None,"1h":60,"30min":30}
OFF={"RTH":570,"GLOBEX":1080}
BOUNDARY={"RTH":[570,571,959,960],"GLOBEX":[570,571,959,960,1081]}
# item 51: exchange-declared halts and documented degraded dates
HALT_SESSIONS={"2020-03-09":("09:30","circuit-breaker limit halt (exchange log)"),
 "2020-03-12":("09:30","circuit-breaker limit halt (exchange log)"),
 "2020-03-18":("09:30","circuit-breaker limit halt (exchange log)"),
 "2020-03-23":("09:30","circuit-breaker limit halt (exchange log)"),
 "2020-03-24":("09:30","circuit-breaker limit halt (exchange log)"),
 "2019-02-27":("09:30","Databento degraded condition (S04 R2 set)"),
 "2020-07-01":("09:30","Databento degraded condition (S04 R2 set)")}
CELLS8=[(r,g,b,h) for g in ["GLOBEX"] for r in ["ES","NQ"] for b in ["B0","B1"]
        for h in ["1h","30min"]]

def tradeable_ext(root,geom):
    """S06R calendar exclusion, extended with the item-51 sessions.

    On a halt session the exclusion targets the minutes where the exchange
    printed NO bar. That is a data-PRESENCE criterion taken from the
    exchange's own record of what traded, not a realized-variance criterion,
    so it stays inside item 42; and unlike a blanket halt-to-close rule it
    keeps the traded portion of those sessions, which are among the highest
    volatility days in the sample. The first audit used a blanket
    09:30-to-close rule and removed 42 to 98 windows per cell that carried
    non-zero realized variance; that rule was discarded for this one.
    """
    z=np.load(os.path.join(S06C,f"tradeable_{root}_{geom}.npz"))
    tr=z["tradeable"].copy(); ds=np.array(z["dates"],dtype="U10")
    pres=np.load(os.path.join(S06C,f"panel_ohlc_{root}_{geom}.npz"))["present"]
    for d,(ht,_) in HALT_SESSIONS.items():
        i=np.where(ds==d)[0]
        if not len(i): continue
        tr[i[0]] &= pres[i[0]]
    return tr, ds

def series(root,geom,btag,wlen):
    z=np.load(os.path.join(S06C,f"panel_ohlc_{root}_{geom}.npz"))
    cl=z["close"].astype(np.float64); hi=z["high"].astype(np.float64)
    lo=z["low"].astype(np.float64); op=z["open"].astype(np.float64); pres=z["present"]
    tr,ds=tradeable_ext(root,geom)
    r1=np.diff(cl,axis=1); keep=tr[:,1:]&tr[:,:-1]
    if btag=="B1":
        for m in BOUNDARY[geom]:
            s=(m-OFF[geom])%1440 if geom=="GLOBEX" else m-OFF[geom]
            if 0<s<=r1.shape[1]: r1[:,s-1]=0.0
    r1=np.where(keep,r1,0.0)
    if wlen is None: nw,rw,kw=1,r1,keep; HIw,LOw,OPw,CLw=hi,lo,op,cl
    else:
        nw=r1.shape[1]//wlen
        rw=r1[:,:nw*wlen].reshape(-1,wlen); kw=keep[:,:nw*wlen].reshape(-1,wlen)
        HIw=hi[:,1:1+nw*wlen].reshape(-1,wlen); LOw=lo[:,1:1+nw*wlen].reshape(-1,wlen)
        OPw=op[:,1:1+nw*wlen].reshape(-1,wlen); CLw=cl[:,1:1+nw*wlen].reshape(-1,wlen)
    r2=rw**2; rv=r2.sum(axis=1); Meff=kw.sum(axis=1).astype(float)
    Mok=np.maximum(Meff,3.0); a=np.abs(rw)
    bv=(np.pi/2)*(Mok/np.maximum(Mok-1,1))*(a[:,1:]*a[:,:-1]).sum(axis=1)
    rq=(Mok/3)*(r2*r2).sum(axis=1)
    kmask=kw if wlen else np.ones_like(HIw,bool)   # 1day: full-width price grid
    HIm=np.where(kmask,HIw,-np.inf).max(axis=1); LOm=np.where(kmask,LOw,np.inf).min(axis=1)
    okr=np.isfinite(HIm)&np.isfinite(LOm); HIm=np.where(okr,HIm,0.0); LOm=np.where(okr,LOm,0.0)
    park=(HIm-LOm)**2/(4*np.log(2))
    gk=0.5*(HIm-LOm)**2-(2*np.log(2)-1)*(CLw[:,-1]-OPw[:,0])**2
    return dict(rv=rv,bv=bv,rq=rq,park=park,gk=np.maximum(gk,1e-300),
                ret=rw.sum(axis=1),nw=nw,Meff=Meff,tradeable=kw.any(axis=1),
                wdates=np.repeat(ds,nw))

def run_cell(job):
    root,geom,btag,hname=job; cell=f"{root}/{geom}/{btag}/{hname}"; t0=time.time()
    S=series(root,geom,btag,HOR[hname]); D=S["nw"]; rv=S["rv"]
    warm=500 if hname=="1day" else max(500,22*D+100); refit=1 if hname=="1day" else D
    F,start,nonconv=pd5.forecasts(S,D,warm,refit,hname=="1day")
    ok=np.ones(len(rv),bool)
    for m in MODELS: ok&=np.isfinite(F[m])
    ok[:max(start,warm)]=False; ok&=S["tradeable"]
    rvv=rv[ok]; ins=rv[:max(start,warm)]
    pos=ins[ins>0]
    rmin=float(pos.min()) if len(pos) else 1e-12      # item 52: strictly positive
    rmax=float(ins.max()); rmean=float(ins.mean())
    filt=[]; Ff={}
    for m in MODELS:
        x=F[m][ok].copy()
        if m in ("M3_HARJ","M4_HARQ"):
            bad=(x<rmin)|(x>rmax)|~np.isfinite(x)
            qb=pd5.qlike(np.where(x>0,x,np.nan),rvv)
            xf=np.where(bad,rmean,x); qa=pd5.qlike(xf,rvv)
            alt=(x<rmin)|(x>100*rmean)
            filt.append(dict(cell=cell,model=m,n_eval=int(ok.sum()),
                n_replaced=int(bad.sum()),share_replaced=float(bad.mean()),
                qlike_before=float(np.nanmean(qb[np.isfinite(qb)])),
                qlike_after=float(np.nanmean(qa)),
                n_replaced_alt_100x=int(alt.sum()),share_replaced_alt_100x=float(alt.mean()),
                dates_replaced=";".join(sorted(set(np.array(S["wdates"])[ok][bad].tolist()))[:40]),
                rv_min=rmin,rv_max=rmax,rv_mean=rmean))
            x=xf
        Ff[m]=x
    # Item 41: a model that cannot produce admissible forecasts in a cell is
    # marked unavailable there and the model set is reduced, with the
    # reduction stated in every table. That rule is written for RGARCH, which
    # is never filtered; the same logic is applied to any other model failing
    # positivity (here M6_PARK, which returns exactly zero when high equals
    # low across a whole window). No value is replaced and no model is
    # respecified - the model is removed from the set for that cell only.
    # Disclosed as a post-hoc extension of item 41.
    dropped=[]
    for m in MODELS:
        try: assert_forecasts_positive(Ff[m],cell,m)
        except InvariantViolation as e: dropped.append((m,str(e)))
    mods=[m for m in MODELS if m not in [d[0] for d in dropped]]
    for m in mods: assert_forecasts_positive(Ff[m],cell,m)   # retained set must pass
    L=np.column_stack([pd5.qlike(Ff[m],rvv) for m in mods])
    np.savez_compressed(os.path.join(CACHE,f"gen_{root}_{geom}_{btag}_{hname}.npz"),
        rv=rv,ok=ok,L=L,rvv=rvv,Meff=S["Meff"],wdates=S["wdates"],
        tradeable=S["tradeable"],D=D,start=start,warm=warm,nonconv=nonconv,
        ret=S["ret"],models=np.array(mods),
        dropped=np.array([d[0] for d in dropped]),
        **{f"F_{m}":Ff[m] for m in MODELS})
    return dict(cell=cell,n_eval=int(ok.sum()),n_excluded=int((~S["tradeable"]).sum()),
                D=int(D),rv_min_positive=rmin,model_set="|".join(mods),
                n_models=len(mods),dropped="|".join(d[0] for d in dropped),
                drop_reason=" ;; ".join(d[1] for d in dropped),
                seconds=round(time.time()-t0,1)),filt

def main():
    t0=time.time(); os.makedirs(CACHE,exist_ok=True)
    # exclusion audit
    aud=[]
    for root,geom in [("ES","GLOBEX"),("NQ","GLOBEX"),("ES","RTH"),("NQ","RTH")]:
        z=np.load(os.path.join(S06C,f"panel_ohlc_{root}_{geom}.npz"))
        cl=z["close"].astype(np.float64); tr,ds=tradeable_ext(root,geom)
        r1=np.diff(cl,axis=1); trr=tr[:,1:]&tr[:,:-1]
        for hname,wl in [("1h",60),("30min",30)]:
            nw=r1.shape[1]//wl
            rw=np.where(trr,r1,0.0)[:,:nw*wl].reshape(-1,wl)
            tw=trr[:,:nw*wl].reshape(-1,wl)
            rv_raw=(r1[:,:nw*wl].reshape(-1,wl)**2).sum(axis=1)
            exc=~tw.any(axis=1); rv=(rw**2).sum(axis=1)
            aud.append(dict(root=root,geom=geom,horizon=hname,n_windows=int(len(rv)),
                n_excluded=int(exc.sum()),
                n_excluded_with_nonzero_rv=int((exc&(rv_raw>0)).sum()),
                n_zero_rv_remaining=int(((rv==0)&~exc).sum())))
    pd.DataFrame(aud).to_csv(os.path.join(RES,"phase2_exclusion_audit.csv"),index=False)
    print(pd.DataFrame(aud).to_string(index=False),flush=True)
    meta,filt,halts=[],[],[]
    todo=[c for c in CELLS8 if not os.path.exists(
        os.path.join(CACHE,f"gen_{c[0]}_{c[1]}_{c[2]}_{c[3]}.npz"))]
    print(f"rerunning {len(todo)} halted cells",flush=True)
    with ProcessPoolExecutor(max_workers=5) as ex:
        futs={ex.submit(run_cell,c):c for c in todo}
        for f in as_completed(futs):
            try: m,fr=f.result()
            except InvariantViolation as e:
                halts.append(dict(cell="/".join(futs[f]),message=str(e)))
                print("STILL HALTED:",e,flush=True); continue
            meta.append(m); filt.extend(fr)
            print(f"  {len(meta)}/{len(todo)} {m['cell']} ({m['seconds']}s)",flush=True)
    pd.DataFrame(meta).to_csv(os.path.join(RES,"phase2_gen_meta.csv"),index=False)
    pd.DataFrame(filt).to_csv(os.path.join(RES,"phase2_filter_new8.csv"),index=False)
    pd.DataFrame(halts).to_csv(os.path.join(RES,"phase2_still_halted.csv"),index=False)
    print(f"PHASE2 GEN DONE {time.time()-t0:.0f}s",flush=True)
if __name__=="__main__": main()
