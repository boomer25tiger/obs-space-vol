# Session 5B report, S05 defect diagnosis and estimator validity audit

Generated 2026-08-19T04:06:35+00:00 (UTC). Diagnosis only. No S05 or S05A artifact was modified, no MCS was re-run, no forecast was filtered or clipped, no estimator or truncation level was selected. All output under `sessions/s05b-defect-and-estimator-audit/`.

## Phase 1, source inspection (no computation)

### 1a. The array passed to `mcs()`

`partde.py:241-263`:

```python
241  rv = S["rv"]
242  ev = slice(max(start, warm), len(rv))
243  idx_ok = np.ones(len(rv), bool)
244  for m in MODELS:
245      idx_ok &= np.isfinite(F[m])
246  idx_ok[:ev.start] = False
247  rvv = rv[idx_ok]
248  Fm = {m: F[m][idx_ok] for m in MODELS}
249  L = np.column_stack([qlike(Fm[m], rvv) for m in MODELS])
...
262  Ls = L[smask]
263  pv = mcs(Ls, rngm)
```

with `qlike` at `partde.py:180-182`:

```python
180  def qlike(F, rv):
181      x = rv / F
182      return x - np.log(x) - 1.0
```

Construction: `L` is `np.column_stack` of seven float64 QLIKE columns, shape (n_evaluated, 7), dtype float64; `Ls = L[smask]` is a row subset. **The complete list of filtering, masking, dropping, clipping and imputation steps between the per-observation loss and the MCS call is: (i) `idx_ok` requires every model's FORECAST to be finite (line 245), (ii) `idx_ok` drops the warm-up (line 246), (iii) `smask` selects the evaluation scheme's rows.** There is no step of any kind applied to the LOSS. A forecast that is finite but arbitrarily small or large passes the filter, and its QLIKE - including `inf` from a zero realized variance or a floored forecast - enters `mcs()` unaltered.

### 1b. Which Part C estimator supplies `lam_hat`

`partde.py:250-255`:

```python
250  lamrow = lamC[(lamC.root == root) & (lamC.geom == geom)
251                & (lamC.btag == btag)
252                & (lamC.horizon == horizon)
253                & (lamC.year == 0) & (lamC.tercile == 0)]
254  lamrow = lamrow[lamrow.M == lamrow.M.max()]
255  lam_hat = float(lamrow["E4"].iloc[0])
```

**E4 supplies `lam_hat`, unconditionally.** The selection is FIXED, hard-coded as the literal column name `"E4"`; it is not conditional and there is no fallback to another estimator. The row is pinned to the pooled cell (`year == 0`, `tercile == 0`) at the finest M.

Pre-registration search: S05 `PREREG.md` Part C specifies only that E4 uses "the Part A variant with the most stable R" (that is a QUARTICITY-VARIANT rule, not an estimator rule) and Part E asks for "reliability-corrected IC" without naming a source estimator. `specs/` contains only `NOTE-missing-specs.md` (both spec documents are absent from the repository, per DECISIONS item 11). `DECISIONS.md` contains no rule either. **Nothing in any frozen document specifies which of the six Part C estimators supplies `lam_hat`.** The choice of E4 exists only in the source.

### 1c. Definition of the `IC-IR` column

`partde.py:276-298`:

```python
276  ic = float(np.corrcoef(lf, lrv)[0, 1])
280  w = 63
281  ics = [np.corrcoef(lf[i:i + w], lrv[i:i + w])[0, 1]
283         for i in range(0, len(lrv) - w, w)]
284  ics = [x for x in ics if np.isfinite(x)]
285  ir = float(np.mean(ics) / np.std(ics)) \
286       if len(ics) > 2 and np.std(ics) > 0 else np.nan
295  ic_corrected=ic / np.sqrt(lam_hat),
298  ic_ir=ir,
```

- Aggregation period: **63 windows**, non-overlapping (`range(..., w)` steps by w). At the 1day horizon that is 63 sessions; at 1h and 30min it is 63 intraday WINDOWS, not 63 days, so the period differs by horizon.
- Number of periods entering the standard deviation: `floor((n_obs - 63)/63)`, after dropping non-finite blocks; it is not recorded in the output and varies by cell and scheme.
- Annualization: **none**. No sqrt(periods-per-year) or any other factor is applied.
- IC used: **Pearson on logs** (`np.corrcoef(lf, lrv)`), not Spearman. `np.std` is the population standard deviation (ddof=0).
- Reliability correction: **not applied at all** to `ic_ir`. The correction appears only in the separate `ic_corrected` column (line 295), formed as `ic / sqrt(lam_hat)` AFTER the Pearson IC; the ratio in `ic_ir` is built from uncorrected block ICs.

### 1d. Representation of the sampling variance of log RV

Every occurrence in the S05 code path, and in the S01/S02 code S05 imports:

| file:line | expression | role |
|---|---|---|
| `s02/estimators2.py:62` | `v = (2.0 / M) * Q / np.maximum(P * P, 1e-300)` | E4, the estimator S05 Part C and Part E use |
| `s01/estimators.py:132` | `v = (2.0 / M) * rq / (rv * rv)` | S01 E4 |
| `s05/parta.py:151` | `R = (2.0 / M) * Q / np.maximum(P * P, 1e-300)` | Part A ratio |
| `s05/parta.py:170-171` | `ref_2overM=2.0 / M`, `med_over_ref=med / (2.0 / M)` | Part A reference line |

**`2/M` is used everywhere; `trigamma(M/2)` (or `polygamma`) appears nowhere in the S01-S05 codebase.** No measured sampling variance is substituted anywhere.

Finite-M or Jensen bias correction on E[log RV]: **none exists**. The only occurrences of the word Jensen (`parta.py:83`, `parta.py:91`, `report5.py:44`) concern the mean-of-ratios versus ratio-of-means diagnostic inside unit test T1 for RQ/TQ, not E[log RV]. `partc.py` applies no correction: it takes `np.log(np.maximum(rv, 1e-300))` and uses `.var()` directly.

### 1e. Bar aggregation

`partde.py:47-57`:

```python
47  def build_series(grid, wlen):
49      n1 = grid.shape[1] - 1
50      nw = n1 // wlen if wlen else 1
52      r1 = np.diff(grid, axis=1)[:, :nw * wlen]
53      rw = r1.reshape(-1, wlen)
56      rw = np.diff(grid, axis=1)
```

Coarser bars are built by `np.diff` of the log-price panel and reshaping, i.e. by summing consecutive one-minute log returns. **The panel holds close prices only** (S03 `analysis.build_panels` fills `px` from `sub["close"]`), so every aggregate - RV, BV, RQ, and the range proxies `park`/`gk` at lines 64-69, which take max/min of the CUMULATIVE CLOSE path rather than true session high/low - uses closes only. No open, high or low enters any S05 quantity.

### 1f. Panel provenance

A materialized panel exists on disk: eight `panel_<root>_<geom>_<btag>.npz` files under `sessions/s05-reliability-mcs/results/`, float32 log-price grids (sessions x minutes), 32.2 MB total, 13,732,320 price points and 13,716,914 one-minute returns. Returns are NOT rebuilt from the DBN file: one `np.diff` recovers them. **Read time for one full pass over all eight panels: 1.05 s.** Phases 3 and 4 are therefore cheap, which places this session at the low end of the 30-55 minute expectation.

| panel | sessions | price_cols | returns | read_s |
|---|---|---|---|---|
| panel_ES_GLOBEX_B0.npz | 1953 | 1380 | 2693187 | 0.249 |
| panel_ES_GLOBEX_B1.npz | 1953 | 1380 | 2693187 | 0.159 |
| panel_ES_RTH_B0.npz | 1901 | 390 | 739489 | 0.053 |
| panel_ES_RTH_B1.npz | 1901 | 390 | 739489 | 0.039 |
| panel_NQ_GLOBEX_B0.npz | 1948 | 1380 | 2686292 | 0.194 |
| panel_NQ_GLOBEX_B1.npz | 1948 | 1380 | 2686292 | 0.17 |
| panel_NQ_RTH_B0.npz | 1901 | 390 | 739489 | 0.029 |
| panel_NQ_RTH_B1.npz | 1901 | 390 | 739489 | 0.159 |

## Phase 2, forecast pathology

**Obstruction, reported not worked around:** S05 persisted no forecast artifacts (`partde.py` holds `F` in memory and writes only `s05_metrics.csv` and `s05_mcs.csv`), so Phase 2's premise "reads S05 forecast artifacts only" cannot be satisfied. Forecasts were regenerated by calling S05's own `build_series`/`forecasts` unmodified on S05's stored panels. Part D contains no RNG and a fixed refit schedule, so the regeneration is deterministic; S05A Phase 4 verified this class of regeneration reproduces S05's QLIKE column bitwise, and the Phase 3 reconstruction below reproduces the section 5 QLIKE means exactly.

### Forecast distribution, every model x cell

Full table (168 rows): `phase2_forecast_stats.csv`. Rows with any pathology:

| cell | model | n_eval | n_nonpositive | n_below_1e12 | n_below_1e6 | n_above_100x_mean_rv | min_forecast | p001_forecast | max_forecast |
|---|---|---|---|---|---|---|---|---|---|
| ES/GLOBEX/B0/1day | M4_HARQ | 1453 | 0 | 2 | 2 | 0 | 1e-300 | 3.002e-06 | 0.006261 |
| ES/GLOBEX/B0/1h | M2_HAR | 40996 | 0 | 0 | 5098 | 2 | 3.481e-07 | 4.483e-07 | 0.0006517 |
| ES/GLOBEX/B0/1h | M3_HARJ | 40996 | 0 | 0 | 5460 | 2 | 1.347e-07 | 3.124e-07 | 0.0007316 |
| ES/GLOBEX/B0/1h | M4_HARQ | 40996 | 0 | 3 | 8314 | 0 | 1e-300 | 3.395e-07 | 0.0005327 |
| ES/GLOBEX/B0/1h | M5_RGARCH | 40996 | 3 | 1410 | 1425 | 39568 | 0 | 1.431e-25 | 4.924e+263 |
| ES/GLOBEX/B0/1h | M6_PARK | 40996 | 180 | 180 | 20856 | 5 | 0 | 0 | 0.00138 |
| ES/GLOBEX/B0/1h | M6_GK | 40996 | 0 | 180 | 21029 | 6 | 1e-300 | 1e-300 | 0.001193 |
| ES/GLOBEX/B0/30min | M2_HAR | 21604 | 0 | 0 | 4158 | 1 | 3.626e-07 | 4.303e-07 | 0.0003237 |
| ES/GLOBEX/B0/30min | M3_HARJ | 21604 | 0 | 0 | 4154 | 1 | 3.531e-07 | 4.301e-07 | 0.0004104 |
| ES/GLOBEX/B0/30min | M5_RGARCH | 21604 | 0 | 112 | 112 | 21492 | 1.464e-125 | 2.628e-125 | 1.635e+299 |
| ES/GLOBEX/B0/30min | M6_PARK | 21604 | 126 | 126 | 12754 | 0 | 0 | 0 | 0.0003202 |
| ES/GLOBEX/B0/30min | M6_GK | 21604 | 0 | 126 | 13117 | 0 | 1e-300 | 1e-300 | 0.0002472 |
| ES/GLOBEX/B1/1day | M3_HARJ | 1453 | 0 | 1 | 1 | 0 | 1e-300 | 2.083e-05 | 0.006042 |
| ES/GLOBEX/B1/1day | M4_HARQ | 1453 | 0 | 6 | 8 | 0 | 1e-300 | 1e-300 | 0.005438 |
| ES/GLOBEX/B1/1h | M5_RGARCH | 1403 | 3 | 16 | 22 | 1381 | 0 | 0 | 4.222e+301 |
| ES/GLOBEX/B1/1h | M6_PARK | 1403 | 21 | 21 | 594 | 0 | 0 | 0 | 6.763e-05 |
| ES/GLOBEX/B1/1h | M6_GK | 1403 | 0 | 21 | 613 | 0 | 1e-300 | 1e-300 | 5.08e-05 |
| ES/GLOBEX/B1/30min | M2_HAR | 79538 | 0 | 0 | 33947 | 6 | 1.781e-07 | 2.34e-07 | 0.0005362 |
| ES/GLOBEX/B1/30min | M3_HARJ | 79538 | 0 | 0 | 34016 | 6 | 1.284e-07 | 2.051e-07 | 0.0005521 |
| ES/GLOBEX/B1/30min | M4_HARQ | 79538 | 0 | 4 | 37848 | 3 | 1e-300 | 1.202e-07 | 0.0003961 |
| ES/GLOBEX/B1/30min | M5_RGARCH | 79538 | 69119 | 75098 | 75187 | 4314 | 0 | 0 | 1.464e+308 |
| ES/GLOBEX/B1/30min | M6_PARK | 79538 | 401 | 401 | 55413 | 15 | 0 | 0 | 0.00138 |
| ES/GLOBEX/B1/30min | M6_GK | 79538 | 0 | 401 | 56503 | 8 | 1e-300 | 1e-300 | 0.001113 |
| NQ/GLOBEX/B0/1day | M4_HARQ | 1448 | 0 | 1 | 1 | 0 | 1e-300 | 2.383e-05 | 0.00602 |
| NQ/GLOBEX/B0/1h | M2_HAR | 22259 | 0 | 0 | 2918 | 1 | 4.384e-07 | 4.774e-07 | 0.0006827 |
| NQ/GLOBEX/B0/1h | M3_HARJ | 22259 | 0 | 0 | 3379 | 3 | 3.03e-07 | 3.662e-07 | 0.0007164 |
| NQ/GLOBEX/B0/1h | M4_HARQ | 22259 | 0 | 2 | 4406 | 0 | 1e-300 | 3.727e-07 | 0.0005326 |
| NQ/GLOBEX/B0/1h | M5_RGARCH | 22259 | 166 | 166 | 166 | 22093 | 0 | 0 | 1.033e+298 |
| NQ/GLOBEX/B0/1h | M6_PARK | 22259 | 166 | 166 | 11318 | 5 | 0 | 0 | 0.001486 |
| NQ/GLOBEX/B0/1h | M6_GK | 22259 | 0 | 166 | 11407 | 4 | 1e-300 | 1e-300 | 0.001183 |
| NQ/GLOBEX/B0/30min | M2_HAR | 80900 | 0 | 0 | 21079 | 4 | 2.487e-07 | 2.866e-07 | 0.000663 |
| NQ/GLOBEX/B0/30min | M3_HARJ | 80900 | 0 | 0 | 21370 | 5 | 2.305e-07 | 2.671e-07 | 0.0006383 |
| NQ/GLOBEX/B0/30min | M4_HARQ | 80900 | 0 | 4 | 25741 | 1 | 1e-300 | 1.616e-07 | 0.0004439 |
| NQ/GLOBEX/B0/30min | M5_RGARCH | 80900 | 0 | 382 | 382 | 80518 | 1.917e-219 | 1.319e-174 | 1.246e+122 |
| NQ/GLOBEX/B0/30min | M6_PARK | 80900 | 382 | 382 | 47883 | 4 | 0 | 0 | 0.001486 |
| NQ/GLOBEX/B0/30min | M6_GK | 80900 | 0 | 382 | 49198 | 5 | 1e-300 | 1e-300 | 0.001271 |
| NQ/GLOBEX/B1/1day | M3_HARJ | 1448 | 0 | 3 | 3 | 0 | 1e-300 | 1e-300 | 0.005396 |
| NQ/GLOBEX/B1/1day | M4_HARQ | 1448 | 0 | 2 | 2 | 0 | 1e-300 | 4.621e-06 | 0.005311 |
| NQ/GLOBEX/B1/1h | M4_HARQ | 39503 | 0 | 3 | 4925 | 0 | 1e-300 | 3.722e-07 | 0.0005724 |
| NQ/GLOBEX/B1/1h | M5_RGARCH | 39503 | 18495 | 19052 | 19062 | 20435 | 0 | 0 | 3.86e+276 |
| NQ/GLOBEX/B1/1h | M6_PARK | 39503 | 166 | 166 | 16087 | 2 | 0 | 0 | 0.001486 |
| NQ/GLOBEX/B1/1h | M6_GK | 39503 | 0 | 166 | 16269 | 2 | 1e-300 | 1e-300 | 0.001183 |
| NQ/GLOBEX/B1/30min | M2_HAR | 83735 | 0 | 0 | 23431 | 4 | 2.434e-07 | 2.762e-07 | 0.0006782 |
| NQ/GLOBEX/B1/30min | M3_HARJ | 83735 | 0 | 0 | 23785 | 3 | 2.32e-07 | 2.666e-07 | 0.0005401 |
| NQ/GLOBEX/B1/30min | M4_HARQ | 83735 | 0 | 5 | 28014 | 0 | 1e-300 | 1.546e-07 | 0.0003911 |
| NQ/GLOBEX/B1/30min | M5_RGARCH | 83735 | 0 | 385 | 385 | 83350 | 9.232e-231 | 2.086e-184 | 6.061e+306 |
| NQ/GLOBEX/B1/30min | M6_PARK | 83735 | 385 | 385 | 50350 | 4 | 0 | 0 | 0.001486 |
| NQ/GLOBEX/B1/30min | M6_GK | 83735 | 0 | 385 | 51690 | 5 | 1e-300 | 1e-300 | 0.001271 |
| ES/RTH/B0/1day | M4_HARQ | 1401 | 0 | 2 | 2 | 0 | 1e-300 | 2.37e-06 | 0.002675 |
| ES/RTH/B0/1h | M4_HARQ | 10906 | 0 | 2 | 114 | 0 | 1e-300 | 7.205e-07 | 0.0007221 |
| ES/RTH/B0/1h | M6_PARK | 10906 | 0 | 0 | 2587 | 1 | 2.816e-08 | 6.994e-08 | 0.001325 |
| ES/RTH/B0/1h | M6_GK | 10906 | 0 | 0 | 2628 | 1 | 1.811e-08 | 6.327e-08 | 0.001599 |
| ES/RTH/B0/30min | M4_HARQ | 22312 | 0 | 2 | 3354 | 0 | 1e-300 | 3.406e-07 | 0.0003608 |
| ES/RTH/B0/30min | M6_GK | 22312 | 0 | 0 | 10116 | 1 | 4.539e-09 | 1.859e-08 | 0.0005804 |
| ES/RTH/B1/1day | M4_HARQ | 1401 | 0 | 2 | 2 | 0 | 1e-300 | 2.06e-06 | 0.0026 |
| ES/RTH/B1/1h | M4_HARQ | 10906 | 0 | 2 | 123 | 0 | 1e-300 | 7.052e-07 | 0.0005919 |
| ES/RTH/B1/1h | M6_PARK | 10906 | 0 | 0 | 2604 | 1 | 2.816e-08 | 6.995e-08 | 0.001325 |
| ES/RTH/B1/1h | M6_GK | 10906 | 0 | 0 | 2641 | 1 | 1.811e-08 | 6.334e-08 | 0.001599 |
| ES/RTH/B1/30min | M4_HARQ | 22312 | 0 | 2 | 3542 | 0 | 1e-300 | 3.292e-07 | 0.0003589 |
| ES/RTH/B1/30min | M6_GK | 22312 | 0 | 0 | 10157 | 1 | 4.539e-09 | 1.859e-08 | 0.0005804 |
| NQ/RTH/B0/1day | M4_HARQ | 1401 | 0 | 1 | 1 | 0 | 1e-300 | 1.394e-05 | 0.002679 |
| NQ/RTH/B0/1h | M4_HARQ | 10906 | 0 | 2 | 2 | 0 | 1e-300 | 1.42e-06 | 0.0009812 |
| NQ/RTH/B0/30min | M4_HARQ | 22312 | 0 | 2 | 1101 | 0 | 1e-300 | 5.232e-07 | 0.0004773 |
| NQ/RTH/B1/1day | M3_HARJ | 1401 | 0 | 1 | 1 | 0 | 1e-300 | 1.474e-05 | 0.002492 |
| NQ/RTH/B1/1day | M4_HARQ | 1401 | 0 | 2 | 2 | 0 | 1e-300 | 5.572e-06 | 0.002507 |
| NQ/RTH/B1/1h | M4_HARQ | 10906 | 0 | 1 | 1 | 0 | 1e-300 | 1.43e-06 | 0.001001 |
| NQ/RTH/B1/30min | M4_HARQ | 22312 | 0 | 1 | 1107 | 0 | 1e-300 | 5.415e-07 | 0.0004392 |

### M4_HARQ and M3_HARJ offending observations

3662 offending observations in total ({'nonfinite_qlike': 3580, 'below_1e-12': 58, 'above_100x_mean_rv': 24}); full list `phase2_offending_observations.csv`. Every 1day-horizon offender:

| cell | model | trade_date | forecast | realized | qlike | share_of_cell_qlike | reason |
|---|---|---|---|---|---|---|---|
| ES/GLOBEX/B0/1day | M4_HARQ | 2018-02-06 | 1e-300 | 0.001876 | 1.876e+297 | 0.7576 | below_1e-12 |
| ES/GLOBEX/B0/1day | M4_HARQ | 2020-03-04 | 1e-300 | 0.0006003 | 6.003e+296 | 0.2424 | below_1e-12 |
| ES/GLOBEX/B1/1day | M3_HARJ | 2022-11-11 | 1e-300 | 0.0001737 | 1.737e+296 | 1 | below_1e-12 |
| ES/GLOBEX/B1/1day | M4_HARQ | 2018-02-06 | 1e-300 | 0.001819 | 1.819e+297 | 0.7154 | below_1e-12 |
| ES/GLOBEX/B1/1day | M4_HARQ | 2020-03-04 | 1e-300 | 0.000594 | 5.94e+296 | 0.2336 | below_1e-12 |
| ES/GLOBEX/B1/1day | M4_HARQ | 2021-02-16 | 1e-300 | 4.909e-05 | 4.909e+295 | 0.01931 | below_1e-12 |
| ES/GLOBEX/B1/1day | M4_HARQ | 2021-04-05 | 1e-300 | 2.491e-05 | 2.491e+295 | 0.009799 | below_1e-12 |
| ES/GLOBEX/B1/1day | M4_HARQ | 2021-06-01 | 1e-300 | 2.732e-05 | 2.732e+295 | 0.01075 | below_1e-12 |
| ES/GLOBEX/B1/1day | M4_HARQ | 2021-07-06 | 1e-300 | 2.832e-05 | 2.832e+295 | 0.01114 | below_1e-12 |
| NQ/GLOBEX/B0/1day | M4_HARQ | 2020-03-04 | 1e-300 | 0.0006767 | 6.767e+296 | 1 | below_1e-12 |
| NQ/GLOBEX/B1/1day | M3_HARJ | 2021-06-17 | 1e-300 | 9.65e-05 | 9.65e+295 | 0.08549 | below_1e-12 |
| NQ/GLOBEX/B1/1day | M3_HARJ | 2022-07-14 | 1e-300 | 0.000351 | 3.51e+296 | 0.311 | below_1e-12 |
| NQ/GLOBEX/B1/1day | M3_HARJ | 2022-10-14 | 1e-300 | 0.0006813 | 6.813e+296 | 0.6036 | below_1e-12 |
| NQ/GLOBEX/B1/1day | M4_HARQ | 2020-03-04 | 1e-300 | 0.0006622 | 6.622e+296 | 0.4929 | below_1e-12 |
| NQ/GLOBEX/B1/1day | M4_HARQ | 2022-10-14 | 1e-300 | 0.0006813 | 6.813e+296 | 0.5071 | below_1e-12 |
| ES/RTH/B0/1day | M4_HARQ | 2018-02-06 | 1e-300 | 0.000717 | 7.17e+296 | 0.6904 | below_1e-12 |
| ES/RTH/B0/1day | M4_HARQ | 2020-03-04 | 1e-300 | 0.0003216 | 3.216e+296 | 0.3096 | below_1e-12 |
| ES/RTH/B1/1day | M4_HARQ | 2018-02-06 | 1e-300 | 0.0006816 | 6.816e+296 | 0.6795 | below_1e-12 |
| ES/RTH/B1/1day | M4_HARQ | 2020-03-04 | 1e-300 | 0.0003214 | 3.214e+296 | 0.3205 | below_1e-12 |
| NQ/RTH/B0/1day | M4_HARQ | 2020-03-04 | 1e-300 | 0.0003408 | 3.408e+296 | 1 | below_1e-12 |
| NQ/RTH/B1/1day | M3_HARJ | 2021-06-17 | 1e-300 | 5.638e-05 | 5.638e+295 | 1 | below_1e-12 |
| NQ/RTH/B1/1day | M4_HARQ | 2018-02-06 | 1e-300 | 0.0008642 | 8.642e+296 | 0.7172 | below_1e-12 |
| NQ/RTH/B1/1day | M4_HARQ | 2020-03-04 | 1e-300 | 0.0003407 | 3.407e+296 | 0.2828 | below_1e-12 |

### Share of cell QLIKE carried by the worst observations

| cell | model | worst1_share_of_qlike | worst5_share_of_qlike |
|---|---|---|---|
| NQ/GLOBEX/B0/1h | M3_HARJ | inf | inf |
| ES/GLOBEX/B1/30min | M3_HARJ | inf | inf |
| NQ/GLOBEX/B0/30min | M4_HARQ | inf | inf |
| NQ/GLOBEX/B0/30min | M3_HARJ | inf | inf |
| NQ/GLOBEX/B0/1h | M4_HARQ | inf | inf |
| NQ/GLOBEX/B1/1h | M4_HARQ | inf | inf |
| NQ/GLOBEX/B1/30min | M3_HARJ | inf | inf |
| ES/GLOBEX/B1/30min | M4_HARQ | inf | inf |
| ES/GLOBEX/B1/1h | M4_HARQ | inf | inf |
| ES/GLOBEX/B0/1h | M3_HARJ | inf | inf |
| ES/GLOBEX/B1/1h | M3_HARJ | inf | inf |
| NQ/GLOBEX/B1/30min | M4_HARQ | inf | inf |
| ES/GLOBEX/B0/30min | M4_HARQ | inf | inf |
| ES/GLOBEX/B0/30min | M3_HARJ | inf | inf |
| ES/GLOBEX/B0/1h | M4_HARQ | inf | inf |
| NQ/GLOBEX/B1/1h | M3_HARJ | inf | inf |
| NQ/RTH/B0/1day | M4_HARQ | 1 | 1 |
| NQ/RTH/B1/30min | M4_HARQ | 1 | 1 |
| NQ/RTH/B1/1day | M3_HARJ | 1 | 1 |
| NQ/GLOBEX/B0/1day | M4_HARQ | 1 | 1 |
| NQ/RTH/B1/1h | M4_HARQ | 1 | 1 |
| ES/GLOBEX/B1/1day | M3_HARJ | 1 | 1 |
| ES/RTH/B0/1h | M4_HARQ | 0.8255 | 1 |
| ES/RTH/B0/30min | M4_HARQ | 0.8129 | 1 |
| ES/RTH/B1/1h | M4_HARQ | 0.8101 | 1 |

### Fitted coefficient vectors at the worst observations

Coefficient order: [const, RV_d, RV_w, RV_m] for M3_HARJ plus [J], for M4_HARQ plus [sqrt(RQ)*RV_d]. `linear_fit` is the raw OLS prediction before `max(., 1e-300)`:

| cell | model | rank | trade_date | linear_fit | negative_by_construction | stored_forecast | coef | components |
|---|---|---|---|---|---|---|---|---|
| ES/GLOBEX/B0/1day | M4_HARQ | 1 | 2018-02-06 | -3.865e-05 | True | 1e-300 | [4.625485867002123e-06, 1.0609683945781627, -0.04837052512917596, 0.04299283632867598, -438.63765152042964] | [4.625485867002123e-06, 0.0007216907504513472, -9.898254341148138e-06, 2.989199317783372e-06, -0.0007580586003469586] |
| ES/GLOBEX/B0/1day | M4_HARQ | 2 | 2020-03-04 | -0.0005405 | True | 1e-300 | [6.148358176528451e-06, 0.830292208818347, 0.33192625343055926, -0.1431791479066088, -122.41930431210076] | [6.148358176528451e-06, 0.0016807450226268051, 0.0004492955722478078, -5.309341887146172e-05, -0.002623583713436539] |
| ES/GLOBEX/B0/1day | M4_HARQ | 3 | 2020-11-30 | 1.15e-05 | False | 1.15e-05 | [3.38785427010543e-07, 0.9228573624481329, 0.2869884214179368, -0.12182316058480605, -41.00061292536028] | [3.38785427010543e-07, 1.9123458699305847e-05, 1.8394161526999055e-05, -2.632174999498503e-05, -3.2841753767864035e-08] |
| ES/GLOBEX/B0/1h | M3_HARJ | 1 | 2019-07-04 | 7.364e-07 | False | 7.364e-07 | [2.851049167020641e-07, 0.5906764191711352, 0.32884559614034214, 0.010106466158408338, -0.20919564090207537] | [2.851049167020641e-07, 0.0, 4.275030270590042e-07, 2.381101322021224e-08, -0.0] |
| ES/GLOBEX/B0/1h | M3_HARJ | 2 | 2020-03-09 | 2.44e-05 | False | 2.44e-05 | [2.596342770317812e-07, 0.6369607177248453, 0.3648844447940314, -0.037054941119044574, -0.2890678371455222] | [2.596342770317812e-07, 7.308956566241203e-06, 1.7597589171463926e-05, -7.663364903482148e-07, -0.0] |
| ES/GLOBEX/B0/1h | M3_HARJ | 3 | 2018-12-05 | 2.483e-06 | False | 2.483e-06 | [2.923957013278239e-07, 0.5874501607517625, 0.30983135421543134, 0.02874664139231535, -0.2580902466442811] | [2.923957013278239e-07, 5.36774169496628e-07, 1.4809777051050785e-06, 1.7300371072419637e-07, -0.0] |
| ES/GLOBEX/B0/1h | M4_HARQ | 1 | 2020-01-20 | 4.234e-07 | False | 4.234e-07 | [1.6023240208038939e-07, 0.7480807148975595, 0.2520636949488015, -0.019210812737108424, -1000.2058126636095] | [1.6023240208038939e-07, 0.0, 2.879007897556908e-07, -2.4686094041204074e-08, -0.0] |
| ES/GLOBEX/B0/1h | M4_HARQ | 2 | 2020-03-18 | 5.558e-05 | False | 5.558e-05 | [-4.3037750504619783e-07, 0.6447918110420964, 0.5640636114486534, -0.04013942676082382, -196.240258825717] | [-4.3037750504619783e-07, 0.0, 5.7673042356109846e-05, -1.6584205244427306e-06, -0.0] |
| ES/GLOBEX/B0/1h | M4_HARQ | 3 | 2022-09-05 | 4.077e-06 | False | 4.077e-06 | [1.6601963298734455e-07, 0.6729779453832837, 0.4139737320787235, -0.08907752211399536, -224.42695880295153] | [1.6601963298734455e-07, 8.913965325065697e-07, 3.5029173375830798e-06, -4.833684789489469e-07, -3.705580356128823e-10] |
| ES/GLOBEX/B0/30min | M3_HARJ | 1 | 2016-02-15 | 2.966e-06 | False | 2.966e-06 | [1.505525096472033e-05, 0.5936616489775616, 0.2954427230513076, -2.071514508966132, 0.22148372878768102] | [1.505525096472033e-05, 0.0, 1.928681834299328e-06, -1.4017980190701124e-05, 0.0] |
| ES/GLOBEX/B0/30min | M3_HARJ | 2 | 2022-01-17 | 1.181e-06 | False | 1.181e-06 | [1.9140331449379814e-07, 0.4435004030546417, 0.5324944555403606, -0.09405466924163454, 0.4068546603402133] | [1.9140331449379814e-07, 0.0, 1.1674936398698492e-06, -1.7740382436435754e-07, 0.0] |
| ES/GLOBEX/B0/30min | M3_HARJ | 3 | 2022-01-17 | 1.21e-06 | False | 1.21e-06 | [1.9140331449379814e-07, 0.4435004030546417, 0.5324944555403606, -0.09405466924163454, 0.4068546603402133] | [1.9140331449379814e-07, 0.0, 1.1968702252584105e-06, -1.7839024518106535e-07, 0.0] |
| ES/GLOBEX/B0/30min | M4_HARQ | 1 | 2016-02-15 | 1.749e-06 | False | 1.749e-06 | [1.3578423726253987e-05, 0.9080262539611598, 0.22644648808575324, -1.966529885812906, -8052.064848206334] | [1.3578423726253987e-05, 0.0, 1.478267000456888e-06, -1.3307547142165713e-05, -0.0] |
| ES/GLOBEX/B0/30min | M4_HARQ | 2 | 2023-01-16 | 9.573e-07 | False | 9.573e-07 | [1.135990401711953e-07, 0.6413190481815534, 0.426780091370546, -0.0847307111676195, -310.52918673838604] | [1.135990401711953e-07, 0.0, 1.1257671984352908e-06, -2.8204421302667025e-07, -0.0] |
| ES/GLOBEX/B0/30min | M4_HARQ | 3 | 2023-01-16 | 9.445e-07 | False | 9.445e-07 | [1.135990401711953e-07, 0.6413190481815534, 0.426780091370546, -0.0847307111676195, -310.52918673838604] | [1.135990401711953e-07, 0.0, 1.1127732231580594e-06, -2.8183850788389987e-07, -0.0] |
| ES/GLOBEX/B1/1day | M3_HARJ | 1 | 2022-11-11 | -0.0001495 | True | 1e-300 | [2.227906644900348e-05, 0.6185319683382987, 0.34754378732118696, -0.029725400948953477, -1.7780487369341853] | [2.227906644900348e-05, 0.0004023001860137408, 0.00010840129781568605, -9.926341588072306e-06, -0.0006725095140764445] |
| ES/GLOBEX/B1/1day | M3_HARJ | 2 | 2018-02-05 | 6.747e-05 | False | 6.747e-05 | [5.519087197398021e-06, 0.12103257651237749, 0.14774331576774963, 0.3045699482395513, 2.79491437786069] | [5.519087197398021e-06, 1.4203031896076766e-05, 1.1015915525297537e-05, 1.1712461113733504e-05, 2.5022035109585986e-05] |
| ES/GLOBEX/B1/1day | M3_HARJ | 3 | 2018-12-06 | 5.534e-05 | False | 5.534e-05 | [8.052947748550277e-06, 0.28361246942446244, 0.2211512522897436, 0.1063558314739429, 3.27278920994941] | [8.052947748550277e-06, 1.0097663042932246e-05, 2.0510829202733365e-05, 1.3393026520533757e-05, 3.280667559160009e-06] |
| ES/GLOBEX/B1/1day | M4_HARQ | 1 | 2018-02-06 | -3.679e-05 | True | 1e-300 | [4.425308145068478e-06, 1.0707525230177903, -0.054218498996147675, 0.0427343282210719, -447.1146390144308] | [4.425308145068478e-06, 0.0006993429586832575, -1.0710009469758371e-05, 2.8789310581126286e-06, -0.0007327229766507732] |
| ES/GLOBEX/B1/1day | M4_HARQ | 2 | 2020-03-04 | -0.0008991 | True | 1e-300 | [5.758202349226503e-06, 0.8477597957590224, 0.3261621560403112, -0.14557614280024916, -140.5171159991085] | [5.758202349226503e-06, 0.0016995589568704439, 0.00042823647491861563, -5.2413895493226055e-05, -0.0029802377258795632] |
| ES/GLOBEX/B1/1day | M4_HARQ | 3 | 2021-02-16 | -7.142e-07 | True | 1e-300 | [-6.807398031633931e-06, 1.0340116518081657, 0.29461954832124193, -0.1500687138425766, -64.14676155023224] | [-6.807398031633931e-06, 9.04019068096888e-06, 1.0740598242959568e-05, -1.3681170977884704e-05, -6.443800845197072e-09] |
| ES/GLOBEX/B1/1h | M3_HARJ | 1 | 2016-05-30 | 5.158e-07 | False | 5.158e-07 | [3.779436103538773e-09, 0.5837100815721512, 0.3100128867432414, 0.03666340855345335, 0.37074925372459194] | [3.779436103538773e-09, 0.0, 4.168682983080771e-07, 9.516510364877036e-08, 0.0] |
| ES/GLOBEX/B1/1h | M3_HARJ | 2 | 2016-05-30 | 5.226e-07 | False | 5.226e-07 | [3.779436103538773e-09, 0.5837100815721512, 0.3100128867432414, 0.03666340855345335, 0.37074925372459194] | [3.779436103538773e-09, 0.0, 4.2340425603653086e-07, 9.54219869604276e-08, 0.0] |
| ES/GLOBEX/B1/1h | M3_HARJ | 3 | 2017-02-20 | 1.882e-07 | False | 1.882e-07 | [-1.4449525121951763e-08, 0.6016569600198837, 0.15489360085302897, 0.045483835740861976, 1.7675029113381149] | [-1.4449525121951763e-08, 0.0, 1.5168182286016496e-07, 5.092251649871877e-08, 0.0] |
| ES/GLOBEX/B1/1h | M4_HARQ | 1 | 2017-01-16 | 3.985e-07 | False | 3.985e-07 | [1.90679027535489e-07, 0.7864206319068916, 0.10803744773993776, 0.05126490449435203, -674.3634038858299] | [1.90679027535489e-07, 0.0, 1.4121983142355717e-07, 6.66260016577383e-08, -0.0] |
| ES/GLOBEX/B1/1h | M4_HARQ | 2 | 2017-01-16 | 4.003e-07 | False | 4.003e-07 | [1.90679027535489e-07, 0.7864206319068916, 0.10803744773993776, 0.05126490449435203, -674.3634038858299] | [1.90679027535489e-07, 0.0, 1.4281070632635773e-07, 6.683318209319127e-08, -0.0] |
| ES/GLOBEX/B1/1h | M4_HARQ | 3 | 2016-11-24 | 5.829e-07 | False | 5.829e-07 | [2.2968433664746805e-07, 0.7891092838499659, 0.09960937880366931, 0.053565336369813844, -683.83897645864] | [2.2968433664746805e-07, 0.0, 9.97041083797822e-08, 2.534849956934978e-07, -0.0] |
| ES/GLOBEX/B1/30min | M3_HARJ | 1 | 2022-11-24 | 7.013e-07 | False | 7.013e-07 | [2.4937871097413136e-07, 0.5034084286017619, 0.5282834930786854, -0.08322392997571218, -0.31273689622764217] | [2.4937871097413136e-07, 0.0, 8.24064873808466e-07, -3.7215955172545977e-07, -0.0] |
| ES/GLOBEX/B1/30min | M3_HARJ | 2 | 2022-11-24 | 7.428e-07 | False | 7.428e-07 | [2.4937871097413136e-07, 0.5034084286017619, 0.5282834930786854, -0.08322392997571218, -0.31273689622764217] | [2.4937871097413136e-07, 0.0, 8.665526735820539e-07, -3.7310998463640537e-07, -0.0] |
| ES/GLOBEX/B1/30min | M3_HARJ | 3 | 2022-11-24 | 7.502e-07 | False | 7.502e-07 | [2.4937871097413136e-07, 0.5034084286017619, 0.5282834930786854, -0.08322392997571218, -0.31273689622764217] | [2.4937871097413136e-07, 0.0, 8.742652459341e-07, -3.734129324254731e-07, -0.0] |
| ES/GLOBEX/B1/30min | M4_HARQ | 1 | 2018-11-22 | 6.026e-07 | False | 6.026e-07 | [5.815110858503572e-08, 0.8139060311179522, 0.19083933845967493, -0.016081610612735796, -1699.553577110848] | [5.815110858503572e-08, 0.0, 6.114610054274944e-07, -6.701155143574067e-08, -0.0] |
| ES/GLOBEX/B1/30min | M4_HARQ | 2 | 2018-11-22 | 1.095e-06 | False | 1.095e-06 | [5.815110858503572e-08, 0.8139060311179522, 0.19083933845967493, -0.016081610612735796, -1699.553577110848] | [5.815110858503572e-08, 4.1802478615336837e-07, 6.875906716047889e-07, -6.799105342619413e-08, -5.149925534104127e-10] |
| ES/GLOBEX/B1/30min | M4_HARQ | 3 | 2023-02-20 | 1.218e-06 | False | 1.218e-06 | [9.768662593293942e-08, 0.6510230923561929, 0.4233945644083608, -0.08397904220515266, -384.9660731594424] | [9.768662593293942e-08, 2.4958048906920615e-07, 1.086863484987851e-06, -2.1641242799934846e-07, -6.83746978225211e-11] |
| NQ/GLOBEX/B0/1day | M4_HARQ | 1 | 2020-03-04 | -0.0006795 | True | 1e-300 | [5.738460270328875e-06, 0.9219661535273379, 0.24731493312844818, -0.10072770206753073, -136.2850857013559] | [5.738460270328875e-06, 0.001954907693235391, 0.0004030148018931394, -4.7706170511187696e-05, -0.002995434592666857] |
| NQ/GLOBEX/B0/1day | M4_HARQ | 2 | 2018-02-06 | 7.885e-05 | False | 7.885e-05 | [4.576864414268788e-06, 1.0543789319278856, -0.05494293173650789, 0.06766270799096658, -340.698341729366] | [4.576864414268788e-06, 0.0008873202269177311, -1.5443130221834436e-05, 6.833857031278655e-06, -0.0008044331900879085] |
| NQ/GLOBEX/B0/1day | M4_HARQ | 3 | 2018-12-06 | 7.429e-05 | False | 7.429e-05 | [1.0907534227107698e-05, 0.8192809685716494, 0.14349807740497048, 0.027216710725786106, -171.88504273498154] | [1.0907534227107698e-05, 3.603551459279887e-05, 2.1437338589276857e-05, 6.505542492477849e-06, -5.910337373042368e-07] |
| NQ/GLOBEX/B0/1h | M3_HARJ | 1 | 2020-03-09 | 1.766e-05 | False | 1.766e-05 | [3.325286720582472e-07, 0.6332330703349979, 0.3561195740000315, -0.02169852379394807, -0.3051877327625204] | [3.325286720582472e-07, 0.0, 1.787316273549625e-05, -5.480570423614491e-07, -0.0] |
| NQ/GLOBEX/B0/1h | M3_HARJ | 2 | 2021-02-15 | 1.327e-06 | False | 1.327e-06 | [5.689453376551773e-07, 0.550392128779247, 0.45188440200632324, -0.06845072889905032, -0.12875064801938974] | [5.689453376551773e-07, 0.0, 1.1763809634729563e-06, -4.1800697448899604e-07, -0.0] |
| NQ/GLOBEX/B0/1h | M3_HARJ | 3 | 2021-02-15 | 1.337e-06 | False | 1.337e-06 | [5.689453376551773e-07, 0.550392128779247, 0.45188440200632324, -0.06845072889905032, -0.12875064801938974] | [5.689453376551773e-07, 0.0, 1.1860576884670156e-06, -4.184298450981099e-07, -0.0] |
| NQ/GLOBEX/B0/1h | M4_HARQ | 1 | 2021-04-02 | 1.185e-06 | False | 1.185e-06 | [1.619411423399884e-07, 0.7197472366818939, 0.36386476273496826, -0.07640516329118165, -250.26854240730552] | [1.619411423399884e-07, 0.0, 2.0274255076437253e-06, -1.0042538226474526e-06, -0.0] |

**34 of 105 inspected worst-observation fits are negative by construction.** In every negative case the quarticity interaction coefficient is large and negative (for example -438.6 and -122.4 in ES/GLOBEX/B0/1day), so on a high-quarticity day the term `coef * sqrt(RQ) * RV_d` exceeds the sum of the positive HAR terms; the OLS prediction goes below zero and `partde.py:157` (`F[m][t] = max(float(X[t - 1] @ coef[m]), 1e-300)`) floors it to 1e-300, which is the finite value that passes the `np.isfinite` filter at line 245 and produces QLIKE of order 1e296.

## Phase 3, panel materialization and non-finite audit

### Windows with zero or near-zero realized variance

Pooled across years (per-year rows in `phase3_zero_rv.csv`):

| root | geom | btag | horizon | n_windows | n_rv_exact_zero | share_rv_exact_zero | n_rv_lt_1e14 | min_rv |
|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | 1h | 42966 | 186 | 0.004329 | 186 | 0 |
| ES | GLOBEX | B0 | 30min | 87885 | 435 | 0.00495 | 435 | 0 |
| ES | GLOBEX | B1 | 1h | 42966 | 186 | 0.004329 | 186 | 0 |
| ES | GLOBEX | B1 | 30min | 87885 | 438 | 0.004984 | 438 | 0 |
| NQ | GLOBEX | B0 | 1h | 42856 | 169 | 0.003943 | 169 | 0 |
| NQ | GLOBEX | B0 | 30min | 87660 | 396 | 0.004517 | 396 | 0 |
| NQ | GLOBEX | B1 | 1h | 42856 | 169 | 0.003943 | 169 | 0 |
| NQ | GLOBEX | B1 | 30min | 87660 | 399 | 0.004552 | 399 | 0 |

**No RTH cell at any horizon contains a zero-variance window (0 found across all RTH cells, 1day, 1h and 30min).** Every invariance result at every RTH horizon in Phase 5 is therefore NOT provisional on this ground. GLOBEX 1day likewise contains none; the zero-variance windows are confined to GLOBEX 1h and 30min.

### Quarticity variants at or below zero

163 of 696 (cell, horizon, M, variant) combinations have a zero quarticity or zero proxy; full table `phase3_quarticity_zeros.csv`.

| root | geom | btag | horizon | M | variant | n | n_Q_zero | n_P_zero | min_Q | min_P |
|---|---|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | 1day | 5 | TQ_BV | 1953 | 31 | 1 | 0 | 0 |
| ES | GLOBEX | B0 | 1day | 5 | TRQ3_TRV3 | 1953 | 1 | 1 | 0 | 0 |
| ES | GLOBEX | B0 | 1day | 5 | TRQ5_TRV5 | 1953 | 1 | 1 | 0 | 0 |
| ES | GLOBEX | B0 | 1day | 5 | TRQ10_TRV10 | 1953 | 1 | 1 | 0 | 0 |
| ES | GLOBEX | B0 | 1day | 6 | TQ_BV | 1953 | 11 | 1 | 0 | 0 |
| ES | GLOBEX | B0 | 1day | 6 | TRQ3_TRV3 | 1953 | 1 | 1 | 0 | 0 |
| ES | GLOBEX | B0 | 1day | 6 | TRQ5_TRV5 | 1953 | 1 | 1 | 0 | 0 |
| ES | GLOBEX | B0 | 1day | 6 | TRQ10_TRV10 | 1953 | 1 | 1 | 0 | 0 |
| ES | GLOBEX | B0 | 1day | 10 | TQ_BV | 1953 | 1 | 0 | 0 | 6.367e-07 |
| ES | GLOBEX | B1 | 1day | 5 | TQ_BV | 1953 | 29 | 1 | 0 | 0 |
| ES | GLOBEX | B1 | 1day | 5 | TRQ3_TRV3 | 1953 | 1 | 1 | 0 | 0 |
| ES | GLOBEX | B1 | 1day | 5 | TRQ5_TRV5 | 1953 | 1 | 1 | 0 | 0 |
| ES | GLOBEX | B1 | 1day | 5 | TRQ10_TRV10 | 1953 | 1 | 1 | 0 | 0 |
| ES | GLOBEX | B1 | 1day | 6 | TQ_BV | 1953 | 10 | 0 | 0 | 2.527e-07 |
| ES | GLOBEX | B1 | 1day | 10 | TQ_BV | 1953 | 1 | 0 | 0 | 6.832e-07 |
| NQ | GLOBEX | B0 | 1day | 5 | TQ_BV | 1948 | 12 | 0 | 0 | 3.242e-07 |
| NQ | GLOBEX | B0 | 1day | 6 | TQ_BV | 1948 | 1 | 0 | 0 | 1.597e-07 |
| NQ | GLOBEX | B1 | 1day | 5 | TQ_BV | 1948 | 12 | 0 | 0 | 2.388e-07 |
| NQ | GLOBEX | B1 | 1day | 6 | TQ_BV | 1948 | 2 | 0 | 0 | 1.931e-07 |
| ES | RTH | B0 | 1day | 5 | TQ_BV | 1901 | 49 | 1 | 0 | 0 |

### Non-finite QLIKE by cell and model

| root | geom | btag | horizon | model | n_eval | n_nonfinite_qlike | n_rv_zero_in_eval |
|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | 1h | M1_EWMA | 40996 | 180 | 180 |
| ES | GLOBEX | B0 | 1h | M2_HAR | 40996 | 180 | 180 |
| ES | GLOBEX | B0 | 1h | M3_HARJ | 40996 | 180 | 180 |
| ES | GLOBEX | B0 | 1h | M4_HARQ | 40996 | 180 | 180 |
| ES | GLOBEX | B0 | 1h | M5_RGARCH | 40996 | 181 | 180 |
| ES | GLOBEX | B0 | 1h | M6_PARK | 40996 | 237 | 180 |
| ES | GLOBEX | B0 | 1h | M6_GK | 40996 | 180 | 180 |
| ES | GLOBEX | B1 | 1h | M1_EWMA | 1403 | 15 | 15 |
| ES | GLOBEX | B1 | 1h | M2_HAR | 1403 | 15 | 15 |
| ES | GLOBEX | B1 | 1h | M3_HARJ | 1403 | 15 | 15 |
| ES | GLOBEX | B1 | 1h | M4_HARQ | 1403 | 15 | 15 |
| ES | GLOBEX | B1 | 1h | M5_RGARCH | 1403 | 16 | 15 |
| ES | GLOBEX | B1 | 1h | M6_PARK | 1403 | 22 | 15 |
| ES | GLOBEX | B1 | 1h | M6_GK | 1403 | 15 | 15 |
| NQ | GLOBEX | B0 | 1h | M1_EWMA | 22259 | 140 | 140 |
| NQ | GLOBEX | B0 | 1h | M2_HAR | 22259 | 140 | 140 |
| NQ | GLOBEX | B0 | 1h | M3_HARJ | 22259 | 140 | 140 |
| NQ | GLOBEX | B0 | 1h | M4_HARQ | 22259 | 140 | 140 |
| NQ | GLOBEX | B0 | 1h | M5_RGARCH | 22259 | 194 | 140 |
| NQ | GLOBEX | B0 | 1h | M6_PARK | 22259 | 194 | 140 |
| NQ | GLOBEX | B0 | 1h | M6_GK | 22259 | 140 | 140 |

GLOBEX 1h and 30min detail (2482 logged occurrences, `phase3_nonfinite_detail.csv`): **17.6% fall inside the overnight period** (window start before 09:30 New York). Time-of-day distribution of the affected windows:

| ny_clock | count |
|---|---|
| 14:00 | 713 |
| 15:00 | 712 |
| 13:00 | 510 |
| 18:00 | 149 |
| 06:00 | 42 |
| 12:00 | 41 |
| 11:00 | 41 |
| 07:00 | 31 |
| 04:00 | 28 |
| 03:00 | 28 |
| 08:00 | 28 |
| 10:00 | 27 |
| 02:00 | 21 |
| 20:00 | 17 |
| 22:00 | 17 |

Distinct windows producing infinite QLIKE, by cell:

| root | geom | btag | horizon | distinct_windows |
|---|---|---|---|---|
| ES | GLOBEX | B0 | 1h | 228 |
| ES | GLOBEX | B1 | 1h | 22 |
| NQ | GLOBEX | B0 | 1h | 194 |

### Reconstructed loss arrays for the three named cells

| cell | shape | model | n_nonfinite | n_inf | n_nan | col_mean | col_mean_finite_only | s05_qlike_mean | matches_s05 |
|---|---|---|---|---|---|---|---|---|---|
| ES/GLOBEX/B0/1h/S-A | 40996x7 | M1_EWMA | 180 | 180 | 0 | inf | 0.5987 | inf | True |
| ES/GLOBEX/B0/1h/S-A | 40996x7 | M2_HAR | 180 | 180 | 0 | inf | 0.3441 | inf | True |
| ES/GLOBEX/B0/1h/S-A | 40996x7 | M3_HARJ | 180 | 180 | 0 | inf | 0.3437 | inf | True |
| ES/GLOBEX/B0/1h/S-A | 40996x7 | M4_HARQ | 180 | 180 | 0 | inf | 1.064e+292 | inf | True |
| ES/GLOBEX/B0/1h/S-A | 40996x7 | M5_RGARCH | 181 | 178 | 3 | -- | 9.251e+28 | -- | True |
| ES/GLOBEX/B0/1h/S-A | 40996x7 | M6_PARK | 237 | 57 | 180 | -- | 1.572 | -- | True |
| ES/GLOBEX/B0/1h/S-A | 40996x7 | M6_GK | 180 | 180 | 0 | inf | 4.422e+292 | inf | True |

The reconstructed arrays match S05's section 5 QLIKE column exactly in 7 of 7 model columns (inf matching inf, NaN matching NaN). **The array the MCS consumes is the same array whose column means section 5 reports as `inf`/`nan`** - the MCS is not fed a cleaned version.

### Non-finite handling in the MCS implementations

S05's own implementation, `partde.py:185-215`, contains no non-finite handling of any kind: `np.cumsum` (line 191) propagates `inf`, the block difference `csum[b:] - csum[:-b]` (line 192) turns `inf - inf` into `nan`, `losses.mean(axis=0)` (line 194) is the plain mean rather than `nanmean`, and the elimination test `p = float((TR_boot >= TR).mean())` (line 209) compares against `nan`, which is False everywhere and yields p = 0.0. Measured behaviour on a synthetic loss matrix whose first column contains one `inf`: p-values `{M1: 0.0, M3: 0.0, M2: 1.0}` - the procedure returns a definite single-model confidence set with no error and no warning. That is the mechanism by which DECISIONS item 22's cells acquire definite compositions.

The installed third-party implementation `arch.bootstrap.MCS` (arch 8.0.0) was also read: its `compute()` contains no reference to `nan`, `inf`, `isfinite` or `dropna` either. Neither implementation guards the input.

## Phase 4, grid cache build

Grid verification. Every nominal M divides its session length in minutes exactly. **The panel, however, supplies L = session_minutes - 1 one-minute returns**, because a session's first close has no predecessor inside the session. Consequences, both reported rather than repaired:

1. At the 1day horizons no M in the grid divides L, so **every 1day grid point carries exactly one stub sub-bar** one minute shorter than the rest. At the RTH 1h and 30min horizons L is 60 and 30 exactly and every M divides it, so those grids have no stub.
2. The nominal finest points M=390 (RTH) and M=1380 (GLOBEX) are **unattainable**: they exceed L. S05 reached them at `partc.py`/`parta.py` via `if p.shape[1] == M: p = concat([p, grid[:, -1:]])`, which appends a duplicate final price and injects one identically zero return, leaving effective M = L. S05B adds M = L (389 / 1379) as the finest attainable point and records the nominal point as unattainable.

| geom | horizon | nominal_M | L | reason |
|---|---|---|---|---|
| RTH | 1day | 390 | 389 | panel supplies L = session_minutes - 1 returns; S05 reached nominal M by duplicating the final price point, injecting one zero return |
| GLOBEX | 1day | 1380 | 1379 | panel supplies L = session_minutes - 1 returns; S05 reached nominal M by duplicating the final price point, injecting one zero return |

Grid index (ES/B0 shown; all cells in `phase4_grid_index.csv`):

| geom | horizon | M | session_minutes | L_returns_per_window | M_divides_session | M_divides_L | subbar_size_min | subbar_size_max | n_stub_subbars | n_windows | share_full_M | share_below_0p9M | mean_eff_M | var_log_rv |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GLOBEX | 1day | 5 | 1380 | 1379 | True | False | 275 | 276 | 1 | 1953 | 0.9985 | 0.001536 | 4.998 | 2.023 |
| GLOBEX | 1day | 6 | 1380 | 1379 | True | False | 229 | 230 | 1 | 1953 | 0.9734 | 0.02663 | 5.972 | 2.05 |
| GLOBEX | 1day | 10 | 1380 | 1379 | True | False | 137 | 138 | 1 | 1953 | 0.9729 | 0.001536 | 9.97 | 1.708 |
| GLOBEX | 1day | 12 | 1380 | 1379 | True | False | 114 | 115 | 1 | 1953 | 0.9724 | 0.02663 | 11.94 | 1.697 |
| GLOBEX | 1day | 23 | 1380 | 1379 | True | False | 59 | 60 | 1 | 1953 | 0.9724 | 0.02663 | 22.89 | 1.513 |
| GLOBEX | 1day | 46 | 1380 | 1379 | True | False | 29 | 30 | 1 | 1953 | 0.9713 | 0.02714 | 45.77 | 1.42 |
| GLOBEX | 1day | 138 | 1380 | 1379 | True | False | 9 | 10 | 1 | 1953 | 0.3062 | 0.02765 | 136.6 | 1.312 |
| GLOBEX | 1day | 345 | 1380 | 1379 | True | False | 3 | 4 | 1 | 1953 | 0.3057 | 0.02816 | 341.1 | 1.221 |
| RTH | 1day | 5 | 390 | 389 | True | False | 77 | 78 | 1 | 1901 | 1 | 0 | 5 | 1.949 |
| RTH | 1day | 6 | 390 | 389 | True | False | 64 | 65 | 1 | 1901 | 1 | 0 | 6 | 1.826 |
| RTH | 1day | 10 | 390 | 389 | True | False | 38 | 39 | 1 | 1901 | 1 | 0 | 10 | 1.604 |
| RTH | 1day | 13 | 390 | 389 | True | False | 29 | 30 | 1 | 1901 | 1 | 0 | 13 | 1.528 |
| RTH | 1day | 26 | 390 | 389 | True | False | 14 | 15 | 1 | 1901 | 1 | 0 | 26 | 1.381 |
| RTH | 1day | 78 | 390 | 389 | True | False | 4 | 5 | 1 | 1901 | 0.9984 | 0 | 78 | 1.288 |
| RTH | 1day | 195 | 390 | 389 | True | False | 1 | 2 | 1 | 1901 | 0.9984 | 0 | 195 | 1.182 |
| RTH | 1h | 4 | 60 | 60 | True | True | 15 | 15 | 0 | 11406 | 1 | 0 | 4 | 2.29 |
| RTH | 1h | 5 | 60 | 60 | True | True | 12 | 12 | 0 | 11406 | 1 | 0 | 5 | 2.138 |
| RTH | 1h | 6 | 60 | 60 | True | True | 10 | 10 | 0 | 11406 | 0.9998 | 0.0001753 | 6 | 2.048 |
| RTH | 1h | 10 | 60 | 60 | True | True | 6 | 6 | 0 | 11406 | 0.9997 | 0.0001753 | 10 | 1.832 |
| RTH | 1h | 12 | 60 | 60 | True | True | 5 | 5 | 0 | 11406 | 0.9997 | 0.000263 | 12 | 1.789 |
| RTH | 1h | 15 | 60 | 60 | True | True | 4 | 4 | 0 | 11406 | 0.9997 | 0.000263 | 15 | 1.709 |
| RTH | 1h | 20 | 60 | 60 | True | True | 3 | 3 | 0 | 11406 | 0.9997 | 0.000263 | 20 | 1.645 |
| RTH | 1h | 30 | 60 | 60 | True | True | 2 | 2 | 0 | 11406 | 0.9997 | 0.000263 | 30 | 1.548 |
| RTH | 1h | 60 | 60 | 60 | True | True | 1 | 1 | 0 | 11406 | 0.9997 | 0.000263 | 60 | 1.38 |
| RTH | 30min | 5 | 30 | 30 | True | True | 6 | 6 | 0 | 22812 | 0.9999 | 0.0001315 | 5 | 2.148 |
| RTH | 30min | 6 | 30 | 30 | True | True | 5 | 5 | 0 | 22812 | 0.9999 | 0.0001315 | 6 | 2.06 |
| RTH | 30min | 10 | 30 | 30 | True | True | 3 | 3 | 0 | 22812 | 0.9998 | 0.0001315 | 9.999 | 1.813 |
| RTH | 30min | 15 | 30 | 30 | True | True | 2 | 2 | 0 | 22812 | 0.9998 | 0.0001315 | 15 | 1.67 |
| RTH | 30min | 30 | 30 | 30 | True | True | 1 | 1 | 0 | 22812 | 0.9998 | 0.0001315 | 30 | 1.454 |
| GLOBEX | 1day | 1379 | 1380 | 1379 | False | True | 1 | 1 | 0 | 1953 | 1 | 0 | 1379 | 1.043 |
| RTH | 1day | 389 | 390 | 389 | False | True | 1 | 1 | 0 | 1901 | 1 | 0 | 389 | 1.09 |

Effective sub-bar counts: `share_full_M` is the share of windows in which every sub-bar contains at least one minute with data on both ends (presence masks regenerated exactly by re-running S03's `build_panels` on the S04 repaired bars). **Nominal M is assumed everywhere in the estimators**: `estimators2.e4` takes `M` as an argument and S05 always passes the nominal value; no S05 code path consults an effective count. At GLOBEX 1day M=138 and M=345 only 30.6% of windows are at full nominal M.

Noise-robust references cached once per session-day:

| root | geom | btag | n | omega2_N1 | xi2 | kernel_bandwidth_H | tsrv_K | mean_kernel | mean_tsrv | mean_rv | n_kernel_nonpos | n_tsrv_nonpos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | 1379 | 3.952e-09 | 3.266e-05 | 1 | 2 | 0.000124 | 0.0001237 | 0.0001285 | 0 | 0 |
| ES | GLOBEX | B1 | 1379 | 3.952e-09 | 3.266e-05 | 1 | 2 | 0.0001213 | 0.0001212 | 0.0001255 | 0 | 0 |
| NQ | GLOBEX | B0 | 1379 | 2.117e-09 | 1.152e-05 | 1 | 2 | 0.0001861 | 0.0001856 | 0.0001856 | 0 | 0 |
| NQ | GLOBEX | B1 | 1379 | 2.117e-09 | 1.152e-05 | 1 | 2 | 0.0001816 | 0.0001816 | 0.000181 | 0 | 0 |
| ES | RTH | B0 | 389 | 6.343e-09 | 9.012e-05 | 1 | 2 | 7.41e-05 | 7.282e-05 | 7.438e-05 | 0 | 0 |
| ES | RTH | B1 | 389 | 6.343e-09 | 9.012e-05 | 1 | 2 | 7.259e-05 | 7.259e-05 | 7.309e-05 | 0 | 0 |
| NQ | RTH | B0 | 389 | 1.98e-09 | 1.735e-05 | 1 | 2 | 0.0001179 | 0.0001158 | 0.0001146 | 0 | 0 |
| NQ | RTH | B1 | 389 | 1.98e-09 | 1.735e-05 | 1 | 2 | 0.0001155 | 0.0001155 | 0.0001125 | 0 | 0 |

Cache: 136 files, 71.3 MB, built in 49.9 s (panel read and presence masks a further 74.5 s and 24.7 s).

## Phase 5, grid invariance and boundary separation

### lambda_M x Var(log RV_M): ratio of largest to smallest, and coefficient of variation

Var(log IV) cannot depend on M, so a valid estimator holds this product constant across the grid (DECISIONS item 26). 1day horizons:

| ('estimator', '', '') | ('GLOBEX', 'ES', 'B0') | ('GLOBEX', 'ES', 'B1') | ('GLOBEX', 'NQ', 'B0') | ('GLOBEX', 'NQ', 'B1') | ('RTH', 'ES', 'B0') | ('RTH', 'ES', 'B1') | ('RTH', 'NQ', 'B0') | ('RTH', 'NQ', 'B1') |
|---|---|---|---|---|---|---|---|---|
| E1_a_exp_L1-10 | 1.361 | 1.363 | 1.137 | 1.142 | 1.284 | 1.261 | 1.132 | 1.133 |
| E1_a_exp_L1-5 | 1.373 | 1.377 | 1.109 | 1.127 | 1.285 | 1.278 | 1.102 | 1.102 |
| E1_d_model_L1-10 | 1.084 | 1.077 | 1.048 | 1.055 | 1.112 | 1.11 | 1.065 | 1.064 |
| E1_d_model_L1-5 | 1.361 | 1.365 | 1.117 | 1.135 | 1.274 | 1.267 | 1.072 | 1.074 |
| E2 | 1.468 | 1.464 | 1.23 | 1.312 | 1.308 | 1.343 | 1.57 | 1.185 |
| E4 | 1.683 | 1.691 | 1.494 | 1.484 | 1.521 | 1.531 | 1.45 | 1.452 |
| E4_asS05 | 1.968 | 1.934 | 1.547 | 1.544 | 1.794 | 1.802 | 1.522 | 1.525 |

RTH intraday horizons:

| ('estimator', '', '') | ('1h', 'ES', 'B0') | ('1h', 'ES', 'B1') | ('1h', 'NQ', 'B0') | ('1h', 'NQ', 'B1') | ('30min', 'ES', 'B0') | ('30min', 'ES', 'B1') | ('30min', 'NQ', 'B0') | ('30min', 'NQ', 'B1') |
|---|---|---|---|---|---|---|---|---|
| E1_a_exp_L1-10 | 1.258 | 1.26 | 1.094 | 1.093 | 1.216 | 1.218 | 1.081 | 1.08 |
| E1_a_exp_L1-5 | 1.259 | 1.271 | 1.104 | 1.104 | 1.209 | 1.211 | 1.086 | 1.095 |
| E1_d_model_L1-10 | 1.276 | 1.276 | 1.1 | 1.098 | 1.116 | 1.117 | 1.069 | 1.069 |
| E1_d_model_L1-5 | 1.271 | 1.272 | 1.123 | 1.097 | 1.014 | 1.011 | 1.015 | 1.015 |
| E2 | 1.212 | 1.212 | 1.306 | 1.323 | 1.482 | 1.484 | 1.065 | 1.066 |
| E4 | 1.458 | 1.461 | 1.306 | 1.305 | 1.342 | 1.342 | 1.216 | 1.216 |
| E4_asS05 | 1.7 | 1.703 | 1.527 | 1.527 | 1.478 | 1.479 | 1.4 | 1.401 |

Coefficient of variation of the same product, 1day:

| ('estimator', '', '') | ('GLOBEX', 'ES', 'B0') | ('GLOBEX', 'ES', 'B1') | ('GLOBEX', 'NQ', 'B0') | ('GLOBEX', 'NQ', 'B1') | ('RTH', 'ES', 'B0') | ('RTH', 'ES', 'B1') | ('RTH', 'NQ', 'B0') | ('RTH', 'NQ', 'B1') |
|---|---|---|---|---|---|---|---|---|
| E1_a_exp_L1-10 | 0.0844 | 0.0854 | 0.037 | 0.0395 | 0.0774 | 0.0746 | 0.0392 | 0.0383 |
| E1_a_exp_L1-5 | 0.0867 | 0.0884 | 0.0302 | 0.0338 | 0.0789 | 0.077 | 0.0325 | 0.0308 |
| E1_d_model_L1-10 | 0.0299 | 0.0259 | 0.0173 | 0.0229 | 0.0363 | 0.0335 | 0.0209 | 0.0222 |
| E1_d_model_L1-5 | 0.0861 | 0.0873 | 0.0315 | 0.035 | 0.0776 | 0.0763 | 0.0212 | 0.0225 |
| E2 | 0.104 | 0.1045 | 0.0541 | 0.0762 | 0.0864 | 0.0906 | 0.1508 | 0.0568 |
| E4 | 0.1515 | 0.1516 | 0.1388 | 0.1354 | 0.1323 | 0.1345 | 0.1301 | 0.1304 |
| E4_asS05 | 0.2157 | 0.1915 | 0.1528 | 0.1504 | 0.182 | 0.1838 | 0.1457 | 0.146 |

### Ranking by grid invariance

| estimator | ES/GLOBEX/B0/1day | ES/GLOBEX/B1/1day | ES/RTH/B0/1day | ES/RTH/B0/1h | ES/RTH/B0/30min | ES/RTH/B1/1day | ES/RTH/B1/1h | ES/RTH/B1/30min | NQ/GLOBEX/B0/1day | NQ/GLOBEX/B1/1day | NQ/RTH/B0/1day | NQ/RTH/B0/1h | NQ/RTH/B0/30min | NQ/RTH/B1/1day | NQ/RTH/B1/1h | NQ/RTH/B1/30min |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1_a_exp_L1-10 | 2 | 2 | 3 | 2 | 4 | 2 | 2 | 4 | 4 | 4 | 4 | 1 | 4 | 4 | 1 | 4 |
| E1_a_exp_L1-5 | 4 | 4 | 4 | 3 | 3 | 4 | 3 | 3 | 2 | 2 | 3 | 3 | 5 | 3 | 4 | 5 |
| E1_d_model_L1-10 | 1 | 1 | 1 | 5 | 2 | 1 | 5 | 2 | 1 | 1 | 1 | 2 | 3 | 1 | 3 | 3 |
| E1_d_model_L1-5 | 3 | 3 | 2 | 4 | 1 | 3 | 4 | 1 | 3 | 3 | 2 | 4 | 1 | 2 | 2 | 1 |
| E2 | 5 | 5 | 5 | 1 | 7 | 5 | 1 | 7 | 5 | 5 | 7 | 6 | 2 | 5 | 6 | 2 |
| E4 | 6 | 6 | 6 | 6 | 5 | 6 | 6 | 5 | 6 | 6 | 5 | 5 | 6 | 6 | 5 | 6 |
| E4_asS05 | 7 | 7 | 7 | 7 | 6 | 7 | 7 | 6 | 7 | 7 | 6 | 7 | 7 | 7 | 7 | 7 |

**The ranking is not consistent across all cells (identical-rank estimators: 0 of 7).** Reading the table: E4 ranks last in 11 of 16 cells and never better than 5th; E1_d_model_L1-10 ranks first in 8 cells. Rankings within the 1day horizons agree closely; the RTH intraday horizons reorder the middle of the table.

### Fitted elasticity of (1-lambda)/lambda against M

Extended grid versus the original S05 grid, 1day:

| ('estimator', '', '') | ('elasticity', 'GLOBEX', 'B0') | ('elasticity', 'GLOBEX', 'B1') | ('elasticity', 'RTH', 'B0') | ('elasticity', 'RTH', 'B1') | ('elasticity_s05grid', 'GLOBEX', 'B0') | ('elasticity_s05grid', 'GLOBEX', 'B1') | ('elasticity_s05grid', 'RTH', 'B0') | ('elasticity_s05grid', 'RTH', 'B1') |
|---|---|---|---|---|---|---|---|---|
| E1_a_exp_L1-10 | -0.281 | -0.28 | -0.311 | -0.312 | -0.171 | -0.175 | -0.21 | -0.206 |
| E1_a_exp_L1-5 | -0.307 | -0.304 | -0.342 | -0.344 | -0.186 | -0.187 | -0.228 | -0.22 |
| E1_d_model_L1-10 | -1.173 | -1.196 | -1.516 | -1.535 | -- | -- | -- | -- |
| E1_d_model_L1-5 | -0.805 | -0.816 | -0.929 | -0.897 | -0.777 | -0.806 | -0.878 | -0.816 |
| E2 | -0.272 | -0.257 | -0.371 | -0.426 | -0.136 | -0.134 | -0.325 | -0.323 |
| E4 | -0.615 | -0.616 | -0.706 | -0.707 | -0.682 | -0.68 | -0.763 | -0.762 |
| E4_asS05 | -0.478 | -0.625 | -0.563 | -0.564 | -0.903 | -0.902 | -0.88 | -0.88 |

Fit quality and dropped points (extended grid):

| root | geom | btag | horizon | estimator | elasticity | elasticity_r2 | n_used | n_dropped |
|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | 1day | E1_a_exp_L1-10 | -0.2741 | 0.912 | 9 | 0 |
| ES | GLOBEX | B0 | 1day | E1_a_exp_L1-5 | -0.2891 | 0.8874 | 9 | 0 |
| ES | GLOBEX | B0 | 1day | E1_d_model_L1-10 | -1.135 | 0.9778 | 5 | 4 |
| ES | GLOBEX | B0 | 1day | E1_d_model_L1-5 | -0.9247 | 0.9932 | 9 | 0 |
| ES | GLOBEX | B0 | 1day | E2 | -0.2215 | 0.7627 | 8 | 1 |
| ES | GLOBEX | B0 | 1day | E4 | -0.6265 | 0.9941 | 9 | 0 |
| ES | GLOBEX | B0 | 1day | E4_asS05 | -0.1691 | 0.0305 | 9 | 0 |
| ES | GLOBEX | B1 | 1day | E1_a_exp_L1-10 | -0.2737 | 0.911 | 9 | 0 |
| ES | GLOBEX | B1 | 1day | E1_a_exp_L1-5 | -0.2877 | 0.8959 | 9 | 0 |
| ES | GLOBEX | B1 | 1day | E1_d_model_L1-10 | -1.135 | 0.9765 | 5 | 4 |
| ES | GLOBEX | B1 | 1day | E1_d_model_L1-5 | -0.9255 | 0.9904 | 9 | 0 |
| ES | GLOBEX | B1 | 1day | E2 | -0.2225 | 0.7623 | 8 | 1 |
| ES | GLOBEX | B1 | 1day | E4 | -0.6267 | 0.9946 | 9 | 0 |
| ES | GLOBEX | B1 | 1day | E4_asS05 | -0.4625 | 0.254 | 9 | 0 |
| ES | RTH | B0 | 1day | E1_a_exp_L1-10 | -0.2869 | 0.9028 | 8 | 0 |
| ES | RTH | B0 | 1day | E1_a_exp_L1-5 | -0.3109 | 0.8993 | 8 | 0 |
| ES | RTH | B0 | 1day | E1_d_model_L1-10 | -1.624 | 0.9803 | 5 | 3 |
| ES | RTH | B0 | 1day | E1_d_model_L1-5 | -0.8435 | 0.9825 | 8 | 0 |
| ES | RTH | B0 | 1day | E2 | -0.3703 | 0.8937 | 8 | 0 |
| ES | RTH | B0 | 1day | E4 | -0.7044 | 0.9961 | 8 | 0 |
| ES | RTH | B0 | 1day | E4_asS05 | -0.3335 | 0.1027 | 8 | 0 |
| ES | RTH | B1 | 1day | E1_a_exp_L1-10 | -0.2907 | 0.8936 | 8 | 0 |
| ES | RTH | B1 | 1day | E1_a_exp_L1-5 | -0.3156 | 0.8751 | 8 | 0 |
| ES | RTH | B1 | 1day | E1_d_model_L1-10 | -1.671 | 0.982 | 5 | 3 |
| ES | RTH | B1 | 1day | E1_d_model_L1-5 | -0.8167 | 0.9796 | 8 | 0 |
| ES | RTH | B1 | 1day | E2 | -0.3655 | 0.9002 | 8 | 0 |
| ES | RTH | B1 | 1day | E4 | -0.7058 | 0.996 | 8 | 0 |
| ES | RTH | B1 | 1day | E4_asS05 | -0.3331 | 0.1028 | 8 | 0 |
| NQ | GLOBEX | B0 | 1day | E1_a_exp_L1-10 | -0.2887 | 0.8861 | 9 | 0 |
| NQ | GLOBEX | B0 | 1day | E1_a_exp_L1-5 | -0.324 | 0.8962 | 9 | 0 |
| NQ | GLOBEX | B0 | 1day | E1_d_model_L1-10 | -1.212 | 0.9658 | 6 | 3 |
| NQ | GLOBEX | B0 | 1day | E1_d_model_L1-5 | -0.6854 | 0.9811 | 9 | 0 |
| NQ | GLOBEX | B0 | 1day | E2 | -0.3216 | 0.8764 | 9 | 0 |
| NQ | GLOBEX | B0 | 1day | E4 | -0.6028 | 0.988 | 9 | 0 |
| NQ | GLOBEX | B0 | 1day | E4_asS05 | -0.7877 | 0.98 | 9 | 0 |
| NQ | GLOBEX | B1 | 1day | E1_a_exp_L1-10 | -0.2865 | 0.8973 | 9 | 0 |
| NQ | GLOBEX | B1 | 1day | E1_a_exp_L1-5 | -0.3198 | 0.8973 | 9 | 0 |
| NQ | GLOBEX | B1 | 1day | E1_d_model_L1-10 | -1.256 | 0.9618 | 6 | 3 |
| NQ | GLOBEX | B1 | 1day | E1_d_model_L1-5 | -0.7074 | 0.9699 | 9 | 0 |
| NQ | GLOBEX | B1 | 1day | E2 | -0.292 | 0.883 | 9 | 0 |
| NQ | GLOBEX | B1 | 1day | E4 | -0.6045 | 0.9899 | 9 | 0 |
| NQ | GLOBEX | B1 | 1day | E4_asS05 | -0.7868 | 0.9805 | 9 | 0 |
| NQ | RTH | B0 | 1day | E1_a_exp_L1-10 | -0.3342 | 0.9127 | 8 | 0 |
| NQ | RTH | B0 | 1day | E1_a_exp_L1-5 | -0.3731 | 0.9156 | 8 | 0 |
| NQ | RTH | B0 | 1day | E1_d_model_L1-10 | -1.409 | 0.9921 | 5 | 3 |
| NQ | RTH | B0 | 1day | E1_d_model_L1-5 | -1.014 | 0.993 | 8 | 0 |
| NQ | RTH | B0 | 1day | E2 | -0.3725 | 0.8196 | 8 | 0 |
| NQ | RTH | B0 | 1day | E4 | -0.7076 | 0.9912 | 8 | 0 |
| NQ | RTH | B0 | 1day | E4_asS05 | -0.7921 | 0.9826 | 8 | 0 |
| NQ | RTH | B1 | 1day | E1_a_exp_L1-10 | -0.3326 | 0.9102 | 8 | 0 |
| NQ | RTH | B1 | 1day | E1_a_exp_L1-5 | -0.3722 | 0.9054 | 8 | 0 |
| NQ | RTH | B1 | 1day | E1_d_model_L1-10 | -1.399 | 0.9844 | 5 | 3 |
| NQ | RTH | B1 | 1day | E1_d_model_L1-5 | -0.977 | 0.9901 | 8 | 0 |
| NQ | RTH | B1 | 1day | E2 | -0.4862 | 0.9443 | 8 | 0 |
| NQ | RTH | B1 | 1day | E4 | -0.7089 | 0.9919 | 8 | 0 |
| NQ | RTH | B1 | 1day | E4_asS05 | -0.794 | 0.9823 | 8 | 0 |

### B0 versus B1 elasticity difference

| root | geom | horizon | estimator | B0 | B1 | abs_diff | pct_diff |
|---|---|---|---|---|---|---|---|
| ES | GLOBEX | 1day | E1_a_exp_L1-10 | -0.2741 | -0.2737 | 0.0004 | 0.1452 |
| ES | GLOBEX | 1day | E1_a_exp_L1-5 | -0.2891 | -0.2877 | 0.0014 | 0.4947 |
| ES | GLOBEX | 1day | E1_d_model_L1-10 | -1.135 | -1.135 | 0.0003 | 0.0263 |
| ES | GLOBEX | 1day | E1_d_model_L1-5 | -0.9247 | -0.9255 | 0.0008 | 0.0847 |
| ES | GLOBEX | 1day | E2 | -0.2215 | -0.2225 | 0.001 | 0.4694 |
| ES | GLOBEX | 1day | E4 | -0.6265 | -0.6267 | 0.0002 | 0.0313 |
| ES | GLOBEX | 1day | E4_asS05 | -0.1691 | -0.4625 | 0.2934 | 173.5 |
| ES | RTH | 1day | E1_a_exp_L1-10 | -0.2869 | -0.2907 | 0.0038 | 1.329 |
| ES | RTH | 1day | E1_a_exp_L1-5 | -0.3109 | -0.3156 | 0.0048 | 1.531 |
| ES | RTH | 1day | E1_d_model_L1-10 | -1.624 | -1.671 | 0.0475 | 2.924 |
| ES | RTH | 1day | E1_d_model_L1-5 | -0.8435 | -0.8167 | 0.0269 | 3.186 |
| ES | RTH | 1day | E2 | -0.3703 | -0.3655 | 0.0048 | 1.303 |
| ES | RTH | 1day | E4 | -0.7044 | -0.7058 | 0.0014 | 0.2014 |
| ES | RTH | 1day | E4_asS05 | -0.3335 | -0.3331 | 0.0004 | 0.1131 |
| ES | RTH | 1h | E1_a_exp_L1-10 | -0.3357 | -0.3405 | 0.0048 | 1.442 |
| ES | RTH | 1h | E1_a_exp_L1-5 | -0.3606 | -0.3621 | 0.0015 | 0.4142 |
| ES | RTH | 1h | E1_d_model_L1-10 | -0.6987 | -0.7339 | 0.0352 | 5.034 |
| ES | RTH | 1h | E1_d_model_L1-5 | -0.7837 | -0.8362 | 0.0525 | 6.703 |
| ES | RTH | 1h | E2 | -0.4964 | -0.5024 | 0.006 | 1.204 |
| ES | RTH | 1h | E4 | -0.6434 | -0.6423 | 0.0011 | 0.1688 |
| ES | RTH | 1h | E4_asS05 | 2.454 | 2.465 | 0.0108 | 0.4391 |
| ES | RTH | 30min | E1_a_exp_L1-10 | -0.439 | -0.4465 | 0.0075 | 1.718 |
| ES | RTH | 30min | E1_a_exp_L1-5 | -0.761 | -0.7556 | 0.0054 | 0.7141 |
| ES | RTH | 30min | E1_d_model_L1-10 | -2.184 | -2.664 | 0.4793 | 21.94 |
| ES | RTH | 30min | E2 | 1.168 | 1.17 | 0.0017 | 0.1468 |
| ES | RTH | 30min | E4 | -0.609 | -0.6074 | 0.0016 | 0.2662 |
| ES | RTH | 30min | E4_asS05 | 1.798 | 1.8 | 0.0014 | 0.0764 |
| NQ | GLOBEX | 1day | E1_a_exp_L1-10 | -0.2887 | -0.2865 | 0.0022 | 0.7606 |
| NQ | GLOBEX | 1day | E1_a_exp_L1-5 | -0.324 | -0.3198 | 0.0042 | 1.286 |
| NQ | GLOBEX | 1day | E1_d_model_L1-10 | -1.212 | -1.256 | 0.0441 | 3.641 |
| NQ | GLOBEX | 1day | E1_d_model_L1-5 | -0.6854 | -0.7074 | 0.0221 | 3.22 |
| NQ | GLOBEX | 1day | E2 | -0.3216 | -0.292 | 0.0296 | 9.206 |
| NQ | GLOBEX | 1day | E4 | -0.6028 | -0.6045 | 0.0017 | 0.2878 |
| NQ | GLOBEX | 1day | E4_asS05 | -0.7877 | -0.7868 | 0.0009 | 0.1121 |
| NQ | RTH | 1day | E1_a_exp_L1-10 | -0.3342 | -0.3326 | 0.0015 | 0.4601 |
| NQ | RTH | 1day | E1_a_exp_L1-5 | -0.3731 | -0.3722 | 0.0009 | 0.2339 |
| NQ | RTH | 1day | E1_d_model_L1-10 | -1.409 | -1.399 | 0.0101 | 0.7177 |
| NQ | RTH | 1day | E1_d_model_L1-5 | -1.014 | -0.977 | 0.0369 | 3.636 |
| NQ | RTH | 1day | E2 | -0.3725 | -0.4862 | 0.1138 | 30.55 |
| NQ | RTH | 1day | E4 | -0.7076 | -0.7089 | 0.0012 | 0.1719 |
| NQ | RTH | 1day | E4_asS05 | -0.7921 | -0.794 | 0.0019 | 0.2438 |
| NQ | RTH | 1h | E1_a_exp_L1-10 | -0.3274 | -0.3342 | 0.0068 | 2.066 |
| NQ | RTH | 1h | E1_a_exp_L1-5 | -0.3221 | -0.3301 | 0.008 | 2.486 |
| NQ | RTH | 1h | E1_d_model_L1-10 | -0.5471 | -0.5885 | 0.0413 | 7.549 |
| NQ | RTH | 1h | E1_d_model_L1-5 | -0.601 | -0.6558 | 0.0548 | 9.117 |
| NQ | RTH | 1h | E2 | -0.5309 | -0.5304 | 0.0004 | 0.0825 |
| NQ | RTH | 1h | E4 | -0.6777 | -0.6776 | 0 | 0.0053 |
| NQ | RTH | 1h | E4_asS05 | 0.8627 | 0.841 | 0.0216 | 2.506 |
| NQ | RTH | 30min | E1_a_exp_L1-10 | -0.4051 | -0.416 | 0.0109 | 2.687 |
| NQ | RTH | 30min | E1_a_exp_L1-5 | -0.751 | -0.7422 | 0.0088 | 1.169 |
| NQ | RTH | 30min | E1_d_model_L1-10 | -2.68 | -5.326 | 2.646 | 98.72 |
| NQ | RTH | 30min | E2 | -0.8566 | -0.8658 | 0.0092 | 1.069 |
| NQ | RTH | 30min | E4 | -0.6598 | -0.6585 | 0.0014 | 0.2057 |
| NQ | RTH | 30min | E4_asS05 | 2.323 | 2.329 | 0.0065 | 0.2806 |

Median absolute B0-B1 elasticity difference 0.0048, maximum 2.6460; median percentage difference 0.91%, maximum 173.49%.

### Measured R = (2/M) Q / P^2 against trigamma(M/2)

Part A artifacts at every M and variant (pooled years), ES/B0 shown, full table `phase5_partA_R_vs_trigamma.csv`:

| geom | M | variant | median | ref_2overM | trigamma | med_over_ref | median_over_trigamma |
|---|---|---|---|---|---|---|---|
| GLOBEX | 23 | RQ_RV | 0.1164 | 0.08696 | 0.09085 | 1.339 | 1.282 |
| GLOBEX | 23 | TQ_BV | 0.0944 | 0.08696 | 0.09085 | 1.086 | 1.039 |
| GLOBEX | 23 | TRQ3_TRV3 | 0.09871 | 0.08696 | 0.09085 | 1.135 | 1.087 |
| GLOBEX | 23 | TRQ5_TRV5 | 0.1145 | 0.08696 | 0.09085 | 1.317 | 1.26 |
| GLOBEX | 23 | TRQ10_TRV10 | 0.1164 | 0.08696 | 0.09085 | 1.339 | 1.282 |
| GLOBEX | 23 | MEDRQ_MEDRV | 0.09915 | 0.08696 | 0.09085 | 1.14 | 1.091 |
| GLOBEX | 46 | RQ_RV | 0.06927 | 0.04348 | 0.04444 | 1.593 | 1.559 |
| GLOBEX | 46 | TQ_BV | 0.05814 | 0.04348 | 0.04444 | 1.337 | 1.308 |
| GLOBEX | 46 | TRQ3_TRV3 | 0.05378 | 0.04348 | 0.04444 | 1.237 | 1.21 |
| GLOBEX | 46 | TRQ5_TRV5 | 0.06717 | 0.04348 | 0.04444 | 1.545 | 1.512 |
| GLOBEX | 46 | TRQ10_TRV10 | 0.06927 | 0.04348 | 0.04444 | 1.593 | 1.559 |
| GLOBEX | 46 | MEDRQ_MEDRV | 0.06011 | 0.04348 | 0.04444 | 1.383 | 1.353 |
| GLOBEX | 138 | RQ_RV | 0.02903 | 0.01449 | 0.0146 | 2.003 | 1.989 |
| GLOBEX | 138 | TQ_BV | 0.02465 | 0.01449 | 0.0146 | 1.701 | 1.689 |
| GLOBEX | 138 | TRQ3_TRV3 | 0.01914 | 0.01449 | 0.0146 | 1.321 | 1.311 |
| GLOBEX | 138 | TRQ5_TRV5 | 0.02616 | 0.01449 | 0.0146 | 1.805 | 1.792 |
| GLOBEX | 138 | TRQ10_TRV10 | 0.02902 | 0.01449 | 0.0146 | 2.003 | 1.988 |
| GLOBEX | 138 | MEDRQ_MEDRV | 0.02548 | 0.01449 | 0.0146 | 1.758 | 1.746 |
| GLOBEX | 345 | RQ_RV | 0.0135 | 0.0058 | 0.00581 | 2.329 | 2.323 |
| GLOBEX | 345 | TQ_BV | 0.01147 | 0.0058 | 0.00581 | 1.979 | 1.973 |
| GLOBEX | 345 | TRQ3_TRV3 | 0.00782 | 0.0058 | 0.00581 | 1.348 | 1.344 |
| GLOBEX | 345 | TRQ5_TRV5 | 0.01115 | 0.0058 | 0.00581 | 1.923 | 1.917 |
| GLOBEX | 345 | TRQ10_TRV10 | 0.01344 | 0.0058 | 0.00581 | 2.318 | 2.311 |
| GLOBEX | 345 | MEDRQ_MEDRV | 0.0118 | 0.0058 | 0.00581 | 2.035 | 2.03 |
| GLOBEX | 1380 | RQ_RV | 0.0038 | 0.00145 | 0.00145 | 2.622 | 2.62 |
| GLOBEX | 1380 | TQ_BV | 0.00334 | 0.00145 | 0.00145 | 2.306 | 2.305 |
| GLOBEX | 1380 | TRQ3_TRV3 | 0.00191 | 0.00145 | 0.00145 | 1.318 | 1.317 |
| GLOBEX | 1380 | TRQ5_TRV5 | 0.00271 | 0.00145 | 0.00145 | 1.871 | 1.87 |
| GLOBEX | 1380 | TRQ10_TRV10 | 0.0037 | 0.00145 | 0.00145 | 2.551 | 2.549 |
| GLOBEX | 1380 | MEDRQ_MEDRV | 0.00322 | 0.00145 | 0.00145 | 2.223 | 2.221 |
| RTH | 13 | RQ_RV | 0.1412 | 0.1538 | 0.1663 | 0.9181 | 0.8494 |
| RTH | 13 | TQ_BV | 0.1224 | 0.1538 | 0.1663 | 0.7953 | 0.7358 |
| RTH | 13 | TRQ3_TRV3 | 0.1348 | 0.1538 | 0.1663 | 0.8762 | 0.8107 |
| RTH | 13 | TRQ5_TRV5 | 0.1409 | 0.1538 | 0.1663 | 0.9157 | 0.8472 |
| RTH | 13 | TRQ10_TRV10 | 0.1412 | 0.1538 | 0.1663 | 0.9181 | 0.8494 |
| RTH | 13 | MEDRQ_MEDRV | 0.1276 | 0.1538 | 0.1663 | 0.8294 | 0.7673 |
| RTH | 26 | RQ_RV | 0.08185 | 0.07692 | 0.07996 | 1.064 | 1.024 |
| RTH | 26 | TQ_BV | 0.07118 | 0.07692 | 0.07996 | 0.9253 | 0.8902 |
| RTH | 26 | TRQ3_TRV3 | 0.0746 | 0.07692 | 0.07996 | 0.9698 | 0.933 |
| RTH | 26 | TRQ5_TRV5 | 0.08133 | 0.07692 | 0.07996 | 1.057 | 1.017 |
| RTH | 26 | TRQ10_TRV10 | 0.08185 | 0.07692 | 0.07996 | 1.064 | 1.024 |
| RTH | 26 | MEDRQ_MEDRV | 0.07492 | 0.07692 | 0.07996 | 0.974 | 0.9371 |
| RTH | 78 | RQ_RV | 0.03355 | 0.02564 | 0.02597 | 1.308 | 1.292 |
| RTH | 78 | TQ_BV | 0.02874 | 0.02564 | 0.02597 | 1.121 | 1.107 |
| RTH | 78 | TRQ3_TRV3 | 0.02748 | 0.02564 | 0.02597 | 1.072 | 1.058 |
| RTH | 78 | TRQ5_TRV5 | 0.03308 | 0.02564 | 0.02597 | 1.29 | 1.274 |
| RTH | 78 | TRQ10_TRV10 | 0.03355 | 0.02564 | 0.02597 | 1.308 | 1.292 |
| RTH | 78 | MEDRQ_MEDRV | 0.03027 | 0.02564 | 0.02597 | 1.18 | 1.165 |
| RTH | 195 | RQ_RV | 0.01502 | 0.01026 | 0.01031 | 1.465 | 1.457 |
| RTH | 195 | TQ_BV | 0.01297 | 0.01026 | 0.01031 | 1.264 | 1.258 |
| RTH | 195 | TRQ3_TRV3 | 0.01124 | 0.01026 | 0.01031 | 1.096 | 1.09 |
| RTH | 195 | TRQ5_TRV5 | 0.01436 | 0.01026 | 0.01031 | 1.4 | 1.393 |
| RTH | 195 | TRQ10_TRV10 | 0.01502 | 0.01026 | 0.01031 | 1.465 | 1.457 |
| RTH | 195 | MEDRQ_MEDRV | 0.01325 | 0.01026 | 0.01031 | 1.292 | 1.285 |
| RTH | 390 | RQ_RV | 0.00802 | 0.00513 | 0.00514 | 1.563 | 1.559 |
| RTH | 390 | TQ_BV | 0.00703 | 0.00513 | 0.00514 | 1.371 | 1.367 |
| RTH | 390 | TRQ3_TRV3 | 0.00563 | 0.00513 | 0.00514 | 1.098 | 1.095 |
| RTH | 390 | TRQ5_TRV5 | 0.00736 | 0.00513 | 0.00514 | 1.434 | 1.431 |
| RTH | 390 | TRQ10_TRV10 | 0.00801 | 0.00513 | 0.00514 | 1.562 | 1.558 |
| RTH | 390 | MEDRQ_MEDRV | 0.00699 | 0.00513 | 0.00514 | 1.363 | 1.359 |

### Boundary separation: elasticity with and without the first and last 5 minutes

| root | geom | btag | horizon | estimator | full_session | trimmed_5min | shift_from_trimming |
|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | 1day | E1_a_exp_L1-10 | -0.2741 | -0.3344 | -0.0603 |
| ES | GLOBEX | B0 | 1day | E1_a_exp_L1-5 | -0.2891 | -0.3611 | -0.072 |
| ES | GLOBEX | B0 | 1day | E1_d_model_L1-10 | -1.135 | -1.375 | -0.2401 |
| ES | GLOBEX | B0 | 1day | E1_d_model_L1-5 | -0.9247 | -0.8571 | 0.0676 |
| ES | GLOBEX | B0 | 1day | E2 | -0.2215 | -0.3121 | -0.0906 |
| ES | GLOBEX | B0 | 1day | E4 | -0.6265 | -0.6114 | 0.0152 |
| ES | GLOBEX | B0 | 1day | E4_asS05 | -0.1691 | -0.3188 | -0.1496 |
| ES | GLOBEX | B1 | 1day | E1_a_exp_L1-10 | -0.2737 | -0.3344 | -0.0607 |
| ES | GLOBEX | B1 | 1day | E1_a_exp_L1-5 | -0.2877 | -0.3588 | -0.0712 |
| ES | GLOBEX | B1 | 1day | E1_d_model_L1-10 | -1.135 | -1.353 | -0.2185 |
| ES | GLOBEX | B1 | 1day | E1_d_model_L1-5 | -0.9255 | -0.8758 | 0.0497 |
| ES | GLOBEX | B1 | 1day | E2 | -0.2225 | -0.3112 | -0.0887 |
| ES | GLOBEX | B1 | 1day | E4 | -0.6267 | -0.613 | 0.0137 |
| ES | GLOBEX | B1 | 1day | E4_asS05 | -0.4625 | -0.7383 | -0.2758 |
| ES | RTH | B0 | 1day | E1_a_exp_L1-10 | -0.2869 | -0.3033 | -0.0165 |
| ES | RTH | B0 | 1day | E1_a_exp_L1-5 | -0.3109 | -0.3466 | -0.0357 |
| ES | RTH | B0 | 1day | E1_d_model_L1-10 | -1.624 | -1.547 | 0.0767 |
| ES | RTH | B0 | 1day | E1_d_model_L1-5 | -0.8435 | -0.7691 | 0.0745 |
| ES | RTH | B0 | 1day | E2 | -0.3703 | -0.3811 | -0.0108 |
| ES | RTH | B0 | 1day | E4 | -0.7044 | -0.686 | 0.0184 |
| ES | RTH | B0 | 1day | E4_asS05 | -0.3335 | -0.1562 | 0.1773 |
| ES | RTH | B1 | 1day | E1_a_exp_L1-10 | -0.2907 | -0.3033 | -0.0127 |
| ES | RTH | B1 | 1day | E1_a_exp_L1-5 | -0.3156 | -0.3466 | -0.031 |
| ES | RTH | B1 | 1day | E1_d_model_L1-10 | -1.671 | -1.547 | 0.1239 |
| ES | RTH | B1 | 1day | E1_d_model_L1-5 | -0.8167 | -0.7691 | 0.0476 |
| ES | RTH | B1 | 1day | E2 | -0.3655 | -0.3811 | -0.0156 |
| ES | RTH | B1 | 1day | E4 | -0.7058 | -0.686 | 0.0198 |
| ES | RTH | B1 | 1day | E4_asS05 | -0.3331 | -0.1562 | 0.1769 |
| NQ | GLOBEX | B0 | 1day | E1_a_exp_L1-10 | -0.2887 | -0.3473 | -0.0586 |
| NQ | GLOBEX | B0 | 1day | E1_a_exp_L1-5 | -0.324 | -0.3881 | -0.0642 |
| NQ | GLOBEX | B0 | 1day | E1_d_model_L1-10 | -1.212 | -1.252 | -0.0401 |
| NQ | GLOBEX | B0 | 1day | E1_d_model_L1-5 | -0.6854 | -0.7318 | -0.0464 |
| NQ | GLOBEX | B0 | 1day | E2 | -0.3216 | -0.4007 | -0.0791 |
| NQ | GLOBEX | B0 | 1day | E4 | -0.6028 | -0.5725 | 0.0303 |
| NQ | GLOBEX | B0 | 1day | E4_asS05 | -0.7877 | -0.7279 | 0.0598 |
| NQ | GLOBEX | B1 | 1day | E1_a_exp_L1-10 | -0.2865 | -0.344 | -0.0575 |
| NQ | GLOBEX | B1 | 1day | E1_a_exp_L1-5 | -0.3198 | -0.3878 | -0.068 |
| NQ | GLOBEX | B1 | 1day | E1_d_model_L1-10 | -1.256 | -1.257 | -0.0009 |
| NQ | GLOBEX | B1 | 1day | E1_d_model_L1-5 | -0.7074 | -0.7395 | -0.032 |
| NQ | GLOBEX | B1 | 1day | E2 | -0.292 | -0.4032 | -0.1112 |
| NQ | GLOBEX | B1 | 1day | E4 | -0.6045 | -0.5802 | 0.0243 |
| NQ | GLOBEX | B1 | 1day | E4_asS05 | -0.7868 | -0.7303 | 0.0565 |
| NQ | RTH | B0 | 1day | E1_a_exp_L1-10 | -0.3342 | -0.3724 | -0.0383 |
| NQ | RTH | B0 | 1day | E1_a_exp_L1-5 | -0.3731 | -0.4138 | -0.0407 |
| NQ | RTH | B0 | 1day | E1_d_model_L1-10 | -1.409 | -1.183 | 0.2257 |
| NQ | RTH | B0 | 1day | E1_d_model_L1-5 | -1.014 | -0.8898 | 0.1241 |
| NQ | RTH | B0 | 1day | E2 | -0.3725 | -0.5316 | -0.1591 |
| NQ | RTH | B0 | 1day | E4 | -0.7076 | -0.6892 | 0.0184 |
| NQ | RTH | B0 | 1day | E4_asS05 | -0.7921 | -0.7558 | 0.0363 |
| NQ | RTH | B1 | 1day | E1_a_exp_L1-10 | -0.3326 | -0.3724 | -0.0398 |
| NQ | RTH | B1 | 1day | E1_a_exp_L1-5 | -0.3722 | -0.4138 | -0.0416 |
| NQ | RTH | B1 | 1day | E1_d_model_L1-10 | -1.399 | -1.183 | 0.2156 |
| NQ | RTH | B1 | 1day | E1_d_model_L1-5 | -0.977 | -0.8898 | 0.0873 |
| NQ | RTH | B1 | 1day | E2 | -0.4862 | -0.5316 | -0.0454 |
| NQ | RTH | B1 | 1day | E4 | -0.7089 | -0.6892 | 0.0196 |
| NQ | RTH | B1 | 1day | E4_asS05 | -0.794 | -0.758 | 0.036 |

Median elasticity shift from trimming the first and last 5 minutes: -0.0237; maximum absolute shift 4.5414.

First and last sub-bar share of window RV at every M (ES/B0; full table in `phase4_grid_index.csv`):

| geom | horizon | M | mean_first_share | mean_last_share |
|---|---|---|---|---|
| GLOBEX | 1day | 5 | 0.1212 | 0.2795 |
| GLOBEX | 1day | 6 | 0.1032 | 0.241 |
| GLOBEX | 1day | 10 | 0.0564 | 0.1523 |
| GLOBEX | 1day | 12 | 0.0437 | 0.1263 |
| GLOBEX | 1day | 23 | 0.0241 | 0.0299 |
| GLOBEX | 1day | 46 | 0.0159 | 0.0104 |
| GLOBEX | 1day | 138 | 0.0081 | 0.0029 |
| GLOBEX | 1day | 345 | 0.0039 | 0.0014 |
| RTH | 1day | 5 | 0.2958 | 0.2158 |
| RTH | 1day | 6 | 0.2637 | 0.185 |
| RTH | 1day | 10 | 0.1784 | 0.1271 |
| RTH | 1day | 13 | 0.1419 | 0.1091 |
| RTH | 1day | 26 | 0.0818 | 0.0703 |
| RTH | 1day | 78 | 0.0293 | 0.0293 |
| RTH | 1day | 195 | 0.0089 | 0.016 |
| RTH | 1h | 4 | 0.2653 | 0.2304 |
| RTH | 1h | 5 | 0.2147 | 0.1885 |
| RTH | 1h | 6 | 0.1828 | 0.1568 |
| RTH | 1h | 10 | 0.1151 | 0.0944 |
| RTH | 1h | 12 | 0.0987 | 0.0775 |
| RTH | 1h | 15 | 0.0791 | 0.0633 |
| RTH | 1h | 20 | 0.0605 | 0.0489 |
| RTH | 1h | 30 | 0.0428 | 0.0339 |
| RTH | 1h | 60 | 0.0217 | 0.0212 |
| RTH | 30min | 5 | 0.2201 | 0.1956 |
| RTH | 30min | 6 | 0.1868 | 0.1616 |
| RTH | 30min | 10 | 0.1172 | 0.1033 |
| RTH | 30min | 15 | 0.0834 | 0.0734 |
| RTH | 30min | 30 | 0.043 | 0.048 |
| GLOBEX | 1day | 1379 | 0.0017 | 0.0006 |
| RTH | 1day | 389 | 0.0085 | 0.0114 |

## Phase 6, microstructure noise

### 6a. Arithmetic on held quantities

S03 N1/N2 artifacts, all 48 cells (`phase6_s03_noise_full.csv`). Summary:

- **Negative omega^2 estimates: 8 of 48 cells under N1** (minimum -8.902e-09), 0 under N2. A negative variance estimate is not interpretable as a variance.
- Signature-plot linearity R^2: median 0.539, range 9.86e-06 to 0.991; **20 of 48 cells below 0.5**.
- omega^2 (N1) median 3.073e-09, range -8.902e-09 to 2.699e-08.

The 8 cells with negative N1 estimates:

| root | geom | group | omega2_N1 | NSR_N1 | signature_R2 | n_days |
|---|---|---|---|---|---|---|
| ES | RTH | y2022 | -1.692e-11 | -1.235e-07 | 9.86e-06 | 238 |
| NQ | GLOBEX | y2022 | -1.365e-09 | -3.583e-06 | 0.1042 | 238 |
| NQ | GLOBEX | terc3 | -4.903e-10 | -1.179e-06 | 0.01809 | 634 |
| NQ | RTH | y2016 | -3.173e-09 | -4.596e-05 | 0.2823 | 239 |
| NQ | RTH | y2021 | -6.872e-10 | -8.072e-06 | 0.01272 | 239 |
| NQ | RTH | y2022 | -3.153e-09 | -1.305e-05 | 0.1155 | 238 |
| NQ | RTH | y2023 | -3.087e-09 | -3.533e-05 | 0.5294 | 236 |
| NQ | RTH | terc3 | -8.902e-09 | -3.464e-05 | 0.4597 | 634 |

**Resolution floor of the N1 procedure as run.** N1 regresses the cross-day MEAN of RV_M on M over the five S03 grid points. The smallest slope distinguishable from zero is set by the standard error of those means: with mean RV of order 1e-4 and roughly 1,900 sessions of a strongly right-skewed series, the standard error of each mean is of order 1e-6, and the M-range is a few hundred, so slopes below roughly 1e-8 to 1e-9 - i.e. omega^2 below roughly 5e-9 - are not separable from zero by this procedure. The measured median omega^2 (N1) of 3.07e-09 sits at that floor, which is why 8 cells return negative values: the estimator is resolving noise below its own resolution.

Implied relative RV bias 2*M*omega^2/IV at every extended grid point, with the range induced by the spread of S03 omega^2 estimates across that cell's groups:

| geom | M | omega2_N1 | bias_2Momega2_over_IV | bias_min_across_estimates | bias_max_across_estimates | trigamma |
|---|---|---|---|---|---|---|
| GLOBEX | 5 | 0 | 0.000327 | 7.6e-05 | 0.00116 | 0.4904 |
| GLOBEX | 6 | 0 | 0.000392 | 9.1e-05 | 0.001393 | 0.3949 |
| GLOBEX | 10 | 0 | 0.000653 | 0.000152 | 0.002321 | 0.2213 |
| GLOBEX | 12 | 0 | 0.000784 | 0.000183 | 0.002785 | 0.1813 |
| GLOBEX | 23 | 0 | 0.001503 | 0.000351 | 0.005338 | 0.09085 |
| GLOBEX | 46 | 0 | 0.003005 | 0.000701 | 0.01068 | 0.04444 |
| GLOBEX | 138 | 0 | 0.009015 | 0.002104 | 0.03203 | 0.0146 |
| GLOBEX | 345 | 0 | 0.02254 | 0.00526 | 0.08007 | 0.005814 |
| GLOBEX | 1379 | 0 | 0.09009 | 0.02103 | 0.3201 | 0.001451 |
| RTH | 5 | 0 | 0.000901 | -2e-06 | 0.003834 | 0.4904 |
| RTH | 6 | 0 | 0.001081 | -3e-06 | 0.004601 | 0.3949 |
| RTH | 10 | 0 | 0.001802 | -5e-06 | 0.007669 | 0.2213 |
| RTH | 13 | 0 | 0.002343 | -6e-06 | 0.009969 | 0.1663 |
| RTH | 26 | 0 | 0.004686 | -1.2e-05 | 0.01994 | 0.07996 |
| RTH | 78 | 0 | 0.01406 | -3.7e-05 | 0.05982 | 0.02597 |
| RTH | 195 | 0 | 0.03515 | -9.4e-05 | 0.1495 | 0.01031 |
| RTH | 389 | 0 | 0.07012 | -0.000187 | 0.2983 | 0.005155 |

Implied inflation of Var(log RV_M) and the refitted elasticity after subtracting it:

| root | geom | btag | estimator | elasticity_raw | elasticity_noise_corrected | shift | mean_delta | delta_share_of_var |
|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | E1_a_exp_L1-5 | -0.2891 | -0.3199 | -0.03084 | 0.00381 | 0.00353 |
| ES | GLOBEX | B0 | E1_a_exp_L1-10 | -0.2741 | -0.3019 | -0.02781 | 0.00381 | 0.00353 |
| ES | GLOBEX | B0 | E1_d_model_L1-5 | -0.9247 | -0.9682 | -0.0435 | 0.00381 | 0.00353 |
| ES | GLOBEX | B0 | E1_d_model_L1-10 | -1.134 | -1.135 | -0.00063 | 0.00381 | 0.00353 |
| ES | GLOBEX | B0 | E2 | -0.2215 | -0.248 | -0.02647 | 0.00381 | 0.00353 |
| ES | GLOBEX | B0 | E4 | -0.6265 | -0.6635 | -0.037 | 0.00381 | 0.00353 |
| ES | GLOBEX | B0 | E4_asS05 | -0.1691 | -0.01344 | 0.1557 | 0.00381 | 0.00353 |
| ES | GLOBEX | B1 | E1_a_exp_L1-5 | -0.2877 | -0.3196 | -0.03196 | 0.00395 | 0.00364 |
| ES | GLOBEX | B1 | E1_a_exp_L1-10 | -0.2737 | -0.3024 | -0.02877 | 0.00395 | 0.00364 |
| ES | GLOBEX | B1 | E1_d_model_L1-5 | -0.9255 | -0.9535 | -0.02808 | 0.00395 | 0.00364 |
| ES | GLOBEX | B1 | E1_d_model_L1-10 | -1.135 | -1.135 | -0.00065 | 0.00395 | 0.00364 |
| ES | GLOBEX | B1 | E2 | -0.2225 | -0.2497 | -0.02718 | 0.00395 | 0.00364 |
| ES | GLOBEX | B1 | E4 | -0.6267 | -0.6681 | -0.04139 | 0.00395 | 0.00364 |
| ES | GLOBEX | B1 | E4_asS05 | -0.4625 | -0.4513 | 0.01125 | 0.00395 | 0.00364 |
| NQ | GLOBEX | B0 | E1_a_exp_L1-5 | -0.324 | -0.3303 | -0.00633 | 0.0009 | 0.00083 |
| NQ | GLOBEX | B0 | E1_a_exp_L1-10 | -0.2887 | -0.294 | -0.00536 | 0.0009 | 0.00083 |
| NQ | GLOBEX | B0 | E1_d_model_L1-5 | -0.6854 | -0.7555 | -0.07013 | 0.0009 | 0.00083 |
| NQ | GLOBEX | B0 | E1_d_model_L1-10 | -1.212 | -1.212 | -0.00024 | 0.0009 | 0.00083 |
| NQ | GLOBEX | B0 | E2 | -0.3216 | -0.3284 | -0.00687 | 0.0009 | 0.00083 |
| NQ | GLOBEX | B0 | E4 | -0.6028 | -0.8647 | -0.2619 | 0.0009 | 0.00083 |
| NQ | GLOBEX | B0 | E4_asS05 | -0.7877 | -0.7433 | 0.04441 | 0.0009 | 0.00083 |
| NQ | GLOBEX | B1 | E1_a_exp_L1-5 | -0.3198 | -0.3264 | -0.00663 | 0.00094 | 0.00087 |
| NQ | GLOBEX | B1 | E1_a_exp_L1-10 | -0.2865 | -0.2921 | -0.00561 | 0.00094 | 0.00087 |
| NQ | GLOBEX | B1 | E1_d_model_L1-5 | -0.7074 | -0.7866 | -0.07918 | 0.00094 | 0.00087 |
| NQ | GLOBEX | B1 | E1_d_model_L1-10 | -1.256 | -1.257 | -0.00028 | 0.00094 | 0.00087 |
| NQ | GLOBEX | B1 | E2 | -0.292 | -0.299 | -0.00706 | 0.00094 | 0.00087 |
| NQ | GLOBEX | B1 | E4 | -0.6045 | -0.9399 | -0.3354 | 0.00094 | 0.00087 |
| NQ | GLOBEX | B1 | E4_asS05 | -0.7868 | -0.7436 | 0.04324 | 0.00094 | 0.00087 |
| ES | RTH | B0 | E1_a_exp_L1-5 | -0.3109 | -0.3381 | -0.02727 | 0.00399 | 0.00351 |
| ES | RTH | B0 | E1_a_exp_L1-10 | -0.2869 | -0.31 | -0.02315 | 0.00399 | 0.00351 |
| ES | RTH | B0 | E1_d_model_L1-5 | -0.8435 | -0.9279 | -0.08433 | 0.00399 | 0.00351 |
| ES | RTH | B0 | E1_d_model_L1-10 | -1.624 | -1.633 | -0.00939 | 0.00399 | 0.00351 |
| ES | RTH | B0 | E2 | -0.3703 | -0.4115 | -0.04117 | 0.00399 | 0.00351 |
| ES | RTH | B0 | E4 | -0.7044 | -0.8278 | -0.1233 | 0.00399 | 0.00351 |
| ES | RTH | B0 | E4_asS05 | -0.3335 | -0.4509 | -0.1174 | 0.00399 | 0.00351 |
| ES | RTH | B1 | E1_a_exp_L1-5 | -0.3156 | -0.3438 | -0.02816 | 0.00419 | 0.00366 |
| ES | RTH | B1 | E1_a_exp_L1-10 | -0.2907 | -0.3146 | -0.02391 | 0.00419 | 0.00366 |
| ES | RTH | B1 | E1_d_model_L1-5 | -0.8167 | -0.9119 | -0.09528 | 0.00419 | 0.00366 |
| ES | RTH | B1 | E1_d_model_L1-10 | -1.671 | -1.681 | -0.00976 | 0.00419 | 0.00366 |
| ES | RTH | B1 | E2 | -0.3655 | -0.4091 | -0.04364 | 0.00419 | 0.00366 |
| ES | RTH | B1 | E4 | -0.7058 | -0.8398 | -0.134 | 0.00419 | 0.00366 |
| ES | RTH | B1 | E4_asS05 | -0.3331 | -0.4839 | -0.1507 | 0.00419 | 0.00366 |
| NQ | RTH | B0 | E1_a_exp_L1-5 | -0.3731 | -0.3746 | -0.0015 | 0.00022 | 0.0002 |
| NQ | RTH | B0 | E1_a_exp_L1-10 | -0.3342 | -0.3355 | -0.00128 | 0.00022 | 0.0002 |
| NQ | RTH | B0 | E1_d_model_L1-5 | -1.014 | -1.044 | -0.0303 | 0.00022 | 0.0002 |
| NQ | RTH | B0 | E1_d_model_L1-10 | -1.409 | -1.409 | -0.00013 | 0.00022 | 0.0002 |
| NQ | RTH | B0 | E2 | -0.3725 | -0.3755 | -0.00306 | 0.00022 | 0.0002 |
| NQ | RTH | B0 | E4 | -0.7077 | -0.7268 | -0.0192 | 0.00022 | 0.0002 |
| NQ | RTH | B0 | E4_asS05 | -0.7921 | -0.8301 | -0.038 | 0.00022 | 0.0002 |
| NQ | RTH | B1 | E1_a_exp_L1-5 | -0.3722 | -0.3738 | -0.00156 | 0.00023 | 0.00021 |
| NQ | RTH | B1 | E1_a_exp_L1-10 | -0.3326 | -0.334 | -0.00134 | 0.00023 | 0.00021 |
| NQ | RTH | B1 | E1_d_model_L1-5 | -0.977 | -1.003 | -0.02642 | 0.00023 | 0.00021 |
| NQ | RTH | B1 | E1_d_model_L1-10 | -1.399 | -1.399 | -0.00013 | 0.00023 | 0.00021 |
| NQ | RTH | B1 | E2 | -0.4863 | -0.4895 | -0.00328 | 0.00023 | 0.00021 |
| NQ | RTH | B1 | E4 | -0.7089 | -0.7295 | -0.02062 | 0.00023 | 0.00021 |
| NQ | RTH | B1 | E4_asS05 | -0.794 | -0.8344 | -0.04039 | 0.00023 | 0.00021 |

**Decision recorded: 6a does NOT settle the question, so 6b was run.** The implied noise inflation is 0.21% of Var(log RV) on average, and correcting for it moves the fitted elasticity by a mean -0.0349 (maximum absolute 0.3354). The elasticities remain far from -1 for E1_a, E2 and E4 after the correction, so the departure is not accounted for by microstructure noise at the measured magnitude.

### 6b. Reference-based reliability

lambda_M = Var(log ref) / Var(log RV_M) with `ref` the per-session realized kernel (bandwidth H = 0.97 xi^(4/5) n^(3/5), the DECISIONS item 16 rule) or two-scale estimator. Note the invariance PRODUCT is constant by construction here (the numerator carries no M), so the informative quantity is the elasticity of the excess variance:

| root | geom | btag | reference | var_log_ref | elasticity | elasticity_r2 | n_dropped | n_ref_nonpositive |
|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | kernel | 1.289 | -1.01 | 0.9708 | 2 | 0 |
| ES | GLOBEX | B0 | tsrv | 1.289 | -1.014 | 0.9703 | 2 | 0 |
| ES | GLOBEX | B1 | kernel | 1.294 | -0.9693 | 0.974 | 2 | 0 |
| ES | GLOBEX | B1 | tsrv | 1.294 | -0.969 | 0.974 | 2 | 0 |
| NQ | GLOBEX | B0 | kernel | 1.153 | -0.8951 | 0.9898 | 2 | 0 |
| NQ | GLOBEX | B0 | tsrv | 1.154 | -0.8962 | 0.9898 | 2 | 0 |
| NQ | GLOBEX | B1 | kernel | 1.158 | -0.8681 | 0.9932 | 2 | 0 |
| NQ | GLOBEX | B1 | tsrv | 1.158 | -0.8682 | 0.9932 | 2 | 0 |
| ES | RTH | B0 | kernel | 1.308 | -1.292 | 0.9899 | 3 | 0 |
| ES | RTH | B0 | tsrv | 1.322 | -1.406 | 0.984 | 3 | 0 |
| ES | RTH | B1 | kernel | 1.319 | -1.34 | 0.988 | 3 | 0 |
| ES | RTH | B1 | tsrv | 1.318 | -1.334 | 0.9883 | 3 | 0 |
| NQ | RTH | B0 | kernel | 1.128 | -1.663 | 0.9777 | 2 | 0 |
| NQ | RTH | B0 | tsrv | 1.137 | -1.381 | 0.9906 | 3 | 0 |
| NQ | RTH | B1 | kernel | 1.135 | -1.81 | 0.9658 | 2 | 0 |
| NQ | RTH | B1 | tsrv | 1.135 | -1.788 | 0.9677 | 2 | 0 |

Per-grid-point detail is in `phase6b_reference_lambda.csv`.

### Var(log RV_M) against M and interior minima in Var(log eps)

0 of 112 (cell, horizon, estimator) profiles have an interior minimum inside the grid:


ES/GLOBEX/B0/1day under E2, the cell that turns between M=138 and M=1380 in the S05 output:

| M | var_log_rv | lam | var_log_eps |
|---|---|---|---|
| 5 | 2.023 | 1.111 | -0.2242 |
| 6 | 2.05 | 0.6312 | 0.7562 |
| 10 | 1.708 | 0.7004 | 0.5118 |
| 12 | 1.697 | 0.7244 | 0.4678 |
| 23 | 1.513 | 0.7859 | 0.324 |
| 46 | 1.42 | 0.824 | 0.25 |
| 138 | 1.312 | 0.8578 | 0.1866 |
| 345 | 1.221 | 0.8615 | 0.1691 |
| 1379 | 1.043 | 0.8455 | 0.1611 |

## Phase 7, jump contribution

lambda under RV and under TRV3, elasticity and grid-invariance ratio recomputed under truncation (per-grid-point lambda values in `phase5_lambda_grid.csv`):

| root | geom | btag | estimator | elasticity_RV | elasticity_TRV3 | elasticity_shift_TRV3_minus_RV | ratio_max_min_RV | ratio_max_min_TRV3 | moves_toward_minus1 |
|---|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | E1_a_exp_L1-10 | -0.2741 | -1.105 | -0.8305 | 1.361 | 2.198 | True |
| ES | GLOBEX | B0 | E1_a_exp_L1-5 | -0.2891 | -1.106 | -0.8166 | 1.373 | 1.58 | True |
| ES | GLOBEX | B0 | E1_d_model_L1-10 | -1.135 | -5.94 | -4.805 | 1.084 | 2.191 | False |
| ES | GLOBEX | B0 | E1_d_model_L1-5 | -0.9247 | -3.14 | -2.215 | 1.361 | 2.208 | False |
| ES | GLOBEX | B0 | E2 | -0.2215 | -0.9955 | -0.774 | 1.468 | 2.549 | True |
| ES | GLOBEX | B0 | E4 | -0.6265 | -0.1691 | 0.4574 | 1.683 | 237.1 | False |
| ES | GLOBEX | B0 | E4_asS05 | -0.1691 | -0.1691 | 0 | 1.968 | 237.1 | False |
| ES | GLOBEX | B1 | E1_a_exp_L1-10 | -0.2737 | -0.75 | -0.4763 | 1.363 | 1.434 | True |
| ES | GLOBEX | B1 | E1_a_exp_L1-5 | -0.2877 | -0.7953 | -0.5076 | 1.377 | 1.554 | True |
| ES | GLOBEX | B1 | E1_d_model_L1-10 | -1.135 | -4.177 | -3.042 | 1.077 | 1.652 | False |
| ES | GLOBEX | B1 | E1_d_model_L1-5 | -0.9255 | -2.58 | -1.655 | 1.365 | 1.634 | False |
| ES | GLOBEX | B1 | E2 | -0.2225 | -0.6219 | -0.3994 | 1.464 | 4.69 | True |
| ES | GLOBEX | B1 | E4 | -0.6267 | -0.4625 | 0.1642 | 1.691 | 236.8 | False |
| ES | GLOBEX | B1 | E4_asS05 | -0.4625 | -0.4625 | 0 | 1.934 | 236.8 | False |
| ES | RTH | B0 | E1_a_exp_L1-10 | -0.2869 | -0.8794 | -0.5926 | 1.284 | 1.388 | True |
| ES | RTH | B0 | E1_a_exp_L1-5 | -0.3109 | -0.918 | -0.6071 | 1.285 | 1.335 | True |
| ES | RTH | B0 | E1_d_model_L1-10 | -1.624 | -6.883 | -5.259 | 1.112 | 1.09 | False |
| ES | RTH | B0 | E1_d_model_L1-5 | -0.8435 | -2.025 | -1.181 | 1.274 | 1.29 | False |
| ES | RTH | B0 | E2 | -0.3703 | -0.9212 | -0.5509 | 1.308 | 1.308 | True |
| ES | RTH | B0 | E4 | -0.7044 | -0.3335 | 0.3709 | 1.521 | 220.7 | False |
| ES | RTH | B0 | E4_asS05 | -0.3335 | -0.3335 | 0 | 1.794 | 220.7 | False |
| ES | RTH | B1 | E1_a_exp_L1-10 | -0.2907 | -0.8777 | -0.587 | 1.261 | 1.411 | True |
| ES | RTH | B1 | E1_a_exp_L1-5 | -0.3156 | -0.9261 | -0.6105 | 1.278 | 1.31 | True |
| ES | RTH | B1 | E1_d_model_L1-10 | -1.671 | -6.234 | -4.563 | 1.11 | 1.289 | False |
| ES | RTH | B1 | E1_d_model_L1-5 | -0.8167 | -1.923 | -1.106 | 1.267 | 1.266 | False |
| ES | RTH | B1 | E2 | -0.3655 | -0.9257 | -0.5602 | 1.343 | 1.343 | True |
| ES | RTH | B1 | E4 | -0.7058 | -0.3331 | 0.3727 | 1.531 | 219.9 | False |
| ES | RTH | B1 | E4_asS05 | -0.3331 | -0.3331 | 0 | 1.802 | 219.9 | False |
| NQ | GLOBEX | B0 | E1_a_exp_L1-10 | -0.2887 | -0.4187 | -0.13 | 1.137 | 1.093 | True |
| NQ | GLOBEX | B0 | E1_a_exp_L1-5 | -0.324 | -0.4645 | -0.1406 | 1.109 | 1.088 | True |
| NQ | GLOBEX | B0 | E1_d_model_L1-10 | -1.212 | -1.605 | -0.3932 | 1.048 | 1.088 | False |
| NQ | GLOBEX | B0 | E1_d_model_L1-5 | -0.6854 | -1.446 | -0.7609 | 1.117 | 1.149 | False |
| NQ | GLOBEX | B0 | E2 | -0.3216 | -0.3365 | -0.0149 | 1.23 | 1.23 | True |
| NQ | GLOBEX | B0 | E4 | -0.6028 | -0.7877 | -0.1849 | 1.494 | 1.945 | True |
| NQ | GLOBEX | B0 | E4_asS05 | -0.7877 | -0.7877 | 0 | 1.547 | 1.945 | False |
| NQ | GLOBEX | B1 | E1_a_exp_L1-10 | -0.2865 | -0.4156 | -0.1292 | 1.142 | 1.1 | True |
| NQ | GLOBEX | B1 | E1_a_exp_L1-5 | -0.3198 | -0.4623 | -0.1425 | 1.127 | 1.082 | True |
| NQ | GLOBEX | B1 | E1_d_model_L1-10 | -1.256 | -1.607 | -0.3511 | 1.055 | 1.081 | False |
| NQ | GLOBEX | B1 | E1_d_model_L1-5 | -0.7074 | -1.339 | -0.6317 | 1.135 | 1.143 | False |
| NQ | GLOBEX | B1 | E2 | -0.292 | -0.3179 | -0.0259 | 1.312 | 1.312 | True |
| NQ | GLOBEX | B1 | E4 | -0.6045 | -0.7868 | -0.1823 | 1.484 | 1.925 | True |
| NQ | GLOBEX | B1 | E4_asS05 | -0.7868 | -0.7868 | 0 | 1.544 | 1.925 | False |
| NQ | RTH | B0 | E1_a_exp_L1-10 | -0.3342 | -0.4363 | -0.1021 | 1.132 | 1.081 | True |
| NQ | RTH | B0 | E1_a_exp_L1-5 | -0.3731 | -0.4926 | -0.1195 | 1.103 | 1.093 | True |
| NQ | RTH | B0 | E1_d_model_L1-10 | -1.409 | -2.179 | -0.7698 | 1.065 | 1.093 | False |
| NQ | RTH | B0 | E1_d_model_L1-5 | -1.014 | -1.335 | -0.3208 | 1.072 | 1.154 | False |
| NQ | RTH | B0 | E2 | -0.3725 | -0.3331 | 0.0394 | 1.57 | 1.57 | False |
| NQ | RTH | B0 | E4 | -0.7076 | -0.7921 | -0.0844 | 1.45 | 1.811 | True |
| NQ | RTH | B0 | E4_asS05 | -0.7921 | -0.7921 | 0 | 1.522 | 1.811 | False |
| NQ | RTH | B1 | E1_a_exp_L1-10 | -0.3326 | -0.4389 | -0.1063 | 1.133 | 1.08 | True |
| NQ | RTH | B1 | E1_a_exp_L1-5 | -0.3722 | -0.4816 | -0.1094 | 1.103 | 1.095 | True |
| NQ | RTH | B1 | E1_d_model_L1-10 | -1.399 | -2.041 | -0.6423 | 1.064 | 1.047 | False |
| NQ | RTH | B1 | E1_d_model_L1-5 | -0.977 | -1.302 | -0.3244 | 1.074 | 1.095 | False |
| NQ | RTH | B1 | E2 | -0.4862 | -0.3999 | 0.0863 | 1.185 | 1.185 | False |
| NQ | RTH | B1 | E4 | -0.7089 | -0.794 | -0.0851 | 1.452 | 1.845 | True |
| NQ | RTH | B1 | E4_asS05 | -0.794 | -0.794 | 0 | 1.525 | 1.845 | False |

**The elasticity moves toward -1 under truncation in 32 of 112 (cell, horizon, estimator) combinations**, by a mean shift of -0.828 and a maximum of 5.309. The shift is uniformly negative, so estimators already below -1 under RV are carried further past it while those above -1 are carried toward it.

Share of RV removed by truncation at each M, beside the elasticity change (ES/B0 shown; full table `phase7_truncation_share.csv`):

| geom | horizon | M | trv_over_rv | share_rv_removed |
|---|---|---|---|---|
| GLOBEX | 1day | 5 | 0.8964 | 0.1036 |
| GLOBEX | 1day | 6 | 0.8862 | 0.1138 |
| GLOBEX | 1day | 10 | 0.881 | 0.119 |
| GLOBEX | 1day | 12 | 0.8607 | 0.1394 |
| GLOBEX | 1day | 23 | 0.814 | 0.186 |
| GLOBEX | 1day | 46 | 0.7617 | 0.2383 |
| GLOBEX | 1day | 138 | 0.7149 | 0.2851 |
| GLOBEX | 1day | 345 | 0.7046 | 0.2954 |
| GLOBEX | 1day | 1379 | 0.7062 | 0.2938 |
| RTH | 1day | 5 | 0.9015 | 0.09846 |
| RTH | 1day | 6 | 0.9159 | 0.08415 |
| RTH | 1day | 10 | 0.9152 | 0.08484 |
| RTH | 1day | 13 | 0.9109 | 0.08909 |
| RTH | 1day | 26 | 0.8851 | 0.1149 |
| RTH | 1day | 78 | 0.8481 | 0.1519 |
| RTH | 1day | 195 | 0.8284 | 0.1716 |
| RTH | 1day | 389 | 0.8259 | 0.1741 |
| RTH | 1h | 4 | 0.9285 | 0.07154 |
| RTH | 1h | 5 | 0.9316 | 0.06837 |
| RTH | 1h | 6 | 0.9383 | 0.06172 |
| RTH | 1h | 10 | 0.9384 | 0.06163 |
| RTH | 1h | 12 | 0.9381 | 0.06187 |
| RTH | 1h | 15 | 0.9308 | 0.06917 |
| RTH | 1h | 20 | 0.9243 | 0.0757 |
| RTH | 1h | 30 | 0.9144 | 0.08555 |
| RTH | 1h | 60 | 0.9035 | 0.09648 |
| RTH | 30min | 5 | 0.9262 | 0.07383 |
| RTH | 30min | 6 | 0.9324 | 0.06764 |
| RTH | 30min | 10 | 0.9321 | 0.06789 |
| RTH | 30min | 15 | 0.9282 | 0.0718 |
| RTH | 30min | 30 | 0.9183 | 0.08172 |
