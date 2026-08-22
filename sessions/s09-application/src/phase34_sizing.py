"""S09 Phases 3 and 4: sizing parameters (restricted + extended), simulated sizing.

Item 66: the intercept fit is reported on BOTH the original S05 grid and the
extended grid; no sizing result is reported at only one. Where the original
grid holds a single M (the RTH intraday horizons) a restricted fit is
undefined and is reported as such rather than substituted.
Nothing here reads data dated on or after 2024-01-01.
"""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy.optimize import curve_fit
from scipy.special import polygamma
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
S06=os.path.join(ROOT,"sessions","s06r-repair"); S08=os.path.join(ROOT,"sessions","s08-final")
S05E=os.path.join(ROOT,"sessions","s05e-positive-control")
sys.path.insert(0,os.path.join(ROOT,"sessions","s07-completion-and-spy","src"))
sys.path.insert(0,os.path.join(ROOT,"sessions","s05-reliability-mcs","src"))
sys.path.insert(0,os.path.join(ROOT,"sessions","s01-estimator-validation","src"))
from fbm import fgn_acf, CirculantEmbedding
from phase2_rerun8 import tradeable_ext
import partde as pd5
CELLS=[(r,g,b,h) for g in ["GLOBEX","RTH"] for r in ["ES","NQ"] for b in ["B0","B1"]
       for h in (["1day"] if g=="GLOBEX" else ["1day","1h","30min"])]
GRID_EXT={("RTH","1day"):[5,6,10,13,26,78,195,389],("RTH","1h"):[4,5,6,10,12,15,20,30,60],
          ("RTH","30min"):[5,6,10,15,30],("GLOBEX","1day"):[5,6,10,12,23,46,138,276,345,1379]}
GRID_S05={("RTH","1day"):[13,26,78,195,389],("RTH","1h"):[60],("RTH","30min"):[30],
          ("GLOBEX","1day"):[23,46,138,345,1379]}
FIVEMIN={("RTH","1day"):78,("RTH","1h"):12,("RTH","30min"):6,("GLOBEX","1day"):276}
HOR={"1day":None,"1h":60,"30min":30}
NDAY=252; TARGET_ANN=0.10; TARGET_D=TARGET_ANN/np.sqrt(NDAY)
TICKS=[0.5,1.0,2.0,4.0]; TICKVAL={"ES":12.50,"NQ":5.00}; MULT={"ES":50.0,"NQ":20.0}
JUMP_INTENSITY=1.0; SEEDS_MASTER=20260819; N_SEEDS=5
H_ROUGH=0.1          # S05E A4
ARMS=["A2","A4p"]    # A2: iid log-IV + diurnal + jumps. A4p: persistent (rough) log-IV, same diurnal and jumps.
def trig(M): return float(polygamma(1,M/2.0))
def fitf(M,y):
    M=np.asarray(M,float); y=np.asarray(y,float); ok=np.isfinite(y)
    if ok.sum()<4: return None
    try:
        p,_=curve_fit(lambda x,c,A,b:c+A*np.power(x,b),M[ok],y[ok],
                      p0=[y[ok].min(),1.0,-0.5],maxfev=80000)
        pred=p[0]+p[1]*np.power(M[ok],p[2])
        return dict(c=float(p[0]),A=float(p[1]),b=float(p[2]),
                    rmse=float(np.sqrt(np.mean((y[ok]-pred)**2))),n=int(ok.sum()))
    except Exception: return None
def subbars(rw,kw,M):
    N,L=rw.shape; e=(np.arange(M+1)*L)//M
    cs=np.concatenate([np.zeros((N,1)),np.cumsum(rw,axis=1)],axis=1)
    sb=cs[:,e[1:]]-cs[:,e[:-1]]
    kc=np.concatenate([np.zeros((N,1)),np.cumsum(kw.astype(np.int32),axis=1)],axis=1)
    return sb,((kc[:,e[1:]]-kc[:,e[:-1]])>0).sum(axis=1).astype(float)
def cell_windows(root,geom,btag,hname):
    z=np.load(os.path.join(S06,"cache",f"panel_ohlc_{root}_{geom}.npz"))
    cl=z["close"].astype(np.float64); pres=z["present"]
    trm,_=tradeable_ext(root,geom)
    r1=np.where(trm[:,1:]&trm[:,:-1],np.diff(cl,axis=1),0.0)
    keep=trm[:,1:]&trm[:,:-1]&pres[:,1:]&pres[:,:-1]
    wl=HOR[hname]
    if wl is None: rw,kw=r1,keep
    else:
        nw=r1.shape[1]//wl; rw=r1[:,:nw*wl].reshape(-1,wl); kw=keep[:,:nw*wl].reshape(-1,wl)
    live=kw.any(axis=1)
    return rw[live],kw[live],float(np.exp(cl).mean())
def har_forecast(rv,D):
    T=len(rv); x1,x5,x22=pd5.har_X(rv,D)
    X=np.column_stack([np.ones(T),x1,x5,x22]); F=np.full(T,np.nan)
    warm=max(500,22*D+2)
    for t in range(warm,T):
        Xt,yt=X[22*D:t-1],rv[22*D+1:t]
        ok=np.isfinite(Xt).all(axis=1)
        if ok.sum()<6: continue
        b,*_=np.linalg.lstsq(Xt[ok],yt[ok],rcond=None)
        F[t]=max(float(X[t-1]@b),1e-12)
    return F,warm
def size_and_score(iv_true,fc,lam,mu_ins,tickval,mult,px):
    ok=np.isfinite(fc)&np.isfinite(iv_true)&(iv_true>0)
    elog=(1-lam)*mu_ins+lam*np.log(np.maximum(fc,1e-300)) if lam is not None else np.log(np.maximum(fc,1e-300))
    sig=np.sqrt(np.exp(elog)); w=np.where(ok,TARGET_D/np.maximum(sig,1e-12),np.nan)
    realized=w*np.sqrt(iv_true)
    te=float(np.sqrt(np.nanmean((np.log(np.maximum(realized,1e-300))-np.log(TARGET_D))**2)))
    dw=np.abs(np.diff(w[ok])); turn=float(np.nanmean(dw))
    notional=mult*px
    costs={f"{t}t":float(turn*(2*t*tickval/notional)*1e4) for t in TICKS}
    return dict(te=te,turnover=turn,**costs)
def main():
    t0=time.time(); timers={}
    # ---------------- PHASE 3
    p3=[]
    for root,geom,btag,hname in CELLS:
        rw,kw,px=cell_windows(root,geom,btag,hname)
        varlog={}
        for M in sorted(set(GRID_EXT[(geom,hname)])|set(GRID_S05[(geom,hname)])):
            if M>rw.shape[1]: continue
            sb,_=subbars(rw,kw,M); rv=(sb**2).sum(axis=1); pos=rv>0
            varlog[M]=float(np.log(rv[pos]).var())
        for tag,g in [("restricted_S05",GRID_S05[(geom,hname)]),("extended",GRID_EXT[(geom,hname)])]:
            Ms=[m for m in g if m in varlog]
            f=fitf(Ms,[varlog[m] for m in Ms])
            M5=FIVEMIN[(geom,hname)]
            ok=bool(f and f["A"]>0 and f["b"]<0 and M5 in varlog)
            p3.append(dict(root=root,geom=geom,btag=btag,horizon=hname,range=tag,
                n_grid=len(Ms),grid=";".join(map(str,Ms)),
                c=f["c"] if f else np.nan,A=f["A"] if f else np.nan,
                b=f["b"] if f else np.nan,rmse=f["rmse"] if f else np.nan,
                M_5min=M5,var_log_rv_at_M5=varlog.get(M5,np.nan),
                lam_intercept=(f["c"]/varlog[M5]) if ok else np.nan,
                lam_theory=(f["c"]/(f["c"]+trig(M5))) if ok else np.nan,
                valid=ok,note=("" if ok else ("single grid point, fit undefined"
                    if f is None and len(Ms)<4 else "invalid fit"))))
    P3=pd.DataFrame(p3); P3.to_csv(os.path.join(RES,"phase3_sizing_params.csv"),index=False)
    # equivalence: the extended fit must reproduce S08 phase4_fits.csv
    S8=pd.read_csv(os.path.join(S08,"results","phase4_fits.csv"))
    e=P3[P3.range=="extended"].merge(S8,on=["root","geom","btag","horizon"],
                                     suffixes=("_s09","_s08"))
    e["dc"]=(e.c_s09-e.c_s08).abs(); e["db"]=(e.b_s09-e.b_s08).abs()
    e[["root","geom","btag","horizon","c_s09","c_s08","dc","b_s09","b_s08","db"]].to_csv(
        os.path.join(RES,"phase3_s08_equivalence.csv"),index=False)
    print(f"S08 equivalence: max|dc|={e.dc.max():.3e} max|db|={e.db.max():.3e} n={len(e)}",flush=True)
    timers["phase3"]=round(time.time()-t0,1)
    print(P3[["root","geom","btag","horizon","range","n_grid","c","b","lam_intercept","lam_theory","valid","note"]].to_string(index=False),flush=True)
    # ---------------- PHASE 4
    t=time.time(); seeds=[int(s) for s in np.random.SeedSequence(SEEDS_MASTER).generate_state(N_SEEDS)]
    prof_cache={}
    rows=[]
    for root,geom,btag,hname in CELLS:
        if hname!="1day" or btag!="B0": continue   # daily rebalance; c is B-invariant
        sub=P3[(P3.root==root)&(P3.geom==geom)&(P3.btag==btag)&(P3.horizon==hname)]
        M5=FIVEMIN[(geom,hname)]
        rw,kw,px=cell_windows(root,geom,btag,hname)
        S,L=rw.shape
        if geom not in prof_cache:
            zz=np.load(os.path.join(S06,"cache",f"panel_ohlc_ES_{geom}.npz"))
            r1=np.diff(zz["close"].astype(np.float64),axis=1)
            pr=(r1**2).mean(axis=0); prof_cache[geom]=pr/pr.mean()
        prof=prof_cache[geom][:L]; prof=prof/prof.mean()
        ext=sub[sub.range=="extended"].iloc[0]
        var_log_iv=float(ext.c)
        sigj=0.0466 if geom=="GLOBEX" else 0.0353
        for si,sd in enumerate(seeds):
          for arm in ARMS:
            rng=np.random.Generator(np.random.PCG64(sd))
            if arm=="A2":
                x=rng.normal(0.0,np.sqrt(var_log_iv),size=S)
            else:
                emb=CirculantEmbedding(fgn_acf(H_ROUGH,np.arange(S)))
                x=emb.sample(rng,size=1)[0]
                x=x/x.std()*np.sqrt(var_log_iv)
            iv=np.exp(x); sv=np.outer(iv/L,prof)
            r=rng.standard_normal((S,L))*np.sqrt(sv)
            nj=rng.poisson(JUMP_INTENSITY,size=S); tot=int(nj.sum())
            if tot:
                np.add.at(r,(np.repeat(np.arange(S),nj),rng.integers(0,L,size=tot)),
                          rng.normal(0.0,sigj,size=tot))
            iv_true=sv.sum(axis=1)
            e=(np.arange(M5+1)*L)//M5
            cs=np.concatenate([np.zeros((S,1)),np.cumsum(r,axis=1)],axis=1)
            sb=cs[:,e[1:]]-cs[:,e[:-1]]; rv5=(sb**2).sum(axis=1)
            F,warm=har_forecast(rv5,1)
            mu=float(np.log(rv5[:warm][rv5[:warm]>0]).mean())
            np.savez_compressed(os.path.join(CACHE,f"sim_{arm}_{root}_{geom}_s{si}.npz"),
                iv_true=iv_true,rv5=rv5,F=F,x=x,seed=sd,warm=warm)
            for rng_tag in ["restricted_S05","extended"]:
                rr=sub[sub.range==rng_tag]
                if not len(rr) or not bool(rr.iloc[0].valid): continue
                lam_t=float(rr.iloc[0].lam_theory); lam_m=float(rr.iloc[0].lam_intercept)
                for rule,lam,fc in [("R0",None,iv_true),("R1",None,F),
                                    ("R2",lam_t,F),("R3",lam_m,F)]:
                    sc=size_and_score(iv_true,fc,lam,mu,TICKVAL[root],MULT[root],px)
                    rows.append(dict(root=root,geom=geom,btag=btag,horizon=hname,arm=arm,
                        range=rng_tag,rule=rule,seed_index=si,seed=sd,
                        lam_used=(lam if lam is not None else np.nan),
                        lam_in_unit=bool(lam is None or 0.0<lam<=1.0),**sc))
    P4=pd.DataFrame(rows); P4.to_csv(os.path.join(RES,"phase4_sizing_raw.csv"),index=False)
    agg=P4.groupby(["arm","root","geom","range","rule"]).agg(
        te_mean=("te","mean"),te_sd=("te","std"),turnover_mean=("turnover","mean"),
        turnover_sd=("turnover","std"),**{f"cost_{t}t":(f"{t}t","mean") for t in TICKS},
        lam_in_unit=("lam_in_unit","all"),n_seeds=("seed","nunique")).reset_index()
    agg.to_csv(os.path.join(RES,"phase4_sizing_agg.csv"),index=False)
    # --- item 71 input: R2 vs R3 relative TE difference, per cell / arm / range
    k=agg[agg.rule.isin(["R2","R3"])].pivot_table(
        index=["arm","root","geom","range"],columns="rule",
        values=["te_mean"]+[f"cost_{t}t" for t in TICKS]).reset_index()
    k.columns=["_".join([c for c in col if c]) for col in k.columns]
    k["rel_te_diff_pct"]=100*(k.te_mean_R2-k.te_mean_R3).abs()/k.te_mean_R2
    for tk in TICKS:
        a,b=f"cost_{tk}t_R2",f"cost_{tk}t_R3"
        k[f"rel_netcost_diff_pct_{tk}t"]=100*(k[a]-k[b]).abs()/k[a]
    k.to_csv(os.path.join(RES,"phase4_r2_vs_r3.csv"),index=False)
    print(); print(k.to_string(index=False),flush=True)
    timers["phase4"]=round(time.time()-t,1)
    json.dump(dict(timers=timers,seeds=seeds,master=SEEDS_MASTER,
                   target_ann=TARGET_ANN,ticks=TICKS,tickval=TICKVAL,mult=MULT),
              open(os.path.join(RES,"phase34_meta.json"),"w"),indent=1)
    print(); print(agg.to_string(index=False))
    print(f"PHASE3+4 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
