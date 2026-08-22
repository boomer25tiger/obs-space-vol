"""S06R Phase 6: Part C rerun. E2 and E4 only, effective M, calendar-excluded."""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy.optimize import curve_fit
from scipy.special import polygamma
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
RES, CACHE = os.path.join(BASE, "results"), os.path.join(BASE, "cache")
S05B = os.path.join(ROOT, "sessions", "s05b-defect-and-estimator-audit", "results")
sys.path.insert(0, os.path.join(BASE, "tests"))
sys.path.insert(0, os.path.join(ROOT, "sessions", "s02-mechanism-expansion", "src"))
sys.path.insert(0, os.path.join(ROOT, "sessions", "s05-reliability-mcs", "src"))
from test_invariants import assert_lambda_in_unit, assert_effective_M, InvariantViolation
import estimators2 as e2mod
from parta import quart_suite
GRID = {("RTH","1day"): [5,6,10,13,26,78,195,389],
        ("RTH","1h"): [4,5,6,10,12,15,20,30,60],
        ("RTH","30min"): [5,6,10,15,30],
        ("GLOBEX","1day"): [5,6,10,12,23,46,138,345,1379]}
HOR = {"1day": None, "1h": 60, "30min": 30}
BOUNDARY = {"RTH":[570,571,959,960], "GLOBEX":[570,571,959,960,1081]}
OFF = {"RTH":570, "GLOBEX":1080}
CELLS = [(r,g,b) for g in ["GLOBEX","RTH"] for r in ["ES","NQ"] for b in ["B0","B1"]]

def e4_eff(P, Q, logP, Meff):
    """E4 with the per-window EFFECTIVE sub-bar count (item 45)."""
    v = (2.0/np.maximum(Meff,1.0)) * Q / np.maximum(P*P, 1e-300)
    return float(1.0 - np.mean(v)/logP.var())

def subbars_masked(rw, kw, M):
    N, L = rw.shape
    e = (np.arange(M+1)*L)//M
    cs = np.concatenate([np.zeros((N,1)), np.cumsum(rw,axis=1)],axis=1)
    sb = cs[:,e[1:]] - cs[:,e[:-1]]
    kc = np.concatenate([np.zeros((N,1)), np.cumsum(kw.astype(np.int32),axis=1)],axis=1)
    kb = kc[:,e[1:]] - kc[:,e[:-1]]
    return sb, (kb > 0).sum(axis=1).astype(float)

def fit_free(M, y):
    M=np.asarray(M,float); y=np.asarray(y,float); ok=np.isfinite(y)
    if ok.sum()<4: return dict(c=np.nan,A=np.nan,b=np.nan,rmse=np.nan)
    try:
        p,_=curve_fit(lambda x,c,A,b: c+A*np.power(x,b), M[ok], y[ok],
                      p0=[y[ok].min(),1.0,-0.5], maxfev=60000)
        pred=p[0]+p[1]*np.power(M[ok],p[2])
        return dict(c=float(p[0]),A=float(p[1]),b=float(p[2]),
                    rmse=float(np.sqrt(np.mean((y[ok]-pred)**2))))
    except Exception: return dict(c=np.nan,A=np.nan,b=np.nan,rmse=np.nan)

def main():
    t0=time.time(); rows=[]; viol=[]; corr=[]; fits=[]
    for root, geom, btag in CELLS:
        z = np.load(os.path.join(CACHE, f"panel_ohlc_{root}_{geom}.npz"))
        cl = z["close"].astype(np.float64); pres = z["present"]
        tr = np.load(os.path.join(CACHE, f"tradeable_{root}_{geom}.npz"))["tradeable"]
        r1 = np.diff(cl, axis=1)
        keep = tr[:,1:] & tr[:,:-1] & pres[:,1:] & pres[:,:-1]
        if btag=="B1":
            for m in BOUNDARY[geom]:
                s=(m-OFF[geom])%1440 if geom=="GLOBEX" else m-OFF[geom]
                if 0 < s <= r1.shape[1]: r1[:,s-1]=0.0
        r1 = np.where(tr[:,1:] & tr[:,:-1], r1, 0.0)
        for (g2,hname), Ms in GRID.items():
            if g2!=geom: continue
            wl = HOR[hname]
            if wl is None: rw, kw = r1, keep
            else:
                nw=r1.shape[1]//wl
                rw=r1[:,:nw*wl].reshape(-1,wl); kw=keep[:,:nw*wl].reshape(-1,wl)
            live = kw.any(axis=1)
            rw, kw = rw[live], kw[live]
            varlogs, Mlist = [], []
            for M in Ms:
                if M > rw.shape[1]: continue
                sb, meff = subbars_masked(rw, kw, M)
                assert_effective_M(meff, meff, f"{root}/{geom}/{btag}/{hname}/M{M}")
                q = quart_suite(sb, M)
                rq, rv = q["RQ_RV"]; trq, trv = q["TRQ3_TRV3"]
                pos = rv > 0
                logp = np.log(np.maximum(rv,1e-300))
                h = M//2
                p1=(sb[:,:h]**2).sum(axis=1); p2=(sb[:,h:]**2).sum(axis=1)
                lam2 = float(e2mod.e2(logp[pos], np.log(np.maximum(p1[pos],1e-300)),
                                      np.log(np.maximum(p2[pos],1e-300))))
                lam4 = e4_eff(trv[pos], trq[pos],
                              np.log(np.maximum(trv[pos],1e-300)), meff[pos])
                vlog = float(logp[pos].var())
                for nm, lv in [("E2",lam2), ("E4",lam4)]:
                    cellid=f"{root}/{geom}/{btag}/{hname}/M{M}"
                    try:
                        assert_lambda_in_unit(lv, cellid, nm)
                        ok=True; msg=""
                    except InvariantViolation as e:
                        ok=False; msg=str(e)
                        viol.append(dict(cell=cellid, estimator=nm, lam=lv, message=msg))
                    rows.append(dict(root=root,geom=geom,btag=btag,horizon=hname,M=M,
                        estimator=nm, lam=lv, var_log_rv=vlog, in_unit=ok,
                        n_windows=int(pos.sum()), mean_eff_M=float(meff.mean()),
                        share_full_M=float((meff==M).mean())))
                varlogs.append(vlog); Mlist.append(M)
                if M == max([m for m in Ms if m<=rw.shape[1]]):
                    vol=np.sqrt(rv[pos]); em=meff[pos]
                    corr.append(dict(root=root,geom=geom,btag=btag,horizon=hname,M=M,
                        corr_effM_vol=float(np.corrcoef(em,vol)[0,1]) if em.std()>0 else np.nan,
                        corr_effM_logvol=float(np.corrcoef(em,np.log(vol))[0,1]) if em.std()>0 else np.nan,
                        mean_eff_M=float(em.mean()), sd_eff_M=float(em.std()),
                        vol_p16=float(np.quantile(vol,.16)), vol_p84=float(np.quantile(vol,.84)),
                        vol_ratio_p84_p16=float(np.quantile(vol,.84)/np.quantile(vol,.16)),
                        sd_log_rv=float(np.log(rv[pos]).std())))
            f = fit_free(Mlist, varlogs)
            old = pd.read_csv(os.path.join(S05B,"phase4_grid_index.csv"))
            o = old[(old.root==root)&(old.geom==geom)&(old.btag==btag)&(old.horizon==hname)]
            fo = fit_free(o.M.values, o.var_log_rv.values) if len(o)>=4 else dict(c=np.nan,A=np.nan,b=np.nan,rmse=np.nan)
            fits.append(dict(root=root,geom=geom,btag=btag,horizon=hname,
                c_new=f["c"],A_new=f["A"],b_new=f["b"],rmse_new=f["rmse"],
                c_s05b=fo["c"],A_s05b=fo["A"],b_s05b=fo["b"],rmse_s05b=fo["rmse"],
                b_shift=f["b"]-fo["b"],
                implied_sd_log_iv=float(np.sqrt(f["c"])) if f["c"]==f["c"] and f["c"]>0 else np.nan,
                implied_vol_ratio_1sd=float(np.exp(np.sqrt(f["c"]))) if f["c"]==f["c"] and f["c"]>0 else np.nan))
    pd.DataFrame(rows).to_csv(os.path.join(RES,"phase6_lambda.csv"),index=False)
    pd.DataFrame(viol).to_csv(os.path.join(RES,"phase6_lambda_violations.csv"),index=False)
    pd.DataFrame(corr).to_csv(os.path.join(RES,"phase6_effM_corr.csv"),index=False)
    pd.DataFrame(fits).to_csv(os.path.join(RES,"phase6_fits.csv"),index=False)
    print("lambda rows:",len(rows),"| [0,1] violations:",len(viol),f"| {time.time()-t0:.0f}s")
    print(pd.DataFrame(fits)[["root","geom","btag","horizon","b_new","b_s05b","b_shift","c_new","implied_vol_ratio_1sd"]].to_string(index=False))
    print("\neff-M correlation:\n", pd.DataFrame(corr)[["root","geom","btag","horizon","corr_effM_vol","mean_eff_M","sd_eff_M","vol_ratio_p84_p16","sd_log_rv"]].to_string(index=False))

if __name__=="__main__": main()
