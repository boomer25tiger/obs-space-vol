"""S11 Phase 6: roughness with sigma_w CALIBRATED (item 89), not chosen.

Within-window volatility dispersion is measured as RQ/RV^2, whose value under
constant within-window volatility is exactly 1 (RQ = (M/3)sum r^4 estimates
sigma^4 and RV = sigma^2). The measured value is taken from the real panels via
`parta.quart_suite`, the Part A code path, and the synthetic is passed through
the SAME function at the same M and the same window count, so the finite-M bias
in the ratio is identical on both sides and cancels in the calibration.

`make_a6` is imported unmodified from S10.
"""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common11 import BASE,RES,CACHE,CELLS,FIVEMIN
from common import GRID_EXT,trig,fitf,fit_diag,cell_windows,subbars,logrv_matrix,var_cols
from parta import quart_suite
from phase6_arm_a6 import make_a6, DIMS, VAR_LOG_IV     # S10, unmodified
MASTER_CAL=20260823; MASTER_SWEEP=20260824; N_SEEDS=5
HS=[0.05,0.10,0.20,0.30,0.45,0.50]
SIGW_S10=float(np.sqrt(VAR_LOG_IV))
OBS_LO,OBS_HI=-1.00,-0.41
S_CAL=400          # sessions used inside the bisection, full DIMS for the sweep
def ratio_real(root,geom,hname,M):
    rw,kw,ds=cell_windows(root,geom,hname)
    sb=subbars(rw,M); q=quart_suite(sb,M); rq,rv=q["RQ_RV"]
    pos=rv>0
    return float(np.mean(rq[pos]/np.maximum(rv[pos]**2,1e-300))),int(pos.sum())
def ratio_synth(geom,H,sw,M,seed,S=None):
    rng=np.random.Generator(np.random.PCG64(seed))
    r,x,neg,mn=make_a6(geom,H,sw,rng)
    if S is not None: r=r[:S]
    sb=subbars(r,M); q=quart_suite(sb,M); rq,rv=q["RQ_RV"]
    pos=rv>0
    return float(np.mean(rq[pos]/np.maximum(rv[pos]**2,1e-300)))
def calibrate(geom,H,M,target,seed):
    lo,hi=1e-3,6.0
    if ratio_synth(geom,H,hi,M,seed,S_CAL)<target: return hi,False,ratio_synth(geom,H,hi,M,seed,S_CAL)
    if ratio_synth(geom,H,lo,M,seed,S_CAL)>target: return lo,False,ratio_synth(geom,H,lo,M,seed,S_CAL)
    for _ in range(24):
        mid=0.5*(lo+hi)
        if ratio_synth(geom,H,mid,M,seed,S_CAL)<target: lo=mid
        else: hi=mid
    sw=0.5*(lo+hi)
    return sw,True,ratio_synth(geom,H,sw,M,seed,S_CAL)
def main():
    t0=time.time(); timers={}
    # ---------------- measured ratio, every grid point
    t=time.time(); meas=[]
    for root,geom,btag,hname in CELLS:
        if btag=="B1": continue
        for M in GRID_EXT[(geom,hname)]:
            rw,_,_=cell_windows(root,geom,hname)
            if M>rw.shape[1]: continue
            rr,n=ratio_real(root,geom,hname,M)
            meas.append(dict(root=root,geom=geom,horizon=hname,M=M,rq_over_rv2=rr,
                n_windows=n,constant_vol_value=1.0,excess=rr-1.0,
                asym_var=(2.0/M)*rr,trigamma=float(trig(M)),
                ratio_to_trigamma=((2.0/M)*rr)/float(trig(M)),
                is_5min=(M==FIVEMIN[(geom,hname)])))
    ME=pd.DataFrame(meas); ME.to_csv(os.path.join(RES,"phase6_measured_ratio.csv"),index=False)
    timers["measure"]=round(time.time()-t,1)
    print("=== measured RQ/RV^2 at the five-minute equivalent ===")
    print(ME[ME.is_5min][["root","geom","horizon","M","rq_over_rv2","excess",
                          "ratio_to_trigamma"]].to_string(index=False))
    # ---------------- calibrate sigma_w per (root, geom) x H at the 5-min M
    t=time.time(); cal=[]
    ss=np.random.SeedSequence(MASTER_CAL); cseeds=[int(x) for x in ss.generate_state(64)]
    ci=0
    for geom in ["GLOBEX","RTH"]:
        M=FIVEMIN[(geom,"1day")]
        for root in ["ES","NQ"]:
            tgt=float(ME[(ME.root==root)&(ME.geom==geom)&(ME.horizon=="1day")&
                         (ME.M==M)].rq_over_rv2.iloc[0])
            for H in HS:
                sw,ok,got=calibrate(geom,H,M,tgt,cseeds[ci]); ci+=1
                cal.append(dict(root=root,geom=geom,H=H,M=M,target_ratio=tgt,
                    sigma_w_calibrated=sw,achieved_ratio=got,bracketed=ok,
                    sigma_w_s10=SIGW_S10,seed=cseeds[ci-1]))
                print(f"  calib {root}/{geom} H={H:.2f} target={tgt:.4f} "
                      f"sigma_w={sw:.4f} got={got:.4f} bracketed={ok}",flush=True)
    C=pd.DataFrame(cal); C.to_csv(os.path.join(RES,"phase6_calibration.csv"),index=False)
    timers["calibrate"]=round(time.time()-t,1)
    # ---------------- A6 sweep at calibrated sigma_w, full DIMS, 5 seeds
    t=time.time(); rows=[]
    sw2=np.random.SeedSequence(MASTER_SWEEP)
    children=sw2.spawn(len(HS)*2*2*N_SEEDS); k=0
    for geom in ["GLOBEX","RTH"]:
        Ms=GRID_EXT[(geom,"1day")]
        for root in ["ES","NQ"]:
            for H in HS:
                swv=float(C[(C.root==root)&(C.geom==geom)&(C.H==H)].sigma_w_calibrated.iloc[0])
                bs=[]
                for si in range(N_SEEDS):
                    child=children[k]; k+=1; sd=int(child.generate_state(1)[0])
                    rng=np.random.Generator(np.random.PCG64(child))
                    r,x,neg,mn=make_a6(geom,H,swv,rng)
                    L,used=logrv_matrix(r,[m for m in Ms if m<=r.shape[1]])
                    y=var_cols(L); f=fitf(used,y); d=fit_diag(used,y,f)
                    np.savez_compressed(os.path.join(CACHE,
                        f"a6cal_{root}_{geom}_H{H:.2f}_s{si}.npz"),
                        logrv=L.astype(np.float32),Ms=np.array(used),y=y,x=x,seed=sd,
                        H=H,sigma_w=swv,neg_eig=neg,min_eig=mn,
                        ret=(r.astype(np.float32) if si==0 else np.zeros(0,np.float32)))
                    if f: bs.append(f["b"])
                    rows.append(dict(root=root,geom=geom,H=H,sigma_w=swv,seed_index=si,
                        seed=sd,b=f["b"] if f else np.nan,c=f["c"] if f else np.nan,
                        A=f["A"] if f else np.nan,rmse=f["rmse"] if f else np.nan,
                        cond=d["cond"],emb_neg_eig=int(neg),emb_min_eig=float(mn)))
                bs=np.array(bs)
                print(f"  {root}/{geom} H={H:.2f} sw={swv:.4f}  b={bs.mean():+.4f}"
                      f" sd={bs.std(ddof=1):.4f}",flush=True)
    R=pd.DataFrame(rows); R.to_csv(os.path.join(RES,"phase6_a6cal_raw.csv"),index=False)
    agg=R.groupby(["root","geom","H","sigma_w"]).agg(
        b_mean=("b","mean"),b_sd=("b","std"),b_min=("b","min"),b_max=("b","max"),
        rmse_mean=("rmse","mean"),cond_mean=("cond","mean"),
        emb_neg_eig=("emb_neg_eig","max"),n_seeds=("seed","nunique")).reset_index()
    agg.to_csv(os.path.join(RES,"phase6_a6cal_agg.csv"),index=False)
    det={}
    for root in ["ES","NQ"]:
        for geom in ["GLOBEX","RTH"]:
            g=agg[(agg.root==root)&(agg.geom==geom)].sort_values("H")
            bm=g.b_mean.values; sd=g.b_sd.values; dif=np.diff(bm)
            pooled=np.sqrt((sd[:-1]**2+sd[1:]**2)/2)
            mono=bool(np.all(dif>0) or np.all(dif<0))
            sep=bool(np.all(np.abs(dif)>pooled))
            det[f"{root}/{geom}"]=dict(H=HS,b_mean=[float(v) for v in bm],
                b_sd=[float(v) for v in sd],
                sigma_w=[float(v) for v in g.sigma_w.values],
                consecutive_diff=[float(v) for v in dif],
                pooled_seed_sd=[float(v) for v in pooled],
                monotonic=mono,separated=sep,
                total_range_of_b=float(bm.max()-bm.min()),max_seed_sd=float(sd.max()),
                any_in_observed_range=bool(((bm>=OBS_LO)&(bm<=OBS_HI)).any()),
                invertible=bool(mono and sep))
    det["decision"]=("INVERT" if all(v["invertible"] for k,v in det.items()
                                     if isinstance(v,dict)) else "NOT SUPPORTED")
    det["sigma_w_s10_assumed"]=SIGW_S10
    det["sigma_w_calibrated_range"]=[float(C.sigma_w_calibrated.min()),
                                     float(C.sigma_w_calibrated.max())]
    det["timers"]=timers; det["timers"]["sweep"]=round(time.time()-t,1)
    json.dump(det,open(os.path.join(RES,"phase6_determination.json"),"w"),indent=1)
    print(); print(json.dumps(det,indent=1))
    print(f"PHASE6 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
