"""S02 full crossed grid runner.

24,500 datasets = 7 latents x 7 within-window configs x 50 contamination
combinations x 2 geometries x 5 master seeds, priority-ordered
C0 -> C2 -> C1 -> C3 so the pre-registered primary output (the NSR
threshold map at zero jump share) completes first. Each dataset: 200
replications of T = 2000 windows at 4 sampling frequencies, 54 estimator
outputs per (replication, M). Seeds logged per dataset; writes are atomic.
"""

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
from scipy.signal import fftconvolve

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import estimators2 as e2mod
import proxies_robust as px
from dgp2 import (GEOMETRIES, build_embedding, build_param_grid,
                  diurnal_profile, simulate_day_chunk, simulate_latent,
                  contamination_class)
from estimators2 import E1_KEYS, safe_log

T_WINDOWS = 2000
REPS = 200
MASTER_ROOT = 20260819
N_MASTERS = 5
DAY_CHUNK = 250

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE, "results", "raw")
LOG_DIR = os.path.join(BASE, "logs")

PROXIES = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
E4_PROXIES = ["P1", "P4", "P5", "P6", "P7", "P8"]   # matching quarticity exists

ARM_NAMES = (
    [f"E1_{a}_{ls}_{p}" for p in PROXIES for (a, ls) in E1_KEYS]
    + [f"E2_{p}" for p in PROXIES]
    + [f"E4_{p}" for p in E4_PROXIES]
    + ["E5", "E6",
       "E6pre_E1_a_L1-5", "E6pre_E1_a_L1-10",
       "E6pre_E1_d_L1-5", "E6pre_E1_d_L1-10",
       "E6pre_E2", "E6pre_E4"]
)
N_ARMS = len(ARM_NAMES)          # 54
ARM_IDX = {a: i for i, a in enumerate(ARM_NAMES)}
# lambda_true index used for each arm's recovery ratio (P1-based for E5/E6)
ARM_TRUE_PROXY = (
    [p for p in PROXIES for _ in E1_KEYS]
    + list(PROXIES) + list(E4_PROXIES)
    + ["P1"] * 8
)


def kernel_flattop_fft(r, H):
    """Flat-top Parzen kernel via convolution: sum_h w_h gamma_h computed as
    row-wise correlation of r with the weight vector (identical math to
    px.p3_kernel_flattop, evaluated by FFT for large H)."""
    if H <= 4:
        return px.p3_kernel_flattop(r, H)
    w = px.parzen((np.arange(1, H + 1) - 1.0) / H)
    rf = r.astype(np.float64)
    conv = fftconvolve(rf, w[None, ::-1], mode="full", axes=1)
    lagged = conv[:, H:rf.shape[1]]        # sum_h w_h r_{i+h} for valid i
    out = (rf * rf).sum(axis=1)
    out += 2.0 * (rf[:, :lagged.shape[1]] * lagged).sum(axis=1)
    return out


def med3(a, b, c):
    """Median of three arrays without sorting: a+b+c - min - max."""
    return a + b + c - np.minimum(np.minimum(a, b), c) \
        - np.maximum(np.maximum(a, b), c)


def medrv_fast(r):
    T, M = r.shape
    a = np.abs(r).astype(np.float64)
    med = med3(a[:, :-2], a[:, 1:-1], a[:, 2:])
    c = np.pi / (6.0 - 4.0 * np.sqrt(3.0) + np.pi)
    return c * (M / (M - 2.0)) * (med * med).sum(axis=1)


def proxy_suite(r, M, full=True):
    """All eight proxies plus quarticities and rule values for one grid.

    The pre-averaged quantities share one _preav_bars computation and are
    algebraically identical to the px.p4_preav / p4_preav_quarticity /
    p8_preav_truncated reference implementations (V2 validates this suite
    directly). full=False (used for the E2 half-windows, which only need
    the proxies themselves) skips the quarticities TQ and PQ.
    """
    rv = px.p1_rv(r)
    rq_v = px.rq(r, M)
    bv = px.p5_bipower(r)
    mean_rv = float(rv.mean())
    omega2_hat = mean_rv / (2.0 * M)            # BNHLS/ZMA dense-RV rule
    iq_hat = float(rq_v.mean())
    K = px.tsrv_K(M, omega2_hat, iq_hat)
    p = np.concatenate([np.zeros((r.shape[0], 1), dtype=r.dtype),
                        np.cumsum(r, axis=1)], axis=1)
    tsrv = px.p2_tsrv(p, K)
    H = px.kernel_H(M, omega2_hat, mean_rv)     # IV_hat = sparse-scale RV
    kern = kernel_flattop_fft(r, H)
    kn = px.preav_kn(M)

    # shared pre-averaging pieces (JLMPV 2009; CKP 2010 adjustment)
    zb, g = px._preav_bars(r, kn)
    psi1, psi2 = px._preav_consts(kn, g)
    adj = px._preav_fs_adjustment(kn, psi1, psi2)
    delta = 1.0 / M
    theta = kn * np.sqrt(delta)
    c1 = np.sqrt(delta) / (theta * psi2)
    c2 = psi1 * delta / (2.0 * theta ** 2 * psi2)
    zb2 = zb * zb
    s2 = (r.astype(np.float64) ** 2).sum(axis=1)
    preav = adj * (c1 * zb2.sum(axis=1) - c2 * s2)
    scale = np.median(np.abs(zb), axis=1) / 0.6744897501960817
    zt2 = np.where(np.abs(zb) <= (3.0 * scale)[:, None], zb2, 0.0)
    ptrv = adj * (c1 * zt2.sum(axis=1) - c2 * s2)

    medrv = medrv_fast(r)
    trv = px.p7_truncated(r, local_var=bv)
    out = dict(P1=rv, P2=tsrv, P3=kern, P4=preav, P5=bv, P6=medrv,
               P7=trv, P8=ptrv, RQ=rq_v, rules=(K, H, kn))
    if full:
        r2 = (r.astype(np.float64)) ** 2
        cs = np.concatenate([np.zeros((r.shape[0], 1)),
                             np.cumsum(r2, axis=1)], axis=1)
        nbar = zb.shape[1]
        lo = np.arange(nbar) + kn
        hi = np.minimum(lo + kn, M)
        valid = lo < M
        win = cs[:, hi[valid]] - cs[:, lo[valid]]
        t1 = (zb2 * zb2).sum(axis=1) / (3.0 * theta ** 2 * psi2 ** 2)
        t2 = (zb2[:, valid] * win).sum(axis=1) \
            * delta * psi1 / (theta ** 4 * psi2 ** 2)
        t3 = (r2[:, :-2] * r2[:, 2:]).sum(axis=1) \
            * delta * psi1 ** 2 / (4.0 * theta ** 4 * psi2 ** 2)
        out["PQ"] = t1 - t2 + t3
        out["TQ"] = px.tripower_quarticity(r, M)
    return out


Q_FOR = {"P1": "RQ", "P4": "PQ", "P5": "TQ", "P6": "TQ", "P7": "TQ",
         "P8": "PQ"}


def run_dataset(job):
    cfg, n, m_list, master_seed, ds_index, tag = (
        job["cfg"], job["n"], job["m_list"], job["master_seed"],
        job["ds_index"], job["tag"])
    t0 = time.time()
    ss = np.random.SeedSequence([master_seed, ds_index])
    rng = np.random.Generator(np.random.PCG64(ss))
    emb = build_embedding(cfg, T_WINDOWS)
    profile = diurnal_profile(n, cfg.ptt if cfg.w in ("W1", "W2") else 1.0)

    nM = len(m_list)
    lam = np.full((N_ARMS, nM, REPS), np.nan, dtype=np.float32)
    lam_true = np.full((len(PROXIES), nM, REPS), np.nan, dtype=np.float32)
    rules_log = np.zeros((nM, 3), dtype=np.int64)
    floor_counter = [0]
    omega2_e5_sum = 0.0

    strides = {M: n // M for M in m_list}
    m_finest = max(m_list)

    for rep in range(REPS):
        x = simulate_latent(cfg, emb, rng)
        iv_true = np.empty(T_WINDOWS)
        rM = {M: np.empty((T_WINDOWS, M), dtype=np.float32) for M in m_list}
        for lo in range(0, T_WINDOWS, DAY_CHUNK):
            hi = min(lo + DAY_CHUNK, T_WINDOWS)
            tiv, path = simulate_day_chunk(cfg, x[lo:hi], n, profile, rng)
            iv_true[lo:hi] = tiv
            for M in m_list:
                b = path[:, ::strides[M]]
                rM[M][lo:hi] = np.diff(b, axis=1)
        log_iv = np.log(np.maximum(iv_true, e2mod.LOG_FLOOR))
        var_x = log_iv.var()

        # E6 noise estimate from the finest grid, once per replication.
        rv_finest = px.p1_rv(rM[m_finest])
        om2_t = e2mod.e6_omega2(rv_finest, m_finest)

        rv_by_m, log_rv_by_m = {}, {}
        for mi, M in enumerate(m_list):
            r = rM[M]
            S = proxy_suite(r, M)
            rules_log[mi] = S["rules"]
            h = M // 2
            SH1 = proxy_suite(r[:, :h], h, full=False)
            SH2 = proxy_suite(r[:, h:], M - h, full=False)
            rv_by_m[M] = S["P1"]

            logs = {}
            for p in PROXIES:
                logs[p] = safe_log(S[p], floor_counter)
                pi = PROXIES.index(p)
                lam_true[pi, mi, rep] = var_x / logs[p].var()
                grid = e2mod.e1_reduced(logs[p])
                for (a, ls) in E1_KEYS:
                    lam[ARM_IDX[f"E1_{a}_{ls}_{p}"], mi, rep] = grid[(a, ls)]
                lam[ARM_IDX[f"E2_{p}"], mi, rep] = e2mod.e2(
                    logs[p],
                    safe_log(SH1[p], floor_counter),
                    safe_log(SH2[p], floor_counter))
            for p in E4_PROXIES:
                lam[ARM_IDX[f"E4_{p}"], mi, rep] = e2mod.e4(
                    S[p], S[Q_FOR[p]], logs[p], M)
            log_rv_by_m[M] = logs["P1"]

            # ---- E6: Hansen-Lunde correction (P1-based)
            rvc = e2mod.e6_correct(S["P1"], M, om2_t, floor_counter)
            log_rvc = np.log(rvc)
            lam[ARM_IDX["E6"], mi, rep] = log_rvc.var() / logs["P1"].var()
            grid_c = e2mod.e1_reduced(log_rvc)
            lam[ARM_IDX["E6pre_E1_a_L1-5"], mi, rep] = grid_c[("a_exp", "L1-5")]
            lam[ARM_IDX["E6pre_E1_a_L1-10"], mi, rep] = grid_c[("a_exp", "L1-10")]
            lam[ARM_IDX["E6pre_E1_d_L1-5"], mi, rep] = grid_c[("d_model", "L1-5")]
            lam[ARM_IDX["E6pre_E1_d_L1-10"], mi, rep] = grid_c[("d_model", "L1-10")]
            h1c = e2mod.e6_correct(SH1["P1"], h, om2_t, floor_counter)
            h2c = e2mod.e6_correct(SH2["P1"], M - h, om2_t, floor_counter)
            lam[ARM_IDX["E6pre_E2"], mi, rep] = e2mod.e2(
                log_rvc, np.log(h1c), np.log(h2c))
            lam[ARM_IDX["E6pre_E4"], mi, rep] = e2mod.e4(
                rvc, S["RQ"], log_rvc, M)

        lam_e5, om2_e5 = e2mod.e5_signature(rv_by_m, m_list, log_rv_by_m,
                                            floor_counter)
        omega2_e5_sum += om2_e5
        for mi, M in enumerate(m_list):
            lam[ARM_IDX["E5"], mi, rep] = lam_e5[M]

    out = os.path.join(RAW_DIR, f"{tag}.npz")
    tmp = out + ".tmp.npz"
    np.savez_compressed(
        tmp, lam=lam, lam_true=lam_true, m_list=np.array(m_list), n=n,
        rules=rules_log, dgp=cfg.dgp, family=cfg.family, shape=cfg.shape,
        w=cfg.w, ptt=cfg.ptt, jump_share=cfg.jump_share, nsr=cfg.nsr,
        master_seed=master_seed, ds_index=ds_index,
        omega2_e5=omega2_e5_sum / REPS)
    os.replace(tmp, out)
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
                                 tag=tag,
                                 cclass=contamination_class(cfg.jump_share,
                                                            cfg.nsr)))
                ds_index += 1
    return jobs, masters


def main(limit=None, workers=6):
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    jobs, masters = build_jobs()
    done = {f[:-4] for f in os.listdir(RAW_DIR) if f.endswith(".npz")}
    jobs = [j for j in jobs if j["tag"] not in done]
    if limit:
        jobs = jobs[:int(limit)]
    total = len(jobs)
    print(f"master seeds: {[int(m) for m in masters]}", flush=True)
    print(f"jobs to run: {total} (done: {len(done)}, grand total 24500)",
          flush=True)
    t_start = time.time()
    prog_path = os.path.join(LOG_DIR, "progress.jsonl")
    with ProcessPoolExecutor(max_workers=workers) as ex, \
            open(prog_path, "a") as prog:
        futures = {ex.submit(run_dataset, j): j for j in jobs}
        n_done = 0
        for fut in as_completed(futures):
            res = fut.result()
            n_done += 1
            res["t_wall"] = time.time() - t_start
            prog.write(json.dumps(res) + "\n")
            prog.flush()
            if n_done % 25 == 0 or n_done == total:
                rate = res["t_wall"] / n_done
                print(f"[{n_done}/{total}] {res['tag']} "
                      f"({res['elapsed']:.1f}s) ETA {(total-n_done)*rate/60:.0f} min",
                      flush=True)
    print(f"grid segment complete in {(time.time()-t_start)/60:.1f} min",
          flush=True)


if __name__ == "__main__":
    lim = sys.argv[1] if len(sys.argv) > 1 else None
    wk = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    main(limit=lim, workers=wk)
