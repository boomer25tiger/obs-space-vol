"""S12 Phase 2: verification of the S11 sigma_w calibration (item 96).

`make_a6` and `quart_suite` are imported unmodified; nothing is reimplemented.
The sweep exposes the sigma_w -> RQ/RV^2 mapping directly instead of inferring
it, and reports alongside each sigma_w the quantity item 96 is actually about:
the standard deviation of log within-window variance that sigma_w produces.
"""
import json, os, sys, time
import numpy as np, pandas as pd
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
S10=os.path.join(ROOT,"sessions","s10-exponent-audit")
S11=os.path.join(ROOT,"sessions","s11-extensions")
for p in [os.path.join(S11,"src"),os.path.join(S10,"src"),
          os.path.join(ROOT,"sessions","s05-reliability-mcs","src"),
          os.path.join(ROOT,"sessions","s01-estimator-validation","src"),
          os.path.join(ROOT,"sessions","s07-completion-and-spy","src")]:
    sys.path.insert(0,p)
from common import GRID_EXT,cell_windows,subbars,fitf,fit_diag,logrv_matrix,var_cols
from parta import quart_suite
from phase6_arm_a6 import make_a6, DIMS, VAR_LOG_IV      # S10, unmodified
from fbm import fgn_acf, CirculantEmbedding
FIVEMIN={("RTH","1day"):78,("GLOBEX","1day"):276}
HS=[0.05,0.10,0.20,0.30,0.45,0.50]
S_CAL=400                       # the S11 bisection sample size, reproduced here
MASTER_SWEEP=20260826; MASTER_RERUN=20260827; N_SEEDS=5
OBS_LO,OBS_HI=-0.97,-0.44       # observed range as restated in the session brief
TOL=0.02                        # relative tolerance for "calibration is correct"
def ratio_of(sb,M):
    q=quart_suite(sb,M); rq,rv=q["RQ_RV"]; pos=rv>0
    return float(np.mean(rq[pos]/np.maximum(rv[pos]**2,1e-300)))
def sw_diagnostics(geom,H,sw,seed,S=S_CAL,M=None):
    """Implied RQ/RV^2 AND the sd of log within-window variance that sigma_w
    actually produces, which is the quantity item 96 reasons about."""
    rng=np.random.Generator(np.random.PCG64(seed))
    r,x,neg,mn=make_a6(geom,H,sw,rng)
    r=r[:S]
    Sn,L=r.shape
    # reconstruct the same v path make_a6 built, to read its dispersion directly
    rng2=np.random.Generator(np.random.PCG64(seed))
    _=rng2.normal(0.0,np.sqrt(VAR_LOG_IV),size=DIMS[geom][0])
    emb=CirculantEmbedding(fgn_acf(H,np.arange(L)))
    g=emb.sample(rng2,size=DIMS[geom][0])
    B=np.cumsum(g,axis=1)/np.power(L,H)
    v=np.exp(sw*B); v=v/v.mean(axis=1,keepdims=True)
    sd_log_v=float(np.log(v[:S]).std(axis=1).mean())
    Mu=M if M is not None else FIVEMIN[(geom,"1day")]
    return ratio_of(subbars(r,Mu),Mu),sd_log_v
def main():
    t0=time.time(); timers={}
    C11=pd.read_csv(os.path.join(S11,"results","phase6_calibration.csv"))
    ME=pd.read_csv(os.path.join(S11,"results","phase6_measured_ratio.csv"))
    # ---------------- (a) implied ratio at the S11 calibrated sigma_w, every grid point
    t=time.time(); ver=[]
    for _,r in C11.iterrows():
        geom,root,H,sw=r.geom,r.root,r.H,r.sigma_w_calibrated
        for M in GRID_EXT[(geom,"1day")]:
            meas=ME[(ME.root==root)&(ME.geom==geom)&(ME.horizon=="1day")&(ME.M==M)]
            if not len(meas): continue
            imp,sdv=sw_diagnostics(geom,H,sw,int(r.seed),M=int(M))
            mv=float(meas.rq_over_rv2.iloc[0])
            ver.append(dict(root=root,geom=geom,H=H,M=int(M),sigma_w=sw,
                implied_rq_rv2=imp,measured_rq_rv2=mv,constant_vol_value=1.0,
                abs_discrepancy=imp-mv,prop_discrepancy=imp/mv-1.0,
                sd_log_within_window_var=sdv,
                is_calibration_point=(M==FIVEMIN[(geom,"1day")])))
        print(f"  verify {root}/{geom} H={H:.2f} sw={sw:.4f} done",flush=True)
    V=pd.DataFrame(ver); V.to_csv(os.path.join(RES,"phase2_verification.csv"),index=False)
    CP=V[V.is_calibration_point]
    timers["verify"]=round(time.time()-t,1)
    # ---------------- (b) the mapping, swept
    t=time.time(); sweep=[]
    SWG=np.exp(np.linspace(np.log(0.1),np.log(5.0),25))
    ss=np.random.SeedSequence(MASTER_SWEEP); sd0=[int(x) for x in ss.generate_state(8)]
    for gi,geom in enumerate(["GLOBEX","RTH"]):
        M=FIVEMIN[(geom,"1day")]
        for H in HS:
            for sw in SWG:
                imp,sdv=sw_diagnostics(geom,H,float(sw),sd0[gi],M=M)
                sweep.append(dict(geom=geom,H=H,sigma_w=float(sw),M=M,
                    implied_rq_rv2=imp,sd_log_within_window_var=sdv,seed=sd0[gi]))
        print(f"  sweep {geom} done",flush=True)
    SW=pd.DataFrame(sweep); SW.to_csv(os.path.join(RES,"phase2_sweep.csv"),index=False)
    timers["sweep"]=round(time.time()-t,1)
    mono={}
    for geom in ["GLOBEX","RTH"]:
        for H in HS:
            g=SW[(SW.geom==geom)&(SW.H==H)].sort_values("sigma_w")
            d=np.diff(g.implied_rq_rv2.values)
            mono[f"{geom}/H{H:.2f}"]=dict(monotone_increasing=bool(np.all(d>0)),
                n_decreases=int((d<=0).sum()),
                ratio_at_0p1=float(g.implied_rq_rv2.iloc[0]),
                ratio_at_5p0=float(g.implied_rq_rv2.iloc[-1]),
                sd_log_v_at_0p6=float(np.interp(0.6,g.sigma_w,g.sd_log_within_window_var)),
                ratio_at_0p6=float(np.interp(0.6,g.sigma_w,g.implied_rq_rv2)))
    # second solution near 0.6?
    sec=[]
    for geom in ["GLOBEX","RTH"]:
        for root in ["ES","NQ"]:
            tgt=float(ME[(ME.root==root)&(ME.geom==geom)&(ME.horizon=="1day")&
                         (ME.M==FIVEMIN[(geom,"1day")])].rq_over_rv2.iloc[0])
            for H in HS:
                g=SW[(SW.geom==geom)&(SW.H==H)].sort_values("sigma_w")
                cr=np.where(np.diff(np.sign(g.implied_rq_rv2.values-tgt))!=0)[0]
                sec.append(dict(root=root,geom=geom,H=H,target=tgt,
                    n_crossings=int(len(cr)),
                    crossing_sigma_w=";".join(f"{g.sigma_w.values[i]:.3f}" for i in cr),
                    ratio_at_0p6=float(np.interp(0.6,g.sigma_w,g.implied_rq_rv2)),
                    target_reached_at_0p6=bool(
                        abs(np.interp(0.6,g.sigma_w,g.implied_rq_rv2)/tgt-1)<TOL)))
    SEC=pd.DataFrame(sec); SEC.to_csv(os.path.join(RES,"phase2_crossings.csv"),index=False)
    det=dict(tolerance=TOL,
        n_calibration_points=int(len(CP)),
        max_abs_prop_discrepancy_at_calibration_point=float(
            CP.prop_discrepancy.abs().max()),
        n_within_tolerance=int((CP.prop_discrepancy.abs()<TOL).sum()),
        sd_log_within_window_var_range=[float(CP.sd_log_within_window_var.min()),
                                        float(CP.sd_log_within_window_var.max())],
        sigma_w_range=[float(CP.sigma_w.min()),float(CP.sigma_w.max())],
        monotonicity=mono,
        max_n_crossings=int(SEC.n_crossings.max()),
        any_second_solution_at_0p6=bool(SEC.target_reached_at_0p6.any()),
        timers=timers)
    det["determination"]=("A" if det["n_within_tolerance"]==det["n_calibration_points"]
                          else ("B" if det["max_abs_prop_discrepancy_at_calibration_point"]>0.10
                                else "C"))
    json.dump(det,open(os.path.join(RES,"phase2_determination.json"),"w"),indent=1)
    pd.set_option("display.width",250)
    print("\n=== (a) at the calibration point, implied vs measured ===")
    print(CP[["root","geom","H","M","sigma_w","implied_rq_rv2","measured_rq_rv2",
              "prop_discrepancy","sd_log_within_window_var"]].to_string(index=False))
    print("\n=== (b) mapping sigma_w -> RQ/RV^2, GLOBEX H=0.50 and RTH H=0.50 ===")
    for geom in ["GLOBEX","RTH"]:
        g=SW[(SW.geom==geom)&(SW.H==0.50)].sort_values("sigma_w")
        print(f"-- {geom}"); print(g[["sigma_w","implied_rq_rv2",
                                      "sd_log_within_window_var"]].to_string(index=False))
    print("\n=== crossings ==="); print(SEC.to_string(index=False))
    print(); print(json.dumps(det,indent=1)[:2500])
    print(f"PHASE2 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
