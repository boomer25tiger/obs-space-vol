"""Build S03-report.md and S03-runlog.md."""

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(BASE, "results")
ROOT = os.path.dirname(os.path.dirname(BASE))
DATA = os.path.join(ROOT, "data", "GLBX-20260817-KAB3XQ8E4C")
VENV_PY = sys.executable

counts = json.load(open(os.path.join(RES, "s03_counts.json")))
gates = json.load(open(os.path.join(RES, "s03_gates.json")))
noise = pd.read_csv(os.path.join(RES, "s03_noise.csv"))
sig = pd.read_csv(os.path.join(RES, "s03_signature.csv"))

DESIGNATED = []
for d in counts["early_close_dates"]:
    dt = pd.Timestamp(d)
    if (dt.month == 11 and dt.dayofweek == 4) \
            or (dt.month == 7 and dt.day == 3) \
            or (dt.month == 12 and dt.day == 24):
        DESIGNATED.append(d)


def tbl(df, cols, ndig=6):
    L = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                cells.append(f"{v:.3g}" if abs(v) < 1e-2 or abs(v) > 1e4
                             else f"{v:.4f}")
            else:
                cells.append(str(v))
        L.append("| " + " | ".join(cells) + " |")
    return "\n".join(L)


def report():
    L = []
    L.append("# Session 3 report, data engineering and noise "
             "characterisation\n")
    L.append("Run date 2026-08-18. First session on real data. "
             "Pre-registration: `../PREREG.md`. Holdout respected: no row "
             "dated 2024-01-01 or later was loaded past the Phase 0 "
             "timestamp scan. NOTE: SCOPE.md is absent from the working "
             "tree (DECISIONS item 11); validation targets are the SCOPE "
             "figures quoted in the session instructions.\n")

    # ---------- inventory
    L.append("## Phase 0 inventory\n")
    L.append("Job `GLBX-20260817-KAB3XQ8E4C`, four files:\n")
    L.append("| file | size (bytes) | format | sha256 (manifest, verified) |")
    L.append("|---|---|---|---|")
    L.append("| metadata.json | 710 | JSON | 718dca4b... match |")
    L.append("| manifest.json | 1,475 | JSON | (no self-hash) |")
    L.append("| condition.json | 612,811 | JSON | aafd33b7... match |")
    L.append("| glbx-mdp3-20100606-20260815.ohlcv-1m.dbn.zst | 190,944,913 "
             "| DBN v3, zstd | 08cae0bf... match |")
    L.append("")
    L.append(
        "Metadata: dataset `GLBX.MDP3`, schema `ohlcv-1m` (minute "
        "aggregate OHLCV, as required), encoding `dbn` + `zstd`, "
        "`stype_in=parent`, `stype_out=instrument_id`, symbols "
        "`NQ.FUT`, `ES.FUT` (both roots requested), start "
        "1275782400000000000 (2010-06-06T00:00Z), end 1786838400000000000 "
        "(2026-08-15T00:00Z), limit none, pretty_px/pretty_ts/map_symbols/"
        "split_symbols all false.\n")
    L.append(
        "There is no separate symbology.json in the delivery (manifest "
        "lists exactly the four files above); the symbology ships embedded "
        "in the DBN metadata header, which is the same job symbology and "
        "is date-aware. Structure: 400 raw symbols, 713 "
        "(symbol, start_date, end_date, instrument_id) intervals, 550 of "
        "them calendar spreads (hyphenated), 366 intervals with prefix ES "
        "and 347 with prefix NQ. 305 raw symbols map to more than one "
        "instrument id across the file span - the id-recycling problem the "
        "date-aware rule exists for (e.g. ESH3 -> id 23970 for 2011-12-04 "
        "to 2013-04-08 and id 206299 for 2021-06-03 to 2023-04-04).\n")
    L.append(
        "Condition file: 5,107 dated entries 2010-06-06 to 2026-08-15; "
        "5,076 `available`, 31 `degraded`, of which 20 fall before "
        "2024-01-01: 2014-06-11/12/13/15, 2014-09-22/23/24/25, 2017-11-13, "
        "2018-10-21, 2019-01-15, 2019-02-22, 2019-03-13, 2019-03-26, "
        "2020-02-27/28, 2020-06-30, 2020-07-01, 2021-12-05, 2022-01-02. "
        "Four degraded dates fall inside the 2016-2023 estimation sample "
        "years with RTH content (2017-11-13, 2019-x4, 2020-x4); none were "
        "excluded (no SCOPE rule covers them); they are flagged here.\n")
    L.append(
        "Data (from the file itself): 14,165,173 rows total; timestamp "
        "span 2010-06-06T22:00:00Z to 2026-08-14T20:59:00Z (covers "
        "2016-01-01..2023-12-31, so the Phase 0 stop conditions do not "
        "trigger); 11,318,126 rows before 2024-01-01 were extracted and "
        "nothing later was decoded further. Columns: length, rtype, "
        "publisher_id, instrument_id, ts_event, open, high, low, close, "
        "volume (prices int64 at 1e-9 scale). Roots present after "
        "resolution: ES and NQ only.\n")

    # ---------- ledger
    L.append("## Phase 2 engineering ledger (counts in application "
             "order)\n")
    ec = counts["early_close_sessions_by_root"]
    fr = counts["front_selection"]
    L.append(f"""| step | count |
|---|---|
| rows before 2024-01-01 (Phase 0 extract) | {counts['rows_pre2024']:,} |
| rule 1 unresolved (instrument_id, date) rows | {counts['rows_unresolved_symbol']:,} |
| rule 2 calendar-spread rows filtered | {counts['rows_spread_filtered']:,} |
| non-positive price rows before filter (SCOPE expects 573,473) | {counts['nonpositive_price_rows_before_filter']:,} |
| non-positive price rows after filter | {counts['nonpositive_price_rows_after_filter']:,} |
| rule 3 rows by root | ES {counts['rows_by_root']['ES']:,}, NQ {counts['rows_by_root']['NQ']:,} |
| rule 4 rows outside 2016-2023 by trade date | {counts['rows_outside_2016_2023_by_trade_date']:,} |
| rows in estimation sample | {counts['rows_in_sample']:,} |
| raw trade sessions per root | {counts['front_selection']['ES']['sessions']:,} |
| weekend trade dates (anomaly, reported) | {counts['weekend_trade_dates']} |
| rule 6 front contracts used | ES {fr['ES']['n_contracts']}, NQ {fr['NQ']['n_contracts']} |
| rule 6 median holding, sessions / calendar days (SCOPE ~91 days) | ES {fr['ES']['median_holding_sessions']:.0f} / {fr['ES']['median_holding_calendar_days']:.0f}, NQ {fr['NQ']['median_holding_sessions']:.0f} / {fr['NQ']['median_holding_calendar_days']:.0f} |
| rule 5 early-close sessions excluded (SCOPE expects ~18 designated) | ES {ec['ES']}, NQ {ec['NQ']} (see below) |
| rule 7 roll sessions +/-1 excluded | ES {counts['roll_sessions_excluded_pm1']['ES']}, NQ {counts['roll_sessions_excluded_pm1']['NQ']} |
| final sessions per root | ES {counts['sessions_final_by_root']['ES']:,}, NQ {counts['sessions_final_by_root']['NQ']:,} |
| final rows | {counts['rows_final']:,} |
""")
    L.append(
        f"Early-close detail: the rule catches every session whose day "
        f"portion halts before 15:00 New York. Of the {ec['ES']} caught, "
        f"{len(DESIGNATED)} are the designated half-days SCOPE's ~18 "
        "refers to (day after Thanksgiving, July 3, Christmas Eve): "
        + ", ".join(DESIGNATED) + ". The remainder are full-holiday "
        "shortened sessions (MLK, Presidents, Memorial, July 4, Labor, "
        "Thanksgiving Day), which halt at the same clock time and are "
        "excluded on the same evidence. All excluded dates: "
        + ", ".join(counts["early_close_dates"]) + ".\n")
    L.append(
        "Session-count reconciliation: 2,066 raw sessions per root over "
        "2016-2023; SCOPE's ~2,742 'from 2016' is consistent with the "
        "file's full 2016-2026.6 span (2,066 + ~675 projected sessions "
        "2024-2026), not with 2016-2023 alone.\n")

    # ---------- gates
    L.append("## Phase 3 validation gates (numbers, no flags)\n")
    g = gates
    L.append(f"- Price scaling: int64 / 1e9 confirmed; decoded ranges ES "
             f"[{g['price_scale_min_max_by_root']['ES'][0]:,.2f}, "
             f"{g['price_scale_min_max_by_root']['ES'][1]:,.2f}], NQ "
             f"[{g['price_scale_min_max_by_root']['NQ'][0]:,.2f}, "
             f"{g['price_scale_min_max_by_root']['NQ'][1]:,.2f}].")
    L.append(f"- Tick grid: {g['tick_violations_0p25']} of "
             f"{g['nonzero_increments']:,} non-zero close-to-close "
             "increments violate the 0.25 tick multiple.")
    L.append("- Bars per Globex session by year (mean / p5 / max):")
    for k, v in g["bars_per_session_by_year"].items():
        L.append(f"    - {k}: {v['mean']:.1f} / {v['p5']:.0f} / {v['max']}")
    L.append("- Fill ratio (bars/1380) by year: "
             + ", ".join(f"{k} {v:.4f}" for k, v in
                         g["fill_ratio_globex_by_year"].items())
             + " - consistent with SCOPE's 95-100% from 2016.")
    L.append("- Zero-volume bar fraction by year: "
             + ", ".join(f"{k} {v:.5f}" for k, v in
                         g["zero_volume_fraction_by_year"].items()))
    L.append("- Zero-volume fraction by NY hour: "
             + ", ".join(f"{h:02d}h {v:.4f}" for h, v in
                         sorted(((int(h), v) for h, v in
                                 g["zero_volume_fraction_by_hour_ny"].items()))))
    L.append("- 1-minute log-return moments by year "
             "(n / mean / sd / skew / kurtosis):")
    for k, v in g["return_moments_1min_by_year"].items():
        L.append(f"    - {k}: {v['n']:,} / {v['mean']:.2e} / "
                 f"{v['sd']:.2e} / {v['skew']:.2f} / {v['kurt']:.0f}")
    out = g["outliers_gt_10sd_by_year_flagged_not_removed"]
    L.append(f"- Outliers |r| > 10 sd(year, root): total "
             f"{sum(out.values()):,}, by year "
             + ", ".join(f"{k} {v}" for k, v in out.items())
             + ". Flagged and counted, none removed.\n")

    # ---------- signature + noise
    L.append("## Phase 4 signature plots and noise measurement\n")
    L.append("Raw signature tables (mean daily RV against M), full sample; "
             "figure: `s03_signature.png`.\n")
    for root in ["ES", "NQ"]:
        for geom in ["GLOBEX", "RTH"]:
            s = sig[(sig.root == root) & (sig.geom == geom)
                    & (sig.group == "all")]
            L.append(f"**{root} {geom}** (n_days "
                     f"{int(s['n_days'].iloc[0])}): "
                     + ", ".join(f"M={int(r.M)}: {r.mean_rv:.3e}"
                                 for r in s.itertuples()))
    L.append("")
    n_all = noise[noise.group == "all"]
    L.append("### Signature linearity (takes precedence over estimates)\n")
    L.append(
        "R^2 of the mean-RV-on-M regression: "
        + ", ".join(f"{r.root} {r.geom} {r.signature_R2:.2f}"
                    for r in n_all.itertuples()) + ".\n\n"
        "The signature plots rise from coarse to fine M by only ~4-10% of "
        "the level, and the rise is not cleanly linear in M "
        "(NQ RTH R^2 = 0.14; ES RTH 0.65; NQ GLOBEX 0.68; ES GLOBEX "
        "0.87). Per the pre-registration, weak linearity means the "
        "additive iid noise model is at best marginal at 1-minute "
        "sampling and the point estimates below inherit that caveat. At "
        "this sampling frequency the noise contribution to RV is close to "
        "the resolution limit of the signature method.\n")
    L.append("### N1 and N2, full sample\n")
    L.append(tbl(n_all, ["root", "geom", "n_days", "intercept_EIV",
                         "omega2_N1", "omega2_N2", "NSR_N1", "NSR_N2",
                         "signature_R2"]))
    L.append("")
    L.append("### By year\n")
    ny = noise[noise.group.str.startswith("y")]
    L.append(tbl(ny, ["root", "geom", "group", "NSR_N1", "NSR_N2",
                      "signature_R2"]))
    L.append("")
    L.append("### By volatility tercile (daily RV at coarsest M)\n")
    nt = noise[noise.group.str.startswith("terc")]
    L.append(tbl(nt, ["root", "geom", "group", "NSR_N1", "NSR_N2",
                      "signature_R2"]))
    L.append("")
    L.append("### N1 vs N2 disagreement (reported, not averaged)\n")
    L.append(
        "N2 exceeds N1 by roughly one order of magnitude in every cell "
        "(full-sample ratios: "
        + ", ".join(f"{r.root} {r.geom} {r.omega2_N2/r.omega2_N1:.0f}x"
                    for r in n_all.itertuples())
        + "). Mechanism, as documented in DECISIONS item 12: N2 = "
        "RV_finest/(2n) assumes noise dominates the finest-grid RV "
        "(2n*omega^2 >> IV); at 1-minute bars RV_finest is almost "
        "entirely IV, so N2 returns approximately IV/(2n) - an upper "
        "bound, not a noise measurement. This is the same degeneracy S02 "
        "identified for estimator E6 at NSR -> 0.\n")
    L.append("### Placement relative to the S02 sweep (1e-5 to 1e-1)\n")
    lo1 = n_all["NSR_N1"].min()
    hi1 = n_all["NSR_N1"].max()
    lo2 = n_all["NSR_N2"].min()
    hi2 = n_all["NSR_N2"].max()
    L.append(
        f"Measured NSR by N1 spans {lo1:.1e} to {hi1:.1e} across "
        "instrument x geometry (NQ GLOBEX lowest, ES RTH highest); by N2, "
        f"{lo2:.1e} to {hi2:.1e}. Both ranges sit inside the S02 sweep "
        "[1e-5, 1e-1], in its bottom two decades: N1 places ES/NQ at "
        "1-minute sampling at the extreme low end of the sweep "
        "(1e-5 to 1e-4), N2 - which the mechanism above marks as an "
        "upper bound - at 4e-4 to 1.4e-3. No measured value approaches "
        "the upper decades of the S02 sweep.\n")

    with open(os.path.join(RES, "S03-report.md"), "w") as fh:
        fh.write("\n".join(L))
    print("report written")


def runlog():
    freeze = subprocess.run([VENV_PY, "-m", "pip", "freeze"],
                            capture_output=True, text=True).stdout.strip()
    t2 = json.load(open(os.path.join(RES, "s03_timers_p2.json")))
    t34 = json.load(open(os.path.join(RES, "s03_timers_p34.json")))
    L = []
    L.append("# Session 3 run log\n")
    L.append(f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} (UTC).\n")
    L.append("## Wall clock per phase\n")
    L.append("| phase | wall clock |")
    L.append("|---|---|")
    L.append("| Phase 0 inventory + pre-2024 extraction (streamed, official "
             "databento reader) | ~6 min (26 s decode CPU; rest host "
             "contention from the still-running S02 grid) |")
    L.append("| Phase 1 freeze | ~1 min |")
    L.append("| Phase 2 rules 1-7 (two passes: one detector fix, both "
             "logged) | 5m06s + 5m07s wall |")
    for k, v in {**t2, **t34}.items():
        if isinstance(v, float):
            L.append(f"| Phase 2/3 step `{k}` | {v:.1f} s CPU-side |")
    L.append("| Phase 4 panels + noise + figure | 17 s |")
    L.append("| Phase 5 reports | ~1 min |")
    L.append("")
    L.append("Total S03 wall clock ~45 min, inside the 90-minute budget. "
             "The S02 grid continued running throughout (its own budget "
             "accounting lives in the S02 run log); S03 was executed "
             "single-threaded to avoid starving it.\n")
    L.append("## File checksums (sha256, verified against manifest)\n")
    L.append("```text")
    L.append("condition.json aafd33b74eccb88295d3183bc1612b341c93e6c0e1ec44e38b73b8d7bbab3699  (match)")
    L.append("metadata.json  718dca4b0d756d07e5e6db53a97a6b63b80aaf13dad18adf8486c5479c4a8a7b  (match)")
    L.append("glbx-mdp3-20100606-20260815.ohlcv-1m.dbn.zst 08cae0bfac3eaafee5a22d2ce91076273c95166113336aa34922264fdb3fdf7f  (match)")
    L.append("manifest.json  ebc21d96a8de8522... (manifest carries no self-hash)")
    L.append("```\n")
    L.append("## Package versions (pip freeze)\n")
    L.append("```text\n" + freeze + "\n```\n")
    L.append("## Notes\n")
    L.append(
        "- Holdout: the Phase 0 stream filtered on ts_event < 2024-01-01 "
        "at decode time; only min/max timestamps of the full file were "
        "read (span check mandated by Phase 0). No 2024+ row was decoded "
        "into any dataframe or file.\n"
        "- Early-close detector was corrected once (session-max NY minute "
        "-> day-portion max; first pass reported 0, second 68); both "
        "passes are in the shell log, no data-driven tuning involved.\n"
        "- One weekend trade date appears in the raw session cut "
        "(reported in the ledger); it survives no exclusion rule and is "
        "present in the final panel if it passed all rules.\n"
        "- Degraded-condition dates inside the sample (condition.json): "
        "flagged in the report; no exclusion rule covers them.\n")
    with open(os.path.join(RES, "S03-runlog.md"), "w") as fh:
        fh.write("\n".join(L))
    print("runlog written")


if __name__ == "__main__":
    report()
    runlog()
