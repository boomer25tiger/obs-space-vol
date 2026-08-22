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

# ---------------- rule 6 front selection (S03 logic)
t2 = time.time()
vol = df.groupby(["root", "tdate", "raw"])["volume"].sum().reset_index()
front = vol.sort_values("volume").groupby(["root", "tdate"]).tail(1)
front = front.rename(columns={"raw": "front"})[["root", "tdate", "front"]]
df = df.merge(front, on=["root", "tdate"], how="left")
dff = df[df["raw"] == df["front"]].copy()
out["s03_raw_sessions_per_root"] = int(
    front[front.root == "ES"]["tdate"].nunique())
