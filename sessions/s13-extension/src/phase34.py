"""S13 Phases 3 and 4: trend structure (item 104) and the convexity lookup table."""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common13 import BASE,RES,CACHE,S10,S11,CELLS,FIVEMIN
NREP=9999; MASTER_BREAK=20260833
K_VOL_ANN=0.20; THRESH=0.05
def adj_exact(s2): return 1.0-np.exp(-s2/8.0)
def adj_bl(s2):    return (np.exp(s2)-1.0)/8.0
def fe_rss(X,y,cid,ncl):
    """Within (fixed-effects) OLS: demean y and X by cluster, return rss and coef."""
    yd=y-np.array([y[cid==g].mean() for g in range(ncl)])[cid]
    Xd=X-np.vstack([X[cid==g].mean(axis=0) for g in range(ncl)])[cid]
    beta,*_=np.linalg.lstsq(Xd,yd,rcond=None)
    r=yd-Xd@beta
    return float((r*r).sum()),beta,r
def main():
    t0=time.time(); timers={}; out={}
    # ================= PHASE 3
    t=time.time()
    SUB=pd.read_csv(os.path.join(S10,"results","phase3_subfits.csv"))
    yr=SUB[(SUB.stratum=="year")&(~SUB.degenerate)].copy()
    yr["year"]=yr.key.astype(int)
    yr["distinct"]=yr.cell.str.replace("/B1/","/B0/",regex=False)
    d=yr.drop_duplicates(subset=["distinct","year"]).copy()
    # reference exponent per cell, from the pooled sub-fit's grid
    REF=SUB[SUB.stratum=="pooled"][["cell"]].copy()
    P1=pd.read_csv(os.path.join(S10,"results","phase1_bootstrap.csv"))
    refmap=dict(zip(P1.cell,P1.b_trigamma_ref))
    d["b_ref"]=d.cell.map(refmap); d["gap"]=d.b-d.b_ref
    tab=d.pivot_table(index="distinct",columns="year",values="b").reset_index()
    tab.to_csv(os.path.join(RES,"phase3_b_by_year.csv"),index=False)
    gaptab=d.pivot_table(index="distinct",columns="year",values="gap").reset_index()
    gaptab.to_csv(os.path.join(RES,"phase3_gap_by_year.csv"),index=False)
    cats=sorted(d["distinct"].unique()); cmap={c:i for i,c in enumerate(cats)}
    cid=d["distinct"].map(cmap).values.astype(int); ncl=len(cats)
    yv=d.b.values.astype(float); tv=d.year.values.astype(float)
    years=sorted(d.year.unique())
    # (i) intercept only
    rss0,_,_=fe_rss(np.zeros((len(d),0)),yv,cid,ncl)
    # (ii) linear trend
    rss_lin,b_lin,_=fe_rss(tv[:,None],yv,cid,ncl)
    # (iii) level shift, break date chosen by minimising RSS
    admissible=[y for y in years if years.index(y)>=2 and years.index(y)<=len(years)-2]
    best=(None,np.inf,None)
    brk=[]
    for tau in admissible:
        Dm=(tv>=tau).astype(float)[:,None]
        r_,bb,_=fe_rss(Dm,yv,cid,ncl)
        brk.append(dict(tau=int(tau),rss=r_,delta=float(bb[0])))
        if r_<best[1]: best=(tau,r_,float(bb[0]))
    tau_hat,rss_brk,delta_hat=best
    BR=pd.DataFrame(brk); BR.to_csv(os.path.join(RES,"phase3_break_search.csv"),index=False)
    n,k_fe=len(d),ncl
    F_break_vs_null=float(((rss0-rss_brk)/1)/(rss_brk/(n-k_fe-1)))
    F_lin_vs_null=float(((rss0-rss_lin)/1)/(rss_lin/(n-k_fe-1)))
    # bootstrap p for the sup-F, accounting for the break date being estimated:
    # wild cluster bootstrap under the no-break null (cell fixed effects only),
    # re-searching tau in every replicate
    rng=np.random.Generator(np.random.PCG64(MASTER_BREAK))
    _,_,res0=fe_rss(np.zeros((len(d),0)),yv,cid,ncl)
    supF=np.empty(NREP)
    for i in range(NREP):
        w=rng.choice(np.array([-1.0,1.0]),size=ncl)[cid]
        ystar=yv-res0+w*res0
        r0s,_,_=fe_rss(np.zeros((len(d),0)),ystar,cid,ncl)
        best_=np.inf
        for tau in admissible:
            Dm=(tv>=tau).astype(float)[:,None]
            r_,_,_=fe_rss(Dm,ystar,cid,ncl)
            best_=min(best_,r_)
        supF[i]=((r0s-best_)/1)/(best_/(n-k_fe-1))
    p_sup=float((supF>=F_break_vs_null).mean())
    # and the same for the linear spec, for comparability
    Fl=np.empty(NREP)
    rng2=np.random.Generator(np.random.PCG64(MASTER_BREAK+1))
    for i in range(NREP):
        w=rng2.choice(np.array([-1.0,1.0]),size=ncl)[cid]
        ystar=yv-res0+w*res0
        r0s,_,_=fe_rss(np.zeros((len(d),0)),ystar,cid,ncl)
        rl,_,_=fe_rss(tv[:,None],ystar,cid,ncl)
        Fl[i]=((r0s-rl)/1)/(rl/(n-k_fe-1))
    p_lin=float((Fl>=F_lin_vs_null).mean())
    np.savez_compressed(os.path.join(CACHE,"break_bootstrap.npz"),
        supF=supF,F_lin_boot=Fl,F_break_obs=F_break_vs_null,F_lin_obs=F_lin_vs_null,
        seed=MASTER_BREAK,nrep=NREP,tau_hat=tau_hat)
    gap_fl=[]
    for c,g in d.groupby("distinct"):
        g=g.sort_values("year")
        gap_fl.append(dict(cell=c,year_first=int(g.year.iloc[0]),
            gap_first=float(g.gap.iloc[0]),year_last=int(g.year.iloc[-1]),
            gap_last=float(g.gap.iloc[-1]),
            gap_closed=float(g.gap.iloc[0]-g.gap.iloc[-1]),
            b_first=float(g.b.iloc[0]),b_last=float(g.b.iloc[-1]),
            b_ref=float(g.b_ref.iloc[0])))
    GF=pd.DataFrame(gap_fl); GF.to_csv(os.path.join(RES,"phase3_gap_endpoints.csv"),index=False)
    p3=dict(n_obs=n,n_clusters=ncl,years=[int(y) for y in years],
        admissible_breaks=[int(y) for y in admissible],
        rss_intercept_only=rss0,rss_linear=rss_lin,rss_break=rss_brk,
        linear_slope=float(b_lin[0]),break_date=int(tau_hat),break_delta=delta_hat,
        F_linear=F_lin_vs_null,F_break_sup=F_break_vs_null,
        p_linear_wcb=p_lin,p_break_supF_wcb=p_sup,nrep=NREP,
        rss_ratio_break_over_linear=float(rss_brk/rss_lin),
        prefers=("break" if rss_brk<rss_lin else "linear"),
        mean_gap_first=float(GF.gap_first.mean()),mean_gap_last=float(GF.gap_last.mean()),
        mean_gap_closed=float(GF.gap_closed.mean()),
        share_of_residual_trend_accounts_for=float(1.0-rss_lin/rss0),
        share_of_residual_break_accounts_for=float(1.0-rss_brk/rss0),
        rademacher_p_floor=float(2**-(ncl-1)),
        eight_cluster_note=("Eight clusters. Both p-values come from a wild cluster "
            "bootstrap with Rademacher weights and the null imposed, which is the "
            "recommended small-G correction but is itself only asymptotically valid "
            f"in G. The attainable floor is 2^-(8-1) = {2**-7:.5f} and no result "
            "here should be read as conventional evidence at any nominal level."))
    p3["verdict"]=("LEVEL SHIFT at "+str(tau_hat) if (rss_brk<rss_lin and p_sup<0.05)
                   else ("CONTINUOUS" if (p_lin<0.05 and rss_lin<=rss_brk)
                         else "INDETERMINATE"))
    json.dump(p3,open(os.path.join(RES,"phase3_trend_structure.json"),"w"),indent=1)
    timers["phase3"]=round(time.time()-t,1)
    pd.set_option("display.width",260)
    print("=== b by year, distinct cells ==="); print(tab.to_string(index=False))
    print("\n=== gap to reference, endpoints ==="); print(GF.to_string(index=False))
    print("\n=== break search ==="); print(BR.to_string(index=False))
    print(); print(json.dumps(p3,indent=1))
    # ================= PHASE 4
    t=time.time()
    V=pd.read_csv(os.path.join(S11,"results","phase5_vol_of_vol.csv"))
    rows=[]
    for _,r in V.iterrows():
        e_c,e_n=adj_exact(r.c),adj_exact(r.var_log_rv_naive)
        rows.append(dict(root=r.root,geom=r.geom,btag=r.btag,horizon=r.horizon,M=r.M,
            minutes_per_sub_bar=(1380 if r.geom=="GLOBEX" else 390)/r.M
                if r.horizon=="1day" else (60 if r.horizon=="1h" else 30)/r.M,
            s2_intercept=r.c,s2_intercept_lo=r.c_lo,s2_intercept_hi=r.c_hi,
            s2_naive=r.var_log_rv_naive,
            adj_exact_intercept_vp=100*K_VOL_ANN*e_c,
            adj_exact_intercept_vp_lo=100*K_VOL_ANN*adj_exact(r.c_lo),
            adj_exact_intercept_vp_hi=100*K_VOL_ANN*adj_exact(r.c_hi),
            adj_exact_naive_vp=100*K_VOL_ANN*e_n,
            bias_vp=100*K_VOL_ANN*(e_n-e_c),
            overstatement_prop=float(e_n/e_c-1.0),
            overstatement_lo=float(adj_exact(r.var_log_rv_naive)/adj_exact(r.c_hi)-1.0),
            overstatement_hi=float(adj_exact(r.var_log_rv_naive)/adj_exact(r.c_lo)-1.0),
            adj_BL_naive_vp=100*K_VOL_ANN*adj_bl(r.var_log_rv_naive),
            below_5pct=bool(abs(e_n/e_c-1.0)<THRESH),
            is_5min=r.is_five_min))
    T4=pd.DataFrame(rows); T4.to_csv(os.path.join(RES,"phase4_convexity_table.csv"),index=False)
    freq=[]
    for (root,geom,btag,hname),g in T4.groupby(["root","geom","btag","horizon"]):
        g=g.sort_values("M")
        ok=g[g.below_5pct]
        freq.append(dict(root=root,geom=geom,btag=btag,horizon=hname,
            n_grid=len(g),n_below_5pct=int(len(ok)),
            finest_M_below_5pct=int(ok.M.max()) if len(ok) else None,
            coarsest_M_below_5pct=int(ok.M.min()) if len(ok) else None,
            minutes_per_sub_bar_required=(float(ok.minutes_per_sub_bar.min())
                                          if len(ok) else None),
            best_M=int(g.loc[g.overstatement_prop.abs().idxmin()].M),
            best_overstatement=float(g.overstatement_prop.abs().min()),
            worst_M=int(g.loc[g.overstatement_prop.abs().idxmax()].M),
            worst_overstatement=float(g.overstatement_prop.abs().max()),
            at_5min_overstatement=float(g[g.is_5min].overstatement_prop.iloc[0])
                if g.is_5min.any() else None))
    FQ=pd.DataFrame(freq); FQ.to_csv(os.path.join(RES,"phase4_frequency_guide.csv"),index=False)
    p4=dict(threshold=THRESH,n_rows=len(T4),
        n_below_5pct=int(T4.below_5pct.sum()),
        n_cells_with_any_frequency_below_5pct=int(FQ.n_below_5pct.gt(0).sum()),
        n_cells=int(len(FQ)),
        min_overstatement_any=float(T4.overstatement_prop.abs().min()),
        max_overstatement_any=float(T4.overstatement_prop.abs().max()),
        max_bias_vp=float(T4.bias_vp.abs().max()),
        no_pnl_claim=("No options data is held. This is a pricing-bias calculation on "
            "the adjustment term only; no claim is made about executable P&L."),
        expansion_note=("The Brockhaus-Long column is reported only as a labelled "
            "sensitivity; per item 95 it is invalid at the measured kappa and the "
            "exact lognormal relation is used throughout."))
    json.dump(p4,open(os.path.join(RES,"phase4_summary.json"),"w"),indent=1,default=str)
    timers["phase4"]=round(time.time()-t,1)
    print("\n=== PHASE 4: frequency guide ==="); print(FQ.to_string(index=False))
    print(); print(json.dumps(p4,indent=1))
    out["timers"]=timers
    json.dump(out,open(os.path.join(RES,"phase34_timers.json"),"w"),indent=1)
    print(f"PHASE3+4 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
