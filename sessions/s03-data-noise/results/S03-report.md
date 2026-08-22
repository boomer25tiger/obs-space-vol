# Session 3 report, data engineering and noise characterisation

Run date 2026-08-18. First session on real data. Pre-registration: `../PREREG.md`. Holdout respected: no row dated 2024-01-01 or later was loaded past the Phase 0 timestamp scan. NOTE: SCOPE.md is absent from the working tree (DECISIONS item 11); validation targets are the SCOPE figures quoted in the session instructions.

## Phase 0 inventory

Job `GLBX-20260817-KAB3XQ8E4C`, four files:

| file | size (bytes) | format | sha256 (manifest, verified) |
|---|---|---|---|
| metadata.json | 710 | JSON | 718dca4b... match |
| manifest.json | 1,475 | JSON | (no self-hash) |
| condition.json | 612,811 | JSON | aafd33b7... match |
| glbx-mdp3-20100606-20260815.ohlcv-1m.dbn.zst | 190,944,913 | DBN v3, zstd | 08cae0bf... match |

Metadata: dataset `GLBX.MDP3`, schema `ohlcv-1m` (minute aggregate OHLCV, as required), encoding `dbn` + `zstd`, `stype_in=parent`, `stype_out=instrument_id`, symbols `NQ.FUT`, `ES.FUT` (both roots requested), start 1275782400000000000 (2010-06-06T00:00Z), end 1786838400000000000 (2026-08-15T00:00Z), limit none, pretty_px/pretty_ts/map_symbols/split_symbols all false.

There is no separate symbology.json in the delivery (manifest lists exactly the four files above); the symbology ships embedded in the DBN metadata header, which is the same job symbology and is date-aware. Structure: 400 raw symbols, 713 (symbol, start_date, end_date, instrument_id) intervals, 550 of them calendar spreads (hyphenated), 366 intervals with prefix ES and 347 with prefix NQ. 305 raw symbols map to more than one instrument id across the file span - the id-recycling problem the date-aware rule exists for (e.g. ESH3 -> id 23970 for 2011-12-04 to 2013-04-08 and id 206299 for 2021-06-03 to 2023-04-04).

Condition file: 5,107 dated entries 2010-06-06 to 2026-08-15; 5,076 `available`, 31 `degraded`, of which 20 fall before 2024-01-01: 2014-06-11/12/13/15, 2014-09-22/23/24/25, 2017-11-13, 2018-10-21, 2019-01-15, 2019-02-22, 2019-03-13, 2019-03-26, 2020-02-27/28, 2020-06-30, 2020-07-01, 2021-12-05, 2022-01-02. Four degraded dates fall inside the 2016-2023 estimation sample years with RTH content (2017-11-13, 2019-x4, 2020-x4); none were excluded (no SCOPE rule covers them); they are flagged here.

Data (from the file itself): 14,165,173 rows total; timestamp span 2010-06-06T22:00:00Z to 2026-08-14T20:59:00Z (covers 2016-01-01..2023-12-31, so the Phase 0 stop conditions do not trigger); 11,318,126 rows before 2024-01-01 were extracted and nothing later was decoded further. Columns: length, rtype, publisher_id, instrument_id, ts_event, open, high, low, close, volume (prices int64 at 1e-9 scale). Roots present after resolution: ES and NQ only.

## Phase 2 engineering ledger (counts in application order)

| step | count |
|---|---|
| rows before 2024-01-01 (Phase 0 extract) | 11,318,126 |
| rule 1 unresolved (instrument_id, date) rows | 0 |
| rule 2 calendar-spread rows filtered | 1,031,774 |
| non-positive price rows before filter (SCOPE expects 573,473) | 573,473 |
| non-positive price rows after filter | 0 |
| rule 3 rows by root | ES 5,547,759, NQ 4,738,593 |
| rule 4 rows outside 2016-2023 by trade date | 2,839,822 |
| rows in estimation sample | 7,446,530 |
| raw trade sessions per root | 2,066 |
| weekend trade dates (anomaly, reported) | 1 |
| rule 6 front contracts used | ES 33, NQ 33 |
| rule 6 median holding, sessions / calendar days (SCOPE ~91 days) | ES 65 / 91, NQ 65 / 89 |
| rule 5 early-close sessions excluded (SCOPE expects ~18 designated) | ES 68, NQ 68 (see below) |
| rule 7 roll sessions +/-1 excluded | ES 96, NQ 96 |
| final sessions per root | ES 1,902, NQ 1,902 |
| final rows | 5,179,550 |

Early-close detail: the rule catches every session whose day portion halts before 15:00 New York. Of the 68 caught, 16 are the designated half-days SCOPE's ~18 refers to (day after Thanksgiving, July 3, Christmas Eve): 2016-11-25, 2017-07-03, 2017-11-24, 2018-07-03, 2018-11-23, 2018-12-24, 2019-07-03, 2019-11-29, 2019-12-24, 2020-07-03, 2020-11-27, 2020-12-24, 2021-11-26, 2022-11-25, 2023-07-03, 2023-11-24. The remainder are full-holiday shortened sessions (MLK, Presidents, Memorial, July 4, Labor, Thanksgiving Day), which halt at the same clock time and are excluded on the same evidence. All excluded dates: 2016-01-18, 2016-02-15, 2016-05-30, 2016-07-04, 2016-09-05, 2016-11-24, 2016-11-25, 2017-01-16, 2017-02-20, 2017-05-29, 2017-07-03, 2017-07-04, 2017-09-04, 2017-11-23, 2017-11-24, 2018-01-15, 2018-02-19, 2018-05-28, 2018-07-03, 2018-07-04, 2018-09-03, 2018-11-22, 2018-11-23, 2018-12-05, 2018-12-24, 2019-01-21, 2019-02-18, 2019-05-27, 2019-07-03, 2019-07-04, 2019-09-02, 2019-11-28, 2019-11-29, 2019-12-24, 2020-01-20, 2020-02-17, 2020-05-25, 2020-07-03, 2020-09-07, 2020-11-26, 2020-11-27, 2020-12-24, 2021-01-18, 2021-02-15, 2021-04-02, 2021-05-31, 2021-07-05, 2021-09-06, 2021-11-25, 2021-11-26, 2022-01-17, 2022-02-21, 2022-05-30, 2022-06-20, 2022-07-04, 2022-09-05, 2022-11-24, 2022-11-25, 2023-01-16, 2023-02-20, 2023-04-07, 2023-05-29, 2023-06-19, 2023-07-03, 2023-07-04, 2023-09-04, 2023-11-23, 2023-11-24.

Session-count reconciliation: 2,066 raw sessions per root over 2016-2023; SCOPE's ~2,742 'from 2016' is consistent with the file's full 2016-2026.6 span (2,066 + ~675 projected sessions 2024-2026), not with 2016-2023 alone.

## Phase 3 validation gates (numbers, no flags)

- Price scaling: int64 / 1e9 confirmed; decoded ranges ES [1,804.50, 4,841.50], NQ [3,868.25, 17,163.00].
- Tick grid: 0 of 4,328,167 non-zero close-to-close increments violate the 0.25 tick multiple.
- Bars per Globex session by year (mean / p5 / max):
    - ES_2016: 1359.3 / 1346 / 1365
    - ES_2017: 1349.4 / 1324 / 1365
    - ES_2018: 1356.7 / 1353 / 1367
    - ES_2019: 1362.6 / 1357 / 1366
    - ES_2020: 1362.0 / 1364 / 1367
    - ES_2021: 1372.5 / 1365 / 1380
    - ES_2022: 1380.0 / 1380 / 1380
    - ES_2023: 1379.3 / 1376 / 1380
    - NQ_2016: 1312.9 / 1243 / 1365
    - NQ_2017: 1336.7 / 1302 / 1365
    - NQ_2018: 1357.2 / 1355 / 1367
    - NQ_2019: 1363.7 / 1362 / 1366
    - NQ_2020: 1361.1 / 1364 / 1367
    - NQ_2021: 1372.7 / 1365 / 1380
    - NQ_2022: 1379.9 / 1380 / 1380
    - NQ_2023: 1379.9 / 1379 / 1380
- Fill ratio (bars/1380) by year: ES_2016 0.9850, ES_2017 0.9778, ES_2018 0.9831, ES_2019 0.9874, ES_2020 0.9869, ES_2021 0.9946, ES_2022 1.0000, ES_2023 0.9995, NQ_2016 0.9514, NQ_2017 0.9686, NQ_2018 0.9835, NQ_2019 0.9882, NQ_2020 0.9863, NQ_2021 0.9947, NQ_2022 1.0000, NQ_2023 0.9999 - consistent with SCOPE's 95-100% from 2016.
- Zero-volume bar fraction by year: ES_2016 0.00000, ES_2017 0.00000, ES_2018 0.00000, ES_2019 0.00000, ES_2020 0.00000, ES_2021 0.00000, ES_2022 0.00000, ES_2023 0.00000, NQ_2016 0.00000, NQ_2017 0.00000, NQ_2018 0.00000, NQ_2019 0.00000, NQ_2020 0.00000, NQ_2021 0.00000, NQ_2022 0.00000, NQ_2023 0.00000
- Zero-volume fraction by NY hour: 00h 0.0000, 01h 0.0000, 02h 0.0000, 03h 0.0000, 04h 0.0000, 05h 0.0000, 06h 0.0000, 07h 0.0000, 08h 0.0000, 09h 0.0000, 10h 0.0000, 11h 0.0000, 12h 0.0000, 13h 0.0000, 14h 0.0000, 15h 0.0000, 16h 0.0000, 17h 0.0000, 18h 0.0000, 19h 0.0000, 20h 0.0000, 21h 0.0000, 22h 0.0000, 23h 0.0000
- 1-minute log-return moments by year (n / mean / sd / skew / kurtosis):
    - ES_2016: 324,640 / -1.86e-08 / 3.43e-04 / 4.62 / 1895
    - ES_2017: 319,573 / -6.06e-09 / 1.78e-04 / 1.24 / 1147
    - ES_2018: 321,304 / -4.75e-09 / 4.13e-04 / 6.39 / 2176
    - ES_2019: 322,689 / -4.85e-09 / 3.17e-04 / 2.79 / 1989
    - ES_2020: 325,276 / -5.62e-09 / 7.31e-04 / 4.29 / 3278
    - ES_2021: 327,798 / -2.06e-09 / 3.24e-04 / 0.89 / 1226
    - ES_2022: 328,193 / 5.89e-10 / 5.66e-04 / -1.33 / 1195
    - ES_2023: 325,275 / 4.78e-09 / 3.18e-04 / -3.05 / 867
    - NQ_2016: 313,542 / -1.60e-08 / 4.09e-04 / 4.66 / 1906
    - NQ_2017: 316,565 / -2.48e-09 / 2.47e-04 / 5.08 / 2056
    - NQ_2018: 321,425 / -1.13e-09 / 5.33e-04 / 4.13 / 1788
    - NQ_2019: 322,964 / -4.72e-09 / 3.93e-04 / 0.38 / 1873
    - NQ_2020: 325,065 / 5.47e-09 / 7.84e-04 / 3.32 / 2388
    - NQ_2021: 327,836 / -6.34e-09 / 4.49e-04 / 3.77 / 1461
    - NQ_2022: 328,188 / 5.21e-09 / 7.46e-04 / -0.41 / 1214
    - NQ_2023: 325,413 / 1.17e-08 / 4.27e-04 / -4.88 / 989
- Outliers |r| > 10 sd(year, root): total 2,746, by year ES_2016 159, ES_2017 133, ES_2018 157, ES_2019 184, ES_2020 191, ES_2021 169, ES_2022 180, ES_2023 180, NQ_2016 152, NQ_2017 158, NQ_2018 158, NQ_2019 181, NQ_2020 184, NQ_2021 173, NQ_2022 196, NQ_2023 191. Flagged and counted, none removed.

## Phase 4 signature plots and noise measurement

Raw signature tables (mean daily RV against M), full sample; figure: `s03_signature.png`.

**ES GLOBEX** (n_days 1901): M=23: 1.193e-04, M=46: 1.207e-04, M=138: 1.225e-04, M=345: 1.264e-04, M=1380: 1.312e-04
**ES RTH** (n_days 1901): M=13: 6.907e-05, M=26: 7.002e-05, M=78: 7.309e-05, M=195: 7.425e-05, M=390: 7.438e-05
**NQ GLOBEX** (n_days 1901): M=23: 1.817e-04, M=46: 1.845e-04, M=138: 1.839e-04, M=345: 1.876e-04, M=1380: 1.890e-04
**NQ RTH** (n_days 1901): M=13: 1.129e-04, M=26: 1.132e-04, M=78: 1.162e-04, M=195: 1.165e-04, M=390: 1.146e-04

### Signature linearity (takes precedence over estimates)

R^2 of the mean-RV-on-M regression: ES GLOBEX 0.87, ES RTH 0.65, NQ GLOBEX 0.68, NQ RTH 0.14.

The signature plots rise from coarse to fine M by only ~4-10% of the level, and the rise is not cleanly linear in M (NQ RTH R^2 = 0.14; ES RTH 0.65; NQ GLOBEX 0.68; ES GLOBEX 0.87). Per the pre-registration, weak linearity means the additive iid noise model is at best marginal at 1-minute sampling and the point estimates below inherit that caveat. At this sampling frequency the noise contribution to RV is close to the resolution limit of the signature method.

### N1 and N2, full sample

| root | geom | n_days | intercept_EIV | omega2_N1 | omega2_N2 | NSR_N1 | NSR_N2 | signature_R2 |
|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | 1901 | 0.000121 | 3.95e-09 | 4.75e-08 | 3.27e-05 | 0.000393 | 0.8721 |
| ES | RTH | 1901 | 7.04e-05 | 6.34e-09 | 9.54e-08 | 9.01e-05 | 0.00135 | 0.6521 |
| NQ | GLOBEX | 1901 | 0.000184 | 2.12e-09 | 6.85e-08 | 1.15e-05 | 0.000373 | 0.6750 |
| NQ | RTH | 1901 | 0.000114 | 1.98e-09 | 1.47e-07 | 1.73e-05 | 0.00129 | 0.1412 |

### By year

| root | geom | group | NSR_N1 | NSR_N2 | signature_R2 |
|---|---|---|---|---|---|
| ES | GLOBEX | y2016 | 6.16e-05 | 0.000423 | 0.9668 |
| ES | GLOBEX | y2017 | 0.000162 | 0.000521 | 0.9783 |
| ES | GLOBEX | y2018 | 2.98e-05 | 0.000393 | 0.9157 |
| ES | GLOBEX | y2019 | 4.7e-05 | 0.00041 | 0.8641 |
| ES | GLOBEX | y2020 | 4.24e-05 | 0.000399 | 0.5585 |
| ES | GLOBEX | y2021 | 1.34e-05 | 0.000376 | 0.8634 |
| ES | GLOBEX | y2022 | 4.17e-06 | 0.000366 | 0.0995 |
| ES | GLOBEX | y2023 | 2.12e-05 | 0.000383 | 0.8912 |
| ES | RTH | y2016 | 0.000156 | 0.00144 | 0.9869 |
| ES | RTH | y2017 | 0.00038 | 0.00166 | 0.9907 |
| ES | RTH | y2018 | 7.9e-05 | 0.00136 | 0.6976 |
| ES | RTH | y2019 | 0.000152 | 0.00142 | 0.8514 |
| ES | RTH | y2020 | 0.000157 | 0.00139 | 0.4301 |
| ES | RTH | y2021 | 6.54e-06 | 0.00129 | 0.0472 |
| ES | RTH | y2022 | -1.24e-07 | 0.00128 | 9.86e-06 |
| ES | RTH | y2023 | 2.38e-05 | 0.0013 | 0.3894 |
| NQ | GLOBEX | y2016 | 6.82e-06 | 0.00037 | 0.2488 |
| NQ | GLOBEX | y2017 | 1.96e-05 | 0.000383 | 0.8771 |
| NQ | GLOBEX | y2018 | 1.71e-05 | 0.000379 | 0.8150 |
| NQ | GLOBEX | y2019 | 1.18e-06 | 0.000366 | 0.00281 |
| NQ | GLOBEX | y2020 | 3.11e-05 | 0.000389 | 0.4885 |
| NQ | GLOBEX | y2021 | 3.28e-06 | 0.000364 | 0.0594 |
| NQ | GLOBEX | y2022 | -3.58e-06 | 0.000359 | 0.1042 |
| NQ | GLOBEX | y2023 | 7.09e-06 | 0.000368 | 0.5135 |
| NQ | RTH | y2016 | -4.6e-05 | 0.00125 | 0.2823 |
| NQ | RTH | y2017 | 6.4e-05 | 0.00135 | 0.8963 |
| NQ | RTH | y2018 | 4.71e-05 | 0.00132 | 0.5337 |
| NQ | RTH | y2019 | 7.62e-06 | 0.00129 | 0.0324 |
| NQ | RTH | y2020 | 8.11e-05 | 0.00132 | 0.2727 |
| NQ | RTH | y2021 | -8.07e-06 | 0.00126 | 0.0127 |
| NQ | RTH | y2022 | -1.31e-05 | 0.00126 | 0.1155 |
| NQ | RTH | y2023 | -3.53e-05 | 0.00125 | 0.5294 |

### By volatility tercile (daily RV at coarsest M)

| root | geom | group | NSR_N1 | NSR_N2 | signature_R2 |
|---|---|---|---|---|---|
| ES | GLOBEX | terc1 | 0.000188 | 0.000538 | 0.8133 |
| ES | GLOBEX | terc2 | 6.79e-05 | 0.000426 | 0.8643 |
| ES | GLOBEX | terc3 | 1.59e-05 | 0.000377 | 0.8433 |
| ES | RTH | terc1 | 0.000636 | 0.00184 | 0.7713 |
| ES | RTH | terc2 | 0.000217 | 0.00147 | 0.6995 |
| ES | RTH | terc3 | 3.09e-05 | 0.0013 | 0.3463 |
| NQ | GLOBEX | terc1 | 9.86e-05 | 0.000449 | 0.5442 |
| NQ | GLOBEX | terc2 | 3.32e-05 | 0.000391 | 0.5481 |
| NQ | GLOBEX | terc3 | -1.18e-06 | 0.000362 | 0.0181 |
| NQ | RTH | terc1 | 0.000384 | 0.00159 | 0.5196 |
| NQ | RTH | terc2 | 0.000101 | 0.00136 | 0.3373 |
| NQ | RTH | terc3 | -3.46e-05 | 0.00124 | 0.4597 |

### N1 vs N2 disagreement (reported, not averaged)

N2 exceeds N1 by roughly one order of magnitude in every cell (full-sample ratios: ES GLOBEX 12x, ES RTH 15x, NQ GLOBEX 32x, NQ RTH 74x). Mechanism, as documented in DECISIONS item 12: N2 = RV_finest/(2n) assumes noise dominates the finest-grid RV (2n*omega^2 >> IV); at 1-minute bars RV_finest is almost entirely IV, so N2 returns approximately IV/(2n) - an upper bound, not a noise measurement. This is the same degeneracy S02 identified for estimator E6 at NSR -> 0.

### Placement relative to the S02 sweep (1e-5 to 1e-1)

Measured NSR by N1 spans 1.2e-05 to 9.0e-05 across instrument x geometry (NQ GLOBEX lowest, ES RTH highest); by N2, 3.7e-04 to 1.4e-03. Both ranges sit inside the S02 sweep [1e-5, 1e-1], in its bottom two decades: N1 places ES/NQ at 1-minute sampling at the extreme low end of the sweep (1e-5 to 1e-4), N2 - which the mechanism above marks as an upper bound - at 4e-4 to 1.4e-3. No measured value approaches the upper decades of the S02 sweep.
