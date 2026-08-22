"""S03 phases 3-4: validation gates, session panels, noise measurement."""

import json
import os
import sys
import time

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results")
TICK_INT = 250_000_000            # 0.25 * 1e9
M_SETS = {"RTH": [13, 26, 78, 195, 390],
          "GLOBEX": [23, 46, 138, 345, 1380]}
N_GRID = {"RTH": 390, "GLOBEX": 1380}

gates = {}
timers = {}


def build_panels(df, root, geom):
    """Filled log-price grid (sessions x n+1) from close prices."""
    sub = df[df["root"] == root]
    n = N_GRID[geom]
    if geom == "RTH":
        sub = sub[(sub["ny_min"] >= 570) & (sub["ny_min"] < 960)]
        slot = sub["ny_min"] - 570
    else:
        slot = (sub["ny_min"] - 1080) % 1440
        ok = slot < 1380
        sub, slot = sub[ok], slot[ok]
    dates = np.sort(sub["tdate"].unique())
    didx = {d: i for i, d in enumerate(dates)}
    S = len(dates)
    px = np.full((S, n), np.nan)
    px[sub["tdate"].map(didx).values, slot.values] = \
        np.log(sub["close"].values / 1e9)
    present = ~np.isnan(px)
    # forward fill within session; leading gap backfilled from first obs
    filled = pd.DataFrame(px).ffill(axis=1).bfill(axis=1).values
    return dates, filled, present


def rv_from_grid(filled, M):
    n = filled.shape[1]
    stride = n // M
    p = filled[:, ::stride]
    if p.shape[1] == M:                # need M+1 boundary points
        p = np.concatenate([p, filled[:, -1:]], axis=1)
    r = np.diff(p, axis=1)
    return (r * r).sum(axis=1)


def main():
    t0 = time.time()
    df = pd.read_parquet(os.path.join(RES, "bars_final.parquet"))
    df["year"] = df["tdate"].dt.year

    # ---------------- gates
    g = {}
    g["price_scale_min_max_by_root"] = {
        r: [float(df[df.root == r]["close"].min() / 1e9),
            float(df[df.root == r]["close"].max() / 1e9)]
        for r in ["ES", "NQ"]}
    viol = 0
    nzinc = 0
    for (r, d), sess in df.groupby(["root", "tdate"], sort=False):
        c = sess.sort_values("ny_min")["close"].values
        inc = np.diff(c)
        inc = inc[inc != 0]
        nzinc += len(inc)
        viol += int((inc % TICK_INT != 0).sum())
    g["nonzero_increments"] = nzinc
    g["tick_violations_0p25"] = viol

    counts_sess = df.groupby(["root", "tdate"]).size()
    per_year = counts_sess.groupby(
        [counts_sess.index.get_level_values(0),
         pd.DatetimeIndex(counts_sess.index.get_level_values(1)).year])
    g["bars_per_session_by_year"] = {
        f"{r}_{y}": dict(mean=float(v.mean()), p5=float(v.quantile(0.05)),
                         max=int(v.max()))
        for (r, y), v in per_year}
    g["fill_ratio_globex_by_year"] = {
        f"{r}_{y}": round(float(v.mean()) / 1380.0, 4)
        for (r, y), v in per_year}

    zv = df.assign(zv=(df["volume"] == 0).astype(float),
                   hour=df["ny_min"] // 60)
    g["zero_volume_fraction_by_year"] = {
        f"{r}_{y}": round(float(x), 5) for (r, y), x in
        zv.groupby(["root", "year"])["zv"].mean().items()}
    g["zero_volume_fraction_by_hour_ny"] = {
        int(h): round(float(x), 5)
        for h, x in zv.groupby("hour")["zv"].mean().items()}

    mom = {}
    out_ct = {}
    for (r, y), sub in df.groupby(["root", "year"]):
        lr = []
        for d, sess in sub.groupby("tdate"):
            c = np.log(sess.sort_values("ny_min")["close"].values / 1e9)
            lr.append(np.diff(c))
        lr = np.concatenate(lr)
        sd = lr.std()
        mom[f"{r}_{y}"] = dict(n=len(lr), mean=float(lr.mean()),
                               sd=float(sd),
                               skew=float(((lr - lr.mean()) ** 3).mean() / sd ** 3),
                               kurt=float(((lr - lr.mean()) ** 4).mean() / sd ** 4))
        out_ct[f"{r}_{y}"] = int((np.abs(lr) > 10 * sd).sum())
    g["return_moments_1min_by_year"] = mom
    g["outliers_gt_10sd_by_year_flagged_not_removed"] = out_ct
    gates.update(g)
    timers["gates"] = time.time() - t0

    # ---------------- panels + noise
    t1 = time.time()
    sig_rows, noise_rows = [], []
    for root in ["ES", "NQ"]:
        for geom in ["GLOBEX", "RTH"]:
            dates, filled, present = build_panels(df, root, geom)
            np.savez_compressed(
                os.path.join(RES, f"panel_{root}_{geom}.npz"),
                dates=dates.astype("datetime64[D]").astype(str),
                logpx=filled.astype(np.float32), present=present)
            n = N_GRID[geom]
            rv = {M: rv_from_grid(filled, M) for M in M_SETS[geom]}
            years = pd.DatetimeIndex(dates).year.values
            vol_proxy = rv[min(M_SETS[geom])]
            terc = np.searchsorted(np.quantile(vol_proxy, [1/3, 2/3]),
                                   vol_proxy)

            groups = {"all": np.ones(len(dates), bool)}
            for y in np.unique(years):
                groups[f"y{y}"] = years == y
            for t in range(3):
                groups[f"terc{t+1}"] = terc == t

            for gname, mask in groups.items():
                mrv = {M: float(rv[M][mask].mean()) for M in M_SETS[geom]}
                for M in M_SETS[geom]:
                    sig_rows.append(dict(root=root, geom=geom, group=gname,
                                         M=M, mean_rv=mrv[M],
                                         n_days=int(mask.sum())))
                ms = np.array(M_SETS[geom], float)
                y = np.array([mrv[M] for M in M_SETS[geom]])
                slope, intercept = np.polyfit(ms, y, 1)
                omega2_n1 = slope / 2.0
                omega2_n2 = mrv[max(M_SETS[geom])] / (2.0 * n)
                # goodness of linearity: R^2 of the signature regression
                pred = intercept + slope * ms
                ss = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
                noise_rows.append(dict(
                    root=root, geom=geom, group=gname, n_days=int(mask.sum()),
                    intercept_EIV=float(intercept),
                    omega2_N1=float(omega2_n1), omega2_N2=float(omega2_n2),
                    NSR_N1=float(omega2_n1 / intercept) if intercept > 0 else np.nan,
                    NSR_N2=float(omega2_n2 / intercept) if intercept > 0 else np.nan,
                    signature_R2=float(ss),
                    mean_rv_coarsest=mrv[min(M_SETS[geom])],
                    mean_rv_finest=mrv[max(M_SETS[geom])]))
    pd.DataFrame(sig_rows).to_csv(os.path.join(RES, "s03_signature.csv"),
                                  index=False)
    pd.DataFrame(noise_rows).to_csv(os.path.join(RES, "s03_noise.csv"),
                                    index=False)
    timers["panels_noise"] = time.time() - t1

    # ---------------- figure
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    sig = pd.DataFrame(sig_rows)
    for ax, (root, geom) in zip(axes.ravel(),
                                [(r, g) for r in ["ES", "NQ"]
                                 for g in ["GLOBEX", "RTH"]]):
        s = sig[(sig.root == root) & (sig.geom == geom)
                & (sig.group == "all")]
        ax.plot(s["M"], s["mean_rv"], "o-")
        ax.set_title(f"{root} {geom}: mean RV vs M")
        ax.set_xlabel("M (sub-intervals)")
        ax.set_ylabel("mean daily RV")
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "s03_signature.png"), dpi=110)

    with open(os.path.join(RES, "s03_gates.json"), "w") as fh:
        json.dump(gates, fh, indent=1)
    with open(os.path.join(RES, "s03_timers_p34.json"), "w") as fh:
        json.dump(timers, fh, indent=1)
    print("gates+noise done", json.dumps(timers, indent=1))
    print(pd.DataFrame(noise_rows).query("group=='all'").to_string())


if __name__ == "__main__":
    main()
