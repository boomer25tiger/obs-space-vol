"""S05B Phases 5, 6, 7: grid invariance, noise arithmetic, jump contribution.

Reads the Phase 3/4 cache only. trigamma(M/2) is used wherever a
theoretical sampling variance of log RV is required; 2/M is reported
alongside for comparison but never used as the reference.

Estimator definitions follow S05 Part C exactly so the comparison is
like-for-like: E1 (arms a_exp / d_model at L1-5 / L1-10) and E2 operate on
log plain RV, E4 uses (2/M) Q / P^2 with the Part A selected variant
(TRQ3_TRV3). That asymmetry is S05's, and is recorded rather than altered.
Phase 7 additionally runs every estimator on TRV3.
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
S05_RES = os.path.join(ROOT, "sessions", "s05-reliability-mcs", "results")
sys.path.insert(0, os.path.join(ROOT, "sessions", "s02-mechanism-expansion",
                                "src"))
sys.path.insert(0, os.path.join(ROOT, "sessions", "s05-reliability-mcs",
                                "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import estimators2 as e2mod                              # noqa: E402
from parta import quart_suite                            # noqa: E402
from phase34 import windows, subbars, HORIZ, CELLS, GRID  # noqa: E402

EST = ["E1_a_exp_L1-5", "E1_a_exp_L1-10", "E1_d_model_L1-5",
       "E1_d_model_L1-10", "E2", "E4", "E4_asS05"]
S05_GRID = {("RTH", "1day"): [13, 26, 78, 195, 389],
            ("GLOBEX", "1day"): [23, 46, 138, 345, 1379],
            ("RTH", "1h"): [60], ("RTH", "30min"): [30]}
EXTRA_M = {("RTH", "1day"): 389, ("GLOBEX", "1day"): 1379}
TRIM = 5          # minutes trimmed from each end for the boundary fit


def trigamma(M):
    return float(polygamma(1, M / 2.0))


def lam_all(sb, M, proxy="RV"):
    """Six Part C estimators at one grid point."""
    q = quart_suite(sb, M)
    rq, rv = q["RQ_RV"]
    trq, trv = q["TRQ3_TRV3"]
    P = rv if proxy == "RV" else trv
    Q = rq if proxy == "RV" else trq
    logp = np.log(np.maximum(P, 1e-300))
    h = M // 2
    p1 = (sb[:, :h] ** 2).sum(axis=1)
    p2 = (sb[:, h:] ** 2).sum(axis=1)
    out = {}
    g = e2mod.e1_reduced(logp)
    for (a, ls), v in g.items():
        out[f"E1_{a}_{ls}"] = float(v)
    out["E2"] = float(e2mod.e2(logp, np.log(np.maximum(p1, 1e-300)),
                               np.log(np.maximum(p2, 1e-300))))
    # E4 matched to the proxy under test (RV -> RQ/RV, TRV3 -> TRQ3/TRV3)
    QQ, PP = (rq, rv) if proxy == "RV" else (trq, trv)
    out["E4"] = float(e2mod.e4(PP, QQ, np.log(np.maximum(PP, 1e-300)), M))
    # E4 exactly as S05 Part C ran it: ALWAYS the Part A selected variant
    # (TRQ3/TRV3), even when E1/E2 were fed plain RV. That asymmetry is
    # S05's; it is reported, not altered.
    out["E4_asS05"] = float(e2mod.e4(trv, trq,
                                     np.log(np.maximum(trv, 1e-300)), M))
    return out, float(logp.var()), float(np.mean(trv / np.maximum(rv, 1e-300)))


def elasticity(Ms, lams):
    """Fit log((1-lam)/lam) = a + b log M. Returns b, R2, n_used, n_drop."""
    Ms = np.asarray(Ms, float)
    lams = np.asarray(lams, float)
    ok = np.isfinite(lams) & (lams > 0) & (lams < 1)
    n_drop = int((~ok).sum())
    if ok.sum() < 3:
        return np.nan, np.nan, int(ok.sum()), n_drop
    x = np.log(Ms[ok])
    y = np.log((1 - lams[ok]) / lams[ok])
    b, a = np.polyfit(x, y, 1)
    pred = a + b * x
    ss = 1 - ((y - pred) ** 2).sum() / max(((y - y.mean()) ** 2).sum(), 1e-300)
    return float(b), float(ss), int(ok.sum()), n_drop


def main():
    t0 = time.time()
    timers = {}
    idx = pd.read_csv(os.path.join(RES, "phase4_grid_index.csv"))

    # ---------------- Phase 5 + 7 core sweep
    t = time.time()
    rows = []
    for root, geom, btag in CELLS:
        z = np.load(os.path.join(CACHE, f"ret1m_{root}_{geom}_{btag}.npz"))
        r1 = z["r1"].astype(np.float64)
        for (g2, hname), Ms in GRID.items():
            if g2 != geom:
                continue
            Ms = list(Ms)
            if (geom, hname) in EXTRA_M:
                Ms = [m for m in Ms if m < EXTRA_M[(geom, hname)]] \
                    + [EXTRA_M[(geom, hname)]]
            rw, nw = windows(r1, HORIZ[hname])
            L = rw.shape[1]
            rw_tr = rw[:, TRIM:L - TRIM] if L > 2 * TRIM + 5 else None
            for M in Ms:
                if M > L:
                    continue
                sb, sizes = subbars(rw, M)
                for proxy in ["RV", "TRV3"]:
                    lam, varlog, trv_ratio = lam_all(sb, M, proxy)
                    for e in EST:
                        rows.append(dict(
                            root=root, geom=geom, btag=btag,
                            horizon=hname, M=M, proxy=proxy, estimator=e,
                            lam=lam[e], var_log_proxy=varlog,
                            n_windows=int(sb.shape[0]),
                            trv_over_rv=trv_ratio,
                            trigamma=trigamma(M), two_over_M=2.0 / M,
                            trimmed=False))
                if rw_tr is not None and M <= rw_tr.shape[1]:
                    sbt, _ = subbars(rw_tr, M)
                    lam, varlog, _ = lam_all(sbt, M, "RV")
                    for e in EST:
                        rows.append(dict(
                            root=root, geom=geom, btag=btag,
                            horizon=hname, M=M, proxy="RV", estimator=e,
                            lam=lam[e], var_log_proxy=varlog,
                            n_windows=int(sbt.shape[0]),
                            trv_over_rv=np.nan,
                            trigamma=trigamma(M), two_over_M=2.0 / M,
                            trimmed=True))
    S = pd.DataFrame(rows)
    S.to_csv(os.path.join(RES, "phase5_lambda_grid.csv"), index=False)
    timers["p5_sweep"] = round(time.time() - t, 1)

    # ---------------- invariance products and rankings
    t = time.time()
    inv, ela = [], []
    for (root, geom, btag, hname, proxy, trimmed, e), g in S.groupby(
            ["root", "geom", "btag", "horizon", "proxy", "trimmed",
             "estimator"]):
        g = g.sort_values("M")
        prod = (g["lam"] * g["var_log_proxy"]).values
        fin = np.isfinite(prod) & (g["lam"].values > 0) & \
            (g["lam"].values < 1)
        b, r2, nused, ndrop = elasticity(g["M"].values, g["lam"].values)
        sub = g[g.M.isin(S05_GRID.get((geom, hname), []))]
        b5, r25, nu5, nd5 = elasticity(sub["M"].values, sub["lam"].values)
        inv.append(dict(
            root=root, geom=geom, btag=btag, horizon=hname, proxy=proxy,
            trimmed=bool(trimmed), estimator=e, n_grid=int(len(g)),
            n_valid=int(fin.sum()),
            product_min=float(prod[fin].min()) if fin.any() else np.nan,
            product_max=float(prod[fin].max()) if fin.any() else np.nan,
            ratio_max_min=float(prod[fin].max() / prod[fin].min())
            if fin.any() and prod[fin].min() > 0 else np.nan,
            cv=float(np.std(prod[fin]) / np.mean(prod[fin]))
            if fin.any() and np.mean(prod[fin]) != 0 else np.nan,
            elasticity=b, elasticity_r2=r2, n_used=nused, n_dropped=ndrop,
            elasticity_s05grid=b5, elasticity_s05grid_r2=r25,
            n_used_s05grid=nu5))
    INV = pd.DataFrame(inv)
    INV.to_csv(os.path.join(RES, "phase5_invariance.csv"), index=False)

    # ranking by grid invariance (RV, untrimmed)
    base = INV[(INV.proxy == "RV") & (~INV.trimmed)]
    ranks = []
    for (root, geom, btag, hname), g in base.groupby(
            ["root", "geom", "btag", "horizon"]):
        g = g.sort_values("ratio_max_min")
        for i, (_, r) in enumerate(g.iterrows()):
            ranks.append(dict(cell=f"{root}/{geom}/{btag}/{hname}",
                              rank=i + 1, estimator=r.estimator,
                              ratio_max_min=r.ratio_max_min, cv=r.cv,
                              elasticity=r.elasticity))
    RK = pd.DataFrame(ranks)
    RK.to_csv(os.path.join(RES, "phase5_ranking.csv"), index=False)
    piv = RK.pivot_table(index="estimator", columns="cell", values="rank")
    consistent = bool((piv.nunique(axis=1) == 1).all())
    timers["p5_invariance"] = round(time.time() - t, 1)

    # ---------------- B0 vs B1 elasticity difference
    d = base.pivot_table(index=["root", "geom", "horizon", "estimator"],
                         columns="btag", values="elasticity").reset_index()
    if "B0" in d and "B1" in d:
        d["abs_diff"] = (d["B1"] - d["B0"]).abs()
        d["pct_diff"] = 100 * (d["B1"] - d["B0"]).abs() / d["B0"].abs()
    d.to_csv(os.path.join(RES, "phase5_b0_b1.csv"), index=False)

    # ---------------- Part A measured R at every M and variant
    A = pd.read_csv(os.path.join(S05_RES, "s05_parta.csv"))
    A = A[A.year == 0].copy()
    A["trigamma"] = [trigamma(m) for m in A.M]
    A["median_over_trigamma"] = A["median"] / A["trigamma"]
    A[["root", "geom", "btag", "M", "variant", "median", "ref_2overM",
       "med_over_ref", "trigamma", "median_over_trigamma", "p95",
       "share_gt10x_med"]].to_csv(
        os.path.join(RES, "phase5_partA_R_vs_trigamma.csv"), index=False)

    # ---------------- Phase 6a: noise arithmetic
    t = time.time()
    N = pd.read_csv(os.path.join(S03_RES, "s03_noise.csv"))
    n6 = dict(
        n_cells=int(len(N)),
        n_negative_omega2_N1=int((N.omega2_N1 < 0).sum()),
        n_negative_omega2_N2=int((N.omega2_N2 < 0).sum()),
        n_negative_intercept=int((N.intercept_EIV < 0).sum()),
        r2_min=float(N.signature_R2.min()), r2_max=float(N.signature_R2.max()),
        r2_median=float(N.signature_R2.median()),
        n_r2_below_0p5=int((N.signature_R2 < 0.5).sum()),
        omega2_N1_min=float(N.omega2_N1.min()),
        omega2_N1_max=float(N.omega2_N1.max()),
        omega2_N1_median=float(N.omega2_N1.median()))
    N.to_csv(os.path.join(RES, "phase6_s03_noise_full.csv"), index=False)

    bias_rows = []
    for root, geom, btag in CELLS:
        nr = N[(N.root == root) & (N.geom == geom)]
        om_all = nr["omega2_N1"].values
        om = float(nr[nr.group == "all"]["omega2_N1"].iloc[0])
        iv = float(nr[nr.group == "all"]["intercept_EIV"].iloc[0])
        for (g2, hname), Ms in GRID.items():
            if g2 != geom or hname != "1day":
                continue
            Ms = [m for m in Ms if m < EXTRA_M[(geom, hname)]] \
                + [EXTRA_M[(geom, hname)]]
            for M in Ms:
                b = 2.0 * M * om / iv
                brange = [float(2.0 * M * o / iv) for o in om_all
                          if np.isfinite(o)]
                bias_rows.append(dict(
                    root=root, geom=geom, btag=btag, horizon=hname, M=M,
                    omega2_N1=om, iv_hat=iv, bias_2Momega2_over_IV=b,
                    bias_min_across_estimates=min(brange),
                    bias_max_across_estimates=max(brange),
                    trigamma=trigamma(M)))
    B = pd.DataFrame(bias_rows)
    B.to_csv(os.path.join(RES, "phase6_rv_bias.csv"), index=False)

    # implied Var(log RV) inflation from day-varying noise bias, and refit
    corr_rows = []
    for root, geom, btag in CELLS:
        for hname in ["1day"]:
            if (geom, hname) not in EXTRA_M:
                continue
            nr = N[(N.root == root) & (N.geom == geom)
                   & (N.group == "all")]
            om = float(nr["omega2_N1"].iloc[0])
            Ms = [m for m in GRID[(geom, hname)]
                  if m < EXTRA_M[(geom, hname)]] + [EXTRA_M[(geom, hname)]]
            for e in EST:
                lams, deltas, varlogs = [], [], []
                for M in Ms:
                    f = os.path.join(
                        CACHE, f"grid_{root}_{geom}_{btag}_{hname}_M{M}.npz")
                    if not os.path.exists(f):
                        lams.append(np.nan); deltas.append(np.nan)
                        varlogs.append(np.nan); continue
                    zz = np.load(f)
                    rv = zz["rv"]
                    iv_t = np.maximum(rv, 1e-300)
                    bt = 2.0 * M * om / iv_t
                    delta = float(np.var(np.log1p(bt)))
                    row = S[(S.root == root) & (S.geom == geom)
                            & (S.btag == btag) & (S.horizon == hname)
                            & (S.M == M) & (S.proxy == "RV")
                            & (~S.trimmed) & (S.estimator == e)]
                    lam = float(row["lam"].iloc[0]) if len(row) else np.nan
                    vlog = float(row["var_log_proxy"].iloc[0]) if len(row) \
                        else np.nan
                    lams.append(lam); deltas.append(delta)
                    varlogs.append(vlog)
                lams = np.array(lams); deltas = np.array(deltas)
                varlogs = np.array(varlogs)
                veps = (1 - lams) * varlogs
                veps_c = veps - deltas
                lam_c = 1 - veps_c / np.maximum(varlogs - deltas, 1e-300)
                b0, r20, _, _ = elasticity(Ms, lams)
                bc, r2c, _, _ = elasticity(Ms, lam_c)
                corr_rows.append(dict(
                    root=root, geom=geom, btag=btag, horizon=hname,
                    estimator=e, elasticity_raw=b0, r2_raw=r20,
                    elasticity_noise_corrected=bc, r2_corrected=r2c,
                    shift=bc - b0,
                    mean_delta=float(np.nanmean(deltas)),
                    mean_var_log=float(np.nanmean(varlogs)),
                    delta_share_of_var=float(np.nanmean(deltas / varlogs))))
    C6 = pd.DataFrame(corr_rows)
    C6.to_csv(os.path.join(RES, "phase6_noise_corrected_elasticity.csv"),
              index=False)

    # Var(log eps) profile and interior minimum
    prof_rows = []
    for root, geom, btag in CELLS:
        for (g2, hname), Ms in GRID.items():
            if g2 != geom:
                continue
            Ms = list(Ms)
            if (geom, hname) in EXTRA_M:
                Ms = [m for m in Ms if m < EXTRA_M[(geom, hname)]] \
                    + [EXTRA_M[(geom, hname)]]
            for e in EST:
                g = S[(S.root == root) & (S.geom == geom)
                      & (S.btag == btag) & (S.horizon == hname)
                      & (S.proxy == "RV") & (~S.trimmed)
                      & (S.estimator == e)].sort_values("M")
                if not len(g):
                    continue
                veps = ((1 - g["lam"]) * g["var_log_proxy"]).values
                mm = g["M"].values
                interior = np.nan
                depth = np.nan
                if len(veps) >= 3 and np.isfinite(veps).all():
                    j = int(np.argmin(veps))
                    if 0 < j < len(veps) - 1:
                        interior = float(mm[j])
                        depth = float(min(veps[0], veps[-1]) / veps[j])
                for M, v, vl, lam in zip(mm, veps, g["var_log_proxy"],
                                         g["lam"]):
                    prof_rows.append(dict(
                        root=root, geom=geom, btag=btag, horizon=hname,
                        estimator=e, M=int(M), var_log_rv=float(vl),
                        lam=float(lam), var_log_eps=float(v),
                        interior_min_M=interior, interior_depth=depth))
    pd.DataFrame(prof_rows).to_csv(
        os.path.join(RES, "phase6_var_log_eps_profile.csv"), index=False)
    timers["p6_noise"] = round(time.time() - t, 1)

    # ---------------- Phase 6b (RUN: 6a left the elasticity unexplained,
    # the implied noise inflation is 0.21% of Var(log RV) and moves the
    # elasticity by at most 0.06). Reference-based reliability:
    # lambda_M^ref = Var(log ref) / Var(log RV_M), with ref the per-session
    # kernel or two-scale estimate. The invariance PRODUCT is constant by
    # construction here (numerator is M-free), so the informative output is
    # the elasticity of the excess variance
    # (1-lambda)/lambda = (Var(log RV_M) - Var(log ref)) / Var(log ref).
    t = time.time()
    ref_rows = []
    for root, geom, btag in CELLS:
        f = os.path.join(CACHE, f"ref_{root}_{geom}_{btag}.npz")
        if not os.path.exists(f):
            continue
        zr = np.load(f)
        for refname in ["kernel", "tsrv"]:
            ref = zr[refname]
            pos = ref > 0
            vref = float(np.log(ref[pos]).var())
            hname = "1day"
            if (geom, hname) not in EXTRA_M:
                continue
            Ms = [m for m in GRID[(geom, hname)]
                  if m < EXTRA_M[(geom, hname)]] + [EXTRA_M[(geom, hname)]]
            lams = []
            for M in Ms:
                row = S[(S.root == root) & (S.geom == geom)
                        & (S.btag == btag) & (S.horizon == hname)
                        & (S.M == M) & (S.proxy == "RV") & (~S.trimmed)
                        & (S.estimator == "E2")]
                vlog = float(row["var_log_proxy"].iloc[0]) if len(row) \
                    else np.nan
                lam = vref / vlog if vlog > 0 else np.nan
                lams.append(lam)
                ref_rows.append(dict(
                    root=root, geom=geom, btag=btag, horizon=hname,
                    reference=refname, M=M, n_ref_nonpositive=int((~pos).sum()),
                    var_log_ref=vref, var_log_rv=vlog, lam_ref=lam))
            b, r2, nu, nd = elasticity(Ms, np.array(lams))
            for rr in ref_rows[-len(Ms):]:
                rr["elasticity"] = b
                rr["elasticity_r2"] = r2
                rr["n_dropped"] = nd
    pd.DataFrame(ref_rows).to_csv(
        os.path.join(RES, "phase6b_reference_lambda.csv"), index=False)
    timers["p6b_reference"] = round(time.time() - t, 1)

    # ---------------- Phase 7 summary: RV vs TRV3
    t = time.time()
    j7 = INV[(~INV.trimmed)].pivot_table(
        index=["root", "geom", "btag", "horizon", "estimator"],
        columns="proxy", values=["elasticity", "ratio_max_min", "cv"])
    j7.columns = ["_".join(c) for c in j7.columns]
    j7 = j7.reset_index()
    j7["elasticity_shift_TRV3_minus_RV"] = (j7["elasticity_TRV3"]
                                            - j7["elasticity_RV"])
    j7["moves_toward_minus1"] = (
        (j7["elasticity_TRV3"] + 1).abs() < (j7["elasticity_RV"] + 1).abs())
    trvshare = S[(S.proxy == "TRV3") & (~S.trimmed)].groupby(
        ["root", "geom", "btag", "horizon", "M"], as_index=False)[
            "trv_over_rv"].first()
    trvshare["share_rv_removed"] = 1 - trvshare["trv_over_rv"]
    j7.to_csv(os.path.join(RES, "phase7_rv_vs_trv3.csv"), index=False)
    trvshare.to_csv(os.path.join(RES, "phase7_truncation_share.csv"),
                    index=False)
    timers["p7"] = round(time.time() - t, 1)

    timers["total"] = round(time.time() - t0, 1)
    with open(os.path.join(RES, "phase567_summary.json"), "w") as fh:
        json.dump(dict(timers=timers, noise_summary=n6,
                       ranking_consistent_across_cells=consistent,
                       ranking_table=piv.to_dict()), fh, indent=1,
                  default=str)
    print(json.dumps(timers, indent=1))
    print("\nranking consistent across all cells:", consistent)
    print(piv.to_string())
    print("\nnoise summary:", json.dumps(n6, indent=1))


if __name__ == "__main__":
    main()
