"""S11 Phases 8, 9 and 10: risk-limit breaches (K4), combination weights (K5),
convexity adjustment (K6).

`ho_series` re-executes the tail of S07 `phase2_rerun8.series` on the holdout
panel, which `series()` cannot address because its panel path is hard-coded.
Equivalence is verified by running `ho_series` on the IN-SAMPLE panel and
comparing byte-for-byte against `series()` before any holdout number is used;
the check is asserted, and the run halts if it fails.
"""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common11 import (BASE,RES,CACHE,ROOT,S06,S09,CELLS,FIVEMIN,TICKS,TICKVAL,MULT,
                      NDAY,TARGET_D)
from common import GRID_EXT,subbars,trig,fitf
import partde as pd5
from phase2_rerun8 import series, tradeable_ext, BOUNDARY, OFF
import phase6_holdout as p6
from proxies_robust import p1_rv, p3_kernel_flattop, kernel_H, rq
MODELS=pd5.MODELS
LEV_CAP=2.0; STOP_MULT=1.5          # item 92, fixed before any result
CELLS4=[(r,g) for g in ["GLOBEX","RTH"] for r in ["ES","NQ"]]

def _series_from_grids(cl,hi,lo,op,pres,tr,btag,geom):
    """Line-for-line the S07 `series()` body at wlen=None (the 1day horizon)."""
    r1=np.diff(cl,axis=1); keep=tr[:,1:]&tr[:,:-1]
    if btag=="B1":
        for m in BOUNDARY[geom]:
            s=(m-OFF[geom])%1440 if geom=="GLOBEX" else m-OFF[geom]
            if 0<s<=r1.shape[1]: r1[:,s-1]=0.0
    r1=np.where(keep,r1,0.0)
    rw,kw=r1,keep; HIw,LOw,OPw,CLw=hi,lo,op,cl
    r2=rw**2; rv=r2.sum(axis=1); Meff=kw.sum(axis=1).astype(float)
    Mok=np.maximum(Meff,3.0); a=np.abs(rw)
    bv=(np.pi/2)*(Mok/np.maximum(Mok-1,1))*(a[:,1:]*a[:,:-1]).sum(axis=1)
    rqv=(Mok/3)*(r2*r2).sum(axis=1)
    kmask=np.ones_like(HIw,bool)
    HIm=np.where(kmask,HIw,-np.inf).max(axis=1); LOm=np.where(kmask,LOw,np.inf).min(axis=1)
    okr=np.isfinite(HIm)&np.isfinite(LOm); HIm=np.where(okr,HIm,0.0); LOm=np.where(okr,LOm,0.0)
    park=(HIm-LOm)**2/(4*np.log(2))
    gk=0.5*(HIm-LOm)**2-(2*np.log(2)-1)*(CLw[:,-1]-OPw[:,0])**2
    return dict(rv=rv,bv=bv,rq=rqv,park=park,gk=np.maximum(gk,1e-300),
                ret=rw.sum(axis=1),nw=1,Meff=Meff,tradeable=kw.any(axis=1),rw=rw)

def ho_series(root,geom,btag,holdout=True):
    if holdout:
        z=np.load(os.path.join(S09,"cache",f"ho_panel_{root}_{geom}.npz"))
        tr=z["tradeable"]
    else:
        z=np.load(os.path.join(S06,"cache",f"panel_ohlc_{root}_{geom}.npz"))
        tr,_=tradeable_ext(root,geom)
    g=[z[k].astype(np.float64) for k in ["close","high","low","open"]]
    S=_series_from_grids(g[0],g[1],g[2],g[3],z["present"],tr,btag,geom)
    S["wdates"]=np.array(z["dates"],dtype="U10")
    return S

def verify_equivalence():
    bad=[]
    for root,geom in CELLS4:
        A=series(root,geom,"B0",None); B=ho_series(root,geom,"B0",holdout=False)
        for k in ["rv","bv","rq","park","gk","ret"]:
            if not (len(A[k])==len(B[k]) and np.array_equal(A[k],B[k])):
                bad.append(f"{root}/{geom}:{k}")
    return bad

def size(iv,fc,lam,mu):
    elog=np.log(np.maximum(fc,1e-300)) if lam is None else \
         (1-lam)*mu+lam*np.log(np.maximum(fc,1e-300))
    w=TARGET_D/np.maximum(np.sqrt(np.exp(elog)),1e-12)
    return w,w*np.sqrt(np.maximum(iv,1e-300))

def te_turn_cost(iv,w,tickval,mult,px):
    ok=np.isfinite(w)&np.isfinite(iv)&(iv>0)
    real=w*np.sqrt(np.maximum(iv,1e-300))
    te=float(np.sqrt(np.nanmean((np.log(np.maximum(real[ok],1e-300))-np.log(TARGET_D))**2)))
    turn=float(np.nanmean(np.abs(np.diff(w[ok]))))
    notional=mult*px
    return te,turn,{f"cost_{t}t_bps":float(turn*(2*t*tickval/notional)*1e4) for t in TICKS}

def har_oos(rv_all,n_is,D=1):
    T=len(rv_all); x1,x5,x22=pd5.har_X(rv_all,D)
    X=np.column_stack([np.ones(T),x1,x5,x22]); F=np.full(T,np.nan)
    for t in range(n_is,T):
        Xt,yt=X[22*D:t-1],rv_all[22*D+1:t]
        ok=np.isfinite(Xt).all(axis=1)
        if ok.sum()<6: continue
        b,*_=np.linalg.lstsq(Xt[ok],yt[ok],rcond=None)
        F[t]=max(float(X[t-1]@b),1e-12)
    return F

def main():
    t0=time.time(); timers={}; out={}
    bad=verify_equivalence()
    out["ho_series_equivalence_failures"]=bad
    if bad: raise SystemExit(f"HALT: ho_series does not reproduce series(): {bad}")
    print("ho_series equivalence against S07 series(): byte-identical on all "
          "6 fields x 4 cells",flush=True)
    P3=pd.read_csv(os.path.join(S09,"results","phase3_sizing_params.csv"))
    P7=pd.read_csv(os.path.join(RES,"phase7_proxy_fits.csv"))
    # ================= PHASE 8: K4
    t=time.time(); conf=[]; costs=[]; POS={}
    for root,geom in CELLS4:
        M5=FIVEMIN[(geom,"1day")]
        Sis=ho_series(root,geom,"B0",holdout=False)
        Sho=ho_series(root,geom,"B0",holdout=True)
        # proxy series: RV at the five-minute equivalent (the S09 sizing input)
        rv_is=p1_rv(subbars(Sis["rw"],M5)); rv_ho=p1_rv(subbars(Sho["rw"],M5))
        # best available IV: flat-top realized kernel at the FINEST grid
        Mf_is=Sis["rw"].shape[1]; Mf_ho=Sho["rw"].shape[1]
        om2=float((Sis["rw"]**2).sum(axis=1).mean()/(2.0*Mf_is))
        ivh=float(rv_is.mean()); iqh=float(rq(subbars(Sis["rw"],M5),M5).mean())
        H_is=kernel_H(Mf_is,om2,ivh); H_ho=kernel_H(Mf_ho,om2,ivh)
        rk_is=np.maximum(p3_kernel_flattop(Sis["rw"],H_is),1e-300)
        rk_ho=np.maximum(p3_kernel_flattop(Sho["rw"],H_ho),1e-300)
        n_is=len(rv_is)
        F_rv=har_oos(np.concatenate([rv_is,rv_ho]),n_is)[n_is:]
        F_rk=har_oos(np.concatenate([rk_is,rk_ho]),n_is)[n_is:]
        mu_rv=float(np.log(rv_is[rv_is>0]).mean()); mu_rk=float(np.log(rk_is).mean())
        lam=float(P3[(P3.root==root)&(P3.geom==geom)&(P3.btag=="B0")&
                     (P3.horizon=="1day")&(P3.range=="extended")].lam_intercept.iloc[0])
        w_p,real_p=size(rv_ho,F_rv,lam,mu_rv)     # proxy world
        w_b,real_b=size(rk_ho,F_rk,lam,mu_rk)     # noise-robust world
        px=float(np.exp(np.load(os.path.join(S09,"cache",
             f"ho_panel_{root}_{geom}.npz"))["close"].astype(np.float64)).mean())
        ok=np.isfinite(w_p)&np.isfinite(w_b)
        for lname,bp,bb in [("leverage_cap",w_p>LEV_CAP,w_b>LEV_CAP),
                            ("stop_out",real_p>STOP_MULT*TARGET_D,
                                        real_b>STOP_MULT*TARGET_D)]:
            bp=bp&ok; bb=bb&ok; n=int(ok.sum())
            tp=int((bp&bb).sum()); fp=int((bp&~bb).sum())
            fn=int((~bp&bb).sum()); tn=int((~bp&~bb).sum())
            runs=[];cur=0
            for v in (bp&~bb):
                if v: cur+=1
                elif cur: runs.append(cur); cur=0
            if cur: runs.append(cur)
            conf.append(dict(root=root,geom=geom,limit=lname,n_decision_points=n,
                both=tp,spurious=fp,missed=fn,neither=tn,
                spurious_rate=fp/max(n,1),missed_rate=fn/max(n,1),
                n_spurious_episodes=len(runs),
                mean_spurious_duration=float(np.mean(runs)) if runs else 0.0,
                max_spurious_duration=int(max(runs)) if runs else 0))
            # cost: one round turn out and one back per spurious episode, plus
            # the shortfall in realized volatility while flat, in linear units
            notional=MULT[root]*px
            rel_short=np.abs(np.where(bp&~bb,-1.0,0.0))
            te_lin=float(np.sqrt(np.mean(rel_short[ok]**2)))
            for tk in TICKS:
                rt=2*tk*TICKVAL[root]/notional
                cost_bps=float(len(runs)*2*rt*1e4/max(n,1))
                costs.append(dict(root=root,geom=geom,limit=lname,ticks=tk,
                    n_spurious_episodes=len(runs),
                    breach_cost_bps=cost_bps,
                    te_relative_while_flat=te_lin,
                    total_cost_bps=cost_bps))
        POS[(root,geom)]=dict(w_proxy=w_p,w_best=w_b,rv=rv_ho,rk=rk_ho,
                              F_rv=F_rv,F_rk=F_rk,lam=lam,px=px,H=H_ho)
        np.savez_compressed(os.path.join(CACHE,f"k4_{root}_{geom}.npz"),
            w_proxy=w_p,w_best=w_b,rv=rv_ho,rk=rk_ho,F_rv=F_rv,F_rk=F_rk,
            lam=lam,px=px,H_kernel=H_ho)
    K4=pd.DataFrame(conf); K4.to_csv(os.path.join(RES,"phase8_confusion.csv"),index=False)
    K4C=pd.DataFrame(costs); K4C.to_csv(os.path.join(RES,"phase8_costs.csv"),index=False)
    k4=dict(max_spurious_rate=float(K4.spurious_rate.max()),
        all_below_1pct=bool((K4.spurious_rate<0.01).all()),
        max_cost_bps=float(K4C.total_cost_bps.max()),
        all_cost_below_1bp=bool((K4C.total_cost_bps<1.0).all()),
        leverage_cap=LEV_CAP,stop_mult=STOP_MULT)
    k4["K4"]=("FIRES" if (k4["all_below_1pct"] or k4["all_cost_below_1bp"])
              else "DOES NOT FIRE")
    out["K4"]=k4; timers["phase8"]=round(time.time()-t,1)
    print("\n=== PHASE 8: K4 ==="); print(K4.to_string(index=False))
    print(K4C.pivot_table(index=["root","geom","limit"],columns="ticks",
                          values="total_cost_bps").to_string())
    print(json.dumps(k4,indent=1))
    # ================= PHASE 9: K5
    t=time.time(); wrows=[]; srows=[]; corrs=[]
    for root,geom in CELLS4:
        M5=FIVEMIN[(geom,"1day")]
        Sis=ho_series(root,geom,"B0",holdout=False)
        Sho=ho_series(root,geom,"B0",holdout=True)
        rv_is=p1_rv(subbars(Sis["rw"],M5)); rv_ho=p1_rv(subbars(Sho["rw"],M5))
        n_is=len(rv_is)
        cat={k:np.concatenate([Sis[k],Sho[k]]) for k in
             ["rv","bv","rq","park","gk","ret"]}
        cat["rv"]=np.concatenate([rv_is,rv_ho])          # five-minute-equivalent RV
        cat["nw"]=1
        warm=n_is
        F,start,nonconv=pd5.forecasts(cat,1,warm,1,True)
        avail=[m for m in MODELS if np.isfinite(F[m][n_is:]).mean()>0.5]
        dropped_avail=[m for m in MODELS if m not in avail]
        # in-sample MSE in LOG space, so the Phase 7 noise term is commensurate
        Fis,_,_=pd5.forecasts({**cat,"rv":cat["rv"][:n_is],"bv":Sis["bv"],
                               "rq":Sis["rq"],"park":Sis["park"],"gk":Sis["gk"],
                               "ret":Sis["ret"],"nw":1},1,500,1,True)
        y=np.log(np.maximum(rv_is,1e-300))
        r7=P7[(P7.cell==f"{root}/{geom}/B0/1day")&(P7.proxy=="RV")].iloc[0]
        noise=float(r7.A*np.power(M5,r7.b))
        mse={}; msec={}
        for m in avail:
            f=np.log(np.maximum(Fis[m],1e-300))
            ok=np.isfinite(f)&np.isfinite(y); ok[:500]=False
            mse[m]=float(np.mean((f[ok]-y[ok])**2))
            msec[m]=mse[m]-noise
        excl=[m for m in avail if msec[m]<=0]
        keep=[m for m in avail if msec[m]>0]
        wn={m:1.0/mse[m] for m in avail}; sn=sum(wn.values())
        wn={m:v/sn for m,v in wn.items()}
        wc={m:1.0/msec[m] for m in keep}; sc=sum(wc.values())
        wc={m:v/sc for m,v in wc.items()}
        for m in MODELS:
            wrows.append(dict(root=root,geom=geom,model=m,
                available=m in avail,mse=mse.get(m,np.nan),
                mse_corrected=msec.get(m,np.nan),noise_var=noise,
                w_naive=wn.get(m,0.0),w_corrected=wc.get(m,0.0),
                excluded_corrected=m in excl,
                abs_change=abs(wn.get(m,0.0)-wc.get(m,0.0))))
        FM=np.column_stack([F[m][n_is:] for m in avail])
        okr=np.isfinite(FM).all(axis=1)
        C=np.corrcoef(np.log(np.maximum(FM[okr],1e-300)).T)
        for i,a in enumerate(avail):
            for j,b_ in enumerate(avail):
                corrs.append(dict(root=root,geom=geom,model_i=a,model_j=b_,
                                  corr=float(C[i,j])))
        comb_n=np.nansum(np.column_stack([wn[m]*F[m][n_is:] for m in avail]),axis=1)
        comb_c=np.nansum(np.column_stack([wc[m]*F[m][n_is:] for m in keep]),axis=1)
        mu=float(np.log(rv_is[rv_is>0]).mean())
        lam=POS[(root,geom)]["lam"]; px=POS[(root,geom)]["px"]
        for tag,fc in [("naive",comb_n),("corrected",comb_c)]:
            fc=np.where(okr,fc,np.nan)
            w,_=size(rv_ho,fc,lam,mu)
            te,turn,cst=te_turn_cost(rv_ho,w,TICKVAL[root],MULT[root],px)
            srows.append(dict(root=root,geom=geom,combination=tag,te=te,
                turnover=turn,n=int(okr.sum()),n_models=len(avail if tag=="naive" else keep),
                **cst))
            np.savez_compressed(os.path.join(CACHE,f"k5_{root}_{geom}_{tag}.npz"),
                w=w,forecast=fc,weights=np.array([ (wn if tag=="naive" else wc).get(m,0.0)
                                                   for m in MODELS]),models=np.array(MODELS))
        print(f"  K5 {root}/{geom}: avail={len(avail)} excluded_corrected={excl} "
              f"noise={noise:.4f} mean|dw|={np.mean([abs(wn.get(m,0)-wc.get(m,0)) for m in MODELS]):.4f}",flush=True)
    W=pd.DataFrame(wrows); W.to_csv(os.path.join(RES,"phase9_weights.csv"),index=False)
    pd.DataFrame(corrs).to_csv(os.path.join(RES,"phase9_forecast_corr.csv"),index=False)
    SZ=pd.DataFrame(srows); SZ.to_csv(os.path.join(RES,"phase9_sizing.csv"),index=False)
    per=W.groupby(["root","geom"]).abs_change.agg(["mean","max"]).reset_index()
    pv=SZ.pivot_table(index=["root","geom"],columns="combination",values="te").reset_index()
    pv["rel_te_diff_pct"]=100*(pv.naive-pv.corrected).abs()/pv.naive
    pv.to_csv(os.path.join(RES,"phase9_te_compare.csv"),index=False)
    k5=dict(mean_abs_weight_change_max=float(per["mean"].max()),
        max_abs_weight_change=float(per["max"].max()),
        all_mean_below_0p02=bool((per["mean"]<0.02).all()),
        max_rel_te_diff_pct=float(pv.rel_te_diff_pct.max()),
        all_te_below_5pct=bool((pv.rel_te_diff_pct<5.0).all()),
        n_excluded_corrected=int(W.excluded_corrected.sum()),
        mean_forecast_corr=float(pd.DataFrame(corrs).query("model_i!=model_j").corr_.mean()
                                 if False else pd.DataFrame(corrs).loc[
                                     lambda d:d.model_i!=d.model_j,"corr"].mean()))
    k5["K5"]=("FIRES" if (k5["all_mean_below_0p02"] or k5["all_te_below_5pct"])
              else "DOES NOT FIRE")
    out["K5"]=k5; timers["phase9"]=round(time.time()-t,1)
    print("\n=== PHASE 9: K5 ==="); print(per.to_string(index=False))
    print(pv.to_string(index=False)); print(json.dumps(k5,indent=1))
    # ================= PHASE 10: K6
    t=time.time()
    V=pd.read_csv(os.path.join(RES,"phase5_five_minute.csv"))
    rows=[]
    for _,r in V.iterrows():
        for tag,s2 in [("corrected",r.c),("naive",r.var_log_rv_naive),
                       ("c_lo",r.c_lo),("c_hi",r.c_hi)]:
            rows.append(dict(root=r.root,geom=r.geom,btag=r.btag,horizon=r.horizon,
                M=r.M,basis=tag,s2=s2,factor=(np.exp(s2)-1.0)/8.0))
    A=pd.DataFrame(rows)
    P=A.pivot_table(index=["root","geom","btag","horizon","M"],columns="basis",
                    values="factor").reset_index()
    P.columns=[f"factor_{c}" if c in ["corrected","naive","c_lo","c_hi"] else c
               for c in P.columns]
    S2=A.pivot_table(index=["root","geom","btag","horizon","M"],columns="basis",
                     values="s2").reset_index()
    S2.columns=[f"s2_{c}" if c in ["corrected","naive","c_lo","c_hi"] else c
                for c in S2.columns]
    P=P.merge(S2,on=["root","geom","btag","horizon","M"])
    P["overstatement_prop"]=P.factor_naive/P.factor_corrected-1.0
    # in volatility points: adjustment = sqrt(E[V]) * factor. Annualise E[V] to a
    # 20 percent variance-swap strike so the figure is quotable in vol points.
    K_VAR_ANN=0.20**2
    P["adj_vol_points_corrected"]=np.sqrt(K_VAR_ANN)*P.factor_corrected*100
    P["adj_vol_points_naive"]=np.sqrt(K_VAR_ANN)*P.factor_naive*100
    P["diff_vol_points"]=P.adj_vol_points_naive-P.adj_vol_points_corrected
    P["adj_vol_points_c_lo"]=np.sqrt(K_VAR_ANN)*P.factor_c_lo*100
    P["adj_vol_points_c_hi"]=np.sqrt(K_VAR_ANN)*P.factor_c_hi*100
    P.to_csv(os.path.join(RES,"phase10_convexity.csv"),index=False)
    k6=dict(max_overstatement_prop=float(P.overstatement_prop.max()),
        min_overstatement_prop=float(P.overstatement_prop.min()),
        all_below_5pct=bool((P.overstatement_prop.abs()<0.05).all()),
        max_diff_vol_points=float(P.diff_vol_points.abs().max()),
        strike_assumed_ann_vol=0.20,
        relation=("Brockhaus and Long (2000), second-order Taylor expansion of "
            "sqrt around E[V]: K_vol = sqrt(E[V]) - Var(V)/(8 E[V]^{3/2}). With V "
            "lognormal, Var(V)/E[V]^2 = exp(s^2)-1, so the adjustment is "
            "sqrt(E[V]) * (exp(s^2)-1)/8 with s^2 = Var(log IV)."),
        direction=("Naive s^2 exceeds c in every cell, so the naive convexity "
            "adjustment is too large and the implied volatility-swap strike too "
            "low. That favours the payer of fixed on a volatility swap, i.e. the "
            "side that is long volatility at the quoted strike."),
        no_pnl_claim=("No options data is held. This is a pricing-bias calculation "
            "on the adjustment term only and no claim is made about executable P&L."))
    k6["K6"]=("FIRES" if k6["all_below_5pct"] else "DOES NOT FIRE")
    out["K6"]=k6; timers["phase10"]=round(time.time()-t,1)
    print("\n=== PHASE 10: K6 ===")
    print(P[["root","geom","btag","horizon","M","s2_corrected","s2_naive",
             "overstatement_prop","adj_vol_points_corrected","adj_vol_points_c_lo",
             "adj_vol_points_c_hi","adj_vol_points_naive",
             "diff_vol_points"]].to_string(index=False))
    print(json.dumps(k6,indent=1))
    out["timers"]=timers
    json.dump(out,open(os.path.join(RES,"phase8910_summary.json"),"w"),indent=1,default=str)
    print(f"\nPHASE8-10 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
