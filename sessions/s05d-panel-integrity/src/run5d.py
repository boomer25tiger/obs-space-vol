"""S05D: Globex panel integrity. Diagnosis only, no repair, no rebuild."""

import json
import os
import sys
import time

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
RES = os.path.join(BASE, "results")
S03_RES = os.path.join(ROOT, "sessions", "s03-data-noise", "results")
S04_RES = os.path.join(ROOT, "sessions", "s04-repairs-diagnostics",
                       "results")
S05_RES = os.path.join(ROOT, "sessions", "s05-reliability-mcs", "results")
S05B_CACHE = os.path.join(ROOT, "sessions",
                          "s05b-defect-and-estimator-audit", "results",
                          "cache")

GLOBEX_OFFSET = 1080          # build_panels: slot = (ny_min - 1080) % 1440
RTH_OFFSET = 570              # build_panels: slot = ny_min - 570
CLOCKS = {"13:00": 780, "14:00": 840, "15:00": 900}   # ny_min
M_GRID = [5, 6, 10, 12, 23, 46, 138, 345, 1379]
timers = {}
out = {}


def slot_globex(ny_min):
    return (ny_min - GLOBEX_OFFSET) % 1440


def main():
    t0 = time.time()

    # ---------------- load panels + presence
    t = time.time()
    zg = np.load(os.path.join(S05_RES, "panel_ES_GLOBEX_B0.npz"))
    zr = np.load(os.path.join(S05_RES, "panel_ES_RTH_B0.npz"))
    G, GD = zg["logpx"].astype(np.float64), pd.to_datetime(
        np.array(zg["dates"], dtype="U10"))
    Rp, RD = zr["logpx"].astype(np.float64), pd.to_datetime(
        np.array(zr["dates"], dtype="U10"))
    PG = np.load(os.path.join(S05B_CACHE, "present_ES_GLOBEX.npz"))["present"]
    PR = np.load(os.path.join(S05B_CACHE, "present_ES_RTH.npz"))["present"]
    timers["load"] = round(time.time() - t, 1)

    # ---------------- PHASE 1: clock mapping
    p1 = dict(
        globex_col0_ny="18:00 (slot = (ny_min - 1080) % 1440, so slot 0 is "
                       "ny_min 1080)",
        globex_offset="FIXED at 1080 minutes (18:00 New York); not derived "
                      "per session",
        globex_last_col="slot 1379 = 16:59 New York the following day "
                        "(`ok = slot < 1380` drops 17:00-17:59)",
        rth_col0_ny="09:30 (slot = ny_min - 570)",
        rth_offset="FIXED at 570 minutes (09:30 New York)",
        rth_last_col="slot 389 = 15:59 New York",
        dst_handling="`ny_min` is built in the pipeline from a tz-aware "
                     "conversion to America/New_York (pipeline.py: "
                     "`ny = ts.tz_convert('America/New_York')`, "
                     "`ny_min = ny.hour*60 + ny.minute`), so every column "
                     "carries TRUE New York wall-clock. DST is therefore "
                     "handled correctly for the mapping itself. The "
                     "consequence not handled is that a Globex session "
                     "spans 23 wall-clock hours on the spring-forward "
                     "date and 25 on the fall-back date, so those two "
                     "sessions per year have one fewer / one more real "
                     "column than the fixed 1380-column frame assumes.",
        col_for_1300=int(slot_globex(780)),
        col_for_1400=int(slot_globex(840)),
        col_for_1500=int(slot_globex(900)))
    out["phase1_mapping"] = p1

    # 20 sessions at fixed stride
    stride = max(1, len(GD) // 20)
    idxs = list(range(0, len(GD), stride))[:20]
    rmap = {d: i for i, d in enumerate(RD)}
    rows, disagree = [], []
    for i in idxs:
        d = GD[i]
        for label, nym in CLOCKS.items():
            gs = slot_globex(nym)
            gcols = list(range(gs, min(gs + 60, 1380)))
            gvals = G[i, gcols]
            gpres = PG[i, gcols]
            r = dict(session=str(d.date()), clock=label,
                     globex_col=gs,
                     globex_price=float(np.exp(G[i, gs])),
                     globex_filled=bool(gpres[0]),
                     globex_distinct_prices_in_hour=int(
                         len(np.unique(np.round(gvals, 12)))),
                     globex_present_minutes_in_hour=int(gpres.sum()))
            if d in rmap:
                j = rmap[d]
                rs = nym - RTH_OFFSET
                rcols = list(range(rs, min(rs + 60, 390)))
                rvals = Rp[j, rcols]
                rpres = PR[j, rcols]
                r.update(rth_present=True, rth_col=rs,
                         rth_price=float(np.exp(Rp[j, rs])),
                         rth_filled=bool(rpres[0]),
                         rth_distinct_prices_in_hour=int(
                             len(np.unique(np.round(rvals, 12)))),
                         rth_present_minutes_in_hour=int(rpres.sum()))
                n = min(len(gvals), len(rvals))
                nd = int((np.round(gvals[:n], 10)
                          != np.round(rvals[:n], 10)).sum())
                r["minutes_disagreeing"] = nd
                if nd:
                    bad = np.where(np.round(gvals[:n], 10)
                                   != np.round(rvals[:n], 10))[0]
                    for k in bad[:5]:
                        disagree.append(dict(
                            session=str(d.date()), clock=label,
                            minute_offset=int(k),
                            globex_price=float(np.exp(gvals[k])),
                            rth_price=float(np.exp(rvals[k])),
                            globex_present=bool(gpres[k]),
                            rth_present=bool(rpres[k])))
            else:
                r.update(rth_present=False,
                         note="session absent from the RTH panel")
            rows.append(r)
    P1 = pd.DataFrame(rows)
    P1.to_csv(os.path.join(RES, "phase1_clock_samples.csv"), index=False)
    pd.DataFrame(disagree).to_csv(
        os.path.join(RES, "phase1_disagreements.csv"), index=False)
    out["phase1_n_sessions_sampled"] = len(idxs)
    out["phase1_n_sessions_absent_from_RTH"] = int(
        (~P1.rth_present).sum() / len(CLOCKS))
    out["phase1_total_minute_disagreements"] = int(
        P1.get("minutes_disagreeing", pd.Series(dtype=float)).sum())
    timers["phase1"] = round(time.time() - t0, 1)

    # ---------------- PHASE 2: zero-variance windows at source
    t = time.time()
    bars = pd.read_parquet(os.path.join(S04_RES, "bars_GLOBEX.parquet"))
    bars = bars[bars["root"] == "ES"]
    r1 = np.diff(G, axis=1)
    zrows = []
    for label, nym in CLOCKS.items():
        gs = slot_globex(nym)
        seg = r1[:, gs:gs + 60]
        rv = (seg ** 2).sum(axis=1)
        for i in np.where(rv == 0)[0]:
            zrows.append(dict(session=str(GD[i].date()), clock=label,
                              col_start=gs, col_end=gs + 60,
                              window_rv=float(rv[i])))
    Z = pd.DataFrame(zrows)
    out["phase2_total_zero_windows_at_13_14_15"] = int(len(Z))
    samp = Z.sample(n=min(50, len(Z)), random_state=0).sort_values(
        ["session", "clock"]) if len(Z) else Z
    det = []
    for _, r in samp.iterrows():
        d = pd.Timestamp(r.session)
        nym = CLOCKS[r.clock]
        b = bars[(bars["tdate"] == d) & (bars["ny_min"] >= nym)
                 & (bars["ny_min"] < nym + 60)]
        det.append(dict(
            session=r.session, clock=r.clock,
            col_range=f"{r.col_start}-{r.col_end}",
            raw_bars_present=int(len(b)),
            distinct_closes=int(b["close"].nunique()) if len(b) else 0,
            instrument_ids=",".join(sorted(set(str(int(x)) for x in
                                               b["iid"].unique())))
            if len(b) else "",
            raw_symbols=",".join(sorted(set(b["raw"].astype(str))))
            if len(b) else "",
            underlying_bars_exist=bool(len(b) > 0),
            carries_price_variation=bool(len(b) > 0
                                         and b["close"].nunique() > 1)))
    D2 = pd.DataFrame(det)
    D2.to_csv(os.path.join(RES, "phase2_zero_window_sources.csv"),
              index=False)
    out["phase2_sampled"] = int(len(D2))
    out["phase2_with_zero_underlying_bars"] = int(
        (~D2.underlying_bars_exist).sum()) if len(D2) else 0
    out["phase2_with_price_variation"] = int(
        D2.carries_price_variation.sum()) if len(D2) else 0

    # clustering of affected sessions
    if len(Z):
        zs = pd.to_datetime(Z.session.unique())
        allz = pd.DataFrame(dict(session=zs))
        allz["year"] = allz.session.dt.year
        allz["weekday"] = allz.session.dt.day_name()
        allz["month_day"] = allz.session.dt.strftime("%m-%d")
        # DST regime via the UTC offset of 12:00 NY that date
        off = [pd.Timestamp(f"{d.date()} 12:00").tz_localize(
            "America/New_York").utcoffset().total_seconds() / 3600
            for d in zs]
        allz["utc_offset_hours"] = off
        allz["dst_regime"] = np.where(np.array(off) == -4.0, "EDT", "EST")
        # contract and roll proximity
        fr = bars.groupby("tdate")["raw"].agg(
            lambda s: s.value_counts().index[0])
        frs = fr.sort_index()
        rolls = frs.index[frs != frs.shift()][1:]
        allz["contract"] = [str(fr.get(d, "")) for d in zs]
        allz["days_to_nearest_roll"] = [
            int(min(abs((d - r).days) for r in rolls)) if len(rolls) else -1
            for d in zs]
        allz.to_csv(os.path.join(RES, "phase2_affected_sessions.csv"),
                    index=False)
        out["phase2_n_distinct_sessions"] = int(len(allz))
        out["phase2_by_year"] = allz.year.value_counts().sort_index().to_dict()
        out["phase2_by_weekday"] = allz.weekday.value_counts().to_dict()
        out["phase2_by_dst"] = allz.dst_regime.value_counts().to_dict()
        out["phase2_by_month_day"] = allz.month_day.value_counts().head(
            15).to_dict()
        out["phase2_roll_proximity_min"] = int(
            allz.days_to_nearest_roll.min())
        out["phase2_n_within_1day_of_roll"] = int(
            (allz.days_to_nearest_roll <= 1).sum())
        # is the session in the RTH panel?
        allz["in_RTH_panel"] = [d in set(RD) for d in zs]
        out["phase2_n_in_RTH_panel"] = int(allz.in_RTH_panel.sum())
        allz.to_csv(os.path.join(RES, "phase2_affected_sessions.csv"),
                    index=False)
    timers["phase2"] = round(time.time() - t, 1)

    # ---------------- PHASE 3: padding and fill
    t = time.time()
    pad_g = ~PG
    pad_r = ~PR
    gy = GD.year.values
    ry = RD.year.values
    prows = []
    for y in sorted(set(gy.tolist())):
        m = gy == y
        inside = pad_g[m][:, slot_globex(570):slot_globex(960)]
        prows.append(dict(geometry="GLOBEX", year=int(y),
                          sessions=int(m.sum()),
                          share_padded=float(pad_g[m].mean()),
                          share_padded_0930_1600=float(inside.mean())))
    for y in sorted(set(ry.tolist())):
        m = ry == y
        prows.append(dict(geometry="RTH", year=int(y), sessions=int(m.sum()),
                          share_padded=float(pad_r[m].mean()),
                          share_padded_0930_1600=float(pad_r[m].mean())))
    P3 = pd.DataFrame(prows)
    P3.to_csv(os.path.join(RES, "phase3_padding.csv"), index=False)
    out["phase3_fill_mechanism"] = (
        "`filled = pd.DataFrame(px).ffill(axis=1).bfill(axis=1).values` "
        "(analysis.py:41): forward fill of the last observed close within "
        "the session, with a leading backfill for columns before the "
        "session's first bar. Not zero, not a sentinel.")
    out["phase3_padding_distinguishable"] = (
        "NO. The stored S05 panel npz files contain only `logpx` and "
        "`dates`; the boolean `present` mask that `build_panels` returns "
        "is not saved with them. In the stored panel a padded column is "
        "byte-identical to a genuine unchanged close, and nothing "
        "downstream of the panel can tell them apart. S05D recovers the "
        "mask only by re-running `build_panels` on the S04 bars.")
    timers["phase3"] = round(time.time() - t, 1)

    # ---------------- PHASE 4: daily aggregation exposure
    t = time.time()
    pres_ret = PG[:, 1:] & PG[:, :-1]        # a return needs both endpoints
    L = r1.shape[1]
    rows4 = []
    for M in M_GRID:
        edges = (np.arange(M + 1) * L) // M
        cs = np.concatenate([np.zeros((r1.shape[0], 1)),
                             np.cumsum(r1, axis=1)], axis=1)
        sb = cs[:, edges[1:]] - cs[:, edges[:-1]]
        rv_all = (sb ** 2).sum(axis=1)
        # contribution of sub-bars that contain no present return at all
        pcount = np.add.reduceat(pres_ret.astype(np.int32), edges[:-1],
                                 axis=1)
        empty = pcount == 0
        rv_from_padded = (np.where(empty, sb, 0.0) ** 2).sum(axis=1)
        # excluded: drop entirely-padded sub-bars from the sum
        rv_excl = (np.where(empty, 0.0, sb) ** 2).sum(axis=1)
        ok_all = rv_all > 0
        ok_ex = rv_excl > 0
        rows4.append(dict(
            M=M, n_windows=int(len(rv_all)),
            share_rv_from_padded_subbars=float(
                (rv_from_padded.sum() / rv_all.sum())),
            n_windows_with_empty_subbar=int((empty.any(axis=1)).sum()),
            mean_empty_subbars=float(empty.sum(axis=1).mean()),
            var_log_rv_as_is=float(np.log(rv_all[ok_all]).var()),
            var_log_rv_excluding_padded=float(np.log(rv_excl[ok_ex]).var()),
            delta=float(np.log(rv_excl[ok_ex]).var()
                        - np.log(rv_all[ok_all]).var()),
            n_dropped_zero_rv=int((~ok_ex).sum())))
    P4 = pd.DataFrame(rows4)
    P4.to_csv(os.path.join(RES, "phase4_padding_exposure.csv"), index=False)

    # free-intercept fit Var(log RV_M) = c + A M^b, before and after
    from scipy.optimize import curve_fit

    def model(M, c, A, b):
        return c + A * np.power(M, b)

    fits = {}
    for col, tag in [("var_log_rv_as_is", "as_is"),
                     ("var_log_rv_excluding_padded", "excluding_padded")]:
        x = P4.M.values.astype(float)
        y = P4[col].values.astype(float)
        try:
            popt, _ = curve_fit(model, x, y, p0=[y.min(), 1.0, -0.5],
                                maxfev=40000)
            pred = model(x, *popt)
            rmse = float(np.sqrt(np.mean((y - pred) ** 2)))
            fits[tag] = dict(c=float(popt[0]), A=float(popt[1]),
                             b=float(popt[2]), rmse=rmse)
        except Exception as e:
            fits[tag] = dict(error=str(e))
    out["phase4_free_intercept_fits"] = fits
    timers["phase4"] = round(time.time() - t, 1)

    timers["total"] = round(time.time() - t0, 1)
    out["timers"] = timers
    with open(os.path.join(RES, "s05d_summary.json"), "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("phase1_mapping",)}, indent=1,
                     default=str)[:4000])
    print("\nPHASE4:\n", P4.to_string(index=False))
    print("\nfits:", json.dumps(fits, indent=1))


if __name__ == "__main__":
    main()
