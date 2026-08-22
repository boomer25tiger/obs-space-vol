"""S16 Phase 1: the recoverable band, reported BEFORE any classification (item 120).

ANALYTIC RESULT, stated first because it determines the ceiling.

A3 is an AFFINE transform of A1: z = (1-lam)*mu + lam*x. The item-116
specification z-scores the observable WITHIN each rolling window. For any window
W, mean_W(z) = (1-lam)mu + lam*mean_W(x) and sd_W(z) = lam*sd_W(x), so

    (z - mean_W(z)) / sd_W(z) = (x - mean_W(x)) / sd_W(x)

EXACTLY, for every lam > 0. The z-scored input to the HMM is therefore identical
under A1 and A3, and the recoverable band under the published specification is
EMPTY: no day can reflip, and the ceiling on any improvement is exactly zero.

The band is non-empty only if the classification threshold is NOT re-derived on
the corrected series. Under the K8 rule -- a fixed threshold T at the in-sample
median of raw log RV -- shrinkage classifies HIGH when
(1-lam)mu + lam*x > T, i.e. x > T + (1-lam)(T-mu)/lam, so the effective
threshold shifts by (1-lam)(T-mu)/lam and the band has that width. It is
reported as a labelled DIAGNOSTIC outside the pre-registered arm set, because
holding the threshold fixed changes a component and item 118 fixes all
components but the observable.
"""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common16 import BASE,RES,CACHE,S09,CELLS8,FIVEMIN,WINDOW,MA_LEN
from common import cell_windows,subbars
from proxies_robust import p1_rv
def main():
    t0=time.time(); rows=[]; ver=[]
    P3=pd.read_csv(os.path.join(S09,"results","phase3_sizing_params.csv"))
    for root,geom,hname in CELLS8:
        M5=FIVEMIN[(geom,hname)]
        rw,kw,ds=cell_windows(root,geom,hname)
        rv=p1_rv(subbars(rw,M5)); pos=rv>0
        x=np.log(rv[pos]); n=len(x)
        mu=float(x.mean()); T=float(np.median(x)); sdx=float(x.std())
        for rng_tag in ["extended","restricted_S05"]:
            r=P3[(P3.root==root)&(P3.geom==geom)&(P3.btag=="B0")&
                 (P3.horizon==hname)&(P3["range"]==rng_tag)]
            if not len(r) or not bool(r.iloc[0].valid): 
                rows.append(dict(root=root,geom=geom,horizon=hname,lam_range=rng_tag,
                    lam=np.nan,note="lambda undefined on this range (item 66)"))
                continue
            lam=float(r.iloc[0].lam_intercept)
            valid_unit=bool(0.0<lam<=1.0)
            # (a) published specification: z-scored within window -> band EMPTY
            # (b) diagnostic, fixed threshold on the raw scale
            Tprime=T+(1.0-lam)*(T-mu)/lam if valid_unit else np.nan
            lo,hi=(min(T,Tprime),max(T,Tprime)) if np.isfinite(Tprime) else (np.nan,np.nan)
            inband=(int(((x>=lo)&(x<hi)).sum()) if np.isfinite(lo) else 0)
            rows.append(dict(root=root,geom=geom,horizon=hname,lam_range=rng_tag,
                lam=lam,lam_in_unit=valid_unit,n_obs=n,
                mean_log_rv=mu,median_log_rv=T,sd_log_rv=sdx,
                median_minus_mean=T-mu,
                band_published_spec_width=0.0,
                band_published_spec_share=0.0,
                ceiling_published_spec_pp=0.0,
                threshold_shift_diagnostic=(Tprime-T) if np.isfinite(Tprime) else np.nan,
                band_lo_diagnostic=lo,band_hi_diagnostic=hi,
                band_width_diagnostic=(hi-lo) if np.isfinite(lo) else np.nan,
                band_width_in_sd=((hi-lo)/sdx) if np.isfinite(lo) else np.nan,
                n_in_band_diagnostic=inband,
                share_in_band_diagnostic=inband/max(n,1),
                ceiling_diagnostic_pp=100.0*inband/max(n,1),note=""))
        # (c) arm A2: the 5-day moving average is NOT affine, so its reach is measured
        ma=pd.Series(x).rolling(MA_LEN,min_periods=MA_LEN).mean().values
        okm=np.isfinite(ma)
        Tma=float(np.median(ma[okm]))
        flip=(x[okm]>T)!=(ma[okm]>Tma)
        rows[-1].update(a2_n=int(okm.sum()),a2_n_reflipped=int(flip.sum()),
            a2_share_reflipped=float(flip.mean()),a2_median=Tma)
        # numerical verification of the analytic claim, on the first full window
        lam_e=P3[(P3.root==root)&(P3.geom==geom)&(P3.btag=="B0")&
                 (P3.horizon==hname)&(P3["range"]=="extended")].lam_intercept.iloc[0]
        w=x[:WINDOW]; zs1=(w-w.mean())/w.std()
        s=(1-lam_e)*mu+lam_e*w; zs3=(s-s.mean())/s.std()
        ver.append(dict(root=root,geom=geom,horizon=hname,lam=float(lam_e),
            max_abs_zscore_difference=float(np.abs(zs1-zs3).max()),
            identical_to_machine_precision=bool(np.allclose(zs1,zs3,rtol=0,atol=1e-12))))
    B=pd.DataFrame(rows); B.to_csv(os.path.join(RES,"phase1_band.csv"),index=False)
    V=pd.DataFrame(ver); V.to_csv(os.path.join(RES,"phase1_affine_verification.csv"),index=False)
    e=B[B.lam_range=="extended"]
    out=dict(
        analytic_result=("A3 is affine in A1 and the item-116 specification z-scores "
            "within each rolling window, which annihilates affine transforms exactly. "
            "The z-scored HMM input is identical under A1 and A3, the recoverable band "
            "under the published specification is EMPTY, and the ceiling on any "
            "improvement is exactly zero percentage points."),
        max_abs_zscore_difference=float(V.max_abs_zscore_difference.max()),
        all_identical_to_machine_precision=bool(V.identical_to_machine_precision.all()),
        ceiling_published_spec_pp=0.0,
        diagnostic_note=("The fixed-threshold band below holds the K8 threshold on the "
            "raw scale instead of re-deriving it. That changes a component and is "
            "therefore a labelled DIAGNOSTIC, not a fourth arm."),
        diagnostic_band_share_range=[float(e.share_in_band_diagnostic.min()),
                                     float(e.share_in_band_diagnostic.max())],
        diagnostic_ceiling_pp_range=[float(e.ceiling_diagnostic_pp.min()),
                                     float(e.ceiling_diagnostic_pp.max())],
        a2_share_reflipped_range=[float(B.a2_share_reflipped.dropna().min()),
                                  float(B.a2_share_reflipped.dropna().max())],
        timers=dict(phase1=round(time.time()-t0,1)))
    json.dump(out,open(os.path.join(RES,"phase1_summary.json"),"w"),indent=1)
    pd.set_option("display.width",270)
    print("=== ANALYTIC: z-score identity under affine shrinkage ===")
    print(V.to_string(index=False))
    print("\n=== bands, both lambda ranges (item 66) ===")
    print(B[["root","geom","horizon","lam_range","lam","median_minus_mean",
             "band_published_spec_width","ceiling_published_spec_pp",
             "threshold_shift_diagnostic","band_width_in_sd",
             "share_in_band_diagnostic","ceiling_diagnostic_pp","note"]].round(5).to_string(index=False))
    print("\n=== arm A2, the 5-day moving average, measured reach ===")
    print(B[B.a2_n.notna()][["root","geom","horizon","a2_n","a2_n_reflipped",
                             "a2_share_reflipped"]].round(5).to_string(index=False))
    print(); print(json.dumps(out,indent=1))
    print(f"PHASE1 DONE {time.time()-t0:.1f}s")
if __name__=="__main__": main()
