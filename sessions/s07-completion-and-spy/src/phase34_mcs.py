"""S07 Phases 3 and 4: RGARCH on the 8 failed cells; MCS across the full family."""
import json, os, sys, time
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
S06=os.path.join(ROOT,"sessions","s06r-repair")
S06C,S06R_=os.path.join(S06,"cache"),os.path.join(S06,"results")
S05R=os.path.join(ROOT,"sessions","s05-reliability-mcs","results")
sys.path.insert(0,os.path.join(S06,"tests"))
sys.path.insert(0,os.path.join(ROOT,"sessions","s05-reliability-mcs","src"))
sys.path.insert(0,os.path.join(BASE,"src"))
from test_invariants import assert_loss_finite, InvariantViolation
import partde as pd5
from phase2_rerun8 import series, run_cell, HOR
MODELS=pd5.MODELS; BOOT_N=10000; MASTER=20260819; QS=[0.80,0.90]
CELLS=[(r,g,b,h) for g in ["GLOBEX","RTH"] for r in ["ES","NQ"]
       for b in ["B0","B1"] for h in ["1day","1h","30min"]]
CELLS8=[(r,g,b,h) for r in ["ES","NQ"] for b in ["B0","B1"] for h in ["1h","30min"]
        for g in ["GLOBEX"]]
def gpath(c):
    p=os.path.join(CACHE,f"gen_{c[0]}_{c[1]}_{c[2]}_{c[3]}.npz")
    return p if os.path.exists(p) else os.path.join(S06C,f"gen_{c[0]}_{c[1]}_{c[2]}_{c[3]}.npz")
def theta_path(job):
    root,geom,btag,hname=job; cell=f"{root}/{geom}/{btag}/{hname}"
    z=np.load(gpath(job)); rv=z["rv"]; D=int(z["D"]); warm=int(z["warm"]); start=int(z["start"])
    ret=z["ret"] if "ret" in z.files else series(root,geom,btag,HOR[hname])["ret"]
    logx=np.log(np.maximum(rv,1e-300))
    th=np.array([0.1,0.7,0.25,-0.1,1.0,-0.05,0.05,np.log(0.4)]); out=[]
    for t in range(max(start,warm),len(rv),63*D):
        th,_,ok=pd5.rgarch_fit_forecast(ret[:t],logx[:t],th)
        out.append(dict(cell=cell,t=int(t),converged=bool(ok),om=float(th[0]),
            beta=float(th[1]),gamma=float(th[2]),xi=float(th[3]),phi=float(th[4]),
            tau1=float(th[5]),tau2=float(th[6]),log_sigma_u=float(th[7]),
            persistence=float(th[1]+th[2]*th[4])))
    return out
def mcs_seeded(losses,seed,models):
    T,m=losses.shape; b=int(np.ceil(T**(1/3))); nblk=int(np.ceil(T/b))
    cs=np.vstack([np.zeros(m),np.cumsum(losses,axis=0)]); bs=cs[b:]-cs[:-b]
    rng=np.random.Generator(np.random.PCG64(seed)); boot=np.empty((BOOT_N,m)); d=0
    while d<BOOT_N:
        k=min(1000,BOOT_N-d); st=rng.integers(0,T-b+1,size=(k,nblk))
        boot[d:d+k]=bs[st].sum(axis=1)/(nblk*b); d+=k
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
def main():
    t0=time.time(); timers={}
    # ---- regenerate the 4 GLOBEX 1day cells under the extended exclusion
    t=time.time(); g1=[("ES","GLOBEX","B0","1day"),("ES","GLOBEX","B1","1day"),
                       ("NQ","GLOBEX","B0","1day"),("NQ","GLOBEX","B1","1day")]
    todo=[c for c in g1 if not os.path.exists(os.path.join(CACHE,f"gen_{c[0]}_{c[1]}_{c[2]}_{c[3]}.npz"))]
    if todo:
        with ProcessPoolExecutor(max_workers=4) as ex:
            for m,fr in ex.map(run_cell,todo): print("  regen",m["cell"],flush=True)
    timers["regen_globex_1day"]=round(time.time()-t,1)
    # ---- Phase 3: RGARCH theta on the 8
    t=time.time(); th=[]
    avail=[c for c in CELLS8 if os.path.exists(os.path.join(CACHE,f"gen_{c[0]}_{c[1]}_{c[2]}_{c[3]}.npz"))]
    with ProcessPoolExecutor(max_workers=5) as ex:
        for o in ex.map(theta_path,avail): th.extend(o)
    TH=pd.DataFrame(th); TH.to_csv(os.path.join(RES,"phase3_rgarch_params.csv"),index=False)
    diag=[]
    for cell,g in TH.groupby("cell"):
        parts=cell.split("/"); z=np.load(os.path.join(CACHE,f"gen_{parts[0]}_{parts[1]}_{parts[2]}_{parts[3]}.npz"))
        if "F_M5_RGARCH" not in z.files: continue
        F=z["F_M5_RGARCH"]; rvv=z["rvv"]; mean_rv=float(rvv.mean()); D=int(z["D"])
        nonpos=int((F<=0).sum()); huge=int((F>100*mean_rv).sum())
        pos_orig=np.where(z["ok"])[0]; bad=pos_orig[(F>100*mean_rv)|(F<=0)]
        near=int(np.sum([(i-int(z["warm"]))%(63*D)<D for i in bad])) if len(bad) else 0
        pers=g.persistence.values; nonstat=bool(np.nanmax(np.abs(pers))>=1.0)
        st=[str(x) for x in z["models"]] if "models" in z.files else list(MODELS)
        in_set=("M5_RGARCH" in st)
        diag.append(dict(cell=cell,n_refits=len(g),n_converged=int(g.converged.sum()),
            persistence_mean=float(np.nanmean(pers)),persistence_max=float(np.nanmax(pers)),
            violates_stationarity=nonstat,omega_free="YES (no variance targeting in partde.rgarch_ll)",
            beta_last=float(g.iloc[-1].beta),gamma_last=float(g.iloc[-1].gamma),
            phi_last=float(g.iloc[-1].phi),omega_last=float(g.iloc[-1].om),
            n_nonpositive=nonpos,n_above_100x=huge,n_eval=int(len(F)),
            share_pathological=float((nonpos+huge)/max(len(F),1)),
            n_pathological_within_D_of_refit=near,
            divergence_at_refit_boundary=bool(len(bad) and near/max(len(bad),1)>0.5),
            retained_in_model_set=in_set,
            verdict=("RGARCH-UNAVAILABLE (non-stationary parameters)" if nonstat
                     else "RGARCH-UNAVAILABLE (non-positive forecasts; dropped from the model set in Phase 2)" if not in_set
                     else "RESOLVED BY PHASE 2 (stationary, no pathological forecasts)"
                     if (nonpos+huge)==0 else
                     "RGARCH-UNAVAILABLE (divergent forecasts, stationary parameters)")))
    D3=pd.DataFrame(diag); D3.to_csv(os.path.join(RES,"phase3_rgarch_diagnosis.csv"),index=False)
    UNAVAIL=set(D3[D3.verdict.str.startswith("RGARCH-UNAVAILABLE")].cell)
    timers["phase3"]=round(time.time()-t,1)
    # ---- Phase 4: MCS across all cells
    t=time.time(); eff=[]
    for c in CELLS:
        p=gpath(c)
        if os.path.exists(p): eff.append(dict(cell="/".join(c),n_eval=int(np.load(p)["ok"].sum()),
                                              source=("S07" if CACHE in p else "S06R")))
    EFF=pd.DataFrame(eff).sort_values(["n_eval","cell"],ascending=[False,True])
    EFF.to_csv(os.path.join(RES,"phase4_effective_samples.csv"),index=False)
    med_idx=len(EFF)//2; MEDCELL=EFF.iloc[med_idx]["cell"]
    json.dump(dict(criterion_preregistered_S06R="largest effective sample",
        cell_preregistered="ES/RTH/B0/30min",
        criterion_second="median effective sample (post hoc, item 54)",
        cell_median=MEDCELL,n_eval=int(EFF.iloc[med_idx]["n_eval"]),
        logged_before_comparison=True),
        open(os.path.join(RES,"phase4_cells_prespecified.json"),"w"),indent=1)
    print("MEDIAN-EFFECTIVE-SAMPLE CELL (logged before comparison):",MEDCELL,flush=True)
    mcs_rows=[]; halts=[]
    for ci,c in enumerate(CELLS):
        p=gpath(c)
        if not os.path.exists(p): continue
        root,geom,btag,hname=c; cell="/".join(c)
        z=np.load(p); L=z["L"]; rvv=z["rvv"]
        # the stored model set may already be reduced (item 41 handling in
        # Phase 2); L's columns follow it, not the full MODELS list
        stored=[str(x) for x in z["models"]] if "models" in z.files else list(MODELS)
        mods=[m for m in stored if not (m=="M5_RGARCH" and cell in UNAVAIL)]
        keep=[stored.index(m) for m in mods]; La=L[:,keep]
        Fm={m:z[f"F_{m}"] for m in mods}
        sch={"S-A":np.ones(len(rvv),bool)}
        for q in QS:
            sch[f"S-B_q{q:.2f}"]=rvv>np.quantile(rvv,q)
            sch[f"S-C_q{q:.2f}"]=Fm["M2_HAR"]>np.quantile(Fm["M2_HAR"],q)
        for si,(sn,mk) in enumerate(sch.items()):
            Ls=La[mk]
            try: assert_loss_finite(Ls,f"{cell}/{sn}",mods)
            except InvariantViolation as e:
                halts.append(dict(cell=cell,scheme=sn,message=str(e)))
                mcs_rows.append(dict(root=root,geom=geom,btag=btag,horizon=hname,
                    scheme=sn,n_obs=int(mk.sum()),model_set="|".join(mods),
                    mcs75="HALTED",mcs90="HALTED",seed=-1)); continue
            seed=int(np.random.SeedSequence([MASTER,ci,si]).generate_state(1)[0])
            pv=mcs_seeded(Ls,seed,mods)
            mcs_rows.append(dict(root=root,geom=geom,btag=btag,horizon=hname,scheme=sn,
                n_obs=int(mk.sum()),model_set="|".join(mods),
                mcs75="|".join(sorted(m for m,x in pv.items() if x>.25)),
                mcs90="|".join(sorted(m for m,x in pv.items() if x>.10)),seed=seed,
                pvals=json.dumps({m:round(x,4) for m,x in pv.items()})))
        np.savez_compressed(os.path.join(CACHE,f"loss_{root}_{geom}_{btag}_{hname}.npz"),
            L=La,models=np.array(mods),**{f"mask_{k}":v for k,v in sch.items()})
    MC=pd.DataFrame(mcs_rows); MC.to_csv(os.path.join(RES,"phase4_mcs.csv"),index=False)
    pd.DataFrame(halts).to_csv(os.path.join(RES,"phase4_halts.csv"),index=False)
    timers["phase4_mcs"]=round(time.time()-t,1)
    # ---- S-B vs S-C, full family
    prim=[]
    for c in CELLS:
        base="/".join(c); root,geom,btag,hname=c
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
    PR=pd.DataFrame(prim); PR.to_csv(os.path.join(RES,"phase4_primary.csv"),index=False)
    okr=PR[PR.status=="ok"]
    strat=[]
    for dim in ["horizon","root","geom","quantile"]:
        for k,g in okr.groupby(dim):
            strat.append(dict(dimension=dim,level=str(k),n=len(g),
                n_differ=int(g.differs.sum()),share=float(g.differs.mean())))
    pd.DataFrame(strat).to_csv(os.path.join(RES,"phase4_stratified.csv"),index=False)
    summ=dict(family_preregistered=96,n_computed=len(okr),
        n_halted=int((PR.status=="HALTED").sum()),n_not_run=int((PR.status=="NOT RUN").sum()),
        n_differ=int(okr.differs.sum()),
        cell_preregistered="ES/RTH/B0/30min",cell_median=MEDCELL,
        prereg_rows=okr[okr.cell=="ES/RTH/B0/30min"].to_dict("records"),
        median_rows=okr[okr.cell==MEDCELL].to_dict("records"),
        rgarch_unavailable=sorted(UNAVAIL),timers=timers)
    json.dump(summ,open(os.path.join(RES,"phase4_summary.json"),"w"),indent=1,default=str)
    print(json.dumps({k:v for k,v in summ.items() if not k.endswith("_rows")},indent=1,default=str))
    print("\nRGARCH:\n",D3[["cell","persistence_max","violates_stationarity","share_pathological","verdict"]].to_string(index=False))
    print("\nstratified:\n",pd.DataFrame(strat).to_string(index=False))
if __name__=="__main__": main()
