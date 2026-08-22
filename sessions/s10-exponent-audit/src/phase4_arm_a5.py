"""S10 Phase 4: arm A5, Student-t innovations.

A5 is S05E's A0 in every respect except the innovation law: log IV is drawn
i.i.d. lognormal at VAR_LOG_IV, there is no diurnal profile, no jumps and no
padding, and the panel is aggregated and fitted by the SAME functions the real
cells use (`common.logrv_matrix`, `common.var_cols`, `common.fitf`), which are
the S08/S09 lambda code path and S05E `fit_free` unchanged.

For each degrees-of-freedom setting a second sub-arm runs with Var(log IV) = 0.
That sub-arm carries no integrated-variance variation at all, so its
Var(log RV_M) curve IS the sampling variance of log RV under that innovation
law -- the heavy-tailed generalisation of trigamma(M/2). Its fitted exponent is
the correct reference for that setting.
"""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import BASE,RES,GRID_EXT,trig,fitf,fit_diag,logrv_matrix,var_cols
CACHE=os.path.join(BASE,"cache")
DIMS={"GLOBEX":(1953,1380),"RTH":(1901,390)}     # S05E DIMS
VAR_LOG_IV=1.02                                   # S05E, DECISIONS item 36 intercept
MASTER=20260821; N_SEEDS=5
DF_SETTINGS=[("gaussian",np.inf),("nu2.95",2.95),("nu3",3.0),("nu3.67",3.67),
             ("nu4",4.0),("nu6",6.0),("nu10",10.0)]
TAIL_LO,TAIL_HI=2.95,3.67          # S04 measured tail index range
OBS_LO,OBS_HI=-1.00,-0.41          # observed b range, S07/S08 headline
def make_a5(geom,nu,var_log_iv,rng):
    """S05E A0 with a Student-t innovation law standardised to unit variance."""
    S,n=DIMS[geom]; L=n-1
    x=rng.normal(0.0,np.sqrt(var_log_iv),size=S) if var_log_iv>0 else np.zeros(S)
    iv=np.exp(x)
    step_var=np.outer(iv/L,np.ones(L))            # A0: flat profile
    if np.isinf(nu): z=rng.standard_normal((S,L))
    else: z=rng.standard_t(nu,size=(S,L))/np.sqrt(nu/(nu-2.0))
    return z*np.sqrt(step_var),x
def main():
    t0=time.time(); rows=[]; paths=[]
    ss=np.random.SeedSequence(MASTER)
    children=ss.spawn(len(DF_SETTINGS)*2*len(DIMS)*N_SEEDS)
    ci=0; seedlog=[]
    for geom in ["GLOBEX","RTH"]:
        Ms=GRID_EXT[(geom,"1day")]
        b_trig=fitf(Ms,trig(Ms))["b"]
        for tag,nu in DF_SETTINGS:
            for sub,vli in [("signal",VAR_LOG_IV),("reference",0.0)]:
                bs=[]; cs=[]
                for si in range(N_SEEDS):
                    child=children[ci]; ci+=1
                    sd=int(child.generate_state(1)[0])
                    seedlog.append(dict(geom=geom,df=tag,subarm=sub,seed_index=si,seed=sd))
                    rng=np.random.Generator(np.random.PCG64(child))
                    r,x=make_a5(geom,nu,vli,rng)
                    L,used=logrv_matrix(r,[m for m in Ms if m<=r.shape[1]])
                    y=var_cols(L); f=fitf(used,y); d=fit_diag(used,y,f)
                    np.savez_compressed(os.path.join(CACHE,
                        f"a5_{geom}_{tag}_{sub}_s{si}.npz"),
                        logrv=L.astype(np.float32),Ms=np.array(used),y=y,x=x,seed=sd,
                        nu=(np.inf if np.isinf(nu) else nu),var_log_iv=vli,
                        ret=(r.astype(np.float32) if si==0 else np.zeros(0,np.float32)))
                    if si==0: paths.append(f"a5_{geom}_{tag}_{sub}_s0.npz (full return panel)")
                    if f: bs.append(f["b"]); cs.append(f["c"])
                    rows.append(dict(geom=geom,df=tag,nu=(np.nan if np.isinf(nu) else nu),
                        subarm=sub,seed_index=si,seed=sd,n_grid=len(used),
                        b=f["b"] if f else np.nan,c=f["c"] if f else np.nan,
                        A=f["A"] if f else np.nan,rmse=f["rmse"] if f else np.nan,
                        cond=d["cond"],b_trigamma_analytic=b_trig))
                print(f"  {geom:7s} {tag:9s} {sub:9s} b={np.mean(bs):+.4f} "
                      f"sd={np.std(bs,ddof=1):.4f} n={len(bs)}",flush=True)
    R=pd.DataFrame(rows); R.to_csv(os.path.join(RES,"phase4_a5_raw.csv"),index=False)
    pd.DataFrame(seedlog).to_csv(os.path.join(RES,"phase4_seeds.csv"),index=False)
    agg=R.groupby(["geom","df","nu","subarm"],dropna=False).agg(
        b_mean=("b","mean"),b_sd=("b","std"),b_min=("b","min"),b_max=("b","max"),
        c_mean=("c","mean"),rmse_mean=("rmse","mean"),cond_mean=("cond","mean"),
        n_seeds=("seed","nunique")).reset_index()
    agg.to_csv(os.path.join(RES,"phase4_a5_agg.csv"),index=False)
    # signal arm against its own Gaussian baseline and against its own reference
    P=agg.pivot_table(index=["geom","df"],columns="subarm",
                      values=["b_mean","b_sd"]).reset_index()
    P.columns=["_".join([c for c in col if c]) for col in P.columns]
    NU={t:(np.nan if np.isinf(v) else v) for t,v in DF_SETTINGS}
    P["nu"]=[NU[t] for t in P.df]
    P=P.sort_values(["geom","nu"],na_position="first").reset_index(drop=True)
    base={g:float(P[(P.df=="gaussian")&(P.geom==g)].b_mean_signal.iloc[0])
          for g in ["GLOBEX","RTH"]}
    P["b_minus_gaussian"]=P.b_mean_signal-np.array([base[g] for g in P.geom])
    P["b_ref_same_law"]=P.b_mean_reference
    P["gap_signal_minus_ref"]=P.b_mean_signal-P.b_mean_reference
    P["in_observed_range"]=(P.b_mean_signal>=OBS_LO)&(P.b_mean_signal<=OBS_HI)
    P.to_csv(os.path.join(RES,"phase4_a5_summary.csv"),index=False)
    # share of the real gap accounted for, measured at the S04 tail-index range
    real=pd.read_csv(os.path.join(RES,"phase1_bootstrap.csv"))
    real=real[real.cell.str.contains("/1day")]
    shares=[]
    for geom in ["GLOBEX","RTH"]:
        g=P[P.geom==geom]
        gb=float(g[g.df=="gaussian"].b_mean_signal.iloc[0])
        gref=float(g[g.df=="gaussian"].b_mean_reference.iloc[0])
        for tag in ["nu2.95","nu3","nu3.67"]:
            r=g[g.df==tag].iloc[0]
            shares.append(dict(geom=geom,df=tag,
                b_gaussian_signal=gb,b_t_signal=float(r.b_mean_signal),
                move_from_gaussian=float(r.b_mean_signal)-gb,
                b_gaussian_reference=gref,b_t_reference=float(r.b_mean_reference),
                reference_move=float(r.b_mean_reference)-gref,
                real_b_mean=float(real[real.cell.str.contains(geom)].b.mean()),
                real_gap_to_trigamma=float(
                    (real[real.cell.str.contains(geom)].b -
                     real[real.cell.str.contains(geom)].b_trigamma_ref).mean()),
                share_of_real_gap=((float(r.b_mean_signal)-gb)/float(
                    (real[real.cell.str.contains(geom)].b -
                     real[real.cell.str.contains(geom)].b_trigamma_ref).mean())),
                in_observed_range=bool(OBS_LO<=float(r.b_mean_signal)<=OBS_HI)))
    SH=pd.DataFrame(shares); SH.to_csv(os.path.join(RES,"phase4_share.csv"),index=False)
    o=dict(master=MASTER,n_seeds=N_SEEDS,settings=[t for t,_ in DF_SETTINGS],
        tail_index_range=[TAIL_LO,TAIL_HI],observed_b_range=[OBS_LO,OBS_HI],
        max_between_seed_sd=float(R.b.groupby([R.geom,R.df,R.subarm]).std().max()),
        share_mean=float(SH.share_of_real_gap.mean()),
        share_max=float(SH.share_of_real_gap.max()),
        any_in_observed_range=bool(SH.in_observed_range.any()),
        full_paths_persisted=paths,timers=dict(phase4=round(time.time()-t0,1)))
    json.dump(o,open(os.path.join(RES,"phase4_summary.json"),"w"),indent=1)
    print(); print(P[["geom","df","b_mean_signal","b_sd_signal","b_minus_gaussian",
                      "b_ref_same_law","gap_signal_minus_ref","in_observed_range"]].to_string(index=False))
    print(); print(SH[["geom","df","b_t_signal","move_from_gaussian","reference_move",
                       "real_gap_to_trigamma","share_of_real_gap","in_observed_range"]].to_string(index=False))
    print(); print(json.dumps({k:v for k,v in o.items() if k!="full_paths_persisted"},indent=1))
    print(f"PHASE4 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
