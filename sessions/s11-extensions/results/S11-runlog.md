# Session 11 run log — defect correction, extensions, financial applications

Date 2026-08-19. No new data acquired. No prior artifact modified or deleted.
Nothing committed to git (the tree is not a git repository).

## Environment

| field | value |
|---|---|
| interpreter | `~/venvs/obs-space-vol/bin/python` |
| realpath | `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13` |
| Python | 3.13.13 |
| numpy | 2.5.2 (gate requires exactly this) |
| pandas | 3.0.5 (gate requires exactly this) |
| under a synced path | no |
| gate | PASS, Phase 0, before any work |

DECISIONS items 66–85 verified present by grep at lines 398, 405, 413, 419, 424,
433, 437, 442, 445, 454, 457, 466, 469, 474, 485, 490, 497, 502, 510, 515
(20 of 20). Items 86–94 appended once and verified persistent by grep at lines
523, 531, 533, 538, 543, 547, 553, 557, 562, per item 77. DECISIONS.md grew from
37,816 bytes / 519 lines to 41,139 bytes / 563 lines.

## Wall clock per phase

| phase | wall clock | source |
|---|---|---|
| 0 — verification, append, gate, directories | ~3 min | interactive |
| 1 — floor correction, partition, holdout re-evaluation | 6.2 s (in sample 4.4 s, holdout 1.8 s) | `phase1_summary.json` |
| 2 — grid span | 2.0 s | `phase2345_timers.json` |
| 3 — time trend | <0.1 s | `phase2345_timers.json` |
| 4 — reliability vs degradation | <0.1 s | `phase2345_timers.json` |
| 5 — volatility of volatility | <0.1 s | `phase2345_timers.json` |
| 6 — measured ratio 5.7 s, σ_w calibration 144.6 s, A6 sweep 51.4 s | 201.7 s | `phase6_determination.json` |
| 7 — proxy specification test, 54 fits × 2,000 resamples | 122 s | `phase7_summary.json` |
| 8 — K4 risk-limit breaches | 2.1 s | `phase8910_summary.json` |
| 9 — K5 combination weights | 13.9 s | `phase8910_summary.json` |
| 10 — K6 convexity | <0.1 s | `phase8910_summary.json` |
| 11 — report, spec update, runlog | ~15 min | interactive |

Total compute 5 min 48 s. Total session wall clock including code authoring and
inspection, roughly 80 minutes, inside the 60–100 minute expectation. Phases 6
and 7 ran concurrently as separate processes. The bottleneck was Phase 6's σ_w
bisection (24 iterations × 24 (root, geom, H) combinations on 400-session panels)
followed by the 120-panel sweep at full dimensions.

## Seeds and their derivation

| use | master | derivation | count |
|---|---|---|---|
| Phase 6, σ_w bisection | 20260823 | `SeedSequence(20260823).generate_state(64)`, consumed in (geom, root, H) order | 24 |
| Phase 6, A6 sweep | 20260824 | `SeedSequence(20260824).spawn(120)`, consumed in (geom, root, H, seed index) order | 120 |
| Phase 7, bootstrap on b | 20260825 | `SeedSequence(20260825).generate_state(128)`, consumed in (cell, proxy) order | 54 |

Every seed is logged: Phase 6 calibration in `phase6_calibration.csv`, Phase 6
sweep in `phase6_a6cal_raw.csv` and in each `cache/a6cal_*.npz`, Phase 7 in each
`cache/p7boot_*.npz`. Between-seed dispersion is reported as `b_sd` on every
synthetic row, five seeds per (root, geom, H) setting, 120 runs in total.

Phases 1–5 and 8–10 draw no random numbers: they are deterministic recomputations
on existing panels and on the S10 bootstrap already persisted.

## Constants and their sources

| constant | value | source |
|---|---|---|
| retention threshold | R² ≥ 0.02 | DECISIONS item 70 |
| extended grid | per (geom, horizon) | S08 `phase234.py` GRID |
| five-minute equivalent M | 276 / 78 / 12 / 6 | S05, via S09 FIVEMIN |
| DIMS | GLOBEX (1953, 1380), RTH (1901, 390) | S05E `run5e.py` |
| VAR_LOG_IV | 1.02 | S05E, DECISIONS item 36 |
| σ_w assumed by S10 | √1.02 = 1.0100 | S10 Phase 6 |
| σ_w calibrated here | 1.495 to 4.805 | item 89, this session, from RQ/RV² |
| constant-volatility value of RQ/RV² | exactly 1 | RQ = (M/3)Σr⁴ → σ⁴, RV → σ² |
| Hurst sweep | 0.05, 0.10, 0.20, 0.30, 0.45, 0.50 | session instruction |
| kernel bandwidth | H* = 3.5134·ξ^(4/5)·n^(3/5) | BNHLS (2009), via S02 `kernel_H` |
| two-scale subsample count | K = (12ω⁴/IQ)^(1/3)·n^(2/3) | ZMA (2005) eq. 63, via S02 `tsrv_K` |
| volatility target | 10% annualised, daily rebalance | DECISIONS item 68 |
| leverage cap | 2.0× | DECISIONS item 92, fixed before any result |
| stop-out | realized volatility > 1.5× target | DECISIONS item 92 |
| cost sweep | 0.5, 1.0, 2.0, 4.0 ticks per leg | DECISIONS item 69 |
| tick values | ES $12.50, NQ $5.00 | SCOPE section 4, via item 69 |
| convexity relation | K_vol ≈ √E[V] − Var(V)/(8·E[V]^{3/2}) | Brockhaus and Long (2000), 2nd order |
| variance-swap strike for quoting | 20% annualised | chosen here purely to express the adjustment in volatility points |
| K4/K5/K6 thresholds | 1%, 1 bp / 0.02, 5% / 5% | DECISIONS items 92, 93, 94 |
| bootstrap resamples | 2,000 | session instruction |

## Code path and the two re-executions

Imported unmodified: `phase5_signals.build`, `phase5_signals.volume_series`,
`phase6_holdout.wins`, `phase6_holdout.feature_block`, `phase2_rerun8.series`,
`phase2_rerun8.tradeable_ext`, `partde.forecasts`, `partde.har_X`,
`parta.quart_suite`, `proxies_robust.{p1_rv, p2_tsrv, p3_kernel_flattop,
kernel_H, tsrv_K, rq}`, `fbm.{CirculantEmbedding, fgn_acf}`,
`phase6_arm_a6.make_a6`, and the S10 `common` fitting and windowing module.

Two things are re-executed rather than imported, both disclosed:

1. **The signal regression driver.** The floor defect is in
   `phase5_signals.main` and `phase6_holdout.main`, which are prior artifacts and
   were not edited. Their predictor builders return raw values and are imported;
   only the driver is re-executed with `logdrop()` in place of
   `np.log(np.maximum(v, 1e-300))`. This is the S04-build precedent.
2. **`ho_series`.** S07's `series()` has a hard-coded panel path and cannot
   address the holdout panel. `ho_series` re-executes its body line-for-line with
   the panel supplied as an argument. **Equivalence is asserted at run time**: it
   is run on the in-sample panel and compared byte-for-byte against `series()`
   across rv, bv, rq, park, gk and ret for all four cells, and the run halts if
   any field differs. It passed on all 24 comparisons before any holdout number
   was computed.

No synthetic arm required reimplementation, so the report-and-halt condition was
not triggered.

## Holdout reads

Three, all within the stop condition, none changing any parameter, threshold,
rule or specification:

1. Phase 1, the three defect-touched candidates only (item 88), from the S09
   cached holdout panels.
2. Phase 8, the K4 application, from the same cached panels.
3. Phase 9, the K5 application, from the same cached panels.

No holdout extraction was re-run; every holdout read uses `ho_panel_*.npz` and
`ho_bars_*.parquet` built in S09. No fourth read was required, so the
report-and-halt condition was not triggered.

## Fit diagnostics

Condition number, parameter correlation and RMSE are recorded for every fit:
Phase 2 in `phase2_grid_span.csv`, Phase 6 in `phase6_a6cal_raw.csv`, Phase 7 in
`phase7_proxy_fits.csv` (which also carries the bootstrap 95% interval, SE and
the corr(c,b) and corr(A,b) from the draws). The circulant embedding returned
**zero negative eigenvalues across all 120 A6 runs**, minimum eigenvalue
1.50e-4, so every fBm path is exact rather than clipped.

## Deviations and corrections

1. **Two pandas defects, fixed, measurements unaffected.** `IS.sample` resolved
   to the DataFrame method rather than the column (the same collision class this
   programme has hit before); and a duplicated keyword argument in a `dict()`
   call. Both were caught before any result was produced.
2. **Phase 3 pooled trend recomputed on distinct cells.** The first version
   pooled all 16 cells, but B0 and B1 are exact duplicates, which inflates t by
   √2. The reported result is the eight-cell version with a cell-clustered
   standard error; the 16-cell version is retained in the JSON to show the
   inflation.
3. **Phase 10 column labels corrected.** The first run labelled the pivot columns
   `corrected_c` and `naive_var_log_rv` when they held the adjustment factor
   (e^{s²}−1)/8 rather than s² itself. The arithmetic and every derived figure
   were correct; the artifact now carries both `s2_*` and `factor_*` columns.
4. **Phase 7 was launched once with an incomplete import path** (the S02 source
   directory was not on `sys.path`) and relaunched after the fix. No partial
   output was written.

## Persistence

Every reported figure regenerates from a persisted artifact: 54 × 2,000 Phase 7
bootstrap draws in `cache/p7boot_*.npz`; 120 calibrated A6 runs in
`cache/a6cal_*.npz` (log-RV matrix, grid, log-IV path, seed, H, σ_w, embedding
diagnostics, plus the full minute-level return panel for seed index 0 of each
setting, the rest regenerating exactly from the logged seed through the imported
`make_a6`); both K4 position series with both forecasts and both proxies in
`cache/k4_*.npz`; both K5 combination forecasts, position series and
seven-element weight vectors in `cache/k5_*.npz`.

## Verification

File verification paired `wc -c` with `wc -l` per item 78. No full-tree hashing
or integrity scanning.

## Outcome

**K4 FIRES** (both criteria). **K5 FIRES** (on tracking error; the weight
criterion passes by 4×10⁻⁵). **K6 DOES NOT FIRE** (overstatement 10.8% to 443%
against a 5% threshold, in all eight cells).

Item 87 discharged: the corrected partition is 128 / 1 / 15 against S09's
96 / 3 / 45, with 32 of 144 changing status. Item 89 discharged: calibrated σ_w
is 1.495 to 4.805 against S10's 1.010, and at the measured scale the A6 arm
reproduces the observed exponent level while remaining non-monotonic in H. Item
90 answered: the reference lies outside the 95% interval in 54 of 54 proxy-fits,
so the anomaly is in the price process, not in realized variance.
