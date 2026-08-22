"""S05E: positive control on the aggregation and reliability path.

CODE PATH. Every synthetic arm is aggregated and measured by the SAME
functions that produced the real-data numbers, imported unmodified:
  - `phase34.windows`  (S05B) horizon windowing
  - `phase34.subbars`  (S05B) sub-bar aggregation on the M grid
  - `parta.quart_suite` (S05) RV / TRV3 / RQ / TRQ3
  - `estimators2.e1_reduced / e2 / e4` (S02) the Part C estimators
  - `fbm.CirculantEmbedding`, `fbm.fgn_acf` (S01) for the A4 rough path
Only the data generation is new; nothing in the aggregation, the
Var(log RV_M) computation or the estimators is reimplemented here.
"""

import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.special import polygamma

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
RES = os.path.join(BASE, "results")
S05B = os.path.join(ROOT, "sessions", "s05b-defect-and-estimator-audit")
S05B_RES = os.path.join(S05B, "results")
S05B_CACHE = os.path.join(S05B_RES, "cache")
for p in [os.path.join(S05B, "src"),
          os.path.join(ROOT, "sessions", "s05-reliability-mcs", "src"),
          os.path.join(ROOT, "sessions", "s02-mechanism-expansion", "src"),
          os.path.join(ROOT, "sessions", "s01-estimator-validation", "src")]:
    sys.path.insert(0, p)

from phase34 import windows, subbars                     # noqa: E402
from parta import quart_suite                            # noqa: E402
import estimators2 as e2mod                              # noqa: E402
from fbm import CirculantEmbedding, fgn_acf              # noqa: E402

GRIDS = {"RTH_1day": (390, None, [5, 6, 10, 13, 26, 78, 195, 389]),
         "RTH_1h": (390, 60, [4, 5, 6, 10, 12, 15, 20, 30, 60]),
         "RTH_30min": (390, 30, [5, 6, 10, 15, 30]),
         "GLOBEX_1day": (1380, None, [5, 6, 10, 12, 23, 46, 138, 345, 1379])}
DIMS = {"GLOBEX": (1953, 1380), "RTH": (1901, 390)}
VAR_LOG_IV = 1.02                       # DECISIONS item 36 intercept
TRUNC_TARGET = {"GLOBEX": 0.2938, "RTH": 0.1741}   # S05B phase7, finest M
PAD_RATE = {2016: 0.019154, 2017: 0.026621, 2018: 0.018226,
            2019: 0.016714, 2020: 0.016417, 2021: 0.010990,
            2022: 0.004999, 2023: 0.007027}            # S05D phase3, GLOBEX
H_ROUGH = 0.1
JUMP_INTENSITY = 1.0
MASTER = 20260819
N_SEEDS = 5
SEEDS = [int(s) for s in
         np.random.SeedSequence(MASTER).generate_state(N_SEEDS)]
EST = ["E1_a_exp_L1-5", "E1_a_exp_L1-10", "E1_d_model_L1-5",
       "E1_d_model_L1-10", "E2", "E4"]


def trig(M):
    return polygamma(1, np.asarray(M, float) / 2.0)


def fit_free(M, y):
    """Var = c + A M^b by curve_fit, the S05D/S05B procedure."""
    M = np.asarray(M, float)
    y = np.asarray(y, float)
    ok = np.isfinite(y)
    if ok.sum() < 4:
        return dict(c=np.nan, A=np.nan, b=np.nan, rmse=np.nan)
    try:
        p, _ = curve_fit(lambda x, c, A, b: c + A * np.power(x, b),
                         M[ok], y[ok], p0=[y[ok].min(), 1.0, -0.5],
                         maxfev=60000)
        pred = p[0] + p[1] * np.power(M[ok], p[2])
        return dict(c=float(p[0]), A=float(p[1]), b=float(p[2]),
                    rmse=float(np.sqrt(np.mean((y[ok] - pred) ** 2))))
    except Exception as e:
        return dict(c=np.nan, A=np.nan, b=np.nan, rmse=np.nan, err=str(e))


def fit_loglog(M, y):
    M = np.asarray(M, float)
    y = np.asarray(y, float)
    ok = np.isfinite(y) & (y > 0)
    if ok.sum() < 3:
        return dict(b=np.nan, r2=np.nan)
    b, a = np.polyfit(np.log(M[ok]), np.log(y[ok]), 1)
    pred = a + b * np.log(M[ok])
    r2 = 1 - ((np.log(y[ok]) - pred) ** 2).sum() / \
        max(((np.log(y[ok]) - np.log(y[ok]).mean()) ** 2).sum(), 1e-300)
    return dict(b=float(b), r2=float(r2))


def profile_for(geom):
    """Measured intraday variance profile of the REAL panel, mean 1."""
    z = np.load(os.path.join(S05B_CACHE, f"ret1m_ES_{geom}_B0.npz"))
    r1 = z["r1"].astype(np.float64)
    prof = (r1 ** 2).mean(axis=0)
    return prof / prof.mean()


def make_panel(arm, geom, rng, sigma_j=0.0):
    """Synthetic log-price panel (sessions, minutes). Generation only."""
    S, n = DIMS[geom]
    L = n - 1                                    # within-session returns
    if arm == "A4":
        emb = CirculantEmbedding(fgn_acf(H_ROUGH, np.arange(S)))
        x = emb.sample(rng, size=1)[0]
        x = x / x.std() * np.sqrt(VAR_LOG_IV)
    else:
        x = rng.normal(0.0, np.sqrt(VAR_LOG_IV), size=S)
    iv = np.exp(x)
    if arm in ("A1", "A2", "A3"):
        prof = profile_for(geom)[:L]
        prof = prof / prof.mean()
    else:
        prof = np.ones(L)
    step_var = np.outer(iv / L, prof)
    r = rng.standard_normal((S, L)) * np.sqrt(step_var)
    if arm in ("A2", "A3") and sigma_j > 0:
        nj = rng.poisson(JUMP_INTENSITY, size=S)
        tot = int(nj.sum())
        if tot:
            di = np.repeat(np.arange(S), nj)
            si = rng.integers(0, L, size=tot)
            np.add.at(r, (di, si), rng.normal(0.0, sigma_j, size=tot))
    px = np.concatenate([np.zeros((S, 1)), np.cumsum(r, axis=1)], axis=1)
    pad_mask = None
    if arm == "A3":
        years = np.array(sorted(PAD_RATE) * (S // len(PAD_RATE) + 1))[:S]
        rates = np.array([PAD_RATE[y] for y in years])
        drop = rng.random((S, n)) < rates[:, None]
        drop[:, 0] = False
        pad_mask = drop
        pxn = np.where(drop, np.nan, px)
        px = pd.DataFrame(pxn).ffill(axis=1).bfill(axis=1).values
    return px, x, pad_mask


def calibrate_jump(geom, rng):
    """Bisect sigma_j so the finest-M truncated share matches S05B."""
    S, n = DIMS[geom]
    Mf = n - 1
    target = TRUNC_TARGET[geom]
    small = 400
    lo, hi = 1e-4, 2.0

    def removed(sig):
        r2 = np.random.Generator(np.random.PCG64(12345))
        x = r2.normal(0.0, np.sqrt(VAR_LOG_IV), size=small)
        iv = np.exp(x)
        prof = profile_for(geom)[:n - 1]
        prof = prof / prof.mean()
        sv = np.outer(iv / (n - 1), prof)
        r = r2.standard_normal((small, n - 1)) * np.sqrt(sv)
        nj = r2.poisson(JUMP_INTENSITY, size=small)
        tot = int(nj.sum())
        if tot:
            np.add.at(r, (np.repeat(np.arange(small), nj),
                          r2.integers(0, n - 1, size=tot)),
                      r2.normal(0.0, sig, size=tot))
        sb, _ = subbars(r, Mf)
        q = quart_suite(sb, Mf)
        rv = q["RQ_RV"][1]
        trv = q["TRQ3_TRV3"][1]
        return 1.0 - float(np.mean(trv / np.maximum(rv, 1e-300)))

    for _ in range(14):
        mid = 0.5 * (lo + hi)
        if removed(mid) < target:
            lo = mid
        else:
            hi = mid
    sig = 0.5 * (lo + hi)
    return float(sig), float(removed(sig))


def measure(px, geom, hname, Ms, wlen, want_est=False, x_true=None):
    """Aggregate through the REAL path and measure."""
    r1 = np.diff(px, axis=1)
    rw, nw = windows(r1, wlen)
    rows = []
    for M in Ms:
        if M > rw.shape[1]:
            continue
        sb, _ = subbars(rw, M)
        rv = (sb ** 2).sum(axis=1)
        pos = rv > 0
        vlog = float(np.log(rv[pos]).var())
        row = dict(M=M, var_log_rv=vlog, n_windows=int(len(rv)),
                   n_zero_rv=int((~pos).sum()))
        if want_est:
            q = quart_suite(sb, M)
            trq, trv = q["TRQ3_TRV3"]
            rqv, rvv = q["RQ_RV"]
            row["trv_over_rv"] = float(np.mean(trv / np.maximum(rvv, 1e-300)))
            logp = np.log(np.maximum(rvv, 1e-300))
            h = M // 2
            p1 = (sb[:, :h] ** 2).sum(axis=1)
            p2 = (sb[:, h:] ** 2).sum(axis=1)
            g = e2mod.e1_reduced(logp)
            for (a, ls), v in g.items():
                row[f"E1_{a}_{ls}"] = float(v)
            row["E2"] = float(e2mod.e2(
                logp, np.log(np.maximum(p1, 1e-300)),
                np.log(np.maximum(p2, 1e-300))))
            row["E4"] = float(e2mod.e4(trv, trq,
                                       np.log(np.maximum(trv, 1e-300)), M))
            if x_true is not None:
                row["lam_true"] = float(np.var(x_true) / vlog)
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    t0 = time.time()
    timers = {}
    out = {"seeds": SEEDS, "master": MASTER}

    # ---------------- PHASE 1: reference exponent of trigamma itself
    t = time.time()
    p1 = []
    for gname, (n, wlen, Ms) in GRIDS.items():
        y = trig(Ms)
        ff = fit_free(Ms, y)
        ll = fit_loglog(Ms, y)
        p1.append(dict(grid=gname, n_points=len(Ms),
                       M_min=min(Ms), M_max=max(Ms),
                       free_c=ff["c"], free_A=ff["A"], free_b=ff["b"],
                       free_rmse=ff["rmse"],
                       loglog_b=ll["b"], loglog_r2=ll["r2"]))
        # also with the empirical intercept added, matching the data model
        ff2 = fit_free(Ms, VAR_LOG_IV + y)
        p1[-1].update(with_intercept_c=ff2["c"], with_intercept_A=ff2["A"],
                      with_intercept_b=ff2["b"],
                      with_intercept_rmse=ff2["rmse"])
    P1 = pd.DataFrame(p1)
    P1.to_csv(os.path.join(RES, "phase1_trigamma_reference.csv"),
              index=False)
    timers["phase1"] = round(time.time() - t, 1)

    # ---------------- PHASE 2: synthetic arms
    t = time.time()
    sig = {}
    for geom in ["GLOBEX", "RTH"]:
        s, got = calibrate_jump(geom, None)
        sig[geom] = dict(sigma_j=s, achieved_removed_share=got,
                         target=TRUNC_TARGET[geom])
    out["jump_calibration"] = sig
    timers["calibration"] = round(time.time() - t, 1)

    t = time.time()
    fits, est_rows = [], []
    for arm in ["A0", "A1", "A2", "A3", "A4"]:
        for gname, (n, wlen, Ms) in GRIDS.items():
            geom = gname.split("_")[0]
            hname = gname.split("_")[1]
            if geom == "GLOBEX" and hname != "1day":
                continue
            for si, seed in enumerate(SEEDS):
                rng = np.random.Generator(np.random.PCG64(seed))
                px, x, pad = make_panel(
                    arm, geom, rng,
                    sigma_j=sig[geom]["sigma_j"] if arm in ("A2", "A3")
                    else 0.0)
                want = (arm in ("A0", "A2")) and hname == "1day"
                D = measure(px, geom, hname, Ms, wlen, want_est=want,
                            x_true=x)
                ff = fit_free(D.M.values, D.var_log_rv.values)
                fits.append(dict(arm=arm, grid=gname, seed_index=si,
                                 seed=seed, c=ff["c"], A=ff["A"],
                                 b=ff["b"], rmse=ff["rmse"],
                                 var_log_iv_input=float(np.var(x)),
                                 var_log_iv_recovered_as_c=ff["c"],
                                 recovery_error=float(ff["c"] - np.var(x))))
                if want:
                    for _, r in D.iterrows():
                        base = dict(arm=arm, grid=gname, seed_index=si,
                                    M=int(r.M), lam_true=r.get("lam_true"),
                                    var_log_rv=r.var_log_rv,
                                    trv_over_rv=r.get("trv_over_rv"))
                        for e in EST:
                            est_rows.append(dict(base, estimator=e,
                                                 lam=r.get(e)))
    F = pd.DataFrame(fits)
    F.to_csv(os.path.join(RES, "phase2_arm_fits.csv"), index=False)
    E = pd.DataFrame(est_rows)
    E.to_csv(os.path.join(RES, "phase2_estimators.csv"), index=False)
    timers["phase2"] = round(time.time() - t, 1)

    # arm summary with between-seed dispersion
    AS = F.groupby(["arm", "grid"]).agg(
        b_mean=("b", "mean"), b_sd=("b", "std"), b_min=("b", "min"),
        b_max=("b", "max"), c_mean=("c", "mean"), c_sd=("c", "std"),
        A_mean=("A", "mean"), rmse_mean=("rmse", "mean"),
        var_log_iv_input_mean=("var_log_iv_input", "mean"),
        recovery_error_mean=("recovery_error", "mean"),
        n_seeds=("seed", "nunique")).reset_index()
    AS.to_csv(os.path.join(RES, "phase2_arm_summary.csv"), index=False)

    # estimator grid-invariance and elasticity per arm/estimator
    inv = []
    for (arm, grid, si, e), g in E.groupby(
            ["arm", "grid", "seed_index", "estimator"]):
        g = g.sort_values("M")
        prod = (g["lam"] * g["var_log_rv"]).values
        ok = np.isfinite(prod) & (g["lam"].values > 0) & \
            (g["lam"].values < 1)
        lam = g["lam"].values
        Ms = g["M"].values.astype(float)
        ok2 = np.isfinite(lam) & (lam > 0) & (lam < 1)
        b = np.nan
        if ok2.sum() >= 3:
            b = float(np.polyfit(np.log(Ms[ok2]),
                                 np.log((1 - lam[ok2]) / lam[ok2]), 1)[0])
        inv.append(dict(
            arm=arm, grid=grid, seed_index=si, estimator=e,
            ratio_max_min=float(prod[ok].max() / prod[ok].min())
            if ok.any() and prod[ok].min() > 0 else np.nan,
            elasticity=b,
            mean_abs_error_vs_true=float(
                np.nanmean(np.abs(g["lam"].values - g["lam_true"].values))),
            mean_lam=float(np.nanmean(g["lam"].values)),
            mean_lam_true=float(np.nanmean(g["lam_true"].values))))
    IV = pd.DataFrame(inv)
    IV.to_csv(os.path.join(RES, "phase2_estimator_invariance.csv"),
              index=False)

    # ---------------- PHASE 3: decomposition on real data (cache only)
    t = time.time()
    gi = pd.read_csv(os.path.join(S05B_RES, "phase4_grid_index.csv"))
    rows3 = []
    for (root, geom, btag, hname), g in gi.groupby(
            ["root", "geom", "btag", "horizon"]):
        Ms = sorted(g.M.unique())
        vr, vt = [], []
        yearsets = {}
        tercsets = {}
        for M in Ms:
            f = os.path.join(S05B_CACHE,
                             f"grid_{root}_{geom}_{btag}_{hname}_M{M}.npz")
            if not os.path.exists(f):
                vr.append(np.nan); vt.append(np.nan); continue
            z = np.load(f)
            rv, trv, yrs = z["rv"], z["trv"], z["years"]
            pr, pt = rv > 0, trv > 0
            vr.append(float(np.log(rv[pr]).var()))
            vt.append(float(np.log(trv[pt]).var()))
            for y in np.unique(yrs):
                m = (yrs == y) & pr
                yearsets.setdefault(int(y), []).append(
                    float(np.log(rv[m]).var()) if m.sum() > 30 else np.nan)
            if M == min(Ms):
                q = np.quantile(rv[pr], [1/3, 2/3])
                terc_assign = np.searchsorted(q, rv)
            tq = np.quantile(rv[pr], [1/3, 2/3])
            ta = np.searchsorted(tq, rv)
            for tc in [0, 1, 2]:
                m = (ta == tc) & pr
                tercsets.setdefault(tc + 1, []).append(
                    float(np.log(rv[m]).var()) if m.sum() > 30 else np.nan)
        fr = fit_free(Ms, vr)
        ft = fit_free(Ms, vt)
        rec = dict(root=root, geom=geom, btag=btag, horizon=hname,
                   n_M=len(Ms), b_RV=fr["b"], c_RV=fr["c"], A_RV=fr["A"],
                   rmse_RV=fr["rmse"], b_TRV3=ft["b"], c_TRV3=ft["c"],
                   A_TRV3=ft["A"], rmse_TRV3=ft["rmse"],
                   b_shift_TRV3_minus_RV=ft["b"] - fr["b"])
        ybs = {}
        for y, vals in yearsets.items():
            fy = fit_free(Ms, vals)
            ybs[y] = fy["b"]
        tbs = {}
        for tc, vals in tercsets.items():
            fy = fit_free(Ms, vals)
            tbs[tc] = fy["b"]
        yv = np.array([v for v in ybs.values() if np.isfinite(v)])
        tv = np.array([v for v in tbs.values() if np.isfinite(v)])
        rec.update(b_year_mean=float(yv.mean()) if len(yv) else np.nan,
                   b_year_sd=float(yv.std()) if len(yv) else np.nan,
                   b_year_min=float(yv.min()) if len(yv) else np.nan,
                   b_year_max=float(yv.max()) if len(yv) else np.nan,
                   n_years=int(len(yv)),
                   b_terc_mean=float(tv.mean()) if len(tv) else np.nan,
                   b_terc_sd=float(tv.std()) if len(tv) else np.nan,
                   b_terc_min=float(tv.min()) if len(tv) else np.nan,
                   b_terc_max=float(tv.max()) if len(tv) else np.nan,
                   b_by_year=json.dumps({str(k): (None if not np.isfinite(v)
                                                  else round(v, 4))
                                         for k, v in ybs.items()}),
                   b_by_tercile=json.dumps({str(k): (None if not np.isfinite(v)
                                                     else round(v, 4))
                                            for k, v in tbs.items()}))
        rows3.append(rec)
    P3 = pd.DataFrame(rows3)
    P3.to_csv(os.path.join(RES, "phase3_decomposition.csv"), index=False)
    timers["phase3"] = round(time.time() - t, 1)

    timers["total"] = round(time.time() - t0, 1)
    out["timers"] = timers
    with open(os.path.join(RES, "s05e_summary.json"), "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    print(json.dumps(timers, indent=1))
    print("\n=== PHASE 1 trigamma reference ===")
    print(P1[["grid", "free_b", "free_rmse", "loglog_b",
              "with_intercept_b"]].to_string(index=False))
    print("\n=== PHASE 2 arm summary ===")
    print(AS[["arm", "grid", "b_mean", "b_sd", "c_mean",
              "var_log_iv_input_mean", "rmse_mean"]].to_string(index=False))
    print("\n=== PHASE 3 real-data b, RV vs TRV3 ===")
    print(P3[["root", "geom", "btag", "horizon", "b_RV", "b_TRV3",
              "b_year_mean", "b_year_sd", "b_terc_mean"]]
          .to_string(index=False))


if __name__ == "__main__":
    main()
