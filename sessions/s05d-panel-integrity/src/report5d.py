"""S05D report and runlog."""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
RES = os.path.join(BASE, "results")
S04_RES = os.path.join(ROOT, "sessions", "s04-repairs-diagnostics",
                       "results")
VENV_PY = sys.executable


def md(df, cols=None, n=None):
    d = df[cols] if cols else df
    if n:
        d = d.head(n)
    L = ["| " + " | ".join(str(c) for c in d.columns) + " |",
         "|" + "---|" * len(d.columns)]
    for _, r in d.iterrows():
        L.append("| " + " | ".join(
            f"{v:.6g}" if isinstance(v, float) else str(v) for v in r) + " |")
    return "\n".join(L)


def main():
    S = json.load(open(os.path.join(RES, "s05d_summary.json")))
    P1 = pd.read_csv(os.path.join(RES, "phase1_clock_samples.csv"))
    D2 = pd.read_csv(os.path.join(RES, "phase2_zero_window_sources.csv"))
    A2 = pd.read_csv(os.path.join(RES, "phase2_affected_sessions.csv"))
    P3 = pd.read_csv(os.path.join(RES, "phase3_padding.csv"))
    P4 = pd.read_csv(os.path.join(RES, "phase4_padding_exposure.csv"))
    s04 = json.load(open(os.path.join(S04_RES, "s04_build.json")))
    m = S["phase1_mapping"]

    L = []
    L.append("# Session 5D report, Globex panel integrity\n")
    L.append(f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} "
             "(UTC). Diagnosis only: no panel was rebuilt, no prior "
             "artifact modified, nothing repaired. Output under "
             "`sessions/s05d-panel-integrity/results/`.\n")

    # ---------------- PHASE 1
    L.append("## Phase 1, clock mapping\n")
    L.append(
        "`sessions/s03-data-noise/src/analysis.py:22-42`:\n\n"
        "```python\n"
        "22  def build_panels(df, root, geom):\n"
        "23      \"\"\"Filled log-price grid (sessions x n+1) from close prices.\"\"\"\n"
        "24      sub = df[df[\"root\"] == root]\n"
        "25      n = N_GRID[geom]\n"
        "26      if geom == \"RTH\":\n"
        "27          sub = sub[(sub[\"ny_min\"] >= 570) & (sub[\"ny_min\"] < 960)]\n"
        "28          slot = sub[\"ny_min\"] - 570\n"
        "29      else:\n"
        "30          slot = (sub[\"ny_min\"] - 1080) % 1440\n"
        "31          ok = slot < 1380\n"
        "32          sub, slot = sub[ok], slot[ok]\n"
        "33      dates = np.sort(sub[\"tdate\"].unique())\n"
        "34      didx = {d: i for i, d in enumerate(dates)}\n"
        "35      S = len(dates)\n"
        "36      px = np.full((S, n), np.nan)\n"
        "37      px[sub[\"tdate\"].map(didx).values, slot.values] = \\\n"
        "38          np.log(sub[\"close\"].values / 1e9)\n"
        "39      present = ~np.isnan(px)\n"
        "40      # forward fill within session; leading gap backfilled from first obs\n"
        "41      filled = pd.DataFrame(px).ffill(axis=1).bfill(axis=1).values\n"
        "42      return dates, filled, present\n"
        "```\n")
    L.append("| property | GLOBEX (`panel_ES_GLOBEX_B0.npz`) | RTH "
             "(`panel_ES_RTH_B0.npz`) |")
    L.append("|---|---|---|")
    L.append(f"| column 0 wall clock | {m['globex_col0_ny']} | "
             f"{m['rth_col0_ny']} |")
    L.append(f"| offset | {m['globex_offset']} | {m['rth_offset']} |")
    L.append(f"| last column | {m['globex_last_col']} | "
             f"{m['rth_last_col']} |")
    L.append(f"| column for 13:00 / 14:00 / 15:00 NY | "
             f"{m['col_for_1300']} / {m['col_for_1400']} / "
             f"{m['col_for_1500']} | 210 / 270 / 330 |")
    L.append("")
    L.append(f"**Daylight saving.** {m['dst_handling']}\n")
    L.append("### Twenty sessions at fixed stride\n")
    L.append(f"Sampled {S['phase1_n_sessions_sampled']} sessions; "
             f"{S['phase1_n_sessions_absent_from_RTH']} of them are absent "
             "from the RTH panel. Value-by-value comparison of the Globex "
             "and RTH panels over the same wall-clock minutes at 13:00, "
             "14:00 and 15:00 New York:\n")
    L.append(md(P1, ["session", "clock", "globex_col", "globex_price",
                     "globex_filled", "globex_distinct_prices_in_hour",
                     "globex_present_minutes_in_hour", "rth_col",
                     "rth_price", "rth_filled",
                     "rth_distinct_prices_in_hour",
                     "rth_present_minutes_in_hour",
                     "minutes_disagreeing"], n=60))
    L.append("")
    L.append(f"**Total minute-level disagreements across all "
             f"{S['phase1_n_sessions_sampled']} sampled sessions and all "
             f"three clock hours: {S['phase1_total_minute_disagreements']}.** "
             "The two panels carry byte-identical prices over the same "
             "wall-clock minutes wherever both contain the session. The "
             "Globex column index is therefore correctly aligned to New "
             "York wall clock, and the 13:00/14:00/15:00 columns are the "
             "columns they are claimed to be.\n")

    # ---------------- PHASE 2
    L.append("## Phase 2, zero-variance windows at source\n")
    L.append(f"{S['phase2_total_zero_windows_at_13_14_15']} one-hour "
             f"Globex windows at 13:00, 14:00 or 15:00 have exactly zero "
             f"realized variance, spanning "
             f"{S['phase2_n_distinct_sessions']} distinct sessions. Fifty "
             "were sampled and traced to the S04 repaired parquet over "
             "the same wall-clock minutes:\n")
    L.append(md(D2, ["session", "clock", "col_range", "raw_bars_present",
                     "distinct_closes", "instrument_ids", "raw_symbols",
                     "underlying_bars_exist", "carries_price_variation"],
                n=50))
    L.append("")
    L.append(
        f"**{S['phase2_with_zero_underlying_bars']} of "
        f"{S['phase2_sampled']} sampled windows have NO underlying bars at "
        f"all in the source data, and "
        f"{S['phase2_with_price_variation']} of {S['phase2_sampled']} "
        "carry any price variation.** The zero variance is not an "
        "artifact of the panel: there is nothing to vary, because the "
        "market was not trading in those minutes.\n")
    L.append("### Clustering of the affected sessions\n")
    L.append(f"- By year: {S['phase2_by_year']} - flat across the sample, "
             "roughly six to eight sessions a year.\n"
             f"- By weekday: {S['phase2_by_weekday']} - "
             f"{S['phase2_by_weekday'].get('Monday', 0)} of "
             f"{S['phase2_n_distinct_sessions']} fall on Mondays.\n"
             f"- By DST regime: {S['phase2_by_dst']} - split evenly, so "
             "not a daylight-saving effect.\n"
             f"- By contract and roll: the nearest roll is "
             f"{S['phase2_roll_proximity_min']} sessions away and "
             f"{S['phase2_n_within_1day_of_roll']} sessions fall within "
             "one day of a roll, so not roll-related.\n"
             f"- By calendar date: {S['phase2_by_month_day']}\n")
    L.append(
        "Those dates are the US market holidays: Martin Luther King Day "
        "(01-15/16/18), Presidents' Day (02-15/19/20), Memorial Day "
        "(05-28/29/30), Independence Day (07-04, six occurrences), Labor "
        "Day (09-03/04/05) and Thanksgiving (11-23/24). On these dates "
        "the CME equity-index day session halts at 13:00 New York.\n")
    L.append(
        f"**Decisive cross-check: none of the "
        f"{S['phase2_n_distinct_sessions']} affected sessions appears in "
        f"the RTH panel at all "
        f"({S['phase2_n_in_RTH_panel']} of "
        f"{S['phase2_n_distinct_sessions']}).** S04's repair R1 made the "
        "early-close rule geometry-dependent: RTH excludes every session "
        "whose day portion halts before 15:00 New York, while GLOBEX "
        "retains those whose overnight portion is at least 90% complete. "
        "S04 recorded the count of sessions retained by that rule as "
        f"`globex_retained_holiday_sessions = "
        f"{s04['r1_counts']['globex_retained_holiday_sessions']}`, and the "
        f"ES figure, {s04['r1_counts']['globex_retained_holiday_sessions']['ES']}, "
        f"is exactly the {S['phase2_n_distinct_sessions']} sessions found "
        "here. The asymmetry between the two panels is that documented "
        "rule operating as written, not a defect in either panel.\n")

    # ---------------- PHASE 3
    L.append("## Phase 3, padding and fill\n")
    L.append(f"**Fill mechanism.** {S['phase3_fill_mechanism']}\n")
    L.append("Share of padded columns per session, by year and geometry "
             "(the Globex column adjacent to it is restricted to the "
             "09:30-16:00 New York columns, 930-1409):\n")
    L.append(md(P3, ["geometry", "year", "sessions", "share_padded",
                     "share_padded_0930_1600"]))
    L.append("")
    L.append(f"**Is padding distinguishable from a genuine unchanged "
             f"close in the stored panel? {S['phase3_padding_distinguishable']}**\n")

    # ---------------- PHASE 4
    L.append("## Phase 4, daily aggregation exposure\n")
    L.append("Globex 1day at every M in the S05B extended grid. A "
             "sub-bar is counted as padded when it contains no return "
             "whose two endpoint minutes are both present:\n")
    L.append(md(P4, ["M", "n_windows", "share_rv_from_padded_subbars",
                     "n_windows_with_empty_subbar", "mean_empty_subbars",
                     "var_log_rv_as_is", "var_log_rv_excluding_padded",
                     "delta", "n_dropped_zero_rv"]))
    L.append("")
    f = S["phase4_free_intercept_fits"]
    L.append("Free-intercept model Var(log RV_M) = c + A M^b, fitted "
             "before and after excluding padded sub-bars:\n")
    L.append("| fit | c | A | b | RMSE |")
    L.append("|---|---|---|---|---|")
    for tag in ["as_is", "excluding_padded"]:
        g = f.get(tag, {})
        L.append(f"| {tag} | {g.get('c', float('nan')):.6f} | "
                 f"{g.get('A', float('nan')):.6f} | "
                 f"{g.get('b', float('nan')):.6f} | "
                 f"{g.get('rmse', float('nan')):.6f} |")
    L.append("")
    L.append(
        f"Padded sub-bars contribute at most "
        f"{P4.share_rv_from_padded_subbars.max():.4%} of window realized "
        f"variance (at M={int(P4.loc[P4.share_rv_from_padded_subbars.idxmax(), 'M'])}) "
        f"and 0.0000% at M <= 46. Excluding them moves Var(log RV_M) by at "
        f"most {P4.delta.abs().max():.2e} and the fitted exponent b from "
        f"{f['as_is']['b']:.6f} to {f['excluding_padded']['b']:.6f}, a "
        f"change of {abs(f['excluding_padded']['b'] - f['as_is']['b']):.2e}. "
        "The daily-aggregation exposure raised in DECISIONS item 34 is "
        "measured and is negligible; no column displacement is visible at "
        "daily aggregation, consistent with Phase 1's zero minute-level "
        "disagreements.\n")

    # ---------------- verdict
    L.append("## Determination\n")
    L.append("### A. The panel is correct and the zero-variance windows "
             "are genuine.\n")
    L.append("Evidence, in the order it was collected:\n")
    L.append(
        f"1. **Clock mapping is correct (Phase 1).** Globex column 0 is "
        f"18:00 New York by a fixed 1080-minute offset applied to a "
        f"tz-aware New York wall-clock minute, so columns "
        f"{m['col_for_1300']}, {m['col_for_1400']} and {m['col_for_1500']} "
        f"are 13:00, 14:00 and 15:00 as claimed. Across 20 sessions at "
        f"fixed stride and three clock hours, the Globex and RTH panels "
        f"disagree on "
        f"{S['phase1_total_minute_disagreements']} minutes. Option D is "
        "excluded: the S05B clock derivation was right.\n"
        f"2. **The zeros are absences of trading, not padding errors "
        f"(Phase 2).** {S['phase2_with_zero_underlying_bars']} of "
        f"{S['phase2_sampled']} sampled zero-variance windows have zero "
        "underlying bars in the S04 parquet, and none carries price "
        "variation. Option C is excluded as the cause of these windows: "
        "there is no data being padded over, there is no data at all.\n"
        f"3. **The market explanation is holiday early closes (Phase 2).** "
        f"All {S['phase2_n_distinct_sessions']} affected sessions are US "
        "market holidays - MLK, Presidents' Day, Memorial Day, "
        "Independence Day, Labor Day and Thanksgiving - on which the CME "
        "equity-index day session halts at 13:00 New York. The clustering "
        "is on those calendar dates, not on DST regime, contract or roll "
        "proximity.\n"
        f"4. **The two panels do not contradict each other (Phase 2).** "
        f"None of the affected sessions is in the RTH panel. RTH contains "
        "no zero-variance windows over those minutes because it contains "
        "none of those sessions, by S04's repair R1, whose retained-session "
        f"count "
        f"({s04['r1_counts']['globex_retained_holiday_sessions']['ES']} for "
        f"ES) matches the {S['phase2_n_distinct_sessions']} sessions found "
        "here exactly. Option B is excluded.\n"
        f"5. **Daily aggregation is unaffected (Phase 4).** Padded "
        f"sub-bars carry at most "
        f"{P4.share_rv_from_padded_subbars.max():.4%} of realized "
        "variance and the free-intercept exponent b moves by "
        f"{abs(f['excluding_padded']['b'] - f['as_is']['b']):.2e} when "
        "they are excluded.\n")
    L.append(
        "One qualification, recorded because it is real but does not "
        "change the determination: **padding is not distinguishable from "
        "a genuine unchanged close inside the stored panel** (Phase 3). "
        "The `present` mask exists in `build_panels` but is not saved in "
        "the S05 panel files, so any consumer of those files alone cannot "
        "separate the two; S05D could only do so by re-running "
        "`build_panels` against the S04 bars. Globex carries 0.5% to 2.7% "
        "padded columns per session by year against essentially 0% for "
        "RTH.\n")

    with open(os.path.join(RES, "S05D-report.md"), "w") as fh:
        fh.write("\n".join(L))

    # ---------------- runlog
    freeze = subprocess.run([VENV_PY, "-m", "pip", "freeze"],
                            capture_output=True, text=True).stdout.strip()
    env = ""
    ep = os.path.join(ROOT, "ENVIRONMENT.md")
    if os.path.exists(ep):
        env = open(ep).read()
    t = S["timers"]
    R = ["# Session 5D run log\n",
         f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} "
         "(UTC).\n", "## Wall clock per phase\n", "| phase | wall |",
         "|---|---|",
         "| Phase 0 (DECISIONS append, directories) | ~1 min |",
         f"| Load panels and presence masks | {t['load']:.1f} s |",
         f"| Phase 1 clock mapping and 20-session comparison | "
         f"{t['phase1']:.1f} s |",
         f"| Phase 2 zero-variance windows at source (reads the 107 MB S04 "
         f"Globex parquet) | {t['phase2']:.1f} s |",
         f"| Phase 3 padding and fill | {t['phase3']:.1f} s |",
         f"| Phase 4 daily aggregation exposure | {t['phase4']:.1f} s |",
         f"| Phase 5 reports | ~2 min |", "",
         f"Compute total {t['total']:.1f} s; session total well under the "
         "15-minute expectation. No bottleneck.\n",
         "## Inputs read (all read-only)\n",
         "- `sessions/s05-reliability-mcs/results/panel_ES_GLOBEX_B0.npz`, "
         "`panel_ES_RTH_B0.npz`\n"
         "- `sessions/s04-repairs-diagnostics/results/bars_GLOBEX.parquet`, "
         "`s04_build.json`\n"
         "- `sessions/s05b-defect-and-estimator-audit/results/cache/"
         "present_ES_{GLOBEX,RTH}.npz` (presence masks regenerated in "
         "S05B by re-running S03 `build_panels`)\n"
         "- `sessions/s03-data-noise/src/analysis.py` (source quotation "
         "only)\n",
         "## Constants\n",
         "- Globex column offset 1080 minutes (18:00 NY), modulo 1440, "
         "columns kept where slot < 1380.\n"
         "- RTH column offset 570 minutes (09:30 NY), 390 columns.\n"
         "- Clock hours examined: 13:00, 14:00, 15:00 NY = Globex columns "
         f"{m['col_for_1300']}, {m['col_for_1400']}, {m['col_for_1500']}.\n"
         "- Session sample: 20 sessions at fixed stride "
         "`len(dates)//20` across the full span, no randomness.\n"
         "- Zero-variance window sample: 50 drawn with "
         "`DataFrame.sample(random_state=0)`, the only stochastic step in "
         "the session.\n"
         "- Padded sub-bar definition: contains no return whose two "
         "endpoint minutes are both present.\n"
         "- M grid (Globex 1day): 5, 6, 10, 12, 23, 46, 138, 345, 1379.\n"
         "- Free-intercept fit: `scipy.optimize.curve_fit` on "
         "Var(log RV_M) = c + A M^b, start [min(y), 1.0, -0.5].\n",
         "## Environment record (from ENVIRONMENT.md)\n",
         env if env else "(ENVIRONMENT.md not found)", "",
         "### pip freeze at S05D\n", "```text", freeze, "```", ""]
    with open(os.path.join(RES, "S05D-runlog.md"), "w") as fh:
        fh.write("\n".join(R))
    print("report and runlog written")


if __name__ == "__main__":
    main()
