"""S09 Phases 1 and 2: placebo scheme S-D, and seed stability on flipped comparisons.

S-D conditions on the PREVIOUS window's M2_HAR forecast, a variable in F_{t-1}
with no realized-proxy content, at the same quantiles as S-B and S-C. Nothing
dated on or after 2024-01-01 is read here.
"""
import json, os, sys, time
import numpy as np, pandas as pd
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
S08=os.path.join(ROOT,"sessions","s08-final")
sys.path.insert(0,os.path.join(ROOT,"sessions","s08-final","src"))
sys.path.insert(0,os.path.join(ROOT,"sessions","s06r-repair","tests"))
sys.path.insert(0,os.path.join(ROOT,"sessions","s05-reliability-mcs","src"))
from test_invariants import assert_loss_finite, InvariantViolation
import partde as pd5
MODELS=pd5.MODELS; BOOT_N=10000; MASTER=20260819; MASTER_SEEDSTAB=20260820
QS=[0.80,0.90]; N_SEEDS=20
CELLS=[(r,g,b,h) for g in ["GLOBEX","RTH"] for r in ["ES","NQ"]
       for b in ["B0","B1"] for h in ["1day","1h","30min"]]
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
def main():
    t0=time.time(); timers={}
    MC8=pd.read_csv(os.path.join(S08,"results","phase2_mcs.csv"))
    LAM=pd.read_csv(os.path.join(S08,"results","phase4_lambda.csv"))
    rows=[]
    for ci,c in enumerate(CELLS):
        root,geom,btag,hname=c; cell="/".join(c)
        p=os.path.join(S08,"cache",f"gen_{root}_{geom}_{btag}_{hname}.npz")
        if not os.path.exists(p): continue
        z=np.load(p); L=z["L"]; rvv=z["rvv"]
        stored=[str(x) for x in z["models"]]
        mset=MC8[(MC8.root==root)&(MC8.geom==geom)&(MC8.btag==btag)&(MC8.horizon==hname)]
        mods=mset.model_set.iloc[0].split("|") if len(mset) else stored
        keep=[stored.index(m) for m in mods]; La=L[:,keep]
        F=z["F_M2_HAR"]
        Fprev=np.concatenate([[F[0]],F[:-1]])      # F_{t-1}, no proxy content
        for si,q in enumerate(QS):
            mk=Fprev>np.quantile(Fprev,q)
            Ls=La[mk]
            try: assert_loss_finite(Ls,f"{cell}/S-D_q{q:.2f}",mods)
            except InvariantViolation:
                rows.append(dict(root=root,geom=geom,btag=btag,horizon=hname,
                    scheme=f"S-D_q{q:.2f}",n_obs=int(mk.sum()),model_set="|".join(mods),
                    mcs75="HALTED",mcs90="HALTED",seed=-1)); continue
            seed=int(np.random.SeedSequence([MASTER,ci,100+si]).generate_state(1)[0])
            pv=mcs_seeded(Ls,seed,mods)
            rows.append(dict(root=root,geom=geom,btag=btag,horizon=hname,
                scheme=f"S-D_q{q:.2f}",n_obs=int(mk.sum()),model_set="|".join(mods),
                mcs75="|".join(sorted(m for m,x in pv.items() if x>.25)),
                mcs90="|".join(sorted(m for m,x in pv.items() if x>.10)),seed=seed,
                pvals=json.dumps({m:round(x,4) for m,x in pv.items()})))
    SD=pd.DataFrame(rows); SD.to_csv(os.path.join(RES,"phase1_sd_mcs.csv"),index=False)
    timers["phase1_mcs"]=round(time.time()-t0,1)
    # ---- comparisons
    comp=[]
    for c in CELLS:
        root,geom,btag,hname=c; base="/".join(c)
        for q in QS:
            for lev in ["mcs75","mcs90"]:
                def get(df,sc):
                    s=df[(df.root==root)&(df.geom==geom)&(df.btag==btag)
                         &(df.horizon==hname)&(df.scheme==sc)]
                    return str(s[lev].iloc[0]) if len(s) else None
                b_=get(MC8,f"S-B_q{q:.2f}"); c_=get(MC8,f"S-C_q{q:.2f}"); d_=get(SD,f"S-D_q{q:.2f}")
                if b_ is None or c_ is None or d_ is None: continue
                if "HALTED" in (b_,c_,d_):
                    comp.append(dict(cell=base,root=root,geom=geom,btag=btag,horizon=hname,
                        quantile=q,level=lev,status="HALTED")); continue
                comp.append(dict(cell=base,root=root,geom=geom,btag=btag,horizon=hname,
                    quantile=q,level=lev,status="ok",bc_differs=bool(b_!=c_),
                    dc_differs=bool(d_!=c_),s_b=b_,s_c=c_,s_d=d_))
    CP=pd.DataFrame(comp); CP.to_csv(os.path.join(RES,"phase1_comparisons.csv"),index=False)
    ok=CP[CP.status=="ok"]
    strat=[]
    for dim in ["horizon","root","geom","quantile"]:
        for k,g in ok.groupby(dim):
            strat.append(dict(dimension=dim,level=str(k),n=len(g),
                bc_rate=float(g.bc_differs.mean()),dc_rate=float(g.dc_differs.mean()),
                excess=float(g.bc_differs.mean()-g.dc_differs.mean())))
    ST=pd.DataFrame(strat); ST.to_csv(os.path.join(RES,"phase1_stratified.csv"),index=False)
    rth=ok[ok.geom=="RTH"]
    lamh={}
    for h in ["1day","1h","30min"]:
        s=LAM[(LAM.geom=="RTH")&(LAM.horizon==h)]
        s=s[s.M==s.M.max()]
        lamh[h]=float(s.lam_intercept.mean()) if len(s) else np.nan
    byh=[]
    for h in ["1day","1h","30min"]:
        g=rth[rth.horizon==h]
        if not len(g): continue
        byh.append(dict(horizon=h,n=len(g),bc_rate=float(g.bc_differs.mean()),
            dc_rate=float(g.dc_differs.mean()),
            excess=float(g.bc_differs.mean()-g.dc_differs.mean()),
            lam_intercept=lamh[h]))
    BH=pd.DataFrame(byh); BH.to_csv(os.path.join(RES,"phase1_excess_by_horizon.csv"),index=False)
    ex_all=float(ok.bc_differs.mean()-ok.dc_differs.mean())
    ex_rth=float(rth.bc_differs.mean()-rth.dc_differs.mean())
    tracks=bool(len(BH)>2 and abs(np.corrcoef(BH.excess,BH.lam_intercept)[0,1])>0.8)
    k2=("FIRES" if abs(ex_rth)<0.10 else
        "DOES NOT FIRE" if (ex_rth>0.20 and tracks) else "INDETERMINATE")
    timers["phase1"]=round(time.time()-t0,1)
    # ---- Phase 2: seed stability on flipped comparisons
    t=time.time()
    CC=pd.read_csv(os.path.join(S08,"results","phase2_composition_compare.csv"))
    flipped=CC[CC.changed_vs_s07]
    cells_f=sorted({"/".join(x.split("/")[:4]) for x in flipped.cell})
    seeds=[int(s) for s in np.random.SeedSequence(MASTER_SEEDSTAB).generate_state(N_SEEDS)]
    stab=[]
    for cell in cells_f:
        root,geom,btag,hname=cell.split("/")
        p=os.path.join(S08,"cache",f"gen_{root}_{geom}_{btag}_{hname}.npz")
        if not os.path.exists(p): continue
        z=np.load(p); L=z["L"]; rvv=z["rvv"]; stored=[str(x) for x in z["models"]]
        mset=MC8[(MC8.root==root)&(MC8.geom==geom)&(MC8.btag==btag)&(MC8.horizon==hname)]
        mods=mset.model_set.iloc[0].split("|") if len(mset) else stored
        keep=[stored.index(m) for m in mods]; La=L[:,keep]
        F=z["F_M2_HAR"]
        for scheme in ["S-A"]+[f"S-{x}_q{q:.2f}" for x in ["B","C"] for q in QS]:
            if scheme=="S-A": mk=np.ones(len(rvv),bool)
            else:
                q=float(scheme.split("_q")[1])
                base=rvv if scheme.startswith("S-B") else F
                mk=base>np.quantile(base,q)
            Ls=La[mk]
            if not np.isfinite(Ls).all(): continue
            c75=[];c90=[]
            for sd in seeds:
                pv=mcs_seeded(Ls,sd,mods)
                c75.append("|".join(sorted(m for m,x in pv.items() if x>.25)))
                c90.append("|".join(sorted(m for m,x in pv.items() if x>.10)))
            s8=mset[mset.scheme==scheme]
            for lev,cl in [("mcs75",c75),("mcs90",c90)]:
                vc=pd.Series(cl).value_counts()
                stab.append(dict(cell=cell,scheme=scheme,level=lev,n_seeds=len(cl),
                    n_distinct=int(len(vc)),modal=vc.index[0],modal_freq=int(vc.iloc[0]),
                    s08_in_set=bool(str(s8[lev].iloc[0]) in set(cl)) if len(s8) else None,
                    indeterminate=bool(len(vc)>1)))
    SB=pd.DataFrame(stab); SB.to_csv(os.path.join(RES,"phase2_seed_stability.csv"),index=False)
    ind_cells=sorted(set(SB[SB.indeterminate].cell)) if len(SB) else []
    ok2=ok[~ok.cell.isin(ind_cells)]
    ex_rth2=float(ok2[ok2.geom=="RTH"].bc_differs.mean()-ok2[ok2.geom=="RTH"].dc_differs.mean()) if len(ok2) else np.nan
    timers["phase2"]=round(time.time()-t,1)
    summ=dict(n_comparisons=len(ok),n_halted=int((CP.status=="HALTED").sum()),
        bc_differ=int(ok.bc_differs.sum()),dc_differ=int(ok.dc_differs.sum()),
        bc_rate=float(ok.bc_differs.mean()),dc_rate=float(ok.dc_differs.mean()),
        excess_all=ex_all,n_rth=len(rth),bc_rate_rth=float(rth.bc_differs.mean()),
        dc_rate_rth=float(rth.dc_differs.mean()),excess_rth=ex_rth,
        excess_tracks_lambda=tracks,by_horizon=BH.to_dict("records"),
        K2=k2,n_flipped_cells=len(cells_f),n_indeterminate_cells=len(ind_cells),
        indeterminate_cells=ind_cells,excess_rth_excl_indeterminate=ex_rth2,timers=timers)
    json.dump(summ,open(os.path.join(RES,"phase12_summary.json"),"w"),indent=1,default=str)
    print(json.dumps({k:v for k,v in summ.items() if k not in ("by_horizon","indeterminate_cells")},indent=1,default=str))
    print("\nby horizon (RTH):\n",BH.to_string(index=False))
    print("\nstratified:\n",ST.to_string(index=False))
    print("K2:",k2)
if __name__=="__main__": main()
