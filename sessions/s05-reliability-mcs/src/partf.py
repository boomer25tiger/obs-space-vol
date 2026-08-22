"""S05 Part F: synthetic arm at calibrated constants. Error curves, no gate.

S01-style estimator comparison (E1 a/d at L1-5/L1-10, E2, E4) on an AR(1)
latent log-variance (phi 0.98, sd 0.7 — the S01 constants), with:
- intraday variance profile = the S04-measured mean per-minute squared
  return profile (normalized to mean 1), which already CONTAINS the
  boundary-minute elevations (25.9x/20.6x/7.5x are its largest spikes);
- Student-t intraday innovations, nu in {3.0, 3.4, 4.5} (Hill calibration),
  standardized to unit variance;
- additive Gaussian log-price noise, NSR in {1e-5, 3e-5, 1e-4};
- both geometries; T = 2000 windows, 200 replications, 5 master seeds
  (SeedSequence(20260820).generate_state(5)), per-dataset seeds
  [master, index] as in S01/S02.

E4 uses (2/M) RQ / RV^2 on plain RV (the S01 form; Part A's variant
selection applies to the real-data surface, not to the S01 regeneration).
Recovery = lambda_hat / lambda_true(rep) reported as curves over (nu, NSR).
"""

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
for p in [os.path.join(ROOT, "sessions", "s01-estimator-validation", "src"),
          os.path.join(ROOT, "sessions", "s02-mechanism-expansion", "src")]:
    sys.path.insert(0, p)
import estimators2 as e2mod                    # noqa: E402
from fbm import CirculantEmbedding             # noqa: E402

RES = os.path.join(BASE, "results")
T, REPS = 2000, 200
PHI, SD = 0.98, 0.7
NUS = [3.0, 3.4, 4.5]
NSRS = [1e-5, 3e-5, 1e-4]
GEOMS = {390: [13, 26, 78, 195, 390], 1380: [23, 46, 138, 345, 1380]}
MASTERS = [int(x) for x in
           np.random.SeedSequence(20260820).generate_state(5)]


def empirical_profile(n):
    """Mean per-minute squared-return profile from the S04 ES panels."""
    geom = "RTH" if n == 390 else "GLOBEX"
    z = np.load(os.path.join(RES, f"panel_ES_{geom}_B0.npz"))
    g = z["logpx"].astype(np.float64)
    r2 = np.diff(g, axis=1) ** 2
    prof = r2.mean(axis=0)
    prof = np.concatenate([[prof[0]], prof])       # n returns -> n steps
    return prof / prof.mean()


def run_one(job):
    nu, nsr, n, m_list, master, idx = job
    rng = np.random.Generator(np.random.PCG64(
        np.random.SeedSequence([master, idx])))
    emb = CirculantEmbedding(PHI ** np.arange(T, dtype=float))
    prof = PROFILES[n]
    tscale = np.sqrt((nu - 2.0) / nu)              # unit-variance t
    sig_u = np.sqrt(nsr * np.exp(SD ** 2 / 2.0))
    recs = []
    lam = {(a, M): np.empty(REPS) for M in m_list
           for a in ["E1_a_L1-5", "E1_a_L1-10", "E1_d_L1-5", "E1_d_L1-10",
                     "E2", "E4"]}
    lam_true = {M: np.empty(REPS) for M in m_list}
    for rep in range(REPS):
        x = emb.sample(rng, size=1)[0] * SD
        iv = np.exp(x)
        step_sd = np.sqrt(np.outer(iv / n, prof))
        z = rng.standard_t(nu, size=(T, n)) * tscale
        r = (z * step_sd).astype(np.float64)
        path = np.concatenate([np.zeros((T, 1)), np.cumsum(r, axis=1)],
                              axis=1)
        path += rng.normal(0.0, sig_u, size=(T, n + 1))
        logiv = x            # profile mean 1 -> true IV = exp(x)
        for M in m_list:
            stride = n // M
            p = path[:, ::stride]
            if p.shape[1] == M:
                p = np.concatenate([p, path[:, -1:]], axis=1)
            rM = np.diff(p, axis=1)
            r2 = rM * rM
            rv = r2.sum(axis=1)
            rq = (M / 3.0) * (r2 * r2).sum(axis=1)
            h = M // 2
            rv1, rv2 = r2[:, :h].sum(axis=1), r2[:, h:].sum(axis=1)
            logrv = np.log(np.maximum(rv, 1e-300))
            lt = logiv.var() / logrv.var()
            lam_true[M][rep] = lt
            g = e2mod.e1_reduced(logrv)
            lam[("E1_a_L1-5", M)][rep] = g[("a_exp", "L1-5")]
            lam[("E1_a_L1-10", M)][rep] = g[("a_exp", "L1-10")]
            lam[("E1_d_L1-5", M)][rep] = g[("d_model", "L1-5")]
            lam[("E1_d_L1-10", M)][rep] = g[("d_model", "L1-10")]
            lam[("E2", M)][rep] = e2mod.e2(
                logrv, np.log(np.maximum(rv1, 1e-300)),
                np.log(np.maximum(rv2, 1e-300)))
            lam[("E4", M)][rep] = e2mod.e4(rv, rq, logrv, M)
    for M in m_list:
        for a in ["E1_a_L1-5", "E1_a_L1-10", "E1_d_L1-5", "E1_d_L1-10",
                  "E2", "E4"]:
            rec = lam[(a, M)] / lam_true[M]
            recs.append(dict(nu=nu, nsr=nsr, n=n, M=M, master=master,
                             estimator=a, mean_recovery=float(rec.mean()),
                             sd_recovery=float(rec.std())))
    return recs


PROFILES = {}


def main():
    t0 = time.time()
    for n in GEOMS:
        PROFILES[n] = empirical_profile(n)
    jobs = []
    idx = 0
    for nu in NUS:
        for nsr in NSRS:
            for n, m_list in GEOMS.items():
                for master in MASTERS:
                    jobs.append((nu, nsr, n, m_list, master, idx))
                    idx += 1
    print(f"Part F: {len(jobs)} datasets")
    rows = []
    with ProcessPoolExecutor(max_workers=6,
                             initializer=_init) as ex:
        for recs in ex.map(run_one, jobs):
            rows.extend(recs)
            if len(rows) % 600 == 0:
                print(f"  {len(rows)} rows, {time.time()-t0:.0f}s",
                      flush=True)
    F = pd.DataFrame(rows)
    F.to_csv(os.path.join(RES, "s05_partf_raw.csv"), index=False)
    curve = F.groupby(["nu", "nsr", "n", "M", "estimator"]).agg(
        recovery=("mean_recovery", "mean"),
        between_seed_sd=("mean_recovery", "std")).reset_index()
    curve.to_csv(os.path.join(RES, "s05_partf_curves.csv"), index=False)
    with open(os.path.join(RES, "s05_partf_seeds.json"), "w") as fh:
        json.dump(dict(master_root=20260820, masters=MASTERS,
                       scheme="PCG64(SeedSequence([master, dataset_index]))"),
                  fh, indent=1)
    print(f"Part F done: {len(curve)} curve points, {time.time()-t0:.0f}s")


def _init():
    for n in GEOMS:
        if n not in PROFILES:
            PROFILES[n] = empirical_profile(n)


if __name__ == "__main__":
    main()
