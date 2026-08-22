# Session 13 — Mechanism extension, risk parity, trend structure, convexity table

Four strands. One tests a named candidate for the residual S12 left open on RTH
geometry and rejects it. One adds a third pre-registered application and it fires.
One asks what shape the historical closing of the anomaly has and finds the
question cannot be answered at this sample length, for a specific and instructive
reason. One turns S12's corrected convexity arithmetic into a frequency
prescription.

Interpreter `~/venvs/obs-space-vol/bin/python`, realpath
`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13`, numpy 2.5.2,
pandas 3.0.5, outside every synced path. DECISIONS items 66–99 verified present at
lines 398–593 (34 of 34); items 100–105 appended and verified at lines 601, 606,
613, 620, 626, 630.

**Holdout reads: this is the fourth** (item 105). Prior: S09 Phase 6, S11 Phase 1,
S11 Phases 8–9. This session reads it in Phase 2 only, with no parameter,
threshold, rule or specification changed.

---

## Phase 1 — Arm A7, the open-bar candidate

### Measurement first

Reported before any arm was generated, from the pre-2024 panels
(`phase1_amplitudes.csv`). Mean squared return of the first and last sub-bar
relative to the window mean, and the share of window realized variance each
carries, at the five-minute equivalent:

| cell | M | first ratio | last ratio | first share | last share | uniform share |
|---|---|---|---|---|---|---|
| ES/GLOBEX/1day | 276 | 1.446 | 0.320 | 0.452% | 0.155% | 0.362% |
| NQ/GLOBEX/1day | 276 | 1.149 | 0.292 | 0.406% | 0.136% | 0.362% |
| **ES/RTH/1day** | 78 | **1.921** | **2.318** | **2.93%** | **2.93%** | 1.28% |
| **NQ/RTH/1day** | 78 | **2.733** | 1.566 | **4.04%** | 1.91% | 1.28% |
| ES/RTH/1h | 12 | 1.138 | 0.883 | 9.87% | 7.75% | 8.33% |
| NQ/RTH/1h | 12 | 1.300 | 0.813 | 10.24% | 7.20% | 8.33% |
| ES/RTH/30min | 6 | 1.122 | 0.938 | 18.68% | 16.16% | 16.67% |
| NQ/RTH/30min | 6 | 1.203 | 0.893 | 19.10% | 15.59% | 16.67% |

**The measurement supports item 101's premise.** The RTH daily open bar carries
1.9× to 2.7× the average sub-bar, against 1.15× to 1.45× on GLOBEX, exactly as
item 101 predicted from the 18:00 GLOBEX open into quiet. The RTH close is
elevated too — 2.32× on ES — which item 101 did not anticipate.

### The arm

A7 is A0 (`make_a6` at σ_w = 0: flat within-window profile, i.i.d. lognormal
integrated variance, Gaussian innovations) with one minute's variance multiplied
by κ, calibrated by bisection to the measured first-sub-bar ratio through the same
`quart_suite`-adjacent measurement on both sides:

| cell | target first ratio | κ | achieved |
|---|---|---|---|
| ES/GLOBEX | 1.4464 | 5.20 | 1.4464 |
| NQ/GLOBEX | 1.1493 | 3.14 | 1.1493 |
| ES/RTH | 1.9213 | 7.25 | 1.9213 |
| NQ/RTH | 2.7325 | 9.80 | 2.7325 |

### Result: the open-bar mechanism does nothing

Position sweep, five seeds each (`phase1_arms_agg.csv`):

| cell | start | quarter | mid | end | max seed sd | in [−0.97, −0.44]? |
|---|---|---|---|---|---|---|
| ES/GLOBEX | −1.074 | −1.153 | −1.139 | −1.080 | 0.158 | no |
| NQ/GLOBEX | −1.120 | −1.066 | −1.163 | −1.103 | 0.136 | no |
| ES/RTH | −1.086 | −1.131 | −1.180 | −1.180 | 0.169 | no |
| NQ/RTH | −1.175 | −1.008 | −1.134 | −1.114 | 0.103 | no |

Every value sits at the sampling-theory reference (−1.14 to −1.21). **Not one of
sixteen configurations enters the observed range**, and the spread across the four
positions (0.08 to 0.17) is inside the between-seed dispersion, so the effect
depends on neither position nor presence — there is no effect to depend on either.

**A8**, the calibrated within-window dispersion and the dominant return together,
against A6 (dispersion alone):

| cell | A6 range | A6 in range | A8 range | A8 in range | A7 alone |
|---|---|---|---|---|---|
| ES/GLOBEX | −0.850 to −0.926 | 6/6 | −0.824 to −0.896 | **6/6** | −1.074 |
| NQ/GLOBEX | −0.796 to −0.936 | 6/6 | −0.791 to −0.934 | **6/6** | −1.120 |
| ES/RTH | −0.953 to −1.044 | 1/6 | −0.928 to −1.104 | 3/6 | −1.086 |
| NQ/RTH | −0.894 to −1.050 | 3/6 | −0.935 to −1.051 | 2/6 | −1.175 |

A8 is A6. Adding the dominant return moves the mean b by 0.01 to 0.05, inside
seed noise, and the RTH cells go 1/6 → 3/6 and 3/6 → 2/6 in opposite directions —
noise, not signal. The two mechanisms are not non-additive; the second is null.

### Item 101 reading, stated explicitly

Item 101 pre-registered: *if A7 moves b into the observed range on RTH geometry
and not on GLOBEX, the RTH residual is an open-bar effect.* **A7 moves b into the
observed range on neither geometry. The RTH residual is not an open-bar effect,
and the hypothesis is rejected.**

Item 100's observation therefore stands and sharpens. Two candidate mechanisms
have now been tested against the RTH residual and both rejected: i.i.d. heavy
tails (S10 Phase 4, 8.6% of the gap, inside seed noise) and a fixed-position
dominant return (here, no effect at any position). Calibrated within-window
dispersion explains GLOBEX at 6 of 6 Hurst indices and RTH at 1 to 3 of 6. **The
RTH residual is unexplained after three mechanisms.**

---

## Phase 2 — K7, inverse-volatility risk parity

### Derivation and its boundary

Let log σ̂ = log σ + ε with ε ~ N(0, v), which follows from log RV = log IV + η,
η ~ N(0, w), and σ̂ = √RV, giving **v = w/4**. Then

> **exact (lognormal): E[1/σ̂] = (1/σ)·exp(v/2)**
> second order: E[1/σ̂] ≈ (1/σ)·(1 + v/2)

The exact relation is used throughout, per item 95 and the S12 precedent. The
expansion departs from it by 10% at **v = 0.375**; measured v is 0.0129 to 0.0378
on a single-day estimate and 0.00061 to 0.0018 on the 21-day estimate, so here the
expansion would in fact have been safe — reported because the boundary is the
point, not because it binds.

Measured noise at RTH daily, from the S11 Phase 7 fitted curve at M = 78:

| asset | λ | Var(log RV) noise | v single-day | v 21-day | exact bias, single | exact bias, 21-day |
|---|---|---|---|---|---|---|
| ES | 0.840 | 0.1513 | 0.0378 | 0.00180 | 1.0191 | 1.00090 |
| NQ | 0.931 | 0.0515 | 0.0129 | 0.00061 | 1.0065 | 1.00031 |

**ES is systematically overweighted**, being the less reliably measured of the two.

### The book

Two-asset inverse-volatility book, ES and NQ, RTH daily, monthly rebalance
(21 sessions), 21-session trailing volatility estimate. For two assets,
w_i ∝ 1/σ_i is exactly equal-risk-contribution at any correlation, so the
corrected allocation *is* the equal-risk target.

| sample | estimator | naive vol | corrected vol | relative | mean \|Δw\| | max \|Δw\| | w(ES) naive |
|---|---|---|---|---|---|---|---|
| in sample | 21-day | 0.14724 | 0.14725 | 0.0039% | 0.000145 | 0.000148 | 0.5712 |
| in sample | single-day | 0.14737 | 0.14749 | 0.0814% | 0.003023 | — | 0.5785 |
| **holdout** | **21-day** | **0.14553** | **0.14554** | **0.0038%** | **0.000145** | 0.000148 | 0.5751 |
| holdout | single-day | 0.14409 | 0.14420 | 0.0788% | 0.003036 | — | 0.5776 |

Costs differ by 0.0084% between the two weightings, identically at all four sweep
points, because the weight difference is a level shift and turnover is unaffected.

**K7 FIRES**, on both item-103 criteria and by a wide margin: mean absolute weight
deviation 0.000145 against a 0.02 threshold — a factor of 138 — and a realized
portfolio volatility difference of 0.0038% against 5%.

### Bounding it, rather than reporting one pair

Illustration on the widest reliability spread this programme has measured, ES/RTH
30min (λ = 0.396) against NQ/GLOBEX 1day (λ = 0.940). **Labelled explicitly as an
illustration on measured reliabilities, not a backtest** — these two cells are not
a tradeable pair.

| estimator | bias ratio | implied weight deviation | vs the 0.02 threshold |
|---|---|---|---|
| single-day | 1.1597 | **0.0370** | **exceeds** |
| 21-day | 1.0071 | 0.0018 | clears |

**This is the informative result.** At the widest reliability spread in the cell
set, a *daily*-rebalanced inverse-volatility book would breach item 103's weight
threshold by nearly a factor of two. A *monthly* one would not, because averaging
21 sessions divides the proxy-noise variance by 21 and the bias term with it.

So the mechanism item 102 identifies is real and its sign is as predicted — the
less reliably measured asset is overweighted — but its magnitude is governed by
the estimation window, not by the reliability gap alone. Inverse-volatility
weighting belongs to the first-order class in principle and lands in the
second-order class at any realistic rebalance frequency.

---

## Phase 3 — Trend structure

Within-year b per distinct cell (`phase3_b_by_year.csv`):

| cell | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | **2022** | 2023 |
|---|---|---|---|---|---|---|---|---|
| ES/GLOBEX/1day | −0.633 | −0.704 | −0.486 | −0.544 | −0.540 | −0.683 | **−1.131** | −0.736 |
| ES/RTH/1day | −0.461 | −0.631 | −0.509 | −0.956 | −1.173 | −0.652 | **−1.479** | −1.208 |
| ES/RTH/1h | −0.483 | −0.564 | −0.662 | −0.671 | −0.594 | −0.579 | **−1.179** | −0.670 |
| ES/RTH/30min | −0.594 | −0.557 | −0.390 | −0.629 | −0.511 | −0.625 | **−0.900** | −0.564 |
| NQ/GLOBEX/1day | −0.744 | −0.725 | −0.913 | −0.792 | −0.646 | −0.783 | **−1.100** | −0.823 |
| NQ/RTH/1day | −0.868 | −0.900 | −0.745 | −1.012 | −1.462 | −1.137 | −1.411 | −1.092 |
| NQ/RTH/1h | −0.755 | −0.682 | −1.078 | −0.904 | −0.912 | −0.950 | **−1.105** | −0.873 |
| NQ/RTH/30min | −0.866 | −0.682 | −0.783 | −1.098 | −0.889 | −0.878 | −1.049 | −0.821 |

Gap to the reference closes from a mean of **0.497 in 2016 to 0.324 in 2023**, a
mean closing of 0.173 — but not uniformly: ES/RTH/1day closes 0.747 and crosses
the reference, while ES/RTH/30min and NQ/RTH/30min *widen* slightly.

### Linear against level shift

Break date fitted by minimising residual sum of squares over admissible years,
with a wild cluster bootstrap sup-F that re-searches the break in every replicate,
so the p-value accounts for the date being estimated:

| specification | RSS | parameter | F | bootstrap p | share of residual |
|---|---|---|---|---|---|
| cell effects only | 2.5969 | — | — | — | — |
| linear trend | 1.8577 | −0.0469/yr | 21.88 | 0.0086 | 28.5% |
| **level shift, τ̂ = 2022** | **1.7968** | δ = −0.258 | 24.49 (sup) | 0.0038 | 30.8% |
| **single-year 2022 dummy** | **1.4504** | δ = −0.405 | — | — | **44.2%** |

The break narrowly beats the trend, by 3.3% of RSS. But **a one-year 2022 dummy
beats both by 19%**, and the reason is visible in the table: 2022 is the minimum
year in 6 of 8 cells, and b reverts toward its pre-2022 level in 2023 in **8 of
8** — which a level shift does not predict.

Excluding 2022 entirely (`phase3b_robustness.json`):

| | full sample | excluding 2022 |
|---|---|---|
| linear slope | −0.0469/yr | **−0.0275/yr** |
| linear bootstrap p | 0.0086 | 0.0059 |
| break date | 2022 | 2019 |
| break bootstrap p | 0.0038 | 0.0207 |
| share of residual, linear | 28.5% | 16.6% |

**Verdict: INDETERMINATE, and the reason is specific.** The best one-parameter
description of the year effects is neither a trend nor a level shift but a
**single-year excursion in 2022** that fully reverts in 2023. Roughly 40% of the
headline −0.047 per year is 2022 alone; the slope on the remaining seven years is
−0.027 and still directionally intact, so there is residual structure, but its
magnitude is about half what the full sample suggested and its shape cannot be
identified from eight years.

**Eight-cluster limitation, stated regardless of outcome.** Both p-values come
from a wild cluster bootstrap with Rademacher weights and the null imposed. At
G = 8 the attainable floor is 2⁻⁷ = 0.0078, and the sup-F p of 0.0038 is below it —
Monte Carlo noise around a saturated test. No result here should be read as
conventional evidence at any nominal level. This applies to the linear
specification, the break, and the 2022 dummy alike.

This qualifies the S11 and S12 trend finding. The point estimate stands; the claim
that the anomaly is *closing smoothly* does not, and neither does a level-shift
account.

---

## Phase 4 — Convexity lookup table

S12's exact relation, K_vol = √E[V]·exp(−s²/8), evaluated at every grid point
rather than the five-minute equivalent alone, on a 20% variance-swap strike, with
intervals from the S10 bootstrap on c. The Brockhaus-Long column is retained only
as a labelled sensitivity; per item 95 it is invalid at the measured κ.

ES/RTH/1day, the full frequency curve (`phase4_convexity_table.csv` has all 128 rows):

| M | minutes per sub-bar | s² naive | s² intercept | adj. naive | adj. intercept | bias (vol pts) | overstatement |
|---|---|---|---|---|---|---|---|
| 5 | 78 | 1.951 | 1.081 | 4.329 | 2.528 | 1.801 | +71.3% |
| 13 | 30 | 1.531 | 1.081 | 3.484 | 2.528 | 0.956 | +37.8% |
| 26 | 15 | 1.384 | 1.081 | 3.176 | 2.528 | 0.649 | +25.7% |
| 78 | 5 | 1.287 | 1.081 | 2.972 | 2.528 | 0.445 | +17.6% |
| 195 | 2 | 1.181 | 1.081 | 2.746 | 2.528 | 0.218 | +8.6% |
| **389** | **1** | 1.090 | 1.081 | 2.547 | 2.528 | **0.019** | **+0.75%** |

**What a user must do.** The frequency at which the bias falls below 5%
(`phase4_frequency_guide.csv`):

| cell | grid points | below 5% | finest M below 5% | minutes per sub-bar required | at 5-min | best | worst |
|---|---|---|---|---|---|---|---|
| ES/GLOBEX/1day | 10 | 1 | 1379 | **1.0** | +19.3% | +0.64% | +86.6% |
| NQ/GLOBEX/1day | 10 | 2 | 1379 | **1.0** | +5.9% | +0.91% | +67.4% |
| ES/RTH/1day | 8 | 1 | 389 | **1.0** | +17.6% | +0.75% | +71.3% |
| NQ/RTH/1day | 8 | 2 | 389 | **1.0** | +6.9% | +0.90% | +64.2% |
| NQ/RTH/1h | 9 | 1 | 60 | **1.0** | +21.0% | +4.8% | +49.9% |
| ES/RTH/1h | 9 | **0** | — | **unreachable** | +62.6% | +28.5% | +102.2% |
| ES/RTH/30min | 5 | **0** | — | **unreachable** | +134.3% | +71.5% | +143.0% |
| NQ/RTH/30min | 5 | **0** | — | **unreachable** | +42.1% | +14.1% | +48.6% |

Fourteen of 128 rows clear 5%; ten of sixteen cells have at least one frequency
that does. **The prescription is one-minute sampling, and only at the daily
horizon.** At the 30-minute horizon on either instrument, and at the hourly
horizon on ES, no frequency available in this programme's grid brings the bias
under 5% — the shortest windows simply do not contain enough returns for the
proxy's own dispersion to fall below the quantity being measured. Maximum bias
anywhere in the table is 2.77 volatility points on a 20-point strike.

**No options data is held. This is a pricing-bias calculation on the adjustment
term and no claim is made about executable P&L.**

---

## Determinations and what changes

| | outcome |
|---|---|
| **Item 101, the open-bar candidate** | **REJECTED.** A7 enters the observed range on neither geometry, at no position. The RTH residual is not an open-bar effect. |
| **K7, risk parity** | **FIRES**, both criteria: mean \|Δw\| 0.000145 vs 0.02, realized-volatility difference 0.0038% vs 5%, at every cost-sweep point. |
| **Trend shape** | **INDETERMINATE.** A single-year 2022 excursion beats both the trend and a level shift; b reverts in 8 of 8 cells in 2023; excluding 2022 halves the slope to −0.027/yr. |
| **Convexity frequency** | One-minute sampling is required, and suffices only at the daily horizon; unreachable at 30-minute and at hourly on ES. |

**Changes to prior conclusions.**

- **S11/S12's trend claim is qualified.** The point estimate of −0.047 per year
  survives, but roughly 40% of it is 2022 alone and the shape of the closing
  cannot be identified. "The anomaly is shrinking" is supportable; "the anomaly is
  closing smoothly" is not.
- **Item 100's gap is now harder, not easier.** Three mechanisms have been tested
  against the RTH residual — i.i.d. heavy tails, calibrated within-window
  dispersion, and a fixed-position dominant return — and only the second explains
  anything, and only on GLOBEX. The RTH residual survives all three.

**Stands.**

- K3 sizing null, K2 indeterminate, S10 determination A, K5, the stop-out leg of
  K4, K6 does not fire, and S12's corrections to all of them.
- The mechanism claim in its S12-corrected form: calibrated within-window
  volatility dispersion reproduces the observed exponent on GLOBEX at every Hurst
  index and on RTH only at some, while the Hurst index does nothing. A8 confirms
  it is unchanged by adding the open bar.

**New.** Three results with no precedent in the programme: the RTH open bar is
measured at 1.9–2.7× the average sub-bar and is causally inert for the exponent;
the inverse-volatility bias is real, correctly signed and governed by the
estimation window rather than the reliability gap, so it is second-order at
monthly rebalancing and would be first-order at daily rebalancing for the widest
reliability pair measured; and the convexity bias has a frequency prescription —
one minute, daily horizon only.

---

## Persisted artifacts

`results/` — `phase1_amplitudes.csv`, `phase1_kappa.csv`, `phase1_arms_raw.csv`,
`phase1_arms_agg.csv`, `phase1_arm_compare.csv`, `phase1_determination.json`,
`phase2_costs.csv`, `phase2_illustration.csv`, `phase2_k7.json`,
`phase3_b_by_year.csv`, `phase3_gap_by_year.csv`, `phase3_gap_endpoints.csv`,
`phase3_break_search.csv`, `phase3_trend_structure.json`,
`phase3b_reversion.csv`, `phase3b_robustness.json`,
`phase4_convexity_table.csv`, `phase4_frequency_guide.csv`,
`phase4_summary.json`, `phase34_timers.json`.

`cache/` — `a7_*.npz` (80 A7 runs: log-RV matrix, grid, log-IV path, seed, κ,
dominant-return position; full return panel for seed index 0 of each setting),
`a8_*.npz` (120 A8 runs, same plus σ_w and H), `k7_*.npz` (four weight-series
pairs, naive and corrected, in sample and holdout, at both estimator lengths),
`break_bootstrap.npz` and `break_robust_*.npz` (all 9,999 sup-F and linear-F
bootstrap draws per specification, with the observed statistics and the seed).

`src/` — `common13.py`, `phase1_openbar.py`, `phase2_riskparity.py`,
`phase34.py`, `phase3b_robust.py`.
