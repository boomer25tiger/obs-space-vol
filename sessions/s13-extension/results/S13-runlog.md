# Session 13 run log — mechanism extension, risk parity, trend structure, convexity table

Date 2026-08-19. No new data acquired. No prior artifact modified or deleted.
Nothing committed to git (the tree is not a git repository). No parameter,
threshold, rule or specification changed after any holdout number was seen.

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

DECISIONS items 66–99 verified present by grep, 34 of 34, at lines 398, 405, 413,
419, 424, 433, 437, 442, 445, 454, 457, 466, 469, 474, 485, 490, 497, 502, 510,
515, 523, 531, 533, 538, 543, 547, 553, 557, 562, 567, 577, 585, 589, 593. Items
100–105 appended once and verified persistent at lines 601, 606, 613, 620, 626,
630, per item 77. DECISIONS.md grew from 43,701 bytes / 597 lines to 46,430 bytes
/ 633 lines.

## Holdout read count

| # | session | phase | purpose |
|---|---|---|---|
| 1 | S09 | Phase 6 | sizing out of sample, candidate set out of sample |
| 2 | S11 | Phase 1 | re-evaluation of the three floor-defect candidates (item 88) |
| 3 | S11 | Phases 8–9 | K4 risk limits, K5 combination weights |
| **4** | **S13** | **Phase 2** | **K7 risk parity (item 105)** |

Phases 1, 3, 3b and 4 of this session read pre-2024 panels and persisted S10/S11
artifacts only. No phase other than Phase 2 required a holdout read, so the
report-and-halt condition was not triggered. Phase 2 reads through S11's
`ho_series`, whose byte-for-byte equivalence to S07 `series()` on the in-sample
panel is asserted at run time in the S11 source.

## Wall clock per phase

| phase | wall clock | source |
|---|---|---|
| 0 — verification, append, gate, directories | ~3 min | interactive |
| 1 — measurement 1.6 s, κ calibration 44.9 s, A7 60.9 s, A8 92.9 s | 200.3 s | `phase1_determination.json` |
| 2 — K7 risk parity, four books plus illustration | 0.7 s | `phase2_k7.json` |
| 3 — trend structure, 2 × 9,999 wild cluster bootstrap with break re-search | 12.4 s | `phase34_timers.json` |
| 3b — 2022 robustness, 2 × 9,999 with break re-search | 18 s | `logs/phase3b.log` |
| 4 — convexity lookup table, 128 rows | <0.1 s | `phase34_timers.json` |
| 5 — report, spec update, runlog | ~14 min | interactive |

Total compute 3 min 51 s. Total session wall clock including code authoring and
inspection, roughly 55 minutes, inside the 45–90 minute expectation. Phase 1
dominated as predicted, at 200 of the 231 seconds of compute: 93 s for A8
(120 panels), 61 s for the A7 position sweep (80 panels) and 45 s for the kappa
bisection.

## Seeds and their derivation

| use | master | derivation | count |
|---|---|---|---|
| Phase 1, κ calibration | 20260830 | `SeedSequence(20260830).generate_state(16)`, consumed in (geom, root) order | 4 |
| Phase 1, arm A7 | 20260831 | `SeedSequence(20260831).spawn(80)`, consumed in (geom, root, position, seed index) order | 80 |
| Phase 1, arm A8 | 20260832 | `SeedSequence(20260832).spawn(120)`, consumed in (geom, root, H, seed index) order | 120 |
| Phase 3, sup-F bootstrap | 20260833 | `PCG64(20260833)` for the break, `PCG64(20260834)` for the linear comparison | 2 |
| Phase 3b, robustness | 20260834 | `PCG64(20260834)` full sample, `PCG64(20260835)` excluding 2022 | 2 |

Every seed is logged: Phase 1 calibration in `phase1_kappa.csv`, Phase 1 arms in
`phase1_arms_raw.csv` and in each `cache/a7_*.npz` and `cache/a8_*.npz`, Phase 3
and 3b in `cache/break_bootstrap.npz` and `cache/break_robust_*.npz`. Between-seed
dispersion is reported as `b_sd` on every synthetic row, five seeds per setting,
200 runs in total; maximum between-seed sd across all settings is 0.169. Phases 2
and 4 draw no random numbers.

## Constants and their sources

| constant | value | source |
|---|---|---|
| observed b range | −0.97 to −0.44 | as restated in the S12 brief and carried forward |
| DIMS | GLOBEX (1953, 1380), RTH (1901, 390) | S05E `run5e.py` |
| VAR_LOG_IV | 1.02 | S05E, DECISIONS item 36 |
| A7 dominant-return positions | start, quarter, midpoint, end | session instruction |
| A7 amplitude κ | 3.14 to 9.80, calibrated | measured first-sub-bar ratio, this session, before any arm |
| A8 σ_w | 1.495 to 4.805 | S11 `phase6_calibration.csv`, S12-verified |
| Hurst sweep | 0.05, 0.10, 0.20, 0.30, 0.45, 0.50 | S10/S11/S12 |
| inverse-vol bias, exact | E[1/σ̂] = (1/σ)·exp(v/2), v = w/4 | derived in Phase 2, per item 95 |
| expansion validity boundary | v = 0.3754 | computed in Phase 2 |
| proxy noise w at RTH daily | ES 0.1513, NQ 0.0515 | S11 `phase7_proxy_fits.csv`, A·M^b at M = 78 |
| λ at RTH daily | ES 0.840, NQ 0.931 | S09 `phase3_sizing_params.csv`, extended range |
| risk-parity lookback | 21 sessions | this session, stated as a choice |
| rebalance | 21 sessions (monthly) | DECISIONS item 103 |
| K7 thresholds | 0.02 weight, 5% volatility | DECISIONS item 103, unchanged |
| cost sweep | 0.5, 1.0, 2.0, 4.0 ticks per leg | DECISIONS item 69 |
| tick values | ES $12.50, NQ $5.00 | SCOPE section 4 |
| convexity relation | K_vol = √E[V]·exp(−s²/8) | exact under lognormal V, S12 Phase 1 |
| variance-swap strike for quoting | 20% annualised | S11/S12, retained for comparability |
| convexity threshold | 5% | DECISIONS item 94, unchanged |
| bootstrap replications | 9,999 | session instruction |
| Rademacher p floor at G = 8 | 2⁻⁷ = 0.0078 | 2⁸ weight vectors, sign-symmetric statistic |

## Code path

Imported unmodified: `phase6_arm_a6.make_a6` (S10), `parta.quart_suite` (S05),
`phase8910_apps.ho_series` (S11, equivalence-asserted against S07 `series()`), and
the S10 `common` module's `cell_windows`, `subbars`, `fitf`, `fit_diag`,
`logrv_matrix` and `var_cols`. Nothing was reimplemented, so the report-and-halt
condition was not triggered.

Arm A7 is composed on top of `make_a6` rather than written separately: the
generator is called at σ_w = 0 (which is A0) and one column of the returned panel
is scaled by √κ, multiplying that minute's variance by κ. Boosting one minute of L
by a constant multiplies total integrated variance by a constant, so log IV shifts
by a constant and Var(log IV) — hence b — is unaffected by the rescaling itself.
A8 is the same composition at the calibrated σ_w.

## Measurement before generation

Item-mandated and satisfied: `phase1_amplitudes.csv` records the first- and
last-sub-bar amplitude and variance share at every grid point for all eight
distinct cells, written and printed before the first arm panel was generated. The
calibration targets are read from that file.

## Fit diagnostics

Condition number, both parameter correlations and RMSE are recorded for every fit
in `phase1_arms_raw.csv` and aggregated in `phase1_arms_agg.csv`. Phases 2, 3, 3b
and 4 estimate no `c + A·M^b` fits: Phase 2 is closed-form plus a portfolio
construction, Phases 3 and 3b are linear fixed-effects regressions reported with
RSS and bootstrap inference, and Phase 4 is closed-form arithmetic on the S10 and
S11 fits, which carry those diagnostics in their own artifacts.

## Deviations and corrections

1. **One launch error, no effect on results.** A backgrounded compound command put
   the Phase 3/4 log at the project root rather than the session directory, so the
   job did not start; it was rerun in the foreground from an absolute path. No
   partial output was written.
2. **Phase 3b added.** Phase 3 as specified selects a break date and tests it. Its
   selected date, 2022, is the last admissible year and b reverts in 2023 in every
   cell, which a level shift does not predict. A single-year dummy and an
   excluding-2022 refit were added to distinguish the two accounts; both read only
   pre-2024 artifacts and change no threshold.
3. **The risk-parity estimation window is a choice, disclosed.** Item 103 fixes a
   monthly rebalance but not a lookback. Twenty-one sessions is used as the base
   case and the single-day estimator is reported beside it as the upper bound,
   because the bias term scales as 1/n in the averaging window and reporting one
   without the other would misstate the effect by a factor of 21.

## Persistence

Every reported figure regenerates from a persisted artifact: 200 synthetic runs in
`cache/a7_*.npz` and `cache/a8_*.npz`, each holding the log-RV matrix, grid, log-IV
path, seed and arm parameters, with the full minute-level return panel for seed
index 0 of every setting and the rest exactly regenerable from the logged seed
through the imported `make_a6`; four weight-series pairs in `cache/k7_*.npz`; and
all 9,999 sup-F and linear-F bootstrap draws per specification in
`cache/break_bootstrap.npz` and `cache/break_robust_*.npz`.

## Verification

File verification paired `wc -c` with `wc -l` per item 78. No full-tree hashing or
integrity scanning.

## Outcome

**Item 101 REJECTED**: A7 enters the observed range on neither geometry at any of
four positions; the RTH residual is not an open-bar effect, and it now survives
three tested mechanisms.

**K7 FIRES** on both criteria — mean |Δw| 0.000145 against 0.02, realized-volatility
difference 0.0038% against 5% — with the widest-reliability illustration showing a
daily-rebalanced book would breach the weight threshold at 0.0370.

**Trend shape INDETERMINATE**: a single-year 2022 excursion beats both the trend
and a level shift, b reverts in 8 of 8 cells in 2023, and excluding 2022 halves
the slope to −0.0275 per year.

**Convexity prescription**: one-minute sampling, daily horizon only; unreachable at
30-minute on either instrument and at hourly on ES.
