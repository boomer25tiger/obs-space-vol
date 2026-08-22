# Pre-registration, Session 4 exclusion repairs and tail diagnostics

Frozen before any diagnostic is run. Real data. No estimator is applied.

## Purpose
Two goals. Repair three exclusion defects in S03 that change the final session count.
Determine whether realized quarticity is usable as the reliability source, given S03
reported 1-minute return kurtosis of 867 to 3278 by year.

## Holdout
2024-01-01 onward is NOT loaded, processed, or inspected. Estimation sample
2016-01-01 to 2023-12-31.

## Repair R1, split the early-close rule
S03 excluded 68 sessions per root by halting-before-15:00 New York, against ~18
designated half-days. Full holidays with abbreviated day sessions retain complete
overnight periods.
Rule becomes geometry-dependent:
  RTH geometry: exclude any session whose day portion halts before 15:00 NY.
  GLOBEX geometry: exclude a session only if its overnight portion is also incomplete,
  defined as fewer than 90% of expected overnight minutes present.
Both counts reported. The 16 designated half-days S03 identified are excluded from
both geometries regardless.

## Repair R2, degraded condition dates
Four Databento-degraded dates fall in the estimation sample with RTH content:
2017-11-13, 2019-01-15, 2019-02-22, 2019-03-13, 2019-03-26, 2020-02-27, 2020-02-28,
2020-06-30, 2020-07-01, 2021-12-05, 2022-01-02 (the subset with 2016-2023 trade dates
after rule 4 is applied; report the realised list).
Treatment: NOT excluded by default. Every Phase 3 diagnostic is computed twice, with
and without them, and both reported. Exclusion is a later decision, not made here.

## Repair R3, weekend trade date
S03 reported one weekend trade date, which cannot exist under the CME convention of
New York time plus six hours taken as a date. Trace the source rows, report the raw
timestamps, the instrument ids, the computed trade date, and the arithmetic that
produced it. Report whether it is a boundary bug, a DST artifact, a CME special
session, or a data defect. Do not patch the rule until the cause is identified; if a
patch is required, apply it and report the session-count delta.

## Diagnostic D-TAIL, are the extremes jumps or artifacts
Population: 1-minute log returns, both roots, both geometries, estimation sample.
Extreme set: |r| > 10 * sd(year, root), per the S03 definition. S03 counted 2,746.

Pre-specified hypotheses, each with a stated discriminating measurement. All are
reported; none is selected.

H1 GENUINE JUMPS. Extremes cluster on a small number of dates coinciding with
   scheduled events.
   Measurement: share of extremes falling in the top 1% of dates by extreme count;
   share falling within 5 minutes of 08:30 or 10:00 or 14:00 New York; share on FOMC,
   CPI, and NFP dates if a date list can be constructed from the data alone (if not,
   report clock-time clustering only and state that event dates were not available).

H2 SESSION-BOUNDARY ARTIFACT. Extremes concentrate at the 17:00 New York halt, the
   18:00 reopen, or the first and last minutes of the RTH window.
   Measurement: extreme rate per minute-of-day, reported for all 1,380 minutes, with
   the halt and reopen minutes called out explicitly.

H3 ROLL ARTIFACT. Extremes concentrate near front-contract changes despite the
   roll +/-1 exclusion.
   Measurement: extreme rate by trading-day distance from each roll date, -10 to +10.

H4 UNIFORM FAT TAILS. Extremes spread across dates and clock times in proportion to
   activity.
   Measurement: Gini coefficient of extremes per date; comparison of the empirical
   extreme rate against a Student-t null fitted per year, tail index estimated by Hill.

H5 STALE-BAR ARTIFACT. Extremes follow runs of unchanged closes, so the return
   accumulates across inactive minutes.
   Measurement: distribution of the count of consecutive unchanged closes immediately
   preceding each extreme, against the unconditional distribution.

## Diagnostic D-RQ, is realized quarticity stable
Realized quarticity RQ = (M/3) * sum(r_i^4), computed per session at every S03
sampling frequency, both geometries, both roots.
Reported:
  - RQ distribution by year: mean, median, p95, p99, max, and the share of total
    annual RQ contributed by the single largest session.
  - The same for tripower quarticity and for quarticity computed on truncated returns
    at 3, 5, and 10 local standard deviations. Truncation levels are reported as a
    set, never selected.
  - Ratio of standard RQ to tripower quarticity per session, by year. Large and
    unstable ratios indicate the fourth moment is jump-driven.
  - Serial correlation of log RQ at lags 1 to 10. RQ that is essentially white noise
    around a level is not carrying usable information.
  - Concentration: the number of sessions accounting for 50% of annual total RQ.

## Prohibited
No reliability estimator is applied. No forecasting model is estimated. No proxy or
truncation level is selected on the basis of results. No holdout data is touched.
Any deviation logged in DECISIONS.md.
