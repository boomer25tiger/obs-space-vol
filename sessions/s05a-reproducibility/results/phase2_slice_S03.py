phase("load")
raw = np.load(os.path.join(RES, "raw_pre2024.npy"))
df = pd.DataFrame(raw, columns=["ts", "iid", "open", "high", "low",
                                "close", "volume"])
counts["rows_pre2024"] = len(df)

# ---------------- rule 1: date-aware symbol resolution
phase("rule1_symbology")
store = db.DBNStore.from_file(os.path.join(
    DATA, "glbx-mdp3-20100606-20260815.ohlcv-1m.dbn.zst"))
recs = []
for sym, ivs in store.metadata.mappings.items():
    for iv in ivs:
        if not iv["symbol"]:
            continue
        recs.append((int(iv["symbol"]), np.datetime64(iv["start_date"]),
                     np.datetime64(iv["end_date"]), sym))
mtab = pd.DataFrame(recs, columns=["iid", "d0", "d1", "raw"])
counts["symbology_intervals"] = len(mtab)
counts["symbology_raw_symbols"] = mtab["raw"].nunique()
counts["symbology_spread_intervals"] = int(mtab["raw"].str.contains("-").sum())

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
counts["rows_unresolved_symbol"] = int(df["raw"].isna().sum())
df = df[df["raw"].notna()].copy()
# id recycling evidence
recyc = mtab.groupby("raw")["iid"].nunique()
counts["raw_symbols_with_multiple_ids"] = int((recyc > 1).sum())

# ---------------- rule 2: spread filter
phase("rule2_spreads")
nonpos_before = int(((df[["open", "high", "low", "close"]] <= 0)
                     .any(axis=1)).sum())
is_spread = df["raw"].str.contains("-")
counts["rows_spread_filtered"] = int(is_spread.sum())
counts["nonpositive_price_rows_before_filter"] = nonpos_before
df = df[~is_spread].copy()
nonpos_after = int(((df[["open", "high", "low", "close"]] <= 0)
                    .any(axis=1)).sum())
counts["nonpositive_price_rows_after_filter"] = nonpos_after
counts["nonpositive_price_values_before_filter_cellwise"] = int(
    (raw[:, 2:6] <= 0).sum())

# ---------------- rule 3: root separation
phase("rule3_roots")
df["root"] = df["raw"].str[:2]
counts["rows_by_root"] = df["root"].value_counts().to_dict()
df = df[df["root"].isin(["ES", "NQ"])].copy()

# ---------------- rule 4: session cut (NY + 6h as date)
phase("rule4_sessioncut")
ts = pd.DatetimeIndex(df["ts"].values.astype("datetime64[ns]"), tz="UTC")
ny = ts.tz_convert("America/New_York")
df["ny_min"] = (ny.hour * 60 + ny.minute).values
trade_date = (ny + pd.Timedelta(hours=6)).date
df["tdate"] = pd.to_datetime(trade_date)
in_sample = (df["tdate"] >= SAMPLE_LO) & (df["tdate"] <= SAMPLE_HI)
counts["rows_outside_2016_2023_by_trade_date"] = int((~in_sample).sum())
df = df[in_sample].copy()
counts["rows_in_sample"] = len(df)
counts["trade_sessions_raw"] = int(df.groupby(["root", "tdate"]).ngroups)

# weekend check: trade dates falling on Sat/Sun
wd = pd.DatetimeIndex(df["tdate"].unique()).dayofweek
counts["weekend_trade_dates"] = int((wd >= 5).sum())

# ---------------- rule 6 first pass: front contract by volume
phase("rule6_front")
vol = df.groupby(["root", "tdate", "raw"])["volume"].sum().reset_index()
front = vol.sort_values("volume").groupby(["root", "tdate"]).tail(1)
front = front.rename(columns={"raw": "front"})[["root", "tdate", "front"]]
ledger = {}
for root in ["ES", "NQ"]:
    f = front[front["root"] == root].sort_values("tdate")
    runs = (f["front"] != f["front"].shift()).cumsum()
    hold_sessions = f.groupby(runs).size()
    span = f.groupby(runs)["tdate"].agg(["min", "max"])
    hold_cal = (span["max"] - span["min"]).dt.days + 1
    ledger[root] = dict(sessions=len(f),
                        n_contracts=int(f["front"].nunique()),
                        median_holding_sessions=float(hold_sessions.median()),
                        median_holding_calendar_days=float(hold_cal.median()),
                        mean_holding_calendar_days=float(hold_cal.mean()))
counts["front_selection"] = ledger

df = df.merge(front, on=["root", "tdate"], how="left")
df_front = df[df["raw"] == df["front"]].copy()
counts["rows_front_contract"] = len(df_front)
