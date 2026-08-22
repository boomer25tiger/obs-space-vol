# Session 15 — Confound checks: final verification before writing

Three claims from S11 through S14 are put under challenge by items 111, 112 and
113. **One survives, one is withdrawn as indeterminate, one survives at a fifth
of its headline size.** No further measurement session follows (item 114); the
next artifact is the paper.

Interpreter `~/venvs/obs-space-vol/bin/python`, realpath
`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13`, numpy 2.5.2,
pandas 3.0.5, outside every synced path. DECISIONS items 66–110 verified present
at lines 398–663 (45 of 45); items 111–114 appended and verified at lines 669,
677, 685, 692. **The holdout was not read.** Running count stays at five
openings: S09 Phase 6, S11 Phase 1, S11 Phases 8–9, S13 Phase 2, S14 Phase 1.

---

## Phase 1 — K10 lag selection: **the claim survives**

Item 111 argues that corrected S(Δ) going negative at short lags drops exactly
the lags that identify H, and that refitting on longer lags mechanically raises H
regardless of any nugget. The concern is legitimate and the measurement refutes it.

### Surviving lags

| cell | q | lags surviving | dropped | range |
|---|---|---|---|---|
| ES/GLOBEX | 0.5, 1.0, 2.0 | 39 of 40 | **1** (lag 1) | 2–40 |
| NQ/GLOBEX | all q | 40 of 40 | 0 | 1–40 |
| ES/RTH | all q | 40 of 40 | 0 | 1–40 |
| NQ/RTH | all q | 40 of 40 | 0 | 1–40 |

Only one lag is ever dropped, in one cell. The 126% nugget share at lag 1 occurs
only on ES/GLOBEX; elsewhere the nugget is large but stays below S(1).

### The decomposition, with naive-on-subset as its own column

| cell | q | H naive, all lags | **H naive, surviving subset** | H corrected, subset | from lag selection | from nugget | share lag selection |
|---|---|---|---|---|---|---|---|
| ES/GLOBEX | 0.5 | 0.1887 | **0.1834** | 0.3968 | **−0.0053** | +0.2134 | **−2.5%** |
| ES/GLOBEX | 1.0 | 0.1857 | **0.1805** | 0.3676 | **−0.0052** | +0.1871 | **−2.9%** |
| ES/GLOBEX | 2.0 | 0.1819 | **0.1775** | 0.3273 | **−0.0044** | +0.1498 | **−3.0%** |
| NQ/GLOBEX | all q | 0.160–0.167 | identical | 0.192–0.207 | **0.0000** | +0.032 to +0.040 | **0%** |
| ES/RTH | all q | 0.168–0.174 | identical | 0.338–0.352 | **0.0000** | +0.164 to +0.184 | **0%** |
| NQ/RTH | all q | 0.148–0.156 | identical | 0.184–0.191 | **0.0000** | +0.035 to +0.036 | **0%** |

**Lag selection contributes at most −0.0053 and its share is negative.** Dropping
lag 1 makes naive H *lower*, not higher, so the selection works against the
reported shift rather than creating it. Item 111's mechanism — that refitting on
longer lags approaches Brownian — does not operate over a 2-to-40 window on these
series. The nugget accounts for 100% to 103% of the total in every row.

### The fixed common window, free of any per-cell selection

Lags 2–40, the widest window where correction is feasible in every cell at every q:

| cell | q | H naive | H corrected | shift | RMSE naive | RMSE corrected |
|---|---|---|---|---|---|---|
| ES/GLOBEX | 0.5 | 0.1834 | 0.3968 | **+0.2134** | 0.009 | 0.042 |
| ES/GLOBEX | 2.0 | 0.1775 | 0.3273 | +0.1498 | 0.025 | 0.105 |
| ES/RTH | 0.5 | 0.1662 | 0.2909 | +0.1247 | 0.006 | 0.020 |
| ES/RTH | 2.0 | 0.1711 | 0.2840 | +0.1129 | 0.022 | 0.070 |
| NQ/GLOBEX | 0.5 | 0.1588 | 0.1904 | +0.0317 | 0.008 | 0.011 |
| NQ/RTH | 2.0 | 0.1533 | 0.1838 | **+0.0305** | 0.019 | 0.028 |

**Every shift on the common window exceeds 0.02**, from +0.0265 to +0.2134. K10's
determination does not depend on which lags survive.

Note that ES/RTH's corrected H is 0.284–0.291 on the common window against
0.338–0.352 on the full window, so excluding lag 1 *lowers* the corrected figure
by about 0.06. The common-window numbers are the conservative ones and should be
the quoted ones.

### The sensitivity item 111 did not raise, which is the real one

H is strongly and non-linearly sensitive to the size of the nugget:

| cell | q | 0.25× nugget | 0.50× | 0.75× | 1.00× | naive |
|---|---|---|---|---|---|---|
| ES/GLOBEX | 0.5 | 0.220 | 0.269 | 0.388 | 0.397 | 0.189 |
| ES/RTH | 0.5 | 0.190 | 0.219 | 0.263 | **0.352** | 0.168 |
| NQ/GLOBEX | 0.5 | 0.175 | 0.185 | 0.195 | 0.207 | 0.167 |
| NQ/RTH | 0.5 | 0.155 | 0.164 | 0.173 | 0.184 | 0.148 |

On ES/RTH the last 25% of the nugget moves H by 0.089, more than the first 75%
moves it. **The direction of the K10 result is robust; its magnitude is not.**
That matters because Phase 2 shows the nugget's magnitude is itself in doubt.

### **K10 survives, in this corrected form**

> Correcting the lag-direction Hurst estimator for measured proxy noise raises H
> by 0.027 to 0.213 on a fixed lag window of 2 to 40, in every cell at every q of
> 0.5, 1 and 2. Lag selection contributes nothing: at most one lag of forty is
> ever dropped, and dropping it lowers naive H rather than raising it. The
> direction and the ordering across instruments are robust — the shift tracks
> measured reliability, roughly six times larger on ES than on NQ — but the
> magnitude depends non-linearly on the assumed nugget size, and no point
> estimate reaches 0.5.

---

## Phase 2 — K9 classical measurement error: **the determination is withdrawn as indeterminate**

### Conditioning is not the explanation

| cell | cond Σ_XX | min eig Σ_XX | cond (Σ_XX − Σ_E) | min eig (Σ_XX − Σ_E) |
|---|---|---|---|---|
| ES/GLOBEX | 34.7 | 0.0796 | 58.3 | **0.0454** |
| NQ/GLOBEX | 33.3 | 0.0759 | 36.7 | 0.0677 |
| ES/RTH | 33.0 | 0.0853 | 46.7 | 0.0580 |
| NQ/RTH | 33.6 | 0.0739 | 36.8 | 0.0664 |

The corrected matrix is better conditioned than most of the fits in this
programme. **The ES/GLOBEX weekly sign flip is not a near-singularity artifact.**

### The classical assumption is violated, but mildly

Proxy error taken as log RV − log kernel at the five-minute equivalent:

| cell | ρ(error, level) | t | ρ vs daily | ρ vs weekly | ρ vs monthly | classical fraction |
|---|---|---|---|---|---|---|
| ES/GLOBEX | **−0.367** | −17.4 | −0.193 | −0.185 | −0.193 | 86.5% |
| ES/RTH | −0.267 | −12.1 | −0.097 | −0.111 | −0.137 | 92.9% |
| NQ/GLOBEX | −0.169 | −7.6 | −0.005 | −0.007 | −0.037 | 97.1% |
| NQ/RTH | −0.131 | −5.7 | +0.021 | +0.007 | −0.031 | 98.3% |

The error correlates negatively with the level in all four cells, decisively so by
any t-statistic, but it explains only 1.7% to 13.5% of the error variance. Scaling
Σ_E by the classical fraction leaves the daily shift at 18.9% to 86.6% and the
ES/GLOBEX weekly sign flip intact. **On item 112's own proposed sensitivity, K9's
determination survives.**

### The sharper problem: v is 2.4 to 11 times the measurable error

| cell | v from A·M^b | Var(log RV − log kernel) | ratio |
|---|---|---|---|
| ES/GLOBEX | 0.1710 | 0.0156 | **9.1%** |
| ES/RTH | 0.1513 | 0.0229 | 15.1% |
| NQ/GLOBEX | 0.0539 | 0.0146 | 27.1% |
| NQ/RTH | 0.0515 | 0.0215 | 41.8% |

This is item 112's point arriving through a different door and doing far more
damage. v = A·M^b treats the *entire* excess of Var(log RV_M) over Var(log IV) as
measurement error. But that excess decays at M^−0.44, not M^−1, and S11 attributes
a substantial part of it to within-window volatility dispersion — **a property of
the price process, not error in measuring it.** Directly measured disagreement
between RV and the kernel is between a ninth and two-fifths of v.

Recomputing the correction with Σ_E scaled to the measured error variance:

| cell | β_d naive | β_d, Σ_E = v | β_d, classical share | **β_d, measured error** | shift, full | **shift, measured** |
|---|---|---|---|---|---|---|
| ES/GLOBEX | 0.498 | 1.076 | 0.930 | **0.524** | +116% | **+5.1%** |
| ES/RTH | 0.466 | 0.819 | 0.777 | **0.499** | +76% | **+6.9%** |
| NQ/GLOBEX | 0.463 | 0.557 | 0.554 | **0.485** | +20% | **+4.8%** |
| NQ/RTH | 0.423 | 0.505 | 0.503 | **0.454** | +19% | **+7.2%** |

Weekly coefficient: sign-flips on ES/GLOBEX under Σ_E = v and under the classical
share; **does not flip under the measured error** (0.347 → 0.329).

**Under the measured error variance the daily shift is 4.8% to 7.2% — below the
10% threshold in every cell. K9 FIRES.** Under v from A·M^b it does not fire, by a
wide margin.

### **K9 is withdrawn as indeterminate**

The determination flips on a choice the programme cannot currently settle:

- **Σ_E = v from A·M^b** (S14's choice) treats the whole excess as error and
  **over-corrects** if any of it is a price-process property, which S11's
  within-window dispersion result says it is.
- **Σ_E from RV-vs-kernel disagreement** **under-corrects**, because the kernel is
  computed on the same window from the same price path, so its error is
  positively correlated with RV's and their difference understates both.

The truth lies between, and the interval spans the threshold: 4.8% to 116%
against a 10% criterion. **No determination on K9 is reportable.** What is
reportable, and does not depend on the choice, is the qualitative structure:
attenuation raises the daily coefficient and lowers the weekly and monthly ones
in every cell, total persistence is nearly unchanged under every scaling
(0.93 naive against 0.94–0.97), and the effect is ordered by measured
reliability — largest on ES, smallest on NQ. S14's claim that the daily share of
persistence moves from 45–53% to 54–111% is **withdrawn**; the direction is not.

The S14 finding that the corrected coefficients forecast *worse* stands unchanged
and is unaffected by the scaling question.

---

## Phase 3 — The trend against the conditioning control: **survives at a fifth of its size**

Within-year b on year and log₁₀(condition number), cell fixed effects, eight
distinct cells, wild cluster bootstrap with Rademacher weights, 9,999
replications, null imposed, interval by test inversion over 121 grid points.

| specification | year coefficient | cluster SE | t | **bootstrap p** | 95% interval | VIF (year) | R² within |
|---|---|---|---|---|---|---|---|
| year only (the S11/S13 figure) | **−0.0469** | 0.0112 | −4.19 | 0.0076 | [−0.0749, −0.0245] | 1.00 | 0.285 |
| **year + log(cond)** | **−0.0105** | 0.0043 | −2.46 | **0.0036** | **[−0.0211, −0.0020]** | 1.27 | 0.921 |
| year + log(cond) + A/c | −0.0104 | 0.0041 | −2.51 | 0.0030 | [−0.0207, −0.0025] | 1.27 | 0.922 |

**The year coefficient shrinks by 78%**, from −0.0469 to −0.0105, and adding A/c
changes nothing further. The variance inflation factor on year is 1.27, so this
is not a collinearity artifact — year and conditioning are close to orthogonal and
the shrinkage is a genuine reallocation of explained variation, not instability.

The coefficient remains distinguishable from zero and the interval excludes it.
But the magnitude is transformed: over the eight-year sample the implied movement
is **0.073, not 0.375** — about 20% of the mean residual gap of 0.357, where
S12 and S13 reported roughly half.

**Eight-cluster limitation, stated regardless of outcome.** With G = 8 the
attainable two-sided p-value floor from Rademacher weights is 2⁻⁷ = 0.0078, and
all three p-values here sit at or below it. The test is saturated; these are not
conventional evidence at any nominal level, whichever way they come out. What the
design can support is the point estimate and the direction, not a significance
claim.

### **The trend survives in this corrected form**

> Controlling for fit conditioning, the exponent steepens by **0.0105 per year**
> (cluster-robust SE 0.0043, wild cluster bootstrap interval [−0.0211, −0.0020] at
> eight clusters), against an uncontrolled figure of 0.047. **Four-fifths of the
> headline trend was fits becoming less identified in high-volatility years.** The
> anomaly is shrinking, by about 0.07 over 2016–2023, or a fifth of the residual
> gap, not half of it.

---

## Consolidated kill-condition record

A numbering collision in the programme's own record must be stated: **the label
K1 was used in S05 for the MCS-composition condition, and item 61 re-labelled that
same condition K2 from S08 onward**, while the spec's section 7 already used K2
for grid-invariance. The table below names each condition by content and shows
both labels it carried.

| condition (content) | labels | determination | margin | chosen before or after item 106 |
|---|---|---|---|---|
| Reliability correction does not change MCS composition | K1 (S05) → K2 (item 61) | **DOES NOT FIRE** (S08); **INDETERMINATE** placebo-corrected (S09) | 48 of 72 differ; clean-geometry excess 20.8% but not tracking λ | before |
| No reliability estimator is grid-invariant | K2 (item 26) | **FIRES** | λ·Var(log RV) max/min ratio 1.05 best, 1.97 worst | before |
| Proxy-error scaling inconsistent with sampling theory | K3 (items 36/37) | **STANDS** | b −0.44 to −0.97 against a −1.13 to −1.21 reference; reference outside the 95% interval in 54 of 54 proxy-fits | before |
| Sizing consequence null | K3 sizing (item 71) | **FIRES** | max R2-vs-R3 relative TE difference 1.008% vs 5% | before |
| Risk-limit breaches | K4 (item 92) | **stop-out FIRES; leverage cap UNTESTED** | 0.966% vs 1%; 0.042 bps vs 1 bp; cap bound 0 of 2,524 | before |
| Combination weights | K5 (item 93) | **FIRES** | TE difference 0.50% vs 5%; weight criterion by 4×10⁻⁵ | before |
| Convexity adjustment | K6 (item 94) | **DOES NOT FIRE** | overstatement 5.9%–134% vs 5%; tightest cell 5.94% | before |
| Risk parity | K7 (item 103) | **FIRES** | mean \|Δw\| 0.000145 vs 0.02; vol difference 0.0038% vs 5% | before |
| Regime misclassification | K8 (item 107) | **DOES NOT FIRE** | analytic 7.9–13.6% vs 5%; tercile empirical 6.0–11.9% | **after** |
| HAR persistence attenuation | K9 (item 108) | **INDETERMINATE** (S15) | 4.8%–116% vs 10%, spanning the threshold on the Σ_E choice | **after** |
| Hurst bias | K10 (item 109) | **DOES NOT FIRE** | ΔH 0.027–0.213 vs 0.02 on a fixed lag window | **after** |

### The item-106 criterion's predictive record

Of the seven applications chosen **before** the criterion was articulated, five
fired (K3-sizing, K4 stop-out, K5, K7, and grid-invariance in the opposite
direction), one did not (K6), and one was untestable (K4's leverage cap).

Of the three chosen **after** it, **none fires**: K8 and K10 fail outright and K9
is indeterminate but cannot be shown to fire under the noise specification S14
used.

The criterion — that the quantity depends on the variance of the estimate and
that averaging does not reduce the contamination — is therefore **3 for 3 on the
direction it predicts, with one of the three unresolvable on a separate ground**.
Two cases sharpen it. K6 fired before the criterion existed and is a ratio, so it
would have been selected by it; the criterion is not merely descriptive of what
was tried after. And K9's indeterminacy is not a failure of the criterion but of
the noise measurement feeding it, which is the programme's own central open
question resurfacing inside an application.

---

## What changes, in one place

| claim | status after S15 |
|---|---|
| K10, Hurst bias 0.032–0.208 | **SURVIVES**, restated on the common window as **0.027–0.213**, with the magnitude flagged as nugget-sensitive and no point estimate reaching 0.5 |
| K9, daily coefficient +19% to +116%, daily share 45–53% → 54–111% | **WITHDRAWN.** Determination indeterminate; the direction and the reliability ordering stand, the magnitudes and the sign flip do not |
| Trend −0.047 per year | **SURVIVES at −0.0105 per year** after the conditioning control, a 78% reduction; the shrinking-anomaly claim holds at a fifth of its stated size |
| S14's forecast result under corrected coefficients | unchanged, and unaffected by the Σ_E question |
| K8, A7 bound, 2022 identification finding | unchanged |
| Everything in S09–S13 not named above | unchanged |

Per item 114 no further measurement session follows. Recorded as further work and
not pursued: settling Σ_E by measuring proxy error against an instrument that does
not share the window; the RTH residual, which survives three tested mechanisms;
and the roughness question, where this programme can now state a bias direction
and an ordering but not a level.

---

## Persisted artifacts

`results/` — `phase1_k10_decomposition.csv`, `phase1_nugget_sensitivity.csv`,
`phase2_k9_check.csv`, `phase2_error_correlations.csv`,
`phase3_trend_control.csv`, `s15_summary.json`.

`cache/` — `k10_moments.npz` (the raw q-th absolute moment and the implied S(Δ)
at every lag for every cell and q, with the lag vector and the common window),
`k9check_*.npz` (the measured proxy error series, both log series, Σ_XX, the
naive coefficient vector, the classical fraction, v fitted and v measured, per
cell), `trend_wcb.npz` (all 9,999 bootstrap t-statistics for each of the three
trend specifications, with the seed).

`src/` — `confounds.py`.
