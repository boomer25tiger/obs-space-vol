"""S11 Phases 2-5: grid span, time trend in b, reliability vs degradation,
volatility of volatility."""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common11 import BASE,RES,ROOT,S09,S10,CELLS,FIVEMIN,DEFECT_TOUCHED
from common import (GRID_EXT,trig,fitf,fit_diag,cell_windows,logrv_matrix,var_cols,
                    screen_tight)
def main():
    t0=time.time(); timers={}
    P1=pd.read_csv(os.path.join(S10,"results","phase1_bootstrap.csv"))
    # ================= PHASE 2: grid span
    t=time.time()
    COARSE={"1h":60,"30min":30}
    RATIO={"1h":60/4,"30min":30/5}
    rows=[]
    VLOG={}
    for root,geom,btag,hname in CELLS:
        rw,kw,ds=cell_windows(root,geom,hname)
        Ms=[m for m in GRID_EXT[(geom,hname)] if m<=rw.shape[1]]
        L,Ms=logrv_matrix(rw,Ms); y=var_cols(L)
        VLOG[(root,geom,btag,hname)]=(Ms,y,L)
        if hname!="1day": continue
        full=fitf(Ms,y); dfull=fit_diag(Ms,y,full)
        rows.append(dict(root=root,geom=geom,btag=btag,truncation="full",
            grid=";".join(map(str,Ms)),n_grid=len(Ms),M_min=Ms[0],M_max=Ms[-1],
            span_ratio=Ms[-1]/Ms[0],b=full["b"],c=full["c"],rmse=full["rmse"],
            cond=dfull["cond"],b_ref=fitf(Ms,trig(Ms))["b"],
            screen_tight=screen_tight(full,len(Ms))))
        for tgt in ["1h","30min"]:
            for mode,keep in [("abs_coarse_end",[m for m in Ms if m<=COARSE[tgt]]),
                              ("span_ratio",[m for m in Ms if m<=Ms[0]*RATIO[tgt]])]:
                if len(keep)<4: continue
                idx=[Ms.index(m) for m in keep]
                f=fitf(keep,y[idx]); d=fit_diag(keep,y[idx],f)
                if f is None: continue
                rows.append(dict(root=root,geom=geom,btag=btag,
                    truncation=f"match_{tgt}_{mode}",grid=";".join(map(str,keep)),
                    n_grid=len(keep),M_min=keep[0],M_max=keep[-1],
                    span_ratio=keep[-1]/keep[0],b=f["b"],c=f["c"],rmse=f["rmse"],
                    cond=d["cond"],b_ref=fitf(keep,trig(keep))["b"],
                    screen_tight=screen_tight(f,len(keep))))
    G=pd.DataFrame(rows); G.to_csv(os.path.join(RES,"phase2_grid_span.csv"),index=False)
    # decomposition: horizon effect vs span effect
    dec=[]
    for root in ["ES","NQ"]:
        for btag in ["B0","B1"]:
            for tgt in ["1h","30min"]:
                base=G[(G.root==root)&(G.geom=="RTH")&(G.btag==btag)&
                       (G.truncation=="full")]
                tr=G[(G.root==root)&(G.geom=="RTH")&(G.btag==btag)&
                     (G.truncation==f"match_{tgt}_abs_coarse_end")]
                act=P1[P1.cell==f"{root}/RTH/{btag}/{tgt}"]
                if not len(base) or not len(tr) or not len(act): continue
                b0=float(base.b.iloc[0]); bt=float(tr.b.iloc[0]); ba=float(act.b.iloc[0])
                hor=b0-ba; span=b0-bt
                dec.append(dict(root=root,btag=btag,target_horizon=tgt,
                    b_1day_full=b0,b_1day_truncated=bt,b_actual_target=ba,
                    horizon_effect=hor,span_effect=span,
                    share_from_span=(span/hor if hor!=0 else np.nan),
                    residual_after_span=hor-span))
    D=pd.DataFrame(dec); D.to_csv(os.path.join(RES,"phase2_decomposition.csv"),index=False)
    timers["phase2"]=round(time.time()-t,1)
    print("=== PHASE 2: grid span ===")
    print(G[["root","geom","btag","truncation","n_grid","M_max","span_ratio","b","cond","screen_tight"]].to_string(index=False))
    print(); print(D.to_string(index=False))
    # ================= PHASE 3: time trend in b
    t=time.time()
    SUB=pd.read_csv(os.path.join(S10,"results","phase3_subfits.csv"))
    yr=SUB[(SUB.stratum=="year")&(~SUB.degenerate)].copy()
    yr["year"]=yr.key.astype(int)
    tr=[]
    for cell,g in yr.groupby("cell"):
        if len(g)<4: continue
        res=stats.linregress(g.year.values,g.b.values)
        tr.append(dict(cell=cell,n_years=len(g),slope=res.slope,se=res.stderr,
            p_value=res.pvalue,r2=res.rvalue**2,intercept=res.intercept,
            b_first=float(g.sort_values("year").b.iloc[0]),
            b_last=float(g.sort_values("year").b.iloc[-1])))
    T=pd.DataFrame(tr); T.to_csv(os.path.join(RES,"phase3_time_trend.csv"),index=False)
    # pooled with cell fixed effects: demean b within cell, regress on demeaned year
    # B0 and B1 are exact duplicates by construction, so the pooled regression is
    # run on the eight DISTINCT cells; the 16-cell version is reported beside it
    # only to show the duplication inflates t by sqrt(2).
    yr=yr.copy(); yr["distinct"]=yr.cell.str.replace("/B1/","/B0/",regex=False)
    yrd=yr.drop_duplicates(subset=["distinct","year"]).copy()
    yr["b_dm"]=yr.b-yr.groupby("cell").b.transform("mean")
    yr["y_dm"]=yr.year-yr.groupby("cell").year.transform("mean")
    n,k=len(yr),yr.cell.nunique()+1
    beta=float((yr.y_dm*yr.b_dm).sum()/(yr.y_dm**2).sum())
    resid=yr.b_dm-beta*yr.y_dm
    dof=n-k
    se=float(np.sqrt((resid**2).sum()/dof/ (yr.y_dm**2).sum()))
    tstat=beta/se; pval=float(2*stats.t.sf(abs(tstat),dof))
    pooled=dict(slope=beta,se=se,t=tstat,p_value=pval,n_obs=n,n_cells=int(k-1),dof=dof,
        direction=("flatter over time" if beta>0 else "steeper over time"),
        n_cells_positive_slope=int((T.slope>0).sum()),
        n_cells_significant_05=int((T.p_value<0.05).sum()),n_cells_fitted=int(len(T)))
    yrd["b_dm"]=yrd.b-yrd.groupby("distinct").b.transform("mean")
    yrd["y_dm"]=yrd.year-yrd.groupby("distinct").year.transform("mean")
    nd,kd=len(yrd),yrd["distinct"].nunique()+1
    bd=float((yrd.y_dm*yrd.b_dm).sum()/(yrd.y_dm**2).sum())
    rd=yrd.b_dm-bd*yrd.y_dm; dofd=nd-kd
    sed=float(np.sqrt((rd**2).sum()/dofd/(yrd.y_dm**2).sum()))
    # cell-clustered standard error over the eight distinct cells
    num=0.0
    for _,g in yrd.groupby("distinct"):
        num+=float((g.y_dm*(g.b_dm-bd*g.y_dm)).sum())**2
    sec=float(np.sqrt(num)/ (yrd.y_dm**2).sum())
    pooled["distinct_cells"]=dict(slope=bd,se=sed,t=bd/sed,
        p_value=float(2*stats.t.sf(abs(bd/sed),dofd)),n_obs=nd,n_cells=int(kd-1),
        se_clustered_by_cell=sec,t_clustered=bd/sec,
        p_clustered=float(2*stats.t.sf(abs(bd/sec),yrd["distinct"].nunique()-1)))
    json.dump(pooled,open(os.path.join(RES,"phase3_pooled_trend.json"),"w"),indent=1)
    timers["phase3"]=round(time.time()-t,1)
    print("\n=== PHASE 3: time trend ===")
    print(T.to_string(index=False)); print(json.dumps(pooled,indent=1))
    # ================= PHASE 4: reliability vs OOS degradation
    t=time.time()
    IS=pd.read_csv(os.path.join(RES,"phase1_insample.csv"))
    HO11=pd.read_csv(os.path.join(RES,"phase1_holdout.csv"))
    HO09=pd.read_csv(os.path.join(S09,"results","phase6_candidates_oos.csv"))
    HO09=HO09[HO09.range=="extended"]
    key=["root","geom","btag","horizon","candidate"]
    oos=HO09[~HO09.candidate.isin(DEFECT_TOUCHED)][key+["r2_oos"]].copy()
    oos=pd.concat([oos,HO11[key+["r2_oos"]]],ignore_index=True)
    ins=IS[IS["sample"]=="insample"][key+["r2"]].rename(columns={"r2":"r2_is"})
    M=ins.merge(oos,on=key)
    M["degradation"]=M.r2_is-M.r2_oos
    P3=pd.read_csv(os.path.join(S09,"results","phase3_sizing_params.csv"))
    P3=P3[(P3.range=="extended")&(P3.valid==True)][["root","geom","btag","horizon",
                                                    "lam_intercept"]]
    per=M.groupby(["root","geom","btag","horizon"]).agg(
        n_cand=("candidate","size"),r2_is_mean=("r2_is","mean"),
        r2_oos_mean=("r2_oos","mean"),degradation_mean=("degradation","mean"),
        degradation_median=("degradation","median")).reset_index().merge(
        P3,on=["root","geom","btag","horizon"])
    per.to_csv(os.path.join(RES,"phase4_reliability_vs_degradation.csv"),index=False)
    d8=per.drop_duplicates(subset=["root","geom","horizon"])
    rho,p=stats.spearmanr(d8.lam_intercept,d8.degradation_mean)
    rp,pp=stats.pearsonr(d8.lam_intercept,d8.degradation_mean)
    p4=dict(n_rows_all=len(per),n_distinct_cells=len(d8),
        spearman_rho=float(rho),spearman_p_exact=float(p),
        pearson_r=float(rp),pearson_p=float(pp),
        power_note=("Eight distinct cells (B0 and B1 are duplicates by construction). "
            "At n=8 a two-sided Spearman test has roughly 25 percent power to detect "
            "rho=0.7 at the 5 percent level, so a null result here is uninformative "
            "and a significant one would rest on eight points, four of which share "
            "an instrument. This is reported as a descriptive association, not a test."))
    json.dump(p4,open(os.path.join(RES,"phase4_summary.json"),"w"),indent=1)
    timers["phase4"]=round(time.time()-t,1)
    print("\n=== PHASE 4: reliability vs degradation ===")
    print(d8[["root","geom","horizon","lam_intercept","r2_is_mean","r2_oos_mean","degradation_mean"]].to_string(index=False))
    print(json.dumps(p4,indent=1))
    # ================= PHASE 5: volatility of volatility
    t=time.time()
    vv=[]
    for root,geom,btag,hname in CELLS:
        Ms,y,L=VLOG[(root,geom,btag,hname)]
        r=P1[P1.cell==f"{root}/{geom}/{btag}/{hname}"]
        if not len(r): continue
        c=float(r.c.iloc[0]); clo=float(r.c_lo.iloc[0]); chi=float(r.c_hi.iloc[0])
        for M,v in zip(Ms,y):
            vv.append(dict(root=root,geom=geom,btag=btag,horizon=hname,M=M,
                c=c,c_lo=clo,c_hi=chi,
                sd_log_iv=np.sqrt(max(c,0)),sd_log_iv_lo=np.sqrt(max(clo,0)),
                sd_log_iv_hi=np.sqrt(max(chi,0)),
                vol_ratio_1sd=float(np.exp(0.5*np.sqrt(max(c,0)))),
                var_log_rv_naive=float(v),
                sd_log_iv_naive=float(np.sqrt(v)),
                overstatement_var=float(v/c-1) if c>0 else np.nan,
                overstatement_sd=float(np.sqrt(v/c)-1) if c>0 else np.nan,
                is_five_min=(M==FIVEMIN[(geom,hname)])))
    V=pd.DataFrame(vv); V.to_csv(os.path.join(RES,"phase5_vol_of_vol.csv"),index=False)
    F5=V[V.is_five_min]
    F5.to_csv(os.path.join(RES,"phase5_five_minute.csv"),index=False)
    timers["phase5"]=round(time.time()-t,1)
    print("\n=== PHASE 5: vol of vol at the five-minute equivalent ===")
    print(F5[["root","geom","btag","horizon","M","c","c_lo","c_hi","sd_log_iv",
              "vol_ratio_1sd","var_log_rv_naive","overstatement_var","overstatement_sd"]].to_string(index=False))
    json.dump(dict(timers=timers),open(os.path.join(RES,"phase2345_timers.json"),"w"),indent=1)
    print(f"\nPHASE2-5 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
