"""S05B Phase 4 addendum: finest attainable grid point + noise references.

Finding handled here: for the 1day horizons the nominal finest M equals the
session minute count (390 RTH, 1380 GLOBEX), but the panel supplies only
L = session-1 one-minute returns (the session's first close has no
predecessor inside the session). M = 390 / 1380 is therefore NOT attainable
from the panel. S05 reached it by appending a duplicate final price point
(partc.py: `if p.shape[1] == M: p = concat([p, grid[:, -1:]])`), which
injects one identically-zero return and leaves effective M = L. S05B adds
M = L as the finest attainable grid point and records the nominal point as
unattainable rather than fabricating it.

Also caches, once per session-day (not per grid), two noise-robust
integrated-variance references from the finest data:
  - realized kernel, flat-top Parzen, bandwidth by the S05 pre-registered
    rule H = 0.97 * xi^(4/5) * n^(3/5) with xi^2 = omega^2 / IV
    (DECISIONS item 16), omega^2 taken from the S03 N1 estimates;
  - two-scale realized variance (Zhang-Mykland-Ait-Sahalia 2005) with the
    authors' K = c* n^(2/3), c* = (12 omega^4 / IQ)^(1/3).
"""

import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy.special import polygamma

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
RES = os.path.join(BASE, "results")
CACHE = os.path.join(RES, "cache")
S03_RES = os.path.join(ROOT, "sessions", "s03-data-noise", "results")
sys.path.insert(0, os.path.join(ROOT, "sessions", "s02-mechanism-expansion",
                                "src"))
sys.path.insert(0, os.path.join(ROOT, "sessions", "s05-reliability-mcs",
                                "src"))
import proxies_robust as px                              # noqa: E402
from parta import quart_suite                            # noqa: E402
from phase34 import windows, subbars, HORIZ, CELLS       # noqa: E402

L_OF = {("RTH", "1day"): 389, ("GLOBEX", "1day"): 1379}
NOMINAL = {("RTH", "1day"): 390, ("GLOBEX", "1day"): 1380}


def main():
    t0 = time.time()
    noise = pd.read_csv(os.path.join(S03_RES, "s03_noise.csv"))
    idx = pd.read_csv(os.path.join(RES, "phase4_grid_index.csv"))
    add_rows = []
    ref_meta = []
    for root, geom, btag in CELLS:
        z = np.load(os.path.join(CACHE, f"ret1m_{root}_{geom}_{btag}.npz"))
        r1 = z["r1"].astype(np.float64)
        dates = np.array(z["dates"], dtype="U10")
        years = pd.to_datetime(dates).year.values
        key = (geom, "1day")
        if key not in L_OF:
            continue
        L = L_OF[key]
        M = L                                   # finest attainable
        rw, nw = windows(r1, None)
        sb, sizes = subbars(rw, M)
        rv = (sb ** 2).sum(axis=1)
        q = quart_suite(sb, M)
        trq, trv = q["TRQ3_TRV3"]
        rq = q["RQ_RV"][0]
        logrv = np.log(np.maximum(rv, 1e-300))
        eff = np.full(len(rv), M, dtype=np.int16)
        first_share = sb[:, 0] ** 2 / np.maximum(rv, 1e-300)
        last_share = sb[:, -1] ** 2 / np.maximum(rv, 1e-300)
        np.savez_compressed(
            os.path.join(CACHE,
                         f"grid_{root}_{geom}_{btag}_1day_M{M}.npz"),
            rv=rv, trv=trv, rq=rq, trq=trq, logrv=logrv, eff=eff,
            first_share=first_share.astype(np.float32),
            last_share=last_share.astype(np.float32), years=years)
        add_rows.append(dict(
            root=root, geom=geom, btag=btag, horizon="1day", M=int(M),
            session_minutes=NOMINAL[key], L_returns_per_window=int(L),
            M_divides_session=bool(NOMINAL[key] % M == 0),
            M_divides_L=True, subbar_size_min=1, subbar_size_max=1,
            n_stub_subbars=0, n_windows=int(len(rv)),
            var_log_rv=float(logrv.var()),
            n_nonfinite_log=int((rv <= 0).sum()),
            share_full_M=1.0, share_below_0p9M=0.0, mean_eff_M=float(M),
            mean_first_share=float(first_share.mean()),
            mean_last_share=float(last_share.mean()),
            trigamma_M_over_2=float(polygamma(1, M / 2.0)),
            two_over_M=2.0 / M,
            mean_trv_over_rv=float((trv / np.maximum(rv, 1e-300)).mean()),
            note="finest attainable (= L); nominal M="
                 f"{NOMINAL[key]} unattainable from the panel"))

        # ---- noise-robust references, once per session-day
        nr = noise[(noise.root == root) & (noise.geom == geom)
                   & (noise.group == "all")]
        omega2 = float(nr["omega2_N1"].iloc[0])
        iv_hat = float(nr["intercept_EIV"].iloc[0])
        n = L
        xi2 = omega2 / max(iv_hat, 1e-300)
        H = int(np.clip(round(0.97 * xi2 ** (2.0 / 5.0) * n ** (3.0 / 5.0)),
                        1, max(1, n - 2)))
        kern = px.p3_kernel_flattop(sb, H)
        iq_hat = float(np.mean(rq))
        K = px.tsrv_K(n, omega2, iq_hat)
        p = np.concatenate([np.zeros((sb.shape[0], 1)),
                            np.cumsum(sb, axis=1)], axis=1)
        tsrv = px.p2_tsrv(p, K)
        np.savez_compressed(
            os.path.join(CACHE, f"ref_{root}_{geom}_{btag}.npz"),
            kernel=kern, tsrv=tsrv, years=years, dates=dates)
        ref_meta.append(dict(
            root=root, geom=geom, btag=btag, n=int(n),
            omega2_N1=omega2, iv_hat=iv_hat, xi2=xi2,
            kernel_bandwidth_H=int(H), tsrv_K=int(K),
            rule_kernel="H = 0.97 * xi^(4/5) * n^(3/5), xi^2 = omega^2/IV",
            rule_tsrv="K = c* n^(2/3), c* = (12 omega^4 / IQ)^(1/3) (ZMA)",
            mean_kernel=float(np.mean(kern)), mean_tsrv=float(np.mean(tsrv)),
            mean_rv=float(np.mean(rv)),
            n_kernel_nonpos=int((kern <= 0).sum()),
            n_tsrv_nonpos=int((tsrv <= 0).sum())))

    pd.concat([idx, pd.DataFrame(add_rows)], ignore_index=True).to_csv(
        os.path.join(RES, "phase4_grid_index.csv"), index=False)
    pd.DataFrame(ref_meta).to_csv(
        os.path.join(RES, "phase4_noise_references.csv"), index=False)
    unattainable = [dict(geom=g, horizon=h, nominal_M=NOMINAL[(g, h)],
                         L=L_OF[(g, h)],
                         reason="panel supplies L = session_minutes - 1 "
                                "returns; S05 reached nominal M by "
                                "duplicating the final price point, "
                                "injecting one zero return")
                    for (g, h) in NOMINAL]
    with open(os.path.join(RES, "phase4_unattainable_M.json"), "w") as fh:
        json.dump(unattainable, fh, indent=1)
    print(json.dumps(unattainable, indent=1))
    print(pd.DataFrame(ref_meta)[["root", "geom", "btag",
                                  "kernel_bandwidth_H", "tsrv_K",
                                  "mean_kernel", "mean_tsrv",
                                  "mean_rv"]].to_string(index=False))
    print(f"addendum done {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
