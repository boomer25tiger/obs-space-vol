"""S02 aggregation: raw npz -> per-cell stats CSV + threshold map arrays.

Rules fixed before results were inspected (mirroring S01):
- Recovery per replication = lambda_hat / lambda_true(matched proxy, rep).
- Cell = (latent shape, W, ptt, js, nsr, geometry, M, arm). Point = grand
  mean over 5 seeds x 200 reps; 95% CI = percentile bootstrap, 1000
  in-seed resamples averaged across seeds (seed 777); seed sd = sd of the
  5 seed means. Band pass: point and CI inside (1-B, 1+B).
- Threshold map entry (arm, DGP, W+ptt, js, geometry, M): the largest NSR
  in the sweep whose cell passes +/-15%, requiring every latent shape of
  that DGP to pass (the S01 all-cells rule). 'never' if no NSR passes
  (including 0); non-monotone pass patterns are flagged.
- Groups with missing seed files are reported as NOT RUN, never partially
  aggregated.
"""

import csv
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dgp2 import (GEOMETRIES, JS_SWEEP, LATENTS, NSR_SWEEP, W_CONFIGS,
                  DGP2Config, SD_FIXED, contamination_class)
from run2 import (ARM_NAMES, ARM_TRUE_PROXY, N_MASTERS, PROXIES, RAW_DIR,
                  BASE, REPS)

RES_DIR = os.path.join(BASE, "results")
BANDS = [0.10, 0.15, 0.25]
BOOT_N = 1000
BOOT_SEED = 777
PROXY_IDX = {p: i for i, p in enumerate(PROXIES)}


def group_files(cfg, n):
    files = []
    for si in range(N_MASTERS):
        fn = os.path.join(RAW_DIR, f"{cfg.label()}_g{n}_seed{si}.npz")
        if not os.path.exists(fn):
            return None
        files.append(fn)
    return files


def summarize_group(files, rng):
    """-> (per (arm, M): dict of stats). Bootstrap shared across arms."""
    lam = []
    lam_true = []
    m_list = None
    for fn in files:
        with np.load(fn, allow_pickle=False) as f:
            lam.append(f["lam"].astype(np.float64))        # (A, nM, R)
            lam_true.append(f["lam_true"].astype(np.float64))
            m_list = f["m_list"].tolist()
    A, nM, R = lam[0].shape
    # recovery per seed: (A, nM, R)
    rec = []
    for s in range(N_MASTERS):
        lt = lam_true[s]                    # (P, nM, R)
        tgt = np.stack([lt[PROXY_IDX[p]] for p in ARM_TRUE_PROXY])  # (A,nM,R)
        rec.append(lam[s] / tgt)
    rec = np.stack(rec, axis=0)             # (S, A, nM, R)

    W = np.stack([rng.multinomial(R, np.full(R, 1.0 / R), size=BOOT_N) / R
                  for _ in range(N_MASTERS)])            # (S, BOOT_N, R)
    finite = np.isfinite(rec)
    rec_z = np.where(finite, rec, 0.0)
    cnt = finite.astype(np.float64)
    # bootstrap means: for each seed, (A*nM, R) @ (R, BOOT_N)
    boot_num = np.einsum('sanr,sbr->sanb', rec_z, W)
    boot_den = np.einsum('sanr,sbr->sanb', cnt, W)
    boot = (boot_num / np.maximum(boot_den, 1e-12)).mean(axis=0)  # (A,nM,B)
    lo = np.percentile(boot, 2.5, axis=2)
    hi = np.percentile(boot, 97.5, axis=2)
    seed_means = np.where(cnt.sum(axis=3) > 0,
                          rec_z.sum(axis=3) / np.maximum(cnt.sum(axis=3), 1),
                          np.nan)                         # (S, A, nM)
    point = np.nanmean(seed_means, axis=0)
    seed_sd = np.nanstd(seed_means, axis=0, ddof=1)
    nan_frac = 1.0 - cnt.mean(axis=(0, 3))
    return m_list, point, lo, hi, seed_sd, nan_frac


def main():
    rng = np.random.Generator(np.random.PCG64(BOOT_SEED))
    rows = []
    missing = []
    n_groups_done = 0
    for dgp, fam, sh in LATENTS:
        for w, ptt in W_CONFIGS:
            for js in JS_SWEEP:
                for nsr in NSR_SWEEP:
                    cfg = DGP2Config(dgp, fam, sh, SD_FIXED, w, ptt, js, nsr)
                    for n in GEOMETRIES:
                        files = group_files(cfg, n)
                        key = dict(dgp=dgp, shape=sh, w=w, ptt=ptt, js=js,
                                   nsr=nsr, n=n,
                                   cclass=contamination_class(js, nsr))
                        if files is None:
                            missing.append(dict(**key))
                            continue
                        n_groups_done += 1
                        m_list, point, lo, hi, ssd, nf = summarize_group(
                            files, rng)
                        for ai, arm in enumerate(ARM_NAMES):
                            for mi, M in enumerate(m_list):
                                row = dict(**key, M=M, arm=arm,
                                           point=point[ai, mi],
                                           lo=lo[ai, mi], hi=hi[ai, mi],
                                           seed_sd=ssd[ai, mi],
                                           nan_frac=nf[ai, mi])
                                for B in BANDS:
                                    ok = (abs(row["point"] - 1) < B
                                          and row["lo"] > 1 - B
                                          and row["hi"] < 1 + B
                                          and np.isfinite(row["point"]))
                                    row[f"pass{int(B*100)}"] = bool(ok)
                                rows.append(row)
    os.makedirs(RES_DIR, exist_ok=True)
    csv_path = os.path.join(RES_DIR, "S02-cells.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    with open(os.path.join(RES_DIR, "S02-missing.json"), "w") as fh:
        json.dump(missing, fh)
    print(f"groups done {n_groups_done}, missing {len(missing)}, "
          f"rows {len(rows)}")


if __name__ == "__main__":
    main()
