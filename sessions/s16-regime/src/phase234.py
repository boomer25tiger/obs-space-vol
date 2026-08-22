"""S16 Phases 2, 3 and 4: in-sample classification, holdout, allocation, K11.

The three arms differ ONLY in the observable. Window, state count, z-scoring,
warm-start policy, state labelling and the reference classifier are identical
across arms; the reference is the same HMM run on the finest-grid realized
kernel, so misclassification is measured with the classifier held fixed.
"""
import json, os, sys, time
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common16 import (BASE,RES,CACHE,S09,CELLS8,CELLS4,FIVEMIN,WINDOW,MA_LEN,ARMS,
                      TICKS,TICKVAL,MULT,NDAY,gauss_hmm_fit)
from common import cell_windows,subbars
from proxies_robust import p1_rv,p3_kernel_flattop,kernel_H
from phase8910_apps import ho_series

def observables(x,lam,mu_is):
    """The only thing that differs between arms."""
    ma=pd.Series(x).rolling(MA_LEN,min_periods=MA_LEN).mean().values
    return {"A1_raw":x,"A2_ma5":ma,"A3_shrunk":(1.0-lam)*mu_is+lam*x}

def roll_states(v):
    """Rolling 441-window, one step at a time, two-state Gaussian HMM on the
    z-scored observable. State at the window's last observation is recorded."""
    T=len(v); st=np.full(T,-1,np.int8); pr=np.full(T,np.nan)
    init=None; nconv=0
    for e in range(WINDOW,T+1):
        w=v[e-WINDOW:e]
        if not np.isfinite(w).all(): continue
        s=w.std()
        if s<=0: continue
        z=(w-w.mean())/s
        p,g=gauss_hmm_fit(z,init=init)
        init=p
        st[e-1]=int(g[-1,1]>0.5); pr[e-1]=float(g[-1,1])
        if not np.isfinite(p["loglik"]): nconv+=1
    return st,pr,nconv

def build_cell(root,geom,hname,with_holdout):
    M5=FIVEMIN[(geom,hname)]
    rw,kw,ds=cell_windows(root,geom,hname)
    rv=p1_rv(subbars(rw,M5)); pos=rv>0
    Mf=rw.shape[1]
    om2=float((rw**2).sum(axis=1).mean()/(2.0*Mf))
    Hk=kernel_H(Mf,om2,float(rv[pos].mean()))
    rk=np.maximum(p3_kernel_flattop(rw,Hk),1e-300)
    x_is=np.log(rv[pos]); r_is=np.log(rk[pos]); d_is=np.array(ds,dtype="U10")[pos]
    if not with_holdout:
        return x_is,r_is,d_is,len(x_is),Hk
    z=np.load(os.path.join(S09,"cache",f"ho_panel_{root}_{geom}.npz"))
    S=ho_series(root,geom,"B0",holdout=True)
    rvh=p1_rv(subbars(S["rw"],M5)); posh=rvh>0
    rkh=np.maximum(p3_kernel_flattop(S["rw"],Hk),1e-300)
    x=np.concatenate([x_is,np.log(rvh[posh])])
    r=np.concatenate([r_is,np.log(rkh[posh])])
    d=np.concatenate([d_is,np.array(S["wdates"],dtype="U10")[posh]])
    return x,r,d,len(x_is),Hk

def task(job):
    root,geom,hname,arm,lam,with_holdout=job
    x,r,d,n_is,Hk=build_cell(root,geom,hname,with_holdout)
    mu_is=float(x[:n_is].mean())
    v=observables(x,lam,mu_is)[arm]
    st,pr,nc=roll_states(v)
    rst,rpr,_=roll_states(r) if arm=="A1_raw" else (None,None,0)
    return dict(root=root,geom=geom,horizon=hname,arm=arm,lam=lam,mu_is=mu_is,
                n_is=n_is,n_total=len(x),H_kernel=int(Hk),states=st,probs=pr,
                ref_states=rst,ref_probs=rpr,dates=d,x=x,ref=r,nonconv=nc)

def metrics(st,ref,tag):
    ok=(st>=0)&(ref>=0)
    n=int(ok.sum())
    if n<10: return dict(sample=tag,n=n)
    a,b=st[ok],ref[ok]
    dis=a!=b
    sw=int(np.abs(np.diff(a)).sum())
    runs=[];cur=1
    for i in range(1,len(a)):
        if a[i]==a[i-1]: cur+=1
        else: runs.append(cur); cur=1
    runs.append(cur)
    return dict(sample=tag,n=n,misclass=float(dis.mean()),
        both_high=int(((a==1)&(b==1)).sum()),spurious_high=int(((a==1)&(b==0)).sum()),
        spurious_low=int(((a==0)&(b==1)).sum()),both_low=int(((a==0)&(b==0)).sum()),
        switches=sw,switch_rate=sw/max(n-1,1),
        mean_regime_duration=float(np.mean(runs)),share_high=float(a.mean()))

def maxdd(cum):
    peak=np.maximum.accumulate(cum); return float(np.min(cum/np.maximum(peak,1e-300)-1.0))

def main():
    t0=time.time(); timers={}
    P3=pd.read_csv(os.path.join(S09,"results","phase3_sizing_params.csv"))
    LAM={}
    for root,geom,hname in CELLS8:
        r=P3[(P3.root==root)&(P3.geom==geom)&(P3.btag=="B0")&(P3.horizon==hname)&
             (P3["range"]=="extended")]
        LAM[(root,geom,hname)]=float(r.iloc[0].lam_intercept)
    # ---------------- PHASE 2, pre-2024 only
    t=time.time()
    jobs=[(r,g,h,a,LAM[(r,g,h)],False) for r,g,h in CELLS8 for a in ARMS]
    res={}
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs={ex.submit(task,j):j for j in jobs}
        for f in as_completed(futs):
            d=f.result(); res[(d["root"],d["geom"],d["horizon"],d["arm"])]=d
            print(f"  IS {d['root']}/{d['geom']}/{d['horizon']} {d['arm']} done",flush=True)
    timers["phase2"]=round(time.time()-t,1)
    rows=[]; agree=[]; ident=[]
    for root,geom,hname in CELLS8:
        ref=res[(root,geom,hname,"A1_raw")]["ref_states"]
        a1=res[(root,geom,hname,"A1_raw")]["states"]
        a3=res[(root,geom,hname,"A3_shrunk")]["states"]
        ident.append(dict(root=root,geom=geom,horizon=hname,
            n_compared=int(((a1>=0)&(a3>=0)).sum()),
            n_states_differ=int((a1[(a1>=0)&(a3>=0)]!=a3[(a1>=0)&(a3>=0)]).sum()),
            max_abs_prob_diff=float(np.nanmax(np.abs(
                res[(root,geom,hname,'A1_raw')]["probs"]-
                res[(root,geom,hname,'A3_shrunk')]["probs"]))))) 
        lam=LAM[(root,geom,hname)]
        for arm in ARMS:
            d=res[(root,geom,hname,arm)]
            m=metrics(d["states"],ref,"insample")
            rows.append(dict(root=root,geom=geom,horizon=hname,arm=arm,lam=lam,
                analytic_rate=float(np.arccos(np.sqrt(min(lam,1.0)))/np.pi),
                nonconv=d["nonconv"],**m))
            np.savez_compressed(os.path.join(CACHE,
                f"is_{root}_{geom}_{hname}_{arm}.npz"),
                states=d["states"],probs=d["probs"],ref_states=ref,dates=d["dates"],
                x=d["x"],lam=lam,mu_is=d["mu_is"])
        for a,b in [("A3_shrunk","A1_raw"),("A3_shrunk","A2_ma5"),("A2_ma5","A1_raw")]:
            sa,sb=res[(root,geom,hname,a)]["states"],res[(root,geom,hname,b)]["states"]
            ok=(sa>=0)&(sb>=0)
            agree.append(dict(root=root,geom=geom,horizon=hname,pair=f"{a}_vs_{b}",
                n=int(ok.sum()),n_differ=int((sa[ok]!=sb[ok]).sum()),
                share_differ=float((sa[ok]!=sb[ok]).mean())))
    IS=pd.DataFrame(rows); IS.to_csv(os.path.join(RES,"phase2_insample.csv"),index=False)
    AG=pd.DataFrame(agree); AG.to_csv(os.path.join(RES,"phase2_agreement.csv"),index=False)
    ID=pd.DataFrame(ident); ID.to_csv(os.path.join(RES,"phase2_a1_a3_identity.csv"),index=False)
    pd.set_option("display.width",270)
    print("\n=== PHASE 2: in-sample classification ===")
    print(IS[["root","geom","horizon","arm","n","misclass","analytic_rate","switches",
              "switch_rate","mean_regime_duration","share_high"]].round(5).to_string(index=False))
    print("\n=== A1 vs A3 state identity ==="); print(ID.to_string(index=False))
    print("\n=== arm agreement ==="); print(AG.round(5).to_string(index=False))
    # ---------------- PHASE 3, HOLDOUT
    t=time.time()
    jobs=[(r,g,h,a,LAM[(r,g,h)],True) for r,g,h in CELLS8 for a in ARMS]
    hres={}
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs={ex.submit(task,j):j for j in jobs}
        for f in as_completed(futs):
            d=f.result(); hres[(d["root"],d["geom"],d["horizon"],d["arm"])]=d
            print(f"  HO {d['root']}/{d['geom']}/{d['horizon']} {d['arm']} done",flush=True)
    timers["phase3_hmm"]=round(time.time()-t,1)
    hrows=[]
    for root,geom,hname in CELLS8:
        ref=hres[(root,geom,hname,"A1_raw")]["ref_states"]
        n_is=hres[(root,geom,hname,"A1_raw")]["n_is"]
        for arm in ARMS:
            d=hres[(root,geom,hname,arm)]
            for tag,sl in [("insample",slice(0,n_is)),("holdout",slice(n_is,None))]:
                m=metrics(d["states"][sl],ref[sl],tag)
                hrows.append(dict(root=root,geom=geom,horizon=hname,arm=arm,**m))
            np.savez_compressed(os.path.join(CACHE,
                f"ho_{root}_{geom}_{hname}_{arm}.npz"),
                states=d["states"],probs=d["probs"],ref_states=ref,dates=d["dates"],
                n_is=n_is,x=d["x"])
    HO=pd.DataFrame(hrows); HO.to_csv(os.path.join(RES,"phase3_classification.csv"),index=False)
    print("\n=== PHASE 3: in sample vs holdout ===")
    print(HO[["root","geom","horizon","arm","sample","n","misclass","switches",
              "mean_regime_duration"]].round(5).to_string(index=False))
    # ---------------- allocation overlay, daily cells
    t=time.time(); alloc=[]
    for root,geom in CELLS4:
        z=np.load(os.path.join(S09,"cache",f"ho_pos_{root}_{geom}_extended_R3.npz"))
        w=z["w"]; S=ho_series(root,geom,"B0",holdout=True)
        ret=S["ret"]; n=min(len(w),len(ret))
        w,ret=w[:n],ret[:n]
        base=w*ret                                    # always-invested vol-targeted book
        px=float(np.exp(np.load(os.path.join(S09,"cache",
             f"ho_panel_{root}_{geom}.npz"))["close"].astype(np.float64)).mean())
        notional=MULT[root]*px
        n_is=hres[(root,geom,"1day","A1_raw")]["n_is"]
        for arm in ARMS+["reference_kernel","always_invested"]:
            if arm=="always_invested": sig=np.ones(n)
            elif arm=="reference_kernel":
                s=hres[(root,geom,"1day","A1_raw")]["ref_states"][n_is:][:n]
                sig=np.where(s>=0,1.0-s,np.nan)
            else:
                s=hres[(root,geom,"1day",arm)]["states"][n_is:][:n]
                sig=np.where(s>=0,1.0-s,np.nan)
            sig=np.concatenate([[np.nan],sig[:-1]])   # one-day execution lag
            ok=np.isfinite(sig)&np.isfinite(base)
            r=np.where(ok,sig*base,0.0)
            turn=float(np.nansum(np.abs(np.diff(np.where(ok,sig*w,0.0)))))
            sd=float(np.std(r[ok],ddof=1)); mn=float(np.mean(r[ok]))
            cum=np.cumprod(1.0+r[ok])
            for tk in TICKS:
                rt=2*tk*TICKVAL[root]/notional
                cost_tot=turn*rt
                cost_bps=cost_tot*1e4/max(ok.sum(),1)*NDAY
                net=mn-cost_tot/max(ok.sum(),1)
                alloc.append(dict(root=root,geom=geom,arm=arm,ticks=tk,
                    n=int(ok.sum()),ann_return=net*NDAY,ann_vol=sd*np.sqrt(NDAY),
                    sharpe=float(net*NDAY/max(sd*np.sqrt(NDAY),1e-12)),
                    sharpe_gross=float(mn*NDAY/max(sd*np.sqrt(NDAY),1e-12)),
                    max_drawdown=maxdd(cum),turnover=turn,
                    annual_cost_bps=cost_bps,
                    share_invested=float(np.nanmean(sig[ok]))))
            np.savez_compressed(os.path.join(CACHE,f"alloc_{root}_{geom}_{arm}.npz"),
                signal=sig,ret_overlay=r,ret_base=base,w=w,ok=ok)
    AL=pd.DataFrame(alloc); AL.to_csv(os.path.join(RES,"phase3_allocation.csv"),index=False)
    timers["allocation"]=round(time.time()-t,1)
    print("\n=== allocation overlay, holdout ===")
    print(AL[AL.ticks==1.0][["root","geom","arm","n","ann_return","ann_vol","sharpe",
                             "max_drawdown","turnover","annual_cost_bps",
                             "share_invested"]].round(4).to_string(index=False))
    # ---------------- PHASE 4, K11
    ho=HO[HO["sample"]=="holdout"]
    k11=[]
    for root,geom,hname in CELLS8:
        g=ho[(ho.root==root)&(ho.geom==geom)&(ho.horizon==hname)].set_index("arm")
        m1,m2,m3=g.loc["A1_raw","misclass"],g.loc["A2_ma5","misclass"],g.loc["A3_shrunk","misclass"]
        k11.append(dict(root=root,geom=geom,horizon=hname,
            mis_A1=m1,mis_A2=m2,mis_A3=m3,
            reduction_vs_A1_pp=100*(m1-m3),reduction_vs_A2_pp=100*(m2-m3),
            below_1pp_vs_both=bool((100*(m1-m3)<1.0) and (100*(m2-m3)<1.0))))
    K=pd.DataFrame(k11); K.to_csv(os.path.join(RES,"phase4_k11.csv"),index=False)
    sh=[]
    for root,geom in CELLS4:
        for tk in TICKS:
            g=AL[(AL.root==root)&(AL.geom==geom)&(AL.ticks==tk)].set_index("arm")
            sh.append(dict(root=root,geom=geom,ticks=tk,
                sharpe_A1=g.loc["A1_raw","sharpe"],sharpe_A2=g.loc["A2_ma5","sharpe"],
                sharpe_A3=g.loc["A3_shrunk","sharpe"],
                sharpe_always=g.loc["always_invested","sharpe"],
                d_vs_A1=abs(g.loc["A3_shrunk","sharpe"]-g.loc["A1_raw","sharpe"]),
                d_vs_A2=abs(g.loc["A3_shrunk","sharpe"]-g.loc["A2_ma5","sharpe"]),
                max_d=max(abs(g.loc["A3_shrunk","sharpe"]-g.loc["A1_raw","sharpe"]),
                          abs(g.loc["A3_shrunk","sharpe"]-g.loc["A2_ma5","sharpe"]))))
    SH=pd.DataFrame(sh); SH.to_csv(os.path.join(RES,"phase4_sharpe.csv"),index=False)
    det=dict(criterion_misclass_pp=1.0,criterion_sharpe=0.10,
        max_reduction_vs_A1_pp=float(K.reduction_vs_A1_pp.max()),
        max_reduction_vs_A2_pp=float(K.reduction_vs_A2_pp.max()),
        all_below_1pp_vs_both=bool(K.below_1pp_vs_both.all()),
        max_sharpe_difference=float(SH.max_d.max()),
        all_sharpe_below_0p10=bool((SH.max_d<0.10).all()),
        n_cells=len(K),
        a1_a3_states_differ_total=int(ID.n_states_differ.sum()),
        a1_a3_max_prob_diff=float(ID.max_abs_prob_diff.max()))
    det["K11"]=("FIRES" if (det["all_below_1pp_vs_both"] or det["all_sharpe_below_0p10"])
                else "DOES NOT FIRE")
    timers["total"]=round(time.time()-t0,1)
    det["timers"]=timers
    json.dump(det,open(os.path.join(RES,"phase4_determination.json"),"w"),indent=1)
    print("\n=== PHASE 4: K11 ==="); print(K.round(5).to_string(index=False))
    print(); print(SH.round(4).to_string(index=False))
    print(); print(json.dumps(det,indent=1))
    print(f"S16 PHASES 2-4 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
