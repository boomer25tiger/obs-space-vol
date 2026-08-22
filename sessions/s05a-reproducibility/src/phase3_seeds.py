"""S05A Phase 3: MCS composition stability across 20 independent seeds.

S05 seeding (inspected, reported): `partde.py` line 224 creates ONE
`np.random.Generator(np.random.PCG64(20260821))` and passes it to every
`mcs()` call (line 263) in execution order. So the bootstrap is explicitly
seeded, not the global state, but the draw a given cell receives depends on
how much of the shared stream the preceding cells consumed. A per-cell seed
is therefore not recoverable and per-cell reproduction requires replaying
the whole loop in the identical order. Per DECISIONS item 18 we do not
attempt recovery; we measure composition stability across seeds instead.

The 20 seeds are `SeedSequence(20260821).generate_state(20)`, each used as
`PCG64(seed)` for one independent MCS of one cell.

Loss regeneration: `partde.build_series` / `partde.forecasts` / `qlike` are
imported from S05 unmodified and re-run on the same stored panels; Part D
is fully deterministic (fixed OLS refits, fixed-start Nelder-Mead), so the
loss matrices are identical to S05's by construction. No S05 artifact is
written.

MCS: same algorithm as S05's `mcs()` (range statistic, moving-block
bootstrap, b = ceil(T^(1/3)), 10,000 resamples). The only change is that
`rng.integers` is drawn in row-blocks to bound memory; PCG64 fills
row-major, so the concatenated draws are bit-identical to the single-shot
draw (asserted at import by `_assert_chunk_equivalence`).
"""

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
RES = os.path.join(BASE, "results")
S05 = os.path.join(ROOT, "sessions", "s05-reliability-mcs")
S05_RES = os.path.join(S05, "results")
sys.path.insert(0, os.path.join(S05, "src"))

import partde as pd5                                   # noqa: E402

MASTER = 20260821
N_SEEDS = 20
SEEDS = [int(s) for s in np.random.SeedSequence(MASTER).generate_state(N_SEEDS)]
BOOT_N = pd5.BOOT_N
MODELS = pd5.MODELS
QS = pd5.QS
CHUNK = 1000
GROUPS = [(root, geom, btag, horizon)
          for geom in ["GLOBEX", "RTH"] for root in ["ES", "NQ"]
          for btag in ["B0", "B1"]
          for horizon in ["1day", "1h", "30min"]]
SCHEMES = ["S-A"] + [f"S-{x}_q{q:.2f}" for x in ["B", "C"] for q in QS]


def _assert_chunk_equivalence():
    a = np.random.Generator(np.random.PCG64(7)).integers(0, 100,
                                                         size=(40, 13))
    g = np.random.Generator(np.random.PCG64(7))
    b = np.concatenate([g.integers(0, 100, size=(10, 13)) for _ in range(4)])
    assert np.array_equal(a, b), "chunked draw differs from single-shot"


_assert_chunk_equivalence()


def mcs_seeded(losses, seed):
    """S05's MCS with a fresh PCG64(seed); chunked bootstrap draw."""
    T, m = losses.shape
    b = int(np.ceil(T ** (1 / 3)))
    nblk = int(np.ceil(T / b))
    csum = np.vstack([np.zeros(m), np.cumsum(losses, axis=0)])
    blocksum = csum[b:] - csum[:-b]
    rng = np.random.Generator(np.random.PCG64(seed))
    boot_means = np.empty((BOOT_N, m))
    done = 0
    while done < BOOT_N:
        k = min(CHUNK, BOOT_N - done)
        st = rng.integers(0, T - b + 1, size=(k, nblk))
        boot_means[done:done + k] = blocksum[st].sum(axis=1) / (nblk * b)
        done += k
    means = losses.mean(axis=0)
    included = list(range(m))
    pvals = {}
    p_running = 0.0
    while len(included) > 1:
        idx = np.array(included)
        mu = means[idx]
        bm = boot_means[:, idx] - mu[None, :]
        dbar = mu[:, None] - mu[None, :]
        bd = bm[:, :, None] - bm[:, None, :]
        vd = np.maximum(bd.var(axis=0), 1e-30)
        tstat = np.abs(dbar) / np.sqrt(vd)
        TR = tstat.max()
        bt = np.abs(bd) / np.sqrt(vd)[None, :, :]
        TR_boot = bt.reshape(BOOT_N, -1).max(axis=1)
        p = float((TR_boot >= TR).mean())
        p_running = max(p_running, p)
        avg_t = (dbar / np.sqrt(vd)).sum(axis=1)
        worst = included[int(np.argmax(avg_t))]
        pvals[worst] = p_running
        included.remove(worst)
    pvals[included[0]] = 1.0
    return pvals


def prep_group(g):
    """Regenerate the loss matrix and scheme masks for one group."""
    root, geom, btag, horizon = g
    t0 = time.time()
    z = np.load(os.path.join(S05_RES, f"panel_{root}_{geom}_{btag}.npz"))
    grid = z["logpx"].astype(np.float64)
    wlen = {"1day": None, "1h": 60, "30min": 30}[horizon]
    S = pd5.build_series(grid, wlen)
    D = S["nw"]
    warm = 500 if horizon == "1day" else max(500, 22 * D + 100)
    refit = 1 if horizon == "1day" else D
    F, start, nonconv = pd5.forecasts(S, D, warm, refit, horizon == "1day")
    rv = S["rv"]
    ok = np.ones(len(rv), bool)
    for m in MODELS:
        ok &= np.isfinite(F[m])
    ok[:max(start, warm)] = False
    rvv = rv[ok]
    Fm = {m: F[m][ok] for m in MODELS}
    L = np.column_stack([pd5.qlike(Fm[m], rvv) for m in MODELS])
    masks = {"S-A": np.ones(len(rvv), bool)}
    for q in QS:
        masks[f"S-B_q{q:.2f}"] = rvv > np.quantile(rvv, q)
        fc = Fm["M2_HAR"]
        masks[f"S-C_q{q:.2f}"] = fc > np.quantile(fc, q)
    out = os.path.join(RES, "cache",
                       f"loss_{root}_{geom}_{btag}_{horizon}.npz")
    np.savez_compressed(out, L=L.astype(np.float64),
                        **{f"mask_{k}": v for k, v in masks.items()})
    return dict(group="/".join(g), n_obs=int(len(rvv)),
                elapsed_s=round(time.time() - t0, 1), m5_nonconv=int(nonconv))


def run_cell(job):
    """20 seeds of MCS for one (group, scheme) cell."""
    root, geom, btag, horizon, scheme = job
    t0 = time.time()
    z = np.load(os.path.join(RES, "cache",
                             f"loss_{root}_{geom}_{btag}_{horizon}.npz"))
    L = z["L"]
    mask = z[f"mask_{scheme}"]
    Ls = L[mask]
    comps75, comps90, rows = [], [], []
    for si, seed in enumerate(SEEDS):
        pv = mcs_seeded(Ls, seed)
        s75 = "|".join(sorted(MODELS[i] for i, p in pv.items() if p > .25))
        s90 = "|".join(sorted(MODELS[i] for i, p in pv.items() if p > .10))
        comps75.append(s75)
        comps90.append(s90)
        rows.append(dict(cell_id=f"{root}/{geom}/{btag}/{horizon}/{scheme}",
                         seed_index=si, seed=seed, n_obs=int(mask.sum()),
                         mcs75=s75, mcs90=s90,
                         pvals=json.dumps({MODELS[i]: round(p, 4)
                                           for i, p in pv.items()})))
    def modal(c):
        vc = pd.Series(c).value_counts()
        return vc.index[0], int(vc.iloc[0]), int(len(vc))
    m75, f75, d75 = modal(comps75)
    m90, f90, d90 = modal(comps90)
    summ = dict(cell_id=f"{root}/{geom}/{btag}/{horizon}/{scheme}",
                root=root, geom=geom, btag=btag, horizon=horizon,
                scheme=scheme, n_obs=int(mask.sum()),
                n_distinct_75=d75, modal_75=m75, modal_freq_75=f75,
                n_distinct_90=d90, modal_90=m90, modal_freq_90=f90,
                all_75=json.dumps(sorted(set(comps75))),
                all_90=json.dumps(sorted(set(comps90))),
                elapsed_s=round(time.time() - t0, 1))
    return summ, rows


def main():
    t0 = time.time()
    os.makedirs(os.path.join(RES, "cache"), exist_ok=True)

    # ---- fixed execution order, written BEFORE any cell computation
    sb_sc = sorted(f"{r}/{g}/{b}/{h}/{s}" for (r, g, b, h) in GROUPS
                   for s in SCHEMES if s != "S-A")
    s_a = sorted(f"{r}/{g}/{b}/{h}/S-A" for (r, g, b, h) in GROUPS)
    order = sb_sc + s_a
    with open(os.path.join(RES, "S05A-runlog.md"), "w") as fh:
        fh.write("# Session 5A run log\n\n## Phase 3 fixed execution "
                 "order (written before the first cell computation)\n\n"
                 f"Master seed {MASTER}; the 20 seeds are "
                 f"`SeedSequence({MASTER}).generate_state(20)` = "
                 f"{SEEDS}.\n\nEvery S-B / S-C cell runs before every S-A "
                 f"cell; within each stage, ascending cell identifier "
                 f"under lexical sort. {len(sb_sc)} S-B/S-C cells then "
                 f"{len(s_a)} S-A cells, {len(order)} total, 20 seeds "
                 f"each = {len(order)*20} MCS computations.\n\n```text\n"
                 + "\n".join(f"{i+1:3d}. {c}" for i, c in enumerate(order))
                 + "\n```\n")
    print(f"order written: {len(order)} cells", flush=True)

    # ---- stage 0: regenerate losses once per group (shared input)
    prep = []
    with ProcessPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(prep_group, g): g for g in GROUPS}
        for f in as_completed(futs):
            prep.append(f.result())
            print(f"  prepped {len(prep)}/{len(GROUPS)}: "
                  f"{prep[-1]['group']} n={prep[-1]['n_obs']} "
                  f"({prep[-1]['elapsed_s']}s)", flush=True)
    with open(os.path.join(RES, "phase3_prep.json"), "w") as fh:
        json.dump(dict(groups=prep, seconds=round(time.time() - t0, 1)),
                  fh, indent=1)
    print(f"losses ready at {time.time()-t0:.0f}s", flush=True)

    # ---- stages 1 and 2, in the fixed order
    summaries, allrows = [], []
    for stage, cells in [("stage1_SB_SC", sb_sc), ("stage2_SA", s_a)]:
        jobs = [tuple(c.split("/")) for c in cells]
        with ProcessPoolExecutor(max_workers=6) as ex:
            for summ, rows in ex.map(run_cell, jobs):
                summaries.append(summ)
                allrows.extend(rows)
                if len(summaries) % 20 == 0:
                    print(f"  {len(summaries)}/{len(order)} cells "
                          f"({time.time()-t0:.0f}s)", flush=True)
        print(f"{stage} complete at {time.time()-t0:.0f}s", flush=True)

    S = pd.DataFrame(summaries)
    S.to_csv(os.path.join(RES, "S05A-mcs-stability.csv"), index=False)
    pd.DataFrame(allrows).to_csv(
        os.path.join(RES, "S05A-mcs-per-seed.csv"), index=False)

    # ---- compare against S05's reported compositions
    rep = pd.read_csv(os.path.join(S05_RES, "s05_mcs.csv"))
    rep["cell_id"] = (rep.root + "/" + rep.geom + "/" + rep.btag + "/"
                      + rep.horizon + "/" + rep.scheme)
    rep = rep.set_index("cell_id")
    hit75, hit90 = [], []
    for _, r in S.iterrows():
        rr = rep.loc[r.cell_id]
        a75 = set(json.loads(r.all_75))
        a90 = set(json.loads(r.all_90))
        hit75.append(str(rr.mcs75) in a75)
        hit90.append(str(rr.mcs90) in a90)
    S["s05_75_in_seed_set"] = hit75
    S["s05_90_in_seed_set"] = hit90
    S["s05_mcs75"] = [str(rep.loc[c].mcs75) for c in S.cell_id]
    S["s05_mcs90"] = [str(rep.loc[c].mcs90) for c in S.cell_id]
    S.to_csv(os.path.join(RES, "S05A-mcs-stability.csv"), index=False)

    # ---- primary result: is the S-B vs S-C difference seed-invariant?
    # Seed-by-seed: for each (cell, quantile, level) compare the S-B and
    # S-C composition under the SAME seed index, 20 times.
    per = pd.read_csv(os.path.join(RES, "S05A-mcs-per-seed.csv"))
    per["key"] = per.cell_id.str.rsplit("/", n=1).str[0]
    per["scheme"] = per.cell_id.str.rsplit("/", n=1).str[1]
    prim_rows = []
    for (key, q, lev) in [(k, q, l) for k in sorted(per.key.unique())
                          for q in QS for l in ["mcs75", "mcs90"]]:
        pb = per[(per.key == key) & (per.scheme == f"S-B_q{q:.2f}")]
        pc = per[(per.key == key) & (per.scheme == f"S-C_q{q:.2f}")]
        if not len(pb) or not len(pc):
            continue
        pb = pb.sort_values("seed_index")[lev].values
        pc = pc.sort_values("seed_index")[lev].values
        differs = [pb[i] != pc[i] for i in range(len(pb))]
        prim_rows.append(dict(
            cell=key, quantile=q, level=lev,
            n_seeds=len(pb), n_seeds_differ=int(sum(differs)),
            invariant=bool(all(differs) or not any(differs)),
            verdict=("DIFFERS in all seeds" if all(differs)
                     else "IDENTICAL in all seeds" if not any(differs)
                     else "INDETERMINATE (varies across seeds)")))
    P = pd.DataFrame(prim_rows)
    P.to_csv(os.path.join(RES, "S05A-primary-invariance.csv"), index=False)
    print(P.verdict.value_counts().to_string())
    print(f"PHASE3 DONE {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
