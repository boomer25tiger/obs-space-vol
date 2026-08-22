"""Build S04-report.md, S04-runlog.md, and the DECISIONS.md append."""

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
RES = os.path.join(BASE, "results")
VENV_PY = sys.executable

b = json.load(open(os.path.join(RES, "s04_build.json")))
d = json.load(open(os.path.join(RES, "s04_diagnostics.json")))


def dtail_block(tag):
    x = d[f"dtail_{tag}"]
    L = [f"**{tag}** ({x['n_extremes']:,} extremes / "
         f"{x['n_returns']:,} returns, base rate {x['H2_base_rate']:.2e})\n"]
    L.append(f"- H1: share in top-1% dates {x['H1_share_in_top1pct_dates']:.3f}; "
             f"share within 5 min of 08:30/10:00/14:00 NY "
             f"{x['H1_share_within_5min_of_0830_1000_1400']:.3f}. "
             f"{x['H1_event_dates_note']}.")
    c = x["H2_called_out_minutes"]
    L.append("- H2 called-out minutes (rate, xbase): "
             + "; ".join(f"{k}: {v['rate']:.2e} ({v['rel_to_base']:.1f}x)"
                         for k, v in c.items())
             + f". Full 1,440-minute table: `s04_h2_minute_rates_{tag}.csv`.")
    h3 = x["H3_rate_by_roll_distance"]
    for root, tab in h3.items():
        near = {k: v for k, v in sorted(tab.items(), key=lambda kv: int(kv[0]))
                if abs(int(k)) <= 3}
        L.append(f"- H3 {root} rate by distance from roll (d: rate/n_sess): "
                 + "; ".join(f"{k}: {v['rate']:.2e}/{v['n_sessions']}"
                             for k, v in near.items())
                 + " (full -10..+10 in JSON)")
    g4 = x["H4_gini_extremes_per_date"]
    L.append(f"- H4: Gini of extremes per date ES {g4['ES']:.3f}, "
             f"NQ {g4['NQ']:.3f}. Hill alpha and Student-t expected vs "
             "observed extremes by (root, year):")
    for k, v in x["H4_hill_and_t_null"].items():
        L.append(f"    - {k}: alpha {v['hill_alpha']:.2f}, t-null expects "
                 f"{v['expected_extremes_t']:.1f}, observed {v['observed']}")
    e5, u5 = x["H5_prev_stale_extremes"], x["H5_prev_stale_unconditional"]
    L.append(f"- H5: preceding stale-run length, extremes vs unconditional: "
             f"mean {e5['mean']:.3f} vs {u5['mean']:.3f}; share with >=1 "
             f"stale minute before: {e5['share_ge1']:.4f} vs "
             f"{u5['share_ge1']:.4f}; share >=5: {e5['share_ge5']:.4f} vs "
             f"{u5['share_ge5']:.4f}.")
    return "\n".join(L) + "\n"


def drq_block(geom, tag):
    rows = d[f"drq_{geom}_{tag}"]
    L = []
    yr_rows = [r for r in rows if r["year"] != 0]
    acf_rows = [r for r in rows if r["year"] == 0]
    finest = {("ES",): None, ("NQ",): None}
    L.append(f"**{geom} {tag}** - per-year RQ statistics at the finest M "
             "(full grid for every M, both quarticity variants and all "
             "truncation levels, in `s04_diagnostics.json`):\n")
    L.append("| root | M | year | n | RQ mean | RQ median | RQ p99 | RQ max "
             "| top-1 share | RQ/TQ med | RQ/TQ p95 | sess for 50% RQ |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    Mf = max(r["M"] for r in yr_rows)
    for r in yr_rows:
        if r["M"] != Mf:
            continue
        q = r["rq"]
        L.append(f"| {r['root']} | {r['M']} | {r['year']} | "
                 f"{r['n_sessions']} | {q['mean']:.2e} | {q['median']:.2e} | "
                 f"{q['p99']:.2e} | {q['max']:.2e} | {q['top1_share']:.3f} | "
                 f"{r['rq_tq_ratio_median']:.2f} | "
                 f"{r['rq_tq_ratio_p95']:.2f} | {r['rq_top50pct_sessions']} |")
    L.append("")
    L.append("log-RQ autocorrelations, lags 1-10 (pooled sample):")
    for r in acf_rows:
        a = ", ".join(f"{v:.2f}" for v in r["logrq_acf_lags1_10"])
        L.append(f"- {r['root']} M={r['M']}: {a}")
    return "\n".join(L) + "\n"


def main():
    led = b["ledger"]
    r1 = b["r1_counts"]
    L = []
    L.append("# Session 4 report, exclusion repairs and tail diagnostics\n")
    L.append("Run date 2026-08-18. Real data, no estimation. "
             "Pre-registration: `../PREREG.md`. Holdout untouched.\n")

    L.append("## Phase 0 module reuse\n")
    L.append(
        "Reused unmodified by import: S03 `analysis.build_panels`, "
        "`analysis.rv_from_grid`, and the S03 Phase-0 official-reader "
        "extract `raw_pre2024.npy`. Re-executed line-for-line (S03's "
        "`pipeline.main()` is a monolith whose rules 5/7 cannot be swapped "
        "without editing S03 artifacts, which is prohibited): rules 1-4 "
        "and rule 6. New here: R1, R2, R3, and the repaired rule-7 pass.\n")

    L.append("## Repair reconciliation\n")
    L.append("| quantity | ES | NQ |")
    L.append("|---|---|---|")
    L.append("| S03 final sessions (single geometry-blind count) | 1902 | 1902 |")
    L.append("| R3: phantom weekend session removed | -1 | -1 |")
    L.append(f"| R1 RTH: early-day + designated excluded | "
             f"{r1['excluded_rth_per_root']['ES']} | "
             f"{r1['excluded_rth_per_root']['NQ']} |")
    L.append(f"| R1 GLOBEX: excluded (designated + incomplete overnight) | "
             f"{r1['excluded_globex_per_root']['ES']} | "
             f"{r1['excluded_globex_per_root']['NQ']} |")
    L.append(f"| R1 GLOBEX: holiday sessions retained vs S03 | "
             f"+{r1['globex_retained_holiday_sessions']['ES']} | "
             f"+{r1['globex_retained_holiday_sessions']['NQ']} |")
    L.append("| R2: sessions excluded | 0 | 0 (flag-only; diagnostics run "
             "both ways) |")
    L.append(f"| roll +/-1 excluded (unchanged rule) | 96 | 96 |")
    L.append(f"| **final RTH** | **{led['ES_RTH']['final']}** | "
             f"**{led['NQ_RTH']['final']}** |")
    L.append(f"| **final GLOBEX** | **{led['ES_GLOBEX']['final']}** | "
             f"**{led['NQ_GLOBEX']['final']}** |")
    L.append("")
    L.append(
        f"R1 detail: 68 early-day sessions per root; "
        f"{r1['designated_per_root']['ES']} designated half-days "
        "(pre-registration's 16), excluded from both geometries: "
        + ", ".join(b["r1_designated_dates"]) + ". NQ retains 5 fewer "
        "holiday sessions than ES in GLOBEX because their overnight "
        "portions fall below the 90% completeness gate.\n")
    L.append(
        "R2 realised affected trade dates (16, each degraded UTC date maps "
        "to its own and the next trade date): "
        + ", ".join(b["r2_affected_trade_dates_realised"])
        + f"; {b['r2_affected_rows']:,} bars involved. Not excluded; every "
        "diagnostic below is reported with and without them.\n")

    L.append("## R3 root cause\n")
    t = b["r3_trace"][0]
    L.append(
        f"The weekend trade date is {t['trade_date']} (a Sunday). Source: "
        f"exactly {t['n_rows']} rows, one bar per root, raw symbols "
        f"{', '.join(t['raw_symbols'])} (instrument ids "
        f"{', '.join(str(i) for i in t['instrument_ids'])}), timestamp "
        f"{t['ts_utc_min']} = {t['ts_ny_min']}, volumes "
        f"{t['volumes']}. Arithmetic: {t['arithmetic'][0]}. "
        "Classification: not a DST artifact (August; no transition), not a "
        "boundary bug in the +6h rule (the arithmetic is correct), not a "
        "data defect (plausible volume on the correct front contracts): it "
        "is a CME session-boundary special - genuine trades printed in the "
        "17:59 minute before the nominal Sunday 18:00 reopen, which the "
        "+6h convention's no-trading-in-the-halt premise does not cover. "
        "Patch applied (minimal): weekend-dated bars reassign to the next "
        "Monday session; 2 rows moved, 0 weekend dates remain. "
        "Session-count delta: -1 phantom session per root; Friday "
        "halt-window prints (118 bars) correctly stay with Friday's ended "
        "session and were not touched.\n")

    L.append("## D-TAIL, five hypothesis measurements side by side\n")
    L.append("Reported for both geometries, with and without the R2 "
             "dates. No verdict is stated, per the stop conditions.\n")
    for tag in ["GLOBEX_withR2", "GLOBEX_noR2", "RTH_withR2", "RTH_noR2"]:
        L.append(dtail_block(tag))

    L.append("## D-RQ, quarticity stability\n")
    for geom in ["GLOBEX", "RTH"]:
        for tag in ["withR2", "noR2"]:
            L.append(drq_block(geom, tag))

    L.append("## Final counts and conditioning cell sizes\n")
    L.append("| root | geometry | final sessions | cells at q=0.80 | "
             "q=0.90 | q=0.95 |")
    L.append("|---|---|---|---|---|---|")
    for r in ["ES", "NQ"]:
        for geom in ["RTH", "GLOBEX"]:
            n = led[f"{r}_{geom}"]["final"]
            L.append(f"| {r} | {geom} | {n} | {int(n*0.20)} | {int(n*0.10)} "
                     f"| {int(n*0.05)} |")
    L.append("")
    L.append("Cell size = sessions remaining above the conditioning "
             "quantile in a daily-horizon design, (1-q) x final count.\n")

    with open(os.path.join(RES, "S04-report.md"), "w") as fh:
        fh.write("\n".join(L))

    # -------- runlog
    freeze = subprocess.run([VENV_PY, "-m", "pip", "freeze"],
                            capture_output=True, text=True).stdout.strip()
    R = []
    R.append("# Session 4 run log\n")
    R.append(f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} (UTC).\n")
    R.append("## Wall clock per phase\n")
    R.append("| phase | wall |")
    R.append("|---|---|")
    R.append("| Phase 0/1 setup + freeze | ~4 min |")
    R.append("| Phase 2 build, 3 passes (initial + R3-patch/classifier fix "
             "+ dtype fix; all logged in-session) | 3m37 + 6m49 + 7m56 wall "
             "(~40 s CPU each; the S02 grid occupies the cores) |")
    R.append(f"| Phase 3 diagnostics | {d['elapsed_s']:.0f} s |")
    R.append("| Phase 4 reports | ~2 min |")
    R.append("")
    R.append("Total ~35 min wall, inside the 60-minute budget. Bottleneck "
             "throughout: CPU contention with the still-running S02 "
             "simulation grid (6 workers), which multiplies wall time "
             "roughly 8-10x over CPU time for pandas-heavy passes.\n")
    R.append("## Parameters used\n")
    R.append(
        "- Early-day detector: last day-portion (ny_min < 1080) front bar "
        "before 15:00 NY.\n"
        "- Designated half-days: Black Friday (Nov, Fri, day 23-29), "
        "Jul 3, Dec 24.\n"
        "- Overnight completeness: >= 90% of 930 expected overnight "
        "minutes (18:00-09:29 NY).\n"
        "- R3 patch: weekend-dated bars -> next Monday (2 rows).\n"
        "- Extremes: |r| > 10 sd(year, root), within-session 1-minute log "
        "returns on actual bars.\n"
        "- H1 anchors: 08:30, 10:00, 14:00 NY, +/-5 minutes; top-1% date "
        "bucket by ceil(0.01 x dates).\n"
        "- H4: Hill on top 1% of |r| (k >= 50); t-null df = max(alpha, "
        "2.1), scale matched to sd.\n"
        "- H5: stale run = consecutive zero within-session returns "
        "immediately preceding the bar.\n"
        "- D-RQ: RQ = (M/3) sum r^4; TQ tripower with mu_{4/3}; truncation "
        "at c x sqrt(BV/M), c in {3, 5, 10} (set reported, none "
        "selected); panels are the S03 forward-filled grids; log-RQ ACF "
        "lags 1-10 pooled.\n"
        "- R2 dates (16) as listed in the report; diagnostics computed "
        "with and without.\n")
    R.append("## Package versions (pip freeze)\n")
    R.append("```text\n" + freeze + "\n```\n")
    with open(os.path.join(RES, "S04-runlog.md"), "w") as fh:
        fh.write("\n".join(R))

    # -------- DECISIONS append
    dec = f"""
## 2026-08-18, session 4 repairs

13. R1 split the early-close rule by geometry. RTH excludes all 68
    early-halting sessions per root (16 designated half-days plus 52
    holiday sessions); GLOBEX retains holiday sessions whose overnight is
    >= 90% complete, excluding only {r1['excluded_globex_per_root']['ES']} (ES)
    / {r1['excluded_globex_per_root']['NQ']} (NQ). Final counts: RTH
    {led['ES_RTH']['final']}/{led['NQ_RTH']['final']} (ES/NQ), GLOBEX
    {led['ES_GLOBEX']['final']}/{led['NQ_GLOBEX']['final']}. S03's single
    geometry-blind count was 1902/1902.
14. R2 degraded-condition dates are flagged, not excluded; 16 affected
    trade dates; all S04 diagnostics reported with and without them.
15. R3 root cause: the weekend trade date 2018-08-05 came from two genuine
    pre-open prints (ESU8/NQU8) in the Sunday 17:59 halt minute; the +6h
    convention dates them Sunday. Patch: weekend-dated bars reassign to the
    next Monday (2 rows; -1 phantom session per root). Friday halt-window
    prints stay with Friday's session. Two S04 implementation bugs found
    and fixed before any diagnostic ran, both logged: an over-broad first
    patch (pushed Friday prints to Saturday) and an object-dtype boolean
    inversion that collapsed the GLOBEX early-close rule to the RTH rule.
"""
    with open(os.path.join(ROOT, "DECISIONS.md"), "a") as fh:
        fh.write(dec)
    print("report, runlog, DECISIONS written")


if __name__ == "__main__":
    main()
