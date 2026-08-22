"""S06R Phases 4, 7 and 8: RGARCH diagnosis, MCS rerun, primary result."""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy.stats import spearmanr
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
RES, CACHE = os.path.join(BASE, "results"), os.path.join(BASE, "cache")
S05 = os.path.join(ROOT, "sessions", "s05-reliability-mcs", "results")
S05A = os.path.join(ROOT, "sessions", "s05a-reproducibility", "results")
sys.path.insert(0, os.path.join(BASE, "tests"))
sys.path.insert(0, os.path.join(ROOT, "sessions", "s05-reliability-mcs", "src"))
from test_invariants import assert_loss_finite, InvariantViolation
import partde as pd5
MODELS = pd5.MODELS
BOOT_N, MASTER, QS = 10000, 20260819, [0.80, 0.90]
CELLS = [(r,g,b,h) for g in ["GLOBEX","RTH"] for r in ["ES","NQ"]
         for b in ["B0","B1"] for h in ["1day","1h","30min"]]

def mcs_seeded(losses, seed, models):
    T, m = losses.shape
    b = int(np.ceil(T**(1/3))); nblk = int(np.ceil(T/b))
    csum = np.vstack([np.zeros(m), np.cumsum(losses, axis=0)])
    blocksum = csum[b:] - csum[:-b]
    rng = np.random.Generator(np.random.PCG64(seed))
    boot = np.empty((BOOT_N, m)); done = 0
    while done < BOOT_N:
        k = min(1000, BOOT_N-done)
        st = rng.integers(0, T-b+1, size=(k, nblk))
        boot[done:done+k] = blocksum[st].sum(axis=1)/(nblk*b); done += k
    means = losses.mean(axis=0); inc = list(range(m)); pv={}; pr=0.0
    while len(inc) > 1:
        idx=np.array(inc); mu=means[idx]; bm=boot[:,idx]-mu[None,:]
        dbar=mu[:,None]-mu[None,:]; bd=bm[:,:,None]-bm[:,None,:]
        vd=np.maximum(bd.var(axis=0),1e-30); TR=(np.abs(dbar)/np.sqrt(vd)).max()
        TRb=(np.abs(bd)/np.sqrt(vd)[None,:,:]).reshape(BOOT_N,-1).max(axis=1)
        p=float((TRb>=TR).mean()); pr=max(pr,p)
        worst=inc[int(np.argmax((dbar/np.sqrt(vd)).sum(axis=1)))]
        pv[worst]=pr; inc.remove(worst)
    pv[inc[0]]=1.0
    return {models[i]: p for i, p in pv.items()}

def main():
    t0=time.time(); timers={}
    # ================= PHASE 4: RGARCH diagnosis
    TH = pd.read_csv(os.path.join(RES,"phase4_rgarch_params.csv"))
    TH = TH.drop_duplicates(subset=["cell","t"])
    diag=[]
    for cell, g in TH.groupby("cell"):
        root,geom,btag,hname = cell.split("/")
        f=os.path.join(CACHE, f"gen_{root}_{geom}_{btag}_{hname}.npz")
        z=np.load(f); ok=z["ok"]; F=z["F_M5_RGARCH"]; rv=z["rv"]
        # F is stored already subset to the evaluation sample (length ok.sum())
        rvv=z["rvv"]; mean_rv=float(rvv.mean())
        nonpos=int((F<=0).sum()); huge=int((F>100*mean_rv).sum())
        pers=g.persistence.values
        last=g.iloc[-1]
        # divergence at a refit boundary?
        D=int(z["D"]); step=63*D
        pos_orig=np.where(ok)[0]
        bad_idx=pos_orig[(F>100*mean_rv)|(F<=0)]
        near=int(np.sum([(i - int(z["warm"])) % step < D for i in bad_idx])) if len(bad_idx) else 0
        nonstat = bool(np.nanmax(np.abs(pers))>=1.0)
        diag.append(dict(cell=cell, n_refits=len(g), n_converged=int(g.converged.sum()),
            persistence_mean=float(np.nanmean(pers)), persistence_max=float(np.nanmax(pers)),
            persistence_min=float(np.nanmin(pers)), violates_stationarity=nonstat,
            beta_last=float(last.beta), gamma_last=float(last.gamma), phi_last=float(last.phi),
            omega_last=float(last.om), xi_last=float(last.xi),
            variance_targeting="NOT APPLIED (partde.rgarch_ll has no targeting term)",
            n_nonpositive=nonpos, n_above_100x=huge, n_eval=int(len(F)),
            share_pathological=float((nonpos+huge)/max(int(len(F)),1)),
            n_pathological_within_D_of_refit=near,
            divergence_at_refit_boundary=bool(len(bad_idx) and near/max(len(bad_idx),1)>0.5),
            verdict=("RGARCH-UNAVAILABLE (non-stationary parameters)" if nonstat
                     else "estimated (stationary)" if (nonpos+huge)==0
                     else "RGARCH-UNAVAILABLE (divergent forecasts, stationary parameters)")))
    D4=pd.DataFrame(diag); D4.to_csv(os.path.join(RES,"phase4_rgarch_diagnosis.csv"),index=False)
    UNAVAIL=set(D4[D4.verdict.str.startswith("RGARCH-UNAVAILABLE")].cell)
    model_sets={}
    for c in D4.cell:
        model_sets[c]=[m for m in MODELS if not (m=="M5_RGARCH" and c in UNAVAIL)]
    pd.DataFrame([dict(cell=c, n_models=len(v), model_set="|".join(v),
                       rgarch_included=("M5_RGARCH" in v)) for c,v in model_sets.items()]
                 ).to_csv(os.path.join(RES,"phase4_model_sets.csv"),index=False)
    timers["phase4"]=round(time.time()-t0,1)

    # ================= PHASE 8 pre-registration: largest effective sample
    t=time.time()
    eff=[]
    for (root,geom,btag,hname) in CELLS:
        f=os.path.join(CACHE,f"gen_{root}_{geom}_{btag}_{hname}.npz")
        if not os.path.exists(f): continue
        z=np.load(f); eff.append(dict(cell=f"{root}/{geom}/{btag}/{hname}",
                                      n_eval=int(z["ok"].sum())))
    EFF=pd.DataFrame(eff).sort_values(["n_eval","cell"],ascending=[False,True])
    EFF.to_csv(os.path.join(RES,"phase8_effective_samples.csv"),index=False)
    PRIMARY=EFF.iloc[0]["cell"]
    json.dump(dict(criterion="largest effective sample, fixed before the comparison",
                   primary_cell=PRIMARY, n_eval=int(EFF.iloc[0]["n_eval"])),
              open(os.path.join(RES,"phase8_primary_cell.json"),"w"), indent=1)
    print("PRIMARY CELL (ex-ante, largest effective sample):", PRIMARY, flush=True)

    # ================= PHASE 7: MCS + metrics
    lam6=pd.read_csv(os.path.join(RES,"phase6_lambda.csv"))
    mcs_rows, met_rows, halts=[],[],[]
    for ci,(root,geom,btag,hname) in enumerate(CELLS):
        cell=f"{root}/{geom}/{btag}/{hname}"
        f=os.path.join(CACHE,f"gen_{root}_{geom}_{btag}_{hname}.npz")
        if not os.path.exists(f): continue
        z=np.load(f); L=z["L"]; rvv=z["rvv"]; ok=z["ok"]
        mods=model_sets.get(cell, MODELS)
        keep=[MODELS.index(m) for m in mods]
        Ls_all=L[:,keep]
        Fm={m: z[f"F_{m}"] for m in mods}
        lamc={}
        for est in ["E2","E4"]:
            s=lam6[(lam6.root==root)&(lam6.geom==geom)&(lam6.btag==btag)
                   &(lam6.horizon==hname)&(lam6.estimator==est)]
            lamc[est]=float(s[s.M==s.M.max()]["lam"].iloc[0]) if len(s) else np.nan
        schemes={"S-A": np.ones(len(rvv),bool)}
        for q in QS:
            schemes[f"S-B_q{q:.2f}"]=rvv>np.quantile(rvv,q)
            schemes[f"S-C_q{q:.2f}"]=Fm["M2_HAR"]>np.quantile(Fm["M2_HAR"],q)
        for si,(sname,mask) in enumerate(schemes.items()):
            Ls=Ls_all[mask]
            try:
                assert_loss_finite(Ls, f"{cell}/{sname}", mods)
            except InvariantViolation as e:
                halts.append(dict(cell=cell,scheme=sname,message=str(e)))
                mcs_rows.append(dict(root=root,geom=geom,btag=btag,horizon=hname,
                    scheme=sname,n_obs=int(mask.sum()),model_set="|".join(mods),
                    mcs75="HALTED",mcs90="HALTED",seed=-1,
                    note="assert_loss_finite raised; MCS not run for this cell"))
                continue
            seed=int(np.random.SeedSequence([MASTER,ci,si]).generate_state(1)[0])
            pv=mcs_seeded(Ls,seed,mods)
            s75="|".join(sorted(m for m,p in pv.items() if p>.25))
            s90="|".join(sorted(m for m,p in pv.items() if p>.10))
            mcs_rows.append(dict(root=root,geom=geom,btag=btag,horizon=hname,
                scheme=sname,n_obs=int(mask.sum()),model_set="|".join(mods),
                mcs75=s75,mcs90=s90,seed=seed,
                pvals=json.dumps({m:round(p,4) for m,p in pv.items()})))
            lrv=np.log(rvv[mask])
            for m in mods:
                lf=np.log(Fm[m][mask])
                ic=float(np.corrcoef(lf,lrv)[0,1])
                r2=float(1-((lrv-lf)**2).sum()/((lrv-lrv.mean())**2).sum())
                w=63
                ics=[np.corrcoef(lf[i:i+w],lrv[i:i+w])[0,1] for i in range(0,len(lrv)-w,w)]
                ics=[x for x in ics if np.isfinite(x)]
                ir=float(np.mean(ics)/np.std(ics)) if len(ics)>2 and np.std(ics)>0 else np.nan
                met_rows.append(dict(root=root,geom=geom,btag=btag,horizon=hname,
                    scheme=sname,model=m,n=int(mask.sum()),
                    ic_pearson_log=ic, ic_spearman=float(spearmanr(lf,lrv).statistic),
                    lam_E2=lamc["E2"], lam_E4=lamc["E4"],
                    ic_corrected_E2=ic/np.sqrt(lamc["E2"]) if lamc["E2"]==lamc["E2"] and lamc["E2"]>0 else np.nan,
                    ic_corrected_E4=ic/np.sqrt(lamc["E4"]) if lamc["E4"]==lamc["E4"] and lamc["E4"]>0 else np.nan,
                    r2_oos=r2,
                    r2_corrected_E2=r2/lamc["E2"] if lamc["E2"]==lamc["E2"] and lamc["E2"]>0 else np.nan,
                    r2_corrected_E4=r2/lamc["E4"] if lamc["E4"]==lamc["E4"] and lamc["E4"]>0 else np.nan,
                    ic_ir=ir, ic_ir_n_blocks=len(ics), ic_ir_block_len_windows=w,
                    hit_rate=float((np.sign(np.diff(lf))==np.sign(np.diff(lrv))).mean()),
                    qlike_mean=float(pd5.qlike(Fm[m][mask],rvv[mask]).mean())))
        np.savez_compressed(os.path.join(CACHE,f"loss_{root}_{geom}_{btag}_{hname}.npz"),
            L=Ls_all, models=np.array(mods), **{f"mask_{k}":v for k,v in schemes.items()})
    MC=pd.DataFrame(mcs_rows); MC.to_csv(os.path.join(RES,"phase7_mcs.csv"),index=False)
    pd.DataFrame(met_rows).to_csv(os.path.join(RES,"phase7_metrics.csv"),index=False)
    pd.DataFrame(halts).to_csv(os.path.join(RES,"phase7_halts.csv"),index=False)
    timers["phase7"]=round(time.time()-t,1)

    # ---- compositions beside S05
    old=pd.read_csv(os.path.join(S05,"s05_mcs.csv"))
    old["key"]=old.root+"/"+old.geom+"/"+old.btag+"/"+old.horizon+"/"+old.scheme
    om={r.key:(str(r.mcs75),str(r.mcs90)) for _,r in old.iterrows()}
    comp=[]
    for _,r in MC.iterrows():
        k=f"{r.root}/{r.geom}/{r.btag}/{r.horizon}/{r.scheme}"
        o75,o90=om.get(k,("",""))
        for lev,new,o in [("75",r.mcs75,o75),("90",r.mcs90,o90)]:
            ns=set(new.split("|")) if new not in ("","HALTED") else set()
            os_=set(o.split("|")) if o else set()
            comp.append(dict(cell=k,level=lev,s05=o,s06r=new,changed=(new!=o),
                entered="|".join(sorted(ns-os_)), left="|".join(sorted(os_-ns))))
    CP=pd.DataFrame(comp); CP.to_csv(os.path.join(RES,"phase7_composition_vs_s05.csv"),index=False)

    # ================= PHASE 8
    prim=[]; cnt=0; tot=0
    for (root,geom,btag,hname) in CELLS:
        base=f"{root}/{geom}/{btag}/{hname}"
        for q in QS:
            for lev in ["mcs75","mcs90"]:
                b=MC[(MC.root==root)&(MC.geom==geom)&(MC.btag==btag)&(MC.horizon==hname)&(MC.scheme==f"S-B_q{q:.2f}")]
                c=MC[(MC.root==root)&(MC.geom==geom)&(MC.btag==btag)&(MC.horizon==hname)&(MC.scheme==f"S-C_q{q:.2f}")]
                if not len(b) or not len(c): continue
                bv,cv=b[lev].iloc[0],c[lev].iloc[0]
                if bv=="HALTED" or cv=="HALTED":
                    prim.append(dict(cell=base,quantile=q,level=lev,differs=None,status="HALTED")); continue
                tot+=1; d=(bv!=cv); cnt+=int(d)
                prim.append(dict(cell=base,quantile=q,level=lev,differs=bool(d),
                    s_b=bv,s_c=cv,status="ok",is_primary_cell=(base==PRIMARY)))
    PR=pd.DataFrame(prim); PR.to_csv(os.path.join(RES,"phase8_primary.csv"),index=False)
    ind=["ES/RTH/B0/1day","NQ/GLOBEX/B1/1day","NQ/RTH/B0/1day"]
    carry=PR[PR.cell.isin(ind)]
    carry.to_csv(os.path.join(RES,"phase8_s05a_indeterminate.csv"),index=False)
    n_cells_available=len(set(PR.cell)); 
    summ=dict(family_size_preregistered=96,
              family_size_computable=tot, n_differ=cnt,
              n_cells_available=n_cells_available, n_halted=int((PR.status=="HALTED").sum()),
              primary_cell=PRIMARY,
              primary_cell_rows=PR[PR.cell==PRIMARY].to_dict("records"),
              correction_applied="none (item 47); absence disclosed as a limitation",
              timers=timers)
    json.dump(summ, open(os.path.join(RES,"phase8_summary.json"),"w"), indent=1, default=str)
    print(json.dumps({k:v for k,v in summ.items() if k!="primary_cell_rows"},indent=1,default=str))
    print("\nRGARCH verdicts:\n", D4.verdict.value_counts().to_string())
    print("\ncomposition changed:", int(CP.changed.sum()), "of", len(CP))
    print(f"total {time.time()-t0:.0f}s")

if __name__=="__main__": main()
