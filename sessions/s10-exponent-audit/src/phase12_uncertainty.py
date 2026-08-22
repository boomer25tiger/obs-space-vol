"""S10 Phases 1 and 2: uncertainty on b, and grid sensitivity / identifiability."""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import (BASE,RES,CELLS,GRID_EXT,GRID_S05,SPY_GRID,NPAR,trig,fitf,fit_diag,
                    screen_old,screen_tight,cell_windows,logrv_matrix,var_cols,
                    spy_logrv_tick)
CACHE=os.path.join(BASE,"cache"); os.makedirs(CACHE,exist_ok=True)
NBOOT=2000; MASTER=20260820
def boot_cell(L,Ms,seed,nboot=NBOOT):
    rng=np.random.Generator(np.random.PCG64(seed))
    n=L.shape[0]; draws=np.full((nboot,3),np.nan)
    for k in range(nboot):
        idx=rng.integers(0,n,size=n)
        f=fitf(Ms,var_cols(L,idx))
        if f: draws[k]=(f["c"],f["A"],f["b"])
    return draws
def summarise(name,Ms,L,seed,rows,corr_rows,drawfile):
    y=var_cols(L)
    f=fitf(Ms,y); d=fit_diag(Ms,y,f)
    ref=fitf(Ms,trig(Ms))
    b_ref=ref["b"] if ref else np.nan
    draws=boot_cell(L,Ms,seed)
    np.savez_compressed(drawfile,draws=draws,Ms=np.array(Ms,float),y=y,seed=seed,
                        point=np.array([f["c"],f["A"],f["b"]]) if f else np.full(3,np.nan))
    ok=np.isfinite(draws).all(axis=1); D=draws[ok]
    q=lambda col,p: float(np.percentile(D[:,col],p)) if len(D)>50 else np.nan
    se=lambda col: float(D[:,col].std(ddof=1)) if len(D)>50 else np.nan
    b_lo,b_hi=q(2,2.5),q(2,97.5)
    inside=bool(np.isfinite(b_ref) and b_lo<=b_ref<=b_hi)
    p_flatter=float((D[:,2]>b_ref).mean()) if (len(D)>50 and np.isfinite(b_ref)) else np.nan
    C=np.corrcoef(D.T) if len(D)>50 else np.full((3,3),np.nan)
    rows.append(dict(cell=name,n_grid=len(Ms),n_windows=int(L.shape[0]),
        c=f["c"] if f else np.nan,c_lo=q(0,2.5),c_hi=q(0,97.5),c_se=se(0),
        A=f["A"] if f else np.nan,A_lo=q(1,2.5),A_hi=q(1,97.5),A_se=se(1),
        b=f["b"] if f else np.nan,b_lo=b_lo,b_hi=b_hi,b_se=se(2),
        rmse=f["rmse"] if f else np.nan,cond=d["cond"],
        b_trigamma_ref=b_ref,ref_inside_95=inside,p_b_above_ref=p_flatter,
        n_boot_ok=int(len(D)),
        screen_old=screen_old(f),screen_tight=screen_tight(f,len(Ms))))
    for i,ni in enumerate(["c","A","b"]):
        for j,nj in enumerate(["c","A","b"]):
            corr_rows.append(dict(cell=name,par_i=ni,par_j=nj,
                boot_corr=float(C[i,j]),asym_corr=(
                    d["corr_cA"] if {ni,nj}=={"c","A"} else
                    d["corr_cb"] if {ni,nj}=={"c","b"} else
                    d["corr_Ab"] if {ni,nj}=={"A","b"} else (1.0 if ni==nj else np.nan))))
    return f,d,b_ref,D
def main():
    t0=time.time(); timers={}
    rows=[]; corr=[]; loo=[]; gridcmp=[]; screen=[]
    ss=np.random.SeedSequence(MASTER); seeds=[int(x) for x in ss.generate_state(64)]
    si=0
    LOGRV={}
    # ---------------- futures cells
    for root,geom,btag,hname in CELLS:
        name=f"{root}/{geom}/{btag}/{hname}"
        rw,kw,ds=cell_windows(root,geom,hname)
        Me=[m for m in GRID_EXT[(geom,hname)] if m<=rw.shape[1]]
        L,used=logrv_matrix(rw,Me); Me=used
        LOGRV[name]=(L,Me,ds)
        f,d,b_ref,D=summarise(name,Me,L,seeds[si],rows,corr,
                              os.path.join(CACHE,f"boot_{root}_{geom}_{btag}_{hname}.npz"))
        si+=1
        # ---- Phase 2: leave-one-out
        y=var_cols(L)
        best=(None,-1.0)
        for j,M in enumerate(Me):
            keep=[k for k in range(len(Me)) if k!=j]
            fj=fitf([Me[k] for k in keep],y[keep])
            dev=abs(fj["b"]-f["b"]) if (fj and f) else np.nan
            loo.append(dict(cell=name,dropped_M=M,b=fj["b"] if fj else np.nan,
                b_full=f["b"] if f else np.nan,deviation=dev,
                rmse=fj["rmse"] if fj else np.nan,n_grid=len(keep)))
            if np.isfinite(dev) and dev>best[1]: best=(M,dev)
        # ---- Phase 2: restricted vs extended
        Mr=[m for m in GRID_S05[(geom,hname)] if m<=rw.shape[1]]
        Lr,ur=logrv_matrix(rw,Mr); Mr=ur
        fr=fitf(Mr,var_cols(Lr)) if len(Mr)>=4 else None
        dr=fit_diag(Mr,var_cols(Lr),fr) if fr else dict(cond=np.nan)
        refr=fitf(Mr,trig(Mr)) if len(Mr)>=4 else None
        gridcmp.append(dict(cell=name,n_ext=len(Me),b_ext=f["b"] if f else np.nan,
            cond_ext=d["cond"],rmse_ext=f["rmse"] if f else np.nan,
            n_res=len(Mr),b_res=fr["b"] if fr else np.nan,
            cond_res=dr["cond"],rmse_res=fr["rmse"] if fr else np.nan,
            deviation=abs(fr["b"]-f["b"]) if (fr and f) else np.nan,
            worst_drop_M=best[0],worst_drop_deviation=best[1] if best[0] else np.nan,
            b_ref_ext=b_ref,b_ref_res=refr["b"] if refr else np.nan))
        for tag,ff,npts in [("extended",f,len(Me)),("restricted_S05",fr,len(Mr))]:
            screen.append(dict(cell=name,range=tag,n_grid=npts,
                b=ff["b"] if ff else np.nan,A=ff["A"] if ff else np.nan,
                rmse=ff["rmse"] if ff else np.nan,
                screen_old_pass=screen_old(ff),screen_tight_pass=screen_tight(ff,npts),
                fail_reason=("" if screen_tight(ff,npts) else
                    ("no fit" if ff is None else
                     "; ".join(([f"n_grid {npts} < {2*NPAR}"] if npts<2*NPAR else [])+
                               ([f"|b|={abs(ff['b']):.3g} <= 0.01"] if abs(ff["b"])<=0.01 else [])+
                               ([f"A={ff['A']:.3g} <= 0"] if ff["A"]<=0 else [])+
                               ([f"b={ff['b']:.3g} >= 0"] if ff["b"]>=0 else []))))))
        print(f"  {name:26s} b={f['b']:+.4f} [{rows[-1]['b_lo']:+.4f},{rows[-1]['b_hi']:+.4f}]"
              f" ref={b_ref:+.4f} inside={rows[-1]['ref_inside_95']} cond={d['cond']:.3g}",flush=True)
    timers["phase1_futures"]=round(time.time()-t0,1)
    # ---------------- SPY, both venues, traded-tick
    t=time.time()
    for ven in ["ARCX","XNAS"]:
        cf=os.path.join(CACHE,f"spy_tick_logrv_{ven}.npz")
        if os.path.exists(cf):
            z=np.load(cf); L=z["L"]; Ms=[int(m) for m in z["Ms"]]; ds=np.array(z["dates"],dtype="U10")
        else:
            L,ds,Ms=spy_logrv_tick(ven)
            np.savez_compressed(cf,L=L,Ms=np.array(Ms),dates=ds)
        good=[j for j,m in enumerate(Ms) if np.isfinite(L[:,j]).sum()>30]
        Ms=[Ms[j] for j in good]; L=L[:,good]
        name=f"SPY/{ven}/TICK"
        f,d,b_ref,D=summarise(name,Ms,L,seeds[si],rows,corr,
                              os.path.join(CACHE,f"boot_SPY_{ven}.npz")); si+=1
        y=var_cols(L); best=(None,-1.0)
        for j,M in enumerate(Ms):
            keep=[k for k in range(len(Ms)) if k!=j]
            fj=fitf([Ms[k] for k in keep],y[keep])
            dev=abs(fj["b"]-f["b"]) if (fj and f) else np.nan
            loo.append(dict(cell=name,dropped_M=M,b=fj["b"] if fj else np.nan,
                b_full=f["b"],deviation=dev,rmse=fj["rmse"] if fj else np.nan,
                n_grid=len(keep)))
            if np.isfinite(dev) and dev>best[1]: best=(M,dev)
        gridcmp.append(dict(cell=name,n_ext=len(Ms),b_ext=f["b"],cond_ext=d["cond"],
            rmse_ext=f["rmse"],n_res=0,b_res=np.nan,cond_res=np.nan,rmse_res=np.nan,
            deviation=np.nan,worst_drop_M=best[0],worst_drop_deviation=best[1],
            b_ref_ext=b_ref,b_ref_res=np.nan))
        screen.append(dict(cell=name,range="tick_full",n_grid=len(Ms),b=f["b"],A=f["A"],
            rmse=f["rmse"],screen_old_pass=screen_old(f),
            screen_tight_pass=screen_tight(f,len(Ms)),fail_reason=""))
        print(f"  {name:26s} b={f['b']:+.4f} [{rows[-1]['b_lo']:+.4f},{rows[-1]['b_hi']:+.4f}]"
              f" ref={b_ref:+.4f} inside={rows[-1]['ref_inside_95']} cond={d['cond']:.3g}",flush=True)
    timers["phase1_spy"]=round(time.time()-t,1)
    P1=pd.DataFrame(rows); P1.to_csv(os.path.join(RES,"phase1_bootstrap.csv"),index=False)
    pd.DataFrame(corr).to_csv(os.path.join(RES,"phase1_corr.csv"),index=False)
    pd.DataFrame(loo).to_csv(os.path.join(RES,"phase2_leave_one_out.csv"),index=False)
    pd.DataFrame(gridcmp).to_csv(os.path.join(RES,"phase2_grid_compare.csv"),index=False)
    pd.DataFrame(screen).to_csv(os.path.join(RES,"phase2_screen.csv"),index=False)
    summ=dict(master_seed=MASTER,n_boot=NBOOT,seeds_used=seeds[:si],
        n_cells=len(P1),n_ref_inside_95=int(P1.ref_inside_95.sum()),
        cells_ref_inside=[c for c,v in zip(P1.cell,P1.ref_inside_95) if v],
        median_b_se=float(P1.b_se.median()),max_b_se=float(P1.b_se.max()),
        median_cond=float(P1.cond.median()),max_cond=float(P1.cond.max()),
        n_screen_old_pass=int(pd.DataFrame(screen).screen_old_pass.sum()),
        n_screen_tight_pass=int(pd.DataFrame(screen).screen_tight_pass.sum()),
        n_screen_rows=len(screen),timers=timers)
    json.dump(summ,open(os.path.join(RES,"phase12_summary.json"),"w"),indent=1)
    print(); print(json.dumps(summ,indent=1)[:2000])
    print(f"PHASE1+2 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
