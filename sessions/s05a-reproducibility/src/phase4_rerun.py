"""S05A Phase 4: targeted re-run verification of one cell per Part.

Selection rule (applied and logged before any re-run): within each Part,
the cell with the smallest input row count, ties broken by ascending cell
identifier under lexical sort.

Re-run method. Parts A and C are cheap (13 s and 5 s in S05), so rather
than re-implementing one cell we re-execute S05's own `parta.main()` and
`partc.main()` with `RES` redirected to a scratch directory (threads
pinned to 1). No S05 artifact is written. The selected cell is then
compared field by field at full precision, and, as a superset check, every
cell of both Parts is compared too.

Part E cannot be verified bitwise by construction: S05 drew its bootstrap
from a single shared PCG64 stream consumed in execution order (Phase 3),
so an isolated re-run of one cell cannot receive the same draw. What IS
deterministic in Part E - the loss matrix, n_obs and the per-model mean
QLIKE that the MCS consumes - is re-run and compared at full precision,
and the composition is checked against the Phase 3 seed set.
"""

import json
import os
import shutil
import sys
import time

for _v in ["OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ[_v] = "1"

import numpy as np                                      # noqa: E402
import pandas as pd                                     # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
RES = os.path.join(BASE, "results")
S05 = os.path.join(ROOT, "sessions", "s05-reliability-mcs")
S05_RES = os.path.join(S05, "results")
TMP = os.path.join(RES, "p4tmp")
sys.path.insert(0, os.path.join(S05, "src"))


def select_cells():
    A = pd.read_csv(os.path.join(S05_RES, "s05_parta.csv"))
    A["cell_id"] = (A.root + "/" + A.geom + "/" + A.btag + "/M"
                    + A.M.astype(str) + "/" + A.variant + "/y"
                    + A.year.astype(str))
    a = A.sort_values(["n", "cell_id"]).iloc[0]

    C = pd.read_csv(os.path.join(S05_RES, "s05_partc.csv"))
    C["cell_id"] = (C.root + "/" + C.geom + "/" + C.btag + "/" + C.horizon
                    + "/M" + C.M.astype(str) + "/y" + C.year.astype(str)
                    + "/t" + C.tercile.astype(str))
    Cc = C.groupby("cell_id", as_index=False).agg(n=("n", "first"))
    c = Cc.sort_values(["n", "cell_id"]).iloc[0]

    E = pd.read_csv(os.path.join(S05_RES, "s05_mcs.csv"))
    E["cell_id"] = (E.root + "/" + E.geom + "/" + E.btag + "/" + E.horizon
                    + "/" + E.scheme)
    e = E.sort_values(["n_obs", "cell_id"]).iloc[0]
    return (dict(part="A", cell_id=a.cell_id, input_rows=int(a.n)),
            dict(part="C", cell_id=c.cell_id, input_rows=int(c.n)),
            dict(part="E", cell_id=e.cell_id, input_rows=int(e.n_obs)))


def cmp_frames(new, old, keys, valcols, label):
    m = new.merge(old, on=keys, suffixes=("_new", "_old"))
    out = {"label": label, "n_rows_compared": int(len(m)),
           "n_rows_new": int(len(new)), "n_rows_old": int(len(old))}
    worst = {}
    for c in valcols:
        a = m[f"{c}_new"].values.astype(float)
        b = m[f"{c}_old"].values.astype(float)
        fin = np.isfinite(a) & np.isfinite(b)
        exact = int((a[fin] == b[fin]).sum())
        denom = np.maximum(np.abs(b[fin]), 1e-300)
        rel = np.abs(a[fin] - b[fin]) / denom
        worst[c] = dict(n=int(fin.sum()), n_bitwise_identical=exact,
                        max_abs_diff=float(np.abs(a[fin] - b[fin]).max())
                        if fin.any() else 0.0,
                        max_rel_diff=float(rel.max()) if fin.any() else 0.0)
    out["columns"] = worst
    out["all_bitwise_identical"] = all(
        v["n_bitwise_identical"] == v["n"] for v in worst.values())
    return out


def main():
    t0 = time.time()
    sels = select_cells()
    with open(os.path.join(RES, "phase4_selection.json"), "w") as fh:
        json.dump(dict(rule="smallest input row count within each Part; "
                            "ties by ascending cell identifier, lexical",
                       selected=list(sels)), fh, indent=1)
    with open(os.path.join(RES, "S05A-runlog.md"), "a") as fh:
        fh.write("\n## Phase 4 selected verification cells "
                 "(written before any re-run)\n\n"
                 "| Part | cell identifier | input rows |\n|---|---|---|\n")
        for s in sels:
            fh.write(f"| {s['part']} | `{s['cell_id']}` | "
                     f"{s['input_rows']} |\n")
    print(json.dumps(list(sels), indent=1), flush=True)

    os.makedirs(TMP, exist_ok=True)
    for f in os.listdir(S05_RES):
        if f.startswith("panel_") or f == "s05_variant_selection.json":
            shutil.copy2(os.path.join(S05_RES, f), os.path.join(TMP, f))

    report = dict(selection=list(sels), threads="all *_NUM_THREADS = 1")

    # ---------------- Part A re-run
    import parta
    parta.RES = TMP
    t = time.time()
    parta.main()
    report["partA_rerun_seconds"] = round(time.time() - t, 1)
    Anew = pd.read_csv(os.path.join(TMP, "s05_parta.csv"))
    Aold = pd.read_csv(os.path.join(S05_RES, "s05_parta.csv"))
    keys = ["root", "geom", "btag", "M", "variant", "year"]
    vals = ["median", "iqr", "p95", "p99", "share_gt10x_med",
            "med_over_ref", "acf1", "acf5", "acf10"]
    report["partA_all_cells"] = cmp_frames(Anew, Aold, keys, vals,
                                           "Part A, every cell")
    sa = sels[0]
    r, g, b, M, var, y = sa["cell_id"].replace("M", "", 1).split("/")
    Mv = int(sa["cell_id"].split("/M")[1].split("/")[0])
    yv = int(sa["cell_id"].split("/y")[1])
    varv = sa["cell_id"].split("/")[4]
    sel_new = Anew[(Anew.root == r) & (Anew.geom == g) & (Anew.btag == b)
                   & (Anew.M == Mv) & (Anew.variant == varv)
                   & (Anew.year == yv)]
    sel_old = Aold[(Aold.root == r) & (Aold.geom == g) & (Aold.btag == b)
                   & (Aold.M == Mv) & (Aold.variant == varv)
                   & (Aold.year == yv)]
    report["partA_selected_cell"] = {
        c: dict(new=repr(sel_new[c].iloc[0]), old=repr(sel_old[c].iloc[0]),
                bitwise=bool(sel_new[c].iloc[0] == sel_old[c].iloc[0]))
        for c in vals}
    t1new = json.load(open(os.path.join(TMP, "s05_t1.json")))
    t1old = json.load(open(os.path.join(S05_RES, "s05_t1.json")))
    report["T1_reproduced"] = dict(
        new=t1new, old=t1old,
        bitwise=all(t1new[k] == t1old[k] for k in t1old
                    if isinstance(t1old[k], (int, float, bool))))
    selnew = json.load(open(os.path.join(TMP,
                                         "s05_variant_selection.json")))
    selold = json.load(open(os.path.join(S05_RES,
                                         "s05_variant_selection.json")))
    report["variant_selection_reproduced"] = dict(
        new=selnew["chosen"], old=selold["chosen"],
        same=selnew["chosen"] == selold["chosen"])

    # ---------------- Part C re-run
    import partc
    partc.RES = TMP
    partc.CHOSEN = selnew["chosen"]
    t = time.time()
    partc.main()
    report["partC_rerun_seconds"] = round(time.time() - t, 1)
    Cnew = pd.read_csv(os.path.join(TMP, "s05_partc.csv"))
    Cold = pd.read_csv(os.path.join(S05_RES, "s05_partc.csv"))
    keysC = ["root", "geom", "btag", "horizon", "M", "year", "tercile",
             "estimator"]
    report["partC_all_cells"] = cmp_frames(Cnew, Cold, keysC, ["lam"],
                                           "Part C, every estimate")
    sc = sels[1]["cell_id"].split("/")
    rr, gg, bb, hh = sc[0], sc[1], sc[2], sc[3]
    MM = int(sc[4][1:]); yy = int(sc[5][1:]); tt = int(sc[6][1:])
    f_new = Cnew[(Cnew.root == rr) & (Cnew.geom == gg) & (Cnew.btag == bb)
                 & (Cnew.horizon == hh) & (Cnew.M == MM)
                 & (Cnew.year == yy) & (Cnew.tercile == tt)]
    f_old = Cold[(Cold.root == rr) & (Cold.geom == gg) & (Cold.btag == bb)
                 & (Cold.horizon == hh) & (Cold.M == MM)
                 & (Cold.year == yy) & (Cold.tercile == tt)]
    mm = f_new.merge(f_old, on="estimator", suffixes=("_new", "_old"))
    report["partC_selected_cell"] = [
        dict(estimator=r_.estimator, new=repr(r_.lam_new),
             old=repr(r_.lam_old), bitwise=bool(r_.lam_new == r_.lam_old),
             abs_diff=float(abs(r_.lam_new - r_.lam_old)))
        for r_ in mm.itertuples()]

    # ---------------- Part E deterministic re-check
    import partde as pd5
    se = sels[2]["cell_id"].split("/")
    root, geom, btag, horizon, scheme = se
    z = np.load(os.path.join(TMP, f"panel_{root}_{geom}_{btag}.npz"))
    grid = z["logpx"].astype(np.float64)
    wlen = {"1day": None, "1h": 60, "30min": 30}[horizon]
    S = pd5.build_series(grid, wlen)
    D = S["nw"]
    warm = 500 if horizon == "1day" else max(500, 22 * D + 100)
    refit = 1 if horizon == "1day" else D
    t = time.time()
    F, start, nonconv = pd5.forecasts(S, D, warm, refit, horizon == "1day")
    report["partE_rerun_seconds"] = round(time.time() - t, 1)
    rv = S["rv"]
    ok = np.ones(len(rv), bool)
    for m in pd5.MODELS:
        ok &= np.isfinite(F[m])
    ok[:max(start, warm)] = False
    rvv = rv[ok]
    Fm = {m: F[m][ok] for m in pd5.MODELS}
    if scheme == "S-A":
        mask = np.ones(len(rvv), bool)
    else:
        q = float(scheme.split("_q")[1])
        base = rvv if scheme.startswith("S-B") else Fm["M2_HAR"]
        mask = base > np.quantile(base, q)
    MET = pd.read_csv(os.path.join(S05_RES, "s05_metrics.csv"))
    sub = MET[(MET.root == root) & (MET.geom == geom) & (MET.btag == btag)
              & (MET.horizon == horizon) & (MET.scheme == scheme)]
    det = []
    for m in pd5.MODELS:
        qk = float(pd5.qlike(Fm[m][mask], rvv[mask]).mean())
        old = float(sub[sub.model == m]["qlike_mean"].iloc[0])
        det.append(dict(model=m, qlike_new=repr(qk), qlike_old=repr(old),
                        bitwise=bool(qk == old),
                        abs_diff=abs(qk - old),
                        rel_diff=abs(qk - old) / max(abs(old), 1e-300)))
    report["partE_selected_cell"] = dict(
        cell=sels[2]["cell_id"], n_obs_new=int(mask.sum()),
        n_obs_old=int(sub["n"].iloc[0]),
        n_obs_match=bool(int(mask.sum()) == int(sub["n"].iloc[0])),
        deterministic_inputs=det,
        note="MCS composition is not bitwise-testable in isolation; see "
             "Phase 3 seed set for this cell.")
    report["total_seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(RES, "phase4_rerun.json"), "w") as fh:
        json.dump(report, fh, indent=1, default=str)
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ("partA_all_cells", "partC_all_cells")},
                     indent=1, default=str)[:2500])
    print("PART A all-cells identical:",
          report["partA_all_cells"]["all_bitwise_identical"])
    print("PART C all-cells identical:",
          report["partC_all_cells"]["all_bitwise_identical"])
    print("PHASE4 DONE", report["total_seconds"], "s")


if __name__ == "__main__":
    main()
