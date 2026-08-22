# Session 12 run log — correction session

Date 2026-08-19. No new data acquired. **The holdout was not read.** No prior
artifact modified or deleted. Nothing committed to git (the tree is not a git
repository). No pre-registered threshold changed: items 92, 93 and 94 stand as
written.

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

DECISIONS items 66–94 verified present by grep, 29 of 29, at lines 398, 405, 413,
419, 424, 433, 437, 442, 445, 454, 457, 466, 469, 474, 485, 490, 497, 502, 510,
515, 523, 531, 533, 538, 543, 547, 553, 557, 562. Items 95–99 appended once and
verified persistent at lines 567, 577, 585, 589, 593, per item 77. DECISIONS.md
grew from 41,139 bytes / 563 lines to 43,701 bytes / 597 lines.

## Wall clock per phase

| phase | wall clock | source |
|---|---|---|
| 0 — verification, append, gate, directories | ~3 min | interactive |
| 1 — convexity on the exact relation | 0.2 s | `phase1_timer.json` |
| 2 — calibration verification: 130.3 s verify, 203.5 s sweep | 334 s | `phase2_determination.json` |
| 3 — wild cluster bootstrap, 9,999 reps × 2 versions + 121-point inversion | 4 s | `phase34_summary.json` |
| 4 — K4 restatement | 1 s | `phase34_summary.json` |
| 5 — report, spec update, runlog | ~13 min | interactive |

Total compute 5 min 39 s. Total session wall clock including code authoring and
inspection, roughly 45 minutes, inside the 30–60 minute expectation. Phases 3 and
4 ran concurrently with Phase 2 as a separate process. The bottleneck was Phase
2's σ_w sweep, 300 panel generations at 25 grid points × 6 Hurst indices × 2
geometries; Phase 2's B branch (recalibration and an A6 re-run) was not required
because determination A holds.

## Seeds and their derivation

| use | master | derivation | count |
|---|---|---|---|
| Phase 2, verification at the calibration points | — | reuses each row's logged seed from S11 `phase6_calibration.csv` | 24 |
| Phase 2, σ_w sweep | 20260826 | `SeedSequence(20260826).generate_state(8)`, one per geometry, held fixed across the grid so the mapping is a clean function of σ_w | 2 |
| Phase 3, wild cluster bootstrap, 8 distinct cells | 20260828 | `PCG64(20260828)` | 1 |
| Phase 3, wild cluster bootstrap, 16 cells | 20260829 | `PCG64(20260828 + 1)` | 1 |
| Phase 3, interval by test inversion | 20260928 | `PCG64(20260828 + 100)` | 1 |

Phase 2 holds the seed fixed within each geometry's sweep deliberately: varying it
across the grid would inject Monte Carlo noise into the very monotonicity check
the sweep exists to make. Between-seed dispersion for the A6 arm was already
established at five seeds per setting in S11 (`phase6_a6cal_raw.csv`, 120 runs,
b_sd 0.032–0.110) and is quoted from there rather than recomputed; no new
synthetic setting was introduced in this session, so no new dispersion measurement
was required. Phases 1 and 4 draw no random numbers.

## Constants and their sources

| constant | value | source |
|---|---|---|
| convexity relation, exact | K_vol = √E[V]·exp(−s²/8) | lognormal MGF at t = ½; derived in Phase 1, item 95 |
| convexity relation, expansion | K_vol ≈ √E[V]·(1 − (e^{s²}−1)/8) | Brockhaus and Long (2000), second order |
| variance-swap strike for quoting | 20% annualised | S11 Phase 10, retained so the figures are comparable |
| K6 threshold | 5% | DECISIONS item 94, unchanged |
| s² intercept route, s² naive, c interval | per cell | S11 `phase5_five_minute.csv`, from the S10 bootstrap |
| calibration target RQ/RV² | per cell | S11 `phase6_measured_ratio.csv`, via `parta.quart_suite` |
| constant-volatility value of RQ/RV² | exactly 1 | RQ = (M/3)Σr⁴ → σ⁴, RV → σ² |
| S11 bisection bracket | [1e-3, 6.0], 24 steps | `phase6_calibrated.py:37,40` |
| S11 bisection sample size | 400 sessions | `phase6_calibrated.py:22` (`S_CAL`) |
| σ_w sweep grid | 25 log-spaced points, 0.1 to 5.0 | this session |
| calibration tolerance | 2% relative | this session |
| Hurst sweep | 0.05, 0.10, 0.20, 0.30, 0.45, 0.50 | S10/S11 |
| observed b range | −0.97 to −0.44 | as restated in this session's brief |
| bootstrap replications | 9,999 (test), 1,499 per grid point (inversion) | session instruction |
| Rademacher p-value floor at G=8 | 2^(1−8) = 0.0078 | 2^G weight vectors, sign-symmetric statistic |
| leverage cap / stop-out | 2.0× / 1.5× target | DECISIONS item 92, unchanged |
| cost sweep | 0.5, 1.0, 2.0, 4.0 ticks per leg | DECISIONS item 69 |
| tick values | ES $12.50, NQ $5.00 | SCOPE section 4 |

## Code path

Imported unmodified: `phase6_arm_a6.make_a6` (S10), `parta.quart_suite` (S05),
`fbm.CirculantEmbedding` and `fgn_acf` (S01), and the S10 `common` module's
`cell_windows`, `subbars`, `fitf`, `fit_diag`, `logrv_matrix` and `var_cols`.
Nothing was reimplemented, so the report-and-halt condition was not triggered.

Phase 2 reconstructs the within-window volatility path `v` from the same seed in
order to read its dispersion directly. That reconstruction repeats the four lines
of `make_a6` that build `v` and is used only to *report* `sd_log_within_window_var`;
the `RQ/RV²` figure it is reported beside comes from `make_a6`'s own returns
through `quart_suite`, unmodified.

## Holdout

**Not read.** Phase 1 recomputes from S11 `phase5_five_minute.csv`. Phase 2 uses
pre-2024 panels and synthetic arms. Phase 3 uses S10 `phase3_subfits.csv`. Phase 4
reads only S11's persisted `cache/k4_*.npz`, which already holds both position
series, both forecasts, both proxies and the breach inputs. No phase required a
holdout read, so the report-and-halt condition was not triggered.

## Fit diagnostics

Phase 2 reports the objective at the solution, the bracket, the convergence
criterion and the proportional discrepancy at every one of the 24 calibration
points, plus monotonicity and crossing counts over the full 300-point sweep. No
new `c + A·M^b` fits were estimated in this session — Phase 1 is closed-form
arithmetic, Phase 3 is a linear fixed-effects regression whose SEs are reported
three ways (OLS-FE, cluster-robust, wild cluster bootstrap), and Phase 4 is a
classification. The condition-number, parameter-correlation and RMSE requirement
therefore binds on no new fit; the S11 and S10 fits it draws on carry those
diagnostics in `phase6_a6cal_raw.csv` and `phase1_bootstrap.csv` respectively.

## Deviations and corrections

1. **None in execution.** All four phases ran as specified on the first
   completed attempt. Phase 2's B branch (recalibrate and re-run the A6 sweep)
   was not entered because determination A holds — the calibration matched at
   24 of 24 points to 1.2e-7.
2. **One statistical caveat surfaced by the results rather than planned for.**
   The wild cluster bootstrap p-value of 0.0066 falls below the attainable floor
   of 1/128 = 0.0078 for eight clusters with Rademacher weights. It is reported
   as p ≤ 0.0078 with the floor stated, not as 0.0066.

## Persistence

Every reported figure regenerates from a persisted artifact: all 9,999 bootstrap
t and β draws per version in `cache/wcb_*.npz` with the observed statistic, SE and
seed; the full 300-point σ_w mapping in `phase2_sweep.csv`; the 24-point
verification in `phase2_verification.csv`; per-cell breach indicators and both
position and realized-volatility series in `cache/k4restate_*.npz`; and the exact
and expansion convexity figures with intervals in `phase1_convexity_exact.csv`.

## Verification

File verification paired `wc -c` with `wc -l` per item 78. No full-tree hashing or
integrity scanning.

## Outcome

**Item 95 upheld**: S11's convexity magnitudes are void; corrected overstatement
5.9–134.3 percent, maximum 2.60 volatility points; **K6 DOES NOT FIRE**, minimum
margin 5.94 percent against 5 percent.

**Item 96 refuted as to the calibration, upheld as to the concern**: determination
**A**, 24 of 24 within 1.2e-7, monotone mapping, no second solution; but σ_w is a
scale parameter, and the interpretable dispersion is 0.764 to 1.803. The mechanism
claim stands in corrected units with a narrowed range claim.

**Item 97 upheld**: p ≤ 0.0078, the floor of an eight-cluster design; 95 percent
interval [−0.0760, −0.0245]; point estimate −0.047 per year unchanged.

**Item 98 upheld**: K4 restated per limit. Stop-out **FIRES**; leverage cap
**UNTESTED**, bound 0 of 2,524, would first bind at 1.434×. The S11 joint
determination is superseded.

**Item 99 recorded**: missed exceeds spurious in three of four cells, up to 6.5×.
