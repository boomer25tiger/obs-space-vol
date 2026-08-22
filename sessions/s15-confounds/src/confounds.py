"""S15 Phases 1-3: confound checks on K10, K9 and the trend. Pre-2024 only.

Nothing is reimplemented: the panels, fits and estimators are the same imported
functions S14 used, and the K10/K9 machinery is re-executed here only to add the
columns S14 did not report.
"""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy import stats
from scipy.special import gamma as gamma_fn
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
S09=os.path.join(ROOT,"sessions","s09-application")
S10=os.path.join(ROOT,"sessions","s10-exponent-audit")
S11=os.path.join(ROOT,"sessions","s11-extensions")
S14=os.path.join(ROOT,"sessions","s14-applications")
for p in [os.path.join(S14,"src"),os.path.join(S11,"src"),os.path.join(S10,"src"),
          os.path.join(S09,"src"),
          os.path.join(ROOT,"sessions","s07-completion-and-spy","src"),
          os.path.join(ROOT,"sessions","s05-reliability-mcs","src"),
          os.path.join(ROOT,"sessions","s02-mechanism-expansion","src"),
          os.path.join(ROOT,"sessions","s01-estimator-validation","src")]:
    sys.path.insert(0,p)
from common import GRID_EXT,cell_windows,subbars,logrv_matrix,var_cols
from proxies_robust import p1_rv, p3_kernel_flattop, kernel_H
CELLS4=[(r,g) for g in ["GLOBEX","RTH"] for r in ["ES","NQ"]]
FIVEMIN={("RTH","1day"):78,("GLOBEX","1day"):276}
QS=[0.5,1.0,2.0]; LAGS=np.arange(1,41)
NUGGET_SCALES=[0.25,0.50,0.75,1.00]
NREP=9999; MASTER_WCB=20260836
def Cq(q): return 2**(q/2)*gamma_fn((q+1)/2)/np.sqrt(np.pi)
def loglog_fit(lags,m):
    lg=np.log(lags); lm=np.log(m)
    A=np.polyfit(lg,lm,1); pred=np.polyval(A,lg)
    r=lm-pred; n=len(lags)
    rmse=float(np.sqrt(np.mean(r**2)))
    se=float(np.sqrt((r**2).sum()/max(n-2,1)/((lg-lg.mean())**2).sum()))
    return float(A[0]),se,rmse
def main():
    t0=time.time(); timers={}; out={}
    P3=pd.read_csv(os.path.join(S09,"results","phase3_sizing_params.csv"))
    # =============================== PHASE 1: K10 LAG SELECTION
    t=time.time(); rows=[]; surv={}; scal=[]
    MOM={}
    for root,geom in CELLS4:
        M5=FIVEMIN[(geom,"1day")]
        rw,kw,ds=cell_windows(root,geom,"1day")
        rv=p1_rv(subbars(rw,M5)); pos=rv>0
        y=np.log(rv[pos]); varlog=float(y.var())
        lam=float(P3[(P3.root==root)&(P3.geom==geom)&(P3.btag=="B0")&
                     (P3.horizon=="1day")&(P3.range=="extended")].lam_intercept.iloc[0])
        vareps=(1.0-lam)*varlog; nug=2.0*vareps
        for q in QS:
            m=np.array([float((np.abs(y[D:]-y[:-D])**q).mean()) for D in LAGS])
            S=(m/Cq(q))**(2.0/q)
            MOM[(root,geom,q)]=(m,S,nug)
            good=(S-nug)>1e-12
            surv[(root,geom,q)]=set(LAGS[good].tolist())
    # the common window: lags surviving in EVERY cell and EVERY q
    common=sorted(set(LAGS.tolist()).intersection(*surv.values()))
    for root,geom in CELLS4:
        for q in QS:
            m,S,nug=MOM[(root,geom,q)]
            good=(S-nug)>1e-12
            sub=LAGS[good]
            # 1) naive on ALL lags (the S14 naive figure)
            zn_all,se_all,rm_all=loglog_fit(LAGS,m)
            # 2) naive on exactly the SURVIVING subset, uncorrected
            zn_sub,se_sub,rm_sub=loglog_fit(sub,m[good])
            # 3) corrected on the surviving subset (the S14 corrected figure)
            mc=Cq(q)*np.power(S[good]-nug,q/2)
            zc_sub,se_c,rm_c=loglog_fit(sub,mc)
            # 4) the common window, all three
            ci=np.isin(LAGS,common)
            zn_cw,se_ncw,rm_ncw=loglog_fit(LAGS[ci],m[ci])
            mcw=Cq(q)*np.power(S[ci]-nug,q/2)
            zc_cw,se_ccw,rm_ccw=loglog_fit(LAGS[ci],mcw)
            H_all,H_sub,H_cor=zn_all/q,zn_sub/q,zc_sub/q
            H_cw_n,H_cw_c=zn_cw/q,zc_cw/q
            tot=H_cor-H_all
            rows.append(dict(root=root,geom=geom,q=q,
                n_lags_all=len(LAGS),n_lags_surviving=int(good.sum()),
                lags_dropped=int(len(LAGS)-good.sum()),
                surviving_min=int(sub.min()),surviving_max=int(sub.max()),
                H_naive_all=H_all,se_naive_all=se_all/q,rmse_naive_all=rm_all,
                H_naive_subset=H_sub,se_naive_subset=se_sub/q,rmse_naive_subset=rm_sub,
                H_corrected_subset=H_cor,se_corrected=se_c/q,rmse_corrected=rm_c,
                total_shift=tot,
                shift_from_lag_selection=H_sub-H_all,
                shift_from_nugget=H_cor-H_sub,
                share_lag_selection=float((H_sub-H_all)/tot) if abs(tot)>1e-12 else np.nan,
                share_nugget=float((H_cor-H_sub)/tot) if abs(tot)>1e-12 else np.nan,
                H_common_naive=H_cw_n,H_common_corrected=H_cw_c,
                common_shift=H_cw_c-H_cw_n,
                rmse_common_naive=rm_ncw,rmse_common_corrected=rm_ccw,
                nugget=nug,nugget_share_lag1=float(nug/S[0]),
                nugget_share_lag40=float(nug/S[-1])))
            # over-subtraction sensitivity
            for sc in NUGGET_SCALES:
                g2=(S-sc*nug)>1e-12
                if g2.sum()<5: continue
                m2=Cq(q)*np.power(S[g2]-sc*nug,q/2)
                z2,_,rm2=loglog_fit(LAGS[g2],m2)
                scal.append(dict(root=root,geom=geom,q=q,nugget_scale=sc,
                    n_lags=int(g2.sum()),H=z2/q,rmse=rm2,
                    H_naive_all=H_all,delta=z2/q-H_all))
    K10=pd.DataFrame(rows); K10.to_csv(os.path.join(RES,"phase1_k10_decomposition.csv"),index=False)
    SC=pd.DataFrame(scal); SC.to_csv(os.path.join(RES,"phase1_nugget_sensitivity.csv"),index=False)
    np.savez_compressed(os.path.join(CACHE,"k10_moments.npz"),
        **{f"{r}_{g}_q{q}":np.vstack([MOM[(r,g,q)][0],MOM[(r,g,q)][1]])
           for r,g in CELLS4 for q in QS},lags=LAGS,common=np.array(common))
    d10=dict(common_lag_window=[int(min(common)),int(max(common))],
        n_common_lags=len(common),
        lags_dropped_by_cell={f"{r}/{g}/q{q}":int(K10[(K10.root==r)&(K10.geom==g)&
            (K10.q==q)].lags_dropped.iloc[0]) for r,g in CELLS4 for q in QS},
        max_share_lag_selection=float(K10.share_lag_selection.max()),
        min_share_lag_selection=float(K10.share_lag_selection.min()),
        max_abs_shift_from_lag_selection=float(K10.shift_from_lag_selection.abs().max()),
        n_rows_lag_selection_majority=int((K10.share_lag_selection>0.5).sum()),
        n_rows=len(K10),
        max_common_shift=float(K10.common_shift.abs().max()),
        min_common_shift=float(K10.common_shift.abs().min()),
        all_common_shift_above_0p02=bool((K10.common_shift.abs()>0.02).all()),
        threshold=0.02)
    d10["K10_survives"]=bool(d10["n_rows_lag_selection_majority"]==0 and
                             d10["all_common_shift_above_0p02"])
    out["K10"]=d10; timers["phase1"]=round(time.time()-t,1)
    pd.set_option("display.width",280)
    print("=== PHASE 1: K10 lag-selection decomposition ===")
    print(K10[["root","geom","q","n_lags_surviving","lags_dropped","H_naive_all",
               "H_naive_subset","H_corrected_subset","shift_from_lag_selection",
               "shift_from_nugget","share_lag_selection","share_nugget"]].round(4).to_string(index=False))
    print(f"\ncommon lag window across all cells and all q: {min(common)}..{max(common)}"
          f" ({len(common)} lags)")
    print(K10[["root","geom","q","H_common_naive","H_common_corrected","common_shift",
               "rmse_common_naive","rmse_common_corrected"]].round(4).to_string(index=False))
    print("\n=== nugget over-subtraction sensitivity ===")
    print(SC.pivot_table(index=["root","geom","q"],columns="nugget_scale",
                         values="H").round(4).to_string())
    print(); print(json.dumps(d10,indent=1))
    # =============================== PHASE 2: K9 CLASSICAL ERROR
    t=time.time(); k9=[]; cor=[]
    P7=pd.read_csv(os.path.join(S11,"results","phase7_proxy_fits.csv"))
    def har_design(y):
        T=len(y); c=np.concatenate([[0.0],np.cumsum(y)])
        def avg(k):
            o=np.full(T,np.nan); o[k-1:]=(c[k:]-c[:-k])/k; return o
        x1=np.roll(y,1); x1[0]=np.nan
        x5=np.roll(avg(5),1); x5[0]=np.nan
        x22=np.roll(avg(22),1); x22[0]=np.nan
        return np.column_stack([x1,x5,x22])
    for root,geom in CELLS4:
        M5=FIVEMIN[(geom,"1day")]
        rw,kw,ds=cell_windows(root,geom,"1day")
        rv=p1_rv(subbars(rw,M5))
        Mf=rw.shape[1]
        om2=float((rw**2).sum(axis=1).mean()/(2.0*Mf))
        Hk=kernel_H(Mf,om2,float(rv.mean()))
        rk=np.maximum(p3_kernel_flattop(rw,Hk),1e-300)
        pos=(rv>0)&(rk>0)
        lrv=np.log(rv[pos]); lrk=np.log(rk[pos])
        err=lrv-lrk
        n=int(pos.sum())
        def rho_se(a,b):
            m=np.isfinite(a)&np.isfinite(b)
            r=float(np.corrcoef(a[m],b[m])[0,1]); k=int(m.sum())
            return r,float(np.sqrt(max(1-r*r,1e-12)/max(k-2,1)))
        r_lvl,se_lvl=rho_se(err,lrk)
        X=har_design(lrv)
        names=["daily","weekly","monthly"]
        rr={}
        for j,nm in enumerate(names):
            rj,sj=rho_se(err,X[:,j])
            rr[nm]=(rj,sj)
            cor.append(dict(root=root,geom=geom,against=nm,rho=rj,se=sj,
                            t=rj/sj if sj>0 else np.nan))
        cor.append(dict(root=root,geom=geom,against="log_kernel_level",rho=r_lvl,
                        se=se_lvl,t=r_lvl/se_lvl if se_lvl>0 else np.nan))
        # variance decomposition of the measured error
        var_err=float(err.var())
        frac_level=float(r_lvl**2)         # share of error variance explained by the level
        frac_classical=1.0-frac_level
        r7=P7[(P7.cell==f"{root}/{geom}/B0/1day")&(P7.proxy=="RV")].iloc[0]
        v_fit=float(r7.A*np.power(M5,r7.b))
        # HAR under three Sigma_E scalings
        y=np.log(np.maximum(rv,1e-300)); y[~(rv>0)]=np.nan
        Xd=har_design(y); ok=np.isfinite(Xd).all(axis=1)&np.isfinite(y)
        Xo,yo=Xd[ok],y[ok]; nn=len(yo)
        Z=np.column_stack([np.ones(nn),Xo])
        bhat,*_=np.linalg.lstsq(Z,yo,rcond=None)
        resid=yo-Z@bhat
        Sxx=np.cov(Xo,rowvar=False)
        base=np.array([[1.0,1/5,1/22],[1/5,1/5,1/22],[1/22,1/22,1/22]])
        rec={}
        for tag,scale in [("full",1.0),("partial_classical_only",frac_classical),
                          ("measured_var_err",var_err/max(v_fit,1e-12))]:
            SE=v_fit*scale*base
            St=Sxx-SE
            ev=np.linalg.eigvalsh(St)
            bc=np.linalg.solve(St,Sxx@bhat[1:]) if ev.min()>0 else np.full(3,np.nan)
            rec[tag]=dict(v_used=v_fit*scale,beta=bc.tolist(),
                cond=float(np.linalg.cond(St)),min_eig=float(ev.min()),
                rel_shift_daily=float(bc[0]/bhat[1]-1.0) if np.isfinite(bc[0]) else np.nan,
                weekly_sign_flip=bool(np.isfinite(bc[1]) and (bc[1]<0)<(bhat[2]<0)))
        evx=np.linalg.eigvalsh(Sxx)
        k9.append(dict(root=root,geom=geom,n=nn,
            cond_Sxx=float(np.linalg.cond(Sxx)),min_eig_Sxx=float(evx.min()),
            v_fitted=v_fit,var_err_measured=var_err,
            ratio_measured_to_fitted=var_err/max(v_fit,1e-12),
            rho_err_level=r_lvl,se_rho=se_lvl,t_rho=r_lvl/se_lvl,
            frac_level=frac_level,frac_classical=frac_classical,
            rho_err_daily=rr["daily"][0],rho_err_weekly=rr["weekly"][0],
            rho_err_monthly=rr["monthly"][0],
            b_d_naive=float(bhat[1]),b_w_naive=float(bhat[2]),b_m_naive=float(bhat[3]),
            b_d_full=rec["full"]["beta"][0],b_w_full=rec["full"]["beta"][1],
            b_m_full=rec["full"]["beta"][2],
            b_d_partial=rec["partial_classical_only"]["beta"][0],
            b_w_partial=rec["partial_classical_only"]["beta"][1],
            b_m_partial=rec["partial_classical_only"]["beta"][2],
            b_d_measured=rec["measured_var_err"]["beta"][0],
            b_w_measured=rec["measured_var_err"]["beta"][1],
            b_m_measured=rec["measured_var_err"]["beta"][2],
            shift_full=rec["full"]["rel_shift_daily"],
            shift_partial=rec["partial_classical_only"]["rel_shift_daily"],
            shift_measured=rec["measured_var_err"]["rel_shift_daily"],
            cond_measured=rec["measured_var_err"]["cond"],
            min_eig_measured=rec["measured_var_err"]["min_eig"],
            cond_full=rec["full"]["cond"],min_eig_full=rec["full"]["min_eig"],
            cond_partial=rec["partial_classical_only"]["cond"],
            min_eig_partial=rec["partial_classical_only"]["min_eig"],
            rmse=float(np.sqrt((resid**2).mean()))))
        np.savez_compressed(os.path.join(CACHE,f"k9check_{root}_{geom}.npz"),
            err=err,lrk=lrk,lrv=lrv,Sxx=Sxx,beta_naive=bhat,
            frac_classical=frac_classical,v_fit=v_fit,var_err=var_err)
    K9=pd.DataFrame(k9); K9.to_csv(os.path.join(RES,"phase2_k9_check.csv"),index=False)
    CR=pd.DataFrame(cor); CR.to_csv(os.path.join(RES,"phase2_error_correlations.csv"),index=False)
    d9=dict(threshold=0.10,
        rho_err_level_range=[float(K9.rho_err_level.min()),float(K9.rho_err_level.max())],
        max_abs_t_rho=float(K9.t_rho.abs().max()),
        frac_classical_range=[float(K9.frac_classical.min()),float(K9.frac_classical.max())],
        ratio_measured_to_fitted_range=[float(K9.ratio_measured_to_fitted.min()),
                                        float(K9.ratio_measured_to_fitted.max())],
        min_eig_Sxx_range=[float(K9.min_eig_Sxx.min()),float(K9.min_eig_Sxx.max())],
        min_eig_full_range=[float(K9.min_eig_full.min()),float(K9.min_eig_full.max())],
        cond_full_range=[float(K9.cond_full.min()),float(K9.cond_full.max())],
        shift_full_range=[float(K9.shift_full.min()),float(K9.shift_full.max())],
        shift_partial_range=[float(K9.shift_partial.min()),float(K9.shift_partial.max())],
        all_partial_below_10pct=bool((K9.shift_partial.abs()<0.10).all()),
        all_full_below_10pct=bool((K9.shift_full.abs()<0.10).all()),
        shift_measured_range=[float(K9.shift_measured.min()),float(K9.shift_measured.max())],
        all_measured_below_10pct=bool((K9.shift_measured.abs()<0.10).all()),
        n_weekly_sign_flip_measured=int(((K9.b_w_naive>0)&(K9.b_w_measured<0)).sum()),
        n_weekly_sign_flip_full=int(((K9.b_w_naive>0)&(K9.b_w_full<0)).sum()),
        n_weekly_sign_flip_partial=int(((K9.b_w_naive>0)&(K9.b_w_partial<0)).sum()))
    d9["K9_determination_survives"]=bool(not d9["all_partial_below_10pct"])
    out["K9"]=d9; timers["phase2"]=round(time.time()-t,1)
    print("\n=== PHASE 2: K9 conditioning and the classical assumption ===")
    print(K9[["root","geom","cond_Sxx","min_eig_Sxx","cond_full","min_eig_full",
              "v_fitted","var_err_measured","ratio_measured_to_fitted","rho_err_level",
              "t_rho","frac_classical"]].round(5).to_string(index=False))
    print("\n=== error correlation with each regressor ===")
    print(CR.round(4).to_string(index=False))
    print("\n=== coefficients: naive, full correction, partial (classical share only) ===")
    print(K9[["root","geom","b_d_naive","b_d_full","b_d_partial","b_d_measured",
              "shift_full","shift_partial","shift_measured","b_w_naive","b_w_full",
              "b_w_partial","b_w_measured"]].round(4).to_string(index=False))
    print(); print(json.dumps(d9,indent=1))
    # =============================== PHASE 3: TREND AGAINST CONDITIONING
    t=time.time()
    Y=pd.read_csv(os.path.join(S14,"results","phase5_year_fits.csv"))
    d=Y.copy(); cats=sorted(d["distinct"].unique()); cm={c:i for i,c in enumerate(cats)}
    cid=d["distinct"].map(cm).values.astype(int); ncl=len(cats); n=len(d)
    def within(v):
        v=np.asarray(v,float)
        return v-np.array([v[cid==g].mean() for g in range(ncl)])[cid]
    yv=within(d.b.values)
    specs={"year_only":["year"],
           "year_plus_cond":["year","log_cond"],
           "year_plus_cond_plus_Aoverc":["year","log_cond","A_over_c"]}
    def fit(cols):
        X=np.column_stack([within(d[c].values) for c in cols])
        b,*_=np.linalg.lstsq(X,yv,rcond=None); e=yv-X@b
        XtXi=np.linalg.inv(X.T@X); s2=float((e*e).sum()/(n-ncl-len(cols)))
        se=np.sqrt(np.diag(XtXi)*s2)
        G=np.zeros((ncl,len(cols)))
        for g in range(ncl):
            m=cid==g; G[g]=X[m].T@e[m]
        meat=G.T@G
        cl=np.sqrt(np.diag(XtXi@meat@XtXi))
        return X,b,se,cl,e,float(1-(e*e).sum()/max((yv*yv).sum(),1e-300))
    def wcb(X,b0_index,nrep,seed):
        Xr=np.delete(X,b0_index,axis=1)
        if Xr.shape[1]:
            br,*_=np.linalg.lstsq(Xr,yv,rcond=None); rr=yv-Xr@br
        else: rr=yv.copy()
        rng=np.random.Generator(np.random.PCG64(seed))
        XtXi=np.linalg.inv(X.T@X)
        ts=np.empty(nrep)
        for i in range(nrep):
            w=rng.choice(np.array([-1.0,1.0]),size=ncl)[cid]
            ys=(Xr@br if Xr.shape[1] else 0.0)+w*rr
            bs,*_=np.linalg.lstsq(X,ys,rcond=None); es=ys-X@bs
            G=np.zeros((ncl,X.shape[1]))
            for g in range(ncl):
                m=cid==g; G[g]=X[m].T@es[m]
            cl=np.sqrt(np.diag(XtXi@(G.T@G)@XtXi))
            ts[i]=bs[b0_index]/max(cl[b0_index],1e-300)
        return ts
    tr=[]; draws={}
    for nm,cols in specs.items():
        X,b,se,cl,e,r2=fit(cols)
        tobs=b[0]/cl[0]
        ts=wcb(X,0,NREP,MASTER_WCB+len(cols))
        p=float((np.abs(ts)>=abs(tobs)).mean())
        draws[nm]=ts
        # VIF for the year column
        if len(cols)>1:
            Xo=np.column_stack([within(d[c].values) for c in cols[1:]])
            yy=within(d.year.values)
            bb,*_=np.linalg.lstsq(Xo,yy,rcond=None); rr2=yy-Xo@bb
            vif=float(1.0/max(1-(1-(rr2**2).sum()/max((yy*yy).sum(),1e-300)),1e-12))
            vif=float(1.0/max((rr2**2).sum()/max((yy*yy).sum(),1e-300),1e-12))
        else: vif=1.0
        # interval by inverting the WCR test
        grid=np.linspace(b[0]-6*cl[0],b[0]+6*cl[0],121); keep=[]
        for g0 in grid:
            yv2=yv-g0*X[:,0]
            Xr=np.delete(X,0,axis=1)
            if Xr.shape[1]:
                br,*_=np.linalg.lstsq(Xr,yv2,rcond=None); rr=yv2-Xr@br
            else: rr=yv2.copy()
            rng=np.random.Generator(np.random.PCG64(MASTER_WCB+500))
            XtXi=np.linalg.inv(X.T@X); cnt=0; NR=1499
            for i in range(NR):
                w=rng.choice(np.array([-1.0,1.0]),size=ncl)[cid]
                ys=g0*X[:,0]+(Xr@br if Xr.shape[1] else 0.0)+w*rr
                bs,*_=np.linalg.lstsq(X,ys,rcond=None); es=ys-X@bs
                G=np.zeros((ncl,X.shape[1]))
                for gg in range(ncl):
                    mm=cid==gg; G[gg]=X[mm].T@es[mm]
                clx=np.sqrt(np.diag(XtXi@(G.T@G)@XtXi))
                if abs((bs[0]-g0)/max(clx[0],1e-300))>=abs((b[0]-g0)/max(cl[0],1e-300)):
                    cnt+=1
            if cnt/NR>0.05: keep.append(float(g0))
        ci=[min(keep),max(keep)] if keep else [np.nan,np.nan]
        tr.append(dict(spec=nm,regressors=";".join(cols),n_obs=n,n_clusters=ncl,
            year_coef=float(b[0]),se_ols=float(se[0]),se_cluster=float(cl[0]),
            t_cluster=float(tobs),p_wcb=p,ci_lo=ci[0],ci_hi=ci[1],
            vif_year=vif,r2_within=r2,
            other_coefs={c:float(v) for c,v in zip(cols[1:],b[1:])},
            rmse=float(np.sqrt((e*e).mean())),
            significant_05=bool(p<0.05)))
        print(f"  {nm:32s} year={b[0]:+.5f} se_cl={cl[0]:.5f} t={tobs:+.3f} "
              f"p_wcb={p:.4f} CI=[{ci[0]:+.5f},{ci[1]:+.5f}] VIF={vif:.2f} R2w={r2:.3f}",
              flush=True)
    np.savez_compressed(os.path.join(CACHE,"trend_wcb.npz"),
        **{f"t_{k}":v for k,v in draws.items()},seed=MASTER_WCB,nrep=NREP)
    TR=pd.DataFrame(tr); TR.to_csv(os.path.join(RES,"phase3_trend_control.csv"),index=False)
    d3=dict(nrep=NREP,master_seed=MASTER_WCB,n_clusters=ncl,
        rademacher_floor=float(2**-(ncl-1)),
        year_coef_no_control=float(TR[TR.spec=="year_only"].year_coef.iloc[0]),
        year_coef_with_cond=float(TR[TR.spec=="year_plus_cond"].year_coef.iloc[0]),
        year_coef_with_both=float(TR[TR.spec=="year_plus_cond_plus_Aoverc"].year_coef.iloc[0]),
        p_no_control=float(TR[TR.spec=="year_only"].p_wcb.iloc[0]),
        p_with_cond=float(TR[TR.spec=="year_plus_cond"].p_wcb.iloc[0]),
        p_with_both=float(TR[TR.spec=="year_plus_cond_plus_Aoverc"].p_wcb.iloc[0]),
        shrinkage_from_control=float(1-abs(TR[TR.spec=="year_plus_cond"].year_coef.iloc[0])/
                                     abs(TR[TR.spec=="year_only"].year_coef.iloc[0])),
        vif_year_with_cond=float(TR[TR.spec=="year_plus_cond"].vif_year.iloc[0]),
        s11_s13_figure=-0.04690369993539321,
        eight_cluster_note=("Eight clusters throughout. The wild cluster bootstrap "
            "with the null imposed is the recommended small-G correction but is only "
            f"asymptotically valid in G, and the attainable floor is 2^-7 = "
            f"{2**-7:.5f}. No result here is conventional evidence at any nominal "
            "level, whichever way it comes out."))
    d3["trend_survives_control"]=bool(TR[TR.spec=="year_plus_cond"].p_wcb.iloc[0]<0.05)
    out["trend"]=d3; timers["phase3"]=round(time.time()-t,1)
    print("\n=== PHASE 3 ==="); print(TR.drop(columns=["other_coefs"]).round(5).to_string(index=False))
    print(); print(json.dumps(d3,indent=1))
    out["timers"]=timers
    json.dump(out,open(os.path.join(RES,"s15_summary.json"),"w"),indent=1,default=str)
    print(f"\nS15 PHASES 1-3 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
