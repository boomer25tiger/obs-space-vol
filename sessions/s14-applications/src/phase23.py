"""S14 Phases 2 and 3: K9 HAR attenuation, K10 Hurst bias. Pre-2024 only.

K9 DERIVATION. HAR in logs: y_t = a + X*_t beta + u_t with X* the true daily,
weekly and monthly log-volatility averages. Observed X = X* + E. Under classical
measurement error (E independent of X* and of u),

    Sigma_XX = Sigma_X*X* + Sigma_E,   Sigma_Xy = Sigma_X*X* beta
    beta_hat ->p Sigma_XX^{-1} Sigma_X*X* beta
    ==> beta = (Sigma_XX - Sigma_E)^{-1} Sigma_XX beta_hat            [MATRIX form]

not a scalar attenuation factor, because the three regressors share days and
their errors are correlated. With serially independent per-day noise of variance
v, x_1 = e_{t-1}, x_5 = mean of 5 days, x_22 = mean of 22 days:

    Var(E_1)=v      Cov(E_1,E_5)=v/5    Cov(E_1,E_22)=v/22
                    Var(E_5)=v/5        Cov(E_5,E_22)=v/22
                                        Var(E_22)=v/22

Noise in the DEPENDENT variable does not bias the coefficients, only inflates the
residual variance, because y is at t and the regressors are lags t-1..t-22 and
the noise is serially independent. Assumptions: classical measurement error,
serially independent proxy noise, Sigma_E known from the fitted scaling.

K10 DERIVATION. The lag-direction estimator regresses log m(q, D) on log D with
m(q, D) = E|log sigma_{t+D} - log sigma_t|^q. With proxy noise eps of variance
Var(eps) = (1 - lambda) Var(log RV_M), the observed increment carries
2 Var(eps) of extra second moment AT EVERY LAG, an M-invariant nugget that does
not vanish as D -> 0. Under normal increments m(q,D) = C_q S(D)^{q/2} with
C_q = E|Z|^q, so S(D) is recoverable from any q and the corrected moment is
C_q (S(D) - 2 Var(eps))^{q/2}. Applying the estimator to log RV rather than
log sigma scales m by a constant and leaves the slope, hence H, unchanged.
"""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy.special import gamma as gamma_fn
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common14 import BASE,RES,CACHE,S09,S10,S11,CELLS,CELLS4,FIVEMIN
from common import GRID_EXT,cell_windows,subbars,logrv_matrix,var_cols,fitf,fit_diag
from proxies_robust import p1_rv
QS=[0.5,1.0,2.0]; LAGS=list(range(1,41))
def Cq(q): return 2**(q/2)*gamma_fn((q+1)/2)/np.sqrt(np.pi)
def har_design(y,D=1):
    T=len(y); c=np.concatenate([[0.0],np.cumsum(y)])
    def avg(k):
        o=np.full(T,np.nan); o[k-1:]=(c[k:]-c[:-k])/k; return o
    x1=np.roll(y,1); x1[0]=np.nan
    x5=np.roll(avg(5),1); x5[0]=np.nan
    x22=np.roll(avg(22),1); x22[0]=np.nan
    return np.column_stack([x1,x5,x22])
def main():
    t0=time.time(); timers={}; out={}
    P3=pd.read_csv(os.path.join(S09,"results","phase3_sizing_params.csv"))
    P7=pd.read_csv(os.path.join(S11,"results","phase7_proxy_fits.csv"))
    P1=pd.read_csv(os.path.join(S10,"results","phase1_bootstrap.csv"))
    # ================= PHASE 2: K9
    t=time.time(); k9=[]; fc=[]
    for root,geom,btag,hname in CELLS:
        if btag=="B1" or hname!="1day": continue
        M5=FIVEMIN[(geom,hname)]
        rw,kw,ds=cell_windows(root,geom,hname)
        rv=p1_rv(subbars(rw,M5)); pos=rv>0
        y=np.log(np.maximum(rv,1e-300)); y[~pos]=np.nan
        X=har_design(y)
        ok=np.isfinite(X).all(axis=1)&np.isfinite(y)
        Xo,yo=X[ok],y[ok]; n=len(yo)
        Z=np.column_stack([np.ones(n),Xo])
        bhat,*_=np.linalg.lstsq(Z,yo,rcond=None)
        resid=yo-Z@bhat; s2=float((resid**2).sum()/(n-4))
        XtXi=np.linalg.inv(Z.T@Z); se=np.sqrt(np.diag(XtXi)*s2)
        # noise variance from the fitted scaling at the sampling grid actually used
        r7=P7[(P7.cell==f"{root}/{geom}/B0/1day")&(P7.proxy=="RV")].iloc[0]
        v=float(r7.A*np.power(M5,r7.b))
        SE=v*np.array([[1.0,1/5,1/22],[1/5,1/5,1/22],[1/22,1/22,1/22]])
        Sxx=np.cov(Xo,rowvar=False)
        Sxx_true=Sxx-SE
        ev=np.linalg.eigvalsh(Sxx_true)
        bnaive=bhat[1:]
        bcorr=np.linalg.solve(Sxx_true,Sxx@bnaive)
        cn=float(np.linalg.cond(Sxx)); cnt=float(np.linalg.cond(Sxx_true))
        pc=XtXi[1:,1:]/np.sqrt(np.outer(np.diag(XtXi[1:,1:]),np.diag(XtXi[1:,1:])))
        k9.append(dict(root=root,geom=geom,n=n,noise_v=v,
            b_d=bnaive[0],b_w=bnaive[1],b_m=bnaive[2],
            se_d=se[1],se_w=se[2],se_m=se[3],
            bc_d=bcorr[0],bc_w=bcorr[1],bc_m=bcorr[2],
            persistence_naive=float(bnaive.sum()),persistence_corr=float(bcorr.sum()),
            daily_share_naive=float(bnaive[0]/bnaive.sum()),
            daily_share_corr=float(bcorr[0]/bcorr.sum()),
            rel_shift_daily=float(bcorr[0]/bnaive[0]-1.0),
            rel_shift_weekly=float(bcorr[1]/bnaive[1]-1.0),
            rel_shift_monthly=float(bcorr[2]/bnaive[2]-1.0),
            daily_share_shift=float(bcorr[0]/bcorr.sum()-bnaive[0]/bnaive.sum()),
            cond_Sxx=cn,cond_Sxx_true=cnt,min_eig_Sxx_true=float(ev.min()),
            rmse=float(np.sqrt((resid**2).mean())),
            corr_dw=float(pc[0,1]),corr_dm=float(pc[0,2]),corr_wm=float(pc[1,2]),
            r2=float(1-(resid**2).sum()/((yo-yo.mean())**2).sum())))
        # forecast under both coefficient sets: in sample and pseudo-OOS (pre-2024)
        split=int(0.7*n)
        for tag,sl in [("insample",slice(0,n)),("pseudo_oos",slice(split,n))]:
            for cname,bb in [("naive",bnaive),("corrected",bcorr)]:
                pred=bhat[0]+Xo[sl]@bb
                e=yo[sl]-pred
                fc.append(dict(root=root,geom=geom,sample=tag,coefficients=cname,
                    n=int(len(e)),rmse=float(np.sqrt((e**2).mean())),
                    mae=float(np.abs(e).mean()),bias=float(e.mean()),
                    qlike=float(np.mean(np.exp(yo[sl]-pred)-(yo[sl]-pred)-1))))
        np.savez_compressed(os.path.join(CACHE,f"k9_{root}_{geom}.npz"),
            beta_naive=bnaive,beta_corr=bcorr,intercept=bhat[0],se=se,
            Sxx=Sxx,Sigma_E=SE,noise_v=v,X=Xo.astype(np.float32),y=yo)
    K9=pd.DataFrame(k9); K9.to_csv(os.path.join(RES,"phase2_k9.csv"),index=False)
    FC=pd.DataFrame(fc); FC.to_csv(os.path.join(RES,"phase2_forecast.csv"),index=False)
    fp=FC.pivot_table(index=["root","geom","sample"],columns="coefficients",
                      values="rmse").reset_index()
    fp["rel_rmse_diff_pct"]=100*(fp.corrected-fp.naive)/fp.naive
    fp.to_csv(os.path.join(RES,"phase2_forecast_compare.csv"),index=False)
    d9=dict(threshold=0.10,
        max_abs_rel_shift_daily=float(K9.rel_shift_daily.abs().max()),
        rel_shift_daily_by_cell={f"{r}/{g}":float(v) for r,g,v in
            zip(K9.root,K9.geom,K9.rel_shift_daily)},
        all_below_10pct=bool((K9.rel_shift_daily.abs()<0.10).all()),
        persistence_naive_range=[float(K9.persistence_naive.min()),
                                 float(K9.persistence_naive.max())],
        persistence_corr_range=[float(K9.persistence_corr.min()),
                                float(K9.persistence_corr.max())],
        daily_share_shift_range=[float(K9.daily_share_shift.min()),
                                 float(K9.daily_share_shift.max())],
        max_abs_forecast_rmse_diff_pct=float(fp.rel_rmse_diff_pct.abs().max()),
        forecast_claim=("The point forecast is NOT claimed to change. The measured "
            "RMSE difference between the two coefficient sets is reported above and "
            "is the evidence for that statement, not an assertion."),
        min_eig_Sxx_true=float(K9.min_eig_Sxx_true.min()))
    d9["K9"]=("FIRES" if d9["all_below_10pct"] else "DOES NOT FIRE")
    out["K9"]=d9; timers["phase2"]=round(time.time()-t,1)
    pd.set_option("display.width",270)
    print("=== K9 coefficients ===")
    print(K9[["root","geom","noise_v","b_d","se_d","bc_d","rel_shift_daily",
              "b_w","bc_w","b_m","bc_m","persistence_naive","persistence_corr",
              "daily_share_naive","daily_share_corr","cond_Sxx","cond_Sxx_true",
              "rmse"]].to_string(index=False))
    print("\n=== forecast under both coefficient sets ===")
    print(fp.to_string(index=False))
    print(); print(json.dumps(d9,indent=1))
    # ================= PHASE 3: K10
    t=time.time(); k10=[]; mat=[]
    for root,geom,btag,hname in CELLS:
        if btag=="B1" or hname!="1day": continue
        M5=FIVEMIN[(geom,hname)]
        rw,kw,ds=cell_windows(root,geom,hname)
        rv=p1_rv(subbars(rw,M5)); pos=rv>0
        y=np.log(rv[pos])
        varlog=float(y.var())
        lam=float(P3[(P3.root==root)&(P3.geom==geom)&(P3.btag=="B0")&
                     (P3.horizon=="1day")&(P3.range=="extended")].lam_intercept.iloc[0])
        pb=P1[P1.cell==f"{root}/{geom}/B0/1day"].iloc[0]
        lam_lo=float(np.clip(pb.c_lo/varlog,0,1)); lam_hi=float(np.clip(pb.c_hi/varlog,0,1))
        for nm,lm in [("point",lam),("lo",lam_lo),("hi",lam_hi)]:
            vareps=(1.0-lm)*varlog
            for q in QS:
                m=[];S=[]
                for D in LAGS:
                    d=np.abs(y[D:]-y[:-D])
                    mq=float((d**q).mean()); m.append(mq)
                    S.append((mq/Cq(q))**(2.0/q))
                m=np.array(m); S=np.array(S)
                Sc=S-2.0*vareps
                good=Sc>1e-12
                lg=np.log(LAGS)
                An=np.polyfit(lg,np.log(m),1)
                zeta_n=float(An[0]); H_n=zeta_n/q
                predn=np.polyval(An,lg); rmse_n=float(np.sqrt(np.mean((np.log(m)-predn)**2)))
                if good.sum()>=5:
                    mc=Cq(q)*np.power(Sc[good],q/2)
                    Ac=np.polyfit(lg[good],np.log(mc),1)
                    zeta_c=float(Ac[0]); H_c=zeta_c/q
                    predc=np.polyval(Ac,lg[good])
                    rmse_c=float(np.sqrt(np.mean((np.log(mc)-predc)**2)))
                else:
                    zeta_c=H_c=rmse_c=np.nan
                res=np.log(m)-predn
                se_n=float(np.sqrt((res**2).sum()/(len(m)-2)/((lg-lg.mean())**2).sum()))/q
                if nm=="point":
                    for i,D in enumerate(LAGS):
                        mat.append(dict(root=root,geom=geom,q=q,lag=D,
                            S_naive=float(S[i]),nugget=2.0*vareps,
                            S_corrected=float(Sc[i]),
                            nugget_share=float(2.0*vareps/max(S[i],1e-300))))
                k10.append(dict(root=root,geom=geom,q=q,lam_variant=nm,lam=lm,
                    var_log_rv=varlog,var_eps=vareps,nugget=2.0*vareps,
                    H_naive=H_n,se_H_naive=se_n,H_corrected=H_c,
                    delta_H=(H_c-H_n) if np.isfinite(H_c) else np.nan,
                    zeta_naive=zeta_n,zeta_corr=zeta_c,
                    rmse_naive=rmse_n,rmse_corr=rmse_c,n_lags_used=int(good.sum())))
    K10=pd.DataFrame(k10); K10.to_csv(os.path.join(RES,"phase3_k10.csv"),index=False)
    MT=pd.DataFrame(mat); MT.to_csv(os.path.join(RES,"phase3_nugget_by_lag.csv"),index=False)
    pt=K10[K10.lam_variant=="point"]
    mater=MT[MT.nugget_share>0.10].groupby(["root","geom","q"]).lag.max().reset_index()
    mater.columns=["root","geom","q","max_lag_nugget_above_10pct"]
    mater.to_csv(os.path.join(RES,"phase3_material_lags.csv"),index=False)
    d10=dict(threshold=0.02,
        max_abs_delta_H=float(pt.delta_H.abs().max()),
        min_abs_delta_H=float(pt.delta_H.abs().min()),
        all_below_0p02=bool((pt.delta_H.abs()<0.02).all()),
        H_naive_range=[float(pt.H_naive.min()),float(pt.H_naive.max())],
        H_corrected_range=[float(pt.H_corrected.min()),float(pt.H_corrected.max())],
        nugget_share_at_lag1=float(MT[MT.lag==1].nugget_share.max()),
        nugget_share_at_lag40=float(MT[MT.lag==40].nugget_share.max()),
        n_moving_above_0p5=int((pt.H_corrected>0.5).sum()),n_rows=int(len(pt)),
        cont_das_position=("Cont and Das (2024) argue that measured rough volatility "
            "is an artifact of microstructure noise in the volatility proxy and that "
            "correcting for it moves H away from the roughness region toward 0.5. "
            "That is the position being TESTED here against this programme's own "
            "measured reliability, not assumed."))
    d10["K10"]=("FIRES" if d10["all_below_0p02"] else "DOES NOT FIRE")
    out["K10"]=d10; timers["phase3"]=round(time.time()-t,1)
    print("\n=== K10 ===")
    print(pt[["root","geom","q","lam","var_eps","nugget","H_naive","se_H_naive",
              "H_corrected","delta_H","rmse_naive","rmse_corr","n_lags_used"]].to_string(index=False))
    print("\n=== H with the lambda bootstrap interval ===")
    piv=K10.pivot_table(index=["root","geom","q"],columns="lam_variant",
                        values="H_corrected").reset_index()
    print(piv.to_string(index=False))
    print("\n=== lags at which the nugget exceeds 10 percent of the increment moment ===")
    print(mater.to_string(index=False))
    print(); print(json.dumps(d10,indent=1))
    out["timers"]=timers
    json.dump(out,open(os.path.join(RES,"phase23_summary.json"),"w"),indent=1,default=str)
    print(f"PHASE2+3 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
