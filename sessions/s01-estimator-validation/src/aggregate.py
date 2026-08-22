"""Phase-5 aggregation: raw per-replication estimates -> S01-report.md.

Aggregation rules (fixed before results were inspected):
- Recovery ratio per replication: lambda_hat / lambda_true(rep).
- Cell = (DGP parameter combo, geometry, M). Per cell and arm:
    point estimate  = grand mean of recovery over 5 seeds x 200 reps
    between-seed sd = sd of the 5 per-seed means
    95% CI          = percentile bootstrap, 1000 resamples of reps within
                      each seed, averaged across seeds (bootstrap seed 777)
- PASS at band +/-B: point inside (1-B, 1+B) AND CI inside (1-B, 1+B).
- Per (estimator-arm, DGP) verdict: PASS only if every cell passes
  (pre-registration: failure on any single DGP cell is a FAIL).
- E3 triple selection: per (cell group, M) from the across-seed mean error
  correlation matrix; INAPPLICABLE if the best triple's max off-diagonal
  error correlation exceeds 0.20.
"""

import csv
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import estimators as est
from dgp import GEOMETRIES, build_param_grid
from run import ARM_KEYS, N_MASTERS, PROXY_NAMES, PARK_IDX, GK_IDX, RAW_DIR, BASE

RES_DIR = os.path.join(BASE, "results")
LOG_DIR = os.path.join(BASE, "logs")
BANDS = [0.10, 0.15, 0.25]
BOOT_N = 1000
BOOT_SEED = 777
REPS = 200

E1_ARMS = [f"E1_{arm}_{ls}" for arm, ls in ARM_KEYS]
ALL_ARMS = E1_ARMS + ["E2", "E3", "E4"]


def load_group(label, n):
    """Load the 5 seed files of one cell group; returns None if incomplete."""
    out = []
    for si in range(N_MASTERS):
        fn = os.path.join(RAW_DIR, f"{label}_g{n}_seed{si}.npz")
        if not os.path.exists(fn):
            return None
        out.append(np.load(fn, allow_pickle=False))
    return out


def recovery_matrix(files, m_list):
    """dict arm -> (nM, 5, REPS) recovery ratios; plus E3 metadata."""
    nM = len(m_list)
    rec = {a: np.full((nM, N_MASTERS, REPS), np.nan) for a in ALL_ARMS}
    errcorr_mean = np.zeros((len(PROXY_NAMES), len(PROXY_NAMES)))
    for si, f in enumerate(files):
        lt = f["lam_true"]                       # (nM, REPS)
        for ai in range(16):
            rec[E1_ARMS[ai]][:, si, :] = f["lam_e1"][ai] / lt
        rec["E2"][:, si, :] = f["lam_e2"] / lt
        rec["E4"][:, si, :] = f["lam_e4"] / lt
        errcorr_mean += f["errcorr"].mean(axis=2) / N_MASTERS

    e3_meta = {}
    for mi in range(nM):
        triples = est.e3_candidate_triples(mi, len(PROXY_NAMES),
                                           PARK_IDX, GK_IDX)
        best_t, best_c = None, np.inf
        for (i, j, k) in triples:
            c = max(abs(errcorr_mean[i, j]), abs(errcorr_mean[i, k]),
                    abs(errcorr_mean[j, k]))
            if c < best_c:
                best_c, best_t = c, (i, j, k)
        applicable = best_c <= 0.20
        e3_meta[mi] = dict(triple=best_t, maxcorr=float(best_c),
                           applicable=bool(applicable))
        if applicable:
            i, j, k = best_t
            for si, f in enumerate(files):
                yv = f["yvar"].astype(np.float64)        # (9, REPS)
                pv = f["pairvar"].astype(np.float64)     # (9, 9, REPS)
                var_e = 0.5 * (pv[i, j] + pv[i, k] - pv[j, k])
                lam3 = 1.0 - var_e / yv[i]
                rec["E3"][mi, si, :] = lam3 / f["lam_true"][mi]
    return rec, e3_meta, errcorr_mean


def summarize_cell(R, boot_w):
    """R: (5, REPS) recovery. boot_w: (5, BOOT_N, REPS) resample weights."""
    nan_frac = float(np.isnan(R).mean())
    seed_means = np.nanmean(R, axis=1)
    point = float(np.nanmean(seed_means))
    seed_sd = float(np.nanstd(seed_means, ddof=1))
    Rz = np.nan_to_num(R, nan=0.0)
    cnt = (~np.isnan(R)).astype(float)
    num = np.einsum('sr,sbr->sb', Rz, boot_w)
    den = np.einsum('sr,sbr->sb', cnt, boot_w)
    boot = (num / np.maximum(den, 1e-12)).mean(axis=0)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    res = dict(point=point, lo=float(lo), hi=float(hi), seed_sd=seed_sd,
               nan_frac=nan_frac)
    for B in BANDS:
        res[f"pass{int(B*100)}"] = bool(
            (1 - B < point < 1 + B) and (lo > 1 - B) and (hi < 1 + B))
    return res


def main():
    cfgs = build_param_grid()
    rng = np.random.Generator(np.random.PCG64(BOOT_SEED))
    rows = []
    e3_rows = []
    errcorr_by_dgp_geom = defaultdict(lambda: [np.zeros((9, 9)), 0])
    missing = []

    for cfg in cfgs:
        for n, m_list in GEOMETRIES.items():
            files = load_group(cfg.label(), n)
            if files is None:
                missing.append(f"{cfg.label()}_g{n}")
                continue
            rec, e3_meta, ec = recovery_matrix(files, m_list)
            acc = errcorr_by_dgp_geom[(cfg.dgp, n)]
            acc[0] += ec
            acc[1] += 1
            boot_w = np.stack([
                rng.multinomial(REPS, np.full(REPS, 1.0 / REPS),
                                size=BOOT_N) / REPS
                for _ in range(N_MASTERS)])       # (5, BOOT_N, REPS)
            for mi, M in enumerate(m_list):
                for arm in ALL_ARMS:
                    if arm == "E3" and not e3_meta[mi]["applicable"]:
                        rows.append(dict(
                            dgp=cfg.dgp, family=cfg.family, shape=cfg.shape,
                            sd=cfg.sd, js=cfg.jump_share, nsr=cfg.nsr, n=n,
                            M=M, arm=arm, point=np.nan, lo=np.nan, hi=np.nan,
                            seed_sd=np.nan, nan_frac=1.0, pass10=None,
                            pass15=None, pass25=None, inapplicable=True))
                        continue
                    s = summarize_cell(rec[arm][mi], boot_w)
                    rows.append(dict(
                        dgp=cfg.dgp, family=cfg.family, shape=cfg.shape,
                        sd=cfg.sd, js=cfg.jump_share, nsr=cfg.nsr, n=n,
                        M=M, arm=arm, inapplicable=False, **s))
                t, c = e3_meta[mi]["triple"], e3_meta[mi]["maxcorr"]
                e3_rows.append(dict(
                    dgp=cfg.dgp, shape=cfg.shape, sd=cfg.sd,
                    js=cfg.jump_share, nsr=cfg.nsr, n=n, M=M,
                    triple="+".join(PROXY_NAMES[i] for i in t),
                    maxcorr=round(c, 3),
                    applicable=e3_meta[mi]["applicable"]))
            for f in files:
                f.close()

    # ---------------- per-cell CSV (full, uncollapsed record)
    csv_path = os.path.join(RES_DIR, "S01-cells.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    e3_csv = os.path.join(RES_DIR, "S01-e3-selection.csv")
    with open(e3_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(e3_rows[0].keys()))
        w.writeheader()
        w.writerows(e3_rows)

    np.savez(os.path.join(RES_DIR, "S01-errcorr.npz"),
             **{f"{d}_g{g}": v[0] / v[1]
                for (d, g), (v) in
                [(k, vv) for k, vv in errcorr_by_dgp_geom.items()]})

    with open(os.path.join(RES_DIR, "S01-agg-summary.json"), "w") as fh:
        json.dump(dict(n_rows=len(rows), missing=missing), fh, indent=1)
    print(f"rows: {len(rows)}, missing groups: {len(missing)}")
    if missing:
        print("MISSING:", missing[:10], "...")


if __name__ == "__main__":
    main()
