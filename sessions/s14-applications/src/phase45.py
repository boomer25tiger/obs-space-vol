"""S14 Phases 4 and 5: the A7 amplitude bound, and year-fit identification.

PHASE 4 ANALYTIC BOUND. Write RV_M = s*X + (1-s)*Y where X is the boosted
sub-bar's squared return, normalised to mean 1 and variance 2 (one chi-square
with one degree of freedom), and Y is the average of the remaining M-1, of
variance 2/(M-1). Then to first order

    Var(log RV_M) ~ Var(RV_M)/E[RV_M]^2 = 2 s^2 + 2 (1-s)^2/(M-1)

so a localized feature carrying share s of realized variance contributes an
M-INVARIANT FLOOR of 2 s^2. To supply a required excess X_req at the coarse end
a feature must carry s_req = sqrt(X_req / 2). That retires the whole class of
localized mechanisms quantitatively, not one arm at a time.
"""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy.special import polygamma
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common14 import BASE,RES,CACHE,S10,S13,CELLS,CELLS4,FIVEMIN
from common import GRID_EXT,trig,fitf,fit_diag,cell_windows,subbars,logrv_matrix,var_cols
from phase6_arm_a6 import make_a6, DIMS
from phase1_openbar import a7_panel, subbar_amplitudes      # S13, unmodified
MASTER=20260835; N_SEEDS=5
OBS_LO,OBS_HI=-0.97,-0.44
KAPPA_GRID=[1.0,3.0,6.0,10.0,20.0,40.0,80.0,160.0,320.0,640.0,1280.0,2000.0]
def main():
    t0=time.time(); timers={}; out={}
    # ================= PHASE 4a, analytic bound
    t=time.time(); bnd=[]
    P1=pd.read_csv(os.path.join(S10,"results","phase1_bootstrap.csv"))
    AM=pd.read_csv(os.path.join(S13,"results","phase1_amplitudes.csv"))
    for root,geom in CELLS4:
        rw,kw,ds=cell_windows(root,geom,"1day")
        Ms=[m for m in GRID_EXT[(geom,"1day")] if m<=rw.shape[1]]
        L,Ms=logrv_matrix(rw,Ms); y=var_cols(L)
        r=P1[P1.cell==f"{root}/{geom}/B0/1day"].iloc[0]
        c=float(r.c); Mmax=Ms[-1]
        e_obs=float(y[-1]-c); e_trig=float(trig(Mmax))
        req=max(e_obs-e_trig,0.0)
        s_req=float(np.sqrt(req/2.0))
        M5=FIVEMIN[(geom,"1day")]
        # The operative evaluation point is the five-minute equivalent, where the
        # programme's headline sits. At the coarsest grid point the curve has all
        # but converged to c, so the residual excess there is near zero (and
        # negative on NQ) and understates what a mechanism must supply.
        j5=Ms.index(M5)
        e_obs5=float(y[j5]-c); e_trig5=float(trig(M5))
        req5=max(e_obs5-e_trig5,0.0); s_req5=float(np.sqrt(req5/2.0))
        s_meas=float(AM[(AM.root==root)&(AM.geom==geom)&(AM.horizon=="1day")&
                        (AM.M==M5)].first_share.iloc[0])
        # also at the coarsest grid point, where the floor is what matters
        s_meas_coarse=float(AM[(AM.root==root)&(AM.geom==geom)&(AM.horizon=="1day")&
                               (AM.M==Mmax)].first_share.iloc[0])
        bnd.append(dict(root=root,geom=geom,M_five_min=int(M5),
            excess_observed_5min=e_obs5,trigamma_at_5min=e_trig5,
            required_floor_5min=req5,required_share_5min_target=s_req5,
            M_coarsest=int(Mmax),c=c,
            var_log_rv_at_Mmax=float(y[-1]),excess_observed=e_obs,
            trigamma_at_Mmax=e_trig,required_floor=req,
            required_share=s_req,measured_share_5min=s_meas,
            measured_share_at_Mmax=s_meas_coarse,
            ratio_required_to_measured_5min=s_req5/max(s_meas,1e-12),
            ratio_at_coarsest=s_req/max(s_meas_coarse,1e-12),
            ratio_required_to_measured_coarse=s_req/max(s_meas_coarse,1e-12),
            floor_from_measured_5min=2*s_meas**2,
            floor_from_measured_coarse=2*s_meas_coarse**2))
    BD=pd.DataFrame(bnd); BD.to_csv(os.path.join(RES,"phase4_analytic_bound.csv"),index=False)
    timers["bound"]=round(time.time()-t,1)
    pd.set_option("display.width",270)
    print("=== PHASE 4a: analytic bound ===")
    print(BD[["root","geom","M_five_min","excess_observed_5min","trigamma_at_5min",
              "required_floor_5min","required_share_5min_target","measured_share_5min",
              "ratio_required_to_measured_5min","floor_from_measured_5min"]].to_string(index=False))
    print("  (at the coarsest grid point, where the curve has all but converged to c:)")
    print(BD[["root","geom","M_coarsest","excess_observed","trigamma_at_Mmax",
              "required_floor","required_share"]].to_string(index=False))
    # ================= PHASE 4b, kappa sweep
    t=time.time(); rows=[]
    ss=np.random.SeedSequence(MASTER); ch=ss.spawn(len(CELLS4)*len(KAPPA_GRID)*N_SEEDS)
    k=0
    for root,geom in CELLS4:
        Ms=GRID_EXT[(geom,"1day")]; M5=FIVEMIN[(geom,"1day")]
        entered=False
        for kap in KAPPA_GRID:
            bs=[];shr=[]
            for si in range(N_SEEDS):
                child=ch[k]; k+=1; sd=int(child.generate_state(1)[0])
                rng=np.random.Generator(np.random.PCG64(child))
                r,x,p=a7_panel(geom,kap,"start",rng)
                a=subbar_amplitudes(r,M5); shr.append(a["first_share"])
                Lm,used=logrv_matrix(r,[m for m in Ms if m<=r.shape[1]])
                yv=var_cols(Lm); f=fitf(used,yv); d=fit_diag(used,yv,f)
                np.savez_compressed(os.path.join(CACHE,
                    f"a7sweep_{root}_{geom}_k{kap:.0f}_s{si}.npz"),
                    logrv=Lm.astype(np.float32),Ms=np.array(used),y=yv,x=x,seed=sd,
                    kappa=kap,first_share=a["first_share"])
                if f: bs.append(f["b"])
                rows.append(dict(root=root,geom=geom,kappa=kap,seed_index=si,seed=sd,
                    b=f["b"] if f else np.nan,c=f["c"] if f else np.nan,
                    A=f["A"] if f else np.nan,rmse=f["rmse"] if f else np.nan,
                    cond=d["cond"],corr_cb=d["corr_cb"],corr_Ab=d["corr_Ab"],
                    first_share=a["first_share"]))
            bs=np.array(bs); ms=float(np.mean(shr))
            inr=bool(OBS_LO<=bs.mean()<=OBS_HI)
            print(f"  {root}/{geom} kappa={kap:7.1f} share={ms:.4f} "
                  f"b={bs.mean():+.4f} sd={bs.std(ddof=1):.4f} in_range={inr}",flush=True)
            if inr: entered=True
            if inr or ms>0.5: break
        if not entered:
            print(f"  {root}/{geom}: b never entered the observed range before "
                  f"share exceeded 0.5",flush=True)
    SW=pd.DataFrame(rows); SW.to_csv(os.path.join(RES,"phase4_kappa_sweep.csv"),index=False)
    agg=SW.groupby(["root","geom","kappa"]).agg(
        b_mean=("b","mean"),b_sd=("b","std"),share=("first_share","mean"),
        rmse=("rmse","mean"),cond=("cond","mean"),n_seeds=("seed","nunique")).reset_index()
    agg["in_observed_range"]=(agg.b_mean>=OBS_LO)&(agg.b_mean<=OBS_HI)
    agg.to_csv(os.path.join(RES,"phase4_kappa_agg.csv"),index=False)
    p4=dict(kappa_grid=KAPPA_GRID,observed_range=[OBS_LO,OBS_HI],
        any_entered_range=bool(agg.in_observed_range.any()),
        max_share_reached=float(agg.share.max()),
        max_b_reached=float(agg.b_mean.max()),
        b_at_max_kappa={f"{r}/{g}":float(agg[(agg.root==r)&(agg.geom==g)]
            .sort_values("kappa").b_mean.iloc[-1]) for r,g in CELLS4},
        share_at_max_kappa={f"{r}/{g}":float(agg[(agg.root==r)&(agg.geom==g)]
            .sort_values("kappa").share.iloc[-1]) for r,g in CELLS4},
        max_between_seed_sd=float(SW.groupby(["root","geom","kappa"]).b.std().max()),
        required_share_range=[float(BD.required_share_5min_target.min()),
                              float(BD.required_share_5min_target.max())],
        required_floor_range=[float(BD.required_floor_5min.min()),
                              float(BD.required_floor_5min.max())],
        floor_supplied_by_measured_share=[float(BD.floor_from_measured_5min.min()),
                                          float(BD.floor_from_measured_5min.max())],
        measured_share_range=[float(BD.measured_share_5min.min()),
                              float(BD.measured_share_5min.max())],
        ratio_range=[float(BD.ratio_required_to_measured_5min.min()),
                     float(BD.ratio_required_to_measured_5min.max())],
        general_bound=("A localized feature carrying share s of realized variance "
            "contributes an M-invariant floor of 2 s^2 to Var(log RV_M). To supply "
            "the measured excess at the five-minute equivalent it must carry "
            "s = sqrt(excess/2). Any localized "
            "mechanism whose measured share falls short of that value is ruled out "
            "without simulating it."))
    out["phase4"]=p4; timers["sweep"]=round(time.time()-t,1)
    print("\n=== PHASE 4b: kappa sweep ===")
    print(agg[["root","geom","kappa","share","b_mean","b_sd","rmse","cond",
               "in_observed_range"]].to_string(index=False))
    print(); print(json.dumps(p4,indent=1))
    # ================= PHASE 5, year-fit identification
    t=time.time()
    SUB=pd.read_csv(os.path.join(S10,"results","phase3_subfits.csv"))
    yr=SUB[(SUB.stratum=="year")&(~SUB.degenerate)].copy()
    yr["year"]=yr.key.astype(int)
    yr["distinct"]=yr.cell.str.replace("/B1/","/B0/",regex=False)
    d=yr.drop_duplicates(subset=["distinct","year"]).copy()
    pooled=SUB[SUB.stratum=="pooled"].copy()
    pooled["distinct"]=pooled.cell.str.replace("/B1/","/B0/",regex=False)
    pm=dict(zip(pooled["distinct"],pooled.b))
    d["b_pooled"]=d["distinct"].map(pm); d["dev"]=d.b-d.b_pooled
    MMAX={}
    for root,geom,btag,hname in CELLS:
        if btag=="B1": continue
        rw,_,_=cell_windows(root,geom,hname)
        MMAX[f"{root}/{geom}/B0/{hname}"]=max(m for m in GRID_EXT[(geom,hname)]
                                              if m<=rw.shape[1])
    d["M_coarsest"]=d["distinct"].map(MMAX)
    d["A_over_c"]=d.A/d.c
    d["decaying_term_at_Mmax"]=d.A*np.power(d.M_coarsest.astype(float),d.b)
    d["decaying_over_c"]=d.decaying_term_at_Mmax/d.c
    d["log_cond"]=np.log10(d["cond"])
    d[["distinct","year","b","b_pooled","dev","c","A","A_over_c",
       "decaying_over_c","cond","log_cond","rmse","n_windows"]].to_csv(
        os.path.join(RES,"phase5_year_fits.csv"),index=False)
    cats=sorted(d["distinct"].unique()); cm={c:i for i,c in enumerate(cats)}
    cid=d["distinct"].map(cm).values.astype(int); ncl=len(cats)
    def within(v):
        v=np.asarray(v,float)
        return v-np.array([v[cid==g].mean() for g in range(ncl)])[cid]
    yv=within(d.dev.values)
    regs={"A_over_c":within(d.A_over_c.values),
          "log_cond":within(d.log_cond.values),
          "rmse":within(d.rmse.values),
          "is_2022":within((d.year==2022).astype(float).values)}
    res={}
    for nm in ["A_over_c","log_cond","rmse","is_2022"]:
        x=regs[nm]; b=float((x*yv).sum()/max((x*x).sum(),1e-300))
        e=yv-b*x; se=float(np.sqrt((e*e).sum()/(len(d)-ncl-1)/max((x*x).sum(),1e-300)))
        res[f"univariate_{nm}"]=dict(coef=b,se=se,t=b/se if se>0 else np.nan,
            r2=float(1-(e*e).sum()/max((yv*yv).sum(),1e-300)))
    X=np.column_stack([regs["A_over_c"],regs["log_cond"]])
    bb,*_=np.linalg.lstsq(X,yv,rcond=None); e=yv-X@bb
    XtXi=np.linalg.inv(X.T@X); s2=float((e*e).sum()/(len(d)-ncl-2))
    ses=np.sqrt(np.diag(XtXi)*s2)
    res["joint_identification"]=dict(coef_A_over_c=float(bb[0]),se_A_over_c=float(ses[0]),
        coef_log_cond=float(bb[1]),se_log_cond=float(ses[1]),
        r2=float(1-(e*e).sum()/max((yv*yv).sum(),1e-300)))
    X3=np.column_stack([regs["A_over_c"],regs["log_cond"],regs["is_2022"]])
    b3,*_=np.linalg.lstsq(X3,yv,rcond=None); e3=yv-X3@b3
    XtXi3=np.linalg.inv(X3.T@X3); s23=float((e3*e3).sum()/(len(d)-ncl-3))
    ses3=np.sqrt(np.diag(XtXi3)*s23)
    res["with_2022_dummy"]=dict(coef_A_over_c=float(b3[0]),coef_log_cond=float(b3[1]),
        coef_is_2022=float(b3[2]),se_is_2022=float(ses3[2]),
        t_is_2022=float(b3[2]/ses3[2]),
        r2=float(1-(e3*e3).sum()/max((yv*yv).sum(),1e-300)))
    y22=d[d.year==2022]
    res["2022_diagnostics"]=dict(
        mean_A_over_c_2022=float(y22.A_over_c.mean()),
        mean_A_over_c_other=float(d[d.year!=2022].A_over_c.mean()),
        mean_log_cond_2022=float(y22.log_cond.mean()),
        mean_log_cond_other=float(d[d.year!=2022].log_cond.mean()),
        mean_rmse_2022=float(y22.rmse.mean()),
        mean_rmse_other=float(d[d.year!=2022].rmse.mean()),
        mean_c_2022=float(y22.c.mean()),mean_c_other=float(d[d.year!=2022].c.mean()),
        mean_dev_2022=float(y22.dev.mean()))
    res["verdict"]=("IDENTIFICATION ARTIFACT" if abs(res["with_2022_dummy"]["t_is_2022"])<2
                    else "VOLATILITY-STATE EFFECT, not explained by identification")
    res["s10_note"]=("S10 found all 48 volatility-tercile sub-fits degenerate because "
        "conditioning on realized volatility removes the cross-sectional log-IV "
        "variation that identifies the intercept. A high-volatility YEAR is a milder "
        "version of the same conditioning, so the identification channel is the "
        "first thing to test before reading 2022 as a state effect.")
    json.dump(res,open(os.path.join(RES,"phase5_identification.json"),"w"),indent=1)
    out["phase5"]=res; timers["phase5"]=round(time.time()-t,1)
    print("\n=== PHASE 5: year-fit identification ===")
    print(d[["distinct","year","b","dev","c","A","A_over_c","decaying_over_c",
             "cond","rmse"]].round(4).to_string(index=False))
    print(); print(json.dumps(res,indent=1))
    out["timers"]=timers
    json.dump(out,open(os.path.join(RES,"phase45_summary.json"),"w"),indent=1,default=str)
    print(f"PHASE4+5 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
