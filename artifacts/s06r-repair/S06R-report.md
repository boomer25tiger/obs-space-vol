# Session 6R report, defect repair and rerun of Parts C, D and E

Generated 2026-08-19T05:33:52+00:00 (UTC). Prior S05, S05A, S05B, S05D and S05E artifacts are superseded but left in place; nothing was deleted or overwritten. All new output under `sessions/s06r-repair/`.

## Phase 1, invariant tests against the stored S05 artifacts

The five assertions of item 39 were written before any repair (`tests/test_invariants.py`) and run first against the STORED S05 artifacts, as a record that they detect the defects they were written for:

| test | FAIL | PASS | n_lambda_rows_checked |
|---|---|---|---|
| assert_effective_M | 88 | 36 | -- |
| assert_forecasts_positive | 46 | 122 | -- |
| assert_lambda_in_unit | 3683 | 0 | 11568 |
| assert_loss_finite | 35 | 85 | -- |
| assert_range_inputs | 8 | 0 | -- |

- **assert_forecasts_positive**: 46 failures. First: `[assert_forecasts_positive] cell=ES_GLOBEX_B0_1day model=M4_HARQ: 0 non-finite, 0 non-positive, 2 at or below the 1e-300 floor, of 1453 forecasts; min=1e-300`
- **assert_loss_finite**: 35 failures. First: `[assert_loss_finite] cell=ES_GLOBEX_B0_1h/S-A: 1318 non-finite of 286972 entries (shape (40996, 7)); by model: M1_EWMA=180, M2_HAR=180, M3_HARJ=180, M4_HARQ=180, M5_RGARCH=181, M6_PARK=237, M6_GK=180`
- **assert_lambda_in_unit**: 3683 failures. First: `[assert_lambda_in_unit] cell=ES/GLOBEX/B0/1day/M23/y0/t2 estimator=E2: 1 of 1 outside [0,1]; offending values [-1.080849]`
- **assert_range_inputs**: 8 failures. First: `[assert_range_inputs] cell=panel_ES_GLOBEX_B0: panel is missing ['high', 'low', 'close']; range estimators cannot be built from closes alone`
- **assert_effective_M**: 88 failures. First: `[assert_effective_M] cell=ES/GLOBEX/B0/1day/M5: M passed = 5 but effective count differs in 3 of 1953 windows (share at full nominal M = 0.9985, mean effective M = 5.00)`

All five fire. They are then wired into the repaired pipeline: `assert_forecasts_positive` inside the generation pass after filtering, `assert_loss_finite` before every MCS call, `assert_lambda_in_unit` at every Part C grid point, `assert_range_inputs` at panel construction, and `assert_effective_M` at every Part C aggregation.

## Phase 2, panel rebuild with OHLC

| root | geom | shape | byte_identical | n_differing | max_abs_diff |
|---|---|---|---|---|---|
| ES | GLOBEX | (1953, 1380) | True | 0 | 0 |
| NQ | GLOBEX | (1948, 1380) | True | 0 | 0 |
| ES | RTH | (1901, 390) | True | 0 | 0 |
| NQ | RTH | (1901, 390) | True | 0 | 0 |

The rebuilt close grid is byte-identical to the stored close-only panels in every cell (`True`), so the rebuild adds open, high and low without disturbing anything the prior sessions computed. The `present` mask is now persisted alongside the price grids in every panel file, which S05D found absent (item 38).

Share of bars with high equal to low, which bounds what a range estimator can carry:

| root | geom | n_bars | share_high_eq_low |
|---|---|---|---|
| ES | GLOBEX | 2.6548e+06 | 0.042175 |
| ES | RTH | 2.5966e+06 | 0.040803 |
| NQ | GLOBEX | 2.6355e+06 | 0.026623 |
| NQ | RTH | 2.5829e+06 | 0.026441 |

By year: `phase2_high_eq_low.csv`.

### M6_PARK and M6_GK, old against new

| root | geom | model | mean_old | mean_new | ratio_new_over_old | n_zero_old | n_zero_new | n_windows |
|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | M6_PARK | 0.00011009 | 0.00011762 | 1.0684 | 0 | 0 | 1953 |
| ES | GLOBEX | M6_GK | 0.00010652 | 0.00011595 | 1.0885 | 0 | 0 | 1953 |
| NQ | GLOBEX | M6_PARK | 0.00016866 | 0.00017938 | 1.0636 | 0 | 0 | 1948 |
| NQ | GLOBEX | M6_GK | 0.00016192 | 0.00017595 | 1.0867 | 0 | 0 | 1948 |
| ES | RTH | M6_PARK | 6.5067e-05 | 7.1292e-05 | 1.0957 | 0 | 0 | 1901 |
| ES | RTH | M6_GK | 6.2799e-05 | 7.0852e-05 | 1.1282 | 0 | 0 | 1901 |
| NQ | RTH | M6_PARK | 0.00010626 | 0.00011665 | 1.0977 | 0 | 0 | 1901 |
| NQ | RTH | M6_GK | 0.00010066 | 0.00011365 | 1.1291 | 0 | 0 | 1901 |

Rebuilding from true bar high and low raises the range estimators by 1.064 to 1.129 of their old level, confirming the downward bias item 43 names. Neither construction produces exact-zero forecasts at the 1day window in any cell.

### E3 error-correlation gate re-run on the corrected series

| root | geom | proxy_i | proxy_j | error_corr | n |
|---|---|---|---|---|---|
| ES | GLOBEX | RV | BV | 0.91857 | 1953 |
| ES | GLOBEX | RV | PARK | -0.020119 | 1953 |
| ES | GLOBEX | RV | GK | -0.014399 | 1953 |
| ES | GLOBEX | RV | PARK_old | -0.036983 | 1953 |
| ES | GLOBEX | RV | GK_old | -0.038119 | 1953 |
| ES | GLOBEX | BV | PARK | -0.0094265 | 1953 |
| ES | GLOBEX | BV | GK | -0.0026705 | 1953 |
| ES | GLOBEX | BV | PARK_old | -0.022909 | 1953 |
| ES | GLOBEX | BV | GK_old | -0.023211 | 1953 |
| ES | GLOBEX | PARK | GK | 0.85849 | 1953 |
| ES | GLOBEX | PARK | PARK_old | 0.99259 | 1953 |
| ES | GLOBEX | PARK | GK_old | 0.84043 | 1953 |
| ES | GLOBEX | GK | PARK_old | 0.85037 | 1953 |
| ES | GLOBEX | GK | GK_old | 0.97948 | 1953 |
| ES | GLOBEX | PARK_old | GK_old | 0.8517 | 1953 |
| NQ | GLOBEX | RV | BV | 0.84944 | 1948 |
| NQ | GLOBEX | RV | PARK | 0.045848 | 1948 |
| NQ | GLOBEX | RV | GK | 0.0087663 | 1948 |
| NQ | GLOBEX | RV | PARK_old | 0.033915 | 1948 |
| NQ | GLOBEX | RV | GK_old | -0.0041105 | 1948 |
| NQ | GLOBEX | BV | PARK | 0.053535 | 1948 |
| NQ | GLOBEX | BV | GK | 0.022518 | 1948 |
| NQ | GLOBEX | BV | PARK_old | 0.044472 | 1948 |
| NQ | GLOBEX | BV | GK_old | 0.014133 | 1948 |
| NQ | GLOBEX | PARK | GK | 0.84436 | 1948 |
| NQ | GLOBEX | PARK | PARK_old | 0.99228 | 1948 |
| NQ | GLOBEX | PARK | GK_old | 0.82779 | 1948 |
| NQ | GLOBEX | GK | PARK_old | 0.83334 | 1948 |
| NQ | GLOBEX | GK | GK_old | 0.97671 | 1948 |
| NQ | GLOBEX | PARK_old | GK_old | 0.83731 | 1948 |
| ES | RTH | RV | BV | 0.93139 | 1901 |
| ES | RTH | RV | PARK | 0.038844 | 1901 |
| ES | RTH | RV | GK | 0.075084 | 1901 |
| ES | RTH | RV | PARK_old | 0.011136 | 1901 |
| ES | RTH | RV | GK_old | 0.044056 | 1901 |
| ES | RTH | BV | PARK | 0.049965 | 1901 |
| ES | RTH | BV | GK | 0.086865 | 1901 |
| ES | RTH | BV | PARK_old | 0.027947 | 1901 |
| ES | RTH | BV | GK_old | 0.063976 | 1901 |
| ES | RTH | PARK | GK | 0.84219 | 1901 |
| ES | RTH | PARK | PARK_old | 0.98945 | 1901 |
| ES | RTH | PARK | GK_old | 0.77064 | 1901 |
| ES | RTH | GK | PARK_old | 0.83964 | 1901 |
| ES | RTH | GK | GK_old | 0.95694 | 1901 |
| ES | RTH | PARK_old | GK_old | 0.79737 | 1901 |
| NQ | RTH | RV | BV | 0.90861 | 1901 |
| NQ | RTH | RV | PARK | 0.052205 | 1901 |
| NQ | RTH | RV | GK | 0.059207 | 1901 |
| NQ | RTH | RV | PARK_old | 0.0393 | 1901 |
| NQ | RTH | RV | GK_old | 0.037953 | 1901 |
| NQ | RTH | BV | PARK | 0.057019 | 1901 |
| NQ | RTH | BV | GK | 0.059621 | 1901 |
| NQ | RTH | BV | PARK_old | 0.047462 | 1901 |
| NQ | RTH | BV | GK_old | 0.044639 | 1901 |
| NQ | RTH | PARK | GK | 0.83929 | 1901 |
| NQ | RTH | PARK | PARK_old | 0.99098 | 1901 |
| NQ | RTH | PARK | GK_old | 0.77381 | 1901 |
| NQ | RTH | GK | PARK_old | 0.84209 | 1901 |
| NQ | RTH | GK | GK_old | 0.95967 | 1901 |
| NQ | RTH | PARK_old | GK_old | 0.79975 | 1901 |

Parkinson-Garman-Klass error correlation is 0.8461 on the corrected series against 0.8215 on the misconstructed ones, and the largest off-diagonal error correlation among the corrected proxies is 0.9314. **E3 remains excluded at the pre-registered 0.20 threshold (True)**; the correction did not rescue it. Errors are measured against the S05B realized-kernel reference, since true integrated variance is unobservable on real data.

## Phase 3, calendar exclusion

Source: the CME Group published equity-index holiday calendar, generated here by rule with no reference to any realized quantity (item 42). Two classes: EARLY_CLOSE_1300 (day session halts 13:00 New York) and FULL_CLOSURE_0930 (day session does not open).

| date | holiday | halt_ny | halt_ny_min | cls |
|---|---|---|---|---|
| 2016-01-18 | MLK | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2016-02-15 | Presidents | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2016-03-25 | GoodFriday | 09:30 | 570 | FULL_CLOSURE_0930 |
| 2016-05-30 | Memorial | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2016-07-04 | Independence | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2016-09-05 | Labor | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2016-11-24 | Thanksgiving | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2017-01-16 | MLK | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2017-02-20 | Presidents | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2017-04-14 | GoodFriday | 09:30 | 570 | FULL_CLOSURE_0930 |
| 2017-05-29 | Memorial | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2017-07-04 | Independence | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2017-09-04 | Labor | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2017-11-23 | Thanksgiving | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2018-01-15 | MLK | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2018-02-19 | Presidents | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2018-03-30 | GoodFriday | 09:30 | 570 | FULL_CLOSURE_0930 |
| 2018-05-28 | Memorial | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2018-07-04 | Independence | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2018-09-03 | Labor | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2018-11-22 | Thanksgiving | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2018-12-05 | DayOfMourning | 09:30 | 570 | FULL_CLOSURE_0930 |
| 2019-01-21 | MLK | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2019-02-18 | Presidents | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2019-04-19 | GoodFriday | 09:30 | 570 | FULL_CLOSURE_0930 |
| 2019-05-27 | Memorial | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2019-07-04 | Independence | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2019-09-02 | Labor | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2019-11-28 | Thanksgiving | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2020-01-20 | MLK | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2020-02-17 | Presidents | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2020-04-10 | GoodFriday | 09:30 | 570 | FULL_CLOSURE_0930 |
| 2020-05-25 | Memorial | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2020-07-03 | Independence | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2020-09-07 | Labor | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2020-11-26 | Thanksgiving | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2021-01-18 | MLK | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2021-02-15 | Presidents | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2021-04-02 | GoodFriday | 09:30 | 570 | FULL_CLOSURE_0930 |
| 2021-05-31 | Memorial | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2021-07-05 | Independence | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2021-09-06 | Labor | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2021-11-25 | Thanksgiving | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2022-01-17 | MLK | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2022-02-21 | Presidents | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2022-04-15 | GoodFriday | 09:30 | 570 | FULL_CLOSURE_0930 |
| 2022-05-30 | Memorial | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2022-06-20 | Juneteenth | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2022-07-04 | Independence | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2022-09-05 | Labor | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2022-11-24 | Thanksgiving | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2023-01-16 | MLK | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2023-02-20 | Presidents | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2023-04-07 | GoodFriday | 09:30 | 570 | FULL_CLOSURE_0930 |
| 2023-05-29 | Memorial | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2023-06-19 | Juneteenth | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2023-07-04 | Independence | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2023-09-04 | Labor | 13:00 | 780 | EARLY_CLOSE_1300 |
| 2023-11-23 | Thanksgiving | 13:00 | 780 | EARLY_CLOSE_1300 |

| root | geom | n_sessions | n_holiday_sessions | n_minutes_excluded | share_minutes_excluded | halt_slot |
|---|---|---|---|---|---|---|
| ES | GLOBEX | 1953 | 52 | 13110 | 0.0048643 | 1140 |
| NQ | GLOBEX | 1948 | 47 | 11910 | 0.0044304 | 1140 |
| ES | RTH | 1901 | 0 | 0 | 0 | -1 |
| NQ | RTH | 1901 | 0 | 0 | 0 | -1 |

### Cross-check against the S05B zero-variance windows

| root | geom | horizon | n_windows | n_zero_rv | n_excluded | n_zero_not_covered | n_excluded_with_nonzero_rv |
|---|---|---|---|---|---|---|---|
| ES | GLOBEX | 1h | 42966 | 186 | 165 | 21 | 0 |
| ES | GLOBEX | 30min | 87885 | 435 | 385 | 50 | 0 |
| NQ | GLOBEX | 1h | 42856 | 169 | 150 | 19 | 0 |
| NQ | GLOBEX | 30min | 87660 | 396 | 350 | 46 | 0 |
| ES | RTH | 1h | 11406 | 0 | 0 | 0 | 0 |
| ES | RTH | 30min | 22812 | 0 | 0 | 0 | 0 |
| NQ | RTH | 1h | 11406 | 0 | 0 | 0 | 0 |
| NQ | RTH | 30min | 22812 | 0 | 0 | 0 | 0 |

**No excluded window carried non-zero realized variance in any cell (0 of all excluded windows), so the calendar never removes traded data.** In the other direction 136 zero-variance windows are not covered by the calendar. They fall on:

| session | windows | dow |
|---|---|---|
| 2017-10-10 | 1 | Tuesday |
| 2018-04-30 | 2 | Monday |
| 2019-02-27 | 14 | Wednesday |
| 2020-03-09 | 51 | Monday |
| 2020-03-12 | 2 | Thursday |
| 2020-03-18 | 44 | Wednesday |
| 2020-03-23 | 4 | Monday |
| 2020-03-24 | 6 | Tuesday |
| 2020-07-01 | 12 | Wednesday |

2020-03-09, 03-12, 03-18, 03-23 and 03-24 are the COVID circuit-breaker limit-halt days and 2020-07-01 and 2019-02-27 sit in or beside the Databento degraded-condition set S04 R2 flagged. Neither class is determinable from a calendar before the session begins, so per item 42 neither is excluded: they remain in the sample and their zero-variance windows are carried into Phase 7, where `assert_loss_finite` decides what happens to them.

## Phase 4, RGARCH stationarity diagnosis

| cell | n_refits | n_converged | persistence_mean | persistence_max | violates_stationarity | beta_last | gamma_last | phi_last | n_nonpositive | n_above_100x | share_pathological | divergence_at_refit_boundary | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ES/GLOBEX/B0/1day | 24 | 24 | 0.91954 | 0.93269 | False | 0.31869 | 0.70418 | 0.8675 | 0 | 0 | 0 | False | estimated (stationary) |
| ES/GLOBEX/B1/1day | 24 | 24 | 0.91914 | 0.93238 | False | 0.31624 | 0.70593 | 0.86843 | 0 | 0 | 0 | False | estimated (stationary) |
| ES/RTH/B0/1day | 23 | 23 | 0.9186 | 0.93082 | False | 0.33745 | 0.6355 | 0.92937 | 0 | 0 | 0 | False | estimated (stationary) |
| ES/RTH/B0/1h | 29 | 29 | 0.8893 | 0.91843 | False | 0.17426 | 0.67135 | 1.0519 | 0 | 0 | 0 | False | estimated (stationary) |
| ES/RTH/B0/30min | 30 | 30 | 0.92364 | 0.99384 | False | 0.26118 | 0.63327 | 1.044 | 0 | 0 | 0 | False | estimated (stationary) |
| ES/RTH/B1/1day | 23 | 23 | 0.91785 | 0.93048 | False | 0.33738 | 0.63186 | 0.93443 | 0 | 0 | 0 | False | estimated (stationary) |
| ES/RTH/B1/1h | 29 | 29 | 0.89039 | 0.91835 | False | 0.16775 | 0.67779 | 1.0531 | 0 | 0 | 0 | False | estimated (stationary) |
| ES/RTH/B1/30min | 30 | 30 | 0.91941 | 0.93852 | False | 0.25927 | 0.63561 | 1.045 | 0 | 0 | 0 | False | estimated (stationary) |
| NQ/GLOBEX/B0/1day | 23 | 23 | 0.91764 | 0.93169 | False | 0.35485 | 0.56974 | 1.0092 | 0 | 0 | 0 | False | estimated (stationary) |
| NQ/GLOBEX/B1/1day | 23 | 23 | 0.92173 | 0.98947 | False | 0.351 | 0.57148 | 1.012 | 0 | 0 | 0 | False | estimated (stationary) |
| NQ/RTH/B0/1day | 23 | 23 | 0.91648 | 0.93335 | False | 0.36329 | 0.55089 | 1.033 | 0 | 0 | 0 | False | estimated (stationary) |
| NQ/RTH/B0/1h | 29 | 29 | 0.85767 | 0.92875 | False | 0.16677 | 0.54959 | 1.2278 | 0 | 0 | 0 | False | estimated (stationary) |
| NQ/RTH/B0/30min | 30 | 30 | 0.88972 | 0.90499 | False | 0.21215 | 0.55698 | 1.2249 | 0 | 0 | 0 | False | estimated (stationary) |
| NQ/RTH/B1/1day | 23 | 23 | 0.91616 | 0.93275 | False | 0.36456 | 0.54782 | 1.0362 | 0 | 0 | 0 | False | estimated (stationary) |
| NQ/RTH/B1/1h | 29 | 29 | 0.85514 | 0.91467 | False | 0.15334 | 0.55991 | 1.2295 | 0 | 0 | 0 | False | estimated (stationary) |
| NQ/RTH/B1/30min | 30 | 30 | 0.8909 | 0.90605 | False | 0.20434 | 0.56422 | 1.2253 | 0 | 0 | 0 | False | estimated (stationary) |

Persistence is beta + gamma*phi, the log-linear Realized GARCH condition. **Variance targeting is NOT applied anywhere**: `partde.rgarch_ll` contains no targeting term, so omega is a free parameter and nothing pins the unconditional level.

Verdicts: estimated (stationary) (16).

Resulting model set per cell:

| cell | n_models | model_set | rgarch_included |
|---|---|---|---|
| ES/GLOBEX/B0/1day | 7 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | True |
| ES/GLOBEX/B1/1day | 7 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | True |
| ES/RTH/B0/1day | 7 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | True |
| ES/RTH/B0/1h | 7 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | True |
| ES/RTH/B0/30min | 7 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | True |
| ES/RTH/B1/1day | 7 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | True |
| ES/RTH/B1/1h | 7 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | True |
| ES/RTH/B1/30min | 7 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | True |
| NQ/GLOBEX/B0/1day | 7 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | True |
| NQ/GLOBEX/B1/1day | 7 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | True |
| NQ/RTH/B0/1day | 7 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | True |
| NQ/RTH/B0/1h | 7 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | True |
| NQ/RTH/B0/30min | 7 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | True |
| NQ/RTH/B1/1day | 7 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | True |
| NQ/RTH/B1/1h | 7 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | True |
| NQ/RTH/B1/30min | 7 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | True |

RGARCH was not filtered, respecified or constrained (item 41).

## Phase 5, forecast filter

**The positivity invariant halted 8 cells.** Item 39 requires a halt rather than a warning, and the halt is recorded per cell so the remaining cells could still be attempted; a halted cell produces no artifact and therefore reaches no MCS. The mechanism, identical in every case: the BPQ filter replaces forecasts outside the IN-SAMPLE realized-variance range, and in these cells the in-sample minimum is exactly zero because the warm-up window contains the zero-variance windows Phase 3 could not exclude on calendar grounds. A lower bound of zero admits a forecast floored at 1e-300, which then fails the positivity assertion. The filter definition was NOT altered to accommodate this (item 40 fixes it, and changing it here would be tuning):

| cell | assertion | message |
|---|---|---|
| NQ/GLOBEX/B0/1h | assert_forecasts_positive | [assert_forecasts_positive] cell=NQ/GLOBEX/B0/1h model=M4_HARQ: 0 non-finite, 0 non-positive, 2 at or below the 1e-300 floor, of 22137 forecasts; min=1e-300 |
| ES/GLOBEX/B1/1h | assert_forecasts_positive | [assert_forecasts_positive] cell=ES/GLOBEX/B1/1h model=M5_RGARCH: 0 non-finite, 1 non-positive, 1 at or below the 1e-300 floor, of 1384 forecasts; min=0 |
| ES/GLOBEX/B1/30min | assert_forecasts_positive | [assert_forecasts_positive] cell=ES/GLOBEX/B1/30min model=M4_HARQ: 0 non-finite, 0 non-positive, 4 at or below the 1e-300 floor, of 79374 forecasts; min=1e-300 |
| NQ/GLOBEX/B1/1h | assert_forecasts_positive | [assert_forecasts_positive] cell=NQ/GLOBEX/B1/1h model=M4_HARQ: 0 non-finite, 0 non-positive, 1 at or below the 1e-300 floor, of 17985 forecasts; min=1e-300 |
| ES/GLOBEX/B0/1h | assert_forecasts_positive | [assert_forecasts_positive] cell=ES/GLOBEX/B0/1h model=M4_HARQ: 0 non-finite, 0 non-positive, 3 at or below the 1e-300 floor, of 40837 forecasts; min=1e-300 |
| ES/GLOBEX/B0/30min | assert_forecasts_positive | [assert_forecasts_positive] cell=ES/GLOBEX/B0/30min model=M6_PARK: 0 non-finite, 17 non-positive, 17 at or below the 1e-300 floor, of 21480 forecasts; min=0 |
| NQ/GLOBEX/B1/30min | assert_forecasts_positive | [assert_forecasts_positive] cell=NQ/GLOBEX/B1/30min model=M4_HARQ: 0 non-finite, 0 non-positive, 4 at or below the 1e-300 floor, of 83094 forecasts; min=1e-300 |
| NQ/GLOBEX/B0/30min | assert_forecasts_positive | [assert_forecasts_positive] cell=NQ/GLOBEX/B0/30min model=M4_HARQ: 0 non-finite, 0 non-positive, 4 at or below the 1e-300 floor, of 80564 forecasts; min=1e-300 |

## Phase 6, Part C rerun

E2 and E4 only, effective sub-bar count in place of nominal M, on the calendar-excluded sample.

### Var(log RV_M) = c + A M^b, repaired against S05B

| root | geom | btag | horizon | c_new | A_new | b_new | rmse_new | b_s05b | b_shift |
|---|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | 1day | 1.0178 | 2.0817 | -0.43929 | 0.049838 | -0.43929 | -2.9799e-09 |
| ES | GLOBEX | B1 | 1day | 0.9964 | 2.0268 | -0.40735 | 0.048407 | -0.40731 | -3.7697e-05 |
| NQ | GLOBEX | B0 | 1day | 1.0813 | 2.5864 | -0.68676 | 0.037971 | -0.68677 | 1.4778e-05 |
| NQ | GLOBEX | B1 | 1day | 1.0765 | 2.4162 | -0.64352 | 0.031599 | -0.64358 | 5.6858e-05 |
| ES | RTH | B0 | 1day | 1.0842 | 2.3344 | -0.63345 | 0.029458 | -0.63345 | 8.9362e-09 |
| ES | RTH | B0 | 1h | 1.0512 | 2.3215 | -0.46458 | 0.01484 | -0.46458 | 0 |
| ES | RTH | B0 | 30min | 0.81578 | 2.5857 | -0.41089 | 0.0044634 | -0.41089 | 0 |
| ES | RTH | B1 | 1day | 1.0985 | 2.4392 | -0.65567 | 0.030564 | -0.65573 | 5.6409e-05 |
| ES | RTH | B1 | 1h | 1.0492 | 2.3199 | -0.46712 | 0.015156 | -0.46706 | -5.9918e-05 |
| ES | RTH | B1 | 30min | 0.82046 | 2.5799 | -0.41537 | 0.0041788 | -0.41533 | -3.6573e-05 |
| NQ | RTH | B0 | 1day | 1.0574 | 3.5931 | -0.9765 | 0.016347 | -0.9765 | -9.5015e-09 |
| NQ | RTH | B0 | 1h | 1.4248 | 2.438 | -0.80223 | 0.011842 | -0.80223 | -3.2087e-09 |
| NQ | RTH | B0 | 30min | 1.3683 | 2.329 | -0.70043 | 0.0053188 | -0.70043 | -9.6077e-09 |
| NQ | RTH | B1 | 1day | 1.066 | 3.7617 | -1.0031 | 0.016995 | -1.0031 | -2.0095e-05 |
| NQ | RTH | B1 | 1h | 1.4144 | 2.4297 | -0.80519 | 0.011787 | -0.80522 | 2.7752e-05 |
| NQ | RTH | B1 | 30min | 1.3548 | 2.3044 | -0.69567 | 0.0052599 | -0.69551 | -0.00016267 |

**The exponent is unchanged by the repairs.** The largest shift across all sixteen cells is 1.63e-04. Neither the calendar exclusion, nor effective M, nor the OHLC rebuild moves it: the S05B finding that b lies between -0.41 and -1.00 against a trigamma reference of -1.14 survives the repair programme intact.

### Lambda outside [0,1]

14 of 248 grid points violate the bound. Reported, not halted (a violation here is a finding about the estimator, not a code defect):

| cell | estimator | lam |
|---|---|---|
| ES/GLOBEX/B0/1day/M5 | E2 | 1.1108 |
| ES/GLOBEX/B1/1day/M5 | E2 | 2.0494 |
| ES/RTH/B0/1h/M4 | E2 | 2.001 |
| ES/RTH/B0/1h/M5 | E2 | 1.9992 |
| ES/RTH/B0/1h/M6 | E2 | 1.2884 |
| ES/RTH/B0/30min/M5 | E2 | 2.8514 |
| ES/RTH/B0/30min/M6 | E2 | 1.5501 |
| ES/RTH/B1/1h/M4 | E2 | 2.0399 |
| ES/RTH/B1/1h/M5 | E2 | 1.9848 |
| ES/RTH/B1/1h/M6 | E2 | 1.3527 |
| ES/RTH/B1/30min/M5 | E2 | 2.8737 |
| ES/RTH/B1/30min/M6 | E2 | 1.5427 |
| NQ/RTH/B0/30min/M5 | E2 | 1.027 |
| NQ/RTH/B1/30min/M5 | E2 | 1.0293 |

### Effective M against window realized volatility (item 45)

| root | geom | btag | horizon | M | corr_effM_vol | mean_eff_M | sd_eff_M |
|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | 1day | 1379 | 0.14216 | 1354.3 | 47.517 |
| ES | GLOBEX | B1 | 1day | 1379 | 0.14753 | 1354.3 | 47.517 |
| NQ | GLOBEX | B0 | 1day | 1379 | 0.26518 | 1343.1 | 59.551 |
| NQ | GLOBEX | B1 | 1day | 1379 | 0.27002 | 1343.1 | 59.551 |
| ES | RTH | B0 | 1day | 389 | -0.33841 | 388.98 | 0.55572 |
| ES | RTH | B0 | 1h | 60 | -0.1468 | 59.996 | 0.22702 |
| ES | RTH | B0 | 30min | 30 | -0.12777 | 29.998 | 0.15126 |
| ES | RTH | B1 | 1day | 389 | -0.33467 | 388.98 | 0.55572 |
| ES | RTH | B1 | 1h | 60 | -0.14754 | 59.996 | 0.22702 |
| ES | RTH | B1 | 30min | 30 | -0.12843 | 29.998 | 0.15126 |
| NQ | RTH | B0 | 1day | 389 | -0.28538 | 388.98 | 0.58338 |
| NQ | RTH | B0 | 1h | 60 | -0.11051 | 59.996 | 0.23832 |
| NQ | RTH | B0 | 30min | 30 | -0.087311 | 29.998 | 0.15972 |
| NQ | RTH | B1 | 1day | 389 | -0.27827 | 388.98 | 0.58338 |
| NQ | RTH | B1 | 1h | 60 | -0.11164 | 59.996 | 0.23832 |
| NQ | RTH | B1 | 30min | 30 | -0.088236 | 29.998 | 0.15972 |

The coupling is not negligible: the correlation between effective sub-bar count and window realized volatility runs from -0.338 to 0.270, positive in GLOBEX and negative in RTH.

### Level sanity check (item 49)

| root | geom | btag | horizon | c_new | implied_sd_log_iv | implied_vol_ratio_1sd | sd_log_rv | vol_ratio_p84_p16 |
|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | 1day | 1.0178 | 1.0089 | 2.7425 | 1.0212 | 2.7602 |
| ES | GLOBEX | B1 | 1day | 0.9964 | 0.9982 | 2.7134 | 1.0227 | 2.7696 |
| NQ | GLOBEX | B0 | 1day | 1.0813 | 1.0399 | 2.8288 | 1.0373 | 2.853 |
| NQ | GLOBEX | B1 | 1day | 1.0765 | 1.0376 | 2.8223 | 1.0396 | 2.8547 |
| ES | RTH | B0 | 1day | 1.0842 | 1.0413 | 2.8328 | 1.0443 | 2.9241 |
| ES | RTH | B0 | 1h | 1.0512 | 1.0253 | 2.7878 | 1.1746 | 3.2782 |
| ES | RTH | B0 | 30min | 0.81578 | 0.9032 | 2.4675 | 1.2059 | 3.3891 |
| ES | RTH | B1 | 1day | 1.0985 | 1.0481 | 2.8522 | 1.0479 | 2.9421 |
| ES | RTH | B1 | 1h | 1.0492 | 1.0243 | 2.7852 | 1.1722 | 3.2691 |
| ES | RTH | B1 | 30min | 0.82046 | 0.90579 | 2.4739 | 1.2033 | 3.3796 |
| NQ | RTH | B0 | 1day | 1.0574 | 1.0283 | 2.7963 | 1.0231 | 2.883 |
| NQ | RTH | B0 | 1h | 1.4248 | 1.1936 | 3.299 | 1.2249 | 3.5251 |
| NQ | RTH | B0 | 30min | 1.3683 | 1.1697 | 3.2211 | 1.2576 | 3.6191 |
| NQ | RTH | B1 | 1day | 1.066 | 1.0325 | 2.808 | 1.0263 | 2.8829 |
| NQ | RTH | B1 | 1h | 1.4144 | 1.1893 | 3.2847 | 1.2201 | 3.5075 |
| NQ | RTH | B1 | 30min | 1.3548 | 1.164 | 3.2026 | 1.2528 | 3.6005 |

The fitted intercept implies sd(log IV) of 0.903 to 1.194 and a one-standard-deviation volatility ratio of 2.47 to 3.30. The sample's own realized volatility ratio between the 84th and 16th percentiles is 2.76 to 3.62. **The implied level is consistent with the sample's realized volatility range**; the level was never checked in five prior sessions and it survives the check.

## Phase 7, Parts D and E rerun

Forecast panels and loss matrices are persisted for every cell (`cache/gen_*.npz`, `cache/loss_*.npz`, item 48). `assert_loss_finite` was called before every MCS call; it raised in 0 (cell, scheme) combinations, which were NOT run and are marked HALTED:

### MCS composition, repaired against S05

| root | geom | btag | horizon | scheme | n_obs | model_set | mcs75 | mcs90 | seed |
|---|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | 1day | S-A | 1453 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH | 3280325159 |
| ES | GLOBEX | B0 | 1day | S-B_q0.80 | 291 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M5_RGARCH | M3_HARJ|M5_RGARCH | 4011620097 |
| ES | GLOBEX | B0 | 1day | S-C_q0.80 | 291 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR|M5_RGARCH | M2_HAR|M5_RGARCH | 1932513795 |
| ES | GLOBEX | B0 | 1day | S-B_q0.90 | 146 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M5_RGARCH | M5_RGARCH | 490092290 |
| ES | GLOBEX | B0 | 1day | S-C_q0.90 | 146 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR|M5_RGARCH | M2_HAR|M4_HARQ|M5_RGARCH|M6_GK|M6_PARK | 2782361068 |
| ES | GLOBEX | B1 | 1day | S-A | 1453 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH | 4040406603 |
| ES | GLOBEX | B1 | 1day | S-B_q0.80 | 291 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M5_RGARCH | M5_RGARCH | 2357419644 |
| ES | GLOBEX | B1 | 1day | S-C_q0.80 | 291 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR|M5_RGARCH | M2_HAR|M5_RGARCH | 795905876 |
| ES | GLOBEX | B1 | 1day | S-B_q0.90 | 146 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M5_RGARCH | M5_RGARCH | 1194876513 |
| ES | GLOBEX | B1 | 1day | S-C_q0.90 | 146 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR|M5_RGARCH | M2_HAR|M4_HARQ|M5_RGARCH|M6_GK|M6_PARK | 3628868369 |
| NQ | GLOBEX | B0 | 1day | S-A | 1448 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ | 3536224341 |
| NQ | GLOBEX | B0 | 1day | S-B_q0.80 | 290 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 778805554 |
| NQ | GLOBEX | B0 | 1day | S-C_q0.80 | 290 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 346491313 |
| NQ | GLOBEX | B0 | 1day | S-B_q0.90 | 145 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 1702618649 |
| NQ | GLOBEX | B0 | 1day | S-C_q0.90 | 145 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 3586788295 |
| NQ | GLOBEX | B1 | 1day | S-A | 1448 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR|M3_HARJ|M4_HARQ | 3337662334 |
| NQ | GLOBEX | B1 | 1day | S-B_q0.80 | 290 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 1967094566 |
| NQ | GLOBEX | B1 | 1day | S-C_q0.80 | 290 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 2186999783 |
| NQ | GLOBEX | B1 | 1day | S-B_q0.90 | 145 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 979901154 |
| NQ | GLOBEX | B1 | 1day | S-C_q0.90 | 145 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR|M6_PARK | 1250553518 |
| ES | RTH | B0 | 1day | S-A | 1401 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ | 629663445 |
| ES | RTH | B0 | 1day | S-B_q0.80 | 280 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 4238439140 |
| ES | RTH | B0 | 1day | S-C_q0.80 | 280 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 3945777218 |
| ES | RTH | B0 | 1day | S-B_q0.90 | 140 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M1_EWMA|M2_HAR|M6_GK|M6_PARK | 2768131305 |
| ES | RTH | B0 | 1day | S-C_q0.90 | 140 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_GK|M6_PARK | 3441137014 |
| ES | RTH | B0 | 1h | S-A | 10906 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 310945355 |
| ES | RTH | B0 | 1h | S-B_q0.80 | 2181 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 34901983 |
| ES | RTH | B0 | 1h | S-C_q0.80 | 2181 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 4016535017 |
| ES | RTH | B0 | 1h | S-B_q0.90 | 1091 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 2778071878 |
| ES | RTH | B0 | 1h | S-C_q0.90 | 1091 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 1734405981 |
| ES | RTH | B0 | 30min | S-A | 22312 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 3907597529 |
| ES | RTH | B0 | 30min | S-B_q0.80 | 4463 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 832728714 |
| ES | RTH | B0 | 30min | S-C_q0.80 | 4463 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 117370820 |
| ES | RTH | B0 | 30min | S-B_q0.90 | 2232 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 1615113857 |
| ES | RTH | B0 | 30min | S-C_q0.90 | 2232 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 2447780851 |
| ES | RTH | B1 | 1day | S-A | 1401 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR|M3_HARJ | 2734751929 |
| ES | RTH | B1 | 1day | S-B_q0.80 | 280 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 3583050138 |
| ES | RTH | B1 | 1day | S-C_q0.80 | 280 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 3038505791 |
| ES | RTH | B1 | 1day | S-B_q0.90 | 140 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M1_EWMA|M2_HAR|M6_GK|M6_PARK | 518561450 |
| ES | RTH | B1 | 1day | S-C_q0.90 | 140 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_GK|M6_PARK | 410096495 |
| ES | RTH | B1 | 1h | S-A | 10906 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 1045897580 |
| ES | RTH | B1 | 1h | S-B_q0.80 | 2181 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 4120385690 |
| ES | RTH | B1 | 1h | S-C_q0.80 | 2181 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 3717700803 |
| ES | RTH | B1 | 1h | S-B_q0.90 | 1091 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 712479768 |
| ES | RTH | B1 | 1h | S-C_q0.90 | 1091 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 3004156811 |
| ES | RTH | B1 | 30min | S-A | 22312 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 136732739 |
| ES | RTH | B1 | 30min | S-B_q0.80 | 4463 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 1437149941 |
| ES | RTH | B1 | 30min | S-C_q0.80 | 4463 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 2185740070 |
| ES | RTH | B1 | 30min | S-B_q0.90 | 2232 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 810538727 |
| ES | RTH | B1 | 30min | S-C_q0.90 | 2232 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 3199048031 |
| NQ | RTH | B0 | 1day | S-A | 1401 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR|M3_HARJ|M4_HARQ | 598363660 |
| NQ | RTH | B0 | 1day | S-B_q0.80 | 280 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 3132774543 |
| NQ | RTH | B0 | 1day | S-C_q0.80 | 280 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 4162810140 |
| NQ | RTH | B0 | 1day | S-B_q0.90 | 140 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M6_GK|M6_PARK | 1559543155 |
| NQ | RTH | B0 | 1day | S-C_q0.90 | 140 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 2211311582 |
| NQ | RTH | B0 | 1h | S-A | 10906 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 6131605 |
| NQ | RTH | B0 | 1h | S-B_q0.80 | 2181 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M1_EWMA|M2_HAR | 4254605016 |
| NQ | RTH | B0 | 1h | S-C_q0.80 | 2181 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 1872878185 |
| NQ | RTH | B0 | 1h | S-B_q0.90 | 1091 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M1_EWMA|M2_HAR | 3956424179 |
| NQ | RTH | B0 | 1h | S-C_q0.90 | 1091 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 281087360 |
| NQ | RTH | B0 | 30min | S-A | 22312 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 1532726497 |
| NQ | RTH | B0 | 30min | S-B_q0.80 | 4463 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 3416508545 |
| NQ | RTH | B0 | 30min | S-C_q0.80 | 4463 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 3063219730 |
| NQ | RTH | B0 | 30min | S-B_q0.90 | 2232 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 1556410038 |
| NQ | RTH | B0 | 30min | S-C_q0.90 | 2232 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 1954846886 |
| NQ | RTH | B1 | 1day | S-A | 1401 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 1643165716 |
| NQ | RTH | B1 | 1day | S-B_q0.80 | 280 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 3454778690 |
| NQ | RTH | B1 | 1day | S-C_q0.80 | 280 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 2798172795 |
| NQ | RTH | B1 | 1day | S-B_q0.90 | 140 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M6_GK|M6_PARK | 404853592 |
| NQ | RTH | B1 | 1day | S-C_q0.90 | 140 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 2248711278 |
| NQ | RTH | B1 | 1h | S-A | 10906 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 1370928947 |
| NQ | RTH | B1 | 1h | S-B_q0.80 | 2181 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M1_EWMA|M2_HAR | 1034423320 |
| NQ | RTH | B1 | 1h | S-C_q0.80 | 2181 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 3919512435 |
| NQ | RTH | B1 | 1h | S-B_q0.90 | 1091 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 1619288512 |
| NQ | RTH | B1 | 1h | S-C_q0.90 | 1091 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 3071747996 |
| NQ | RTH | B1 | 30min | S-A | 22312 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 997959347 |
| NQ | RTH | B1 | 30min | S-B_q0.80 | 4463 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 2699806576 |
| NQ | RTH | B1 | 30min | S-C_q0.80 | 4463 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 3707498135 |
| NQ | RTH | B1 | 30min | S-B_q0.90 | 2232 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 2399367287 |
| NQ | RTH | B1 | 30min | S-C_q0.90 | 2232 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK|M6_GK | M2_HAR | M2_HAR | 4244299336 |

Composition changed in 155 of 160 (cell, level) comparisons against S05. Entering and leaving models:

| cell | level | s05 | s06r | entered | left |
|---|---|---|---|---|---|
| ES/GLOBEX/B0/1day/S-B_q0.80 | 75 | M4_HARQ|M5_RGARCH | M5_RGARCH | -- | M4_HARQ |
| ES/GLOBEX/B0/1day/S-B_q0.80 | 90 | M4_HARQ|M5_RGARCH | M3_HARJ|M5_RGARCH | M3_HARJ | M4_HARQ |
| ES/GLOBEX/B0/1day/S-C_q0.80 | 75 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH | M2_HAR|M5_RGARCH | -- | M3_HARJ|M4_HARQ |
| ES/GLOBEX/B0/1day/S-C_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH | M2_HAR|M5_RGARCH | -- | M3_HARJ|M4_HARQ |
| ES/GLOBEX/B0/1day/S-B_q0.90 | 75 | M4_HARQ|M5_RGARCH | M5_RGARCH | -- | M4_HARQ |
| ES/GLOBEX/B0/1day/S-B_q0.90 | 90 | M4_HARQ|M5_RGARCH | M5_RGARCH | -- | M4_HARQ |
| ES/GLOBEX/B0/1day/S-C_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH | M2_HAR|M5_RGARCH | -- | M3_HARJ|M4_HARQ |
| ES/GLOBEX/B0/1day/S-C_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_GK|M6_PARK | M2_HAR|M4_HARQ|M5_RGARCH|M6_GK|M6_PARK | -- | M3_HARJ |
| ES/GLOBEX/B1/1day/S-B_q0.80 | 75 | M4_HARQ|M5_RGARCH | M5_RGARCH | -- | M4_HARQ |
| ES/GLOBEX/B1/1day/S-B_q0.80 | 90 | M4_HARQ|M5_RGARCH | M5_RGARCH | -- | M4_HARQ |
| ES/GLOBEX/B1/1day/S-C_q0.80 | 75 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH | M2_HAR|M5_RGARCH | -- | M3_HARJ|M4_HARQ |
| ES/GLOBEX/B1/1day/S-C_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH | M2_HAR|M5_RGARCH | -- | M3_HARJ|M4_HARQ |
| ES/GLOBEX/B1/1day/S-B_q0.90 | 75 | M4_HARQ|M5_RGARCH | M5_RGARCH | -- | M4_HARQ |
| ES/GLOBEX/B1/1day/S-B_q0.90 | 90 | M4_HARQ|M5_RGARCH | M5_RGARCH | -- | M4_HARQ |
| ES/GLOBEX/B1/1day/S-C_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH | M2_HAR|M5_RGARCH | -- | M3_HARJ|M4_HARQ |
| ES/GLOBEX/B1/1day/S-C_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_GK|M6_PARK | M2_HAR|M4_HARQ|M5_RGARCH|M6_GK|M6_PARK | -- | M3_HARJ |
| NQ/GLOBEX/B0/1day/S-A | 75 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ | M3_HARJ | -- |
| NQ/GLOBEX/B0/1day/S-A | 90 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ | M3_HARJ | -- |
| NQ/GLOBEX/B0/1day/S-B_q0.80 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/GLOBEX/B0/1day/S-B_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/GLOBEX/B0/1day/S-C_q0.80 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/GLOBEX/B0/1day/S-C_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/GLOBEX/B0/1day/S-B_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/GLOBEX/B0/1day/S-B_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/GLOBEX/B0/1day/S-C_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/GLOBEX/B0/1day/S-C_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ|M6_PARK | M2_HAR | -- | M3_HARJ|M4_HARQ|M6_PARK |
| NQ/GLOBEX/B1/1day/S-A | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/GLOBEX/B1/1day/S-B_q0.80 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/GLOBEX/B1/1day/S-B_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/GLOBEX/B1/1day/S-C_q0.80 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/GLOBEX/B1/1day/S-C_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/GLOBEX/B1/1day/S-B_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/GLOBEX/B1/1day/S-B_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/GLOBEX/B1/1day/S-C_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/GLOBEX/B1/1day/S-C_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ|M6_GK|M6_PARK | M2_HAR|M6_PARK | -- | M3_HARJ|M4_HARQ|M6_GK |
| ES/RTH/B0/1day/S-A | 75 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ | M3_HARJ | -- |
| ES/RTH/B0/1day/S-A | 90 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ | M3_HARJ | -- |
| ES/RTH/B0/1day/S-B_q0.80 | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B0/1day/S-B_q0.80 | 90 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B0/1day/S-C_q0.80 | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B0/1day/S-C_q0.80 | 90 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B0/1day/S-B_q0.90 | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B0/1day/S-B_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M1_EWMA|M2_HAR|M6_GK|M6_PARK | M1_EWMA|M6_GK|M6_PARK | M3_HARJ|M4_HARQ |
| ES/RTH/B0/1day/S-C_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B0/1day/S-C_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_GK|M6_PARK | M1_EWMA|M6_GK | -- |
| ES/RTH/B0/1h/S-A | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B0/1h/S-A | 90 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B0/1h/S-B_q0.80 | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B0/1h/S-B_q0.80 | 90 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B0/1h/S-C_q0.80 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B0/1h/S-C_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B0/1h/S-B_q0.90 | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B0/1h/S-B_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B0/1h/S-C_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B0/1h/S-C_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B0/30min/S-A | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B0/30min/S-A | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B0/30min/S-B_q0.80 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B0/30min/S-B_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B0/30min/S-C_q0.80 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B0/30min/S-C_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B0/30min/S-B_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B0/30min/S-B_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B0/30min/S-C_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B0/30min/S-C_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/1day/S-A | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B1/1day/S-A | 90 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ | M3_HARJ | M4_HARQ |
| ES/RTH/B1/1day/S-B_q0.80 | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B1/1day/S-B_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/1day/S-C_q0.80 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/1day/S-C_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/1day/S-B_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/1day/S-B_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M1_EWMA|M2_HAR|M6_GK|M6_PARK | M1_EWMA|M6_GK|M6_PARK | M3_HARJ|M4_HARQ |
| ES/RTH/B1/1day/S-C_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/1day/S-C_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_GK|M6_PARK | M1_EWMA|M6_GK | -- |
| ES/RTH/B1/1h/S-A | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B1/1h/S-A | 90 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B1/1h/S-B_q0.80 | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B1/1h/S-B_q0.80 | 90 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B1/1h/S-C_q0.80 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/1h/S-C_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/1h/S-B_q0.90 | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B1/1h/S-B_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/1h/S-C_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/1h/S-C_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/30min/S-A | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/30min/S-A | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/30min/S-B_q0.80 | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B1/30min/S-B_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/30min/S-C_q0.80 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/30min/S-C_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/30min/S-B_q0.90 | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| ES/RTH/B1/30min/S-B_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/30min/S-C_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| ES/RTH/B1/30min/S-C_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B0/1day/S-A | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| NQ/RTH/B0/1day/S-A | 90 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ | M3_HARJ | -- |
| NQ/RTH/B0/1day/S-B_q0.80 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B0/1day/S-B_q0.80 | 90 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M1_EWMA|M3_HARJ|M4_HARQ |
| NQ/RTH/B0/1day/S-C_q0.80 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B0/1day/S-C_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B0/1day/S-B_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B0/1day/S-B_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M6_GK|M6_PARK | M1_EWMA|M6_GK|M6_PARK | -- |
| NQ/RTH/B0/1day/S-C_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B0/1day/S-C_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ|M6_PARK | M2_HAR | -- | M3_HARJ|M4_HARQ|M6_PARK |
| NQ/RTH/B0/1h/S-A | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| NQ/RTH/B0/1h/S-A | 90 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| NQ/RTH/B0/1h/S-B_q0.80 | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| NQ/RTH/B0/1h/S-B_q0.80 | 90 | M1_EWMA|M2_HAR|M4_HARQ | M1_EWMA|M2_HAR | -- | M4_HARQ |
| NQ/RTH/B0/1h/S-C_q0.80 | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| NQ/RTH/B0/1h/S-C_q0.80 | 90 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| NQ/RTH/B0/1h/S-B_q0.90 | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| NQ/RTH/B0/1h/S-B_q0.90 | 90 | M2_HAR|M4_HARQ | M1_EWMA|M2_HAR | M1_EWMA | M4_HARQ |
| NQ/RTH/B0/1h/S-C_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B0/1h/S-C_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B0/30min/S-A | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B0/30min/S-A | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B0/30min/S-B_q0.80 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B0/30min/S-B_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B0/30min/S-C_q0.80 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B0/30min/S-C_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B0/30min/S-B_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B0/30min/S-B_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B0/30min/S-C_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B0/30min/S-C_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B1/1day/S-A | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B1/1day/S-A | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B1/1day/S-B_q0.80 | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| NQ/RTH/B1/1day/S-B_q0.80 | 90 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M1_EWMA|M3_HARJ|M4_HARQ |
| NQ/RTH/B1/1day/S-C_q0.80 | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| NQ/RTH/B1/1day/S-C_q0.80 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B1/1day/S-B_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B1/1day/S-B_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ|M6_GK|M6_PARK | M1_EWMA|M6_GK|M6_PARK | -- |
| NQ/RTH/B1/1day/S-C_q0.90 | 75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR | -- | M3_HARJ|M4_HARQ |
| NQ/RTH/B1/1day/S-C_q0.90 | 90 | M2_HAR|M3_HARJ|M4_HARQ|M6_PARK | M2_HAR | -- | M3_HARJ|M4_HARQ|M6_PARK |
| NQ/RTH/B1/1h/S-A | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| NQ/RTH/B1/1h/S-A | 90 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| NQ/RTH/B1/1h/S-B_q0.80 | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |
| NQ/RTH/B1/1h/S-B_q0.80 | 90 | M2_HAR|M4_HARQ | M1_EWMA|M2_HAR | M1_EWMA | M4_HARQ |
| NQ/RTH/B1/1h/S-C_q0.80 | 75 | M2_HAR|M4_HARQ | M2_HAR | -- | M4_HARQ |

Every cell uses an independently seeded generator derived deterministically from master seed 20260819 as `PCG64(SeedSequence([20260819, cell_index, scheme_index]))`, replacing S05's single stream shared across cells in execution order.

### Metrics

IC, corrected IC under BOTH E2 and E4 side by side, R-squared and its corrections, IC-IR with its block count and block length in WINDOWS, hit rate and QLIKE. S-A rows shown; every scheme in `phase7_metrics.csv`:

| root | geom | btag | horizon | model | lam_E2 | lam_E4 | ic_pearson_log | ic_corrected_E2 | ic_corrected_E4 | r2_oos | r2_corrected_E2 | r2_corrected_E4 | ic_ir | ic_ir_n_blocks | ic_ir_block_len_windows | hit_rate | qlike_mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | 1day | M1_EWMA | 0.84553 | 0.99802 | 0.70681 | 0.76866 | 0.70751 | 0.45449 | 0.53753 | 0.4554 | 1.2399 | 23 | 63 | 0.51722 | 0.29206 |
| ES | GLOBEX | B0 | 1day | M2_HAR | 0.84553 | 0.99802 | 0.83825 | 0.91161 | 0.83909 | 0.68132 | 0.80579 | 0.68268 | 4.1147 | 23 | 63 | 0.39945 | 0.16274 |
| ES | GLOBEX | B0 | 1day | M3_HARJ | 0.84553 | 0.99802 | 0.7532 | 0.81912 | 0.75395 | 0.55547 | 0.65695 | 0.55657 | 3.6144 | 23 | 63 | 0.41391 | 0.55503 |
| ES | GLOBEX | B0 | 1day | M4_HARQ | 0.84553 | 0.99802 | 0.74786 | 0.81331 | 0.7486 | 0.54922 | 0.64956 | 0.55031 | 3.5071 | 23 | 63 | 0.40083 | 0.57742 |
| ES | GLOBEX | B0 | 1day | M5_RGARCH | 0.84553 | 0.99802 | 0.83234 | 0.90518 | 0.83317 | 0.65484 | 0.77447 | 0.65614 | 3.7679 | 23 | 63 | 0.40427 | 0.16539 |
| ES | GLOBEX | B0 | 1day | M6_PARK | 0.84553 | 0.99802 | 0.76204 | 0.82873 | 0.7628 | 0.31983 | 0.37826 | 0.32047 | 3.26 | 23 | 63 | 0.50758 | 0.54641 |
| ES | GLOBEX | B0 | 1day | M6_GK | 0.84553 | 0.99802 | 0.77232 | 0.83991 | 0.77309 | 0.39306 | 0.46487 | 0.39384 | 3.5098 | 23 | 63 | 0.49242 | 0.46874 |
| ES | GLOBEX | B1 | 1day | M1_EWMA | 0.84445 | 0.99803 | 0.70664 | 0.76897 | 0.70733 | 0.451 | 0.53407 | 0.45189 | 1.2232 | 23 | 63 | 0.5241 | 0.29183 |
| ES | GLOBEX | B1 | 1day | M2_HAR | 0.84445 | 0.99803 | 0.83876 | 0.91275 | 0.83959 | 0.68187 | 0.80747 | 0.68322 | 4.1364 | 23 | 63 | 0.40152 | 0.163 |
| ES | GLOBEX | B1 | 1day | M3_HARJ | 0.84445 | 0.99803 | 0.74049 | 0.8058 | 0.74122 | 0.53626 | 0.63504 | 0.53732 | 3.388 | 23 | 63 | 0.41391 | 0.57292 |
| ES | GLOBEX | B1 | 1day | M4_HARQ | 0.84445 | 0.99803 | 0.74167 | 0.80709 | 0.7424 | 0.5319 | 0.62988 | 0.53295 | 3.482 | 23 | 63 | 0.40289 | 0.5853 |
| ES | GLOBEX | B1 | 1day | M5_RGARCH | 0.84445 | 0.99803 | 0.83893 | 0.91293 | 0.83975 | 0.67172 | 0.79545 | 0.67305 | 3.7935 | 23 | 63 | 0.41047 | 0.15661 |
| ES | GLOBEX | B1 | 1day | M6_PARK | 0.84445 | 0.99803 | 0.76292 | 0.83021 | 0.76367 | 0.33489 | 0.39658 | 0.33555 | 3.2771 | 23 | 63 | 0.51171 | 0.52701 |
| ES | GLOBEX | B1 | 1day | M6_GK | 0.84445 | 0.99803 | 0.77319 | 0.84139 | 0.77395 | 0.40623 | 0.48106 | 0.40703 | 3.5254 | 23 | 63 | 0.49105 | 0.45144 |
| NQ | GLOBEX | B0 | 1day | M1_EWMA | 0.87633 | 0.99797 | 0.68591 | 0.73271 | 0.68661 | 0.39974 | 0.45615 | 0.40055 | 1.1443 | 22 | 63 | 0.5349 | 0.26424 |
| NQ | GLOBEX | B0 | 1day | M2_HAR | 0.87633 | 0.99797 | 0.82258 | 0.8787 | 0.82341 | 0.66246 | 0.75595 | 0.66381 | 2.86 | 22 | 63 | 0.40567 | 0.15485 |
| NQ | GLOBEX | B0 | 1day | M3_HARJ | 0.87633 | 0.99797 | 0.74483 | 0.79565 | 0.74559 | 0.54805 | 0.62539 | 0.54916 | 2.2164 | 22 | 63 | 0.40636 | 0.43425 |
| NQ | GLOBEX | B0 | 1day | M4_HARQ | 0.87633 | 0.99797 | 0.74918 | 0.8003 | 0.74994 | 0.5557 | 0.63412 | 0.55684 | 2.2623 | 22 | 63 | 0.40152 | 0.43831 |
| NQ | GLOBEX | B0 | 1day | M5_RGARCH | 0.87633 | 0.99797 | 0.80435 | 0.85923 | 0.80517 | 0.43109 | 0.49192 | 0.43197 | 2.701 | 22 | 63 | 0.39668 | 0.40414 |
| NQ | GLOBEX | B0 | 1day | M6_PARK | 0.87633 | 0.99797 | 0.73456 | 0.78468 | 0.73531 | 0.33305 | 0.38005 | 0.33373 | 2.3352 | 22 | 63 | 0.54112 | 0.48669 |
| NQ | GLOBEX | B0 | 1day | M6_GK | 0.87633 | 0.99797 | 0.74349 | 0.79422 | 0.74424 | 0.39092 | 0.44609 | 0.39172 | 2.5255 | 22 | 63 | 0.50449 | 0.4294 |
| NQ | GLOBEX | B1 | 1day | M1_EWMA | 0.87455 | 0.99799 | 0.68736 | 0.73501 | 0.68806 | 0.38871 | 0.44446 | 0.38949 | 1.1338 | 22 | 63 | 0.55149 | 0.26724 |
| NQ | GLOBEX | B1 | 1day | M2_HAR | 0.87455 | 0.99799 | 0.82376 | 0.88086 | 0.82459 | 0.66387 | 0.7591 | 0.66521 | 2.847 | 22 | 63 | 0.40912 | 0.15453 |
| NQ | GLOBEX | B1 | 1day | M3_HARJ | 0.87455 | 0.99799 | 0.72352 | 0.77367 | 0.72425 | 0.5179 | 0.59219 | 0.51894 | 1.9515 | 22 | 63 | 0.41949 | 0.46186 |
| NQ | GLOBEX | B1 | 1day | M4_HARQ | 0.87455 | 0.99799 | 0.73729 | 0.78839 | 0.73803 | 0.53478 | 0.61149 | 0.53586 | 2.1809 | 22 | 63 | 0.41327 | 0.46266 |
| NQ | GLOBEX | B1 | 1day | M5_RGARCH | 0.87455 | 0.99799 | 0.80321 | 0.85889 | 0.80402 | 0.42769 | 0.48904 | 0.42855 | 2.704 | 22 | 63 | 0.40221 | 0.41086 |
| NQ | GLOBEX | B1 | 1day | M6_PARK | 0.87455 | 0.99799 | 0.73591 | 0.78692 | 0.73665 | 0.34643 | 0.39612 | 0.34713 | 2.3449 | 22 | 63 | 0.54112 | 0.46643 |
| NQ | GLOBEX | B1 | 1day | M6_GK | 0.87455 | 0.99799 | 0.7449 | 0.79654 | 0.74566 | 0.40296 | 0.46076 | 0.40377 | 2.5379 | 22 | 63 | 0.50587 | 0.41065 |
| ES | RTH | B0 | 1day | M1_EWMA | 0.91165 | 0.99485 | 0.72016 | 0.75425 | 0.72202 | 0.43895 | 0.48149 | 0.44123 | 2.2922 | 22 | 63 | 0.50214 | 0.29969 |
| ES | RTH | B0 | 1day | M2_HAR | 0.91165 | 0.99485 | 0.83407 | 0.87355 | 0.83622 | 0.67719 | 0.74282 | 0.68069 | 3.4958 | 22 | 63 | 0.35786 | 0.17149 |
| ES | RTH | B0 | 1day | M3_HARJ | 0.91165 | 0.99485 | 0.71446 | 0.74828 | 0.71631 | 0.50293 | 0.55167 | 0.50553 | 3.1201 | 22 | 63 | 0.38357 | 0.6257 |
| ES | RTH | B0 | 1day | M4_HARQ | 0.91165 | 0.99485 | 0.71593 | 0.74982 | 0.71778 | 0.50247 | 0.55117 | 0.50507 | 2.8203 | 22 | 63 | 0.35929 | 0.64347 |
| ES | RTH | B0 | 1day | M5_RGARCH | 0.91165 | 0.99485 | 0.83143 | 0.87079 | 0.83358 | 0.6665 | 0.7311 | 0.66995 | 3.6708 | 22 | 63 | 0.345 | 0.23791 |
| ES | RTH | B0 | 1day | M6_PARK | 0.91165 | 0.99485 | 0.77324 | 0.80984 | 0.77524 | 0.39516 | 0.43346 | 0.39721 | 3.2815 | 22 | 63 | 0.47571 | 0.46425 |
| ES | RTH | B0 | 1day | M6_GK | 0.91165 | 0.99485 | 0.77692 | 0.8137 | 0.77893 | 0.44225 | 0.48512 | 0.44455 | 3.2224 | 22 | 63 | 0.44571 | 0.41936 |
| ES | RTH | B0 | 1h | M1_EWMA | 0.93089 | 0.97636 | 0.77026 | 0.79835 | 0.77953 | 0.56639 | 0.60844 | 0.5801 | 1.2888 | 173 | 63 | 0.48088 | 0.34592 |
| ES | RTH | B0 | 1h | M2_HAR | 0.93089 | 0.97636 | 0.83234 | 0.86268 | 0.84235 | 0.64541 | 0.69333 | 0.66103 | 3.3697 | 173 | 63 | 0.46868 | 0.25171 |
| ES | RTH | B0 | 1h | M3_HARJ | 0.93089 | 0.97636 | 0.75209 | 0.77951 | 0.76114 | 0.51529 | 0.55355 | 0.52777 | 1.9097 | 173 | 63 | 0.46126 | 0.38067 |
| ES | RTH | B0 | 1h | M4_HARQ | 0.93089 | 0.97636 | 0.70743 | 0.73322 | 0.71594 | 0.44369 | 0.47663 | 0.45443 | 1.5338 | 173 | 63 | 0.46135 | 0.41076 |
| ES | RTH | B0 | 1h | M5_RGARCH | 0.93089 | 0.97636 | 0.80488 | 0.83422 | 0.81456 | 0.42345 | 0.45489 | 0.4337 | 3.3442 | 173 | 63 | 0.45988 | 0.79029 |
| ES | RTH | B0 | 1h | M6_PARK | 0.93089 | 0.97636 | 0.77764 | 0.80599 | 0.787 | 0.40042 | 0.43015 | 0.41011 | 3.1493 | 173 | 63 | 0.48565 | 0.77426 |
| ES | RTH | B0 | 1h | M6_GK | 0.93089 | 0.97636 | 0.7853 | 0.81393 | 0.79474 | 0.45621 | 0.49008 | 0.46725 | 3.2624 | 173 | 63 | 0.48592 | 0.68471 |
| ES | RTH | B0 | 30min | M1_EWMA | 0.79177 | 0.99898 | 0.78445 | 0.88158 | 0.78485 | 0.59132 | 0.74683 | 0.59192 | 1.254 | 354 | 63 | 0.47049 | 0.35388 |
| ES | RTH | B0 | 30min | M2_HAR | 0.79177 | 0.99898 | 0.85331 | 0.95898 | 0.85375 | 0.67932 | 0.85798 | 0.68001 | 4.2079 | 354 | 63 | 0.41527 | 0.23279 |
| ES | RTH | B0 | 30min | M3_HARJ | 0.79177 | 0.99898 | 0.39063 | 0.439 | 0.39083 | -0.21467 | -0.27112 | -0.21489 | 0.66242 | 354 | 63 | 0.3864 | 0.53643 |
| ES | RTH | B0 | 30min | M4_HARQ | 0.79177 | 0.99898 | 0.33594 | 0.37754 | 0.33612 | -0.35195 | -0.44451 | -0.35231 | 0.53078 | 354 | 63 | 0.38465 | 0.57835 |
| ES | RTH | B0 | 30min | M5_RGARCH | 0.79177 | 0.99898 | 0.83022 | 0.93302 | 0.83064 | 0.40439 | 0.51074 | 0.4048 | 4.5299 | 354 | 63 | 0.41231 | 0.87357 |
| ES | RTH | B0 | 30min | M6_PARK | 0.79177 | 0.99898 | 0.81181 | 0.91234 | 0.81222 | 0.50481 | 0.63757 | 0.50533 | 3.7952 | 354 | 63 | 0.45112 | 0.62533 |
| ES | RTH | B0 | 30min | M6_GK | 0.79177 | 0.99898 | 0.8184 | 0.91974 | 0.81882 | 0.55142 | 0.69645 | 0.55199 | 3.9425 | 354 | 63 | 0.4595 | 0.56153 |
| ES | RTH | B1 | 1day | M1_EWMA | 0.91275 | 0.99486 | 0.71913 | 0.75272 | 0.72099 | 0.45232 | 0.49556 | 0.45466 | 2.2875 | 22 | 63 | 0.50357 | 0.30671 |
| ES | RTH | B1 | 1day | M2_HAR | 0.91275 | 0.99486 | 0.83354 | 0.87248 | 0.83569 | 0.67614 | 0.74078 | 0.67963 | 3.4942 | 22 | 63 | 0.34929 | 0.174 |
| ES | RTH | B1 | 1day | M3_HARJ | 0.91275 | 0.99486 | 0.71608 | 0.74953 | 0.71793 | 0.50497 | 0.55324 | 0.50758 | 3.1707 | 22 | 63 | 0.385 | 0.6234 |
| ES | RTH | B1 | 1day | M4_HARQ | 0.91275 | 0.99486 | 0.716 | 0.74944 | 0.71785 | 0.50261 | 0.55066 | 0.50521 | 2.8046 | 22 | 63 | 0.35143 | 0.64475 |
| ES | RTH | B1 | 1day | M5_RGARCH | 0.91275 | 0.99486 | 0.82976 | 0.86852 | 0.8319 | 0.64721 | 0.70908 | 0.65055 | 3.6704 | 22 | 63 | 0.345 | 0.26406 |
| ES | RTH | B1 | 1day | M6_PARK | 0.91275 | 0.99486 | 0.77304 | 0.80914 | 0.77503 | 0.40606 | 0.44487 | 0.40815 | 3.2827 | 22 | 63 | 0.47214 | 0.45332 |
| ES | RTH | B1 | 1day | M6_GK | 0.91275 | 0.99486 | 0.77652 | 0.81279 | 0.77852 | 0.45112 | 0.49424 | 0.45345 | 3.223 | 22 | 63 | 0.44214 | 0.41029 |
| ES | RTH | B1 | 1h | M1_EWMA | 0.93163 | 0.9762 | 0.77271 | 0.80056 | 0.78207 | 0.57127 | 0.61319 | 0.58519 | 1.3244 | 173 | 63 | 0.48226 | 0.34329 |
| ES | RTH | B1 | 1h | M2_HAR | 0.93163 | 0.9762 | 0.83543 | 0.86554 | 0.84555 | 0.65182 | 0.69966 | 0.66771 | 3.4255 | 173 | 63 | 0.46951 | 0.24637 |
| ES | RTH | B1 | 1h | M3_HARJ | 0.93163 | 0.9762 | 0.75253 | 0.77965 | 0.76164 | 0.51577 | 0.55362 | 0.52834 | 1.8902 | 173 | 63 | 0.46126 | 0.37608 |
| ES | RTH | B1 | 1h | M4_HARQ | 0.93163 | 0.9762 | 0.70463 | 0.73003 | 0.71317 | 0.43904 | 0.47126 | 0.44974 | 1.5095 | 173 | 63 | 0.46245 | 0.40957 |
| ES | RTH | B1 | 1h | M5_RGARCH | 0.93163 | 0.9762 | 0.82108 | 0.85068 | 0.83103 | 0.53316 | 0.57228 | 0.54615 | 3.4139 | 173 | 63 | 0.45961 | 0.61271 |
| ES | RTH | B1 | 1h | M6_PARK | 0.93163 | 0.9762 | 0.78013 | 0.80825 | 0.78958 | 0.40605 | 0.43585 | 0.41595 | 3.1935 | 173 | 63 | 0.48767 | 0.75619 |
| ES | RTH | B1 | 1h | M6_GK | 0.93163 | 0.9762 | 0.78783 | 0.81623 | 0.79737 | 0.46168 | 0.49556 | 0.47293 | 3.3063 | 173 | 63 | 0.48776 | 0.66795 |
| ES | RTH | B1 | 30min | M1_EWMA | 0.79117 | 0.99898 | 0.78736 | 0.88519 | 0.78776 | 0.59717 | 0.75479 | 0.59778 | 1.2839 | 354 | 63 | 0.47026 | 0.34797 |
| ES | RTH | B1 | 30min | M2_HAR | 0.79117 | 0.99898 | 0.85567 | 0.96199 | 0.85611 | 0.68448 | 0.86514 | 0.68518 | 4.2205 | 354 | 63 | 0.41522 | 0.22729 |
| ES | RTH | B1 | 30min | M3_HARJ | 0.79117 | 0.99898 | 0.38574 | 0.43366 | 0.38593 | -0.22743 | -0.28746 | -0.22766 | 0.65724 | 354 | 63 | 0.38618 | 0.53628 |
| ES | RTH | B1 | 30min | M4_HARQ | 0.79117 | 0.99898 | 0.32602 | 0.36653 | 0.32619 | -0.37792 | -0.47767 | -0.3783 | 0.51265 | 354 | 63 | 0.38295 | 0.58307 |
| ES | RTH | B1 | 30min | M5_RGARCH | 0.79117 | 0.99898 | 0.84635 | 0.95151 | 0.84678 | 0.51695 | 0.65339 | 0.51748 | 4.5571 | 354 | 63 | 0.41195 | 0.66574 |
| ES | RTH | B1 | 30min | M6_PARK | 0.79117 | 0.99898 | 0.81405 | 0.9152 | 0.81447 | 0.5096 | 0.64411 | 0.51012 | 3.8323 | 354 | 63 | 0.45278 | 0.60881 |
| ES | RTH | B1 | 30min | M6_GK | 0.79117 | 0.99898 | 0.82063 | 0.92259 | 0.82105 | 0.55595 | 0.70269 | 0.55652 | 3.9744 | 354 | 63 | 0.46103 | 0.54652 |
| NQ | RTH | B0 | 1day | M1_EWMA | 0.93444 | 0.99462 | 0.7016 | 0.72579 | 0.70349 | 0.38242 | 0.40925 | 0.38448 | 1.6863 | 22 | 63 | 0.52786 | 0.27147 |
| NQ | RTH | B0 | 1day | M2_HAR | 0.93444 | 0.99462 | 0.82913 | 0.85773 | 0.83137 | 0.67572 | 0.72313 | 0.67938 | 2.9596 | 22 | 63 | 0.37357 | 0.15208 |
| NQ | RTH | B0 | 1day | M3_HARJ | 0.93444 | 0.99462 | 0.72831 | 0.75342 | 0.73027 | 0.52681 | 0.56377 | 0.52966 | 2.9272 | 22 | 63 | 0.40071 | 0.44298 |
| NQ | RTH | B0 | 1day | M4_HARQ | 0.93444 | 0.99462 | 0.72912 | 0.75426 | 0.73109 | 0.52677 | 0.56373 | 0.52962 | 2.6445 | 22 | 63 | 0.37714 | 0.45217 |
| NQ | RTH | B0 | 1day | M5_RGARCH | 0.93444 | 0.99462 | 0.81432 | 0.8424 | 0.81651 | 0.14151 | 0.15144 | 0.14228 | 3.0981 | 22 | 63 | 0.36286 | 0.66186 |
| NQ | RTH | B0 | 1day | M6_PARK | 0.93444 | 0.99462 | 0.75763 | 0.78376 | 0.75967 | 0.40797 | 0.43659 | 0.41017 | 3.1418 | 22 | 63 | 0.50643 | 0.35483 |
| NQ | RTH | B0 | 1day | M6_GK | 0.93444 | 0.99462 | 0.76182 | 0.7881 | 0.76388 | 0.45476 | 0.48667 | 0.45722 | 3.0681 | 22 | 63 | 0.47 | 0.32118 |
| NQ | RTH | B0 | 1h | M1_EWMA | 0.93572 | 0.97818 | 0.74088 | 0.7659 | 0.74909 | 0.4931 | 0.52698 | 0.5041 | 1.0775 | 173 | 63 | 0.4774 | 0.37932 |
| NQ | RTH | B0 | 1h | M2_HAR | 0.93572 | 0.97818 | 0.8052 | 0.83239 | 0.81413 | 0.59661 | 0.63759 | 0.60992 | 3.2382 | 173 | 63 | 0.47299 | 0.32013 |
| NQ | RTH | B0 | 1h | M3_HARJ | 0.93572 | 0.97818 | 0.78189 | 0.8083 | 0.79057 | 0.56443 | 0.6032 | 0.57701 | 2.4192 | 173 | 63 | 0.47162 | 0.37961 |

## Phase 8, primary result and multiplicity

**S-B against S-C composition differs in 16 of 64 comparisons that could be computed, against a pre-registered family of 96** (0 further comparisons are HALTED by the loss invariant). The family size is stated explicitly against the effective sample and **no familywise correction is applied**; its absence is disclosed as a limitation, since correcting a count already seen would be worse than disclosing it (item 47).

### Single pre-specified cell

Chosen on the ex-ante criterion of largest effective sample and logged before the comparison was computed: **ES/RTH/B0/30min** (n_eval 22312).

| cell | quantile | level | differs | s_b | s_c | status |
|---|---|---|---|---|---|---|
| ES/RTH/B0/30min | 0.8 | mcs75 | False | M2_HAR | M2_HAR | ok |
| ES/RTH/B0/30min | 0.8 | mcs90 | False | M2_HAR | M2_HAR | ok |
| ES/RTH/B0/30min | 0.9 | mcs75 | False | M2_HAR | M2_HAR | ok |
| ES/RTH/B0/30min | 0.9 | mcs90 | False | M2_HAR | M2_HAR | ok |

### The three S05A seed-indeterminate cells

| cell | quantile | level | differs | status |
|---|---|---|---|---|
| NQ/GLOBEX/B1/1day | 0.8 | mcs75 | False | ok |
| NQ/GLOBEX/B1/1day | 0.8 | mcs90 | False | ok |
| NQ/GLOBEX/B1/1day | 0.9 | mcs75 | False | ok |
| NQ/GLOBEX/B1/1day | 0.9 | mcs90 | True | ok |
| ES/RTH/B0/1day | 0.8 | mcs75 | False | ok |
| ES/RTH/B0/1day | 0.8 | mcs90 | False | ok |
| ES/RTH/B0/1day | 0.9 | mcs75 | False | ok |
| ES/RTH/B0/1day | 0.9 | mcs90 | True | ok |
| NQ/RTH/B0/1day | 0.8 | mcs75 | False | ok |
| NQ/RTH/B0/1day | 0.8 | mcs90 | False | ok |
| NQ/RTH/B0/1day | 0.9 | mcs75 | False | ok |
| NQ/RTH/B0/1day | 0.9 | mcs90 | True | ok |

## Phase 9, spec reconstruction and persistence

`specs/SPEC-obs-space-vol-eval.md` reconstructed from `DECISIONS.md`, covering the model set, the estimator pair, the exclusion rules, the filter, the holdout boundary, the family size and the three kill conditions with their null abstracts, each marked with the date fixed and whether pre-registered or post hoc.

| report_element | regenerable | missing |
|---|---|---|
| Phase 1 invariant detection | True | -- |
| Phase 2 close-grid check | True | -- |
| Phase 2 high==low | True | -- |
| Phase 2 M6 old vs new | True | -- |
| Phase 2 E3 gate | True | -- |
| Phase 2 OHLC panels + present mask | True | -- |
| Phase 3 calendar | True | -- |
| Phase 4 RGARCH params | True | -- |
| Phase 5 filter | True | -- |
| Phase 6 lambda surface | True | -- |
| Phase 7 forecasts + loss matrices | True | -- |
| Phase 7 MCS + metrics | True | -- |
| Phase 8 primary result | True | -- |

13 of 13 report elements regenerate from persisted artifacts without re-running Phases 2-8; cache 66.4 MB.

## What survives, what changes, what is withdrawn

### Survives unchanged

- The proxy-error scaling anomaly. Var(log RV_M) = c + A M^b refits with b shifted by at most 1.6e-04 after the OHLC rebuild, the calendar exclusion and effective M. Kill condition K3 stands exactly where S05B and S05E left it.
- The S05D determination that the Globex panel is correct: the rebuilt close grid is byte-identical to the stored one in all four cells.
- E3 remains excluded at the 0.20 error-correlation gate; correcting the range estimators did not rescue it.
- The holdout boundary, untouched.

### Changes

- The range estimators. M6_PARK and M6_GK were not range estimators at all; rebuilt from true high and low they rise by 6 to 13 percent, and since M6_GK was the sole MCS survivor in most GLOBEX cells, its construction was load-bearing for the composition result.
- MCS composition. 155 of the (cell, level) compositions differ from S05's after the repairs, the filter, the model-set reductions and per-cell seeding.
- The reliability surface. E1 is dropped, E2 and E4 are reported side by side, and lambda now uses effective sub-bar count.
- The evaluation sample. Non-trading windows are excluded on calendar grounds, and the residual zero-variance windows now halt the MCS in the affected cells rather than silently contaminating it.

### Withdrawn

- Every S05 Part E composition computed on a loss matrix containing non-finite entries. S05's MCS returned definite answers there; those answers are withdrawn and the cells are reported HALTED.
- Every S05 metric whose reliability correction was applied from E4 alone with no recorded provenance (S05B item 23). Corrected IC and corrected R-squared are now reported under both estimators or not at all.
- S05's M6_PARK and M6_GK forecasts and every MCS composition that depended on them.
