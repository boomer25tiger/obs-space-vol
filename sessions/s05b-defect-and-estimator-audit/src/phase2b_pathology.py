"""S05B Phase 2 analysis: forecast pathology on the regenerated forecasts."""

import json
import os
import sys
import time

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
RES = os.path.join(BASE, "results")
CACHE = os.path.join(RES, "cache")
sys.path.insert(0, os.path.join(ROOT, "sessions", "s05-reliability-mcs",
                                "src"))
import partde as pd5                                     # noqa: E402

MODELS = pd5.MODELS
CELLS = [(r, g, b, h) for g in ["GLOBEX", "RTH"] for r in ["ES", "NQ"]
         for b in ["B0", "B1"] for h in ["1day", "1h", "30min"]]


def har_refit(rv, bv, rq, D, t, refit):
    """Reproduce partde's OLS coefficients in force at step t."""
    T = len(rv)
    x1, x5, x22 = pd5.har_X(rv, D)
    J = np.maximum(rv - bv, 0.0)
    sq = np.sqrt(np.maximum(rq, 0.0))
    X = {"M2_HAR": np.column_stack([np.ones(T), x1, x5, x22]),
         "M3_HARJ": np.column_stack([np.ones(T), x1, x5, x22, J]),
         "M4_HARQ": np.column_stack([np.ones(T), x1, x5, x22, sq * x1])}
    t_fit = t - (t % refit) if refit > 1 else t
    out = {}
    for m, Xm in X.items():
        Xt, yt = Xm[22 * D:t_fit - 1], rv[22 * D + 1:t_fit]
        ok = np.isfinite(Xt).all(axis=1)
        if ok.sum() < Xm.shape[1] + 2:
            out[m] = (None, None, t_fit)
            continue
        b, *_ = np.linalg.lstsq(Xt[ok], yt[ok], rcond=None)
        out[m] = (b, Xm[t - 1], t_fit)
    return out


def main():
    t0 = time.time()
    summ, offend, coefs = [], [], []
    for root, geom, btag, hname in CELLS:
        fn = os.path.join(CACHE, f"fc_{root}_{geom}_{btag}_{hname}.npz")
        if not os.path.exists(fn):
            continue
        z = np.load(fn)
        rv, ok = z["rv"], z["ok"]
        bv, rq, D = z["bv"], z["rq"], int(z["D"])
        refit = int(z["refit"])
        wdates = np.array(z["wdates"], dtype="U10")
        mean_rv = float(rv[ok].mean())
        cell = f"{root}/{geom}/{btag}/{hname}"
        for m in MODELS:
            F = z[f"F_{m}"]
            Fe = F[ok]
            summ.append(dict(
                cell=cell, root=root, geom=geom, btag=btag, horizon=hname,
                model=m, n_eval=int(ok.sum()),
                n_nonpositive=int((Fe <= 0).sum()),
                n_below_1e12=int((Fe < 1e-12).sum()),
                n_below_1e6=int((Fe < 1e-6).sum()),
                n_above_100x_mean_rv=int((Fe > 100 * mean_rv).sum()),
                min_forecast=float(Fe.min()),
                p001_forecast=float(np.percentile(Fe, 0.1)),
                max_forecast=float(Fe.max()),
                in_sample_mean_rv=mean_rv))
            if m not in ("M4_HARQ", "M3_HARJ"):
                continue
            ql = pd5.qlike(Fe, rv[ok])
            tot = float(ql[np.isfinite(ql)].sum())
            bad = (Fe <= 0) | (Fe < 1e-12) | (Fe > 100 * mean_rv) \
                | ~np.isfinite(ql)
            idx_all = np.where(ok)[0]
            order = np.argsort(-np.where(np.isfinite(ql), ql, np.inf))
            for j in np.where(bad)[0]:
                offend.append(dict(
                    cell=cell, model=m, window_index=int(idx_all[j]),
                    trade_date=str(wdates[idx_all[j]]),
                    forecast=float(Fe[j]), realized=float(rv[ok][j]),
                    qlike=float(ql[j]),
                    share_of_cell_qlike=float(ql[j] / tot) if tot else np.nan,
                    reason=("nonpositive" if Fe[j] <= 0 else
                            "below_1e-12" if Fe[j] < 1e-12 else
                            "above_100x_mean_rv" if Fe[j] > 100 * mean_rv
                            else "nonfinite_qlike")))
            if bad.any():
                w1 = float(ql[order[0]] / tot) if tot else np.nan
                w5 = float(ql[order[:5]].sum() / tot) if tot else np.nan
                summ[-1]["worst1_share_of_qlike"] = w1
                summ[-1]["worst5_share_of_qlike"] = w5
                for rank, j in enumerate(order[:3]):
                    ti = int(idx_all[j])
                    fits = har_refit(rv, bv, rq, D, ti, refit)
                    b, xrow, tfit = fits.get(m, (None, None, None))
                    if b is None:
                        continue
                    comp = (b * xrow).tolist()
                    coefs.append(dict(
                        cell=cell, model=m, rank=rank + 1,
                        window_index=ti, trade_date=str(wdates[ti]),
                        coef=json.dumps([float(x) for x in b]),
                        regressors=json.dumps([float(x) for x in xrow]),
                        components=json.dumps([float(x) for x in comp]),
                        linear_fit=float(np.dot(b, xrow)),
                        fit_negative_by_construction=bool(
                            np.dot(b, xrow) < 0),
                        forecast_stored=float(F[ti]),
                        realized=float(rv[ti]),
                        coef_fit_at_step=int(tfit)))
    pd.DataFrame(summ).to_csv(os.path.join(RES, "phase2_forecast_stats.csv"),
                              index=False)
    pd.DataFrame(offend).to_csv(
        os.path.join(RES, "phase2_offending_observations.csv"), index=False)
    pd.DataFrame(coefs).to_csv(
        os.path.join(RES, "phase2_harq_coefficients.csv"), index=False)
    S = pd.DataFrame(summ)
    print(f"cells x models: {len(S)}; offending obs: {len(offend)}; "
          f"coef rows: {len(coefs)}; {time.time()-t0:.1f}s")
    bad = S[(S.n_nonpositive > 0) | (S.n_above_100x_mean_rv > 0)
            | (S.n_below_1e12 > 0)]
    print(bad[["cell", "model", "n_nonpositive", "n_below_1e12",
               "n_above_100x_mean_rv", "min_forecast",
               "max_forecast"]].to_string(index=False))


if __name__ == "__main__":
    main()
