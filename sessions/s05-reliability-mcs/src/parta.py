"""S05 T1 + Part A (quarticity ratio R = (2/M) Q / P^2) + variant selection.

T1 runs first and halts on failure. Part B's boundary treatment is crossed
through everything: B1 removes the 1-minute returns at NY minutes
{09:30, 09:31, 15:59, 16:00, 18:01} by bridging the log-price path over
them (zero return), so all M levels inherit the exclusion coherently.

Pre-registered stability metric (fixed here, before any lambda exists):
the share of sessions where R exceeds 10x its cell median, averaged
equally over (root, geometry, year, M) cells under B0. Most stable =
smallest share; tie-break = smaller mean p95/median ratio. The selected
variant is recorded and used by Part C's E4 unchanged.
"""

import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy.special import gamma as G

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, os.path.join(ROOT, "sessions", "s03-data-noise", "src"))
import analysis as s03a                       # noqa: E402

RES = os.path.join(BASE, "results")
S04_RES = os.path.join(ROOT, "sessions", "s04-repairs-diagnostics", "results")
M_SETS = {"RTH": [13, 26, 78, 195, 390], "GLOBEX": [23, 46, 138, 345, 1380]}
BOUNDARY_MIN = [570, 571, 959, 960, 1081]      # NY minutes to bridge in B1

MU43 = 2 ** (2.0 / 3.0) * G(7.0 / 6.0) / G(0.5)          # E|Z|^(4/3)
# ADS (2012) MedRQ constant: 3*pi*M/(9*pi + 72 - 52*sqrt(3)) * M/(M-2)
MEDRQ_C = 3.0 * np.pi / (9.0 * np.pi + 72.0 - 52.0 * np.sqrt(3.0))
MEDRV_C = np.pi / (6.0 - 4.0 * np.sqrt(3.0) + np.pi)

VARIANTS = ["RQ_RV", "TQ_BV", "TRQ3_TRV3", "TRQ5_TRV5", "TRQ10_TRV10",
            "MEDRQ_MEDRV"]


def med3(a, b, c):
    return a + b + c - np.minimum(np.minimum(a, b), c) \
        - np.maximum(np.maximum(a, b), c)


def quart_suite(r, M):
    """All quarticity variants and matching proxies from (S, M) returns."""
    r = r.astype(np.float64)
    r2 = r * r
    rv = r2.sum(axis=1)
    rq = (M / 3.0) * (r2 * r2).sum(axis=1)
    a = np.abs(r)
    bv = (np.pi / 2.0) * (M / (M - 1.0)) * (a[:, 1:] * a[:, :-1]).sum(axis=1)
    a43 = a ** (4.0 / 3.0)
    tq = M * (M / (M - 2.0)) * MU43 ** (-3.0) \
        * (a43[:, :-2] * a43[:, 1:-1] * a43[:, 2:]).sum(axis=1)
    m3 = med3(a[:, :-2], a[:, 1:-1], a[:, 2:])
    medrv = MEDRV_C * (M / (M - 2.0)) * (m3 * m3).sum(axis=1)
    medrq = MEDRQ_C * M * (M / (M - 2.0)) * (m3 ** 4).sum(axis=1)
    outq = {"RQ_RV": (rq, rv), "TQ_BV": (tq, bv),
            "MEDRQ_MEDRV": (medrq, medrv)}
    for c in [3, 5, 10]:
        u = c * np.sqrt(np.maximum(bv, 1e-300) / M)
        keep = a <= u[:, None]
        rr2 = np.where(keep, r2, 0.0)
        trv = rr2.sum(axis=1)
        trq = (M / 3.0) * (rr2 * rr2).sum(axis=1)
        outq[f"TRQ{c}_TRV{c}"] = (trq, trv)
    return outq


def t1():
    """Tripower normalisation check on jump-free constant-vol data."""
    rng = np.random.Generator(np.random.PCG64(20260818))
    days, M = 20000, 390
    r = rng.standard_normal((days, M)) * np.sqrt(1.0 / M)
    q = quart_suite(r, M)
    rq, tq = q["RQ_RV"][0], q["TQ_BV"][0]
    # The normalisation check is the ratio of MEANS: E[RQ]/E[TQ] -> 1 under
    # the correct mu_{4/3}^{-3}. The mean of the per-session RATIO carries a
    # finite-M Jensen term (+1.6% at M=390, +0.5% at M=1380, O(1/M)), which
    # is reported, not gated: the defect this test discriminates is the
    # S04 constant error, a factor 4.97.
    rom = float(rq.mean() / tq.mean())
    ok = abs(rom - 1.0) < 0.01
    diag = dict(mu43=float(MU43),
                s04_wrong_constant=2 ** (2 / 3) * 0.8929795115692492,
                ratio_of_means=rom,
                mean_of_ratios_jensen=float((rq / tq).mean()),
                median_ratio=float(np.median(rq / tq)),
                tol=0.01, passed=bool(ok))
    diag["s04_implied_bias_factor"] = float(
        (diag["s04_wrong_constant"] / MU43) ** 3)
    return ok, diag


def bridged(filled, geom):
    """B1: zero the returns at boundary minutes by bridging the path."""
    n = filled.shape[1]
    r = np.diff(filled, axis=1)
    if geom == "RTH":
        slots = [m - 570 for m in BOUNDARY_MIN if 570 <= m < 960]
    else:
        slots = [(m - 1080) % 1440 for m in BOUNDARY_MIN]
        slots = [s for s in slots if s < 1380]
    for s in slots:
        si = s - 1          # return index ending at slot s
        if 0 <= si < r.shape[1]:
            r[:, si] = 0.0
    out = np.concatenate([filled[:, :1], filled[:, :1]
                          + np.cumsum(r, axis=1)], axis=1)
    return out


def main():
    t0 = time.time()
    ok, diag = t1()
    with open(os.path.join(RES, "s05_t1.json"), "w") as fh:
        json.dump(diag, fh, indent=1)
    print("T1:", json.dumps(diag, indent=1))
    if not ok:
        print("T1 FAILED - halting per pre-registration")
        sys.exit(1)

    rows = []
    panels = {}
    for geom in ["GLOBEX", "RTH"]:
        df = pd.read_parquet(os.path.join(S04_RES, f"bars_{geom}.parquet"))
        for root in ["ES", "NQ"]:
            dates, filled, present = s03a.build_panels(df, root, geom)
            years = pd.DatetimeIndex(dates).year.values
            for btag in ["B0", "B1"]:
                grid = filled if btag == "B0" else bridged(filled, geom)
                np.savez_compressed(
                    os.path.join(RES, f"panel_{root}_{geom}_{btag}.npz"),
                    dates=dates.astype("datetime64[D]").astype(str),
                    logpx=grid.astype(np.float32))
                n = grid.shape[1] - 1 if grid.shape[1] % 2 else grid.shape[1]
                nfull = s03a.N_GRID[geom]
                for M in M_SETS[geom]:
                    stride = nfull // M
                    p = grid[:, ::stride]
                    if p.shape[1] == M:
                        p = np.concatenate([p, grid[:, -1:]], axis=1)
                    r = np.diff(p, axis=1)
                    q = quart_suite(r, M)
                    for var in VARIANTS:
                        Q, P = q[var]
                        R = (2.0 / M) * Q / np.maximum(P * P, 1e-300)
                        logR = np.log(np.maximum(R, 1e-300))
                        for y in list(range(2016, 2024)) + [0]:
                            m = (years == y) if y else np.ones(len(R), bool)
                            Rm = R[m]
                            med = np.median(Rm)
                            lr = logR[m] - logR[m].mean()
                            acf = [float(np.dot(lr[:-k], lr[k:])
                                         / max(np.dot(lr, lr), 1e-300))
                                   for k in range(1, 11)]
                            rows.append(dict(
                                root=root, geom=geom, btag=btag, M=M,
                                variant=var, year=y, n=int(m.sum()),
                                median=float(med),
                                iqr=float(np.quantile(Rm, .75)
                                          - np.quantile(Rm, .25)),
                                p95=float(np.quantile(Rm, .95)),
                                p99=float(np.quantile(Rm, .99)),
                                share_gt10x_med=float((Rm > 10 * med).mean()),
                                ref_2overM=2.0 / M,
                                med_over_ref=float(med / (2.0 / M)),
                                acf1=acf[0], acf5=acf[4], acf10=acf[9],
                                acf_full=json.dumps(
                                    [round(x, 3) for x in acf])))
    A = pd.DataFrame(rows)
    A.to_csv(os.path.join(RES, "s05_parta.csv"), index=False)

    # ---------- pre-registered selection (B0, per-year cells, equal weight)
    sel = A[(A.btag == "B0") & (A.year != 0)]
    score = sel.groupby("variant")["share_gt10x_med"].mean()
    tie = sel.assign(rat=sel["p95"] / sel["median"]).groupby(
        "variant")["rat"].mean()
    ranked = pd.DataFrame(dict(share=score, p95_over_med=tie)).sort_values(
        ["share", "p95_over_med"])
    chosen = ranked.index[0]
    with open(os.path.join(RES, "s05_variant_selection.json"), "w") as fh:
        json.dump(dict(metric="mean share of sessions with R > 10x cell "
                              "median, B0, per (root,geom,year,M) cell",
                       ranking={k: dict(share=float(ranked.loc[k, 'share']),
                                        p95_over_med=float(
                                            ranked.loc[k, 'p95_over_med']))
                                for k in ranked.index},
                       chosen=str(chosen)), fh, indent=1)
    print("variant ranking:\n", ranked)
    print("CHOSEN:", chosen, f"| elapsed {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
