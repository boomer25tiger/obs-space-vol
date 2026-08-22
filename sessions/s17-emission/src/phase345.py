"""S17 Phases 3, 4 and 5: arm A4 in sample, holdout and allocation, K12.

A4 differs from A1 ONLY in the emission. Window, state count, within-window
z-scoring, warm-start policy, mean-ordering state labelling, reference classifier
and allocation rule are the same shared code operating on the same observable.
"""
import json, os, sys, time
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common17 import (BASE,RES,CACHE,S09,S16,CELLS8,CELLS4,FIVEMIN,WINDOW,SCALINGS,
                      TICKS,TICKVAL,MULT,NDAY,build_cell,roll,metrics,
                      gauss_hmm_fit,gauss_hmm_fixednoise)
MASTER_VAL=20260841
def validate():
    """Known state variance, known added observation noise."""
    rng=np.random.Generator(np.random.PCG64(MASTER_VAL))
    T=3000; A=np.array([[0.97,0.03],[0.06,0.94]])
    mu=np.array([-0.7,0.8]); s_true=np.array([0.35,0.55]); v_true=0.30
    s=np.zeros(T,int)
    for t in range(1,T): s[t]=rng.choice(2,p=A[s[t-1]])
    latent=mu[s]+s_true[s]*rng.standard_normal(T)
    x=latent+np.sqrt(v_true)*rng.standard_normal(T)
    pf,gf=gauss_hmm_fit(x)
    pk,gk=gauss_hmm_fixednoise(x,v_true)
    accf=max(((gf[:,1]>0.5).astype(int)==s).mean(),((gf[:,1]<=0.5).astype(int)==s).mean())
    acck=max(((gk[:,1]>0.5).astype(int)==s).mean(),((gk[:,1]<=0.5).astype(int)==s).mean())
    return dict(seed=MASTER_VAL,n=T,v_true=v_true,
        mu_true=mu.tolist(),s2_true=(s_true**2).tolist(),
        total_var_true=((s_true**2)+v_true).tolist(),
        free_mu=pf["mu"].tolist(),free_var=(pf["sd"]**2).tolist(),
        fixednoise_mu=pk["mu"].tolist(),fixednoise_s2=pk["s2"].tolist(),
        fixednoise_total_var=(pk["s2"]+v_true).tolist(),
        s2_abs_error=[abs(a-b) for a,b in zip(pk["s2"],s_true**2)],
        free_recovers_total=[abs(a-b) for a,b in zip(pf["sd"]**2,(s_true**2)+v_true)],
        state_accuracy_free=float(accf),state_accuracy_fixednoise=float(acck),
        n_bind=int(pk["n_bind"]))
def job(j):
    root,geom,hname,scale,lam,varlog,rng_tag,with_ho=j
    x,r,n_is,Hk=build_cell(root,geom,hname,with_holdout=with_ho)
    v=scale*(1.0-lam)*varlog
    if with_ho:
        st,pr,_,dg=roll(x,noise_raw=v,start=n_is-1)
    else:
        st,pr,_,dg=roll(x[:n_is],noise_raw=v)
    return dict(root=root,geom=geom,horizon=hname,scale=scale,lam_range=rng_tag,
                lam=lam,v=v,n_is=n_is,states=st,probs=pr,diag=dg,with_ho=with_ho)
def maxdd(c):
    p=np.maximum.accumulate(c); return float(np.min(c/np.maximum(p,1e-300)-1.0))
def main():
    t0=time.time(); timers={}; out={}
    val=validate(); json.dump(val,open(os.path.join(RES,"phase3_validation.json"),"w"),indent=1)
    print("=== A4 ESTIMATOR VALIDATION ==="); print(json.dumps(val,indent=1))
    P3=pd.read_csv(os.path.join(S09,"results","phase3_sizing_params.csv"))
    from common17 import cell_windows,subbars
    from proxies_robust import p1_rv
    VAR={}
    for root,geom,hname in CELLS8:
        rw,_,_=cell_windows(root,geom,hname)
        rv=p1_rv(subbars(rw,FIVEMIN[(geom,hname)])); pos=rv>0
        VAR[(root,geom,hname)]=float(np.log(rv[pos]).var())
    LAM={}
    for root,geom,hname in CELLS8:
        for rng_tag in ["extended","restricted_S05"]:
            r=P3[(P3.root==root)&(P3.geom==geom)&(P3.btag=="B0")&(P3.horizon==hname)&
                 (P3["range"]==rng_tag)]
            ok=len(r) and bool(r.iloc[0].valid) and 0.0<float(r.iloc[0].lam_intercept)<=1.0
            LAM[(root,geom,hname,rng_tag)]=float(r.iloc[0].lam_intercept) if ok else None
    LT=pd.DataFrame([dict(root=r,geom=g,horizon=h,lam_range=t,
        lam=LAM[(r,g,h,t)],var_log_rv=VAR[(r,g,h)],
        var_eps=(None if LAM[(r,g,h,t)] is None else (1-LAM[(r,g,h,t)])*VAR[(r,g,h)]),
        usable=LAM[(r,g,h,t)] is not None)
        for r,g,h in CELLS8 for t in ["extended","restricted_S05"]])
    LT.to_csv(os.path.join(RES,"phase3_noise_inputs.csv"),index=False)
    print("\n=== observation-noise inputs, both lambda ranges (item 66) ===")
    pd.set_option("display.width",280); print(LT.round(5).to_string(index=False))
    # ================= PHASE 3, in sample
    t=time.time()
    jobs=[(r,g,h,s,LAM[(r,g,h,"extended")],VAR[(r,g,h)],"extended",False)
          for r,g,h in CELLS8 for s in SCALINGS]
    jobs+=[(r,g,h,1.00,LAM[(r,g,h,"restricted_S05")],VAR[(r,g,h)],"restricted_S05",False)
           for r,g,h in CELLS8 if LAM[(r,g,h,"restricted_S05")] is not None]
    res={}
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs={ex.submit(job,j):j for j in jobs}
        for f in as_completed(futs):
            d=f.result(); res[(d["root"],d["geom"],d["horizon"],d["scale"],d["lam_range"])]=d
            print(f"  IS A4 {d['root']}/{d['geom']}/{d['horizon']} scale={d['scale']} "
                  f"{d['lam_range']} bind={d['diag']['n_windows_binding']}/"
                  f"{d['diag']['n_windows']} done",flush=True)
    timers["phase3"]=round(time.time()-t,1)
    rows=[]
    for (root,geom,hname,scale,rt),d in res.items():
        z=np.load(os.path.join(S16,"cache",f"is_{root}_{geom}_{hname}_A1_raw.npz"))
        a1=z["states"]; ref=z["ref_states"]
        n=min(len(d["states"]),len(a1),len(ref))
        st,a1,ref=d["states"][:n],a1[:n],ref[:n]
        ok=(st>=0)&(a1>=0)
        m=metrics(st,ref,"insample"); m1=metrics(a1,ref,"insample")
        rows.append(dict(root=root,geom=geom,horizon=hname,scale=scale,lam_range=rt,
            lam=d["lam"],v_raw=d["v"],
            n_windows=d["diag"]["n_windows"],
            n_windows_binding=d["diag"]["n_windows_binding"],
            share_windows_binding=d["diag"]["n_windows_binding"]/max(d["diag"]["n_windows"],1),
            n_bind_total=d["diag"]["n_bind_total"],
            states_differ_vs_A1=int((st[ok]!=a1[ok]).sum()),
            share_states_differ=float((st[ok]!=a1[ok]).mean()),
            mis_A4=m.get("misclass"),mis_A1=m1.get("misclass"),
            reduction_pp=100*(m1.get("misclass",np.nan)-m.get("misclass",np.nan)),
            switches_A4=m.get("switches"),switches_A1=m1.get("switches"),
            dur_A4=m.get("mean_regime_duration"),dur_A1=m1.get("mean_regime_duration")))
        np.savez_compressed(os.path.join(CACHE,
            f"a4is_{root}_{geom}_{hname}_s{scale:.2f}_{rt}.npz"),
            states=d["states"],probs=d["probs"],v=d["v"],lam=d["lam"],
            n_bind_total=d["diag"]["n_bind_total"],
            n_windows_binding=d["diag"]["n_windows_binding"])
    A4=pd.DataFrame(rows).sort_values(["lam_range","root","geom","horizon","scale"])
    A4.to_csv(os.path.join(RES,"phase3_a4_insample.csv"),index=False)
    print("\n=== PHASE 3: A4 in sample ===")
    print(A4[["root","geom","horizon","lam_range","scale","v_raw","n_windows_binding",
              "share_windows_binding","states_differ_vs_A1","share_states_differ",
              "mis_A1","mis_A4","reduction_pp"]].round(5).to_string(index=False))
    # ================= PHASE 4, HOLDOUT
    t=time.time()
    jobs=[(r,g,h,s,LAM[(r,g,h,"extended")],VAR[(r,g,h)],"extended",True)
          for r,g,h in CELLS8 for s in SCALINGS]
    jobs+=[(r,g,h,1.00,LAM[(r,g,h,"restricted_S05")],VAR[(r,g,h)],"restricted_S05",True)
           for r,g,h in CELLS8 if LAM[(r,g,h,"restricted_S05")] is not None]
    hres={}
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs={ex.submit(job,j):j for j in jobs}
        for f in as_completed(futs):
            d=f.result(); hres[(d["root"],d["geom"],d["horizon"],d["scale"],d["lam_range"])]=d
            print(f"  HO A4 {d['root']}/{d['geom']}/{d['horizon']} scale={d['scale']} "
                  f"{d['lam_range']} done",flush=True)
    timers["phase4_hmm"]=round(time.time()-t,1)
    hrows=[]
    for (root,geom,hname,scale,rt),d in hres.items():
        n_is=d["n_is"]
        z=np.load(os.path.join(S16,"cache",f"hofix_{root}_{geom}_{hname}_A1_raw.npz"))
        a1=z["states"][z["n_is"]:]; ref=z["ref_states"][z["n_is"]:]
        st=d["states"][n_is:]
        n=min(len(st),len(a1),len(ref)); st,a1,ref=st[:n],a1[:n],ref[:n]
        ok=(st>=0)&(a1>=0)
        m=metrics(st,ref,"holdout"); m1=metrics(a1,ref,"holdout")
        hrows.append(dict(root=root,geom=geom,horizon=hname,scale=scale,lam_range=rt,
            n=m.get("n"),states_differ_vs_A1=int((st[ok]!=a1[ok]).sum()),
            mis_A4=m.get("misclass"),mis_A1=m1.get("misclass"),
            reduction_pp=100*(m1.get("misclass",np.nan)-m.get("misclass",np.nan)),
            switches_A4=m.get("switches"),switches_A1=m1.get("switches"),
            dur_A4=m.get("mean_regime_duration"),dur_A1=m1.get("mean_regime_duration")))
        np.savez_compressed(os.path.join(CACHE,
            f"a4ho_{root}_{geom}_{hname}_s{scale:.2f}_{rt}.npz"),
            states=d["states"],probs=d["probs"],n_is=n_is,v=d["v"])
    HO=pd.DataFrame(hrows).sort_values(["lam_range","root","geom","horizon","scale"])
    HO.to_csv(os.path.join(RES,"phase4_a4_holdout.csv"),index=False)
    print("\n=== PHASE 4: A4 holdout ===")
    print(HO[["root","geom","horizon","lam_range","scale","n","states_differ_vs_A1",
              "mis_A1","mis_A4","reduction_pp"]].round(5).to_string(index=False))
    # ---- allocation overlay
    t=time.time(); alloc=[]
    for root,geom in CELLS4:
        zp=np.load(os.path.join(S09,"cache",f"ho_pos_{root}_{geom}_extended_R3.npz"))
        from phase8910_apps import ho_series
        w=zp["w"]; S=ho_series(root,geom,"B0",holdout=True); ret=S["ret"]
        n=min(len(w),len(ret)); w,ret=w[:n],ret[:n]; base=w*ret
        px=float(np.exp(np.load(os.path.join(S09,"cache",
             f"ho_panel_{root}_{geom}.npz"))["close"].astype(np.float64)).mean())
        notional=MULT[root]*px
        z16=np.load(os.path.join(S16,"cache",f"hofix_{root}_{geom}_1day_A1_raw.npz"))
        n_is=int(z16["n_is"])
        sigs={"A1_raw":z16["states"][n_is:][:n],
              "reference_kernel":z16["ref_states"][n_is:][:n],
              "always_invested":np.zeros(n,np.int8)}
        for s in SCALINGS:
            d=hres[(root,geom,"1day",s,"extended")]
            sigs[f"A4_s{s:.2f}"]=d["states"][d["n_is"]:][:n]
        for arm,stv in sigs.items():
            sig=(np.ones(n) if arm=="always_invested"
                 else np.where(stv>=0,1.0-stv,np.nan))
            sig=np.concatenate([[np.nan],sig[:-1]])
            ok=np.isfinite(sig)&np.isfinite(base)
            r=np.where(ok,sig*base,0.0)
            turn=float(np.nansum(np.abs(np.diff(np.where(ok,sig*w,0.0)))))
            sd=float(np.std(r[ok],ddof=1)); mn=float(np.mean(r[ok]))
            cum=np.cumprod(1.0+r[ok])
            for tk in TICKS:
                rt_=2*tk*TICKVAL[root]/notional
                ct=turn*rt_
                alloc.append(dict(root=root,geom=geom,arm=arm,ticks=tk,n=int(ok.sum()),
                    ann_return=(mn-ct/max(ok.sum(),1))*NDAY,ann_vol=sd*np.sqrt(NDAY),
                    sharpe=float((mn-ct/max(ok.sum(),1))*NDAY/max(sd*np.sqrt(NDAY),1e-12)),
                    max_drawdown=maxdd(cum),turnover=turn,
                    annual_cost_bps=ct*1e4/max(ok.sum(),1)*NDAY,
                    share_invested=float(np.nanmean(sig[ok]))))
            np.savez_compressed(os.path.join(CACHE,f"alloc17_{root}_{geom}_{arm}.npz"),
                signal=sig,ret_overlay=r,ret_base=base,w=w,ok=ok)
    AL=pd.DataFrame(alloc); AL.to_csv(os.path.join(RES,"phase4_allocation.csv"),index=False)
    timers["allocation"]=round(time.time()-t,1)
    print("\n=== allocation overlay, 1 tick ===")
    print(AL[AL.ticks==1.0][["root","geom","arm","ann_return","ann_vol","sharpe",
              "max_drawdown","annual_cost_bps","share_invested"]].round(4).to_string(index=False))
    # ================= PHASE 5, K12
    hh=HO[(HO.lam_range=="extended")&(HO.scale==1.00)]
    k12=dict(threshold_pp=1.0,
        reduction_pp_by_cell={f"{r}/{g}/{h}":float(v) for r,g,h,v in
            zip(hh.root,hh.geom,hh.horizon,hh.reduction_pp)},
        max_reduction_pp=float(hh.reduction_pp.max()),
        min_reduction_pp=float(hh.reduction_pp.min()),
        all_below_1pp=bool((hh.reduction_pp<1.0).all()),
        n_cells=int(len(hh)),
        states_differ_total_holdout=int(hh.states_differ_vs_A1.sum()),
        states_differ_total_insample=int(A4[(A4.lam_range=="extended")&
                                            (A4.scale==1.00)].states_differ_vs_A1.sum()),
        windows_binding_total=int(A4[(A4.lam_range=="extended")&
                                     (A4.scale==1.00)].n_windows_binding.sum()),
        windows_total=int(A4[(A4.lam_range=="extended")&(A4.scale==1.00)].n_windows.sum()),
        sensitivity={f"scale_{s:.2f}":dict(
            max_reduction_pp=float(HO[(HO.lam_range=="extended")&
                (HO.scale==s)].reduction_pp.max()),
            states_differ=int(HO[(HO.lam_range=="extended")&
                (HO.scale==s)].states_differ_vs_A1.sum()),
            windows_binding=int(A4[(A4.lam_range=="extended")&
                (A4.scale==s)].n_windows_binding.sum())) for s in SCALINGS})
    k12["K12"]=("FIRES" if k12["all_below_1pp"] else "DOES NOT FIRE")
    out["K12"]=k12; out["validation"]=val; out["timers"]=timers
    json.dump(out,open(os.path.join(RES,"phase345_summary.json"),"w"),indent=1,default=str)
    print("\n=== PHASE 5: K12 ==="); print(json.dumps(k12,indent=1))
    print(f"PHASE3-5 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
