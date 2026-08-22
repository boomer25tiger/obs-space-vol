"""S05 Parts D and E: six pre-registered models, QLIKE, MCS, IC metrics.

Pre-registered constants (fixed here before any run; all reported):
- Warm-up: 500 windows at the daily horizon; max(500, 22*D + 100) windows
  intraday, D = windows per session.
- OLS models (M2-M4) refit each step at daily horizon, once per session
  intraday. M5 (Realized GARCH, Hansen-Huang-Shek 2012 log-linear spec,
  MLE) refit every 63 sessions, parameters held between refits, previous
  parameters kept on non-convergence (occurrences counted).
- M6 uses the within-window range of minute closes (documented: panels
  carry closes only; the same input feeds Parkinson and Garman-Klass).
- QLIKE(F; RV) = RV/F - log(RV/F) - 1.
- MCS: Hansen-Lunde-Nason (2011), range statistic T_R, moving-block
  bootstrap, block length ceil(T^(1/3)), 10,000 resamples (seed 20260821),
  bootstrap drawn once per run and reused across elimination rounds (the
  authors' procedure); reported at 75% and 90% confidence.
- S-B conditions on realized RV above its evaluation-sample quantile;
  S-C conditions on the M2 (HAR) forecast above its own quantile - one
  common predetermined variable so every model is scored on the same set.
- Reliability correction: lambda_hat = Part C E4 (selected variant) at the
  matching (root, geometry, btag, horizon), finest M, pooled year/tercile.
  corrected IC = IC / sqrt(lambda); corrected R2 = R2 / lambda
  (attenuation form; documented).
"""

import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.signal import lfilter
from scipy.stats import spearmanr

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results")
N_GRID = {"RTH": 390, "GLOBEX": 1380}
MODELS = ["M1_EWMA", "M2_HAR", "M3_HARJ", "M4_HARQ", "M5_RGARCH",
          "M6_PARK", "M6_GK"]
BOOT_N = 10000
BOOT_SEED = 20260821
QS = [0.80, 0.90]


def build_series(grid, wlen):
    """Window RV, BV, RQ, range stats, window log-returns from a panel."""
    n1 = grid.shape[1] - 1
    nw = n1 // wlen if wlen else 1
    if wlen:
        r1 = np.diff(grid, axis=1)[:, :nw * wlen]
        rw = r1.reshape(-1, wlen)
        px = grid[:, :nw * wlen + 1:]
    else:
        rw = np.diff(grid, axis=1)
        nw = 1
    r2 = rw ** 2
    rv = r2.sum(axis=1)
    a = np.abs(rw)
    M = rw.shape[1]
    bv = (np.pi / 2.0) * (M / (M - 1.0)) * (a[:, 1:] * a[:, :-1]).sum(axis=1)
    rq = (M / 3.0) * (r2 * r2).sum(axis=1)
    cum = np.cumsum(rw, axis=1)
    hi = np.maximum(cum.max(axis=1), 0.0)
    lo = np.minimum(cum.min(axis=1), 0.0)
    cl = cum[:, -1]
    park = (hi - lo) ** 2 / (4 * np.log(2))
    gk = 0.5 * (hi - lo) ** 2 - (2 * np.log(2) - 1) * cl ** 2
    return dict(rv=rv, bv=bv, rq=rq, park=park, gk=np.maximum(gk, 1e-300),
                ret=cl, nw=nw)


def har_X(rv, D):
    """HAR regressors at lags 1, 5D, 22D windows (Corsi 2009)."""
    T = len(rv)
    c = np.concatenate([[0.0], np.cumsum(rv)])
    def avg(k):
        out = np.full(T, np.nan)
        out[k - 1:] = (c[k:] - c[:-k]) / k
        return out
    return rv, avg(5 * D), avg(22 * D)


def rgarch_ll(theta, r, logx):
    om, be, ga, xi, ph, t1, t2, lsu = theta
    if not (0 < be < 0.999 and abs(t2) < 0.45):
        return 1e10
    logh = lfilter([ga], [1.0, -be], np.concatenate(
        [[ (om + ga * logx.mean()) / max(1 - be, 1e-3)], logx[:-1]]))
    logh = om + logh
    logh = np.clip(logh, -30, 5)
    h = np.exp(logh)
    z = r / np.sqrt(h)
    u = logx - xi - ph * logh - t1 * z - t2 * (z * z - 1)
    su2 = np.exp(lsu)
    return float(0.5 * np.sum(logh + z * z)
                 + 0.5 * np.sum(lsu + u * u / su2))


def rgarch_fit_forecast(r, logx, theta0):
    res = minimize(rgarch_ll, theta0, args=(r, logx), method="Nelder-Mead",
                   options=dict(maxiter=2000, fatol=1e-6))
    th = res.x if res.fun < 1e9 else theta0
    om, be, ga, xi, ph, t1, t2, lsu = th
    logh = lfilter([ga], [1.0, -be], np.concatenate(
        [[(om + ga * logx.mean()) / max(1 - be, 1e-3)], logx[:-1]]))
    logh = om + logh
    logh_next = om + be * logh[-1] + ga * logx[-1]
    if t2 < 0.45:
        mgf = np.exp(-t2) / np.sqrt(max(1 - 2 * t2, 1e-6)) \
            * np.exp(t1 ** 2 / (2 * max(1 - 2 * t2, 1e-6)))
    else:
        mgf = 1.0
    F = float(np.exp(xi + ph * logh_next + 0.5 * np.exp(lsu)) * mgf)
    return th, F, bool(res.fun < 1e9)


def forecasts(S, D, warm, refit_ols, horizon_daily):
    rv, bv, rq, park, gk, ret = (S["rv"], S["bv"], S["rq"], S["park"],
                                 S["gk"], S["ret"])
    T = len(rv)
    F = {m: np.full(T, np.nan) for m in MODELS}
    # M1 EWMA lambda=0.94 (RiskMetrics) on window returns
    s2 = np.full(T, np.nan)
    s2[0] = rv[:20].mean()
    for t in range(1, T):
        s2[t] = 0.94 * s2[t - 1] + 0.06 * ret[t - 1] ** 2
    F["M1_EWMA"] = s2 * (1.0 if horizon_daily else 1.0)
    # M6 range-based: current-window estimate as one-step forecast
    F["M6_PARK"][1:] = park[:-1]
    F["M6_GK"][1:] = gk[:-1]
    # HAR family
    x1, x5, x22 = har_X(rv, D)
    J = np.maximum(rv - bv, 0.0)
    sq = np.sqrt(np.maximum(rq, 0.0))
    Xf = {"M2_HAR": np.column_stack([np.ones(T), x1, x5, x22]),
          "M3_HARJ": np.column_stack([np.ones(T), x1, x5, x22, J]),
          "M4_HARQ": np.column_stack([np.ones(T), x1, x5, x22, sq * x1])}
    start = max(warm, 22 * D + 2)
    coef = {m: None for m in Xf}
    for t in range(start, T):
        if coef["M2_HAR"] is None or t % refit_ols == 0:
            for m, X in Xf.items():
                Xt, yt = X[22 * D:t - 1], rv[22 * D + 1:t]
                ok = np.isfinite(Xt).all(axis=1)
                b, *_ = np.linalg.lstsq(Xt[ok], yt[ok], rcond=None)
                coef[m] = b
        for m, X in Xf.items():
            F[m][t] = max(float(X[t - 1] @ coef[m]), 1e-300)
    # M5 Realized GARCH, refit every 63 sessions
    logx = np.log(np.maximum(rv, 1e-300))
    th = np.array([0.1, 0.7, 0.25, -0.1, 1.0, -0.05, 0.05,
                   np.log(0.4)])
    refit_m5 = 63 * D
    nonconv = 0
    lh_last = None
    for t in range(start, T):
        if (t - start) % refit_m5 == 0:
            th, _, ok = rgarch_fit_forecast(ret[:t], logx[:t], th)
            if not ok:
                nonconv += 1
            om, be, ga = th[0], th[1], th[2]
            logh = lfilter([ga], [1.0, -be], np.concatenate(
                [[(om + ga * logx[:t].mean()) / max(1 - be, 1e-3)],
                 logx[:t - 1]]))
            lh_last = om + logh[-1]
        # between refits lh_last already holds log h_{t-1} from the
        # previous iteration's one-step update
        xi, ph, t1, t2, lsu = th[3], th[4], th[5], th[6], th[7]
        lh_next = om + be * lh_last + ga * logx[t - 1]
        mgf = np.exp(-t2) / np.sqrt(max(1 - 2 * t2, 1e-6)) \
            * np.exp(t1 ** 2 / (2 * max(1 - 2 * t2, 1e-6)))
        F["M5_RGARCH"][t] = float(np.exp(xi + ph * lh_next
                                         + 0.5 * np.exp(lsu)) * mgf)
        lh_last = lh_next          # log h_t for the next step's recursion
    return F, start, nonconv


def qlike(F, rv):
    x = rv / F
    return x - np.log(x) - 1.0


def mcs(losses, rng):
    """Hansen-Lunde-Nason MCS, range statistic, moving-block bootstrap."""
    T, m = losses.shape
    b = int(np.ceil(T ** (1 / 3)))
    nblk = int(np.ceil(T / b))
    starts = rng.integers(0, T - b + 1, size=(BOOT_N, nblk))
    csum = np.vstack([np.zeros(m), np.cumsum(losses, axis=0)])
    blocksum = csum[b:] - csum[:-b]              # (T-b+1, m)
    boot_means = blocksum[starts].sum(axis=1) / (nblk * b)   # (BOOT_N, m)
    means = losses.mean(axis=0)
    included = list(range(m))
    pvals = {}
    p_running = 0.0
    while len(included) > 1:
        idx = np.array(included)
        mu = means[idx]
        bm = boot_means[:, idx] - mu[None, :]
        dbar = mu[:, None] - mu[None, :]
        bd = bm[:, :, None] - bm[:, None, :]
        vd = np.maximum(bd.var(axis=0), 1e-30)
        tstat = np.abs(dbar) / np.sqrt(vd)
        TR = tstat.max()
        bt = np.abs(bd) / np.sqrt(vd)[None, :, :]
        TR_boot = bt.reshape(BOOT_N, -1).max(axis=1)
        p = float((TR_boot >= TR).mean())
        p_running = max(p_running, p)
        # eliminate the model with the worst standardized average loss
        avg_t = (dbar / np.sqrt(vd)).sum(axis=1)
        worst = included[int(np.argmax(avg_t))]
        pvals[worst] = p_running
        included.remove(worst)
    pvals[included[0]] = 1.0
    return pvals


def main():
    t0 = time.time()
    lamC = pd.read_csv(os.path.join(RES, "s05_partc_wide.csv"))
    rows_metrics, rows_mcs = [], []
    rngm = np.random.Generator(np.random.PCG64(BOOT_SEED))
    for geom in ["GLOBEX", "RTH"]:
        for root in ["ES", "NQ"]:
            for btag in ["B0", "B1"]:
                z = np.load(os.path.join(RES,
                                         f"panel_{root}_{geom}_{btag}.npz"))
                grid = z["logpx"].astype(np.float64)
                nfull = N_GRID[geom]
                for horizon, wlen in [("1day", None), ("1h", 60),
                                      ("30min", 30)]:
                    S = build_series(grid, wlen)
                    D = S["nw"]
                    warm = 500 if horizon == "1day" else max(500,
                                                             22 * D + 100)
                    refit = 1 if horizon == "1day" else D
                    F, start, nonconv = forecasts(S, D, warm, refit,
                                                  horizon == "1day")
                    rv = S["rv"]
                    ev = slice(max(start, warm), len(rv))
                    idx_ok = np.ones(len(rv), bool)
                    for m in MODELS:
                        idx_ok &= np.isfinite(F[m])
                    idx_ok[:ev.start] = False
                    rvv = rv[idx_ok]
                    Fm = {m: F[m][idx_ok] for m in MODELS}
                    L = np.column_stack([qlike(Fm[m], rvv) for m in MODELS])
                    lamrow = lamC[(lamC.root == root) & (lamC.geom == geom)
                                  & (lamC.btag == btag)
                                  & (lamC.horizon == horizon)
                                  & (lamC.year == 0) & (lamC.tercile == 0)]
                    lamrow = lamrow[lamrow.M == lamrow.M.max()]
                    lam_hat = float(lamrow["E4"].iloc[0])
                    schemes = {"S-A": np.ones(len(rvv), bool)}
                    for q in QS:
                        schemes[f"S-B_q{q:.2f}"] = rvv > np.quantile(rvv, q)
                        fc = Fm["M2_HAR"]
                        schemes[f"S-C_q{q:.2f}"] = fc > np.quantile(fc, q)
                    for sname, smask in schemes.items():
                        Ls = L[smask]
                        pv = mcs(Ls, rngm)
                        surv75 = [MODELS[i] for i, p in pv.items() if p > .25]
                        surv90 = [MODELS[i] for i, p in pv.items() if p > .10]
                        rows_mcs.append(dict(
                            root=root, geom=geom, btag=btag, horizon=horizon,
                            scheme=sname, n_obs=int(smask.sum()),
                            pvals=json.dumps({MODELS[i]: round(p, 4)
                                              for i, p in pv.items()}),
                            mcs75="|".join(sorted(surv75)),
                            mcs90="|".join(sorted(surv90))))
                        lrv = np.log(rvv[smask])
                        for m in MODELS:
                            lf = np.log(Fm[m][smask])
                            ic = float(np.corrcoef(lf, lrv)[0, 1])
                            icس = float(spearmanr(lf, lrv).statistic)
                            r2 = float(1 - ((lrv - lf) ** 2).sum()
                                       / ((lrv - lrv.mean()) ** 2).sum())
                            w = 63
                            ics = [np.corrcoef(lf[i:i + w],
                                               lrv[i:i + w])[0, 1]
                                   for i in range(0, len(lrv) - w, w)]
                            ics = [x for x in ics if np.isfinite(x)]
                            ir = float(np.mean(ics) / np.std(ics)) \
                                if len(ics) > 2 and np.std(ics) > 0 else np.nan
                            dlF = np.sign(np.diff(lf))
                            dlR = np.sign(np.diff(lrv))
                            hit = float((dlF == dlR).mean())
                            rows_metrics.append(dict(
                                root=root, geom=geom, btag=btag,
                                horizon=horizon, scheme=sname, model=m,
                                n=int(smask.sum()), lam_hat=lam_hat,
                                ic_pearson_log=ic,
                                ic_corrected=ic / np.sqrt(lam_hat),
                                ic_spearman=icس,
                                r2_oos=r2, r2_corrected=r2 / lam_hat,
                                ic_ir=ir, hit_rate=hit,
                                qlike_mean=float(qlike(Fm[m][smask],
                                                       rvv[smask]).mean()),
                                m5_nonconv=nonconv))
                    print(f"{root} {geom} {btag} {horizon}: done "
                          f"({time.time()-t0:.0f}s)", flush=True)
    pd.DataFrame(rows_metrics).to_csv(
        os.path.join(RES, "s05_metrics.csv"), index=False)
    pd.DataFrame(rows_mcs).to_csv(
        os.path.join(RES, "s05_mcs.csv"), index=False)
    print(f"Parts D+E done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
