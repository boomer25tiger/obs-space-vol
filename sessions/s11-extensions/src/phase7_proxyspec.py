"""S11 Phase 7: the exponent as a proxy specification test (item 90).

Var(log X_M) = c + A M^b is fitted for realized variance, the flat-top realized
kernel at the BNHLS (2009) bandwidth, and the ZMA (2005) two-scale estimator at
its published subsample count, on IDENTICAL windows. All three estimators and
both tuning rules are imported unmodified from S02 `proxies_robust`; the fit is
S05E `fit_free`.
"""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common11 import BASE,RES,CACHE,CELLS,S07,S10
from common import (GRID_EXT,SPY_GRID,trig,fitf,fit_diag,screen_tight,cell_windows,
                    subbars,var_cols)
from proxies_robust import p1_rv, p2_tsrv, p3_kernel_flattop, kernel_H, tsrv_K, rq
NBOOT=2000; MASTER=20260825
def proxy_matrices(rw,Ms,om2,iv_hat,iq_hat):
    """log X_M matrices for RV, RK and TSRV on identical windows."""
    out={k:np.full((rw.shape[0],len(Ms)),np.nan) for k in ["RV","RK","TSRV"]}
    tune=[]
    for j,M in enumerate(Ms):
        sb=subbars(rw,M)
        v=p1_rv(sb); out["RV"][v>0,j]=np.log(v[v>0])
        H=kernel_H(M,om2,iv_hat)
        k=p3_kernel_flattop(sb,H); out["RK"][k>0,j]=np.log(k[k>0])
        K=tsrv_K(M,om2,iq_hat)
        p=np.concatenate([np.zeros((sb.shape[0],1)),np.cumsum(sb,axis=1)],axis=1)
        ts=p2_tsrv(p,K) if K<M else np.full(sb.shape[0],np.nan)
        ok=np.isfinite(ts)&(ts>0); out["TSRV"][ok,j]=np.log(ts[ok])
        tune.append(dict(M=M,H_kernel=int(H),K_tsrv=int(K),
            n_pos_RV=int((v>0).sum()),n_pos_RK=int((k>0).sum()),
            n_pos_TSRV=int(ok.sum())))
    return out,tune
def boot(L,Ms,seed,nboot=NBOOT):
    rng=np.random.Generator(np.random.PCG64(seed)); n=L.shape[0]
    d=np.full((nboot,3),np.nan)
    for i in range(nboot):
        f=fitf(Ms,var_cols(L,rng.integers(0,n,size=n)))
        if f: d[i]=(f["c"],f["A"],f["b"])
    return d
def summarise(name,proxy,Ms,L,seed,rows,tag):
    good=[j for j,_ in enumerate(Ms) if np.isfinite(L[:,j]).sum()>50]
    Mu=[Ms[j] for j in good]; Lu=L[:,good]
    y=var_cols(Lu); f=fitf(Mu,y)
    if f is None:
        rows.append(dict(cell=name,proxy=proxy,n_grid=len(Mu),c=np.nan,A=np.nan,
            b=np.nan,rmse=np.nan,cond=np.nan,b_lo=np.nan,b_hi=np.nan,b_se=np.nan,
            b_trigamma_ref=np.nan,ref_inside_95=None,screen_tight=False,
            corr_cb=np.nan,corr_Ab=np.nan,n_boot_ok=0)); return
    d=fit_diag(Mu,y,f); ref=fitf(Mu,trig(Mu)); bref=ref["b"] if ref else np.nan
    D=boot(Lu,Mu,seed); ok=np.isfinite(D).all(axis=1); D=D[ok]
    np.savez_compressed(os.path.join(CACHE,f"p7boot_{tag}_{proxy}.npz"),
        draws=D,Ms=np.array(Mu,float),y=y,seed=seed,
        point=np.array([f["c"],f["A"],f["b"]]))
    blo=float(np.percentile(D[:,2],2.5)); bhi=float(np.percentile(D[:,2],97.5))
    C=np.corrcoef(D.T)
    rows.append(dict(cell=name,proxy=proxy,n_grid=len(Mu),
        grid=";".join(map(str,Mu)),c=f["c"],A=f["A"],b=f["b"],rmse=f["rmse"],
        cond=d["cond"],b_lo=blo,b_hi=bhi,b_se=float(D[:,2].std(ddof=1)),
        b_trigamma_ref=bref,
        ref_inside_95=bool(np.isfinite(bref) and blo<=bref<=bhi),
        screen_tight=screen_tight(f,len(Mu)),
        corr_cb=float(C[0,2]),corr_Ab=float(C[1,2]),n_boot_ok=int(len(D))))
def main():
    t0=time.time(); rows=[]; tunes=[]
    ss=np.random.SeedSequence(MASTER); seeds=[int(x) for x in ss.generate_state(128)]
    si=0
    for root,geom,btag,hname in CELLS:
        name=f"{root}/{geom}/{btag}/{hname}"
        rw,kw,ds=cell_windows(root,geom,hname)
        Ms=[m for m in GRID_EXT[(geom,hname)] if m<=rw.shape[1]]
        Mfine=rw.shape[1]
        # pooled plug-ins, the S02 deterministic analogue of per-day plug-ins
        rdense=rw
        om2=float((rdense**2).sum(axis=1).mean()/(2.0*Mfine))
        sparse=subbars(rw,min(Ms[-1],Mfine))
        iv_hat=float(p1_rv(sparse).mean())
        iq_hat=float(rq(sparse,min(Ms[-1],Mfine)).mean())
        mats,tune=proxy_matrices(rw,Ms,om2,iv_hat,iq_hat)
        for t in tune: t.update(cell=name,omega2=om2,iv_hat=iv_hat,iq_hat=iq_hat)
        tunes+=tune
        for proxy in ["RV","RK","TSRV"]:
            summarise(name,proxy,Ms,mats[proxy],seeds[si],rows,
                      f"{root}_{geom}_{btag}_{hname}"); si+=1
        print(f"  {name:26s} done",flush=True)
    # ---------------- SPY, traded tick
    for ven in ["ARCX","XNAS"]:
        z=np.load(os.path.join(S10,"cache",f"spy_tick_logrv_{ven}.npz"))
        # rebuild the traded-tick sub-bar returns so RK and TSRV see the same windows
        zt=np.load(os.path.join(S07,"cache",f"spy_tick_{ven}.npz"))
        tpx=zt["logpx"].astype(np.float64); tcnt=zt["counts"]
        starts=np.concatenate([[0],np.cumsum(tcnt)]); S=len(tcnt); Lmax=23399
        Ms=[min(M,Lmax) for M in SPY_GRID]
        Ms=sorted(set(Ms))
        mats={k:np.full((S,len(Ms)),np.nan) for k in ["RV","RK","TSRV"]}
        # plug-ins at the finest grid
        Mf=Ms[-1]
        dense=np.full((S,Mf),np.nan)
        for i in range(S):
            a,b=starts[i],starts[i+1]; n=b-a
            if n<Mf+1: continue
            e=(np.arange(Mf+1)*(n-1))//Mf; dense[i]=np.diff(tpx[a:b][e])
        dn=np.nan_to_num(dense)
        om2=float((dn**2).sum(axis=1).mean()/(2.0*Mf))
        iv_hat=float(p1_rv(dn).mean()); iq_hat=float(rq(dn,Mf).mean())
        tune=[]
        for j,M in enumerate(Ms):
            sb=np.full((S,M),np.nan)
            for i in range(S):
                a,b=starts[i],starts[i+1]; n=b-a
                if n<M+1: continue
                e=(np.arange(M+1)*(n-1))//M; sb[i]=np.diff(tpx[a:b][e])
            good=np.isfinite(sb).all(axis=1); sbg=sb[good]
            if sbg.shape[0]<50: continue
            v=p1_rv(sbg); idx=np.where(good)[0]
            mats["RV"][idx[v>0],j]=np.log(v[v>0])
            H=kernel_H(M,om2,iv_hat); k=p3_kernel_flattop(sbg,H)
            mats["RK"][idx[k>0],j]=np.log(k[k>0])
            K=tsrv_K(M,om2,iq_hat)
            p=np.concatenate([np.zeros((sbg.shape[0],1)),np.cumsum(sbg,axis=1)],axis=1)
            ts=p2_tsrv(p,K) if K<M else np.full(sbg.shape[0],np.nan)
            okt=np.isfinite(ts)&(ts>0); mats["TSRV"][idx[okt],j]=np.log(ts[okt])
            tune.append(dict(cell=f"SPY/{ven}/TICK",M=M,H_kernel=int(H),K_tsrv=int(K),
                n_pos_RV=int((v>0).sum()),n_pos_RK=int((k>0).sum()),
                n_pos_TSRV=int(okt.sum()),omega2=om2,iv_hat=iv_hat,iq_hat=iq_hat))
        tunes+=tune
        for proxy in ["RV","RK","TSRV"]:
            summarise(f"SPY/{ven}/TICK",proxy,Ms,mats[proxy],seeds[si],rows,
                      f"SPY_{ven}"); si+=1
        print(f"  SPY/{ven} done",flush=True)
    R=pd.DataFrame(rows); R.to_csv(os.path.join(RES,"phase7_proxy_fits.csv"),index=False)
    pd.DataFrame(tunes).to_csv(os.path.join(RES,"phase7_tuning.csv"),index=False)
    P=R.pivot_table(index="cell",columns="proxy",values="b").reset_index()
    P["RK_minus_RV"]=P.RK-P.RV; P["TSRV_minus_RV"]=P.TSRV-P.RV
    P.to_csv(os.path.join(RES,"phase7_proxy_compare.csv"),index=False)
    o=dict(n_cells=int(R.cell.nunique()),n_fits=len(R),n_boot=NBOOT,master=MASTER,
        ref_inside_by_proxy={p:int(R[(R.proxy==p)&(R.ref_inside_95==True)].shape[0])
                             for p in ["RV","RK","TSRV"]},
        n_by_proxy={p:int((R.proxy==p).sum()) for p in ["RV","RK","TSRV"]},
        mean_b={p:float(R[R.proxy==p].b.mean()) for p in ["RV","RK","TSRV"]},
        mean_RK_minus_RV=float(P.RK_minus_RV.mean()),
        mean_TSRV_minus_RV=float(P.TSRV_minus_RV.mean()),
        n_RK_steeper=int((P.RK_minus_RV<0).sum()),
        n_TSRV_steeper=int((P.TSRV_minus_RV<0).sum()),
        n_cells_compared=int(len(P)),
        screen_tight_by_proxy={p:int(R[(R.proxy==p)&(R.screen_tight)].shape[0])
                               for p in ["RV","RK","TSRV"]},
        timers=dict(phase7=round(time.time()-t0,1)))
    json.dump(o,open(os.path.join(RES,"phase7_summary.json"),"w"),indent=1)
    print(); print(R[["cell","proxy","n_grid","b","b_lo","b_hi","b_trigamma_ref",
                      "ref_inside_95","rmse","cond","screen_tight"]].to_string(index=False))
    print(); print(P.to_string(index=False)); print(); print(json.dumps(o,indent=1))
    print(f"PHASE7 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
