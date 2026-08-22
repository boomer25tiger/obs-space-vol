"""S04 Phase 3: D-TAIL and D-RQ, run with and without R2-degraded dates."""

import json
import os
import sys
import time

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, os.path.join(ROOT, "sessions", "s03-data-noise", "src"))
import analysis as s03a                      # noqa: E402

RES = os.path.join(BASE, "results")
M_SETS = {"RTH": [13, 26, 78, 195, 390], "GLOBEX": [23, 46, 138, 345, 1380]}
build = json.load(open(os.path.join(RES, "s04_build.json")))
R2_DATES = set(pd.to_datetime(build["r2_affected_trade_dates_realised"]))


def session_returns(df):
    """Per-session 1-minute log returns with metadata columns."""
    df = df.sort_values(["root", "tdate", "ts"])
    lc = np.log(df["close"].values / 1e9)
    r = np.diff(lc)
    same = (df["tdate"].values[1:] == df["tdate"].values[:-1]) \
        & (df["root"].values[1:] == df["root"].values[:-1])
    return pd.DataFrame(dict(
        r=r[same], root=df["root"].values[1:][same],
        tdate=df["tdate"].values[1:][same],
        ny_min=df["ny_min"].values[1:][same],
        prev_stale=np.zeros(same.sum(), dtype=int))), df


def add_stale_runs(rets):
    """Consecutive unchanged-close run length immediately before each bar."""
    z = (rets["r"].values == 0.0).astype(int)
    run = np.zeros(len(z), dtype=int)
    newsess = np.zeros(len(z), dtype=bool)
    td = rets["tdate"].values
    rt = rets["root"].values
    newsess[1:] = (td[1:] != td[:-1]) | (rt[1:] != rt[:-1])
    for i in range(1, len(z)):
        run[i] = 0 if newsess[i] else (run[i - 1] + 1 if z[i - 1] else 0)
    rets["prev_stale"] = run
    return rets


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return np.nan
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))


def hill(absr, k_frac=0.01):
    x = np.sort(absr)[::-1]
    k = max(50, int(len(x) * k_frac))
    x = x[:k + 1]
    return float(1.0 / np.mean(np.log(x[:-1] / x[k])))


def dtail(rets, front, tag, out):
    res = {}
    rets = rets.copy()
    yr = pd.DatetimeIndex(rets["tdate"]).year
    sd = rets.groupby([rets["root"], yr])["r"].transform("std")
    ext = np.abs(rets["r"].values) > 10 * sd.values
    rets["ext"] = ext
    res["n_returns"] = int(len(rets))
    res["n_extremes"] = int(ext.sum())

    # H1 date clustering + clock times
    per_date = rets.groupby(["root", "tdate"])["ext"].sum()
    counts = per_date.values
    ntop = max(1, int(np.ceil(len(counts) * 0.01)))
    top = np.sort(counts)[::-1][:ntop]
    res["H1_share_in_top1pct_dates"] = float(top.sum() / max(ext.sum(), 1))
    mins = rets["ny_min"].values[ext]
    near = np.zeros(len(mins), bool)
    for anchor in [8 * 60 + 30, 10 * 60, 14 * 60]:
        near |= np.abs(mins - anchor) <= 5
    res["H1_share_within_5min_of_0830_1000_1400"] = float(near.mean()) \
        if len(mins) else np.nan
    res["H1_event_dates_note"] = ("FOMC/CPI/NFP dates cannot be constructed "
                                  "from the price data alone; clock-time "
                                  "clustering reported instead")

    # H2 per-minute rate (full table to CSV)
    per_min = rets.groupby("ny_min")["ext"].agg(["sum", "count"])
    per_min["rate"] = per_min["sum"] / per_min["count"]
    per_min.to_csv(os.path.join(RES, f"s04_h2_minute_rates_{tag}.csv"))
    base = res["n_extremes"] / max(res["n_returns"], 1)
    calls = {}
    for name, m in [("1700_halt", 1020), ("1800_reopen", 1080),
                    ("1801", 1081), ("1805", 1085),
                    ("rth_first_0930", 570), ("rth_0931", 571),
                    ("rth_last_1559", 959), ("1600", 960)]:
        if m in per_min.index:
            calls[name] = dict(rate=float(per_min.loc[m, "rate"]),
                               n=int(per_min.loc[m, "count"]),
                               rel_to_base=float(per_min.loc[m, "rate"]
                                                 / base) if base else np.nan)
    res["H2_called_out_minutes"] = calls
    res["H2_base_rate"] = float(base)

    # H3 distance from roll
    res["H3_rate_by_roll_distance"] = {}
    for root in ["ES", "NQ"]:
        f = front[front["root"] == root].sort_values("tdate")
        roll_dates = f.loc[f["front"] != f["front"].shift(), "tdate"].values[1:]
        all_dates = np.sort(rets.loc[rets["root"] == root, "tdate"].unique())
        didx = {d: i for i, d in enumerate(all_dates)}
        roll_idx = np.array([didx.get(d, -1) for d in roll_dates])
        sub = rets[rets["root"] == root]
        sess_idx = sub["tdate"].map(didx).values
        dist = np.full(len(sub), 999)
        for ri in roll_idx:
            if ri < 0:
                # roll date itself excluded; nearest retained index
                continue
        # distance in retained-session index space to nearest roll date
        roll_pos = np.array(sorted(
            [didx[d] for d in roll_dates if d in didx]
            + [didx[min(all_dates, key=lambda x: abs(
                (x - d) / np.timedelta64(1, 'D')))] for d in roll_dates
               if d not in didx]))
        if len(roll_pos):
            j = np.searchsorted(roll_pos, sess_idx)
            j = np.clip(j, 0, len(roll_pos) - 1)
            dl = np.abs(sess_idx - roll_pos[np.maximum(j - 1, 0)])
            dr = np.abs(roll_pos[j] - sess_idx)
            signed = np.where(dr <= dl, sess_idx - roll_pos[j],
                              sess_idx - roll_pos[np.maximum(j - 1, 0)])
            dist = signed
        tab = {}
        for d in range(-10, 11):
            m = dist == d
            if m.sum():
                tab[d] = dict(rate=float(sub["ext"].values[m].mean()),
                              n_returns=int(m.sum()),
                              n_sessions=int(len(np.unique(sess_idx[m]))))
        res["H3_rate_by_roll_distance"][root] = tab

    # H4 uniformity
    res["H4_gini_extremes_per_date"] = {
        r: gini(per_date.loc[r].values) for r in ["ES", "NQ"]}
    h4 = {}
    for (root, y), g in rets.groupby([rets["root"], yr]):
        a = np.abs(g["r"].values)
        a = a[a > 0]
        alpha = hill(a)
        from scipy import stats as st
        nu = max(alpha, 2.1)
        sdv = g["r"].std()
        scale = sdv * np.sqrt((nu - 2) / nu)
        p10 = 2 * st.t.sf(10 * sdv / scale, df=nu)
        h4[f"{root}_{y}"] = dict(hill_alpha=float(alpha),
                                 expected_extremes_t=float(p10 * len(g)),
                                 observed=int(g["ext"].sum()))
    res["H4_hill_and_t_null"] = h4

    # H5 stale runs
    ex = rets[rets["ext"]]
    res["H5_prev_stale_extremes"] = {
        "mean": float(ex["prev_stale"].mean()),
        "median": float(ex["prev_stale"].median()),
        "p90": float(ex["prev_stale"].quantile(0.90)),
        "share_ge1": float((ex["prev_stale"] >= 1).mean()),
        "share_ge5": float((ex["prev_stale"] >= 5).mean())}
    res["H5_prev_stale_unconditional"] = {
        "mean": float(rets["prev_stale"].mean()),
        "median": float(rets["prev_stale"].median()),
        "p90": float(rets["prev_stale"].quantile(0.90)),
        "share_ge1": float((rets["prev_stale"] >= 1).mean()),
        "share_ge5": float((rets["prev_stale"] >= 5).mean())}
    out[f"dtail_{tag}"] = res


def drq(df, geom, tag, out):
    rows = []
    for root in ["ES", "NQ"]:
        dates, filled, present = s03a.build_panels(df, root, geom)
        years = pd.DatetimeIndex(dates).year.values
        n = filled.shape[1]
        for M in M_SETS[geom]:
            stride = n // M
            p = filled[:, ::stride]
            if p.shape[1] == M:
                p = np.concatenate([p, filled[:, -1:]], axis=1)
            r = np.diff(p, axis=1)
            bv = (np.pi / 2.0) * (M / (M - 1.0)) \
                * (np.abs(r[:, 1:]) * np.abs(r[:, :-1])).sum(axis=1)
            rq = (M / 3.0) * (r ** 4).sum(axis=1)
            a43 = np.abs(r) ** (4 / 3)
            mu43 = 2 ** (2 / 3) * 0.8929795115692492  # gamma(7/6)/gamma(1/2)
            tq = M * (M / (M - 2.0)) * mu43 ** (-3) \
                * (a43[:, :-2] * a43[:, 1:-1] * a43[:, 2:]).sum(axis=1)
            trq = {}
            for c in [3, 5, 10]:
                u = c * np.sqrt(np.maximum(bv, 1e-300) / M)
                rr = np.where(np.abs(r) <= u[:, None], r, 0.0)
                trq[c] = (M / 3.0) * (rr ** 4).sum(axis=1)
            logrq = np.log(np.maximum(rq, 1e-300))
            acf = []
            lc = logrq - logrq.mean()
            for k in range(1, 11):
                acf.append(float(np.dot(lc[:-k], lc[k:])
                                 / np.dot(lc, lc)))
            for y in sorted(set(years)):
                m = years == y
                def stats_(x):
                    return dict(mean=float(x.mean()),
                                median=float(np.median(x)),
                                p95=float(np.quantile(x, .95)),
                                p99=float(np.quantile(x, .99)),
                                max=float(x.max()),
                                top1_share=float(x.max() / x.sum()))
                srt = np.sort(rq[m])[::-1]
                n50 = int(np.searchsorted(np.cumsum(srt), 0.5 * srt.sum()) + 1)
                ratio = rq[m] / np.maximum(tq[m], 1e-300)
                row = dict(root=root, geom=geom, M=M, year=int(y),
                           n_sessions=int(m.sum()),
                           rq=stats_(rq[m]), tq=stats_(tq[m]),
                           trq3=stats_(trq[3][m]), trq5=stats_(trq[5][m]),
                           trq10=stats_(trq[10][m]),
                           rq_tq_ratio_median=float(np.median(ratio)),
                           rq_tq_ratio_p95=float(np.quantile(ratio, .95)),
                           rq_top50pct_sessions=n50)
                rows.append(row)
            rows.append(dict(root=root, geom=geom, M=M, year=0,
                             n_sessions=int(len(rq)),
                             logrq_acf_lags1_10=acf))
    out[f"drq_{geom}_{tag}"] = rows


def main():
    out = {}
    t0 = time.time()
    for geom in ["GLOBEX", "RTH"]:
        df = pd.read_parquet(os.path.join(RES, f"bars_{geom}.parquet"))
        front = df[["root", "tdate", "raw"]].drop_duplicates(
            ["root", "tdate"]).rename(columns={"raw": "front"})
        rets, _ = session_returns(df)
        rets = add_stale_runs(rets)
        for r2tag, mask in [("withR2", np.ones(len(rets), bool)),
                            ("noR2", ~rets["tdate"].isin(R2_DATES).values)]:
            dtail(rets[mask], front, f"{geom}_{r2tag}", out)
        for r2tag, dmask in [("withR2", np.ones(len(df), bool)),
                             ("noR2", ~df["tdate"].isin(R2_DATES).values)]:
            drq(df[dmask], geom, r2tag, out)
    out["elapsed_s"] = time.time() - t0
    with open(os.path.join(RES, "s04_diagnostics.json"), "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    print("diagnostics done in", round(out["elapsed_s"], 1), "s")
    d = out["dtail_GLOBEX_withR2"]
    print("extremes:", d["n_extremes"], "of", d["n_returns"])
    print("H1 top1%:", round(d["H1_share_in_top1pct_dates"], 3),
          "| near events:", round(d["H1_share_within_5min_of_0830_1000_1400"], 3))
    print("H4 gini:", d["H4_gini_extremes_per_date"])
    print("H5 ext:", d["H5_prev_stale_extremes"])
    print("H5 unc:", d["H5_prev_stale_unconditional"])
EOF_MARKER = None


if __name__ == "__main__":
    main()
