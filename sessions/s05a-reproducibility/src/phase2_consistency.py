"""S05A Phase 2: S03 vs S04 pipeline consistency for rules 1-4 and 6.

Method. The two implementations are not retranscribed here. Each module's
`main()` source is obtained with `inspect.getsource`, sliced at the
documented rule markers, dedented, and exec'd in a copy of that module's
own globals. The code executed IS the code in the S03/S04 files, character
for character. No S03 or S04 artifact is read for the panels and none is
written (output paths are never reached: the slices stop before any
to_parquet/json.dump).

Slices:
  S03 pipeline.main : start .. "# ---------------- rule 5"   -> rules 1-4 + 6
  S04 build.main    : start .. "# ---------------- R1"       -> rules 1-4
                      + R3 patch + 6
  S04 (no-R3)       : same, with the "# ---------------- R3 patch" block
                      removed -> rules 1-4 + 6, the like-for-like copy

The like-for-like test is S03 vs S04(no-R3). The R3 patch is a deliberate
S04 repair (DECISIONS item 15), so S03 vs S04(with-R3) is reported
separately as the expected, quantified divergence.

Comparison span: every session with trade date strictly before 2024-01-01,
both roots, both geometries (the rule-1-4/6 stage is pre-geometry, so a
single pass covers both). No sampling unless the 25-minute cap trips.
"""

import gc
import hashlib
import inspect
import json
import os
import sys
import textwrap
import time

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
RES = os.path.join(BASE, "results")
S03_SRC = os.path.join(ROOT, "sessions", "s03-data-noise", "src")
S04_SRC = os.path.join(ROOT, "sessions", "s04-repairs-diagnostics", "src")
CAP_SECONDS = 25 * 60

sys.path.insert(0, S03_SRC)
import pipeline as s03p                      # noqa: E402
sys.path.insert(0, S04_SRC)
import build as s04b                         # noqa: E402


def body(fn):
    src = inspect.getsource(fn)
    lines = src.split("\n")
    assert lines[0].strip().startswith("def "), lines[0]
    return textwrap.dedent("\n".join(lines[1:]))


def slice_to(src, marker):
    lines = src.split("\n")
    idx = [i for i, l in enumerate(lines) if marker in l]
    assert idx, f"marker not found: {marker}"
    return "\n".join(lines[:idx[0]])


def drop_block(src, start_marker, end_marker):
    lines = src.split("\n")
    a = [i for i, l in enumerate(lines) if start_marker in l]
    b = [i for i, l in enumerate(lines) if end_marker in l]
    assert a and b and a[0] < b[0], (a, b)
    return "\n".join(lines[:a[0]] + lines[b[0]:])


def sha_arr(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def digest(df, front, front_rows, label):
    """Canonical content digests of a rules-1-4+6 panel."""
    d = {}
    d["label"] = label
    d["n_rows_all"] = int(len(df))
    d["n_rows_front_contract"] = int(len(front_rows))
    key = df[["ts", "iid"]].copy()
    order = np.lexsort((key["iid"].values, key["ts"].values))
    for col in ["ts", "iid", "tdate", "ny_min"]:
        v = df[col].values
        if col == "tdate":
            v = pd.DatetimeIndex(v).asi8
        d[f"sha_{col}_sorted"] = sha_arr(v[order])
        d[f"sha_{col}_asis"] = sha_arr(v)
    raw_cat = pd.Categorical(df["raw"].values)
    d["sha_raw_sorted"] = hashlib.sha256(
        "|".join(df["raw"].values[order]).encode()).hexdigest()
    d["n_unique_iid"] = int(df["iid"].nunique())
    d["n_unique_raw"] = int(df["raw"].nunique())
    d["n_trade_dates"] = int(df["tdate"].nunique())
    d["tdate_min"] = str(pd.Timestamp(df["tdate"].min()).date())
    d["tdate_max"] = str(pd.Timestamp(df["tdate"].max()).date())
    f = front.sort_values(["root", "tdate"]).reset_index(drop=True)
    d["front_n"] = int(len(f))
    d["sha_front"] = hashlib.sha256(
        ("|".join(f["root"] + "@" + f["tdate"].astype(str) + "="
                  + f["front"])).encode()).hexdigest()
    bc = front_rows.groupby(["root", "tdate"]).size().sort_index()
    d["sha_session_bar_counts"] = hashlib.sha256(
        ("|".join(f"{r}@{pd.Timestamp(t).date()}={n}"
                  for (r, t), n in bc.items())).encode()).hexdigest()
    d["session_bar_count_total"] = int(bc.sum())
    d["n_sessions"] = int(len(bc))
    return d, f, bc


def run_variant(kind):
    t0 = time.time()
    if kind == "S03":
        code = slice_to(body(s03p.main), "# ---------------- rule 5")
        g = dict(s03p.__dict__)
    else:
        code = slice_to(body(s04b.main), "# ---------------- R1")
        if kind == "S04_noR3":
            code = drop_block(code, "# ---------------- R3 patch",
                              "# ---------------- rule 6 front selection")
        g = dict(s04b.__dict__)
    with open(os.path.join(RES, f"phase2_slice_{kind}.py"), "w") as fh:
        fh.write(code)
    exec(compile(code, f"<{kind}-slice>", "exec"), g)
    df = g["df"]
    front = g["front"]
    front_rows = g["df_front"] if kind == "S03" else g["dff"]
    d, ftab, bc = digest(df, front, front_rows, kind)
    d["elapsed_s"] = time.time() - t0
    ftab.to_parquet(os.path.join(RES, f"phase2_front_{kind}.parquet"))
    bc.rename("bars").reset_index().to_parquet(
        os.path.join(RES, f"phase2_barcounts_{kind}.parquet"))
    # keep a compact row-level key for differencing if needed
    small = df[["ts", "iid", "tdate"]].copy()
    small["tdate"] = pd.DatetimeIndex(small["tdate"]).asi8
    small.to_parquet(os.path.join(RES, f"phase2_rows_{kind}.parquet"))
    for k in list(g):
        if k not in ("__builtins__",):
            g[k] = None
    del g, df, front, front_rows
    gc.collect()
    return d


def main():
    t_start = time.time()
    results = {}
    for kind in ["S03", "S04_noR3", "S04_withR3"]:
        if time.time() - t_start > CAP_SECONDS:
            results["ABANDONED_AT_S"] = time.time() - t_start
            results["abandoned_before"] = kind
            break
        print(f"running {kind} ...", flush=True)
        results[kind] = run_variant(kind)
        print(json.dumps(results[kind], indent=1), flush=True)

    cmp_ = {}
    if "S03" in results and "S04_noR3" in results:
        a, b = results["S03"], results["S04_noR3"]
        fields = [k for k in a if k.startswith(("sha_", "n_", "front_",
                                                "session_"))]
        diffs = {k: [a[k], b[k]] for k in fields if a[k] != b[k]}
        cmp_["like_for_like_S03_vs_S04noR3"] = dict(
            identical=(len(diffs) == 0), differing_fields=diffs,
            fields_compared=len(fields))
    if "S03" in results and "S04_withR3" in results:
        a, c = results["S03"], results["S04_withR3"]
        fields = [k for k in a if k.startswith(("sha_", "n_", "front_",
                                                "session_"))]
        diffs = {k: [a[k], c[k]] for k in fields if a[k] != c[k]}
        cmp_["expected_R3_divergence_S03_vs_S04withR3"] = dict(
            identical=(len(diffs) == 0), differing_fields=diffs)
        # quantify the R3 delta at row level
        try:
            r03 = pd.read_parquet(os.path.join(RES, "phase2_rows_S03.parquet"))
            r04 = pd.read_parquet(
                os.path.join(RES, "phase2_rows_S04_withR3.parquet"))
            m = r03.merge(r04, on=["ts", "iid"], how="outer",
                          suffixes=("_s03", "_s04"), indicator=True)
            n_only03 = int((m["_merge"] == "left_only").sum())
            n_only04 = int((m["_merge"] == "right_only").sum())
            both = m[m["_merge"] == "both"]
            n_tdate_diff = int((both["tdate_s03"] != both["tdate_s04"]).sum())
            ex = both[both["tdate_s03"] != both["tdate_s04"]].head(10)
            cmp_["R3_row_level"] = dict(
                rows_only_in_S03=n_only03, rows_only_in_S04=n_only04,
                rows_with_different_tdate=n_tdate_diff,
                examples=[dict(ts=str(pd.Timestamp(r.ts)),
                               iid=int(r.iid),
                               tdate_s03=str(pd.Timestamp(r.tdate_s03).date()),
                               tdate_s04=str(pd.Timestamp(r.tdate_s04).date()))
                          for r in ex.itertuples()])
        except Exception as e:  # pragma: no cover
            cmp_["R3_row_level"] = dict(error=str(e))

    results["comparison"] = cmp_
    results["total_elapsed_s"] = time.time() - t_start
    results["cap_seconds"] = CAP_SECONDS
    results["span"] = ("every session with trade date strictly before "
                       "2024-01-01, both roots; rules 1-4/6 are "
                       "pre-geometry so one pass covers both geometries")
    results["sampled"] = False
    with open(os.path.join(RES, "phase2_consistency.json"), "w") as fh:
        json.dump(results, fh, indent=1)
    print(json.dumps(cmp_, indent=1))
    print("PHASE2 DONE", round(results["total_elapsed_s"], 1), "s")


if __name__ == "__main__":
    main()
