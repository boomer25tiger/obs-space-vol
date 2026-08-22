"""Phase-4 full grid run.

1050 datasets = 105 DGP parameter combinations x 2 geometries x 5 master
seeds; each dataset is 200 replications of T = 2000 daily windows, evaluated
at 4 sampling frequencies. Per-dataset seeds are derived deterministically
from the master seed and the dataset index and are logged in
logs/progress.jsonl. Raw per-replication estimates are written to
results/raw/ for aggregation.
"""

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import estimators as est
from dgp import (GEOMETRIES, build_embedding, build_param_grid, fou_rho,
                 simulate_day_chunk, simulate_latent)
from proxies import bipower, ohlc_proxies, rv_stats, safe_log

DAY_CHUNK = 250  # days simulated per intraday chunk (memory ceiling)

T_WINDOWS = 2000
REPS = 200
MASTER_ROOT = 20260818
N_MASTERS = 5

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # session dir
RAW_DIR = os.path.join(BASE, "results", "raw")
LOG_DIR = os.path.join(BASE, "logs")

PROXY_NAMES = ["RV_M0", "RV_M1", "RV_M2", "RV_M3", "BV", "PARK", "GK", "RS",
               "OC2"]
PARK_IDX, GK_IDX = 5, 6
N_PROX = 9
ARM_KEYS = [(arm, ls) for arm in est.ARMS for ls in est.LAG_SETS]  # 16, fixed order


def run_dataset(job):
    cfg, n, m_list, master_seed, ds_index, tag = (
        job["cfg"], job["n"], job["m_list"], job["master_seed"],
        job["ds_index"], job["tag"])
    t0 = time.time()
    ss = np.random.SeedSequence([master_seed, ds_index])
    rng = np.random.Generator(np.random.PCG64(ss))
    emb = build_embedding(cfg, T_WINDOWS)

    nM = len(m_list)
    lam_true = np.empty((nM, REPS))
    lam_e1 = np.empty((16, nM, REPS))
    lam_e2 = np.empty((nM, REPS))
    lam_e4 = np.empty((nM, REPS))
    yvar = np.empty((N_PROX, REPS), dtype=np.float32)
    pairvar = np.empty((N_PROX, N_PROX, REPS), dtype=np.float32)
    errcorr = np.empty((N_PROX, N_PROX, REPS), dtype=np.float32)
    floor_counter = [0]

    fine_M = max(m_list)
    daily = {k: np.empty(T_WINDOWS)
             for k in ["bv", "park", "gk", "rs", "oc2"]}
    rv_d = {M: np.empty(T_WINDOWS) for M in m_list}
    rq_d = {M: np.empty(T_WINDOWS) for M in m_list}
    h1_d = {M: np.empty(T_WINDOWS) for M in m_list}
    h2_d = {M: np.empty(T_WINDOWS) for M in m_list}

    for rep in range(REPS):
        x = simulate_latent(cfg, emb, rng)
        var_x = x.var()
        iv = np.exp(x)

        for lo in range(0, T_WINDOWS, DAY_CHUNK):
            hi = min(lo + DAY_CHUNK, T_WINDOWS)
            path = simulate_day_chunk(cfg, iv[lo:hi], n, rng)
            park, gk, rs, oc2 = ohlc_proxies(path)
            daily["park"][lo:hi] = park
            daily["gk"][lo:hi] = gk
            daily["rs"][lo:hi] = rs
            daily["oc2"][lo:hi] = oc2
            daily["bv"][lo:hi] = bipower(path, fine_M)
            for M in m_list:
                rv, rq, rv_h1, rv_h2 = rv_stats(path, M)
                rv_d[M][lo:hi] = rv
                rq_d[M][lo:hi] = rq
                h1_d[M][lo:hi] = rv_h1
                h2_d[M][lo:hi] = rv_h2

        Y = np.empty((T_WINDOWS, N_PROX))
        Y[:, 4] = safe_log(daily["bv"], floor_counter)
        Y[:, 5] = safe_log(daily["park"], floor_counter)
        Y[:, 6] = safe_log(daily["gk"], floor_counter)
        Y[:, 7] = safe_log(daily["rs"], floor_counter)
        Y[:, 8] = safe_log(daily["oc2"], floor_counter)

        for mi, M in enumerate(m_list):
            rv, rq = rv_d[M], rq_d[M]
            logrv = safe_log(rv, floor_counter)
            Y[:, mi] = logrv
            lam_true[mi, rep] = var_x / logrv.var()
            grid = est.e1_grid(logrv)
            for ai, key in enumerate(ARM_KEYS):
                lam_e1[ai, mi, rep] = grid[key]
            lam_e2[mi, rep] = est.e2(logrv,
                                     safe_log(h1_d[M], floor_counter),
                                     safe_log(h2_d[M], floor_counter))
            lam_e4[mi, rep] = est.e4(rv, rq, logrv, M)

        yv, pv, ec = est.e3_moments(Y, x)
        yvar[:, rep] = yv
        pairvar[:, :, rep] = pv
        errcorr[:, :, rep] = ec

    out = os.path.join(RAW_DIR, f"{tag}.npz")
    np.savez_compressed(
        out, lam_true=lam_true, lam_e1=lam_e1, lam_e2=lam_e2, lam_e4=lam_e4,
        yvar=yvar, pairvar=pairvar, errcorr=errcorr,
        m_list=np.array(m_list), n=n,
        dgp=cfg.dgp, family=cfg.family, shape=cfg.shape, sd=cfg.sd,
        jump_share=cfg.jump_share, nsr=cfg.nsr,
        master_seed=master_seed, ds_index=ds_index)
    return dict(tag=tag, elapsed=time.time() - t0,
                neg_eig_count=emb.neg_eig_count, min_eig=emb.min_eig,
                floor_hits=floor_counter[0], master_seed=int(master_seed),
                ds_index=ds_index,
                seed_entropy=str([master_seed, ds_index]))


def build_jobs():
    cfgs = build_param_grid()
    masters = np.random.SeedSequence(MASTER_ROOT).generate_state(N_MASTERS)
    jobs = []
    ds_index = 0
    for cfg in cfgs:
        for n, m_list in GEOMETRIES.items():
            for si, master in enumerate(masters):
                tag = f"{cfg.label()}_g{n}_seed{si}"
                jobs.append(dict(cfg=cfg, n=n, m_list=m_list,
                                 master_seed=int(master), ds_index=ds_index,
                                 tag=tag))
                ds_index += 1
    return jobs, masters


def main(limit=None, workers=7):
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    # Precompute the cached fOU acf tables in the parent so workers reuse them.
    for H in [0.08, 0.10, 0.16, 0.30, 0.50]:
        fou_rho(H, T_WINDOWS)

    jobs, masters = build_jobs()
    done_tags = {f[:-4] for f in os.listdir(RAW_DIR) if f.endswith(".npz")}
    jobs = [j for j in jobs if j["tag"] not in done_tags]
    if limit:
        jobs = jobs[:int(limit)]
    total = len(jobs)
    print(f"master seeds: {[int(m) for m in masters]}", flush=True)
    print(f"jobs to run: {total} (already done: {len(done_tags)})", flush=True)

    t_start = time.time()
    prog_path = os.path.join(LOG_DIR, "progress.jsonl")
    with ProcessPoolExecutor(max_workers=workers) as ex, \
            open(prog_path, "a") as prog:
        futures = {ex.submit(run_dataset, j): j["tag"] for j in jobs}
        n_done = 0
        for fut in as_completed(futures):
            res = fut.result()
            n_done += 1
            res["t_wall"] = time.time() - t_start
            prog.write(json.dumps(res) + "\n")
            prog.flush()
            if n_done % 10 == 0 or n_done == total:
                rate = res["t_wall"] / n_done
                eta = rate * (total - n_done)
                print(f"[{n_done}/{total}] {res['tag']} "
                      f"({res['elapsed']:.1f}s) ETA {eta/60:.1f} min",
                      flush=True)
    print(f"grid complete in {(time.time()-t_start)/60:.1f} min", flush=True)


if __name__ == "__main__":
    lim = sys.argv[1] if len(sys.argv) > 1 else None
    wk = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    main(limit=lim, workers=wk)
