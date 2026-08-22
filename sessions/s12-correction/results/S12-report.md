# Session 12 — Correction: convexity arithmetic, mechanism calibration, trend inference, K4 restatement

Four corrections to S11, three of them raised against my own work. Two hold as
raised, one is refuted but for a reason that still requires the S11 statement to
change, and one is a restatement of scope rather than of arithmetic. No new data,
no holdout read, no pre-registered threshold altered.

Interpreter `~/venvs/obs-space-vol/bin/python`, realpath
`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13`, numpy 2.5.2,
pandas 3.0.5, outside every synced path. DECISIONS items 66–94 verified present at
lines 398–562 (29 of 29); items 95–99 appended and verified at lines 567, 577,
585, 589, 593.

---

## Phase 1 — Convexity on the exact relation (item 95)

**Item 95 is upheld. The S11 magnitudes were void and are replaced.**

Derivation, and its single assumption. Let integrated variance V be lognormal
with log V ~ N(μ, s²). Then E[V] = exp(μ + s²/2), so √E[V] = exp(μ/2 + s²/4);
and E[√V] = exp(μ/2 + s²/8) by the lognormal MGF at t = ½. A volatility swap
pays realized volatility, so its fair strike is

> **K_vol = E[√V] = √E[V] · exp(−s²/8)**

exactly, with no expansion. The single assumption is lognormality of V — the same
assumption the intercept route already makes in reading c as Var(log IV), so the
correction adds no new modelling commitment.

**Where the expansion breaks.** Brockhaus and Long's second-order form,
K_vol ≈ √E[V]·(1 − (e^{s²}−1)/8), needs κ = Var(V)/E[V]² = e^{s²} − 1 small. It
departs from the exact relation by **10% at κ = 0.182** (s² = 0.167). Measured κ
in this programme runs **1.26 to 6.84** — between 7 and 38 times past the
boundary. The validity boundary is now a measured number, not an assertion:

| s² | κ | exact adjustment | BL adjustment | BL / exact | K_vol/√E[V] exact | K_vol/√E[V] BL |
|---|---|---|---|---|---|---|
| 0.10 | 0.105 | 0.0124 | 0.0131 | 1.058 | 0.9876 | 0.9869 |
| 0.167 | **0.182** | 0.0207 | 0.0228 | **1.100** | 0.9794 | 0.9772 |
| 0.50 | 0.649 | 0.0606 | 0.0811 | 1.338 | 0.9394 | 0.9189 |
| 1.00 | 1.718 | 0.1175 | 0.2148 | 1.828 | 0.8825 | 0.7852 |
| 2.00 | 6.389 | 0.2212 | 0.7986 | 3.610 | 0.7788 | 0.2014 |
| 2.50 | 11.18 | 0.2684 | 1.3978 | 5.208 | 0.7316 | **−0.398** |

At s² = 2.5 the expansion returns a negative volatility-swap strike. S11 was
operating in that regime.

**Corrected figures**, adjustment in volatility points on a 20% variance-swap
strike, with the interval propagated from the S10 bootstrap on c:

| cell | s² intercept | s² naive | adj. exact [95%] | adj. exact naive | difference | overstatement | S11 (void) |
|---|---|---|---|---|---|---|---|
| ES/GLOBEX/1day | 1.034 | 1.250 | 2.425 [2.197, 2.605] | 2.893 | 0.468 | **+19.3%** | +37.4% |
| NQ/GLOBEX/1day | 1.085 | 1.155 | 2.537 [2.383, 2.695] | 2.688 | 0.151 | **+5.9%** | +10.8% |
| ES/RTH/1day | 1.081 | 1.287 | 2.528 [2.343, 2.702] | 2.972 | 0.445 | +17.6% | +34.7% |
| NQ/RTH/1day | 1.057 | 1.135 | 2.475 [2.319, 2.619] | 2.645 | 0.170 | +6.9% | +12.4% |
| ES/RTH/1h | 1.052 | 1.789 | 2.464 [2.233, 2.641] | 4.007 | 1.543 | +62.6% | +167.4% |
| NQ/RTH/1h | 1.425 | 1.759 | 3.263 [3.165, 3.356] | 3.947 | 0.684 | +21.0% | +52.2% |
| ES/RTH/30min | 0.815 | 2.060 | 1.938 [1.532, 2.234] | 4.540 | **2.602** | **+134.3%** | +443.3% |
| NQ/RTH/30min | 1.368 | 2.023 | 3.144 [3.017, 3.249] | 4.468 | 1.324 | +42.1% | +123.9% |

The ES/GLOBEX figure of +19.3% matches the hand recompute in item 95 exactly. The
exact-to-expansion ratio runs 0.265 to 0.615, so the expansion overstated the
adjustment by between 1.6× and 3.8× throughout.

**K6 still DOES NOT FIRE** at the item-94 threshold of 5%, which is unchanged.
The overstatement is 5.9% to 134.3% and exceeds 5% in all 16 rows. But the margin
is far narrower than S11 reported: the tightest cell, NQ/GLOBEX, is at **5.94%
against a 5% threshold**, and NQ/RTH/1day at 6.87%. Two of eight distinct cells
now sit within about two percentage points of the threshold, where S11's void
arithmetic put the minimum at 10.8%. The determination survives; the comfort with
which it survives does not.

Direction is unchanged: naive s² exceeds the intercept-route s² in every cell, so
the naive adjustment is too large and the implied volatility-swap strike too low,
favouring the side long volatility at the quoted strike. **No options data is
held; this is a pricing-bias calculation on the adjustment term and no claim is
made about executable P&L.**

---

## Phase 2 — Mechanism calibration verification (item 96)

**Determination: A. The calibration is correct. Item 96's suspicion is refuted —
but its underlying concern was well founded and the S11 statement still changes.**

**The procedure as coded** (`sessions/s11-extensions/src/phase6_calibrated.py`):

- **Target, line 26**: `sb=subbars(rw,M); q=quart_suite(sb,M); rq,rv=q["RQ_RV"]`,
  then line 28 returns `mean(rq[rv>0] / rv[rv>0]**2)` — the mean over windows of
  RQ/RV², computed through `parta.quart_suite` on the real panel.
- **Synthetic side, lines 29–35**: the identical three lines applied to a panel
  from `make_a6`, so the finite-M bias in a mean-of-ratios is present on both
  sides and cancels.
- **Bracket, line 37**: `lo,hi = 1e-3, 6.0`, with an explicit bracket check at
  lines 38–39 returning `bracketed=False` if the target lies outside.
- **Convergence, lines 40–44**: 24 bisection steps, final interval width
  6/2²⁴ = 3.6e-7, assuming the mapping is increasing in σ_w.
- **Objective at the solution, line 45**: re-evaluated and logged as `achieved_ratio`.

**Verification at every calibration point.** Implied RQ/RV² at the S11 calibrated
σ_w against Part A's measured value, 24 points:

| | implied | measured | proportional discrepancy | sd of log within-window variance |
|---|---|---|---|---|
| ES/GLOBEX, six H | 3.043509 | 3.043509 | ≤1.2e-7 | 1.368 – 1.520 |
| NQ/GLOBEX, six H | 3.606698 | 3.606698 | ≤1.2e-7 | 1.539 – 1.803 |
| ES/RTH, six H | 1.506037 | 1.506037 | ≤7.4e-8 | 0.764 – 1.072 |
| NQ/RTH, six H | 1.585652 | 1.585652 | ≤6.9e-8 | 0.841 – 1.152 |

**24 of 24 within tolerance, maximum discrepancy 1.2×10⁻⁷.** The bisection solved
exactly the target Part A measured. No far branch, no wrong target.

**The mapping, swept rather than inferred.** σ_w on a 25-point logarithmic grid
from 0.1 to 5.0, at each of six H, both geometries:

| σ_w | GLOBEX RQ/RV² | RTH RQ/RV² | sd log within-window variance |
|---|---|---|---|
| 0.10 | 0.9999 | 0.9578 | 0.039 |
| 0.60 | 1.0568 | 1.0036 | 0.232 |
| 1.00 | ~1.16 | ~1.06 | ~0.39 |
| 1.60 | 1.3955 | 1.2050 | 0.617 |
| 2.21 | 1.7261 | 1.4110 | 0.855 |
| 3.61 | 2.7039 | — | 1.394 |
| 5.00 | 3.8889 | — | 1.931 |

The mapping is **monotone increasing in all twelve (geometry, H) slices** with
zero decreases, and each of the 24 (cell, H) target lines is crossed **exactly
once**. **There is no second solution near 0.6**: at σ_w = 0.6 the implied ratio
is 1.06 (GLOBEX) and 1.00 (RTH), against targets of 3.04–3.61 and 1.51–1.59.

**Why item 96's arithmetic pointed elsewhere, and what must change anyway.**
Item 96 reasoned that under lognormal within-window volatility RQ/RV² ≈
exp(Var(log v)), so a ratio of 1.5 implies sd(log v) ≈ 0.64. That reasoning is
sound; what it does not capture is that **σ_w is not sd(log v)**. In `make_a6`,
σ_w scales a fractional Brownian path normalised to unit variance *at the
window's terminal point*, and the path is then divided by its own within-window
mean. The dispersion that survives both operations is a fraction of σ_w, and it
is the interpretable quantity:

> **sd of log within-window variance = 0.764 to 1.803**, against a σ_w of
> 1.495 to 4.805.

The RTH figures (0.76–1.15 for a target ratio of 1.51) sit close to item 96's
0.64; the residual gap and the higher GLOBEX figures are the autocorrelation of
the path and the five-minute sub-bar aggregation, both of which pull the realized
RQ/RV² below exp(Var(log v)). A one-standard-deviation swing in instantaneous
variance of e^{0.76} = 2.1× to e^{1.80} = 6.0× within a session is large but not
absurd — least of all for GLOBEX, a 23-hour session spanning the Asian, European
and US days, where the GLOBEX figures are the highest in the set.

**So the S11 mechanism claim stands, in corrected form.** Because determination A
holds, no recalibration and no A6 re-run were required. Two changes to how it is
stated:

1. **Report the dispersion, not the scale parameter.** "Calibrated σ_w of 1.495
   to 4.805" is uninterpretable and invited exactly the objection item 96 raised.
   The claim is: within-window log-variance dispersion of **0.76 to 1.80 in
   standard deviation**, calibrated to Part A's measured RQ/RV².
2. **Narrow the range claim.** S11 said the exponent level lands inside the
   observed range in all four cells, using [−1.00, −0.41]. Against the range as
   restated in this session's brief, [−0.97, −0.44]:

| cell | H values inside [−0.97, −0.44] | b range over the sweep |
|---|---|---|
| ES/GLOBEX | **6 of 6** | −0.850 to −0.926 |
| NQ/GLOBEX | **6 of 6** | −0.796 to −0.936 |
| ES/RTH | 1 of 6 | −0.953 to −1.044 |
| NQ/RTH | 3 of 6 | −0.894 to −1.050 |

The corrected mechanism claim: **calibrated within-window volatility dispersion
reproduces the observed exponent in both GLOBEX cells at every Hurst index, and
in the RTH cells only at some — while the Hurst index itself does nothing in any
cell.** The S10/S11 finding that the map is non-monotonic in H and that its whole
range sits inside seed noise is unaffected and still means no inversion to an
implied H is possible.

---

## Phase 3 — Trend by wild cluster bootstrap (item 97)

**Item 97 is upheld. The point estimate stands; the inference is replaced.**

Wild cluster bootstrap, Rademacher weights, 9,999 replications, clustering on the
eight distinct cells, with the null imposed on the restricted residuals (Cameron,
Gelbach and Miller 2008). The 95% interval is obtained by inverting the same test
over a 121-point grid of β₀ at 1,499 replications per point.

| | β | cluster-robust SE | t | p cluster-robust | **p wild cluster bootstrap** | WCB 95% interval |
|---|---|---|---|---|---|---|
| **8 distinct cells** | **−0.04690** | 0.01119 | −4.190 | 0.00409 | **0.0066** | **[−0.0760, −0.0245]** |
| 16 cells (B0+B1) | −0.04690 | 0.00791 | −5.926 | 0.00003 | 0.0000 | [−0.0643, −0.0303] |

The duplication inflation is visible: B0 and B1 are exact duplicates, and pooling
all sixteen drives the cluster-robust p from 0.004 to 0.00003 and the bootstrap p
to zero purely by counting each cell twice. Only the eight-cell row is
interpretable.

**The trend survives at the 5% level and not at the 1% level**, and the interval
excludes zero. But the correct reading is narrower than that:

**Small-cluster limitation, stated regardless of outcome.** With G = 8 clusters
there are 2⁸ = 256 Rademacher weight vectors and, by the sign symmetry of the
statistic, 2⁷ = 128 distinct values of |t*|. **The smallest two-sided p-value the
design can produce is 1/128 = 0.0078.** The observed 0.0066 is below that floor
and is a Monte Carlo fluctuation around it: the honest statement is **p ≤ 0.0078,
the smallest value this design can return**, not p = 0.0066. The test is
saturated. Cluster-robust standard errors are downward-biased below roughly
thirty clusters, and the wild cluster bootstrap is the recommended correction but
is itself only asymptotically valid in the number of clusters. At G = 8 no result
here should be read as conventional evidence at any nominal level.

What can be said: the point estimate of **−0.047 per year is unchanged**, all
sixteen cells have a negative slope, and the sign is not in question. The
magnitude — roughly 0.33 over the eight-year sample, about half the average gap to
the reference — is what the finding rests on. The p-value is not.

---

## Phase 4 — K4 restatement (items 98, 99)

**Item 98 is upheld. The S11 joint determination is superseded.**

### Stop-out at 1.5× target — tested

| cell | points | both | spurious | missed | spurious rate | missed rate | episodes | mean duration |
|---|---|---|---|---|---|---|---|---|
| ES/GLOBEX | 641 | 20 | 2 | 13 | 0.312% | 2.028% | 2 | 1.0 |
| NQ/GLOBEX | 641 | 21 | 1 | 6 | 0.156% | 0.936% | 1 | 1.0 |
| ES/RTH | 621 | 20 | 4 | 14 | 0.644% | 2.254% | 4 | 1.0 |
| NQ/RTH | 621 | 21 | 6 | 5 | 0.966% | 0.805% | 6 | 1.0 |

Cost of spurious breaches, basis points per decision point, full sweep:

| cell | 0.5t | 1.0t | 2.0t | 4.0t |
|---|---|---|---|---|
| ES/GLOBEX | 0.0025 | 0.0051 | 0.0101 | 0.0203 |
| NQ/GLOBEX | 0.0003 | 0.0007 | 0.0014 | 0.0028 |
| ES/RTH | 0.0052 | 0.0105 | 0.0209 | **0.0418** |
| NQ/RTH | 0.0022 | 0.0043 | 0.0086 | 0.0172 |

**Stop-out: K4 FIRES**, on both item-92 criteria independently — maximum spurious
rate 0.966% against 1%, maximum cost 0.042 bps against 1 bp at every sweep point.
NQ/RTH at 0.966% clears the rate criterion by six days out of 621.

### Leverage cap at 2.0× — untested

| cell | points | times bound | median leverage | 95th pct | 99th pct | max | cap that would first bind | headroom |
|---|---|---|---|---|---|---|---|---|
| ES/GLOBEX | 641 | **0** | 0.797 | 1.009 | 1.098 | 1.166 | 1.166 | 1.72× |
| NQ/GLOBEX | 641 | **0** | 0.591 | 0.803 | 0.852 | 0.916 | 0.916 | 2.18× |
| ES/RTH | 621 | **0** | 1.005 | 1.265 | 1.378 | **1.434** | **1.434** | 1.39× |
| NQ/RTH | 621 | **0** | 0.743 | 0.963 | 1.028 | 1.073 | 1.073 | 1.86× |

The cap bound at **zero of 2,524 decision points**. The cap would first bind at
**1.434×**, the maximum leverage attained anywhere in the holdout, which is
ES/RTH; a cap at or below that level would bind at least once. The nearest the
2.0× cap came to binding is a headroom ratio of 1.39×.

**Leverage cap: UNTESTED at a 10% volatility target with daily rebalancing.** It
is not that the cap passed; it is that the experiment never exercised it. A cap
of 2.0× on a 10%-vol strategy requires realized daily volatility below 0.315%,
about 5% annualised, which the 2024–2026 holdout never delivered.

### Item 99 — the missed-breach asymmetry

| cell | spurious rate | missed rate | missed − spurious |
|---|---|---|---|
| ES/GLOBEX | 0.312% | 2.028% | **+1.716%** |
| NQ/GLOBEX | 0.156% | 0.936% | **+0.780%** |
| ES/RTH | 0.644% | 2.254% | **+1.610%** |
| NQ/RTH | 0.966% | 0.805% | −0.161% |

Missed exceeds spurious in **three of four cells**, by up to a factor of 6.5.
Mechanism: microstructure and sampling noise inflate the estimated volatility that
enters the position size, so the proxy-sized position is *smaller* than the
kernel-sized one precisely on the days when volatility is genuinely high. A
smaller position produces a smaller realized portfolio volatility, so the stop-out
is not triggered on days when it should be. The asymmetry is a consequence of
sizing on a noisy estimate, not a property of the threshold.

Per item 99 this is a **directional finding about proxy noise at risk limits, not
a kill-condition outcome** — item 92 was written about spurious breaches and says
nothing about missed ones. Recorded, not adjudicated.

### K4 determination, per limit

| limit | status | basis |
|---|---|---|
| Stop-out at 1.5× target | **FIRES** | both criteria: 0.966% vs 1%, 0.042 bps vs 1 bp |
| Leverage cap at 2.0× | **UNTESTED** | bound 0 of 2,524; would first bind at 1.434× |

**The S11 joint K4 determination is superseded.** Reporting a two-limit
specification as firing when only one limit was ever exercised overstates
coverage, which is what item 98 says and is correct.

---

## What is corrected, what is withdrawn, what stands

**Corrected.**

- **S11 Phase 10 magnitudes are void and replaced** (item 95). Overstatement
  10.8%–443% becomes **5.9%–134.3%**; the maximum difference 13.96 volatility
  points becomes **2.60**. The Brockhaus-Long expansion was used at κ = 1.26–6.84
  against a validity boundary of κ = 0.182 and, at the extreme, returns a negative
  strike.
- **S11's σ_w statement is corrected in units, not in arithmetic.** The
  calibration is exact (24 of 24, discrepancy 1.2e-7, monotone mapping, unique
  crossing, no second solution at 0.6). But σ_w is a scale parameter on a
  terminal-normalised path, not a dispersion; the interpretable figure is a
  **within-window log-variance sd of 0.76 to 1.80**.
- **S11's range claim is narrowed.** Against [−0.97, −0.44], the calibrated A6
  exponent lands inside for both GLOBEX cells at every H, but for ES/RTH at 1 of 6
  and NQ/RTH at 3 of 6.
- **S11's trend p-value is replaced** (item 97). t = −4.19, p = 0.004 becomes a
  wild cluster bootstrap **p ≤ 0.0078, the floor of an eight-cluster design**,
  with a 95% interval of [−0.0760, −0.0245].
- **K4 is restated per limit** (item 98). The joint "FIRES" is superseded by
  stop-out FIRES, leverage cap UNTESTED.

**Withdrawn.** Nothing is withdrawn outright. Determination A in Phase 2 means the
S11 mechanism claim survives verification rather than being retracted, and K6 and
the stop-out leg of K4 reach the same verdicts on corrected arithmetic.

**Stands.**

- **K6 DOES NOT FIRE**, on the exact relation, at the unchanged 5% threshold —
  but at a minimum margin of 5.94% rather than 10.8%, so two of eight cells are
  now close to the line.
- **K5 FIRES** — untouched by any of these corrections.
- **The stop-out leg of K4 FIRES** on both criteria.
- **The trend's point estimate**, −0.047 per year, all sixteen cells negative.
- **The mechanism claim**, that within-window volatility dispersion flattens the
  exponent while the Hurst index does not, now with the calibration verified and
  the dispersion stated in interpretable units.
- **Everything in S09 and S10 that these four corrections do not touch**: the K3
  sizing null, K2 indeterminate, S10 determination A, and S11's Phases 1, 2, 4, 7
  and 9.

The one substantive change in a conclusion is the margin on K6. It was reported
as overwhelming and is merely clear.

---

## Persisted artifacts

`results/` — `phase1_convexity_exact.csv`, `phase1_validity_boundary.csv`,
`phase1_k6.json`, `phase1_timer.json`, `phase2_verification.csv`,
`phase2_sweep.csv`, `phase2_crossings.csv`, `phase2_determination.json`,
`phase3_wcb.json`, `phase4_stopout.csv`, `phase4_leverage_cap.csv`,
`phase4_costs.csv`, `phase4_k4.json`, `phase34_summary.json`.

`cache/` — `wcb_distinct_8.npz` and `wcb_all_16.npz` (all 9,999 bootstrap t and β
draws per version, with the observed statistic, the SE and the seed),
`k4restate_*.npz` (both position series, both realized-volatility series and both
breach indicator vectors per cell).

`src/` — `phase1_convexity.py`, `phase2_calibcheck.py`, `phase34.py`.
