# Session 7 report, repair completion and SPY exponent replication

Generated 2026-08-19T06:09:51+00:00 (UTC). No prior artifact modified or deleted. Nothing dated on or after 2024-01-01 was read, futures or SPY. The derived SPY parquets were not consumed.

## Phase 1, SPY inventory and span check

Directory `~/Downloads/DataBento Data/SPY 1s Data`, two venue jobs plus a `data/` folder of derived parquets:

| venue | file | bytes | fmt | consumed |
|---|---|---|---|---|
| ARCX.PILLAR | metadata.json | 691 | JSON | True |
| ARCX.PILLAR | manifest.json | 1481 | JSON | True |
| ARCX.PILLAR | condition.json | 259536 | JSON | True |
| ARCX.PILLAR | arcx-pillar-20180501-20260813.ohlcv-1s.dbn.zst | 463107973 | DBN v3 zstd | True |
| XNAS.ITCH | metadata.json | 689 | JSON | True |
| XNAS.ITCH | manifest.json | 1475 | JSON | True |
| XNAS.ITCH | condition.json | 259559 | JSON | True |
| XNAS.ITCH | xnas-itch-20180501-20260813.ohlcv-1s.dbn.zst | 449348270 | DBN v3 zstd | True |
| (derived) | data/arca_daily.parquet | 95723 | parquet/json | False |
| (derived) | data/arca_raw.parquet | 530501830 | parquet/json | False |
| (derived) | data/arca_stats.json | 269 | parquet/json | False |
| (derived) | data/nasdaq_daily.parquet | 95386 | parquet/json | False |
| (derived) | data/nasdaq_raw.parquet | 502870484 | parquet/json | False |
| (derived) | data/nasdaq_stats.json | 269 | parquet/json | False |

- **ARCX.PILLAR**: dataset `ARCX.PILLAR`, schema `ohlcv-1s`, `stype_in=raw_symbol`, symbols ['SPY']; 37,940,683 rows total, 24,381,645 before 2024-01-01; span 2018-05-01T08:00:00.000000000 to 2026-08-13T23:59:41.000000000; **1427 RTH sessions before 2024**; spans 2018-05-01 to 2023-12-31: **True**.
- **XNAS.ITCH**: dataset `XNAS.ITCH`, schema `ohlcv-1s`, `stype_in=raw_symbol`, symbols ['SPY']; 36,068,770 rows total, 23,726,446 before 2024-01-01; span 2018-05-01T08:04:24.000000000 to 2026-08-13T23:59:35.000000000; **1427 RTH sessions before 2024**; spans 2018-05-01 to 2023-12-31: **True**.

Columns: `length, rtype, publisher_id, instrument_id, ts_event, open, high, low, close, volume` (raw DBN v3, zstd). SHA-256 for every file read is in `results/S07-spy-manifest.txt`. **The span check passes for both venues, so the SPY phases proceed.**

Effective sample per SCOPE section 5, after excluding the designated early closes:

| venue | n_sessions | n_early_excluded | n_rows | median_fill | mean_fill |
|---|---|---|---|---|---|
| ARCX | 1415 | 12 | 20514528 | 0.62769 | 0.61957 |
| XNAS | 1415 | 12 | 21487163 | 0.65932 | 0.64894 |

## Phase 2, exclusion and filter repair

### Item 51 sessions

| session | halt time | ground |
|---|---|---|
| 2020-03-09 | 09:30 | circuit-breaker limit halt (exchange log) |
| 2020-03-12 | 09:30 | circuit-breaker limit halt (exchange log) |
| 2020-03-18 | 09:30 | circuit-breaker limit halt (exchange log) |
| 2020-03-23 | 09:30 | circuit-breaker limit halt (exchange log) |
| 2020-03-24 | 09:30 | circuit-breaker limit halt (exchange log) |
| 2019-02-27 | 09:30 | Databento degraded condition, S04 R2 set |
| 2020-07-01 | 09:30 | Databento degraded condition, S04 R2 set |

A blanket halt-to-close rule was written first and discarded on its own audit: it removed 42 to 98 windows per cell that carried non-zero realized variance, and those are among the highest-volatility sessions in the sample. The rule actually applied targets the minutes where the exchange printed NO bar on those sessions - a data-PRESENCE criterion from the exchange's own record, not a realized-variance criterion, so it stays inside item 42:

| root | geom | horizon | n_windows | n_excluded | n_excluded_with_nonzero_rv | n_zero_rv_remaining |
|---|---|---|---|---|---|---|
| ES | GLOBEX | 1h | 42966 | 169 | 0 | 17 |
| ES | GLOBEX | 30min | 87885 | 396 | 1 | 42 |
| NQ | GLOBEX | 1h | 42856 | 154 | 0 | 15 |
| NQ | GLOBEX | 30min | 87660 | 363 | 1 | 36 |
| ES | RTH | 1h | 11406 | 0 | 0 | 0 |
| ES | RTH | 30min | 22812 | 0 | 0 | 0 |
| NQ | RTH | 1h | 11406 | 0 | 0 | 0 |
| NQ | RTH | 30min | 22812 | 0 | 0 | 0 |

**Excluded windows carrying non-zero realized variance: 2 across all cells** (0 in six of eight cells, 1 in each 30min GLOBEX cell). 110 zero-variance windows remain, on sessions with no exchange record of a halt.

### Filter lower bound (item 52) and the rerun of the 8 halted cells

| cell | n_eval | n_excluded | rv_min_positive | n_models | dropped | seconds |
|---|---|---|---|---|---|---|
| NQ/GLOBEX/B0/1h | 22134 | 154 | 8.5398e-07 | 4 | M5_RGARCH|M6_PARK|M6_GK | 32.4 |
| ES/GLOBEX/B1/1h | 1384 | 169 | 7.9431e-07 | 4 | M5_RGARCH|M6_PARK|M6_GK | 47.3 |
| ES/GLOBEX/B1/30min | 79367 | 396 | 2.4747e-07 | 4 | M5_RGARCH|M6_PARK|M6_GK | 62.1 |
| ES/GLOBEX/B0/1h | 40833 | 169 | 7.9431e-07 | 4 | M5_RGARCH|M6_PARK|M6_GK | 93 |
| NQ/GLOBEX/B1/1h | 17982 | 154 | 8.5398e-07 | 4 | M5_RGARCH|M6_PARK|M6_GK | 46.2 |
| ES/GLOBEX/B0/30min | 13019 | 396 | 2.4747e-07 | 5 | M6_PARK|M6_GK | 129.3 |
| NQ/GLOBEX/B1/30min | 83081 | 363 | 1.8073e-07 | 4 | M5_RGARCH|M6_PARK|M6_GK | 103.2 |
| NQ/GLOBEX/B0/30min | 80551 | 363 | 1.8073e-07 | 5 | M6_PARK|M6_GK | 152.2 |

With the lower bound set to the smallest strictly positive in-sample realized variance, **no cell halts on M3_HARJ or M4_HARQ any more**. What remained were M5_RGARCH (6 cells) and M6_PARK (2 cells), neither of which is filtered. Item 41's prescribed remedy for a model that cannot produce admissible forecasts is to mark it unavailable and reduce the model set with the reduction stated; that rule is written for RGARCH and is applied here to M6_PARK by the same logic, disclosed as a post-hoc extension. No value was replaced and no model respecified.

### Filter impact across ALL cells

| cell | source | model | n_eval | n_replaced | share_replaced | mean_qlike | share_qlike_from_replaced | share_qlike_worst5 | flag_replaced_over_quarter |
|---|---|---|---|---|---|---|---|---|---|
| ES/GLOBEX/B0/1day | S06R | M3_HARJ | 1453 | 14 | 0.0096352 | 0.55503 | 0.70946 | 0.45342 | True |
| ES/GLOBEX/B0/1day | S06R | M4_HARQ | 1453 | 14 | 0.0096352 | 0.57742 | 0.6994 | 0.43584 | True |
| ES/GLOBEX/B0/1h | S07 | M3_HARJ | 40833 | 3303 | 0.08089 | -- | -- | 0.018255 | True |
| ES/GLOBEX/B0/1h | S07 | M4_HARQ | 40833 | 5394 | 0.1321 | -- | -- | 0.017903 | True |
| ES/GLOBEX/B1/1day | S06R | M3_HARJ | 1453 | 16 | 0.011012 | 0.57292 | 0.70755 | 0.42565 | True |
| ES/GLOBEX/B1/1day | S06R | M4_HARQ | 1453 | 26 | 0.017894 | 0.5853 | 0.6894 | 0.41665 | True |
| ES/GLOBEX/B1/1h | S07 | M3_HARJ | 1384 | 4 | 0.0028902 | 0.2285 | 0.028473 | 0.10434 | False |
| ES/GLOBEX/B1/1h | S07 | M4_HARQ | 1384 | 37 | 0.026734 | 0.26842 | 0.18031 | 0.1072 | False |
| ES/GLOBEX/B1/30min | S07 | M3_HARJ | 79367 | 642 | 0.008089 | -- | -- | 0.021845 | True |
| ES/GLOBEX/B1/30min | S07 | M4_HARQ | 79367 | 3136 | 0.039513 | -- | -- | 0.02631 | True |
| NQ/GLOBEX/B0/1day | S06R | M3_HARJ | 1448 | 13 | 0.0089779 | 0.43425 | 0.64235 | 0.42511 | True |
| NQ/GLOBEX/B0/1day | S06R | M4_HARQ | 1448 | 13 | 0.0089779 | 0.43831 | 0.61934 | 0.42117 | True |
| NQ/GLOBEX/B0/1h | S07 | M3_HARJ | 22134 | 2574 | 0.11629 | -- | -- | 0.019093 | True |
| NQ/GLOBEX/B0/1h | S07 | M4_HARQ | 22134 | 3195 | 0.14435 | -- | 0.57897 | 0.022977 | True |
| NQ/GLOBEX/B1/1day | S06R | M3_HARJ | 1448 | 18 | 0.012431 | 0.46186 | 0.63466 | 0.38968 | True |
| NQ/GLOBEX/B1/1day | S06R | M4_HARQ | 1448 | 17 | 0.01174 | 0.46266 | 0.61233 | 0.38901 | True |
| NQ/GLOBEX/B1/1h | S07 | M3_HARJ | 17982 | 2529 | 0.14064 | -- | -- | 0.017889 | True |
| NQ/GLOBEX/B1/1h | S07 | M4_HARQ | 17982 | 3016 | 0.16772 | -- | 0.63188 | 0.021248 | True |
| ES/RTH/B0/1day | S06R | M3_HARJ | 1401 | 22 | 0.015703 | 0.6257 | 0.70546 | 0.39826 | True |
| ES/RTH/B0/1day | S06R | M4_HARQ | 1401 | 24 | 0.017131 | 0.64347 | 0.71314 | 0.38726 | True |
| ES/RTH/B0/1h | S06R | M3_HARJ | 10906 | 287 | 0.026316 | 0.38067 | 0.35178 | 0.056324 | True |
| ES/RTH/B0/1h | S06R | M4_HARQ | 10906 | 526 | 0.04823 | 0.41076 | 0.41992 | 0.054079 | True |
| ES/RTH/B0/30min | S06R | M3_HARJ | 22312 | 3639 | 0.1631 | 0.53643 | 0.64773 | 0.01743 | True |
| ES/RTH/B0/30min | S06R | M4_HARQ | 22312 | 4461 | 0.19994 | 0.57835 | 0.7025 | 0.016097 | True |
| ES/RTH/B1/1day | S06R | M3_HARJ | 1401 | 22 | 0.015703 | 0.6234 | 0.70574 | 0.39426 | True |
| ES/RTH/B1/1day | S06R | M4_HARQ | 1401 | 24 | 0.017131 | 0.64475 | 0.70888 | 0.3812 | True |
| ES/RTH/B1/1h | S06R | M3_HARJ | 10906 | 297 | 0.027233 | 0.37608 | 0.35916 | 0.056025 | True |
| ES/RTH/B1/1h | S06R | M4_HARQ | 10906 | 555 | 0.050889 | 0.40957 | 0.43274 | 0.05337 | True |
| ES/RTH/B1/30min | S06R | M3_HARJ | 22312 | 3715 | 0.1665 | 0.53628 | 0.65673 | 0.016913 | True |
| ES/RTH/B1/30min | S06R | M4_HARQ | 22312 | 4615 | 0.20684 | 0.58307 | 0.71499 | 0.015708 | True |
| NQ/RTH/B0/1day | S06R | M3_HARJ | 1401 | 23 | 0.016417 | 0.44298 | 0.6518 | 0.37918 | True |
| NQ/RTH/B0/1day | S06R | M4_HARQ | 1401 | 24 | 0.017131 | 0.45217 | 0.66036 | 0.37148 | True |
| NQ/RTH/B0/1h | S06R | M3_HARJ | 10906 | 86 | 0.0078856 | 0.37961 | 0.15897 | 0.039531 | False |
| NQ/RTH/B0/1h | S06R | M4_HARQ | 10906 | 130 | 0.01192 | 0.39069 | 0.17744 | 0.038415 | False |
| NQ/RTH/B0/30min | S06R | M3_HARJ | 22312 | 1103 | 0.049435 | 0.40194 | 0.33334 | 0.017663 | True |
| NQ/RTH/B0/30min | S06R | M4_HARQ | 22312 | 1565 | 0.070142 | 0.43377 | 0.403 | 0.017544 | True |
| NQ/RTH/B1/1day | S06R | M3_HARJ | 1401 | 25 | 0.017844 | 0.45357 | 0.64938 | 0.36008 | True |
| NQ/RTH/B1/1day | S06R | M4_HARQ | 1401 | 28 | 0.019986 | 0.47731 | 0.67876 | 0.34218 | True |
| NQ/RTH/B1/1h | S06R | M3_HARJ | 10906 | 102 | 0.0093526 | 0.36936 | 0.16764 | 0.038373 | False |
| NQ/RTH/B1/1h | S06R | M4_HARQ | 10906 | 131 | 0.012012 | 0.37866 | 0.17961 | 0.037523 | False |
| NQ/RTH/B1/30min | S06R | M3_HARJ | 22312 | 1240 | 0.055575 | 0.39987 | 0.36702 | 0.01638 | True |
| NQ/RTH/B1/30min | S06R | M4_HARQ | 22312 | 1610 | 0.072158 | 0.42577 | 0.42111 | 0.017542 | True |

**36 of 42 (cell, model) combinations are FLAGGED**: the replaced observations carry more than a quarter of mean QLIKE, and in the 1day cells they carry 61 to 71 percent of it. The flag was written for exactly this condition - a filter that converts an infinite-variance problem into a high-variance one leaves the MCS uninformative - and it fires nearly everywhere.

### The M3_HARJ change at ES/GLOBEX/B0/1day

In-sample bounds: min including zero 6.542e-06, min strictly positive 6.542e-06 (identical here, so item 52 changes nothing in this cell), max 0.00119, mean 5.873e-05.

| model | filtered | forecasts above the in-sample max | forecasts set to the replacement mean | max forecast | mean QLIKE now | mean QLIKE in S05 | IC now | IC in S05 |
|---|---|---|---|---|---|---|---|---|
| M3_HARJ | yes | 0 | 14 | 0.001165 | 0.5550 | 0.1642 | 0.7532 | 0.8317 |
| M4_HARQ | yes | 0 | 14 | 0.001183 | 0.5774 | 1704465726635640266832269781491433390734911383965047032187573334052409441087615184560797480183903023446999806493460080127087678374820531018357677008026686921881534497816838307908013029136950467050856654860092062388106046484226383446812687169799999851070881387763142977004640552246386661907234816.0000 | 0.7479 | -0.0658 |
| M2_HAR | no | 14 | 0 | 0.006321 | 0.1627 | 0.1627 | 0.8383 | 0.8383 |
| M1_EWMA | no | 22 | 0 | 0.001813 | 0.2921 | 0.2921 | 0.7068 | 0.7068 |
| M5_RGARCH | no | 14 | 0 | 0.003665 | 0.1654 | 0.1654 | 0.8323 | 0.8323 |

**The BPQ UPPER bound fired, on 14 forecasts.** M2_HAR, which is not filtered, carries forecasts up to 6.3e-03 against an in-sample maximum of 1.19e-03 and keeps them. M3_HARJ and M4_HARQ produce the same high-volatility forecasts, but the filter replaces each one with the in-sample MEAN of 5.87e-05, roughly twenty times too small on those days. QLIKE moves 0.164 to 0.555 and IC 0.838 to 0.753 for that reason alone, while EWMA, HAR and RGARCH are untouched because the filter never sees them. The filter is not correcting a defect in these cells; it is discarding the correct forecast on the days that matter most.

## Phase 3, RGARCH on the cells where it failed

| cell | n_refits | n_converged | persistence_mean | persistence_max | violates_stationarity | omega_free | beta_last | gamma_last | phi_last | n_nonpositive | n_above_100x | share_pathological | n_pathological_within_D_of_refit | divergence_at_refit_boundary | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ES/GLOBEX/B0/1h | 31 | 31 | 0.74662 | 3.8289 | True | YES (no variance targeting in partde.rgarch_ll) | 9.5882e-120 | 0.00069167 | 986.69 | 1 | 39437 | 0.96584 | 638 | False | RGARCH-UNAVAILABLE (non-stationary parameters) |
| ES/GLOBEX/B0/30min | 31 | 31 | 1.441 | 4.7358 | True | YES (no variance targeting in partde.rgarch_ll) | 5.4192e-28 | -0.00046432 | -1841.9 | 0 | 13007 | 0.99908 | 225 | False | RGARCH-UNAVAILABLE (non-stationary parameters) |
| ES/GLOBEX/B1/1h | 31 | 31 | 1.6753 | 46.227 | True | YES (no variance targeting in partde.rgarch_ll) | 4.7795e-10 | -1.0302 | -0.070833 | 1 | 1383 | 1 | 21 | False | RGARCH-UNAVAILABLE (non-stationary parameters) |
| ES/GLOBEX/B1/30min | 31 | 31 | 0.93156 | 1.0992 | True | YES (no variance targeting in partde.rgarch_ll) | 0.999 | -0.0020739 | -0.59429 | 73120 | 2570 | 0.95367 | 133 | False | RGARCH-UNAVAILABLE (non-stationary parameters) |
| NQ/GLOBEX/B0/1h | 31 | 31 | 2.6969 | 2.8004 | True | YES (no variance targeting in partde.rgarch_ll) | 2.1317e-14 | -0.92325 | -3.0137 | 63 | 22071 | 1 | 353 | False | RGARCH-UNAVAILABLE (non-stationary parameters) |
| NQ/GLOBEX/B0/30min | 31 | 31 | 0.79202 | 0.85733 | False | YES (no variance targeting in partde.rgarch_ll) | 3.0587e-84 | -2.7931e-05 | -30574 | 0 | 80468 | 0.99897 | 1305 | False | RGARCH-UNAVAILABLE (divergent forecasts, stationary parameters) |
| NQ/GLOBEX/B1/1h | 31 | 31 | 2.4356 | 41.728 | True | YES (no variance targeting in partde.rgarch_ll) | 0.052723 | -16.234 | -0.061511 | 2 | 17973 | 0.99961 | 286 | False | RGARCH-UNAVAILABLE (non-stationary parameters) |
| NQ/GLOBEX/B1/30min | 31 | 16 | 6.6952 | 60.763 | True | YES (no variance targeting in partde.rgarch_ll) | 4.6725e-53 | 0.16203 | 33.753 | 83 | 82998 | 1 | 1348 | False | RGARCH-UNAVAILABLE (non-stationary parameters) |

Persistence is beta + gamma*phi. Omega is a free parameter in every cell: `partde.rgarch_ll` contains no variance-targeting term, so nothing pins the unconditional level. RGARCH was not filtered, respecified or constrained.

- RGARCH-UNAVAILABLE (non-stationary parameters): 7 cells
- RGARCH-UNAVAILABLE (divergent forecasts, stationary parameters): 1 cells

## Phase 4, primary result and multiplicity

**S-B against S-C differs in 22 of 72 comparisons computed, against the pre-registered family of 96**; 24 halted at the loss invariant and 0 were not run. Every count in this section carries that denominator. No familywise correction is applied (item 47).

### Stratified breakdown (post hoc, item 54)

| dimension | level | n | n_differ | share |
|---|---|---|---|---|
| horizon | 1day | 32 | 14 | 0.4375 |
| horizon | 1h | 20 | 4 | 0.2 |
| horizon | 30min | 20 | 4 | 0.2 |
| root | ES | 40 | 15 | 0.375 |
| root | NQ | 32 | 7 | 0.21875 |
| geom | GLOBEX | 24 | 15 | 0.625 |
| geom | RTH | 48 | 7 | 0.14583 |
| quantile | 0.8 | 36 | 9 | 0.25 |
| quantile | 0.9 | 36 | 13 | 0.36111 |

### The two pre-specified cells

- **Pre-registered (S06R, largest effective sample): `ES/RTH/B0/30min`** - stands, not replaced.
- **Post hoc (item 54, median effective sample): `ES/RTH/B1/1h`**, n_eval 10906, logged before its comparison was computed.

| cell | quantile | level | differs | status |
|---|---|---|---|---|
| ES/RTH/B0/30min | 0.8 | mcs75 | False | ok |
| ES/RTH/B0/30min | 0.8 | mcs90 | False | ok |
| ES/RTH/B0/30min | 0.9 | mcs75 | False | ok |
| ES/RTH/B0/30min | 0.9 | mcs90 | False | ok |
| ES/RTH/B1/1h | 0.8 | mcs75 | False | ok |
| ES/RTH/B1/1h | 0.8 | mcs90 | False | ok |
| ES/RTH/B1/1h | 0.9 | mcs75 | False | ok |
| ES/RTH/B1/1h | 0.9 | mcs90 | False | ok |

## Phase 5, SPY panels

| venue | year | n_sessions | median_fill | mean_fill | padded_share | off_penny_close_share | corr_fill_vol |
|---|---|---|---|---|---|---|---|
| ARCX | 2018 | 166 | 0.46171 | 0.50693 | 0.49307 | 0.044833 | 0.93944 |
| ARCX | 2019 | 249 | 0.4238 | 0.44324 | 0.55676 | 0.056074 | 0.92769 |
| ARCX | 2020 | 251 | 0.61056 | 0.64028 | 0.35972 | 0.055887 | 0.83192 |
| ARCX | 2021 | 251 | 0.59915 | 0.61649 | 0.38351 | 0.069296 | 0.90047 |
| ARCX | 2022 | 250 | 0.7681 | 0.77197 | 0.22803 | 0.032351 | 0.78224 |
| ARCX | 2023 | 248 | 0.69848 | 0.70052 | 0.29948 | 0.050078 | 0.83737 |
| XNAS | 2018 | 166 | 0.49404 | 0.55505 | 0.44495 | 0.040726 | 0.93709 |
| XNAS | 2019 | 249 | 0.50838 | 0.52916 | 0.47084 | 0.07766 | 0.90707 |
| XNAS | 2020 | 251 | 0.63248 | 0.66096 | 0.33904 | 0.064574 | 0.82372 |
| XNAS | 2021 | 251 | 0.59889 | 0.62001 | 0.37999 | 0.06449 | 0.90605 |
| XNAS | 2022 | 250 | 0.77609 | 0.7817 | 0.2183 | 0.03768 | 0.75655 |
| XNAS | 2023 | 248 | 0.71139 | 0.71535 | 0.28465 | 0.089008 | 0.72765 |

Two panels per venue are persisted: a calendar-time 23,400-second grid with forward fill, and a traded-tick panel holding only seconds with an actual bar. The range-input and effective-M invariants were asserted at construction and passed.

Fill by time of day (half-hour means) is in `phase5_spy_fill_by_tod.csv`; fill by year conditioned on volatility tercile is in `phase5_spy_fill_by_vol.csv`. Those three measurements close SCOPE section 8.3 and are reported regardless of the exponent result:

| venue | year | 1 | 2 | 3 |
|---|---|---|---|---|
| ARCX | 2018 | 0.35989 | 0.46552 | 0.69806 |
| ARCX | 2019 | 0.34146 | 0.42363 | 0.56465 |
| ARCX | 2020 | 0.48093 | 0.61768 | 0.82196 |
| ARCX | 2021 | 0.49357 | 0.60458 | 0.75119 |
| ARCX | 2022 | 0.69344 | 0.77499 | 0.84842 |
| ARCX | 2023 | 0.62276 | 0.69496 | 0.78376 |
| XNAS | 2018 | 0.38046 | 0.5105 | 0.77734 |
| XNAS | 2019 | 0.40085 | 0.51376 | 0.67286 |
| XNAS | 2020 | 0.50241 | 0.63958 | 0.84065 |
| XNAS | 2021 | 0.50027 | 0.60998 | 0.74968 |
| XNAS | 2022 | 0.70603 | 0.77368 | 0.8663 |
| XNAS | 2023 | 0.65541 | 0.71604 | 0.7746 |

## Phase 6, SPY exponent

### ARCX

| M | M_used | stub | n_windows | var_log_rv_CAL | var_log_rv_TICK | var_log_trv3_CAL | trv3_share_removed | mean_eff_M | share_full_M | implied_bias | bias_below_1pct | trigamma |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 5 | False | 1415 | 2.0844 | 1.6842 | 2.9658 | 0.11897 | 5 | 1 | -1.3896e-05 | True | 0.49036 |
| 6 | 6 | False | 1415 | 1.9889 | 1.5988 | 2.4405 | 0.11799 | 6 | 1 | -1.6676e-05 | True | 0.39493 |
| 10 | 10 | False | 1415 | 1.8103 | 1.4451 | 2.1504 | 0.11637 | 10 | 1 | -2.7793e-05 | True | 0.22132 |
| 13 | 13 | False | 1415 | 1.7523 | 1.3676 | 2.0512 | 0.13312 | 13 | 1 | -3.6131e-05 | True | 0.16628 |
| 26 | 26 | False | 1415 | 1.6739 | 1.2599 | 1.8961 | 0.16161 | 26 | 1 | -7.2262e-05 | True | 0.079957 |
| 39 | 39 | False | 1415 | 1.6729 | 1.226 | 1.9144 | 0.19291 | 38.999 | 0.99859 | -0.00010839 | True | 0.052619 |
| 78 | 78 | False | 1415 | 1.6435 | 1.1775 | 1.8958 | 0.2194 | 77.994 | 0.99647 | -0.00021679 | True | 0.025973 |
| 130 | 130 | False | 1415 | 1.6141 | 1.1642 | 1.8557 | 0.24287 | 129.98 | 0.99152 | -0.00036131 | True | 0.015504 |
| 195 | 195 | False | 1415 | 1.6043 | 1.1527 | 1.8396 | 0.25567 | 194.9 | 0.94982 | -0.00054196 | True | 0.010309 |
| 390 | 390 | False | 1415 | 1.5862 | 1.1264 | 1.8475 | 0.27764 | 387.97 | 0.70459 | -0.0010839 | True | 0.0051414 |
| 780 | 780 | False | 1415 | 1.5667 | 1.1122 | 1.8685 | 0.30787 | 760.62 | 0.37739 | -0.0021679 | True | 0.0025674 |
| 1560 | 1560 | False | 1415 | 1.5524 | 1.104 | 1.9328 | 0.34294 | 1441.5 | 0.084099 | -0.0043357 | True | 0.0012829 |
| 2340 | 2340 | False | 1415 | 1.5413 | 1.0973 | 1.9919 | 0.36638 | 2045.7 | 0.021201 | -0.0065036 | True | 0.00085507 |
| 4680 | 4680 | False | 1415 | 1.5304 | 1.0959 | 2.1982 | 0.42748 | 3523.5 | 0.0014134 | -0.013007 | True | 0.00042744 |
| 11700 | 11700 | False | 1415 | 1.5431 | 0.86058 | 3.0651 | 0.54468 | 6338.8 | 0 | -0.032518 | True | 0.00017095 |
| 23400 | 23399 | True | 1415 | 1.5484 | -- | 3.9633 | 0.60146 | 10248 | 0 | -0.065033 | True | 8.5477e-05 |

### XNAS

| M | M_used | stub | n_windows | var_log_rv_CAL | var_log_rv_TICK | var_log_trv3_CAL | trv3_share_removed | mean_eff_M | share_full_M | implied_bias | bias_below_1pct | trigamma |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 5 | False | 1415 | 2.1934 | 1.7306 | 2.6863 | 0.11112 | 5 | 1 | -1.5096e-05 | True | 0.49036 |
| 6 | 6 | False | 1415 | 2.0855 | 1.6077 | 2.486 | 0.11092 | 6 | 1 | -1.8115e-05 | True | 0.39493 |
| 10 | 10 | False | 1415 | 1.837 | 1.4306 | 2.0761 | 0.11932 | 10 | 1 | -3.0191e-05 | True | 0.22132 |
| 13 | 13 | False | 1415 | 1.7523 | 1.3809 | 1.9572 | 0.12572 | 13 | 1 | -3.9248e-05 | True | 0.16628 |
| 26 | 26 | False | 1415 | 1.6528 | 1.2383 | 1.8297 | 0.15945 | 26 | 1 | -7.8497e-05 | True | 0.079957 |
| 39 | 39 | False | 1415 | 1.6458 | 1.2311 | 1.8287 | 0.18646 | 38.999 | 0.99859 | -0.00011775 | True | 0.052619 |
| 78 | 78 | False | 1415 | 1.6133 | 1.1852 | 1.8201 | 0.21299 | 77.994 | 0.99647 | -0.00023549 | True | 0.025973 |
| 130 | 130 | False | 1415 | 1.5632 | 1.162 | 1.7755 | 0.24021 | 129.98 | 0.99152 | -0.00039248 | True | 0.015504 |
| 195 | 195 | False | 1415 | 1.5575 | 1.1486 | 1.7711 | 0.25193 | 194.92 | 0.96749 | -0.00058873 | True | 0.010309 |
| 390 | 390 | False | 1415 | 1.5298 | 1.1289 | 1.7506 | 0.26918 | 388.83 | 0.78799 | -0.0011775 | True | 0.0051414 |
| 780 | 780 | False | 1415 | 1.5046 | 1.1097 | 1.7722 | 0.29914 | 767.08 | 0.43463 | -0.0023549 | True | 0.0025674 |
| 1560 | 1560 | False | 1415 | 1.4882 | 1.1005 | 1.8229 | 0.33217 | 1471 | 0.0947 | -0.0047098 | True | 0.0012829 |
| 2340 | 2340 | False | 1415 | 1.4784 | 1.0957 | 1.8654 | 0.35228 | 2105.8 | 0.030389 | -0.0070647 | True | 0.00085507 |
| 4680 | 4680 | False | 1415 | 1.4652 | 1.0932 | 2.0224 | 0.4081 | 3684.8 | 0.0028269 | -0.014129 | True | 0.00042744 |
| 11700 | 11700 | False | 1415 | 1.4727 | 0.85706 | 2.5858 | 0.51919 | 6762 | 0 | -0.035324 | True | 0.00017095 |
| 23400 | 23399 | True | 1415 | 1.4775 | -- | 329.25 | 0.58003 | 11062 | 0 | -0.070644 | True | 8.5477e-05 |

### Fitted Var(log RV_M) = c + A M^b

| venue | fit | c | A | b | rmse | n | M_min | M_max |
|---|---|---|---|---|---|---|---|---|
| ARCX | CAL_full | 1.5573 | 1.9537 | -0.841 | 0.021401 | 16 | 5 | 23399 |
| ARCX | CAL_primary | 1.5573 | 1.9537 | -0.841 | 0.021401 | 16 | 5 | 23399 |
| ARCX | TICK_full | 1.0343 | 1.4569 | -0.53326 | 0.055765 | 15 | 5 | 23399 |
| ARCX | TICK_primary | 1.0343 | 1.4569 | -0.53326 | 0.055765 | 15 | 5 | 23399 |
| ARCX | CAL_noisecorr_full | 1.5563 | 1.9366 | -0.83489 | 0.021611 | 16 | 5 | 23399 |
| ARCX | TRV3_full | 2.1762 | 18807 | -6.2597 | 0.54426 | 16 | 5 | 23399 |
| ARCX | trigamma_reference | 0.0014712 | 2.9703 | -1.1248 | 0.0018698 | 16 | 5 | 23399 |
| ARCX | trigamma_reference_primary | 0.0014712 | 2.9703 | -1.1248 | 0.0018698 | 16 | 5 | 23399 |
| XNAS | CAL_full | 1.4936 | 2.6205 | -0.83937 | 0.027335 | 16 | 5 | 23399 |
| XNAS | CAL_primary | 1.4936 | 2.6205 | -0.83937 | 0.027335 | 16 | 5 | 23399 |
| XNAS | TICK_full | 1.0439 | 1.6771 | -0.59854 | 0.059002 | 15 | 5 | 23399 |
| XNAS | TICK_primary | 1.0439 | 1.6771 | -0.59854 | 0.059002 | 15 | 5 | 23399 |
| XNAS | CAL_noisecorr_full | 1.4924 | 2.6007 | -0.83409 | 0.027646 | 16 | 5 | 23399 |
| XNAS | TRV3_full | 22.456 | -26.057 | -32.586 | 79.215 | 16 | 5 | 23399 |
| XNAS | trigamma_reference | 0.0014712 | 2.9703 | -1.1248 | 0.0018698 | 16 | 5 | 23399 |
| XNAS | trigamma_reference_primary | 0.0014712 | 2.9703 | -1.1248 | 0.0018698 | 16 | 5 | 23399 |

### Noise by signature plot

| venue | group | omega2 | iv_intercept | nsr |
|---|---|---|---|---|
| ARCX | all | -1.1179e-10 | 8.0448e-05 | -1.3896e-06 |
| ARCX | 2018 | -1.8339e-10 | 5.3021e-05 | -3.4587e-06 |
| ARCX | 2019 | -9.8687e-11 | 2.5296e-05 | -3.9014e-06 |
| ARCX | 2020 | -2.4446e-10 | 0.00019538 | -1.2512e-06 |
| ARCX | 2021 | -8.951e-11 | 3.5136e-05 | -2.5475e-06 |
| ARCX | 2022 | -5.802e-11 | 0.00012231 | -4.7438e-07 |
| ARCX | 2023 | -1.9527e-11 | 4.1518e-05 | -4.7033e-07 |
| XNAS | all | -1.2281e-10 | 8.1353e-05 | -1.5096e-06 |
| XNAS | 2018 | -6.1004e-11 | 5.3584e-05 | -1.1385e-06 |
| XNAS | 2019 | -7.4476e-11 | 2.8318e-05 | -2.6299e-06 |
| XNAS | 2020 | -2.9435e-10 | 0.0001967 | -1.4965e-06 |
| XNAS | 2021 | -8.2043e-11 | 3.4514e-05 | -2.3771e-06 |
| XNAS | 2022 | -1.4751e-10 | 0.0001231 | -1.1984e-06 |
| XNAS | 2023 | -5.5435e-11 | 4.1776e-05 | -1.3269e-06 |

### Per year and per volatility tercile

| venue | stratum | key | c | A | b | rmse |
|---|---|---|---|---|---|---|
| ARCX | vol_tercile | 1 | -141.06 | 141.77 | -5.8009e-05 | 0.025703 |
| ARCX | vol_tercile | 2 | 0.56104 | -1.7493 | -0.977 | 0.030725 |
| ARCX | vol_tercile | 3 | 0.87211 | -0.83488 | -0.66837 | 0.014621 |
| ARCX | year | 2018 | 1.6242 | 1.3601 | -0.45728 | 0.051942 |
| ARCX | year | 2019 | 1.0158 | 2.3795 | -0.76014 | 0.038721 |
| ARCX | year | 2020 | 2.0486 | 37978 | -7.1898 | 0.039367 |
| ARCX | year | 2021 | 0.98604 | 1.3367 | -0.56911 | 0.024568 |
| ARCX | year | 2022 | 0.4918 | 3.5329 | -1.1585 | 0.01427 |
| ARCX | year | 2023 | 0.54899 | 1.9531 | -0.84743 | 0.012815 |
| XNAS | vol_tercile | 1 | -65.739 | 66.464 | -0.00020417 | 0.02926 |
| XNAS | vol_tercile | 2 | 0.55935 | -1.4937 | -0.87009 | 0.031059 |
| XNAS | vol_tercile | 3 | 0.86813 | -1.0367 | -0.79923 | 0.017404 |
| XNAS | year | 2018 | 1.6381 | 1.4444 | -0.40449 | 0.038717 |
| XNAS | year | 2019 | 1.0164 | 4.3669 | -1.0071 | 0.044706 |
| XNAS | year | 2020 | 1.9876 | 1.5633 | -0.72948 | 0.037743 |
| XNAS | year | 2021 | 0.99765 | 1.5714 | -0.67662 | 0.035195 |
| XNAS | year | 2022 | 0.50973 | 5.1342 | -1.2951 | 0.029577 |
| XNAS | year | 2023 | 0.51328 | 2.4881 | -0.85612 | 0.017799 |

## Phase 7, determination

| instrument | cell | convention | b | trigamma_ref | gap |
|---|---|---|---|---|---|
| ES futures | ES/GLOBEX/B0/1day | 1-minute calendar | -0.43929 | -1.1386 | 0.69928 |
| ES futures | ES/GLOBEX/B1/1day | 1-minute calendar | -0.40735 | -1.1386 | 0.73122 |
| NQ futures | NQ/GLOBEX/B0/1day | 1-minute calendar | -0.68676 | -1.1386 | 0.45182 |
| NQ futures | NQ/GLOBEX/B1/1day | 1-minute calendar | -0.64352 | -1.1386 | 0.49506 |
| ES futures | ES/RTH/B0/1day | 1-minute calendar | -0.63345 | -1.1444 | 0.51093 |
| ES futures | ES/RTH/B0/1h | 1-minute calendar | -0.46458 | -1.2097 | 0.74513 |
| ES futures | ES/RTH/B0/30min | 1-minute calendar | -0.41089 | -1.1971 | 0.78621 |
| ES futures | ES/RTH/B1/1day | 1-minute calendar | -0.65567 | -1.1444 | 0.4887 |
| ES futures | ES/RTH/B1/1h | 1-minute calendar | -0.46712 | -1.2097 | 0.7426 |
| ES futures | ES/RTH/B1/30min | 1-minute calendar | -0.41537 | -1.1971 | 0.78173 |
| NQ futures | NQ/RTH/B0/1day | 1-minute calendar | -0.9765 | -1.1444 | 0.16787 |
| NQ futures | NQ/RTH/B0/1h | 1-minute calendar | -0.80223 | -1.2097 | 0.40748 |
| NQ futures | NQ/RTH/B0/30min | 1-minute calendar | -0.70043 | -1.1971 | 0.49667 |
| NQ futures | NQ/RTH/B1/1day | 1-minute calendar | -1.0031 | -1.1444 | 0.14124 |
| NQ futures | NQ/RTH/B1/1h | 1-minute calendar | -0.80519 | -1.2097 | 0.40452 |
| NQ futures | NQ/RTH/B1/30min | 1-minute calendar | -0.69567 | -1.1971 | 0.50143 |
| SPY ARCX | SPY/ARCX/RTH/1day | calendar-time forward fill, full grid | -0.841 | -1.1248 | 0.28376 |
| SPY ARCX | SPY/ARCX/RTH/1day | calendar-time forward fill, bias<1% range | -0.841 | -1.1248 | 0.28376 |
| SPY ARCX | SPY/ARCX/RTH/1day | traded-tick, full grid | -0.53326 | -1.1248 | 0.59151 |
| SPY ARCX | SPY/ARCX/RTH/1day | traded-tick, bias<1% range | -0.53326 | -1.1248 | 0.59151 |
| SPY ARCX | SPY/ARCX/RTH/1day | calendar-time TRV3, full grid | -6.2597 | -1.1248 | -5.135 |
| SPY XNAS | SPY/XNAS/RTH/1day | calendar-time forward fill, full grid | -0.83937 | -1.1248 | 0.2854 |
| SPY XNAS | SPY/XNAS/RTH/1day | calendar-time forward fill, bias<1% range | -0.83937 | -1.1248 | 0.2854 |
| SPY XNAS | SPY/XNAS/RTH/1day | traded-tick, full grid | -0.59854 | -1.1248 | 0.52623 |
| SPY XNAS | SPY/XNAS/RTH/1day | traded-tick, bias<1% range | -0.59854 | -1.1248 | 0.52623 |
| SPY XNAS | SPY/XNAS/RTH/1day | calendar-time TRV3, full grid | -32.586 | -1.1248 | -31.461 |

### A. Replicates.

- ARCX calendar-time b -0.841, traded-tick b -0.533
- XNAS calendar-time b -0.839, traded-tick b -0.599
- trigamma reference on the primary range -1.125

Venue agreement is reported as an independent check and the two venues are never pooled. The SPY result covers roughly 33 percent of consolidated volume and is labelled as such.

## Which project conclusions now stand

The proxy-error scaling anomaly is unchanged by every repair applied to it: S06R moved the futures exponent by at most 1.6e-04 through the OHLC rebuild, the calendar exclusion and effective sub-bar count, and S05E's positive control recovered the trigamma reference through the identical code path while no synthetic arm reproduced the observed flatness. The MCS result is weaker than it was: the pre-registered insanity filter dominates the loss in 36 of 42 filtered (cell, model) combinations, and in the 1day cells the replaced observations carry 61 to 71 percent of mean QLIKE, so composition differences computed on those losses describe the filter as much as the models. The reliability programme itself is unaffected either way, since lambda does not enter the MCS. The SPY determination above sets how far the exponent result generalises beyond futures.
