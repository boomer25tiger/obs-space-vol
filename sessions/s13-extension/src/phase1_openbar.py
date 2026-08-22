"""S13 Phase 1: arm A7, the open-bar candidate (items 100, 101).

Measurement comes first and is reported before any arm is generated: the
amplitude of the first and last sub-bar in every window, at every grid point,
per root and geometry, from the pre-2024 panels.

A7 is A0 with one dominant squared return at a FIXED within-window position.
A0 is `make_a6` at sigma_w = 0, which gives a flat within-window profile,
i.i.d. lognormal integrated variance and Gaussian innovations; the dominant
return is imposed by scaling one column of the returned panel by sqrt(kappa),
which multiplies that minute's variance by kappa. Boosting one minute of L by a
constant kappa multiplies total IV by a constant, so log IV shifts by a constant
and Var(log IV) -- hence b -- is unaffected by the rescaling itself.

A8 runs the S12-verified calibrated within-window dispersion and the A7 dominant
return together, since the two mechanisms need not be additive.
"""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common13 import (BASE,RES,CACHE,CELLS,FIVEMIN,OBS_LO,OBS_HI,S11)
from common import GRID_EXT,trig,fitf,fit_diag,cell_windows,subbars,logrv_matrix,var_cols
from phase6_arm_a6 import make_a6, DIMS, VAR_LOG_IV      # S10, unmodified
MASTER_CAL=20260830; MASTER_A7=20260831; MASTER_A8=20260832
N_SEEDS=5; S_CAL=400
HS=[0.05,0.10,0.20,0.30,0.45,0.50]
POSITIONS=["start","quarter","mid","end"]
def pos_index(tag,L):
    return {"start":0,"quarter":L//4,"mid":L//2,"end":L-1}[tag]
def subbar_amplitudes(rw,M):
    """Mean squared return of each sub-bar, relative to the window mean, and the
    share of window realized variance each carries."""
    sb=subbars(rw,M); s2=sb**2
    rv=s2.sum(axis=1); pos=rv>0
    m=s2[pos].mean(axis=0)
    ratio=m/m.mean()
    share=s2[pos]/rv[pos][:,None]
    return dict(first_ratio=float(ratio[0]),last_ratio=float(ratio[-1]),
        first_share=float(share[:,0].mean()),last_share=float(share[:,-1].mean()),
        uniform_share=1.0/M,n_windows=int(pos.sum()))
def a7_panel(geom,kappa,pos_tag,rng,sigma_w=0.0,H=0.50):
    r,x,neg,mn=make_a6(geom,H,sigma_w,rng)
    p=pos_index(pos_tag,r.shape[1])
    r=r.copy(); r[:,p]*=np.sqrt(kappa)
    return r,x,p
def synth_first_ratio(geom,kappa,M,seed,S=S_CAL,sigma_w=0.0,H=0.50):
    rng=np.random.Generator(np.random.PCG64(seed))
    r,_,_=a7_panel(geom,kappa,"start",rng,sigma_w,H)
    return subbar_amplitudes(r[:S],M)["first_ratio"]
def calibrate_kappa(geom,M,target,seed):
    lo,hi=1.0,4000.0
    if synth_first_ratio(geom,hi,M,seed)<target:
        return hi,False,synth_first_ratio(geom,hi,M,seed)
    for _ in range(30):
        mid=0.5*(lo+hi)
        if synth_first_ratio(geom,mid,M,seed)<target: lo=mid
        else: hi=mid
    k=0.5*(lo+hi); return k,True,synth_first_ratio(geom,k,M,seed)
def fit_panel(r,Ms):
    L,used=logrv_matrix(r,[m for m in Ms if m<=r.shape[1]])
    y=var_cols(L); f=fitf(used,y); d=fit_diag(used,y,f)
    return L,used,y,f,d
def main():
    t0=time.time(); timers={}
    # ================= MEASUREMENT, before any arm
    t=time.time(); meas=[]
    for root,geom,btag,hname in CELLS:
        if btag=="B1": continue
        rw,kw,ds=cell_windows(root,geom,hname)
        for M in GRID_EXT[(geom,hname)]:
            if M>rw.shape[1]: continue
            a=subbar_amplitudes(rw,M)
            meas.append(dict(root=root,geom=geom,horizon=hname,M=M,
                sub_bar_minutes=rw.shape[1]/M,**a,
                first_over_uniform=a["first_share"]/a["uniform_share"],
                last_over_uniform=a["last_share"]/a["uniform_share"],
                is_5min=(M==FIVEMIN[(geom,hname)])))
    ME=pd.DataFrame(meas); ME.to_csv(os.path.join(RES,"phase1_amplitudes.csv"),index=False)
    timers["measure"]=round(time.time()-t,1)
    pd.set_option("display.width",250)
    print("=== MEASURED sub-bar amplitudes, five-minute equivalent ===")
    print(ME[ME.is_5min][["root","geom","horizon","M","first_ratio","last_ratio",
                          "first_share","last_share","uniform_share"]].to_string(index=False))
    print("\n=== 1day cells, every grid point ===")
    print(ME[ME.horizon=="1day"][["root","geom","M","first_ratio","last_ratio",
                                  "first_share","last_share"]].to_string(index=False))
    # ================= CALIBRATE kappa to the measured first-sub-bar ratio
    t=time.time(); cal=[]
    ss=np.random.SeedSequence(MASTER_CAL); cs=[int(x) for x in ss.generate_state(16)]
    ci=0
    for geom in ["GLOBEX","RTH"]:
        M=FIVEMIN[(geom,"1day")]
        for root in ["ES","NQ"]:
            tgt=float(ME[(ME.root==root)&(ME.geom==geom)&(ME.horizon=="1day")&
                         (ME.M==M)].first_ratio.iloc[0])
            k,ok,got=calibrate_kappa(geom,M,tgt,cs[ci]); ci+=1
            cal.append(dict(root=root,geom=geom,M=M,target_first_ratio=tgt,
                kappa=k,achieved=got,bracketed=ok,seed=cs[ci-1],
                amplitude_multiple_on_one_minute=k))
            print(f"  calib A7 {root}/{geom} target={tgt:.4f} kappa={k:.2f} "
                  f"got={got:.4f} bracketed={ok}",flush=True)
    CA=pd.DataFrame(cal); CA.to_csv(os.path.join(RES,"phase1_kappa.csv"),index=False)
    timers["calibrate"]=round(time.time()-t,1)
    # ================= ARM A7, position sweep
    t=time.time(); rows=[]
    sq=np.random.SeedSequence(MASTER_A7); ch=sq.spawn(2*2*len(POSITIONS)*N_SEEDS); k=0
    for geom in ["GLOBEX","RTH"]:
        Ms=GRID_EXT[(geom,"1day")]
        for root in ["ES","NQ"]:
            kap=float(CA[(CA.root==root)&(CA.geom==geom)].kappa.iloc[0])
            for ptag in POSITIONS:
                bs=[]
                for si in range(N_SEEDS):
                    child=ch[k]; k+=1; sd=int(child.generate_state(1)[0])
                    rng=np.random.Generator(np.random.PCG64(child))
                    r,x,p=a7_panel(geom,kap,ptag,rng)
                    L,used,y,f,d=fit_panel(r,Ms)
                    np.savez_compressed(os.path.join(CACHE,
                        f"a7_{root}_{geom}_{ptag}_s{si}.npz"),
                        logrv=L.astype(np.float32),Ms=np.array(used),y=y,x=x,seed=sd,
                        kappa=kap,position=p,position_tag=ptag,
                        ret=(r.astype(np.float32) if si==0 else np.zeros(0,np.float32)))
                    if f: bs.append(f["b"])
                    rows.append(dict(arm="A7",root=root,geom=geom,position=ptag,
                        H=np.nan,sigma_w=0.0,kappa=kap,seed_index=si,seed=sd,
                        b=f["b"] if f else np.nan,c=f["c"] if f else np.nan,
                        A=f["A"] if f else np.nan,rmse=f["rmse"] if f else np.nan,
                        cond=d["cond"],corr_cb=d["corr_cb"],corr_Ab=d["corr_Ab"]))
                bs=np.array(bs)
                print(f"  A7 {root}/{geom} pos={ptag:8s} b={bs.mean():+.4f} "
                      f"sd={bs.std(ddof=1):.4f}",flush=True)
    timers["a7"]=round(time.time()-t,1)
    # ================= ARM A8, calibrated dispersion + dominant return
    t=time.time()
    C11=pd.read_csv(os.path.join(S11,"results","phase6_calibration.csv"))
    sq8=np.random.SeedSequence(MASTER_A8); ch8=sq8.spawn(2*2*len(HS)*N_SEEDS); k=0
    for geom in ["GLOBEX","RTH"]:
        Ms=GRID_EXT[(geom,"1day")]
        for root in ["ES","NQ"]:
            kap=float(CA[(CA.root==root)&(CA.geom==geom)].kappa.iloc[0])
            for H in HS:
                sw=float(C11[(C11.root==root)&(C11.geom==geom)&
                             (C11.H==H)].sigma_w_calibrated.iloc[0])
                bs=[]
                for si in range(N_SEEDS):
                    child=ch8[k]; k+=1; sd=int(child.generate_state(1)[0])
                    rng=np.random.Generator(np.random.PCG64(child))
                    r,x,p=a7_panel(geom,kap,"start",rng,sigma_w=sw,H=H)
                    L,used,y,f,d=fit_panel(r,Ms)
                    np.savez_compressed(os.path.join(CACHE,
                        f"a8_{root}_{geom}_H{H:.2f}_s{si}.npz"),
                        logrv=L.astype(np.float32),Ms=np.array(used),y=y,x=x,seed=sd,
                        kappa=kap,sigma_w=sw,H=H,
                        ret=(r.astype(np.float32) if si==0 else np.zeros(0,np.float32)))
                    if f: bs.append(f["b"])
                    rows.append(dict(arm="A8",root=root,geom=geom,position="start",
                        H=H,sigma_w=sw,kappa=kap,seed_index=si,seed=sd,
                        b=f["b"] if f else np.nan,c=f["c"] if f else np.nan,
                        A=f["A"] if f else np.nan,rmse=f["rmse"] if f else np.nan,
                        cond=d["cond"],corr_cb=d["corr_cb"],corr_Ab=d["corr_Ab"]))
                bs=np.array(bs)
                print(f"  A8 {root}/{geom} H={H:.2f} sw={sw:.3f} b={bs.mean():+.4f} "
                      f"sd={bs.std(ddof=1):.4f}",flush=True)
    timers["a8"]=round(time.time()-t,1)
    R=pd.DataFrame(rows); R.to_csv(os.path.join(RES,"phase1_arms_raw.csv"),index=False)
    agg=R.groupby(["arm","root","geom","position","H"],dropna=False).agg(
        b_mean=("b","mean"),b_sd=("b","std"),b_min=("b","min"),b_max=("b","max"),
        rmse_mean=("rmse","mean"),cond_mean=("cond","mean"),
        corr_cb_mean=("corr_cb","mean"),corr_Ab_mean=("corr_Ab","mean"),
        kappa=("kappa","first"),sigma_w=("sigma_w","first"),
        n_seeds=("seed","nunique")).reset_index()
    agg["in_observed_range"]=(agg.b_mean>=OBS_LO)&(agg.b_mean<=OBS_HI)
    agg.to_csv(os.path.join(RES,"phase1_arms_agg.csv"),index=False)
    A6=pd.read_csv(os.path.join(S11,"results","phase6_a6cal_agg.csv"))
    A6["in_observed_range"]=(A6.b_mean>=OBS_LO)&(A6.b_mean<=OBS_HI)
    cmp=[]
    for geom in ["GLOBEX","RTH"]:
        for root in ["ES","NQ"]:
            a6=A6[(A6.root==root)&(A6.geom==geom)]
            a7=agg[(agg.arm=="A7")&(agg.root==root)&(agg.geom==geom)&
                   (agg.position=="start")]
            a8=agg[(agg.arm=="A8")&(agg.root==root)&(agg.geom==geom)]
            cmp.append(dict(root=root,geom=geom,
                A6_b_range=f"{a6.b_mean.max():+.3f} to {a6.b_mean.min():+.3f}",
                A6_in_range=f"{int(a6.in_observed_range.sum())}/{len(a6)}",
                A7_b=float(a7.b_mean.iloc[0]),A7_sd=float(a7.b_sd.iloc[0]),
                A7_in_range=bool(a7.in_observed_range.iloc[0]),
                A8_b_range=f"{a8.b_mean.max():+.3f} to {a8.b_mean.min():+.3f}",
                A8_in_range=f"{int(a8.in_observed_range.sum())}/{len(a8)}",
                A8_b_mean=float(a8.b_mean.mean())))
    CM=pd.DataFrame(cmp); CM.to_csv(os.path.join(RES,"phase1_arm_compare.csv"),index=False)
    a7s=agg[(agg.arm=="A7")]
    det=dict(measurement_first=True,
        kappa_range=[float(CA.kappa.min()),float(CA.kappa.max())],
        first_ratio_measured={f"{r}/{g}":float(v) for r,g,v in
            zip(CA.root,CA.geom,CA.target_first_ratio)},
        A7_position_dependence={f"{r}/{g}":{p:float(agg[(agg.arm=="A7")&
            (agg.root==r)&(agg.geom==g)&(agg.position==p)].b_mean.iloc[0])
            for p in POSITIONS} for r in ["ES","NQ"] for g in ["GLOBEX","RTH"]},
        A7_in_range_by_geom={g:int(a7s[(a7s.geom==g)&(a7s.position=="start")]
            .in_observed_range.sum()) for g in ["GLOBEX","RTH"]},
        A7_n_by_geom={g:int(((a7s.geom==g)&(a7s.position=="start")).sum())
                      for g in ["GLOBEX","RTH"]},
        max_between_seed_sd=float(R.groupby(["arm","root","geom","position","H"],
                                            dropna=False).b.std().max()),
        observed_range=[OBS_LO,OBS_HI],timers=timers)
    json.dump(det,open(os.path.join(RES,"phase1_determination.json"),"w"),indent=1)
    print("\n=== arm comparison ==="); print(CM.to_string(index=False))
    print("\n=== A7 position sweep ===")
    print(agg[agg.arm=="A7"][["root","geom","position","kappa","b_mean","b_sd",
                              "rmse_mean","cond_mean","in_observed_range"]].to_string(index=False))
    print("\n=== A8 ===")
    print(agg[agg.arm=="A8"][["root","geom","H","sigma_w","kappa","b_mean","b_sd",
                              "rmse_mean","cond_mean","in_observed_range"]].to_string(index=False))
    print(); print(json.dumps(det,indent=1))
    print(f"PHASE1 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
