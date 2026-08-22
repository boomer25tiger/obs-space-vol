"""S09 Phase 6: HOLDOUT, 2024-01-01 to 2026-08-14 by CME trade date.

Every rule, threshold and parameter used here was fixed before any holdout
number was seen: the engineering rules are the S03/S04/S06R code path with
the sample window moved forward, the reliability parameters are the frozen
Phase 3 fits (both the restricted and the extended range), the shrinkage
rules are the pre-registered R1/R2/R3, and the candidate threshold is the
pre-registered R-squared >= 0.02.  Nothing is re-tuned.
"""
import json, os, sys, time
import numpy as np, pandas as pd
import databento as db
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
DATA=os.path.join(ROOT,"data","GLBX-20260817-KAB3XQ8E4C")
DBN=os.path.join(DATA,"glbx-mdp3-20100606-20260815.ohlcv-1m.dbn.zst")
S06=os.path.join(ROOT,"sessions","s06r-repair")
sys.path.insert(0,os.path.join(S06,"src"))
sys.path.insert(0,os.path.join(ROOT,"sessions","s07-completion-and-spy","src"))
sys.path.insert(0,os.path.join(ROOT,"sessions","s05-reliability-mcs","src"))
from phase23_panels import build_ohlc, cme_holidays, N_GRID, OFF
from phase2_rerun8 import BOUNDARY
import partde as pd5
HO_LO,HO_HI="2024-01-01","2026-08-14"
IS_LO,IS_HI="2016-01-01","2023-12-31"
FIVEMIN={("RTH","1day"):78,("RTH","1h"):12,("RTH","30min"):6,("GLOBEX","1day"):276}
HOR={"1day":None,"1h":60,"30min":30}
GRID_SIG={"1day":[13,26,78,195],"1h":[6,10,15,30],"30min":[5,6,10,15]}
NDAY=252; TARGET_D=0.10/np.sqrt(NDAY)
TICKS=[0.5,1.0,2.0,4.0]; TICKVAL={"ES":12.50,"NQ":5.00}; MULT={"ES":50.0,"NQ":20.0}
THRESH=0.02
CANDS=["RS_up","RS_down","JumpVar","Parkinson","GarmanKlass","VolumeSurprise",
       "CrossLeadLag","RealizedQuarticity","SignatureSlope"]
out={}; timers={}

def gate():
    import numpy, pandas, platform
    rp=os.path.realpath(sys.executable)
    bad=[s for s in ["/Library/Mobile Documents","iCloud","Desktop/obs-space-vol/.venv"] if s in rp]
    g=dict(executable=sys.executable,realpath=rp,numpy=numpy.__version__,
           pandas=pandas.__version__,python=platform.python_version(),
           inside_sync_scope=bool(bad))
    print("GATE",json.dumps(g),flush=True)
    if bad: raise SystemExit("GATE FAILED: interpreter inside sync scope")
    return g

def extract():
    """Stream the official reader; keep UTC ts >= 2023-12-31 so the first
    holdout trade date is complete.  Trade-date filtering happens below."""
    store=db.DBNStore.from_file(DBN)
    lo=np.datetime64("2023-12-31T00:00:00","ns").astype("int64")
    chunks=[]
    it=store.to_ndarray(count=2_000_000)
    for arr in it:
        ts=arr["ts_event"].astype("int64")
        m=ts>=lo
        if m.any():
            a=arr[m]
            chunks.append(np.column_stack([
                a["ts_event"].astype("int64"),a["instrument_id"].astype("int64"),
                a["open"].astype("int64"),a["high"].astype("int64"),
                a["low"].astype("int64"),a["close"].astype("int64"),
                a["volume"].astype("int64")]).astype(np.int64))
    raw=np.concatenate(chunks) if chunks else np.zeros((0,7),np.int64)
    out["holdout_raw_rows"]=int(len(raw))
    return raw,store

def engineer(raw,store):
    """S03 rules 1-4 + R3 + rule 6 + R1 + rule 7, sample window moved forward."""
    df=pd.DataFrame(raw,columns=["ts","iid","open","high","low","close","volume"])
    recs=[]
    for sym,ivs in store.metadata.mappings.items():
        for iv in ivs:
            if iv["symbol"]:
                recs.append((int(iv["symbol"]),np.datetime64(iv["start_date"]),
                             np.datetime64(iv["end_date"]),sym))
    mtab=pd.DataFrame(recs,columns=["iid","d0","d1","raw"])
    df["utc_date"]=df["ts"].values.astype("datetime64[ns]").astype("datetime64[D]")
    df["raw"]=pd.Series(pd.NA,index=df.index,dtype="object")
    for iid,g in mtab.groupby("iid"):
        sel=df.index[df["iid"]==iid]
        if not len(sel): continue
        d=df.loc[sel,"utc_date"].values
        assign=np.full(len(sel),None,dtype=object)
        for _,r in g.iterrows():
            assign[(d>=r["d0"])&(d<r["d1"])]=r["raw"]
        df.loc[sel,"raw"]=assign
    out["rows_unresolved_symbol"]=int(df["raw"].isna().sum())
    df=df[df["raw"].notna()]
    out["rows_spread_filtered"]=int(df["raw"].str.contains("-").sum())
    df=df[~df["raw"].str.contains("-")].copy()
    df["root"]=df["raw"].str[:2]
    df=df[df["root"].isin(["ES","NQ"])].copy()
    ts=pd.DatetimeIndex(df["ts"].values.astype("datetime64[ns]"),tz="UTC")
    ny=ts.tz_convert("America/New_York")
    df["ny_min"]=(ny.hour*60+ny.minute).values
    df["tdate"]=pd.to_datetime((ny+pd.Timedelta(hours=6)).date)
    dow=pd.DatetimeIndex(df["tdate"]).dayofweek; wk=dow>=5
    out["r3_rows_reassigned"]=int(wk.sum())
    df.loc[wk,"tdate"]=df.loc[wk,"tdate"]+pd.to_timedelta((7-dow[wk]).values,unit="D")
    df=df[(df["tdate"]>=HO_LO)&(df["tdate"]<=HO_HI)].copy()
    out["rows_in_holdout"]=int(len(df))
    out["holdout_weekend_trade_dates"]=int(
        (pd.DatetimeIndex(df["tdate"].unique()).dayofweek>=5).sum())
    vol=df.groupby(["root","tdate","raw"])["volume"].sum().reset_index()
    front=vol.sort_values("volume").groupby(["root","tdate"]).tail(1)
    front=front.rename(columns={"raw":"front"})[["root","tdate","front"]]
    df=df.merge(front,on=["root","tdate"],how="left")
    dff=df[df["raw"]==df["front"]].copy()
    daypart=dff[dff["ny_min"]<18*60]
    last_min=daypart.groupby(["root","tdate"])["ny_min"].max()
    early_day=last_min<15*60
    on_mask=(dff["ny_min"]>=1080)|(dff["ny_min"]<570)
    on_ok=(dff[on_mask].groupby(["root","tdate"])["ny_min"].count()/930.0)>=0.90
    def designated(d):
        return ((d.month==11 and d.dayofweek==4 and 23<=d.day<=29)
                or (d.month==7 and d.day==3) or (d.month==12 and d.day==24))
    flags=pd.DataFrame(dict(early_day=early_day)).join(on_ok.rename("on_ok"),how="left")
    flags["on_ok"]=flags["on_ok"].fillna(False).astype(bool)
    flags["early_day"]=flags["early_day"].astype(bool)
    flags["designated"]=[designated(d) for (_,d) in flags.index]
    flags["excl_rth"]=flags["early_day"]|flags["designated"]
    flags["excl_glbx"]=(flags["early_day"]&~flags["on_ok"])|flags["designated"]
    out["r1_excluded_rth"]={r:int(flags.loc[r]["excl_rth"].sum()) for r in ["ES","NQ"]}
    out["r1_excluded_globex"]={r:int(flags.loc[r]["excl_glbx"].sum()) for r in ["ES","NQ"]}
    cond=json.load(open(os.path.join(DATA,"condition.json")))
    entries=cond["conditions"] if isinstance(cond,dict) and "conditions" in cond else cond
    degr=sorted({e["date"] for e in entries if e.get("condition")=="degraded"
                 and e["date"]>=HO_LO})
    out["holdout_degraded_dates"]=degr
    panels={}; ledger={}
    for geom,exfl in [("RTH","excl_rth"),("GLOBEX","excl_glbx")]:
        keep_frames=[]
        for r in ["ES","NQ"]:
            fl=flags.loc[r]; keep_dates=set(fl.index[~fl[exfl]])
            f=front[front["root"]==r].sort_values("tdate")
            f=f[f["tdate"].isin(keep_dates)].reset_index(drop=True)
            roll=f["front"]!=f["front"].shift(); roll.iloc[0]=False
            bad=roll|roll.shift(-1,fill_value=False)|roll.shift(1,fill_value=False)
            keep=set(f.loc[~bad,"tdate"])
            ledger[f"{r}_{geom}"]=dict(after_r1=len(f),roll_excluded=int(bad.sum()),
                                       final=len(keep))
            keep_frames.append(dff[(dff["root"]==r)&(dff["tdate"].isin(keep))])
        panels[geom]=pd.concat(keep_frames)
    out["ledger"]=ledger
    return panels

def build_panels(panels):
    P={}
    hol=cme_holidays(range(2024,2028))
    hol.to_csv(os.path.join(RES,"phase6_calendar.csv"),index=False)
    halt_of=dict(zip(hol.date,hol.halt_ny_min)); hset=set(hol.date)
    for geom in ["GLOBEX","RTH"]:
        d=panels[geom]
        for root in ["ES","NQ"]:
            dates,grids,present=build_ohlc(d,root,geom)
            ds=np.array([str(x)[:10] for x in dates.astype("datetime64[D]")])
            n=N_GRID[geom]; tr=np.ones((len(ds),n),bool)
            for i,dd in enumerate(ds):
                if dd in hset:
                    hm=int(halt_of[dd])
                    hs=(hm-OFF[geom])%1440 if geom=="GLOBEX" else hm-570
                    tr[i,hs:]=False
            np.savez_compressed(os.path.join(CACHE,f"ho_panel_{root}_{geom}.npz"),
                dates=ds,present=present,tradeable=tr,
                **{k:v.astype(np.float32) for k,v in grids.items()})
            P[(root,geom)]=(ds,grids,present,tr)
    return P

def wins(grids,present,tr,btag,geom,hname):
    cl=grids["close"].astype(np.float64); hi=grids["high"].astype(np.float64)
    lo=grids["low"].astype(np.float64); op=grids["open"].astype(np.float64)
    r1=np.diff(cl,axis=1)
    if btag=="B1":
        for m in BOUNDARY[geom]:
            sl=(m-OFF[geom])%1440 if geom=="GLOBEX" else m-OFF[geom]
            if 0<sl<=r1.shape[1]: r1[:,sl-1]=0.0
    keep=tr[:,1:]&tr[:,:-1]&present[:,1:]&present[:,:-1]
    r1=np.where(tr[:,1:]&tr[:,:-1],r1,0.0)
    wl=HOR[hname]
    if wl is None:
        rw,kw,nw=r1,keep,1; HIw,LOw,OPw,CLw=hi,lo,op,cl
    else:
        nw=r1.shape[1]//wl
        rw=r1[:,:nw*wl].reshape(-1,wl); kw=keep[:,:nw*wl].reshape(-1,wl)
        HIw=hi[:,1:1+nw*wl].reshape(-1,wl); LOw=lo[:,1:1+nw*wl].reshape(-1,wl)
        OPw=op[:,1:1+nw*wl].reshape(-1,wl); CLw=cl[:,1:1+nw*wl].reshape(-1,wl)
    live=kw.any(axis=1)
    kmask=kw if wl else np.ones_like(HIw,bool)   # 1day: full-width price grid (series())
    return rw,kmask,HIw,LOw,OPw,CLw,live,nw

def subb(rw,M):
    N,L=rw.shape; e=(np.arange(M+1)*L)//M
    cs=np.concatenate([np.zeros((N,1)),np.cumsum(rw,axis=1)],axis=1)
    return cs[:,e[1:]]-cs[:,e[:-1]]

def feature_block(rw,kw,HIw,LOw,OPw,CLw,M5,hname):
    sb=subb(rw,M5); rv=(sb**2).sum(axis=1)
    a=np.abs(sb); Mo=max(M5,3)
    bv=(np.pi/2)*(Mo/max(Mo-1,1))*(a[:,1:]*a[:,:-1]).sum(axis=1)
    rq=(Mo/3.0)*((sb**2)**2).sum(axis=1)
    rsu=(np.where(sb>0,sb,0.0)**2).sum(axis=1); rsd=(np.where(sb<0,sb,0.0)**2).sum(axis=1)
    HIm=np.where(kw,HIw,-np.inf).max(axis=1); LOm=np.where(kw,LOw,np.inf).min(axis=1)
    okr=np.isfinite(HIm)&np.isfinite(LOm)
    HIm=np.where(okr,HIm,0.0); LOm=np.where(okr,LOm,0.0)
    park=(HIm-LOm)**2/(4*np.log(2))
    gk=np.maximum(0.5*(HIm-LOm)**2-(2*np.log(2)-1)*(CLw[:,-1]-OPw[:,0])**2,1e-300)
    Ms=np.array(GRID_SIG[hname],float)
    Y=np.column_stack([ (subb(rw,int(M))**2).sum(axis=1) for M in Ms ])
    slope=((Ms-Ms.mean())@(Y-Y.mean(axis=1,keepdims=True)).T)/((Ms-Ms.mean())**2).sum()
    return dict(rv=rv,rsu=rsu,rsd=rsd,jv=np.maximum(rv-bv,0.0),park=park,gk=gk,
                rq=rq,slope=slope)

def har_oos(rv_all,n_is,D):
    T=len(rv_all); x1,x5,x22=pd5.har_X(rv_all,D)
    X=np.column_stack([np.ones(T),x1,x5,x22]); F=np.full(T,np.nan)
    for t in range(n_is,T):
        Xt,yt=X[22*D:t-1],rv_all[22*D+1:t]
        ok=np.isfinite(Xt).all(axis=1)
        if ok.sum()<6: continue
        b,*_=np.linalg.lstsq(Xt[ok],yt[ok],rcond=None)
        F[t]=max(float(X[t-1]@b),1e-12)
    return F

def score(iv_proxy,fc,lam,mu,tickval,mult,px,qtr=None):
    elog=np.log(np.maximum(fc,1e-300)) if lam is None else \
         (1-lam)*mu+lam*np.log(np.maximum(fc,1e-300))
    sig=np.sqrt(np.exp(elog)); w=TARGET_D/np.maximum(sig,1e-12)
    ok=np.isfinite(w)&np.isfinite(iv_proxy)&(iv_proxy>0)
    realized=w*np.sqrt(np.maximum(iv_proxy,1e-300))
    dev=np.log(np.maximum(realized,1e-300))-np.log(TARGET_D)
    te=float(np.sqrt(np.nanmean(dev[ok]**2)))
    turn=float(np.nanmean(np.abs(np.diff(w[ok]))))
    notional=mult*px
    d=dict(te=te,turnover=turn,n=int(ok.sum()),
           **{f"cost_{t}t_bps":float(turn*(2*t*tickval/notional)*1e4) for t in TICKS})
    if qtr is not None:
        qt=pd.DataFrame(dict(q=qtr[ok],d2=dev[ok]**2)).groupby("q")["d2"].mean()
        te_q=np.sqrt(qt.values)
        d["te_quarterly_mean"]=float(te_q.mean()); d["te_quarterly_sd"]=float(te_q.std())
        d["n_quarters"]=int(len(te_q)); d["te_quarterly_max"]=float(te_q.max())
        d["_qtab"]=qt
    return d,w

def main():
    t0=time.time(); out["gate_phase6"]=gate()
    t=time.time(); raw,store=extract(); timers["extract"]=round(time.time()-t,1)
    print(f"extracted {len(raw)} rows in {timers['extract']}s",flush=True)
    t=time.time(); panels=engineer(raw,store); timers["engineer"]=round(time.time()-t,1)
    for geom in ["GLOBEX","RTH"]:
        panels[geom].drop(columns=["front","utc_date"]).to_parquet(
            os.path.join(CACHE,f"ho_bars_{geom}.parquet"))
    P=build_panels(panels); timers["panels"]=round(time.time()-t,1)
    print(json.dumps({k:v for k,v in out.items() if k!="gate_phase6"},indent=1)[:1800],flush=True)
    P3=pd.read_csv(os.path.join(RES,"phase3_sizing_params.csv"))
    P5=pd.read_csv(os.path.join(RES,"phase5_signals.csv"))
    # ---------------- sizing OOS
    rows=[]; qrows=[]
    for geom in ["GLOBEX","RTH"]:
        for root in ["ES","NQ"]:
            ds,grids,present,tr=P[(root,geom)]
            M5=FIVEMIN[(geom,"1day")]
            rw,kw,HIw,LOw,OPw,CLw,live,nw=wins(grids,present,tr,"B0",geom,"1day")
            f_ho=feature_block(rw[live],kw[live],HIw[live],LOw[live],OPw[live],
                               CLw[live],M5,"1day")
            ho_dates=pd.to_datetime(ds[live])
            zi=np.load(os.path.join(S06,"cache",f"panel_ohlc_{root}_{geom}.npz"))
            from phase2_rerun8 import tradeable_ext
            trm,dsi=tradeable_ext(root,geom)
            rwi,kwi,HIi,LOi,OPi,CLi,livei,_=wins(
                {k:zi[k] for k in ["open","high","low","close"]},zi["present"],trm,
                "B0",geom,"1day")
            f_is=feature_block(rwi[livei],kwi[livei],HIi[livei],LOi[livei],
                               OPi[livei],CLi[livei],M5,"1day")
            rv_all=np.concatenate([f_is["rv"],f_ho["rv"]]); n_is=len(f_is["rv"])
            F=har_oos(rv_all,n_is,1)[n_is:]
            iv_ho=f_ho["rv"]
            mu=float(np.log(f_is["rv"][f_is["rv"]>0]).mean())
            px=float(np.exp(grids["close"][live]).mean())
            qtr=ho_dates.to_period("Q").astype(str).values
            np.savez_compressed(os.path.join(CACHE,f"ho_sizing_{root}_{geom}.npz"),
                rv=iv_ho,F=F,dates=ds[live],mu=mu,px=px,n_is=n_is)
            sub=P3[(P3.root==root)&(P3.geom==geom)&(P3.btag=="B0")&(P3.horizon=="1day")]
            for rng_tag in ["restricted_S05","extended"]:
                rr=sub[sub.range==rng_tag]
                if not len(rr) or not bool(rr.iloc[0].valid): continue
                lt=float(rr.iloc[0].lam_theory); lm=float(rr.iloc[0].lam_intercept)
                for rule,lam in [("R1",None),("R2",lt),("R3",lm)]:
                    d,w=score(iv_ho,F,lam,mu,TICKVAL[root],MULT[root],px,qtr)
                    qt=d.pop("_qtab")
                    for q,v in qt.items():
                        qrows.append(dict(root=root,geom=geom,range=rng_tag,rule=rule,
                                          quarter=q,te=float(np.sqrt(v))))
                    rows.append(dict(root=root,geom=geom,range=rng_tag,rule=rule,
                        lam_used=(lam if lam is not None else np.nan),**d))
                    np.savez_compressed(os.path.join(CACHE,
                        f"ho_pos_{root}_{geom}_{rng_tag}_{rule}.npz"),w=w,dates=ds[live])
    H=pd.DataFrame(rows); H.to_csv(os.path.join(RES,"phase6_sizing_oos.csv"),index=False)
    pd.DataFrame(qrows).to_csv(os.path.join(RES,"phase6_te_quarterly.csv"),index=False)
    print(); print(H.to_string(index=False),flush=True)
    # ---------------- candidates OOS
    VOL={}
    for geom in ["GLOBEX","RTH"]:
        d=pd.read_parquet(os.path.join(CACHE,f"ho_bars_{geom}.parquet"),
                          columns=["root","tdate","volume"])
        for root in ["ES","NQ"]:
            VOL[(root,geom)]=d[d.root==root].groupby("tdate")["volume"].sum()
    BLK={}
    for geom in ["GLOBEX","RTH"]:
        for root in ["ES","NQ"]:
            for hname in (["1day"] if geom=="GLOBEX" else ["1day","1h","30min"]):
                ds,grids,present,tr=P[(root,geom)]
                rw,kw,HIw,LOw,OPw,CLw,live,nw=wins(grids,present,tr,"B0",geom,hname)
                BLK[(root,geom,hname)]=(feature_block(rw[live],kw[live],HIw[live],
                    LOw[live],OPw[live],CLw[live],FIVEMIN[(geom,hname)],hname),
                    np.repeat(ds,nw)[live])
    crows=[]
    for geom in ["GLOBEX","RTH"]:
        for root in ["ES","NQ"]:
            other="NQ" if root=="ES" else "ES"
            for btag in ["B0","B1"]:
                for hname in (["1day"] if geom=="GLOBEX" else ["1day","1h","30min"]):
                    ds,grids,present,tr=P[(root,geom)]
                    rw,kw,HIw,LOw,OPw,CLw,live,nw=wins(grids,present,tr,btag,geom,hname)
                    d=feature_block(rw[live],kw[live],HIw[live],LOw[live],OPw[live],
                                    CLw[live],FIVEMIN[(geom,hname)],hname)
                    wd=pd.to_datetime(np.repeat(ds,nw)[live][:-1])
                    y=np.log(np.maximum(d["rv"][1:],1e-300))
                    ft={k:np.log(np.maximum(d[v][:-1],1e-300)) for k,v in
                        [("RS_up","rsu"),("RS_down","rsd"),("JumpVar","jv"),
                         ("Parkinson","park"),("GarmanKlass","gk"),
                         ("RealizedQuarticity","rq")]}
                    ft["SignatureSlope"]=d["slope"][:-1]
                    lv=np.log(np.maximum(pd.Series(wd).map(VOL[(root,geom)])
                                         .astype(float).values,1.0))
                    ft["VolumeSurprise"]=np.nan_to_num(
                        lv-pd.Series(lv).rolling(22,min_periods=5).mean().values,nan=0.0)
                    oc=BLK[(other,geom,hname)][0]
                    m=min(len(oc["rv"])-1,len(y)); cl_=np.full(len(y),np.nan)
                    cl_[:m]=np.log(np.maximum(oc["rv"][:m],1e-300))
                    ft["CrossLeadLag"]=np.nan_to_num(cl_,nan=np.nanmean(cl_))
                    sub=P3[(P3.root==root)&(P3.geom==geom)&(P3.btag==btag)&
                           (P3.horizon==hname)]
                    for rng_tag in ["restricted_S05","extended"]:
                        rr=sub[sub.range==rng_tag]
                        if not len(rr) or not bool(rr.iloc[0].valid): continue
                        lt=float(rr.iloc[0].lam_theory); lm=float(rr.iloc[0].lam_intercept)
                        for c in CANDS:
                            x=ft[c]; ok=np.isfinite(x)&np.isfinite(y)
                            if ok.sum()<50: continue
                            ic=float(np.corrcoef(x[ok],y[ok])[0,1]); r2=ic*ic
                            crows.append(dict(root=root,geom=geom,btag=btag,
                                horizon=hname,range=rng_tag,candidate=c,
                                n_oos=int(ok.sum()),ic_oos=ic,r2_oos=r2,
                                r2_oos_corr_theory=r2/lt,r2_oos_corr_measured=r2/lm,
                                keep_oos_raw=bool(r2>=THRESH),
                                keep_oos_measured=bool(r2/lm>=THRESH)))
    C=pd.DataFrame(crows)
    K=P5[["root","geom","btag","horizon","range","candidate","r2_raw",
          "r2_corr_measured","keep_raw","keep_measured"]].rename(columns={
          "r2_raw":"r2_is","r2_corr_measured":"r2_is_corr_measured",
          "keep_raw":"keep_is_raw","keep_measured":"keep_is_measured"})
    C=C.merge(K,on=["root","geom","btag","horizon","range","candidate"],how="left")
    C["partition_is"]=np.where(C.keep_is_raw&C.keep_is_measured,"clears_both",
        np.where((~C.keep_is_raw)&C.keep_is_measured,"only_after_measured",
        np.where(C.keep_is_raw&(~C.keep_is_measured),"raw_only","clears_neither")))
    C["degradation_r2"]=C.r2_is-C.r2_oos
    C.to_csv(os.path.join(RES,"phase6_candidates_oos.csv"),index=False)
    S=C.groupby(["range","partition_is"]).agg(
        n=("candidate","size"),r2_is_mean=("r2_is","mean"),
        r2_oos_mean=("r2_oos","mean"),degradation_mean=("degradation_r2","mean"),
        oos_clears_raw=("keep_oos_raw","sum"),
        oos_clears_measured=("keep_oos_measured","sum")).reset_index()
    S.to_csv(os.path.join(RES,"phase6_partition_oos.csv"),index=False)
    print(); print(S.to_string(index=False),flush=True)
    timers["total"]=round(time.time()-t0,1); out["timers"]=timers
    json.dump(out,open(os.path.join(RES,"phase6_summary.json"),"w"),indent=1,default=str)
    print(f"PHASE6 DONE {timers['total']}s")
if __name__=="__main__": main()
