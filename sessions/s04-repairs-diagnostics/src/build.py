"""S04 Phase 2: rebuild bars with repairs R1-R3.

Module reuse (Phase 0 report):
- REUSED UNMODIFIED (imported): S03 `analysis.build_panels`,
  `analysis.rv_from_grid`, S03 constants (M_SETS, N_GRID, TICK_INT), and the
  S03 Phase-0 extract `raw_pre2024.npy` (the official-reader output).
- RE-EXECUTED: S03 rules 1-4 and rule 6 (front selection) run here with
  logic identical to S03's `pipeline.main()`; that function is a monolith
  that applies the S03 versions of rules 5 and 7 inline, so it cannot be
  called with R1-R3 in place without modifying S03 artifacts, which is
  prohibited. The re-execution is line-for-line the S03 code path up to
  rule 5.
- EXTENDED (new here): R1 geometry-dependent early-close, R2 degraded-date
  flagging, R3 weekend-trade-date trace, and the repaired rule-7 pass.
"""

import json
import os
import sys
import time

import databento as db
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
S03 = os.path.join(ROOT, "sessions", "s03-data-noise")
S03_RES = os.path.join(S03, "results")
sys.path.insert(0, os.path.join(S03, "src"))

import analysis as s03a          # noqa: E402  (build_panels, rv_from_grid)

RES = os.path.join(BASE, "results")
DATA = os.path.join(ROOT, "data", "GLBX-20260817-KAB3XQ8E4C")
SAMPLE_LO, SAMPLE_HI = "2016-01-01", "2023-12-31"
DEGRADED_RAW = ["2017-11-13", "2019-01-15", "2019-02-22", "2019-03-13",
                "2019-03-26", "2020-02-27", "2020-02-28", "2020-06-30",
                "2020-07-01", "2021-12-05", "2022-01-02"]

out = {}
timers = {}


def main():
    t0 = time.time()
    # ---------------- S03 rules 1-4 + 6, re-executed identically
    raw = np.load(os.path.join(S03_RES, "raw_pre2024.npy"))
    df = pd.DataFrame(raw, columns=["ts", "iid", "open", "high", "low",
                                    "close", "volume"])
    store = db.DBNStore.from_file(os.path.join(
        DATA, "glbx-mdp3-20100606-20260815.ohlcv-1m.dbn.zst"))
    recs = []
    for sym, ivs in store.metadata.mappings.items():
        for iv in ivs:
            if iv["symbol"]:
                recs.append((int(iv["symbol"]), np.datetime64(iv["start_date"]),
                             np.datetime64(iv["end_date"]), sym))
    mtab = pd.DataFrame(recs, columns=["iid", "d0", "d1", "raw"])
    utc_date = df["ts"].values.astype("datetime64[ns]").astype("datetime64[D]")
    df["utc_date"] = utc_date
    df["raw"] = pd.Series(pd.NA, index=df.index, dtype="object")
    for iid, g in mtab.groupby("iid"):
        sel = df.index[df["iid"] == iid]
        if not len(sel):
            continue
        d = df.loc[sel, "utc_date"].values
        assign = np.full(len(sel), None, dtype=object)
        for _, r in g.iterrows():
            m = (d >= r["d0"]) & (d < r["d1"])
            assign[m] = r["raw"]
        df.loc[sel, "raw"] = assign
    df = df[df["raw"].notna()]
    df = df[~df["raw"].str.contains("-")].copy()
    df["root"] = df["raw"].str[:2]
    df = df[df["root"].isin(["ES", "NQ"])].copy()
    ts = pd.DatetimeIndex(df["ts"].values.astype("datetime64[ns]"), tz="UTC")
    ny = ts.tz_convert("America/New_York")
    df["ny_min"] = (ny.hour * 60 + ny.minute).values
    df["ny_dow"] = ny.dayofweek.values
    df["tdate"] = pd.to_datetime((ny + pd.Timedelta(hours=6)).date)
    df = df[(df["tdate"] >= SAMPLE_LO) & (df["tdate"] <= SAMPLE_HI)].copy()
    timers["rules_1_4"] = time.time() - t0

    # ---------------- R3: trace the weekend trade date BEFORE any repair
    t1 = time.time()
    wk = df[pd.DatetimeIndex(df["tdate"]).dayofweek >= 5]
    trace = []
    for td, g in wk.groupby("tdate"):
        tsg = pd.DatetimeIndex(g["ts"].values.astype("datetime64[ns]"),
                               tz="UTC")
        nyg = tsg.tz_convert("America/New_York")
        trace.append(dict(
            trade_date=str(td.date()),
            trade_dow=int(td.dayofweek),
            n_rows=len(g),
            roots=sorted(g["root"].unique().tolist()),
            raw_symbols=sorted(g["raw"].unique().tolist()),
            instrument_ids=sorted(int(x) for x in g["iid"].unique()),
            ts_utc_min=str(tsg.min()), ts_utc_max=str(tsg.max()),
            ts_ny_min=str(nyg.min()), ts_ny_max=str(nyg.max()),
            ny_minutes=sorted(g["ny_min"].unique().tolist())[:20],
            volumes=[int(v) for v in g["volume"].head(10)],
            arithmetic=[f"{a} NY + 6h = {b} -> date {c}"
                        for a, b, c in zip(
                            nyg[:5].strftime("%Y-%m-%d %H:%M %Z"),
                            (nyg[:5] + pd.Timedelta(hours=6))
                            .strftime("%Y-%m-%d %H:%M"),
                            (nyg[:5] + pd.Timedelta(hours=6)).date)]))
    out["r3_trace"] = trace
    timers["r3_trace"] = time.time() - t1

    # ---------------- R3 patch (minimal): a weekend-dated bar is a pre-open
    # print in the Sunday halt window; it belongs to the next Monday's
    # session. Friday halt-window prints stay with Friday's ended session
    # (the +6h rule already places them there), so only weekend-dated bars
    # move.
    dow = pd.DatetimeIndex(df["tdate"]).dayofweek
    wk_mask = dow >= 5
    out["r3_patch_rows_reassigned"] = int(wk_mask.sum())
    shift = pd.to_timedelta((7 - dow[wk_mask]).values, unit="D")
    df.loc[wk_mask, "tdate"] = df.loc[wk_mask, "tdate"] + shift
    df = df[(df["tdate"] >= SAMPLE_LO) & (df["tdate"] <= SAMPLE_HI)].copy()
    out["r3_weekend_trade_dates_after_patch"] = int(
        (pd.DatetimeIndex(df["tdate"].unique()).dayofweek >= 5).sum())

    # ---------------- rule 6 front selection (S03 logic)
    t2 = time.time()
    vol = df.groupby(["root", "tdate", "raw"])["volume"].sum().reset_index()
    front = vol.sort_values("volume").groupby(["root", "tdate"]).tail(1)
    front = front.rename(columns={"raw": "front"})[["root", "tdate", "front"]]
    df = df.merge(front, on=["root", "tdate"], how="left")
    dff = df[df["raw"] == df["front"]].copy()
    out["s03_raw_sessions_per_root"] = int(
        front[front.root == "ES"]["tdate"].nunique())

    # ---------------- R1: geometry-dependent early close
    daypart = dff[dff["ny_min"] < 18 * 60]
    last_min = daypart.groupby(["root", "tdate"])["ny_min"].max()
    early_day = last_min < 15 * 60            # S03 detector: 68 per root
    # overnight completeness: expected 930 overnight minutes
    on_mask = (dff["ny_min"] >= 1080) | (dff["ny_min"] < 570)
    on_count = dff[on_mask].groupby(["root", "tdate"])["ny_min"].count()
    on_ok = (on_count / 930.0) >= 0.90
    # designated half-days (S03 classifier)
    def designated(d):
        # Black Friday = the Friday after the fourth Thursday of November,
        # always day 23-29; July 3; December 24.
        return ((d.month == 11 and d.dayofweek == 4 and 23 <= d.day <= 29)
                or (d.month == 7 and d.day == 3)
                or (d.month == 12 and d.day == 24))
    flags = pd.DataFrame(dict(early_day=early_day)).join(
        on_ok.rename("on_ok"), how="left")
    flags["on_ok"] = flags["on_ok"].fillna(False).astype(bool)
    flags["early_day"] = flags["early_day"].astype(bool)
    flags["designated"] = [designated(d) for (_, d) in flags.index]
    flags["excl_rth"] = flags["early_day"] | flags["designated"]
    flags["excl_glbx"] = (flags["early_day"] & ~flags["on_ok"]) \
        | flags["designated"]
    out["r1_counts"] = {
        "early_day_per_root": {r: int(flags.loc[r]["early_day"].sum())
                               for r in ["ES", "NQ"]},
        "designated_per_root": {r: int(flags.loc[r]["designated"].sum())
                                for r in ["ES", "NQ"]},
        "excluded_rth_per_root": {r: int(flags.loc[r]["excl_rth"].sum())
                                  for r in ["ES", "NQ"]},
        "excluded_globex_per_root": {r: int(flags.loc[r]["excl_glbx"].sum())
                                     for r in ["ES", "NQ"]},
        "globex_retained_holiday_sessions": {
            r: int((flags.loc[r]["early_day"] & flags.loc[r]["on_ok"]
                    & ~flags.loc[r]["designated"]).sum())
            for r in ["ES", "NQ"]},
    }
    out["r1_designated_dates"] = sorted(
        {str(d.date()) for (r, d) in flags.index[flags["designated"]]})

    # ---------------- R2: degraded dates -> affected trade dates (flag only)
    deg = [np.datetime64(d) for d in DEGRADED_RAW]
    aff = dff[np.isin(dff["utc_date"].values, deg)]
    r2_dates = sorted({str(d.date()) for d in aff["tdate"].unique()})
    out["r2_affected_trade_dates_realised"] = r2_dates
    out["r2_affected_rows"] = int(len(aff))

    # ---------------- rule 7 (roll +/-1) per geometry after R1
    t3 = time.time()
    panels = {}
    ledger = {}
    for geom, exfl in [("RTH", "excl_rth"), ("GLOBEX", "excl_glbx")]:
        keep_frames = []
        for r in ["ES", "NQ"]:
            fl = flags.loc[r]
            keep_dates = set(fl.index[~fl[exfl]])
            f = front[front["root"] == r].sort_values("tdate")
            f = f[f["tdate"].isin(keep_dates)].reset_index(drop=True)
            roll = f["front"] != f["front"].shift()
            roll.iloc[0] = False
            bad = roll | roll.shift(-1, fill_value=False) \
                | roll.shift(1, fill_value=False)
            keep = set(f.loc[~bad, "tdate"])
            ledger[f"{r}_{geom}"] = dict(
                after_r1=len(f), roll_excluded=int(bad.sum()),
                final=len(keep))
            sub = dff[(dff["root"] == r) & (dff["tdate"].isin(keep))]
            keep_frames.append(sub)
        panels[geom] = pd.concat(keep_frames)
    out["ledger"] = ledger
    for geom, d in panels.items():
        d2 = d.drop(columns=["front", "utc_date"])
        d2.to_parquet(os.path.join(RES, f"bars_{geom}.parquet"))
    # R2 flag file
    with open(os.path.join(RES, "s04_build.json"), "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    timers["r1_r7_build"] = time.time() - t3
    with open(os.path.join(RES, "s04_timers_build.json"), "w") as fh:
        json.dump(timers, fh, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "r3_trace"},
                     indent=1, default=str))
    print("R3 TRACE:")
    print(json.dumps(out["r3_trace"], indent=1, default=str))


if __name__ == "__main__":
    main()
