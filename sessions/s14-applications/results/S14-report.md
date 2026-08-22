# Session 14 — First-order applications

Item 106 concedes that the first four applications were chosen badly. K3, K4, K5
and K7 all fired because volatility targeting, risk limits, combination weights
and risk parity sit where the loss surface is smooth or the contamination averages
away with the estimation window. S14 selects on the operative criterion instead:
**the quantity of interest must depend on the variance of the estimate, and more
data must not reduce the contamination.**

Three applications selected that way. **All three fail.**

Interpreter `~/venvs/obs-space-vol/bin/python`, realpath
`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13`, numpy 2.5.2,
pandas 3.0.5, outside every synced path. DECISIONS items 66–105 verified present
at lines 398–630 (40 of 40); items 106–110 appended and verified at lines 637,
644, 649, 657, 663.

**Holdout reads: this is the fifth** (item 110). Prior: S09 Phase 6, S11 Phase 1,
S11 Phases 8–9, S13 Phase 2. Read in Phase 1 only, no parameter changed.

---

## K8 — Regime misclassification

### Derivation, exact

Let z = log IV and x = log RV = z + e, e ~ N(0, v) independent of z, each series
classified against its own median. Then u = x − med(x) and w = z − med(z) are
jointly normal with mean zero and

> ρ = Corr(x, z) = sd(z)/√(Var(z) + v) = **√λ**

because λ = Var(z)/Var(x) is exactly the reliability this programme measures. By
the bivariate normal orthant probability, P(u > 0, w < 0) = ¼ − arcsin(ρ)/(2π), so

> **misclassification rate = arccos(√λ) / π**

Exact, not an expansion. Assumptions: joint normality of log IV and the noise,
independence of the two, thresholds at the respective medians. The threshold is
fixed at the in-sample median and never re-estimated.

### Rates, analytic and empirical side by side

| cell | λ | analytic | empirical, in sample | empirical, holdout | gap | episodes | mean duration |
|---|---|---|---|---|---|---|---|
| ES/GLOBEX | 0.827 | **13.6%** | 3.07% | 3.12% | −77% | 59 | 1.02 |
| NQ/GLOBEX | 0.940 | **7.9%** | 2.67% | 3.28% | −66% | 49 | 1.06 |
| ES/RTH | 0.840 | **13.1%** | 3.89% | 3.06% | −70% | 66 | 1.12 |
| NQ/RTH | 0.931 | **8.4%** | 4.21% | **5.15%** | −50% | 75 | 1.07 |

**The analytic rate exceeds 5% in every cell.** The empirical rate sits below it
in three of four holdout cells and above in one — and the two diverge by 50% to
77%, well past any sensible validity boundary, which the search over λ locates
below 0.30, i.e. outside the measured range entirely.

The divergence is not a failure of the derivation, and the reason must be stated:
**the empirical rate compares the five-minute-equivalent RV against the
finest-grid realized kernel, and both are computed on the same window from the
same price path.** Their errors are positively correlated, which suppresses
disagreement relative to the analytic rate, which is keyed to disagreement with
integrated variance itself. The empirical figure is therefore a **lower bound**.
Neither number alone is the answer, which is why item 107 required both.

Two further readings support the analytic side:

- **At a tercile split**, which places thresholds where the density is higher, the
  empirical rate is **6.0% to 11.9%** and exceeds 5% in all eight
  cell-sample combinations.
- **Conditional on distance from the threshold**, essentially all error is in the
  nearest quintile: 15.3% (ES/GLOBEX), 13.1% (NQ/GLOBEX) in quintile 1 against
  0.0% to 0.3% in quintiles 2 through 5. The error does not spread; it
  concentrates exactly where a threshold inside the distribution puts it.

### Priced consequence

A two-state allocation — invested in the low-volatility state, cash in the high —
switching on the regime call. **Illustration on measured misclassification, not a
strategy backtest**; no return series is claimed.

Excess switching cost from spurious regime changes, holdout, basis points:

| cell | 0.5t | 1.0t | 2.0t | 4.0t |
|---|---|---|---|---|
| ES/GLOBEX | 14.89 | 29.79 | 59.57 | 119.14 |
| ES/RTH | 17.27 | 34.53 | 69.06 | **138.13** |
| NQ/GLOBEX | 2.78 | 5.57 | 11.13 | 22.26 |
| NQ/RTH | 5.55 | 11.10 | 22.20 | 44.40 |

This is the first application in the programme with a materially large priced
consequence. K4's spurious stop-outs cost at most 0.042 bps; here the excess is
**three to four orders of magnitude larger**, because a threshold at the median
binds every day whereas a leverage cap at 2.0× never bound at all.

### **K8 DOES NOT FIRE.**

The analytic rate exceeds 5% in all four cells and the tercile-split empirical
rate exceeds it in all eight. Only the median-split empirical rate — the measure
most attenuated by shared-window error correlation — falls below, and even that
breaches in one holdout cell.

---

## K9 — HAR persistence attenuation

### Derivation, matrix form

HAR in logs: y_t = a + X*_t β + u_t, observed X = X* + E. Under classical
measurement error,

> Σ_XX = Σ_X*X* + Σ_E,  Σ_Xy = Σ_X*X* β  ⟹  **β = (Σ_XX − Σ_E)⁻¹ Σ_XX β̂**

a matrix expression, not a scalar attenuation factor, because the three
regressors share days and their errors are correlated. With serially independent
per-day noise of variance v, x₁ = e_{t−1}, x₅ a 5-day mean and x₂₂ a 22-day mean:

> Σ_E = v · [[1, 1/5, 1/22], [1/5, 1/5, 1/22], [1/22, 1/22, 1/22]]

Noise in the *dependent* variable does not bias the coefficients, only inflates
the residual variance, because y is at t, the regressors are lags t−1…t−22, and
the noise is serially independent. Assumptions: classical measurement error,
serial independence of the proxy noise, Σ_E known from the fitted scaling.

### Result

| cell | v | β_d naive (se) | β_d corrected | shift | β_w naive → corr | β_m naive → corr | persistence | daily share |
|---|---|---|---|---|---|---|---|---|
| ES/GLOBEX | 0.171 | 0.498 (0.026) | **1.076** | **+116%** | 0.347 → **−0.168** | 0.088 → 0.063 | 0.934 → 0.971 | 53% → **111%** |
| ES/RTH | 0.151 | 0.466 (0.027) | **0.819** | **+76%** | 0.370 → 0.078 | 0.092 → 0.057 | 0.928 → 0.954 | 50% → **86%** |
| NQ/GLOBEX | 0.054 | 0.463 (0.027) | 0.557 | +20% | 0.354 → 0.285 | 0.118 → 0.099 | 0.934 → 0.942 | 50% → 59% |
| NQ/RTH | 0.051 | 0.423 (0.027) | 0.505 | +19% | 0.391 → 0.336 | 0.117 → 0.098 | 0.932 → 0.939 | 45% → 54% |

**Total persistence is almost unchanged** — 0.928–0.934 naive against 0.939–0.971
corrected — but its **composition is transformed**. The daily share of total
persistence moves from 45–53% to 54–111%, and on ES/GLOBEX the weekly coefficient
changes sign. The correction is large enough on ES that the corrected vector
leaves the economically ordinary region, which is itself a statement about how
much noise the daily regressor carries: v/Var(x₁) is about 12% on ES against 4%
on NQ. The condition number of Σ_XX − Σ_E rises from 33–35 to 37–58.

### The forecast, measured rather than asserted

Item 108 requires that no forecasting improvement be claimed. It is not — and the
measurement shows the opposite:

| cell | sample | RMSE naive | RMSE corrected | change |
|---|---|---|---|---|
| ES/GLOBEX | in sample | 0.581 | 0.745 | **+28.3%** |
| ES/GLOBEX | pseudo-OOS | 0.586 | 0.775 | **+32.3%** |
| ES/RTH | in sample | 0.614 | 0.696 | +13.4% |
| ES/RTH | pseudo-OOS | 0.555 | 0.658 | +18.5% |
| NQ/GLOBEX | in sample | 0.585 | 0.591 | +1.1% |
| NQ/GLOBEX | pseudo-OOS | 0.589 | 0.606 | +2.8% |
| NQ/RTH | in sample | 0.590 | 0.596 | +0.9% |
| NQ/RTH | pseudo-OOS | 0.515 | 0.529 | +2.7% |

**The corrected coefficients forecast worse, by 0.9% to 32%.** That is not a
defect of the correction; it is the correct behaviour of two estimators answering
different questions. The naive coefficients are the best linear predictors of a
noisy target from noisy regressors, which is what a forecaster wants. The
corrected coefficients are consistent estimates of the structural relation among
true log-IV lags, which is what anyone reporting "volatility persistence is
predominantly weekly" needs. **The claim here is about reported persistence and
relative lag structure, and about nothing else.**

### **K9 DOES NOT FIRE.**

The daily coefficient shifts by 19% to 116% relative, against a 10% threshold, in
all four cells.

---

## K10 — Hurst bias

### Derivation

The lag-direction estimator regresses log m(q, Δ) on log Δ with
m(q, Δ) = E|log σ_{t+Δ} − log σ_t|^q. With proxy noise ε of variance
Var(ε) = (1 − λ)·Var(log RV_M), the observed increment carries **2·Var(ε) of extra
second moment at every lag** — an M-invariant nugget that does not vanish as
Δ → 0, which flattens the apparent scaling and biases H downward. Under normal
increments m(q, Δ) = C_q·S(Δ)^{q/2} with C_q = E|Z|^q, so S(Δ) is recoverable from
any q and the corrected moment is C_q·(S(Δ) − 2Var(ε))^{q/2}. Applying the
estimator to log RV rather than log σ scales m by a constant and leaves the slope
unchanged.

### Result

| cell | λ | Var(ε) | nugget | q | H naive (se) | H corrected | ΔH | H corrected [λ bootstrap] |
|---|---|---|---|---|---|---|---|---|
| ES/GLOBEX | 0.827 | 0.216 | 0.432 | 0.5 | 0.189 (0.004) | **0.397** | **+0.208** | [0.305, 0.572] |
| ES/GLOBEX | | | | 1.0 | 0.186 (0.003) | 0.368 | +0.182 | [0.291, 0.586] |
| ES/GLOBEX | | | | 2.0 | 0.182 (0.003) | 0.327 | +0.145 | [0.268, 0.550] |
| ES/RTH | 0.840 | 0.206 | 0.412 | 0.5 | 0.168 (0.002) | **0.352** | **+0.184** | [0.236, 0.391] |
| ES/RTH | | | | 1.0 | 0.169 (0.002) | 0.347 | +0.178 | [0.236, 0.494] |
| ES/RTH | | | | 2.0 | 0.174 (0.002) | 0.338 | +0.164 | [0.239, 0.443] |
| NQ/GLOBEX | 0.940 | 0.069 | 0.139 | 0.5 | 0.167 (0.004) | 0.207 | +0.040 | [0.167, 0.289] |
| NQ/GLOBEX | | | | 2.0 | 0.160 (0.003) | 0.192 | +0.032 | [0.160, 0.245] |
| NQ/RTH | 0.931 | 0.078 | 0.156 | 0.5 | 0.148 (0.003) | 0.184 | +0.036 | [0.152, 0.241] |
| NQ/RTH | | | | 2.0 | 0.156 (0.002) | 0.191 | +0.035 | [0.161, 0.246] |

The nugget is **126% of the increment second moment at lag 1** in the worst cell —
larger than the signal — and remains above 10% of it out to lag **33 to 40**, the
full range examined. There is no short-lag region where the correction is
immaterial, which is precisely the point: the contamination does not decay in the
lag direction, so no amount of data in that direction removes it.

### Cont and Das, tested rather than assumed

Cont and Das (2024) argue that measured rough volatility is an artifact of
microstructure noise in the volatility proxy and that correcting for it moves H
away from the roughness region toward 0.5. **That is the position being tested
here, against this programme's independently measured reliability** — λ measures
the nugget along the sampling-frequency axis, not the lag axis, so this is not a
circular test.

**The result is a partial and instrument-dependent confirmation.** Correcting for
measured proxy noise roughly **doubles H on the noisier instrument** (ES,
λ ≈ 0.83–0.84: 0.17–0.19 → 0.33–0.40) and moves it by only about 0.035 on the
cleaner one (NQ, λ ≈ 0.93–0.94: 0.15–0.17 → 0.18–0.21). The ordering is exactly
what Cont and Das predict: **the size of the correction tracks the measured
noise**. But no point estimate reaches 0.5. Only ES/GLOBEX has a bootstrap
interval that includes it, at [0.305, 0.572] for q = 0.5.

So: correcting for measured proxy noise moves H materially away from the roughness
region on the noisy cells and barely at all on the clean ones, and leaves every
point estimate below 0.5. "Rough volatility is entirely a noise artifact" is not
supported by these data; "the roughness estimate is substantially biased downward
by proxy noise, in proportion to that noise" is.

### **K10 DOES NOT FIRE.**

Corrected H differs from naive by 0.032 to 0.208 against a 0.02 threshold, in
every cell at every q.

---

## The A7 amplitude bound

S13's rejection of the open-bar arm carried no power, which item 106's revision of
method requires acknowledging. The bound supplies it.

### Analytic

A localized feature carrying share s of realized variance contributes an
**M-invariant floor of 2s²** to Var(log RV_M): writing RV_M = sX + (1−s)Y with X
one chi-square and Y the average of the rest, Var(log RV) ≈ 2s² + 2(1−s)²/(M−1),
whose second term vanishes in M and whose first does not. To supply a required
excess X_req a feature must carry **s_req = √(X_req/2)**.

| cell | M | observed excess | trigamma | required floor | **required share** | **measured share** | ratio | floor actually supplied |
|---|---|---|---|---|---|---|---|---|
| ES/GLOBEX | 276 | 0.2159 | 0.0073 | 0.2087 | **32.3%** | 0.45% | **71.5×** | 4.1e-05 |
| NQ/GLOBEX | 276 | 0.0693 | 0.0073 | 0.0621 | **17.6%** | 0.41% | **43.4×** | 3.3e-05 |
| ES/RTH | 78 | 0.2062 | 0.0260 | 0.1803 | **30.0%** | 2.93% | **10.3×** | 1.7e-03 |
| NQ/RTH | 78 | 0.0780 | 0.0260 | 0.0520 | **16.1%** | 4.04% | **4.0×** | 3.3e-03 |

Evaluated at the five-minute equivalent, where the programme's headline sits. At
the coarsest grid point the curve has all but converged to c and the residual
excess is near zero — negative on NQ — so that point understates the requirement
and is reported separately in `phase4_analytic_bound.csv`.

**The shortfall is 4× to 72× in share, hence 16× to 5,100× in the floor supplied**,
because the floor goes as the square. The ES/RTH figure reproduces item 106's
arithmetic: 2 × 0.0293² = 0.0017 against a required 0.180.

### Empirical, by sweep

κ swept upward from the calibrated value at five seeds each, stopping when b
enters the observed range or the first-sub-bar share exceeds 0.5:

| cell | κ range | share reached | b range over the sweep | ever in range? |
|---|---|---|---|---|
| ES/GLOBEX | 1 → 2000 | 0.29% → 40.6% | −1.038 to −1.256 | **no** |
| NQ/GLOBEX | 1 → 2000 | 0.29% → 40.1% | −1.083 to −1.219 | **no** |
| ES/RTH | 1 → 1280 | 1.03% → ~54% | −1.070 to −1.248 | **no** |
| NQ/RTH | 1 → 1280 | 1.05% → 54.1% | −1.073 to −1.191 | **no** |

b never leaves the reference band even when a single sub-bar carries **more than
half** the window's realized variance. Between-seed dispersion is 0.03 to 0.22, so
the flatness is not masked variation.

**The class of localized mechanisms is retired quantitatively.** Any feature
confined to a fixed position inside the window must carry 16% to 32% of realized
variance to produce the observed floor. Nothing measured in this programme comes
within a factor of four of that, and the sweep confirms the analytic bound is not
merely a first-order approximation.

---

## The 2022 excursion: identification, not calendar

S13 found the year-effect structure indeterminate, with a one-year 2022 excursion
beating both a trend and a level shift. Phase 5 asks what 2022 actually is.

Regressing the within-cell year-to-year deviation in b on fit diagnostics
(`phase5_identification.json`), 64 observations, cell fixed effects:

| regressor | coefficient | se | t | R² alone |
|---|---|---|---|---|
| **log₁₀(condition number)** | **−1.146** | 0.049 | **−23.5** | **0.910** |
| A/c | −0.027 | 0.007 | −3.67 | 0.196 |
| RMSE | +6.74 | 2.40 | 2.81 | 0.126 |
| is-2022 dummy | −0.405 | 0.061 | −6.59 | 0.441 |

Jointly, condition number takes −1.169 (se 0.056) and A/c becomes insignificant
(0.0023, se 0.0029). **Adding the 2022 dummy on top of the identification
variables shrinks its coefficient from −0.405 to −0.082** (t = −2.76), and raises
R² only from 0.911 to 0.922.

What 2022 looks like on the diagnostics: mean condition number 112 against 55 in
other years, mean fitted c of 0.569 against 0.829, mean A/c of 8.15 against 4.38.
**The intercept collapses in the high-volatility year and the fit becomes
ill-conditioned** — which is the S10 tercile pathology in milder form. S10 found
all 48 volatility-tercile sub-fits degenerate for exactly this reason:
conditioning on realized volatility removes the cross-sectional log-IV variation
that identifies the intercept. A high-volatility *year* is the same conditioning,
weaker.

**Verdict: the 2022 excursion is predominantly an identification artifact.**
Roughly 80% of it is absorbed by fit conditioning; a small residual (−0.082)
survives and may be a genuine state effect, but it is a fifth of what the raw
dummy suggested. The automatic decision rule in the code returns "volatility-state
effect" because |t| > 2 on that residual; that rule is too crude for this case and
the substantive reading above supersedes it.

This qualifies S11 and S12's trend result a second time. S13 established that ~40%
of the −0.047 per year is 2022; Phase 5 establishes that most of *that* is the
fits becoming less identified in high-volatility years, not the market changing.

---

## Determinations

| | outcome | margin |
|---|---|---|
| **K8, regime misclassification** | **DOES NOT FIRE** | analytic 7.9–13.6% vs 5% in all cells; tercile empirical 6.0–11.9%; excess switching cost to 138 bps |
| **K9, HAR attenuation** | **DOES NOT FIRE** | daily coefficient shifts +19% to +116% vs 10%; forecast measurably worse, not better |
| **K10, Hurst bias** | **DOES NOT FIRE** | ΔH = 0.032 to 0.208 vs 0.02, every cell at every q |
| **A7 bound** | localized mechanisms retired | required share 16–32% vs measured 0.4–4.0%; sweep flat to 54% share |
| **2022** | identification artifact | log(cond) explains 91%; the dummy shrinks 80% when controlled |

### What this settles

**Item 106's criterion works.** Four applications chosen without it all fired;
three chosen with it all fail. The dividing line is now empirical rather than
asserted: proxy noise is second-order in volatility targeting, risk limits,
combination weights and risk parity, and first-order in regime classification,
reported HAR persistence, and the Hurst exponent. The common feature of the second
group is that the quantity of interest is a function of the *variance* of the
estimate and that averaging over more data does not remove the contamination —
K8's threshold binds every day, K9's Σ_E does not shrink with sample size, and
K10's nugget is flat in lag by construction.

### What changes in prior conclusions

- **S11 and S12's trend result is qualified again.** After S13 attributed ~40% to
  2022, Phase 5 attributes most of 2022 to fit conditioning. What survives is a
  small, poorly identified drift.
- **S13's A7 rejection is now powered.** It was a null with no stated alternative;
  it is now a bound that retires the class.

### What stands

K3, K4 (stop-out leg), K5, K6, K7 and their S12 corrections; S10 determination A;
the S12-corrected mechanism claim; and the item-101 rejection, now strengthened.

**One thing this session does not do.** K10's result bears on the rough-volatility
literature, and the correction is applied to a proxy-noise term this programme
measured on an independent axis. It is not a claim that the true H is 0.35 or 0.40.
It is a claim that the standard estimator, applied to a proxy with this
programme's measured reliability, is biased downward by 0.03 to 0.21, and that the
bias tracks the noise.

---

## Persisted artifacts

`results/` — `phase1_k8_rates.csv`, `phase1_by_distance.csv`, `phase1_tercile.csv`,
`phase1_switch_costs.csv`, `phase1_k8.json`, `phase2_k9.csv`,
`phase2_forecast.csv`, `phase2_forecast_compare.csv`, `phase3_k10.csv`,
`phase3_nugget_by_lag.csv`, `phase3_material_lags.csv`, `phase23_summary.json`,
`phase4_analytic_bound.csv`, `phase4_kappa_sweep.csv`, `phase4_kappa_agg.csv`,
`phase5_year_fits.csv`, `phase5_identification.json`, `phase45_summary.json`.

`cache/` — `k8_*.npz` (both log-series, both thresholds, both classification
vectors in and out of sample, λ and the kernel bandwidths), `k9_*.npz` (both
coefficient vectors, the intercept, standard errors, Σ_XX, Σ_E, the noise variance
and the full design), `a7sweep_*.npz` (220 synthetic runs across the κ grid: log-RV
matrix, grid, log-IV path, seed, κ and the realised first-sub-bar share).

`src/` — `common14.py`, `phase1_k8.py`, `phase23.py`, `phase45.py`.
