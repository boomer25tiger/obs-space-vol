"""S10 Phase 6: arm A6, WITHIN-window fractional volatility (item 84).

A5's defect, and A4's before it, was that roughness varied only ACROSS
sessions. A6 is S05E's A0 in every respect except that the log volatility path
varies WITHIN each window as fractional Brownian motion at Hurst index H, which
is the only place a roughness effect on realized variance can live. The
across-session log-IV law is unchanged from A0, and the panel is aggregated and
fitted by the same `common` functions the real cells use.

sigma_w, the within-window log-volatility scale, is not measured anywhere in
this programme. It is set to sqrt(VAR_LOG_IV) so that within-window dispersion
equals the across-session dispersion, and a sensitivity leg runs at 0.5x and
2x that value. The choice is stated as a choice, not a measurement.
"""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import BASE,RES,GRID_EXT,trig,fitf,fit_diag,logrv_matrix,var_cols,subbars
from fbm import fgn_acf, CirculantEmbedding
CACHE=os.path.join(BASE,"cache")
DIMS={"GLOBEX":(1953,1380),"RTH":(1901,390)}
VAR_LOG_IV=1.02; MASTER=20260822; N_SEEDS=5
HS=[0.05,0.10,0.20,0.30,0.45,0.50]
SIGW=float(np.sqrt(VAR_LOG_IV))
SIGW_SENS=[0.5*SIGW,2.0*SIGW]
OBS_LO,OBS_HI=-1.00,-0.41
def make_a6(geom,H,sigma_w,rng,var_log_iv=VAR_LOG_IV):
    S,n=DIMS[geom]; L=n-1
    x=rng.normal(0.0,np.sqrt(var_log_iv),size=S); iv=np.exp(x)
    emb=CirculantEmbedding(fgn_acf(H,np.arange(L)))
    g=emb.sample(rng,size=S)                     # fGn, unit variance per step
    B=np.cumsum(g,axis=1)                        # fBm, Var(B_t) = t^{2H}
    B=B/np.power(L,H)                            # terminal variance 1
    v=np.exp(sigma_w*B); v=v/v.mean(axis=1,keepdims=True)
    step_var=(iv/L)[:,None]*v
    return rng.standard_normal((S,L))*np.sqrt(step_var),x,emb.neg_eig_count,emb.min_eig
def run(geom,H,sigma_w,children,ci,tag,rows):
    Ms=GRID_EXT[(geom,"1day")]; bs=[]
    for si in range(N_SEEDS):
        child=children[ci+si]; sd=int(child.generate_state(1)[0])
        rng=np.random.Generator(np.random.PCG64(child))
        r,x,neg,mn=make_a6(geom,H,sigma_w,rng)
        L,used=logrv_matrix(r,[m for m in Ms if m<=r.shape[1]])
        y=var_cols(L); f=fitf(used,y); d=fit_diag(used,y,f)
        np.savez_compressed(os.path.join(CACHE,f"a6_{geom}_{tag}_s{si}.npz"),
            logrv=L.astype(np.float32),Ms=np.array(used),y=y,x=x,seed=sd,H=H,
            sigma_w=sigma_w,neg_eig=neg,min_eig=mn,
            ret=(r.astype(np.float32) if si==0 else np.zeros(0,np.float32)))
        if f: bs.append(f["b"])
        rows.append(dict(geom=geom,H=H,sigma_w=sigma_w,tag=tag,seed_index=si,seed=sd,
            b=f["b"] if f else np.nan,c=f["c"] if f else np.nan,
            A=f["A"] if f else np.nan,rmse=f["rmse"] if f else np.nan,cond=d["cond"],
            emb_neg_eig=int(neg),emb_min_eig=float(mn)))
    return ci+N_SEEDS,np.array(bs)
def main():
    t0=time.time(); rows=[]
    ss=np.random.SeedSequence(MASTER)
    children=ss.spawn((len(HS)+2*2)*2*N_SEEDS+20); ci=0
    curve={}
    for geom in ["GLOBEX","RTH"]:
        for H in HS:
            ci,bs=run(geom,H,SIGW,children,ci,f"H{H:.2f}",rows)
            curve[(geom,H)]=bs
            print(f"  {geom:7s} H={H:.2f} sigw={SIGW:.3f}  b={bs.mean():+.4f}"
                  f" sd={bs.std(ddof=1):.4f}",flush=True)
    for geom in ["GLOBEX","RTH"]:
        for sw in SIGW_SENS:
            for H in [0.05,0.50]:
                ci,bs=run(geom,H,sw,children,ci,f"sens_H{H:.2f}_sw{sw:.3f}",rows)
                print(f"  {geom:7s} H={H:.2f} sigw={sw:.3f}  b={bs.mean():+.4f}"
                      f" sd={bs.std(ddof=1):.4f}",flush=True)
    R=pd.DataFrame(rows); R.to_csv(os.path.join(RES,"phase6_a6_raw.csv"),index=False)
    agg=R.groupby(["geom","tag","H","sigma_w"]).agg(
        b_mean=("b","mean"),b_sd=("b","std"),b_min=("b","min"),b_max=("b","max"),
        rmse_mean=("rmse","mean"),cond_mean=("cond","mean"),
        emb_neg_eig=("emb_neg_eig","max"),n_seeds=("seed","nunique")).reset_index()
    agg.to_csv(os.path.join(RES,"phase6_a6_agg.csv"),index=False)
    det={}
    for geom in ["GLOBEX","RTH"]:
        bm=np.array([curve[(geom,H)].mean() for H in HS])
        sd=np.array([curve[(geom,H)].std(ddof=1) for H in HS])
        dif=np.diff(bm)
        mono=bool(np.all(dif>0) or np.all(dif<0))
        # separation: consecutive means differ by more than the pooled seed sd
        pooled=np.sqrt((sd[:-1]**2+sd[1:]**2)/2)
        sep=bool(np.all(np.abs(dif)>pooled))
        det[geom]=dict(H=HS,b_mean=[float(v) for v in bm],b_sd=[float(v) for v in sd],
            consecutive_diff=[float(v) for v in dif],
            pooled_seed_sd=[float(v) for v in pooled],
            monotonic=mono,separated=sep,
            total_range_of_b=float(bm.max()-bm.min()),
            max_seed_sd=float(sd.max()),
            any_in_observed_range=bool(((bm>=OBS_LO)&(bm<=OBS_HI)).any()),
            invertible=bool(mono and sep))
    det["decision"]=("INVERT" if all(det[g]["invertible"] for g in ["GLOBEX","RTH"])
                     else "NOT SUPPORTED")
    det["sigma_w_primary"]=SIGW; det["sigma_w_sensitivity"]=SIGW_SENS
    det["timers"]=dict(phase6=round(time.time()-t0,1))
    json.dump(det,open(os.path.join(RES,"phase6_determination.json"),"w"),indent=1)
    print(); print(json.dumps(det,indent=1))
    print(f"PHASE6 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
