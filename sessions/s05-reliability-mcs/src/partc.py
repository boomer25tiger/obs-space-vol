"""S05 Part C: reliability surface.

lambda = Var(log IV)/Var(log RV) estimated by E4 (selected Part A variant
TRQ3_TRV3), E1 arms a/d at L1-5/L1-10 (S02 implementation imported
unmodified), and E2 contiguous halves. Surface over horizon (30m, 1h,
1day), M, root, geometry, year (2016-23 + pooled), volatility tercile
(1-3 + all), boundary treatment (B0/B1).

Documented implementation choices (fixed before results):
- Sub-daily horizons use the 1-minute grid within each window (M = window
  length); the 1h RTH horizon uses six 60-minute windows (09:30-15:30),
  dropping the final half hour; GLOBEX uses 46/23 windows.
- E1/E2 operate on log plain RV; E4 operates on the selected variant's
  own proxy (log truncated RV at 3 local sd), per the pre-registration.
- Tercile and year cells concatenate non-contiguous segments; E1's
  autocovariances then span joins. Reported as-is.
- Terciles: session-level daily RV at the coarsest M per (root, geom),
  tercile of the session inherited by its windows.
"""

import json
import os
import sys
import time

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, os.path.join(ROOT, "sessions", "s02-mechanism-expansion",
                                "src"))
import estimators2 as e2mod                   # noqa: E402
sys.path.insert(0, ".")
from parta import quart_suite                 # noqa: E402

RES = os.path.join(BASE, "results")
M_SETS = {"RTH": [13, 26, 78, 195, 390], "GLOBEX": [23, 46, 138, 345, 1380]}
N_GRID = {"RTH": 390, "GLOBEX": 1380}
HORIZONS = {"RTH": {"30min": 30, "1h": 60}, "GLOBEX": {"30min": 30, "1h": 60}}
CHOSEN = json.load(open(os.path.join(RES,
                                     "s05_variant_selection.json")))["chosen"]


def lam_estimates(logrv, logrv_h1, logrv_h2, P, Q, M):
    out = {}
    if len(logrv) >= 30:
        grid = e2mod.e1_reduced(logrv)
        for (a, ls), v in grid.items():
            out[f"E1_{a}_{ls}"] = float(v)
        out["E2"] = float(e2mod.e2(logrv, logrv_h1, logrv_h2))
        out["E4"] = float(e2mod.e4(P, Q, np.log(np.maximum(P, 1e-300)), M))
    return out


def main():
    t0 = time.time()
    rows = []
    for geom in ["GLOBEX", "RTH"]:
        nfull = N_GRID[geom]
        for root in ["ES", "NQ"]:
            for btag in ["B0", "B1"]:
                z = np.load(os.path.join(RES,
                                         f"panel_{root}_{geom}_{btag}.npz"))
                grid = z["logpx"].astype(np.float64)
                dates = pd.to_datetime(z["dates"])
                years = dates.year.values
                # terciles from coarsest-M daily RV
                Mc = min(M_SETS[geom])
                stride = nfull // Mc
                pc = grid[:, ::stride]
                if pc.shape[1] == Mc:
                    pc = np.concatenate([pc, grid[:, -1:]], axis=1)
                rvc = (np.diff(pc, axis=1) ** 2).sum(axis=1)
                terc = np.searchsorted(np.quantile(rvc, [1 / 3, 2 / 3]), rvc)

                def cells(nwin_per_day, series_pack, M, horizon):
                    logrv, h1, h2, P, Q = series_pack
                    wyears = np.repeat(years, nwin_per_day)
                    wterc = np.repeat(terc, nwin_per_day)
                    for y in list(range(2016, 2024)) + [0]:
                        for tc in [0, 1, 2, -1]:
                            m = np.ones(len(logrv), bool)
                            if y:
                                m &= wyears == y
                            if tc >= 0:
                                m &= wterc == tc
                            if m.sum() < 30:
                                continue
                            est = lam_estimates(logrv[m], h1[m], h2[m],
                                                P[m], Q[m], M)
                            for k, v in est.items():
                                rows.append(dict(
                                    root=root, geom=geom, btag=btag,
                                    horizon=horizon, M=M, year=y,
                                    tercile=tc + 1 if tc >= 0 else 0,
                                    n=int(m.sum()), estimator=k, lam=v))

                # ---- daily horizon at every M
                for M in M_SETS[geom]:
                    stride = nfull // M
                    p = grid[:, ::stride]
                    if p.shape[1] == M:
                        p = np.concatenate([p, grid[:, -1:]], axis=1)
                    r = np.diff(p, axis=1)
                    rv = (r ** 2).sum(axis=1)
                    h = M // 2
                    rv1 = (r[:, :h] ** 2).sum(axis=1)
                    rv2 = (r[:, h:] ** 2).sum(axis=1)
                    q = quart_suite(r, M)
                    Q, P = q[CHOSEN]
                    pack = (np.log(np.maximum(rv, 1e-300)),
                            np.log(np.maximum(rv1, 1e-300)),
                            np.log(np.maximum(rv2, 1e-300)), P, Q)
                    cells(1, pack, M, "1day")

                # ---- sub-daily horizons at the 1-minute grid
                for hname, wlen in HORIZONS[geom].items():
                    # the panel has n price points -> n-1 one-minute returns
                    nw = (nfull - 1) // wlen
                    used = nw * wlen
                    r1 = np.diff(grid, axis=1)[:, :used]
                    rw = r1.reshape(len(grid), nw, wlen)
                    S = len(grid) * nw
                    rws = rw.reshape(S, wlen)
                    rv = (rws ** 2).sum(axis=1)
                    hh = wlen // 2
                    rv1 = (rws[:, :hh] ** 2).sum(axis=1)
                    rv2 = (rws[:, hh:] ** 2).sum(axis=1)
                    q = quart_suite(rws, wlen)
                    Q, P = q[CHOSEN]
                    pack = (np.log(np.maximum(rv, 1e-300)),
                            np.log(np.maximum(rv1, 1e-300)),
                            np.log(np.maximum(rv2, 1e-300)), P, Q)
                    cells(nw, pack, wlen, hname)

    C = pd.DataFrame(rows)
    C.to_csv(os.path.join(RES, "s05_partc.csv"), index=False)
    piv = C.pivot_table(index=["root", "geom", "btag", "horizon", "M",
                               "year", "tercile", "n"],
                        columns="estimator", values="lam").reset_index()
    est_cols = [c for c in piv.columns if str(c).startswith("E")]
    piv["disagreement"] = piv[est_cols].max(axis=1) - piv[est_cols].min(axis=1)
    piv.to_csv(os.path.join(RES, "s05_partc_wide.csv"), index=False)
    print(f"Part C: {len(C)} estimates, {len(piv)} cells, "
          f"{time.time()-t0:.0f}s")
    pooled = piv[(piv.year == 0) & (piv.tercile == 0) & (piv.btag == "B0")
                 & (piv.horizon == "1day")]
    print(pooled[["root", "geom", "M"] + est_cols].to_string(index=False))


if __name__ == "__main__":
    main()
