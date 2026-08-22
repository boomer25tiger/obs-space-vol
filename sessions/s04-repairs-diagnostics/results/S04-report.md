# Session 4 report, exclusion repairs and tail diagnostics

Run date 2026-08-18. Real data, no estimation. Pre-registration: `../PREREG.md`. Holdout untouched.

## Phase 0 module reuse

Reused unmodified by import: S03 `analysis.build_panels`, `analysis.rv_from_grid`, and the S03 Phase-0 official-reader extract `raw_pre2024.npy`. Re-executed line-for-line (S03's `pipeline.main()` is a monolith whose rules 5/7 cannot be swapped without editing S03 artifacts, which is prohibited): rules 1-4 and rule 6. New here: R1, R2, R3, and the repaired rule-7 pass.

## Repair reconciliation

| quantity | ES | NQ |
|---|---|---|
| S03 final sessions (single geometry-blind count) | 1902 | 1902 |
| R3: phantom weekend session removed | -1 | -1 |
| R1 RTH: early-day + designated excluded | 68 | 68 |
| R1 GLOBEX: excluded (designated + incomplete overnight) | 16 | 21 |
| R1 GLOBEX: holiday sessions retained vs S03 | +52 | +47 |
| R2: sessions excluded | 0 | 0 (flag-only; diagnostics run both ways) |
| roll +/-1 excluded (unchanged rule) | 96 | 96 |
| **final RTH** | **1901** | **1901** |
| **final GLOBEX** | **1953** | **1948** |

R1 detail: 68 early-day sessions per root; 16 designated half-days (pre-registration's 16), excluded from both geometries: 2016-11-25, 2017-07-03, 2017-11-24, 2018-07-03, 2018-11-23, 2018-12-24, 2019-07-03, 2019-11-29, 2019-12-24, 2020-07-03, 2020-11-27, 2020-12-24, 2021-11-26, 2022-11-25, 2023-07-03, 2023-11-24. NQ retains 5 fewer holiday sessions than ES in GLOBEX because their overnight portions fall below the 90% completeness gate.

R2 realised affected trade dates (16, each degraded UTC date maps to its own and the next trade date): 2017-11-13, 2017-11-14, 2019-01-15, 2019-01-16, 2019-02-22, 2019-03-13, 2019-03-14, 2019-03-26, 2019-03-27, 2020-02-27, 2020-02-28, 2020-06-30, 2020-07-01, 2020-07-02, 2021-12-06, 2022-01-03; 24,305 bars involved. Not excluded; every diagnostic below is reported with and without them.

## R3 root cause

The weekend trade date is 2018-08-05 (a Sunday). Source: exactly 2 rows, one bar per root, raw symbols ESU8, NQU8 (instrument ids 47511, 57287), timestamp 2018-08-05 21:59:00+00:00 = 2018-08-05 17:59:00-04:00, volumes [302, 73]. Arithmetic: 2018-08-05 17:59 EDT NY + 6h = 2018-08-05 23:59 -> date 2018-08-05. Classification: not a DST artifact (August; no transition), not a boundary bug in the +6h rule (the arithmetic is correct), not a data defect (plausible volume on the correct front contracts): it is a CME session-boundary special - genuine trades printed in the 17:59 minute before the nominal Sunday 18:00 reopen, which the +6h convention's no-trading-in-the-halt premise does not cover. Patch applied (minimal): weekend-dated bars reassign to the next Monday session; 2 rows moved, 0 weekend dates remain. Session-count delta: -1 phantom session per root; Friday halt-window prints (118 bars) correctly stay with Friday's ended session and were not touched.

## D-TAIL, five hypothesis measurements side by side

Reported for both geometries, with and without the R2 dates. No verdict is stated, per the stop conditions.

**GLOBEX_withR2** (1,623 extremes / 5,286,379 returns, base rate 3.07e-04)

- H1: share in top-1% dates 0.350; share within 5 min of 08:30/10:00/14:00 NY 0.186. FOMC/CPI/NFP dates cannot be constructed from the price data alone; clock-time clustering reported instead.
- H2 called-out minutes (rate, xbase): 1700_halt: 0.00e+00 (0.0x); 1800_reopen: 0.00e+00 (0.0x); 1801: 2.31e-03 (7.5x); 1805: 0.00e+00 (0.0x); rth_first_0930: 7.96e-03 (25.9x); rth_0931: 5.91e-03 (19.2x); rth_last_1559: 6.31e-03 (20.6x); 1600: 2.37e-03 (7.7x). Full 1,440-minute table: `s04_h2_minute_rates_GLOBEX_withR2.csv`.
- H3 ES rate by distance from roll (d: rate/n_sess): -3: 1.87e-04/32; -2: 2.06e-04/32; -1: 7.56e-04/32; 0: 7.62e-04/32; 1: 8.49e-04/32; 2: 3.43e-04/32; 3: 1.23e-03/32 (full -10..+10 in JSON)
- H3 NQ rate by distance from roll (d: rate/n_sess): -3: 3.01e-04/32; -2: 2.54e-04/32; -1: 7.16e-04/32; 0: 7.69e-04/32; 1: 7.39e-04/32; 2: 2.76e-04/32; 3: 1.05e-03/32 (full -10..+10 in JSON)
- H4: Gini of extremes per date ES 0.932, NQ 0.907. Hill alpha and Student-t expected vs observed extremes by (root, year):
    - ES_2016: alpha 3.38, t-null expects 94.2, observed 88
    - ES_2017: alpha 3.67, t-null expects 67.9, observed 42
    - ES_2018: alpha 3.49, t-null expects 82.8, observed 101
    - ES_2019: alpha 3.14, t-null expects 119.9, observed 130
    - ES_2020: alpha 2.98, t-null expects 141.1, observed 187
    - ES_2021: alpha 3.46, t-null expects 87.6, observed 73
    - ES_2022: alpha 3.57, t-null expects 78.0, observed 69
    - ES_2023: alpha 3.46, t-null expects 87.4, observed 98
    - NQ_2016: alpha 3.50, t-null expects 79.2, observed 88
    - NQ_2017: alpha 3.48, t-null expects 82.2, observed 71
    - NQ_2018: alpha 3.54, t-null expects 78.4, observed 91
    - NQ_2019: alpha 3.18, t-null expects 115.7, observed 138
    - NQ_2020: alpha 3.07, t-null expects 129.2, observed 159
    - NQ_2021: alpha 3.41, t-null expects 92.3, observed 95
    - NQ_2022: alpha 3.47, t-null expects 86.6, observed 86
    - NQ_2023: alpha 3.39, t-null expects 93.7, observed 107
- H5: preceding stale-run length, extremes vs unconditional: mean 0.428 vs 0.268; share with >=1 stale minute before: 0.0351 vs 0.1651; share >=5: 0.0049 vs 0.0044.

**GLOBEX_noR2** (1,610 extremes / 5,242,970 returns, base rate 3.07e-04)

- H1: share in top-1% dates 0.352; share within 5 min of 08:30/10:00/14:00 NY 0.188. FOMC/CPI/NFP dates cannot be constructed from the price data alone; clock-time clustering reported instead.
- H2 called-out minutes (rate, xbase): 1700_halt: 0.00e+00 (0.0x); 1800_reopen: 0.00e+00 (0.0x); 1801: 2.33e-03 (7.6x); 1805: 0.00e+00 (0.0x); rth_first_0930: 7.77e-03 (25.3x); rth_0931: 5.44e-03 (17.7x); rth_last_1559: 5.84e-03 (19.0x); 1600: 2.39e-03 (7.8x). Full 1,440-minute table: `s04_h2_minute_rates_GLOBEX_noR2.csv`.
- H3 ES rate by distance from roll (d: rate/n_sess): -3: 2.10e-04/32; -2: 2.06e-04/32; -1: 7.56e-04/32; 0: 7.62e-04/32; 1: 8.49e-04/32; 2: 3.43e-04/32; 3: 1.23e-03/32 (full -10..+10 in JSON)
- H3 NQ rate by distance from roll (d: rate/n_sess): -3: 3.47e-04/32; -2: 2.54e-04/32; -1: 7.16e-04/32; 0: 7.69e-04/32; 1: 7.39e-04/32; 2: 2.99e-04/32; 3: 1.12e-03/32 (full -10..+10 in JSON)
- H4: Gini of extremes per date ES 0.932, NQ 0.908. Hill alpha and Student-t expected vs observed extremes by (root, year):
    - ES_2016: alpha 3.38, t-null expects 94.2, observed 88
    - ES_2017: alpha 3.66, t-null expects 68.3, observed 42
    - ES_2018: alpha 3.49, t-null expects 82.8, observed 101
    - ES_2019: alpha 3.12, t-null expects 118.8, observed 128
    - ES_2020: alpha 2.95, t-null expects 142.1, observed 182
    - ES_2021: alpha 3.47, t-null expects 86.5, observed 72
    - ES_2022: alpha 3.57, t-null expects 77.3, observed 69
    - ES_2023: alpha 3.46, t-null expects 87.4, observed 98
    - NQ_2016: alpha 3.50, t-null expects 79.2, observed 88
    - NQ_2017: alpha 3.48, t-null expects 82.0, observed 71
    - NQ_2018: alpha 3.54, t-null expects 78.4, observed 91
    - NQ_2019: alpha 3.17, t-null expects 113.2, observed 137
    - NQ_2020: alpha 3.04, t-null expects 131.1, observed 157
    - NQ_2021: alpha 3.42, t-null expects 91.0, observed 95
    - NQ_2022: alpha 3.47, t-null expects 86.5, observed 84
    - NQ_2023: alpha 3.39, t-null expects 93.7, observed 107
- H5: preceding stale-run length, extremes vs unconditional: mean 0.432 vs 0.269; share with >=1 stale minute before: 0.0354 vs 0.1652; share >=5: 0.0050 vs 0.0044.

**RTH_withR2** (1,572 extremes / 5,175,748 returns, base rate 3.04e-04)

- H1: share in top-1% dates 0.352; share within 5 min of 08:30/10:00/14:00 NY 0.188. FOMC/CPI/NFP dates cannot be constructed from the price data alone; clock-time clustering reported instead.
- H2 called-out minutes (rate, xbase): 1700_halt: 0.00e+00 (0.0x); 1800_reopen: 0.00e+00 (0.0x); 1801: 1.84e-03 (6.1x); 1805: 0.00e+00 (0.0x); rth_first_0930: 7.89e-03 (26.0x); rth_0931: 6.05e-03 (19.9x); rth_last_1559: 6.05e-03 (19.9x); 1600: 2.37e-03 (7.8x). Full 1,440-minute table: `s04_h2_minute_rates_RTH_withR2.csv`.
- H3 ES rate by distance from roll (d: rate/n_sess): -3: 1.83e-04/32; -2: 2.06e-04/32; -1: 7.56e-04/32; 0: 7.39e-04/32; 1: 8.49e-04/32; 2: 3.20e-04/32; 3: 1.19e-03/32 (full -10..+10 in JSON)
- H3 NQ rate by distance from roll (d: rate/n_sess): -3: 2.76e-04/32; -2: 2.08e-04/32; -1: 7.16e-04/32; 0: 7.69e-04/32; 1: 7.39e-04/32; 2: 2.76e-04/32; 3: 1.01e-03/32 (full -10..+10 in JSON)
- H4: Gini of extremes per date ES 0.931, NQ 0.906. Hill alpha and Student-t expected vs observed extremes by (root, year):
    - ES_2016: alpha 3.38, t-null expects 92.1, observed 86
    - ES_2017: alpha 3.63, t-null expects 69.4, observed 41
    - ES_2018: alpha 3.49, t-null expects 81.0, observed 97
    - ES_2019: alpha 3.14, t-null expects 117.5, observed 125
    - ES_2020: alpha 3.01, t-null expects 135.2, observed 183
    - ES_2021: alpha 3.45, t-null expects 86.4, observed 69
    - ES_2022: alpha 3.59, t-null expects 74.9, observed 66
    - ES_2023: alpha 3.46, t-null expects 84.8, observed 95
    - NQ_2016: alpha 3.49, t-null expects 79.3, observed 88
    - NQ_2017: alpha 3.50, t-null expects 79.1, observed 69
    - NQ_2018: alpha 3.55, t-null expects 76.3, observed 86
    - NQ_2019: alpha 3.19, t-null expects 112.3, observed 136
    - NQ_2020: alpha 3.08, t-null expects 126.3, observed 155
    - NQ_2021: alpha 3.42, t-null expects 89.7, observed 90
    - NQ_2022: alpha 3.49, t-null expects 83.2, observed 83
    - NQ_2023: alpha 3.40, t-null expects 91.0, observed 103
- H5: preceding stale-run length, extremes vs unconditional: mean 0.441 vs 0.266; share with >=1 stale minute before: 0.0356 vs 0.1638; share >=5: 0.0051 vs 0.0043.

**RTH_noR2** (1,565 extremes / 5,132,339 returns, base rate 3.05e-04)

- H1: share in top-1% dates 0.352; share within 5 min of 08:30/10:00/14:00 NY 0.188. FOMC/CPI/NFP dates cannot be constructed from the price data alone; clock-time clustering reported instead.
- H2 called-out minutes (rate, xbase): 1700_halt: 0.00e+00 (0.0x); 1800_reopen: 0.00e+00 (0.0x); 1801: 1.86e-03 (6.1x); 1805: 0.00e+00 (0.0x); rth_first_0930: 7.69e-03 (25.2x); rth_0931: 5.57e-03 (18.3x); rth_last_1559: 5.57e-03 (18.3x); 1600: 2.39e-03 (7.8x). Full 1,440-minute table: `s04_h2_minute_rates_RTH_noR2.csv`.
- H3 ES rate by distance from roll (d: rate/n_sess): -3: 2.06e-04/32; -2: 2.06e-04/32; -1: 7.56e-04/32; 0: 7.39e-04/32; 1: 8.49e-04/32; 2: 3.43e-04/32; 3: 1.19e-03/32 (full -10..+10 in JSON)
- H3 NQ rate by distance from roll (d: rate/n_sess): -3: 3.45e-04/32; -2: 2.31e-04/32; -1: 7.16e-04/32; 0: 7.69e-04/32; 1: 7.39e-04/32; 2: 2.76e-04/32; 3: 1.01e-03/32 (full -10..+10 in JSON)
- H4: Gini of extremes per date ES 0.932, NQ 0.906. Hill alpha and Student-t expected vs observed extremes by (root, year):
    - ES_2016: alpha 3.38, t-null expects 92.1, observed 86
    - ES_2017: alpha 3.62, t-null expects 69.8, observed 41
    - ES_2018: alpha 3.49, t-null expects 81.0, observed 97
    - ES_2019: alpha 3.13, t-null expects 116.0, observed 124
    - ES_2020: alpha 2.96, t-null expects 138.6, observed 182
    - ES_2021: alpha 3.45, t-null expects 86.0, observed 68
    - ES_2022: alpha 3.58, t-null expects 75.0, observed 66
    - ES_2023: alpha 3.46, t-null expects 84.8, observed 95
    - NQ_2016: alpha 3.49, t-null expects 79.3, observed 88
    - NQ_2017: alpha 3.49, t-null expects 79.7, observed 69
    - NQ_2018: alpha 3.55, t-null expects 76.3, observed 86
    - NQ_2019: alpha 3.17, t-null expects 110.6, observed 134
    - NQ_2020: alpha 3.03, t-null expects 129.1, observed 152
    - NQ_2021: alpha 3.42, t-null expects 89.1, observed 91
    - NQ_2022: alpha 3.49, t-null expects 82.8, observed 83
    - NQ_2023: alpha 3.40, t-null expects 91.0, observed 103
- H5: preceding stale-run length, extremes vs unconditional: mean 0.443 vs 0.266; share with >=1 stale minute before: 0.0358 vs 0.1640; share >=5: 0.0051 vs 0.0043.

## D-RQ, quarticity stability

**GLOBEX withR2** - per-year RQ statistics at the finest M (full grid for every M, both quarticity variants and all truncation levels, in `s04_diagnostics.json`):

| root | M | year | n | RQ mean | RQ median | RQ p99 | RQ max | top-1 share | RQ/TQ med | RQ/TQ p95 | sess for 50% RQ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ES | 1380 | 2016 | 245 | 7.27e-08 | 7.46e-09 | 7.88e-07 | 4.52e-06 | 0.254 | 6.33 | 14.92 | 4 |
| ES | 1380 | 2017 | 243 | 6.09e-09 | 1.31e-09 | 1.70e-08 | 9.20e-07 | 0.622 | 6.35 | 13.43 | 1 |
| ES | 1380 | 2018 | 243 | 1.95e-07 | 1.10e-08 | 6.22e-06 | 7.19e-06 | 0.152 | 6.48 | 12.95 | 4 |
| ES | 1380 | 2019 | 243 | 6.54e-08 | 7.94e-09 | 1.10e-06 | 1.92e-06 | 0.121 | 6.94 | 33.55 | 9 |
| ES | 1380 | 2020 | 244 | 2.95e-06 | 4.64e-08 | 9.70e-05 | 1.30e-04 | 0.181 | 6.65 | 14.09 | 4 |
| ES | 1380 | 2021 | 246 | 3.64e-08 | 6.18e-09 | 5.30e-07 | 8.69e-07 | 0.097 | 5.92 | 11.43 | 12 |
| ES | 1380 | 2022 | 245 | 1.66e-06 | 9.45e-08 | 3.70e-05 | 1.62e-04 | 0.399 | 6.10 | 19.07 | 2 |
| ES | 1380 | 2023 | 244 | 6.33e-08 | 1.08e-08 | 1.16e-06 | 2.08e-06 | 0.135 | 6.25 | 17.57 | 7 |
| NQ | 1380 | 2016 | 241 | 1.25e-07 | 1.62e-08 | 1.16e-06 | 5.97e-06 | 0.199 | 6.69 | 15.98 | 7 |
| NQ | 1380 | 2017 | 242 | 1.11e-08 | 3.98e-09 | 1.10e-07 | 3.54e-07 | 0.132 | 6.68 | 15.03 | 20 |
| NQ | 1380 | 2018 | 243 | 4.04e-07 | 4.29e-08 | 8.06e-06 | 1.33e-05 | 0.135 | 6.05 | 15.28 | 5 |
| NQ | 1380 | 2019 | 243 | 1.44e-07 | 2.38e-08 | 2.10e-06 | 3.98e-06 | 0.114 | 7.24 | 33.79 | 10 |
| NQ | 1380 | 2020 | 244 | 2.83e-06 | 1.08e-07 | 9.00e-05 | 1.10e-04 | 0.160 | 6.56 | 15.82 | 4 |
| NQ | 1380 | 2021 | 246 | 1.44e-07 | 2.55e-08 | 1.61e-06 | 6.03e-06 | 0.170 | 6.35 | 15.34 | 11 |
| NQ | 1380 | 2022 | 245 | 6.15e-06 | 3.08e-07 | 1.44e-04 | 7.24e-04 | 0.481 | 6.33 | 25.01 | 2 |
| NQ | 1380 | 2023 | 244 | 2.42e-07 | 3.83e-08 | 4.97e-06 | 8.96e-06 | 0.152 | 6.31 | 30.82 | 6 |

log-RQ autocorrelations, lags 1-10 (pooled sample):
- ES M=23: 0.68, 0.63, 0.60, 0.57, 0.56, 0.54, 0.52, 0.51, 0.49, 0.47
- ES M=46: 0.71, 0.65, 0.63, 0.60, 0.58, 0.56, 0.54, 0.53, 0.50, 0.49
- ES M=138: 0.74, 0.69, 0.66, 0.63, 0.61, 0.59, 0.55, 0.55, 0.53, 0.50
- ES M=345: 0.74, 0.69, 0.65, 0.64, 0.63, 0.60, 0.57, 0.55, 0.54, 0.52
- ES M=1380: 0.73, 0.69, 0.65, 0.63, 0.62, 0.59, 0.56, 0.53, 0.53, 0.51
- NQ M=23: 0.64, 0.59, 0.54, 0.54, 0.50, 0.49, 0.47, 0.46, 0.44, 0.43
- NQ M=46: 0.66, 0.61, 0.58, 0.56, 0.53, 0.52, 0.49, 0.48, 0.45, 0.45
- NQ M=138: 0.69, 0.65, 0.61, 0.59, 0.57, 0.55, 0.50, 0.50, 0.48, 0.47
- NQ M=345: 0.70, 0.65, 0.61, 0.60, 0.58, 0.56, 0.52, 0.51, 0.50, 0.48
- NQ M=1380: 0.70, 0.65, 0.62, 0.60, 0.58, 0.56, 0.52, 0.50, 0.50, 0.48

**GLOBEX noR2** - per-year RQ statistics at the finest M (full grid for every M, both quarticity variants and all truncation levels, in `s04_diagnostics.json`):

| root | M | year | n | RQ mean | RQ median | RQ p99 | RQ max | top-1 share | RQ/TQ med | RQ/TQ p95 | sess for 50% RQ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ES | 1380 | 2016 | 245 | 7.27e-08 | 7.46e-09 | 7.88e-07 | 4.52e-06 | 0.254 | 6.33 | 14.92 | 4 |
| ES | 1380 | 2017 | 241 | 6.13e-09 | 1.31e-09 | 1.71e-08 | 9.20e-07 | 0.623 | 6.35 | 13.46 | 1 |
| ES | 1380 | 2018 | 243 | 1.95e-07 | 1.10e-08 | 6.22e-06 | 7.19e-06 | 0.152 | 6.48 | 12.95 | 4 |
| ES | 1380 | 2019 | 236 | 6.69e-08 | 7.95e-09 | 1.11e-06 | 1.92e-06 | 0.121 | 6.94 | 34.06 | 8 |
| ES | 1380 | 2020 | 239 | 2.95e-06 | 4.19e-08 | 9.74e-05 | 1.30e-04 | 0.184 | 6.63 | 13.88 | 4 |
| ES | 1380 | 2021 | 245 | 3.63e-08 | 6.14e-09 | 5.30e-07 | 8.69e-07 | 0.098 | 5.91 | 11.48 | 12 |
| ES | 1380 | 2022 | 244 | 1.66e-06 | 9.46e-08 | 3.73e-05 | 1.62e-04 | 0.399 | 6.11 | 19.11 | 2 |
| ES | 1380 | 2023 | 244 | 6.33e-08 | 1.08e-08 | 1.16e-06 | 2.08e-06 | 0.135 | 6.25 | 17.57 | 7 |
| NQ | 1380 | 2016 | 241 | 1.25e-07 | 1.62e-08 | 1.16e-06 | 5.97e-06 | 0.199 | 6.69 | 15.98 | 7 |
| NQ | 1380 | 2017 | 240 | 1.11e-08 | 3.98e-09 | 1.12e-07 | 3.54e-07 | 0.132 | 6.68 | 15.23 | 19 |
| NQ | 1380 | 2018 | 243 | 4.04e-07 | 4.29e-08 | 8.06e-06 | 1.33e-05 | 0.135 | 6.05 | 15.28 | 5 |
| NQ | 1380 | 2019 | 236 | 1.47e-07 | 2.40e-08 | 2.10e-06 | 3.98e-06 | 0.115 | 7.21 | 33.94 | 10 |
| NQ | 1380 | 2020 | 239 | 2.82e-06 | 1.09e-07 | 9.06e-05 | 1.10e-04 | 0.164 | 6.59 | 16.10 | 4 |
| NQ | 1380 | 2021 | 245 | 1.44e-07 | 2.54e-08 | 1.61e-06 | 6.03e-06 | 0.171 | 6.32 | 15.38 | 10 |
| NQ | 1380 | 2022 | 244 | 6.17e-06 | 3.09e-07 | 1.45e-04 | 7.24e-04 | 0.481 | 6.35 | 25.18 | 2 |
| NQ | 1380 | 2023 | 244 | 2.42e-07 | 3.83e-08 | 4.97e-06 | 8.96e-06 | 0.152 | 6.31 | 30.82 | 6 |

log-RQ autocorrelations, lags 1-10 (pooled sample):
- ES M=23: 0.68, 0.63, 0.60, 0.57, 0.55, 0.54, 0.52, 0.51, 0.49, 0.47
- ES M=46: 0.71, 0.65, 0.62, 0.60, 0.58, 0.57, 0.54, 0.53, 0.50, 0.50
- ES M=138: 0.74, 0.68, 0.65, 0.63, 0.60, 0.59, 0.55, 0.55, 0.52, 0.50
- ES M=345: 0.73, 0.69, 0.65, 0.63, 0.62, 0.60, 0.56, 0.54, 0.54, 0.52
- ES M=1380: 0.73, 0.68, 0.64, 0.63, 0.61, 0.59, 0.55, 0.52, 0.52, 0.50
- NQ M=23: 0.64, 0.59, 0.54, 0.54, 0.50, 0.49, 0.47, 0.46, 0.44, 0.43
- NQ M=46: 0.66, 0.61, 0.57, 0.56, 0.53, 0.52, 0.49, 0.47, 0.45, 0.45
- NQ M=138: 0.69, 0.64, 0.61, 0.59, 0.56, 0.55, 0.50, 0.50, 0.48, 0.47
- NQ M=345: 0.70, 0.65, 0.61, 0.60, 0.58, 0.56, 0.52, 0.51, 0.50, 0.48
- NQ M=1380: 0.70, 0.65, 0.61, 0.60, 0.58, 0.56, 0.51, 0.49, 0.49, 0.48

**RTH withR2** - per-year RQ statistics at the finest M (full grid for every M, both quarticity variants and all truncation levels, in `s04_diagnostics.json`):

| root | M | year | n | RQ mean | RQ median | RQ p99 | RQ max | top-1 share | RQ/TQ med | RQ/TQ p95 | sess for 50% RQ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ES | 390 | 2016 | 239 | 7.45e-09 | 1.25e-09 | 1.14e-07 | 1.85e-07 | 0.104 | 6.24 | 11.85 | 11 |
| ES | 390 | 2017 | 237 | 1.60e-09 | 2.53e-10 | 3.51e-09 | 2.60e-07 | 0.685 | 6.33 | 13.23 | 1 |
| ES | 390 | 2018 | 236 | 3.56e-08 | 2.38e-09 | 5.50e-07 | 2.03e-06 | 0.242 | 6.34 | 11.47 | 3 |
| ES | 390 | 2019 | 237 | 8.89e-09 | 1.26e-09 | 1.32e-07 | 3.60e-07 | 0.171 | 6.24 | 20.05 | 8 |
| ES | 390 | 2020 | 239 | 4.55e-07 | 7.37e-09 | 1.17e-05 | 3.14e-05 | 0.289 | 6.38 | 14.56 | 3 |
| ES | 390 | 2021 | 239 | 7.62e-09 | 1.29e-09 | 1.16e-07 | 1.52e-07 | 0.084 | 5.90 | 11.31 | 12 |
| ES | 390 | 2022 | 238 | 7.57e-08 | 1.99e-08 | 1.33e-06 | 2.90e-06 | 0.161 | 5.92 | 11.71 | 7 |
| ES | 390 | 2023 | 236 | 6.92e-09 | 2.28e-09 | 8.18e-08 | 1.34e-07 | 0.082 | 6.02 | 12.57 | 15 |
| NQ | 390 | 2016 | 239 | 1.57e-08 | 3.27e-09 | 2.19e-07 | 2.41e-07 | 0.064 | 6.35 | 12.29 | 10 |
| NQ | 390 | 2017 | 237 | 2.45e-09 | 8.71e-10 | 2.10e-08 | 9.28e-08 | 0.160 | 6.54 | 14.31 | 17 |
| NQ | 390 | 2018 | 236 | 7.20e-08 | 9.04e-09 | 1.25e-06 | 3.40e-06 | 0.200 | 5.84 | 13.44 | 6 |
| NQ | 390 | 2019 | 237 | 1.87e-08 | 3.76e-09 | 2.82e-07 | 5.97e-07 | 0.135 | 6.20 | 20.57 | 9 |
| NQ | 390 | 2020 | 239 | 4.86e-07 | 2.15e-08 | 1.20e-05 | 3.01e-05 | 0.259 | 6.23 | 14.93 | 3 |
| NQ | 390 | 2021 | 239 | 2.71e-08 | 5.78e-09 | 3.04e-07 | 5.33e-07 | 0.082 | 6.14 | 11.91 | 13 |
| NQ | 390 | 2022 | 238 | 2.24e-07 | 6.16e-08 | 3.20e-06 | 9.20e-06 | 0.172 | 5.95 | 12.55 | 9 |
| NQ | 390 | 2023 | 236 | 1.96e-08 | 7.90e-09 | 2.21e-07 | 2.87e-07 | 0.062 | 5.70 | 11.12 | 18 |

log-RQ autocorrelations, lags 1-10 (pooled sample):
- ES M=13: 0.69, 0.65, 0.61, 0.58, 0.57, 0.54, 0.53, 0.52, 0.49, 0.49
- ES M=26: 0.73, 0.69, 0.64, 0.62, 0.60, 0.58, 0.57, 0.56, 0.53, 0.51
- ES M=78: 0.76, 0.72, 0.68, 0.65, 0.64, 0.62, 0.59, 0.58, 0.57, 0.54
- ES M=195: 0.78, 0.73, 0.69, 0.67, 0.66, 0.63, 0.60, 0.59, 0.57, 0.56
- ES M=390: 0.78, 0.73, 0.69, 0.67, 0.66, 0.63, 0.60, 0.59, 0.57, 0.55
- NQ M=13: 0.64, 0.62, 0.57, 0.56, 0.54, 0.51, 0.52, 0.49, 0.46, 0.46
- NQ M=26: 0.69, 0.65, 0.61, 0.59, 0.57, 0.55, 0.53, 0.53, 0.50, 0.49
- NQ M=78: 0.73, 0.69, 0.66, 0.64, 0.62, 0.60, 0.57, 0.56, 0.55, 0.52
- NQ M=195: 0.77, 0.72, 0.69, 0.67, 0.65, 0.62, 0.59, 0.59, 0.57, 0.56
- NQ M=390: 0.78, 0.73, 0.69, 0.68, 0.66, 0.63, 0.60, 0.59, 0.57, 0.56

**RTH noR2** - per-year RQ statistics at the finest M (full grid for every M, both quarticity variants and all truncation levels, in `s04_diagnostics.json`):

| root | M | year | n | RQ mean | RQ median | RQ p99 | RQ max | top-1 share | RQ/TQ med | RQ/TQ p95 | sess for 50% RQ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ES | 390 | 2016 | 239 | 7.45e-09 | 1.25e-09 | 1.14e-07 | 1.85e-07 | 0.104 | 6.24 | 11.85 | 11 |
| ES | 390 | 2017 | 235 | 1.61e-09 | 2.53e-10 | 3.51e-09 | 2.60e-07 | 0.686 | 6.33 | 13.27 | 1 |
| ES | 390 | 2018 | 236 | 3.56e-08 | 2.38e-09 | 5.50e-07 | 2.03e-06 | 0.242 | 6.34 | 11.47 | 3 |
| ES | 390 | 2019 | 230 | 9.08e-09 | 1.23e-09 | 1.34e-07 | 3.60e-07 | 0.172 | 6.22 | 20.95 | 8 |
| ES | 390 | 2020 | 234 | 4.50e-07 | 7.10e-09 | 1.19e-05 | 3.14e-05 | 0.298 | 6.39 | 14.69 | 3 |
| ES | 390 | 2021 | 238 | 7.59e-09 | 1.28e-09 | 1.16e-07 | 1.52e-07 | 0.084 | 5.90 | 11.32 | 12 |
| ES | 390 | 2022 | 237 | 7.60e-08 | 2.00e-08 | 1.33e-06 | 2.90e-06 | 0.161 | 5.93 | 11.71 | 7 |
| ES | 390 | 2023 | 236 | 6.92e-09 | 2.28e-09 | 8.18e-08 | 1.34e-07 | 0.082 | 6.02 | 12.57 | 15 |
| NQ | 390 | 2016 | 239 | 1.57e-08 | 3.27e-09 | 2.19e-07 | 2.41e-07 | 0.064 | 6.35 | 12.29 | 10 |
| NQ | 390 | 2017 | 235 | 2.46e-09 | 8.71e-10 | 2.10e-08 | 9.28e-08 | 0.161 | 6.54 | 14.32 | 16 |
| NQ | 390 | 2018 | 236 | 7.20e-08 | 9.04e-09 | 1.25e-06 | 3.40e-06 | 0.200 | 5.84 | 13.44 | 6 |
| NQ | 390 | 2019 | 230 | 1.91e-08 | 3.76e-09 | 2.83e-07 | 5.97e-07 | 0.136 | 6.20 | 21.22 | 9 |
| NQ | 390 | 2020 | 234 | 4.83e-07 | 2.15e-08 | 1.23e-05 | 3.01e-05 | 0.266 | 6.26 | 15.27 | 3 |
| NQ | 390 | 2021 | 238 | 2.68e-08 | 5.62e-09 | 3.04e-07 | 5.33e-07 | 0.083 | 6.13 | 11.93 | 13 |
| NQ | 390 | 2022 | 237 | 2.25e-07 | 6.16e-08 | 3.21e-06 | 9.20e-06 | 0.172 | 5.95 | 12.56 | 9 |
| NQ | 390 | 2023 | 236 | 1.96e-08 | 7.90e-09 | 2.21e-07 | 2.87e-07 | 0.062 | 5.70 | 11.12 | 18 |

log-RQ autocorrelations, lags 1-10 (pooled sample):
- ES M=13: 0.69, 0.65, 0.61, 0.58, 0.56, 0.55, 0.54, 0.52, 0.49, 0.49
- ES M=26: 0.73, 0.69, 0.64, 0.62, 0.60, 0.59, 0.58, 0.56, 0.53, 0.51
- ES M=78: 0.76, 0.72, 0.67, 0.65, 0.64, 0.62, 0.59, 0.58, 0.57, 0.54
- ES M=195: 0.78, 0.73, 0.69, 0.67, 0.65, 0.63, 0.60, 0.58, 0.57, 0.56
- ES M=390: 0.78, 0.73, 0.68, 0.67, 0.65, 0.63, 0.60, 0.58, 0.57, 0.55
- NQ M=13: 0.63, 0.61, 0.57, 0.56, 0.54, 0.52, 0.52, 0.49, 0.46, 0.46
- NQ M=26: 0.69, 0.65, 0.61, 0.59, 0.57, 0.55, 0.54, 0.53, 0.50, 0.49
- NQ M=78: 0.73, 0.69, 0.66, 0.64, 0.62, 0.60, 0.57, 0.56, 0.55, 0.52
- NQ M=195: 0.77, 0.72, 0.69, 0.67, 0.65, 0.62, 0.60, 0.59, 0.57, 0.56
- NQ M=390: 0.78, 0.73, 0.69, 0.67, 0.65, 0.63, 0.60, 0.59, 0.57, 0.56

## Final counts and conditioning cell sizes

| root | geometry | final sessions | cells at q=0.80 | q=0.90 | q=0.95 |
|---|---|---|---|---|---|
| ES | RTH | 1901 | 380 | 190 | 95 |
| ES | GLOBEX | 1953 | 390 | 195 | 97 |
| NQ | RTH | 1901 | 380 | 190 | 95 |
| NQ | GLOBEX | 1948 | 389 | 194 | 97 |

Cell size = sessions remaining above the conditioning quantile in a daily-horizon design, (1-q) x final count.
