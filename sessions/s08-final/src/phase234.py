"""S08 Phases 2, 3 and 4: MCS rerun, K2 determination, intercept route to lambda."""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy.optimize import curve_fit
from scipy.special import polygamma
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
S06=os.path.join(ROOT,"sessions","s06r-repair"); S07=os.path.join(ROOT,"sessions","s07-completion-and-spy")
S05R=os.path.join(ROOT,"sessions","s05-reliability-mcs","results")
sys.path.insert(0,os.path.join(S06,"tests")); sys.path.insert(0,os.path.join(S07,"src"))
sys.path.insert(0,os.path.join(ROOT,"sessions","s05-reliability-mcs","src"))
sys.path.insert(0,os.path.join(ROOT,"sessions","s02-mechanism-expansion","src"))
from test_invariants import assert_loss_finite, assert_lambda_in_unit, InvariantViolation
import partde as pd5, estimators2 as e2mod
from parta import quart_suite
from phase2_rerun8 import series, HOR
MODELS=pd5.MODELS; BOOT_N=10000; MASTER=20260819; QS=[0.80,0.90]; NBOOT_C=500
CELLS=[(r,g,b,h) for g in ["GLOBEX","RTH"] for r in ["ES","NQ"]
       for b in ["B0","B1"] for h in ["1day","1h","30min"]]
RG_UNAVAIL={f"{r}/GLOBEX/{b}/{h}" for r in ["ES","NQ"] for b in ["B0","B1"] for h in ["1h","30min"]}
PARK_UNAVAIL={"ES/GLOBEX/B0/30min","NQ/GLOBEX/B0/30min"}
GRID={("RTH","1day"):[5,6,10,13,26,78,195,389],("RTH","1h"):[4,5,6,10,12,15,20,30,60],
      ("RTH","30min"):[5,6,10,15,30],("GLOBEX","1day"):[5,6,10,12,23,46,138,276,345,1379]}
FIVEMIN={("RTH","1day"):78,("RTH","1h"):12,("RTH","30min"):6,("GLOBEX","1day"):276}
def trig(M): return float(polygamma(1,M/2.0))
def fitf(M,y):
    M=np.asarray(M,float); y=np.asarray(y,float); ok=np.isfinite(y)
    if ok.sum()<4: return None
    try:
        p,_=curve_fit(lambda x,c,A,b: c+A*np.power(x,b),M[ok],y[ok],
                      p0=[y[ok].min(),1.0,-0.5],maxfev=80000)
        pred=p[0]+p[1]*np.power(M[ok],p[2])
        return dict(c=float(p[0]),A=float(p[1]),b=float(p[2]),
                    rmse=float(np.sqrt(np.mean((y[ok]-pred)**2))))
    except Exception: return None
def mcs_seeded(losses,seed,models):
    T,m=losses.shape; b=int(np.ceil(T**(1/3))); nb=int(np.ceil(T/b))
    cs=np.vstack([np.zeros(m),np.cumsum(losses,axis=0)]); bs=cs[b:]-cs[:-b]
    rng=np.random.Generator(np.random.PCG64(seed)); boot=np.empty((BOOT_N,m)); d=0
    while d<BOOT_N:
        k=min(1000,BOOT_N-d); st=rng.integers(0,T-b+1,size=(k,nb))
        boot[d:d+k]=bs[st].sum(axis=1)/(nb*b); d+=k
    means=losses.mean(axis=0); inc=list(range(m)); pv={}; pr=0.0
    while len(inc)>1:
        idx=np.array(inc); mu=means[idx]; bm=boot[:,idx]-mu[None,:]
        db_=mu[:,None]-mu[None,:]; bd=bm[:,:,None]-bm[:,None,:]
        vd=np.maximum(bd.var(axis=0),1e-30); TR=(np.abs(db_)/np.sqrt(vd)).max()
        TRb=(np.abs(bd)/np.sqrt(vd)[None,:,:]).reshape(BOOT_N,-1).max(axis=1)
        p=float((TRb>=TR).mean()); pr=max(pr,p)
        w=inc[int(np.argmax((db_/np.sqrt(vd)).sum(axis=1)))]; pv[w]=pr; inc.remove(w)
    pv[inc[0]]=1.0
    return {models[i]:p for i,p in pv.items()}
def subbars_masked(rw,kw,M):
    N,L=rw.shape; e=(np.arange(M+1)*L)//M
    cs=np.concatenate([np.zeros((N,1)),np.cumsum(rw,axis=1)],axis=1)
    sb=cs[:,e[1:]]-cs[:,e[:-1]]
    kc=np.concatenate([np.zeros((N,1)),np.cumsum(kw.astype(np.int32),axis=1)],axis=1)
    kb=kc[:,e[1:]]-kc[:,e[:-1]]
    return sb,(kb>0).sum(axis=1).astype(float)
def main():
    t0=time.time(); timers={}
    # ================= PHASE 4 first (lambda feeds the Phase 2 metrics)
    t=time.time(); lam_rows=[]; fit_rows=[]
    rng_c=np.random.Generator(np.random.PCG64(MASTER))
    for root,geom,btag in [(r,g,b) for g in ["GLOBEX","RTH"] for r in ["ES","NQ"] for b in ["B0","B1"]]:
        for (g2,hname),Ms in GRID.items():
            if g2!=geom: continue
            S=series(root,geom,btag,HOR[hname])
            z=np.load(os.path.join(S06,"cache",f"panel_ohlc_{root}_{geom}.npz"))
            cl=z["close"].astype(np.float64); pres=z["present"]
            tr=np.load(os.path.join(S07,"cache") if False else os.path.join(S06,"cache"),
                       allow_pickle=False) if False else None
            from phase2_rerun8 import tradeable_ext
            trm,_=tradeable_ext(root,geom)
            r1=np.diff(cl,axis=1); keep=trm[:,1:]&trm[:,:-1]&pres[:,1:]&pres[:,:-1]
            r1=np.where(trm[:,1:]&trm[:,:-1],r1,0.0)
            wl=HOR[hname]
            if wl is None: rw,kw=r1,keep
            else:
                nw=r1.shape[1]//wl; rw=r1[:,:nw*wl].reshape(-1,wl); kw=keep[:,:nw*wl].reshape(-1,wl)
            live=kw.any(axis=1); rw,kw=rw[live],kw[live]
            per_M={}; Ms_used=[]; varlogs=[]
            logrv_by_M={}
            for M in Ms:
                if M>rw.shape[1]: continue
                sb,meff=subbars_masked(rw,kw,M)
                q=quart_suite(sb,M); rq,rv=q["RQ_RV"]; trq,trv=q["TRQ3_TRV3"]
                pos=rv>0; logp=np.log(np.maximum(rv,1e-300))
                h=M//2; p1=(sb[:,:h]**2).sum(axis=1); p2=(sb[:,h:]**2).sum(axis=1)
                lam2=float(e2mod.e2(logp[pos],np.log(np.maximum(p1[pos],1e-300)),
                                    np.log(np.maximum(p2[pos],1e-300))))
                v=(2.0/np.maximum(meff[pos],1.0))*trq[pos]/np.maximum(trv[pos]**2,1e-300)
                lam4=float(1.0-np.mean(v)/np.log(np.maximum(trv[pos],1e-300)).var())
                vlog=float(logp[pos].var())
                per_M[M]=dict(lam_E2=lam2,lam_E4=lam4,var_log_rv=vlog,n=int(pos.sum()),
                              mean_eff_M=float(meff.mean()))
                logrv_by_M[M]=logp[pos]; Ms_used.append(M); varlogs.append(vlog)
            f=fitf(Ms_used,varlogs)
            valid=bool(f and f["A"]>0 and f["b"]<0)
            # bootstrap CI on c over sessions
            cis=[]
            if valid:
                n=min(len(v) for v in logrv_by_M.values())
                arr=np.column_stack([logrv_by_M[M][:n] for M in Ms_used])
                for _ in range(NBOOT_C):
                    idx=rng_c.integers(0,n,size=n)
                    fb=fitf(Ms_used,arr[idx].var(axis=0))
                    if fb and fb["A"]>0 and fb["b"]<0: cis.append(fb["c"])
            fit_rows.append(dict(root=root,geom=geom,btag=btag,horizon=hname,
                c=f["c"] if f else np.nan,A=f["A"] if f else np.nan,
                b=f["b"] if f else np.nan,rmse=f["rmse"] if f else np.nan,
                valid=valid,n_boot=len(cis),
                c_lo=float(np.percentile(cis,2.5)) if len(cis)>20 else np.nan,
                c_hi=float(np.percentile(cis,97.5)) if len(cis)>20 else np.nan,
                invalid_reason=("" if valid else ("no fit" if not f else
                    f"A={f['A']:.3g}<=0" if f["A"]<=0 else f"b={f['b']:.3g}>=0"))))
            for M,d in per_M.items():
                lam_int=(f["c"]/d["var_log_rv"]) if valid else np.nan
                lam_rows.append(dict(root=root,geom=geom,btag=btag,horizon=hname,M=M,
                    lam_E2=d["lam_E2"],lam_E4=d["lam_E4"],lam_intercept=lam_int,
                    var_log_rv=d["var_log_rv"],n=d["n"],mean_eff_M=d["mean_eff_M"],
                    trigamma=trig(M),
                    lam_theory=(f["c"]/(f["c"]+trig(M))) if valid else np.nan,
                    is_five_min_equiv=(M==FIVEMIN.get((geom,hname)))))
    LAM=pd.DataFrame(lam_rows); LAM.to_csv(os.path.join(RES,"phase4_lambda.csv"),index=False)
    FIT=pd.DataFrame(fit_rows); FIT.to_csv(os.path.join(RES,"phase4_fits.csv"),index=False)
    viol=dict(E2=int(((LAM.lam_E2<0)|(LAM.lam_E2>1)).sum()),
              E4=int(((LAM.lam_E4<0)|(LAM.lam_E4>1)).sum()),
              intercept=int(((LAM.lam_intercept<0)|(LAM.lam_intercept>1)).sum()),
              n_rows=len(LAM))
    F5=LAM[LAM.is_five_min_equiv].copy()
    F5["gap_measured_minus_theory"]=F5.lam_intercept-F5.lam_theory
    F5["shrinkage_weight_measured"]=F5.lam_intercept
    F5["shrinkage_weight_theory"]=F5.lam_theory
    F5["pct_diff_position_variability"]=100*(F5.lam_intercept/F5.lam_theory-1)
    F5.to_csv(os.path.join(RES,"phase4_five_minute.csv"),index=False)
    json.dump(viol,open(os.path.join(RES,"phase4_bound_violations.json"),"w"),indent=1)
    timers["phase4"]=round(time.time()-t,1)
    print("bound violations:",viol,flush=True)
    print(F5[["root","geom","btag","horizon","M","lam_intercept","lam_theory",
              "gap_measured_minus_theory","pct_diff_position_variability"]].to_string(index=False),flush=True)
    # ================= PHASE 2: MCS
    t=time.time(); mcs_rows=[]; met_rows=[]; halts=[]
    for ci,c in enumerate(CELLS):
        p=os.path.join(CACHE,f"gen_{c[0]}_{c[1]}_{c[2]}_{c[3]}.npz")
        if not os.path.exists(p): continue
        root,geom,btag,hname=c; cell="/".join(c)
        z=np.load(p); L=z["L"]; rvv=z["rvv"]
        mods=[m for m in MODELS if not (m=="M5_RGARCH" and cell in RG_UNAVAIL)
              and not (m=="M6_PARK" and cell in PARK_UNAVAIL)]
        keep=[MODELS.index(m) for m in mods]; La=L[:,keep]
        Fm={m:z[f"F_{m}"] for m in mods}
        lam={}
        for est,col in [("E2","lam_E2"),("E4","lam_E4"),("INT","lam_intercept")]:
            s=LAM[(LAM.root==root)&(LAM.geom==geom)&(LAM.btag==btag)&(LAM.horizon==hname)]
            lam[est]=float(s[s.M==s.M.max()][col].iloc[0]) if len(s) else np.nan
        sch={"S-A":np.ones(len(rvv),bool)}
        for q in QS:
            sch[f"S-B_q{q:.2f}"]=rvv>np.quantile(rvv,q)
            sch[f"S-C_q{q:.2f}"]=Fm["M2_HAR"]>np.quantile(Fm["M2_HAR"],q)
        for si,(sn,mk) in enumerate(sch.items()):
            Ls=La[mk]
            try: assert_loss_finite(Ls,f"{cell}/{sn}",mods)
            except InvariantViolation as e:
                halts.append(dict(cell=cell,scheme=sn,message=str(e)))
                mcs_rows.append(dict(root=root,geom=geom,btag=btag,horizon=hname,scheme=sn,
                    n_obs=int(mk.sum()),model_set="|".join(mods),mcs75="HALTED",mcs90="HALTED",seed=-1))
                continue
            seed=int(np.random.SeedSequence([MASTER,ci,si]).generate_state(1)[0])
            pv=mcs_seeded(Ls,seed,mods)
            mcs_rows.append(dict(root=root,geom=geom,btag=btag,horizon=hname,scheme=sn,
                n_obs=int(mk.sum()),model_set="|".join(mods),
                mcs75="|".join(sorted(m for m,x in pv.items() if x>.25)),
                mcs90="|".join(sorted(m for m,x in pv.items() if x>.10)),seed=seed,
                pvals=json.dumps({m:round(x,4) for m,x in pv.items()})))
            lrv=np.log(rvv[mk])
            for m in mods:
                lf=np.log(Fm[m][mk]); ic=float(np.corrcoef(lf,lrv)[0,1])
                r2=float(1-((lrv-lf)**2).sum()/((lrv-lrv.mean())**2).sum())
                w=63; ics=[np.corrcoef(lf[i:i+w],lrv[i:i+w])[0,1] for i in range(0,len(lrv)-w,w)]
                ics=[x for x in ics if np.isfinite(x)]
                ir=float(np.mean(ics)/np.std(ics)) if len(ics)>2 and np.std(ics)>0 else np.nan
                row=dict(root=root,geom=geom,btag=btag,horizon=hname,scheme=sn,model=m,
                    n=int(mk.sum()),ic_pearson_log=ic,r2_oos=r2,ic_ir=ir,
                    ic_ir_n_blocks=len(ics),ic_ir_block_len_windows=w,
                    hit_rate=float((np.sign(np.diff(lf))==np.sign(np.diff(lrv))).mean()),
                    qlike_mean=float(pd5.qlike(Fm[m][mk],rvv[mk]).mean()))
                for est in ["E2","E4","INT"]:
                    lv=lam[est]
                    row[f"lam_{est}"]=lv
                    row[f"ic_corrected_{est}"]=ic/np.sqrt(lv) if lv==lv and lv>0 else np.nan
                    row[f"r2_corrected_{est}"]=r2/lv if lv==lv and lv>0 else np.nan
                met_rows.append(row)
        np.savez_compressed(os.path.join(CACHE,f"loss_{root}_{geom}_{btag}_{hname}.npz"),
            L=La,models=np.array(mods),**{f"mask_{k}":v for k,v in sch.items()})
    MC=pd.DataFrame(mcs_rows); MC.to_csv(os.path.join(RES,"phase2_mcs.csv"),index=False)
    pd.DataFrame(met_rows).to_csv(os.path.join(RES,"phase2_metrics.csv"),index=False)
    pd.DataFrame(halts).to_csv(os.path.join(RES,"phase2_halts.csv"),index=False)
    timers["phase2"]=round(time.time()-t,1)
    # ================= PHASE 3: K2
    prim=[]
    for c in CELLS:
        root,geom,btag,hname=c; base="/".join(c)
        for q in QS:
            for lev in ["mcs75","mcs90"]:
                b=MC[(MC.root==root)&(MC.geom==geom)&(MC.btag==btag)&(MC.horizon==hname)&(MC.scheme==f"S-B_q{q:.2f}")]
                cc=MC[(MC.root==root)&(MC.geom==geom)&(MC.btag==btag)&(MC.horizon==hname)&(MC.scheme==f"S-C_q{q:.2f}")]
                if not len(b) or not len(cc):
                    prim.append(dict(cell=base,root=root,geom=geom,btag=btag,horizon=hname,
                        quantile=q,level=lev,differs=None,status="NOT RUN")); continue
                bv,cv=b[lev].iloc[0],cc[lev].iloc[0]
                if bv=="HALTED" or cv=="HALTED":
                    prim.append(dict(cell=base,root=root,geom=geom,btag=btag,horizon=hname,
                        quantile=q,level=lev,differs=None,status="HALTED")); continue
                prim.append(dict(cell=base,root=root,geom=geom,btag=btag,horizon=hname,
                    quantile=q,level=lev,differs=bool(bv!=cv),s_b=bv,s_c=cv,status="ok"))
    PR=pd.DataFrame(prim); PR.to_csv(os.path.join(RES,"phase3_primary.csv"),index=False)
    ok=PR[PR.status=="ok"]; rth=ok[ok.geom=="RTH"]
    strat=[]
    for dim in ["horizon","root","geom","quantile"]:
        for k,g in ok.groupby(dim):
            strat.append(dict(dimension=dim,level=str(k),n=len(g),n_differ=int(g.differs.sum()),
                              share=float(g.differs.mean())))
    pd.DataFrame(strat).to_csv(os.path.join(RES,"phase3_stratified.csv"),index=False)
    rate_all=float(ok.differs.mean()) if len(ok) else np.nan
    rate_rth=float(rth.differs.mean()) if len(rth) else np.nan
    pre=ok[ok.cell=="ES/RTH/B0/30min"]; med=ok[ok.cell=="ES/RTH/B1/1h"]
    k2=("FIRES" if (rate_rth<=0.15 and int(pre.differs.sum())==0 and int(med.differs.sum())==0)
        else "DOES NOT FIRE" if rate_rth>0.25 else "INDETERMINATE")
    summ=dict(family_preregistered=96,n_computed=len(ok),n_halted=int((PR.status=="HALTED").sum()),
        n_differ=int(ok.differs.sum()),rate_all=rate_all,
        n_rth=len(rth),n_differ_rth=int(rth.differs.sum()),rate_rth=rate_rth,
        prereg_cell="ES/RTH/B0/30min",prereg_n_differ=int(pre.differs.sum()),prereg_n=len(pre),
        median_cell="ES/RTH/B1/1h",median_n_differ=int(med.differs.sum()),median_n=len(med),
        differing_cells=ok[ok.differs].cell.unique().tolist(),
        K2=k2,bound_violations=viol,timers=timers)
    json.dump(summ,open(os.path.join(RES,"phase3_k2.json"),"w"),indent=1,default=str)
    print(json.dumps({k:v for k,v in summ.items() if k!="differing_cells"},indent=1,default=str))
    print("K2:",k2)
if __name__=="__main__": main()
