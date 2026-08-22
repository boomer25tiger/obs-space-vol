# SPEC-obs-space-vol-eval.md

Frozen record, reconstructed 2026-08-19 in S06R Phase 9 from `DECISIONS.md`,
which is the only surviving authority (the original spec documents were absent
from the repository at S03, DECISIONS item 11). Every element carries the date
it was fixed and whether it was pre-registered or added post hoc.

## 1. Model set

| model | definition | fixed | status |
|---|---|---|---|
| M1_EWMA | RiskMetrics, lambda 0.94 | 2026-08-18 (S05 PREREG Part D) | pre-registered |
| M2_HAR | Corsi (2009), lags 1/5/22 | 2026-08-18 (S05 PREREG Part D) | pre-registered |
| M3_HARJ | HAR plus max(RV-BV,0) | 2026-08-18 (S05 PREREG Part D) | pre-registered |
| M4_HARQ | Bollerslev, Patton, Quaedvlieg (2016) | 2026-08-18 (S05 PREREG Part D) | pre-registered |
| M5_RGARCH | Hansen, Huang, Shek (2012) | 2026-08-18 (S05 PREREG Part D) | pre-registered |
| M6_PARK, M6_GK | Parkinson and Garman-Klass, from TRUE bar high and low | rebuilt 2026-08-19 (item 43) | POST HOC repair of a defective construction |

Model-set reduction: where RGARCH parameters violate stationarity or the
forecasts diverge, the cell is marked RGARCH-unavailable and the set is reduced
there, with the reduction stated in every table. Fixed 2026-08-19 (item 41),
POST HOC. RGARCH is never filtered, respecified or constrained.

## 2. Estimator pair

E2 (non-overlapping contiguous halves) and E4 (asymptotic-variance route) are
retained and BOTH reported throughout; neither is primary. E1_a and E1_d are
dropped. Fixed 2026-08-19 (item 46), POST HOC, on the S05E control evidence:
E2 mean absolute error 0.006-0.012 on clean data degrading to 0.16-0.25 under
jumps; E4 0.045-0.051 clean, 0.105-0.128 under jumps.

Effective sub-bar count replaces nominal M wherever an estimator takes M.
Fixed 2026-08-19 (item 45), POST HOC.

## 3. Exclusion rules

| rule | fixed | status |
|---|---|---|
| Calendar-spread filter, root separation, CME trade-date session cut, front contract by volume, roll +/-1 | 2026-08-18 (S03 phases 2) | pre-registered (SCOPE section 3 as quoted) |
| Early close, geometry-dependent: RTH excludes any session halting before 15:00 NY; GLOBEX excludes only if the overnight is under 90% complete | 2026-08-18 (item 13, S04 R1) | POST HOC repair |
| Degraded Databento dates flagged, NOT excluded | 2026-08-18 (item 14, S04 R2) | POST HOC, deliberate non-exclusion |
| Weekend trade date reassigned to the next session | 2026-08-18 (item 15, S04 R3) | POST HOC repair |
| Non-trading windows excluded on EXCHANGE-CALENDAR grounds only, never on realized variance | 2026-08-19 (item 42) | POST HOC |

Calendar classes: EARLY_CLOSE_1300 (MLK, Presidents, Memorial, Independence,
Labor, Thanksgiving, Juneteenth from 2022) and FULL_CLOSURE_0930 (Good Friday,
and 2018-12-05 National Day of Mourning). Intraday trading halts, such as the
March 2020 circuit breakers, are NOT ex-ante determinable and are NOT excluded.

## 4. Forecast filter

Bollerslev, Patton and Quaedvlieg insanity filter on M3_HARJ and M4_HARQ:
any forecast outside the in-sample realized-variance range is replaced by the
in-sample mean. Applied identically in every cell whether or not it fires.
Fixed 2026-08-19 (item 40), POST HOC. A 100x-mean alternative is reported as a
sensitivity and is NOT adopted.

## 5. Holdout boundary

2024-01-01. Nothing on or after that date has been loaded, processed or
inspected in any session. Fixed 2026-08-18 (S03 PREREG), pre-registered,
restated unchanged 2026-08-19 (item 50).

## 6. Family size and multiplicity

The Part E family is 96 comparisons (24 cells x 2 conditioning quantiles x 2
confidence levels). No familywise correction is applied; its absence is
disclosed as a limitation, since correcting a count already seen would be worse
than disclosing it. Alongside the count, the result is reported at a single
cell chosen on the ex-ante criterion of largest effective sample, fixed before
the rerun. Fixed 2026-08-19 (item 47), POST HOC.

## 7. Kill conditions and their null abstracts

K1. The reliability correction does not change Model Confidence Set
composition.
  Null abstract: "Across 96 (cell, quantile, level) comparisons the model
  confidence set is invariant to whether evaluation conditions on the realized
  proxy or on a predetermined variable, and invariant to whether the
  information coefficient is corrected for proxy reliability. The correction
  rescales every model in a cell by a common factor and therefore cannot
  reorder them; the reliability programme is not decision-relevant for model
  selection." Fixed 2026-08-18 (item 15), pre-registered as the S05 criterion.

K2. No reliability estimator is grid-invariant.
  Null abstract: "lambda_M multiplied by Var(log RV_M) should be constant in M
  because Var(log IV) cannot depend on the sampling grid. No estimator holds it
  constant: the best achieves a max/min ratio of 1.05 and the worst 1.97, and
  the ranking is not stable across cells. Reliability as estimated here is a
  property of the grid, not of the data." Fixed 2026-08-19 (item 26), POST HOC.

K3. The measured proxy-error scaling is inconsistent with sampling theory.
  Null abstract: "Var(log RV_M) = c + A M^b fits the data with b between -0.41
  and -1.00 against a measured trigamma reference of -1.14. A positive control
  passing synthetic data through the identical code path recovers -1.19 at the
  same grid, and no arm - diurnal profile, calibrated jumps, measured padding
  or a rough volatility path - reproduces the observed flatness. The proxy
  error does not scale as sampling theory requires and the cause is not
  located." Fixed 2026-08-19 (items 36 and 37), POST HOC.

## 8. Provenance of every post-hoc element

Items 13-15 (S04 repairs), 26-32 (S05B estimator-validity additions), 33-38
(S05D/S05E panel integrity and positive control) and 39-50 (S06R repairs) were
all specified after the data they concern had been seen, and are marked POST
HOC in DECISIONS.md at the point of specification. Items 1-12, 16-25 were fixed
before the analysis they govern.


## 9. S07 additions (2026-08-19)

| item | element | fixed | status |
|---|---|---|---|
| 51 | Exchange-declared halts join the calendar exclusion: 2020-03-09, 03-12, 03-18, 03-23, 03-24 (circuit-breaker limit halts, exchange log) and 2019-02-27, 2020-07-01 (Databento degraded, S04 R2). Applied as a data-PRESENCE criterion on those sessions, never on realized variance. | 2026-08-19 | POST HOC |
| 52 | Filter lower bound is the smallest STRICTLY POSITIVE in-sample realized variance. | 2026-08-19 | POST HOC, disclosed |
| 53 | RGARCH diagnosis extended to the 8 GLOBEX intraday cells. | 2026-08-19 | POST HOC |
| 54 | The S06R pre-specified cell ES/RTH/B0/30min stands. Added: a stratified breakdown, and a second pre-specified cell at the MEDIAN effective sample logged before its comparison. | 2026-08-19 | POST HOC |
| 55 | SPY raw DBN only; derived parquets not consumed; SHA-256 manifest recorded. | 2026-08-19 | POST HOC |
| 56 | SPY exponent fitted under BOTH calendar-time forward fill and traded-tick sampling; a flat exponent under forward fill alone is not a replication. | 2026-08-19 | POST HOC |
| 57 | SPY is two-venue (~33% of consolidated volume), venues never pooled, noise corrected, primary M range restricted to implied bias below 1%. | 2026-08-19 | POST HOC |
| 58 | SPY holdout boundary 2024-01-01, matching futures. | 2026-08-19 | POST HOC |

Model-set reduction, extended: item 41's rule (mark unavailable, reduce the set, state
the reduction) is applied to any model failing the positivity invariant, not only
RGARCH. In S07 this covered M6_PARK in two GLOBEX 30min cells. POST HOC, 2026-08-19.


## 10. S08 additions (2026-08-19)

| item | element | fixed | status |
|---|---|---|---|
| 59 | The two-sided, two-model insanity filter is recorded as an analyst error, with the damage measured. | 2026-08-19 | POST HOC |
| 60 | Revised filter: lower bound only, all seven models, replacement = smallest strictly positive in-sample RV. No upper bound. | 2026-08-19 | POST HOC |
| 61 | The MCS leg is evaluated as kill condition K2 on repaired losses. | 2026-08-19 | POST HOC |
| 62 | RGARCH is an implementation failure at intraday GLOBEX horizons, not a model failure; no claim is made about Realized GARCH. | 2026-08-19 | POST HOC |
| 63 | Intercept route to lambda adopted as a third reported column beside E2 and E4; bounded in (0,1) by construction where A>0 and b<0. | 2026-08-19 | POST HOC |
| 64 | The holdout is NOT opened in S08; it opens once, at the economic validation of the sizing consequence. | 2026-08-19 | POST HOC |
| 65 | SPY is a robustness paragraph, traded-tick primary, calendar-time sensitivity, three failed measurements recorded as failures. | 2026-08-19 | POST HOC |

### Kill-condition outcomes

- **K2 (reliability correction does not change MCS composition): DOES NOT FIRE.** Determined
  2026-08-19 on repaired losses. Clean-geometry (RTH) rate
  33 of 48; full family
  48 of 72 computed against a pre-registered 96,
  24 halted. Pre-registered cell ES/RTH/B0/30min
  3 of 4; post-hoc median cell
  ES/RTH/B1/1h 3 of 4.
- **K3 (proxy-error scaling inconsistent with sampling theory): STANDS.** Unmoved by
  every repair, reproduced on SPY at two venues under both sampling conventions.


## 11. S09 additions (2026-08-19)

| item | element | fixed | status |
|---|---|---|---|
| 66 | Item 29 amended: the intercept route does not use E2's subsampling or E4's quarticity, so the M ∈ {5,6,10} bar does not transfer. BOTH ranges reported side by side throughout, every grid point labelled; neither alone. | 2026-08-19 | POST HOC, disclosed |
| 67 | K2 is not reportable without a placebo. Scheme S-D conditions on a second F_{t−1} variable with no proxy involvement; the reportable quantity is the EXCESS of S-B vs S-C over S-D vs S-C. | 2026-08-19 | POST HOC |
| 68 | Sizing rules, fixed before any result: 10% annualized target, daily rebalance, M2_HAR forecast at five-minute-equivalent sampling. R0 oracle (simulation only), R1 none, R2 λ_theory = c/(c+trigamma(M/2)), R3 λ_intercept. Shrinkage in logs. | 2026-08-19 | PRE-REGISTERED |
| 69 | Sizing metrics: primary tracking error (RMS deviation of log realized portfolio volatility from log target); secondary turnover, priced across 0.5, 1.0, 2.0, 4.0 ticks per leg at $12.50 ES / $5.00 NQ. A single assumed cost is not admissible. | 2026-08-19 | PRE-REGISTERED |
| 70 | Nine candidates, threshold R² ≥ 0.02, three-way partition. The correction rescales every candidate in a cell by the same factor, so ranking is unchanged by construction; stated, not presented as a finding. | 2026-08-19 | PRE-REGISTERED |
| 71 | K3 sizing kill condition, evaluated on the holdout: fires if the R2-vs-R3 tracking-error difference is below 5% relative in every cell and at every cost-sweep point. | 2026-08-19 | PRE-REGISTERED |
| 72 | Holdout opens once, Phase 6, ES and NQ 2024-01-01 to 2026-08-14. No parameter, threshold, rule or specification changes after any holdout number is seen. Tracking error aggregated quarterly, and that aggregation is the stated reason the measurement is not circular. | 2026-08-19 | PRE-REGISTERED |
| 73 | No further measurement session follows S09. Roughness, vol-of-vol from the fitted intercept, the overnight leg, SPY as a second instrument, and cross-sectional reliability are further work. | 2026-08-19 | PRE-REGISTERED |
| 74 | The S09 integrity scan of 2026-08-19 is VOID; `S09-integrity-scan.txt` is retained as a record of the fault and carries no evidential weight. | 2026-08-19 | POST HOC |
| 75 | No full-tree hashing or integrity scanning in any session. | 2026-08-19 | POST HOC |
| 76 | Environment event: the project venv failed on pandas and was rebuilt from `requirements.lock`, not patched; the broken environment is retained at `.venv-broken-20260819`. | 2026-08-19 | POST HOC |
| 77 | Any session appending to DECISIONS.md verifies by grep that its append persisted before proceeding. | 2026-08-19 | POST HOC |
| 78 | Item 75 amended: `wc -c` alone is insufficient. File verification pairs `wc -c` with `wc -l`; nonzero bytes with zero lines is treated as unreadable. | 2026-08-19 | POST HOC |
| 79 | The project environment lives outside the iCloud sync scope, at `~/venvs/obs-space-vol`. | 2026-08-19 | POST HOC |

### Reliability parameters as measured (S09 Phase 3, extended grid, five-minute equivalent)

| cell | M | λ_intercept | λ_theory |
|---|---|---|---|
| ES/GLOBEX/1day | 276 | 0.8272 | 0.9930 |
| NQ/GLOBEX/1day | 276 | 0.9399 | 0.9933 |
| ES/RTH/1day | 78 | 0.8398 | 0.9765 |
| NQ/RTH/1day | 78 | 0.9313 | 0.9760 |
| ES/RTH/1h | 12 | 0.5881 | 0.8530 |
| NQ/RTH/1h | 12 | 0.8102 | 0.8871 |
| ES/RTH/30min | 6 | 0.3958 | 0.6737 |
| NQ/RTH/30min | 6 | 0.6765 | 0.7760 |

Identical for B0 and B1: the λ code path rebuilds returns from the raw close grid
under the tradeability mask only, so the boundary treatment never enters.
Restricted (original S05) grid: undefined at all four RTH intraday cells (one grid
point against three fitted parameters), degenerate at ES/GLOBEX/1day
(b = −1.02e-4, λ = −890.21, and the A > 0 / b < 0 screen does not catch it), and
materially different at ES/RTH/1day (λ = 0.3466 against 0.8398).

### Kill-condition outcomes, S09

- **K2 (placebo-corrected, item 67): INDETERMINATE.** Clean-geometry excess 20.8%
  (S-B vs S-C 68.8%, placebo S-D vs S-C 47.9%, n = 48), above the 20% threshold
  but not tracking λ across horizons: excess 12.5% / 43.8% / 6.3% at 1day / 1h /
  30min against λ 1.001 / 0.856 / 0.713. Excluding the 7 seed-unstable cells the
  excess is 25.0% and still does not track. Half the raw effect is subset
  variation carrying no proxy content.
- **K3 sizing null (item 71): FIRES on the extended range.** Holdout maximum
  R2-vs-R3 relative tracking-error difference 1.008% (ES/RTH), with R3 better in
  all four cells by 0.46% to 1.01%, invariant across the whole cost sweep.
  Abstract: "Measured reliability at five-minute-equivalent sampling runs from
  0.40 to 0.94 against a textbook 0.67 to 0.99, but replacing the textbook
  shrinkage weight with the measured one changes out-of-sample tracking error by
  at most 1.008% in relative terms, in the same direction in every cell, at every
  point of a cost sweep spanning an eightfold range of transaction cost. The
  reliability gap is real and has no sizing consequence at a 10% volatility
  target with daily rebalancing." K3 DOES NOT FIRE on the restricted range, where
  ES/RTH deteriorates by 7.08% and ES/GLOBEX is degenerate; the null is therefore
  conditional on the extended grid.
- **K3 (proxy-error scaling, section 7): STANDS, unchanged.** Independent of the
  sizing null above. The sizing null says the anomaly has no consequence at this
  target and rebalance frequency; it does not locate or resolve the anomaly.

### Signal status (S09 Phase 5/6, extended grid, 144 candidate-cells)

Ranking is unchanged by construction. Status changes in 3 of 144 cases (2.1%):
ES/RTH 1h RS-up under B0 and B1, and ES/RTH 1day signature slope under B1, all in
the flip band [0.02λ, 0.02). Out of sample two of the three clear decisively
(R² 0.0128 → 0.237 and 0.240) and the third does not (→ 0.0023). Of the 96
clears-under-both, 96 still clear after correction out of sample and 95 clear raw.


## 12. S10 additions (2026-08-19)

| item | element | fixed | status |
|---|---|---|---|
| 80 | Item 73 amended. S10 runs because the headline exponent never carried an uncertainty estimate: S08 bootstrapped c and reported nothing for b. No new data, no holdout. | 2026-08-19 | POST HOC, disclosed |
| 81 | The exponent is grid-dependent by more than has been stated; c and A·M^b are strongly correlated and most information about b sits at the coarse end. | 2026-08-19 | POST HOC |
| 82 | Pooling accounts for part of the gap and was never followed up. | 2026-08-19 | POST HOC |
| 83 | The return-distribution hypothesis was never tested; arms A0–A4 all use Gaussian innovations. | 2026-08-19 | POST HOC |
| 84 | The within-window roughness hypothesis was never tested either; S05E's A4 varied roughness ACROSS sessions only, and its negative result is withdrawn. | 2026-08-19 | POST HOC |
| 85 | RS-up at ES/RTH/1h is under suspicion; diagnosed in sample. | 2026-08-19 | POST HOC |

### Tightened validity screen (adopted)

A fit is admissible only if A > 0, b < 0, the grid carries at least 2 × 3 = 6
points, and |b| > 0.01. The S08 screen (A > 0, b < 0 alone) passed the
ES/GLOBEX/1day restricted fit at b = −1.23e-4 with a condition number of
5×10¹¹, which carried λ = −890 into S09 Phase 5 and manufactured 14 false signal
rejections. Under the tightened screen 14 of 34 fits pass, against 26 of 34
before: the extended grid loses the four RTH/30min cells on point count, and the
restricted grid loses all sixteen.

### Determination: A — the exponent anomaly stands, with uncertainty quantified

- Trigamma reference outside the 95% bootstrap interval on b in **18 of 18
  cells** (2,000 joint resamples, master seed 20260820). Median SE(b) 0.054
  against a median gap of 0.483. P(b ≥ measured) is 1.0000 in 16 cells and
  0.987 / 0.985 in the two closest.
- Grid sensitivity bounded below the gap: leave-one-out median 0.019, maximum
  0.232. The restricted-versus-extended deviation of up to 0.483 is real but the
  restricted fits carry condition numbers of 60 to 5×10¹¹ and all fail the
  tightened screen.
- Pooling accounts for a mean **36.0%** of the pooled-to-reference gap (median
  31.4%, range 23.6%–61.1%), residual 0.357 in the same direction in every cell.
  Within-year b is steeper than pooled by 0.176, reproducing S05E's 0.182.
- Quoted from the 14 cells that pass the tightened screen: **b from −0.443 to
  −0.974 against references of −1.126 to −1.210.**

### Item 82 amended: the volatility-tercile evidence is withdrawn

All 48 volatility-tercile sub-fits are degenerate — 32 return A < 0 with |b|
between 2 and 67, and 16 return the flat-power pathology (b ≈ −1e-4, condition
number 10¹⁰–10¹²). Sorting sessions on realized volatility removes the
cross-sectional log-IV variation that identifies the intercept, so c and A·M^b
are not separately identified within a tercile. S05E's "steeper within
volatility tercile in 15 of 16" was computed on fits of this kind. The
within-year leg stands; all 128 year sub-fits are clean.

### Item 83 answered: NO. Return distribution does not account for the gap

Arm A5 (S05E A0 with Student-t innovations standardised to unit variance) at the
S04 measured tail index moves b by +0.067 to +0.111 (GLOBEX) and +0.096 to
−0.046 (RTH), against between-seed SD of 0.066 to 0.170 — every move inside seed
noise, two in the wrong direction. Mean share of the gap 8.6%, maximum 28.0%. No
setting from ν = 2.95 to ν = 10 enters the observed range. The paired
Var(log IV) = 0 sub-arms give the correct heavy-tailed reference, which stays at
−1.09 to −1.18 and moves at most 0.065 from Gaussian: **the reference is not
wrong, the data depart from it.**

### Item 84 answered: NOT SUPPORTED. Within-window roughness does not account for it

Arm A6 (A0 with the log volatility path varying WITHIN each window as fBm at
Hurst index H) over H ∈ {0.05, 0.10, 0.20, 0.30, 0.45, 0.50}. The b–H map is
non-monotonic in both geometries and its entire range (0.079 GLOBEX, 0.126 RTH)
is smaller than the largest between-seed SD (0.130, 0.103). No H enters the
observed range. The inversion to implied H was therefore not performed, and no
comparison against the lag-direction estimator was made. A sensitivity leg at
0.5× and 2× the within-window volatility scale reaches b = −0.978 at most. The
within-window scale σ_w is not measured anywhere in this programme and is set to
√(VAR_LOG_IV); that is the weakest assumption in the phase and is stated as a
choice.

### Item 85 answered: a defect, but NOT an alignment defect

The two S09 code paths produce byte-identical RV and RS-up on the same in-sample
panel and identical R² to 1e-17. The lag is a clean one-window shift and
predictor and target windows are disjoint index blocks, so there is no overlap.
The defect is **floor substitution**: `np.log(np.maximum(v, 1e-300))` at
`phase5_signals.py:104` and `phase6_holdout.py:330` maps the three windows of
11,406 with zero realized semivariance to −690.78. Removing or replacing those
three moves in-sample R² from **0.0128 to 0.4286**. It is the same 1e-300 floor
item 60 already banned for the forecast insanity filter, applied to a predictor
that can legitimately be zero.

Reach: 32 of 96 candidate-cells contain a zero and **16 change retention status
once repaired** — RS-up and RS-down at all eight RTH intraday cells, R² lifts of
0.18 to 0.48. Parkinson, Garman-Klass and realized quarticity contain no zeros
and are untouched. Jump variation is legitimately zero in 21%–49% of windows and
needs a different transform, not a floor repair; its status does not change.
This corrects S09's Phase 5 partition for RS-up and RS-down and does not touch
the K3 sizing null or the K2 placebo result, which do not involve the candidate
set.


## 13. S11 additions (2026-08-19)

| item | element | fixed | status |
|---|---|---|---|
| 86 | Zero-predictor windows are DROPPED, not floored. Zero upside semivariance is a legitimate observation; substituting any value invents data. Count reported per cell, applied identically to every candidate, never conditioned on the target. | 2026-08-19 | POST HOC |
| 87 | The S09 Phase 5 partition is VOID and is recomputed. | 2026-08-19 | POST HOC |
| 88 | Holdout re-evaluation, disclosed in full: only the candidates the defect touched, no threshold, rule, sizing parameter or specification changed. | 2026-08-19 | POST HOC, disclosed |
| 89 | sigma_w is CALIBRATED, not chosen, from the excess of RQ/RV-squared over its constant-volatility value of 1. | 2026-08-19 | POST HOC |
| 90 | The exponent as a proxy specification test: steeper b for the noise-robust proxies locates the anomaly in realized variance, flat b for all three locates it in the price process. | 2026-08-19 | PRE-REGISTERED |
| 91 | Financial applications, pre-registered before any result: risk-limit breaches, inverse-MSE combination weights, variance-to-volatility convexity. | 2026-08-19 | PRE-REGISTERED |
| 92 | K4, risk-limit breaches. Leverage cap 2.0x, stop-out at realized volatility above 1.5x target. Fires if the spurious breach rate is below 1 percent in every cell, or the cost below 1 bp at every sweep point. | 2026-08-19 | PRE-REGISTERED |
| 93 | K5, combination weights. Fires if the mean absolute weight change is below 0.02 in every cell, or the out-of-sample tracking-error difference below 5 percent relative at every sweep point. | 2026-08-19 | PRE-REGISTERED |
| 94 | K6, convexity. Fires if the proportional overstatement of the convexity adjustment from naive Var(log IV) is below 5 percent in every cell. | 2026-08-19 | PRE-REGISTERED |

### Item 87 discharged: the corrected signal partition

Extended range, 144 candidate-cells. S09 (floored) 96 / 3 / 45 / 0 against
S11 (item-86 drop rule) **128 / 1 / 15 / 0** for clears-both /
only-after-measured / neither / raw-but-not-measured. **32 of 144 change status,
all promotions** — jump variation in all 16 cells, RS-up and RS-down at all 8 RTH
intraday cells. S10's estimate of 16 was half the true figure because its
min-positive substitution is not the right repair for a candidate that is
legitimately zero in 21 to 49 percent of windows. Occupancy of the flip band
falls from 3 to 1: correcting the predictor made the reliability correction
matter LESS for retention.

Holdout (item 88, touched candidates only): ES/RTH/1h RS-up in-sample R-squared
0.0128 to **0.4286**, out-of-sample **unchanged at 0.2369** because the holdout
contained no zero-semivariance hour. Item 85's "dead then strong" anomaly was
entirely an in-sample artifact and is dissolved, not explained.

### Item 89 discharged: sigma_w calibrated

Measured RQ/RV-squared runs 0.778 to 3.607 against a constant-volatility value of
1. Calibrated sigma_w runs **1.495 to 4.805 against S10's assumed 1.010**. Re-run
at calibrated sigma_w the A6 map is still non-monotonic with range at or below
between-seed SD in all four cells, so the roughness hypothesis remains NOT
SUPPORTED and no inversion is performed. But the LEVEL of b now lands inside the
observed range [-1.00, -0.41] in all four cells, where at S10's sigma_w it sat at
-1.06 to -1.18. **S10's statement that within-window variation at any scale tried
produces an exponent at the reference is CORRECTED**: at the measured scale it
produces an exponent at the observed value. The mechanism is within-window
volatility DISPERSION, not its Hurst index.

### Item 90 answered: the anomaly is in the price process

Var(log X_M) = c + A*M^b for realized variance, the BNHLS (2009) flat-top
realized kernel and the ZMA (2005) two-scale estimator on identical windows,
2,000 bootstrap resamples each, 18 cells. **The trigamma reference lies outside
the 95 percent interval on b in 54 of 54 fits.** Mean b -0.631 (RV), -0.521 (RK),
-0.495 (TSRV): the noise-robust proxies are on average FLATTER, not steeper. The
sign is mixed by cell (RK steeper than RV in 8 of 18) but no cell on any proxy
approaches the reference. **Item 90's second reading holds: the anomaly is in the
price process, not in realized variance.** Combined with the Phase 6 result, it
is a property of how volatility is distributed inside the window, which no proxy
for the same window can remove.

### Other S11 results

- **Grid span does not explain the residual and runs the wrong way.** Truncating
  a 1day grid to the 1h coarse end makes b STEEPER (ES/RTH -0.627 to -0.929)
  while the actual 1h cell is FLATTER (-0.466). Share attributable to span is
  negative in all four comparisons (-1.87 to -0.14). The residual tracks
  instrument and horizon.
- **b is steepening over time.** All 16 cells have a negative slope; pooled with
  cell fixed effects on the eight distinct cells, **-0.0469 per year, clustered
  SE 0.0112, t = -4.19, p = 0.0041** — a drift of about 0.33 over 2016-2023,
  roughly half the average gap. The anomaly is shrinking.
- **Reliability against out-of-sample degradation**: Spearman rho 0.762, exact
  p 0.028 on eight distinct cells, higher lambda degrading MORE. Reported as a
  descriptive association, not a test: at n = 8 the design has about 25 percent
  power against rho = 0.7.
- **Volatility of volatility**: c gives sd(log IV) of 0.90 to 1.19 and a
  one-sigma volatility ratio of 1.57 to 1.82. Naive Var(log RV) at
  five-minute-equivalent sampling overstates the variance of log IV by 6 to 153
  percent, rising sharply as the horizon shortens.

### Kill-condition outcomes, S11

- **K4 (risk-limit breaches): FIRES**, on both criteria independently. The
  leverage cap never binds in 2,524 decision points. Stop-out spurious rate 0.16
  to 0.97 percent against a 1 percent threshold; cost 0.0003 to 0.042 bps against
  1 bp, across the full 0.5/1/2/4-tick sweep. Every spurious episode lasted one
  day. Observation not covered by item 92: the MISSED breach rate (0.81 to 2.25
  percent) exceeds the spurious rate in three of four cells.
- **K5 (combination weights): FIRES.** Tracking-error criterion 0.50 percent
  maximum against 5 percent. The weight criterion passes by 4e-5 (ES/GLOBEX mean
  |dw| = 0.019960 against 0.02) and would be a coin flip on that cell alone; K5
  fires because item 93 requires either. No corrected MSE fell to zero, so no
  model was excluded. Median pairwise forecast correlation 0.775.
- **K6 (convexity): DOES NOT FIRE.** Brockhaus and Long (2000) second-order
  adjustment, sqrt(E[V]) * (exp(s^2)-1)/8. Naive s^2 overstates the adjustment by
  **10.8 to 443 percent** in all eight cells against a 5 percent threshold; on a
  20 percent variance-swap strike the error is 0.53 to **13.96 volatility
  points**. The naive adjustment is too large, so the implied volatility-swap
  strike is too low, favouring the side long volatility at the quoted strike. No
  options data is held; this is a pricing-bias calculation and no claim is made
  about executable P&L.

**Item 91's structural claim survives in a sharper form.** Proxy noise is
second-order at a threshold when the threshold sits far from the distribution,
and first-order in a RATIO. The one decision of the three that fails is the only
one where the quantity of interest is a function of the VARIANCE OF the
volatility estimate rather than of its level.


## 14. S12 corrections (2026-08-19)

| item | element | fixed | status |
|---|---|---|---|
| 95 | The S11 Phase 10 convexity magnitude is VOID: the Brockhaus-Long second-order expansion was applied at Var(V)/E[V]^2 of 1.8 to 6.8. Under lognormal V the exact relation needs no expansion. | 2026-08-19 | POST HOC |
| 96 | The S11 Phase 6 mechanism claim is provisional pending calibration verification. | 2026-08-19 | POST HOC |
| 97 | The S11 Phase 3 trend p-value is not trustworthy as stated; cluster-robust inference is downward-biased below ~30 clusters. Point estimate stands, inference replaced by wild cluster bootstrap. | 2026-08-19 | POST HOC |
| 98 | K4 is restated by limit. The leverage cap never bound, so a joint determination overstates coverage. | 2026-08-19 | POST HOC |
| 99 | K4's missed-breach asymmetry, observed and not written into item 92. Directional finding, not a kill-condition outcome. | 2026-08-19 | POST HOC |

### Item 95 discharged: convexity on the exact relation

**K_vol = E[sqrt V] = sqrt(E[V]) * exp(-s2/8)**, exact under lognormal V by the
lognormal MGF at t = 1/2. No expansion; the single assumption is lognormality of
V, which the intercept route already makes in reading c as Var(log IV).

The Brockhaus-Long second-order form departs from exact by 10 percent at
**kappa = Var(V)/E[V]^2 = 0.182** (s2 = 0.167). Measured kappa runs **1.26 to
6.84**, 7 to 38 times past the boundary; at s2 = 2.5 the expansion returns a
negative strike. The exact-to-expansion ratio runs 0.265 to 0.615.

Corrected overstatement of the convexity adjustment: **5.9 to 134.3 percent**
(S11's 10.8 to 443 percent is void). Maximum difference **2.60 volatility points**
on a 20 percent strike (S11's 13.96 is void). ES/GLOBEX is +19.3 percent, matching
item 95's hand recompute.

**K6 DOES NOT FIRE**, threshold unchanged at 5 percent, in all 16 rows. The margin
is much narrower than S11 reported: the tightest cell, NQ/GLOBEX, is at **5.94
percent against 5 percent**, and NQ/RTH/1day at 6.87 percent. Direction unchanged:
the naive adjustment is too large, the implied volatility-swap strike too low,
favouring the side long volatility at the quoted strike. No options data is held;
pricing bias only, no claim about executable P&L.

### Item 96 discharged: determination A, the calibration is correct

Implied RQ/RV^2 at the S11 calibrated sigma_w equals Part A's measured value at
**24 of 24 calibration points, maximum proportional discrepancy 1.2e-7**. The
sigma_w -> RQ/RV^2 mapping is **monotone increasing in all twelve (geometry, H)
slices** with exactly one crossing of each target and **no second solution near
0.6** (implied ratio there is 1.00 to 1.10 against targets of 1.51 to 3.61). No
far branch, no wrong target, no recalibration required.

Item 96's suspicion is refuted but its concern was well founded: **sigma_w is not
the standard deviation of log within-window variance.** In `make_a6` it scales a
fractional Brownian path normalised to unit variance at the window's TERMINAL
point, which is then divided by its own within-window mean. The interpretable
dispersion is **0.764 to 1.803 in standard deviation of log within-window
variance**, not 1.495 to 4.805. The S11 statement is corrected in units.

The range claim is also narrowed. Against the observed range as restated,
[-0.97, -0.44], the calibrated A6 exponent lands inside for **both GLOBEX cells at
6 of 6 Hurst indices**, but for ES/RTH at 1 of 6 and NQ/RTH at 3 of 6.

**Corrected mechanism claim**: calibrated within-window volatility dispersion
reproduces the observed exponent in both GLOBEX cells at every Hurst index and in
the RTH cells only at some, while the Hurst index itself does nothing in any cell.
The non-monotonicity of the b-H map and its range sitting inside seed noise are
unaffected, so no inversion to an implied H is possible.

### Item 97 discharged: wild cluster bootstrap

Rademacher weights, 9,999 replications, null imposed on restricted residuals
(Cameron, Gelbach and Miller 2008), clustering on the eight distinct cells; 95
percent interval by inverting the same test over 121 grid points.

| version | beta | cluster-robust t | p cluster-robust | p wild cluster bootstrap | WCB 95 percent interval |
|---|---|---|---|---|---|
| **8 distinct cells** | **-0.04690** | -4.190 | 0.00409 | **0.0066** | **[-0.0760, -0.0245]** |
| 16 cells (B0+B1 duplicated) | -0.04690 | -5.926 | 0.00003 | 0.0000 | [-0.0643, -0.0303] |

**The observed 0.0066 is below the attainable floor.** At G = 8 there are 2^7 =
128 distinct values of |t*|, so the smallest two-sided p-value the design can
produce is 1/128 = 0.0078; 0.0066 is Monte Carlo noise around that floor. The
honest statement is **p <= 0.0078, the smallest value this design can return**.
The test is saturated and no result at G = 8 should be read as conventional
evidence at any nominal level. The **point estimate of -0.047 per year stands**,
all sixteen cells have a negative slope, and the sign is not in question.

### Item 98 discharged: K4 restated per limit

| limit | status | basis |
|---|---|---|
| **Stop-out at 1.5x target** | **FIRES** | both criteria: max spurious rate 0.966 percent vs 1 percent, max cost 0.042 bps vs 1 bp across the full sweep |
| **Leverage cap at 2.0x** | **UNTESTED** | bound 0 of 2,524 decision points; maximum leverage attained 1.434x, so a cap at or below 1.434x would first bind; minimum headroom 1.39x |

**The S11 joint K4 determination is superseded.** A 2.0x cap on a 10 percent-vol
strategy requires realized daily volatility below about 0.315 percent, roughly 5
percent annualised, which the 2024-2026 holdout never delivered.

### Item 99 recorded: the missed-breach asymmetry

Missed breach rate exceeds the spurious rate in **three of four cells**, by up to
a factor of 6.5 (ES/RTH 2.254 percent missed against 0.644 percent spurious;
NQ/RTH is the exception at 0.805 against 0.966). Mechanism: noise inflates the
estimated volatility entering the position size, so the proxy-sized position is
smaller than the kernel-sized one precisely when volatility is genuinely high; the
smaller position produces a smaller realized portfolio volatility and the stop-out
is not triggered when it should be. A consequence of sizing on a noisy estimate,
not of the threshold. Directional finding, not a kill-condition outcome.

### Net effect on the programme's conclusions

Nothing is withdrawn. Corrected: the convexity magnitudes, the units of the
sigma_w statement, the breadth of the A6 range claim, the trend p-value, and the
scope of K4. Standing: K6 DOES NOT FIRE (at a minimum margin of 5.94 percent
rather than 10.8), K5 FIRES, the stop-out leg of K4 FIRES, the trend point
estimate, the mechanism claim in corrected form, and everything in S09 and S10
these corrections do not touch. **The one substantive change in a conclusion is
the margin on K6: reported as overwhelming, it is merely clear.**


## 15. S13 additions (2026-08-19)

| item | element | fixed | status |
|---|---|---|---|
| 100 | The within-window dispersion mechanism is partial, not general: 6 of 6 Hurst indices in range for both GLOBEX cells, 3 of 6 for NQ/RTH, 1 of 6 for ES/RTH. | 2026-08-19 | POST HOC |
| 101 | The open-bar candidate for RTH. Arm A7 places one amplitude-matched dominant return at a fixed within-window position. Pre-registered reading stated in the item. | 2026-08-19 | PRE-REGISTERED |
| 102 | Risk parity is the second first-order application: E[1/sigma_hat] exceeds 1/sigma, so an asset measured with more proxy noise is systematically overweighted. | 2026-08-19 | PRE-REGISTERED |
| 103 | K7, risk parity. Fires if the mean absolute weight deviation is below 0.02, or the out-of-sample realized-volatility difference below 5 percent relative at every cost-sweep point. | 2026-08-19 | PRE-REGISTERED |
| 104 | The anomaly is largely historical and its shape is untested: smooth decline against a level shift at a date. | 2026-08-19 | PRE-REGISTERED |
| 105 | The holdout is read once more, in Phase 2 only, as the FOURTH opening, with the running count stated. | 2026-08-19 | POST HOC, disclosed |

### Item 101 answered: REJECTED. The RTH residual is not an open-bar effect

Measured first: the RTH daily open bar carries **1.921x (ES) and 2.733x (NQ)** the
average sub-bar against **1.446x and 1.149x** on GLOBEX, confirming item 101's
premise. The RTH close is also elevated, at 2.318x on ES, which item 101 did not
anticipate. Amplitude calibrated by bisection to kappa of 5.20, 3.14, 7.25 and
9.80 on one minute's variance.

Arm A7 gives b between **-1.008 and -1.180 across four within-window positions and
both geometries**, sitting at the sampling-theory reference of -1.14 to -1.21.
**Not one of sixteen configurations enters the observed range [-0.97, -0.44]**,
and the spread across positions is inside the between-seed dispersion, so the
effect depends on neither position nor presence.

Arm A8, calibrated dispersion and the dominant return together, is
indistinguishable from A6 alone: GLOBEX 6 of 6 in range for both roots, ES/RTH
3 of 6 against A6's 1 of 6 and NQ/RTH 2 of 6 against A6's 3 of 6, the two moving
in opposite directions and both inside seed noise.

**Item 100's gap is now harder.** Three mechanisms have been tested against the
RTH residual -- i.i.d. heavy tails (S10, 8.6 percent of the gap, inside seed
noise), calibrated within-window dispersion (S11/S12, GLOBEX only) and a
fixed-position dominant return (here, null). The RTH residual survives all three.

### K7 answered: FIRES

Exact relation used per item 95: **E[1/sigma_hat] = (1/sigma) exp(v/2)** with
v = Var(log sigma_hat) = w/4; the second-order expansion departs by 10 percent at
v = 0.375, well above the measured 0.0006 to 0.0378. ES carries v of 0.0378
single-day against NQ's 0.0129, so **ES is systematically overweighted**, as item
102 predicts.

Two-asset ES/NQ book, RTH daily, monthly rebalance, 21-session trailing estimate.
Holdout: mean absolute weight deviation **0.000145 against a 0.02 threshold**, and
a realized portfolio volatility difference of **0.0038 percent against 5 percent**,
identical at all four cost-sweep points. **K7 FIRES on both criteria.**

Bounded rather than reported alone. On the widest reliability spread measured
(lambda 0.396 against 0.940), an ILLUSTRATION on measured reliabilities and not a
backtest: a **daily**-rebalanced book implies a weight deviation of **0.0370,
which exceeds the 0.02 threshold**, while a monthly one implies 0.0018. The bias
is real and correctly signed but is governed by the estimation window, not by the
reliability gap alone: averaging 21 sessions divides the proxy-noise variance and
the bias term by 21. Inverse-volatility weighting is first-order in principle and
second-order at any realistic rebalance frequency.

### Item 104 answered: INDETERMINATE, with the reason named

| specification | RSS | parameter | bootstrap p | share of residual |
|---|---|---|---|---|
| cell effects only | 2.5969 | — | — | — |
| linear trend | 1.8577 | -0.0469/yr | 0.0086 | 28.5 percent |
| level shift, tau-hat = 2022 | 1.7968 | -0.258 | 0.0038 (sup-F) | 30.8 percent |
| **single-year 2022 dummy** | **1.4504** | **-0.405** | — | **44.2 percent** |

The break narrowly beats the trend, by 3.3 percent of RSS, but **a one-year 2022
dummy beats both by 19 percent**. 2022 is the minimum year in 6 of 8 cells and b
reverts toward its pre-2022 level in 2023 in **8 of 8**, which a level shift does
not predict. Excluding 2022, the linear slope halves to **-0.0275 per year**
(p = 0.0059) and the selected break moves to 2019 (p = 0.0207).

**Roughly 40 percent of the headline -0.047 per year is 2022 alone.** The claim
that the anomaly is shrinking is supportable; the claim that it is closing
smoothly is not, and neither is a level-shift account. Eight-cluster limitation
applies throughout: the wild cluster bootstrap floor at G = 8 is 2^-7 = 0.0078 and
the sup-F p of 0.0038 sits below it, so the test is saturated.

### Convexity frequency prescription

S12's exact relation evaluated at every grid point, 20 percent strike, intervals
from the S10 bootstrap on c. Fourteen of 128 rows clear the 5 percent threshold;
ten of sixteen cells have at least one frequency that does.

| cell | minutes per sub-bar required | bias at 5-minute sampling |
|---|---|---|
| ES/GLOBEX/1day, NQ/GLOBEX/1day | **1.0** | +19.3, +5.9 percent |
| ES/RTH/1day, NQ/RTH/1day | **1.0** | +17.6, +6.9 percent |
| NQ/RTH/1h | **1.0** | +21.0 percent |
| ES/RTH/1h | **unreachable** (best +28.5 percent) | +62.6 percent |
| ES/RTH/30min, NQ/RTH/30min | **unreachable** (best +71.5, +14.1 percent) | +134.3, +42.1 percent |

**The prescription is one-minute sampling, and only at the daily horizon.** At the
30-minute horizon on either instrument and the hourly horizon on ES, no frequency
in the grid brings the bias under 5 percent: the shortest windows do not contain
enough returns for the proxy's own dispersion to fall below the quantity being
measured. Maximum bias 2.77 volatility points on a 20-point strike. No options
data is held; pricing bias only, no claim about executable P&L.

### Holdout read count

Four openings to date: S09 Phase 6, S11 Phase 1, S11 Phases 8-9, S13 Phase 2. The
programme is not single-use on the holdout and is reported as such rather than
described otherwise.


## 16. S14 additions (2026-08-20)

| item | element | fixed | status |
|---|---|---|---|
| 106 | The first four applications were chosen badly, disclosed. The operative criterion is that the quantity depends on the VARIANCE of the estimate and more data does not reduce the contamination. | 2026-08-20 | POST HOC, disclosed |
| 107 | K8, regime misclassification. Threshold at the in-sample median of log realized variance, which sits inside the distribution and binds at every decision point. Fires below 5 percent in every cell. | 2026-08-20 | PRE-REGISTERED |
| 108 | K9, HAR persistence attenuation. Fires if the corrected daily coefficient differs from naive by less than 10 percent relative in every cell. The point forecast is NOT claimed to change. | 2026-08-20 | PRE-REGISTERED |
| 109 | K10, Hurst bias. Fires if corrected H differs from naive H by less than 0.02 in every cell. | 2026-08-20 | PRE-REGISTERED |
| 110 | The holdout is read once more, in Phase 1 only, for K8. Fifth opening, running count stated. | 2026-08-20 | POST HOC, disclosed |

### The criterion works: four fired, three fail

K3, K4, K5 and K7 all fired. K8, K9 and K10, selected on item 106's criterion, all
**DO NOT FIRE**. The dividing line is now empirical: proxy noise is second-order in
volatility targeting, risk limits, combination weights and risk parity, and
first-order in regime classification, reported HAR persistence and the Hurst
exponent. The second group shares two features: the quantity depends on the
variance of the estimate, and averaging over more data does not remove the
contamination.

### K8 DOES NOT FIRE

Exact relation derived here: with thresholds at the respective medians and
lognormal noise, **misclassification rate = arccos(sqrt(lambda)) / pi**, since
Corr(log RV, log IV) = sqrt(lambda). Analytic rate **7.9 to 13.6 percent**, above
the 5 percent threshold in every cell. Tercile-split empirical rate **6.0 to 11.9
percent**, above in all eight cell-sample combinations. Median-split empirical
rate 2.7 to 5.2 percent, below in three of four holdout cells and above in one.

The analytic and empirical rates diverge by 50 to 77 percent because the empirical
figure compares two estimates computed on the same window, whose errors are
positively correlated; it is a LOWER BOUND on disagreement with integrated
variance. Error concentrates in the nearest distance quintile (13 to 15 percent)
and is essentially zero beyond it (0.0 to 0.3 percent).

Priced illustration, not a backtest: excess switching cost from spurious regime
changes reaches **138 bps at 4 ticks per leg**, three to four orders of magnitude
above K4's 0.042 bps, because a median threshold binds every day whereas a 2.0x
leverage cap never bound at all.

### K9 DOES NOT FIRE

Matrix errors-in-variables correction, **beta = (Sigma_XX - Sigma_E)^-1 Sigma_XX
beta_hat**, with Sigma_E = v [[1, 1/5, 1/22], [1/5, 1/5, 1/22], [1/22, 1/22,
1/22]] from the shared-day structure of the HAR regressors. The daily coefficient
shifts by **+19 to +116 percent** against a 10 percent threshold. Total
persistence barely moves (0.928-0.934 to 0.939-0.971) but the daily share of it
goes from 45-53 percent to **54-111 percent**, and the weekly coefficient changes
sign on ES/GLOBEX.

Item 108's limit is honoured and measured, not asserted: the corrected
coefficients forecast **worse** by 0.9 to 32.3 percent in RMSE, in sample and
pseudo-out-of-sample. The naive coefficients are the best predictors of a noisy
target from noisy regressors; the corrected ones are consistent estimates of the
structural lag relation. The claim is about reported persistence and relative lag
structure and nothing else.

### K10 DOES NOT FIRE

Proxy noise adds a nugget of **2 Var(eps)** to the increment second moment at
every lag, with Var(eps) = (1 - lambda) Var(log RV_M). Corrected H differs from
naive by **0.032 to 0.208** against a 0.02 threshold, in every cell at every q of
0.5, 1 and 2. Naive H 0.148-0.189; corrected 0.184-0.397. The nugget is **126
percent of the increment moment at lag 1** and stays above 10 percent of it out to
lag 33-40, so there is no lag region where the correction is immaterial.

Cont and Das (2024) is the position TESTED, not assumed, and lambda measures the
nugget along the sampling-frequency axis rather than the lag axis, so the test is
not circular. **Partial, instrument-dependent confirmation**: H roughly doubles on
the noisier instrument (ES, lambda 0.83-0.84, 0.17-0.19 to 0.33-0.40) and moves
about 0.035 on the cleaner one (NQ, lambda 0.93-0.94). The size of the correction
tracks the measured noise, as predicted. No point estimate reaches 0.5; only
ES/GLOBEX has a bootstrap interval including it, [0.305, 0.572] at q = 0.5.
"Rough volatility is entirely a noise artifact" is not supported; "the roughness
estimate is biased downward by proxy noise in proportion to that noise" is.

### The A7 amplitude bound: localized mechanisms retired

A localized feature carrying share s of realized variance contributes an
**M-invariant floor of 2 s^2**, so supplying a required excess X needs
s = sqrt(X/2). At the five-minute equivalent:

| cell | required share | measured share | ratio | floor supplied vs required |
|---|---|---|---|---|
| ES/GLOBEX | 32.3 percent | 0.45 percent | 71.5x | 4.1e-05 vs 0.209 |
| NQ/GLOBEX | 17.6 percent | 0.41 percent | 43.4x | 3.3e-05 vs 0.062 |
| ES/RTH | 30.0 percent | 2.93 percent | 10.3x | 1.7e-03 vs 0.180 |
| NQ/RTH | 16.1 percent | 4.04 percent | 4.0x | 3.3e-03 vs 0.052 |

Shortfall of 4 to 72 times in share, hence **16 to 5,100 times in the floor**,
since the floor goes as the square. A kappa sweep at five seeds per point confirms
it: b never leaves -1.07 to -1.26 even when a single sub-bar carries **more than
half** the window's realized variance. **S13's A7 rejection is now powered and the
whole class of localized mechanisms is retired quantitatively.**

### The 2022 excursion is predominantly an identification artifact

Regressing the within-cell year-to-year deviation in b on fit diagnostics, 64
observations with cell fixed effects: **log10(condition number) alone explains 91
percent** (coefficient -1.146, t = -23.5), A/c 20 percent, RMSE 13 percent, the
2022 dummy 44 percent. Jointly, condition number takes -1.169 and A/c becomes
insignificant. **Adding the 2022 dummy on top shrinks its coefficient from -0.405
to -0.082**, an 80 percent reduction, raising R-squared only from 0.911 to 0.922.

2022 carries a mean condition number of 112 against 55 elsewhere and a mean fitted
c of 0.569 against 0.829: the intercept collapses in the high-volatility year and
the fit becomes ill-conditioned. That is the S10 volatility-tercile pathology in
milder form -- conditioning on realized volatility removes the cross-sectional
log-IV variation that identifies the intercept.

**This qualifies the trend result a second time.** S13 attributed about 40 percent
of the -0.047 per year to 2022; S14 attributes most of that 40 percent to fit
conditioning rather than to the market changing. What survives is a small, poorly
identified drift.

### Holdout read count

Five openings: S09 Phase 6, S11 Phase 1, S11 Phases 8-9, S13 Phase 2, S14 Phase 1.


## 17. S15 confound checks (2026-08-20)

| item | element | fixed | status |
|---|---|---|---|
| 111 | K10 carries a lag-selection confound: corrected S(Delta) goes negative at short lags and short lags identify H. No Hurst figure reportable until naive H is refitted on the surviving subset. | 2026-08-20 | POST HOC |
| 112 | K9 assumes classical measurement error and the programme's central finding disputes it. If part of the excess is a price-process property the correction over-corrects. | 2026-08-20 | POST HOC |
| 113 | The trend has not been tested against the conditioning control. If the year coefficient does not survive, the shrinking-anomaly claim comes out of the paper. | 2026-08-20 | POST HOC |
| 114 | No further measurement session follows S15. The next artifact is the paper. | 2026-08-20 | POST HOC |

### Item 111 discharged: K10 SURVIVES

Only **one lag of forty is ever dropped**, on ES/GLOBEX, where the nugget exceeds
S(1). The decomposition, with naive-on-subset reported as its own column:

| cell | H naive all lags | H naive surviving subset | H corrected subset | from lag selection | from nugget | share lag selection |
|---|---|---|---|---|---|---|
| ES/GLOBEX q0.5 | 0.1887 | 0.1834 | 0.3968 | **-0.0053** | +0.2134 | **-2.5 percent** |
| all other cells | — | identical to all-lags | — | **0.0000** | full shift | **0 percent** |

**Lag selection contributes at most -0.0053 and its share is negative**: dropping
lag 1 LOWERS naive H, so the selection works against the reported shift rather
than creating it. Item 111's mechanism does not operate over a 2-to-40 window on
these series.

On the fixed common window of lags 2 to 40, free of any per-cell selection, the
shift is **+0.0265 to +0.2134**, above the 0.02 threshold in every cell at every
q. Those are the conservative figures and are the ones to quote; ES/RTH's
corrected H is 0.284-0.291 on the common window against 0.338-0.352 on the full
window.

**The real sensitivity is one item 111 did not raise**: H depends non-linearly on
the assumed nugget size. On ES/RTH the last 25 percent of the nugget moves H by
0.089, more than the first 75 percent does. **The direction and the
reliability-ordering of the K10 result are robust; the magnitude is not.**

### Item 112 discharged: K9 IS WITHDRAWN AS INDETERMINATE

Conditioning is not the explanation. The corrected matrix has minimum eigenvalue
0.045 to 0.068 against 0.074 to 0.085 uncorrected, and condition number 37 to 58
against 33 to 35 — better conditioned than most fits in this programme. **The
ES/GLOBEX weekly sign flip is not a near-singularity artifact.**

The classical assumption is violated but mildly. Corr(proxy error, level) is
**-0.13 to -0.37**, decisive by t (5.7 to 17.4), but explains only 1.7 to 13.5
percent of error variance. On item 112's own proposed sensitivity — scaling
Sigma_E by the classical fraction — the daily shift stays at 18.9 to 86.6 percent
and the sign flip survives.

**The damage comes from a different door.** v = A*M^b is **2.4 to 11 times** the
directly measured RV-versus-kernel disagreement (ratio 9.1, 15.1, 27.1, 41.8
percent), because it treats the entire excess over Var(log IV) as measurement
error when that excess decays at M^-0.44 and S11 attributes part of it to
within-window volatility dispersion, a price-process property.

| Sigma_E specification | daily shift range | weekly sign flip | verdict |
|---|---|---|---|
| v from A*M^b (S14's choice) | +19 to +116 percent | yes, ES/GLOBEX | DOES NOT FIRE |
| scaled by the classical fraction | +19 to +87 percent | yes, ES/GLOBEX | DOES NOT FIRE |
| **scaled to the measured error variance** | **+4.8 to +7.2 percent** | **no** | **FIRES** |

The first over-corrects; the third under-corrects, because the kernel shares the
window with RV so their difference understates both errors. **The interval spans
the 10 percent threshold and no determination on K9 is reportable.** S14's claim
that the daily share of persistence moves from 45-53 percent to 54-111 percent is
**WITHDRAWN**. What survives, unchanged under every scaling: attenuation raises
the daily coefficient and lowers the weekly and monthly in every cell, total
persistence is nearly unchanged (0.93 against 0.94-0.97), the effect is ordered by
measured reliability, and the corrected coefficients forecast worse.

### Item 113 discharged: the trend SURVIVES at a fifth of its size

Wild cluster bootstrap, Rademacher, 9,999 replications, null imposed, eight
distinct cells, interval by test inversion:

| specification | year coefficient | cluster SE | bootstrap p | 95 percent interval | VIF | R2 within |
|---|---|---|---|---|---|---|
| year only (S11/S13) | **-0.0469** | 0.0112 | 0.0076 | [-0.0749, -0.0245] | 1.00 | 0.285 |
| **year + log(condition number)** | **-0.0105** | 0.0043 | 0.0036 | **[-0.0211, -0.0020]** | 1.27 | 0.921 |
| year + log(cond) + A/c | -0.0104 | 0.0041 | 0.0030 | [-0.0207, -0.0025] | 1.27 | 0.922 |

**The year coefficient shrinks by 78 percent** and the interval still excludes
zero. VIF of 1.27 shows this is a genuine reallocation of explained variation, not
collinearity. Implied movement over 2016-2023 is **0.073, not 0.375** — about 20
percent of the mean residual gap of 0.357, where S12 and S13 reported roughly
half. **Four-fifths of the headline trend was fits becoming less identified in
high-volatility years.**

Eight-cluster limitation, stated regardless of outcome: the attainable p-value
floor at G = 8 is 2^-7 = 0.0078 and all three p-values sit at or below it. The
test is saturated and none of these is conventional evidence at any nominal level.

### Numbering collision, recorded

The label **K1** was used in S05 for the MCS-composition condition, and item 61
re-labelled that same condition **K2** from S08 onward, while spec section 7
already used K2 for grid-invariance. Both labels are shown against content in the
S15 report's consolidated table.

### The item-106 criterion's predictive record

Of seven applications chosen BEFORE the criterion was articulated, five fired, one
did not (K6) and one was untestable (K4's leverage cap). Of the three chosen
AFTER it, **none fires**: K8 and K10 fail outright, K9 is indeterminate and cannot
be shown to fire under the noise specification S14 used. The criterion is 3 for 3
on direction. Two cases sharpen it: K6 predates the criterion but is a ratio and
would have been selected by it, so the criterion is not merely descriptive of what
was tried afterwards; and K9's indeterminacy is a failure of the noise measurement
feeding the application, not of the selection rule — the programme's central open
question resurfacing inside an application.

### Recorded as further work, not pursued (item 114)

Settling Sigma_E by measuring proxy error against an instrument that does not
share the window; the RTH residual, which survives three tested mechanisms; and
the roughness question, where the programme can now state a bias direction and an
ordering across instruments but not a level.


## 18. S16 regime classification under measured reliability (2026-08-20)

| item | element | fixed | status |
|---|---|---|---|
| 115 | Item 114 amended: S16 runs because K8 measured 7.9-13.6 percent misclassification and 138 bps of spurious switching without testing whether correcting the observable reduces either. | 2026-08-20 | POST HOC, disclosed |
| 116 | The rule is sourced, not invented: Blake, Gandhi and Jakkula, arXiv 2510.03236. Gaussian HMM on a z-scored smoothed RV series, rolling 441-observation window stepped one at a time, two regimes. | 2026-08-20 | PRE-REGISTERED |
| 117 | The source assumes away what this project measures, and its 5-day moving average is an unmotivated noise treatment. | 2026-08-20 | POST HOC |
| 118 | Three arms: A1 raw log RV, A2 the published 5-day moving average, A3 shrinkage at the measured lambda. Only the observable differs. | 2026-08-20 | PRE-REGISTERED |
| 119 | K11 fires if A3 reduces misclassification by less than 1 pp against BOTH A1 and A2 in every cell, or if the allocation Sharpe difference is below 0.10 at every cost-sweep point. | 2026-08-20 | PRE-REGISTERED |
| 120 | The recoverable band is reported before any P&L. | 2026-08-20 | PRE-REGISTERED |
| 121 | Holdout opens a sixth time, Phase 3 only. | 2026-08-20 | POST HOC, disclosed |

### Item 120 discharged: THE BAND IS EMPTY, and it is empty by construction

A3 is AFFINE in A1 and the item-116 specification z-scores WITHIN each rolling
window, so for any window W

    (z - mean_W(z)) / sd_W(z) = (x - mean_W(x)) / sd_W(x)

exactly, for every lambda > 0. The z-scored HMM input is identical under A1 and
A3. **The recoverable band is empty and the ceiling on any improvement is 0.0
percentage points.** Verified numerically: maximum absolute z-score difference
**6.3e-15** across all eight cells.

Reach by treatment: A3 under the published specification **0.00 percent**; A3
under a fixed threshold (labelled diagnostic, changes a component) 0.04 to 0.89
percent; **A2, the published moving average, 13.0 to 20.1 percent**.

### K11 DOES NOT FIRE, and the verdict inverts what item 119 anticipated

| | reduction in misclassification | Sharpe difference |
|---|---|---|
| attributable to the reliability correction (A3 vs A1) | **0.00 pp in all 8 cells** | **0.0000 at all 16 sweep points** |
| attributable to not applying the moving average (A3 vs A2) | **1.10 to 38.08 pp** | up to **0.259** |

Both item-119 clauses fail, so K11 does not fire — but every point of the
measured effect is A3 not being A2. Had K11 been stated against A1 alone it would
have fired trivially. The measured contribution of the correction, 0.00 pp,
equals the Phase 1 ceiling exactly: **the correction did not fail, it was never
able to act.**

### The published smoothing is the costly step

Misclassification against an HMM run on the finest-grid realized kernel, holdout:

| cell | A1 = A3 | A2 (published 5-day MA) |
|---|---|---|
| ES/GLOBEX 1day | 1.25 percent | **11.86 percent** |
| NQ/GLOBEX 1day | 3.28 percent | **15.13 percent** |
| ES/RTH 1day | 2.25 percent | **11.59 percent** |
| NQ/RTH 1day | 5.64 percent | **12.40 percent** |
| ES/RTH 1h | 5.15 percent | **14.76 percent** |
| NQ/RTH 1h | 7.94 percent | **46.03 percent** |

A1 and A3 produce **zero differing states** out of 641 to 7,452 observations per
cell, in sample and out. A2 reflips 8.5 to 42.9 percent of days and gets a large
share wrong. It switches less than A1 (26-32 against 40-48 daily) because a
moving average is a low-pass filter, so it buys turnover reduction at the price
of accuracy. **The correction recovers exactly 0 of K8's 138 basis points.**

### Two further results, neither about the correction

**The HMM's temporal context does what an affine correction cannot.** The
empirical rate on A1 (2.1-3.6 percent daily) sits far below the pointwise
analytic rate arccos(sqrt(lambda))/pi of 7.9-13.6 percent. Pooling 441
observations suppresses misclassification by a factor of three to six.

**The allocation overlay destroys value regardless of the observable.** Sharpe at
1 tick: always-invested 0.690, 0.643, 0.164, 0.019 against overlay -0.017, 0.356,
-0.306, -0.095. The **reference_kernel** control, classifying on the noise-robust
proxy, also underperforms always-invested in every cell, so the failure is not a
classification-quality problem a better observable could repair.

### The general lesson

Any affine adjustment to an observable is removed exactly by within-window
z-scoring. This applies to the whole class of linear proxy corrections applied
upstream of a normalising classifier, not to reliability shrinkage alone. For a
reliability correction to have reach, one of three things must change: the
normalisation must not be re-derived on the corrected series; the correction must
be non-affine; or it must enter the model rather than the observable, for
instance as a known measurement-error variance in a state-space observation
equation.

### Defect found and corrected, disclosed

The first Phase 3 run built the holdout through S11 `ho_series`, which is
wlen = None and yields daily windows only; the 1h and 30min cells had 621 daily
windows appended to intraday in-sample series. Rebuilt through
`phase6_holdout.wins` at each cell's own horizon; holdout window counts go from a
uniform 621 to 641, 621, 3,726 and 7,452. The four 1day cells and the entire
allocation were unaffected. Both runs are retained, the first marked superseded.

### Holdout read count

Six openings: S09 Phase 6, S11 Phase 1, S11 Phases 8-9, S13 Phase 2, S14 Phase 1,
S16 Phase 3.


## 19. S17 measurement error in the model rather than the observable (2026-08-20)

| item | element | fixed | status |
|---|---|---|---|
| 122 | Result hierarchy, not subject to revision by S17: the scaling exponent, the intercept estimator for lambda, and the first-order criterion are PRIMARY; K1-K12 are applications and are secondary. | 2026-08-20 | PRE-REGISTERED |
| 123 | The S16 A2 finding is provisional pending lag alignment. | 2026-08-20 | POST HOC |
| 124 | The 30min in-sample against holdout inversion is unexplained; label swapping is the leading candidate. | 2026-08-20 | POST HOC |
| 125 | Arm A4: the correction enters the observation equation, with the emission variance decomposed into a state variance plus a KNOWN observation-noise variance held fixed. | 2026-08-20 | PRE-REGISTERED |
| 126 | K12 fires if A4 reduces misclassification by less than 1 pp against A1 in every cell. | 2026-08-20 | PRE-REGISTERED |
| 127 | The observation-noise variance is derived, not tuned: Var(eps) = (1 - lambda) Var(log RV_M), both lambda ranges, four pre-registered scalings. | 2026-08-20 | PRE-REGISTERED |
| 128 | Holdout opens a seventh time, Phase 4 only. S17 is the last measurement session. | 2026-08-20 | POST HOC, disclosed |

### Item 123 discharged: the S16 A2 claim is WITHDRAWN in its stated form

S16 compared a five-day TRAILING filter against a CONTEMPORANEOUS reference. Two
controls, holdout, gap of A2 over A1 in percentage points:

| cell | S16 gap | phase-matched gap | best-lag gap | best lag |
|---|---|---|---|---|
| ES/GLOBEX 1day | +10.61 | **+0.16** | +5.95 | 2 |
| NQ/GLOBEX 1day | +11.86 | **+1.40** | +9.09 | 2 |
| ES/RTH 1day | +9.34 | **+1.77** | +5.18 | 2 |
| NQ/RTH 1day | +6.76 | **-3.06** | +3.25 | 2 |
| ES/RTH 1h | +9.61 | **-0.13** | +4.73 | 2 |
| NQ/RTH 1h | +38.08 | **-2.95** | +37.56 | 3 |
| ES/RTH 30min | +1.10 | **-3.42** | +0.56 | 4 |
| NQ/RTH 30min | +6.62 | +19.65 | +4.57 | 1 |

**The best lag is 2 days in every daily cell**, exactly what a five-day trailing
mean induces. Under phase matching the gap is negative in four of eight cells and
below 2 pp in six. NQ/RTH/1h, which S16 reported at 46.03 percent, is
distinguishable from chance (p < 1e-5 at n = 3,726) but its phase-matched rate is
**4.99 percent against A1's 7.94** -- the 38-point gap is entirely phase and
scale. The item-117 objection to the moving average as UNMOTIVATED stands on its
own terms; the empirical case S16 built for it does not.

### Item 124 discharged: the inversion REMAINS UNEXPLAINED

Label instability is real and sits exactly where item 124 predicted -- NQ/RTH/30min
carries 17.4 percent of in-sample windows with a state-mean gap below 0.25 against
6.9 percent in the holdout, and ES/RTH/30min carries none. But restricting to
windows separated by at least 0.50 moves the in-sample rate 48.476 to 47.808 and
the holdout 26.526 to 26.564, **about 3 percent of a 21.95 pp inversion**. Mean
separation is 1.709 in sample against 1.668 in the holdout, so a change in
separability is ruled out too. Neither candidate accounts for it. The S16 figures
are NOT superseded -- no corrected labelling produces different numbers -- but are
flagged as carrying an unexplained inversion.

### K12 FIRES, and the reach makes the null informative

**Identifiability condition, which is also the reach condition.** With
sigma_k^2 = max(total_k - v, 0) the emission variance is max(total_k, v), so A4 is
the free-variance HMM WITH A VARIANCE FLOOR at v, identical to A1 wherever both
states clear the floor.

**Validation** (seed 20260841, T = 3,000, v = 0.30): the free HMM recovers the
TOTAL variance (0.4225 against a true 0.4225); the fixed-noise HMM recovers the
STATE variance by subtracting known v (0.1225 against a true 0.1225); their means
agree to ten decimal places.

**Reach, reported before any outcome.** The floor never binds at the daily horizon
(0 of ~1,460 windows in all four cells) and binds in most windows intraday (88
percent at ES/RTH/1h, 97 percent at ES/RTH/30min). Across all cells and scalings,
**46,120 of 72,619 windows bind and 18,311 in-sample states differ from A1.**

**Outcome.** Maximum reduction **0.00 pp at every one of the four scalings**, in
every cell. Where it acts it degrades: ES/RTH/1h -0.70 pp on the holdout,
ES/RTH/30min -0.42 pp. At the RESTRICTED lambda for ES/RTH/1day, lambda = 0.347
gives v = 0.841, the floor binds in 100 percent of windows and holdout
misclassification worsens by **10.47 pp** -- the S10-flagged degenerate restricted
fit propagating into an application, and the item-66 both-ranges requirement
earning its place again.

**Attribution per item 126: the noise floor binding, not the change being inert.**
This is the opposite of S16, where the correction had literally zero reach. The
reason is algebraic: a variance floor cannot sharpen a discrimination, only widen
both densities; and in a two-state HMM where both states carry the SAME known
noise, that noise enters both likelihoods and cancels in the posterior ratio.

### The two routes are now both closed

S16 closed the observable side: any affine correction is annihilated by
within-window z-scoring. S17 closes the model side for this class: the emission
route has real reach and no benefit. Between them the two sessions exhaust the
ways a scalar reliability parameter can enter a two-state Gaussian HMM classifier.
**Not established**: that lambda is wrong, or that measurement error is irrelevant
to state-space models generally. A continuous-latent stochastic-volatility model
with a known observation-error variance is a different object and is recorded as
further work.

### Defect in S16's HMM, found and contained

`common16.py:50` divides by `c[0]` without the underflow guard applied at
`c[t>0]` on line 51. When `pi*B[0]` underflows the forward pass returns NaN, the
warm start propagates it, and EM runs its full iteration cap without converging.
**S16's 32 persisted A1/A2 series were audited and are clean** -- the underflow is
reached only by the MA-smoothed kernel series introduced in S17. The S16 artifact
is untouched; S17 guards at the call site, retries cold once, leaves the window
unclassified otherwise, and counts failures.

### The item-106 criterion after twelve conditions

Seven applications chosen before the criterion: five fire, one does not (K6), one
untestable. Five chosen after: K8, K10 and K11 fail, K9 is indeterminate, and
**K12 FIRES** -- the first post-criterion application to do so. That sharpens the
criterion rather than weakening it: a two-state HMM posterior depends on the RATIO
of two densities carrying the same noise, so the noise cancels and the quantity
does not depend on the estimate's variance in the way the criterion requires. The
criterion correctly predicts the null.

### Holdout read count

Seven openings: S09 Phase 6, S11 Phase 1, S11 Phases 8-9, S13 Phase 2, S14 Phase 1,
S16 Phase 3, S17 Phase 4. **S17 is the last measurement session; the next artifact
is the paper.**
