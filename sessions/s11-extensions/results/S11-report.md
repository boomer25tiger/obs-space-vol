# Session 11 — Defect correction, extensions, and financial applications

Two halves. **Diagnostics**: repair the floor defect S10 found, and follow the
exponent anomaly into the four places S10 left open — grid span, time, the
calibration S10 flagged as its own weakest assumption, and the proxy itself.
**Applications**: three pre-registered decisions where a threshold or a ratio
intervenes, each with a kill condition fixed in items 92–94 before any result.

Interpreter `~/venvs/obs-space-vol/bin/python`, realpath
`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13`, numpy 2.5.2,
pandas 3.0.5, outside every synced path. DECISIONS items 66–85 verified at lines
398–515; items 86–94 appended and verified at lines 523, 531, 533, 538, 543, 547,
553, 557, 562.

The S09 sources are prior artifacts and were **not edited**. The floor defect
lives in the regression drivers, not the predictor builders: `phase5_signals.build`,
`phase6_holdout.wins` and `phase6_holdout.feature_block` all return raw, un-logged
values and are imported unmodified. Only the driver is re-executed with item 86's
drop rule in place of the floor.

---

# Part I — Diagnostics

## Phase 1 — Floor defect correction

Item 86's rule: a window whose predictor is zero has no defined log-predictor and
is dropped. `logdrop()` reads only the predictor vector. The target is dropped
separately where log RV_{t+1} is undefined, identically for all nine candidates —
a missing-target drop, not selection on the target's value.

**Drop counts, in sample** (`phase1_insample.csv`):

| candidate | cells with drops | windows dropped | max share of a cell |
|---|---|---|---|
| JumpVar | 16 of 16 | 70,602 | 49.4% |
| RS_down | 8 of 16 | 1,895 | 2.35% |
| RS_up | 8 of 16 | 1,279 | 1.50% |
| CrossLeadLag | 2 of 16 | 10 | 0.26% |
| Parkinson, Garman-Klass, realized quarticity, volume surprise, signature slope | 0 | 0 | 0 |

**The corrected partition** (extended range, 144 candidate-cells):

| | clears both | only after measured | neither | raw but not measured | in flip band |
|---|---|---|---|---|---|
| S09 (floored) | 96 | 3 | 45 | 0 | 3 |
| **S11 (dropped)** | **128** | **1** | **15** | **0** | **1** |

**32 of 144 change status** — twice S10's estimate of 16, because S10's repair
substituted the smallest positive value, which for jump variation leaves a large
cluster at an extreme and keeps R² near zero. Item 86's drop rule is the correct
treatment and lifts jump variation in all 16 cells. Every change is a promotion:
all 32 go from failing to clearing. The changed set is jump variation in all 16
cells, plus RS-up and RS-down at all 8 RTH intraday cells.

The flip band per cell is unchanged in width (it depends only on λ): from
[0.0188, 0.02) at NQ/GLOBEX/1day, width 0.0012, to [0.0079, 0.02) at ES/RTH/30min,
width 0.0121. What changes is occupancy — **one** candidate-cell now sits in its
band, against three before. Correcting the predictor made the reliability
correction matter *less* for retention, not more.

**Holdout, item 88** — only the three touched candidates, every threshold and
parameter unchanged. The headline case:

| ES/RTH/1h RS-up | in sample | out of sample |
|---|---|---|
| S09 (floored) | 0.0128 | 0.2369 |
| S11 (dropped) | **0.4286** | **0.2369** |

The out-of-sample number does not move at all: the holdout window contained no
zero-semivariance hour, so nothing was ever floored there. **The "dead in sample,
strong out of sample" anomaly was entirely an in-sample artifact.** Corrected, the
cell degrades from 0.429 to 0.237, which is ordinary — the clears-both group
degrades from 0.45 to 0.27 on average.

Jump variation moves out of sample too, and by more: ES/RTH/1h from 0.00021 to
0.1671, ES/GLOBEX/1day from 0.0053 to 0.1540. The 16 cells where jump variation
was recorded as dead all carry real predictive content once the zeros are dropped
rather than floored.

## Phase 2 — Grid span against instrument and horizon

S10's residual after pooling is not uniform: 0.463 on ES against 0.251 on NQ, and
rising as the horizon shortens. Short horizons also carry the narrowest grids, so
span is confounded with horizon. Phase 2 breaks the confound by refitting the
1day cells on grids truncated to the coarse-end position of the 1h and 30min grids.

| cell | full grid | b | truncated to 1h coarse end | b | truncated to 30min | b |
|---|---|---|---|---|---|---|
| ES/GLOBEX/1day | 10 pts, M≤1379 | −0.4427 | 6 pts, M≤46 | −0.7103 | 5 pts, M≤23 | −0.5578 |
| NQ/GLOBEX/1day | 10 pts, M≤1379 | −0.6886 | 6 pts, M≤46 | −0.7809 | 5 pts, M≤23 | −0.6389 |
| ES/RTH/1day | 8 pts, M≤389 | −0.6274 | 5 pts, M≤26 | −0.9295 | 5 pts, M≤26 | −0.9295 |
| NQ/RTH/1day | 8 pts, M≤389 | −0.9744 | 5 pts, M≤26 | −1.0131 | 5 pts, M≤26 | −1.0131 |

**The residual does not track grid span, and span runs the wrong way.** Narrowing
a 1day grid makes b *steeper*, while the actual short-horizon cells are *flatter*:

| | horizon effect (1day → target) | span effect (truncation) | share from span |
|---|---|---|---|
| ES → 1h | −0.1616 | +0.3020 | **−1.87** |
| ES → 30min | −0.2163 | +0.3020 | **−1.40** |
| NQ → 1h | −0.1712 | +0.0387 | **−0.23** |
| NQ → 30min | −0.2734 | +0.0387 | **−0.14** |

The share attributable to span is negative in all four comparisons. Span, if
anything, masks part of the horizon effect rather than creating it. The residual
tracks **instrument and horizon**, not grid width. (All truncated fits except the
GLOBEX six-point ones fail the S10 tightened screen on point count, and are
reported as diagnostics of the span question rather than as measurements.)

## Phase 3 — Time trend in b

Within-year exponents from S10's 128 clean year sub-fits, regressed on year.

**All 16 cells have a negative slope: b is getting steeper, i.e. moving toward
the sampling-theory reference, over 2016–2023.**

| cell | slope/yr | SE | p | b 2016 | b 2023 |
|---|---|---|---|---|---|
| ES/RTH/1day | −0.1204 | 0.0386 | 0.021 | −0.461 | −1.208 |
| NQ/RTH/1day | −0.0684 | 0.0319 | 0.076 | −0.868 | −1.092 |
| ES/RTH/1h | −0.0483 | 0.0297 | 0.154 | −0.483 | −0.670 |
| ES/GLOBEX/1day | −0.0410 | 0.0292 | 0.209 | −0.633 | −0.736 |
| NQ/RTH/1h | −0.0306 | 0.0205 | 0.187 | −0.755 | −0.873 |
| ES/RTH/30min | −0.0249 | 0.0218 | 0.297 | −0.594 | −0.564 |
| NQ/GLOBEX/1day | −0.0226 | 0.0211 | 0.327 | −0.744 | −0.823 |
| NQ/RTH/30min | −0.0190 | 0.0212 | 0.404 | −0.866 | −0.821 |

Pooled with cell fixed effects on the **eight distinct** cells (B0 and B1 are
exact duplicates; pooling all 16 inflates t by √2 and is reported only to show
that): slope **−0.0469 per year**, clustered SE 0.0112, **t = −4.19, p = 0.0041**
over eight clusters. Over the eight-year sample that is a drift of about 0.33 in
b, roughly half the average gap to the reference.

So the anomaly is **shrinking over time**. Two of sixteen cells reach individual
significance; the pooled result does not depend on them.

## Phase 4 — Reliability against out-of-sample degradation

λ_intercept beside the candidate set's in-sample-to-holdout R² degradation,
recomputed under the Phase 1 correction.

| cell | λ | R² in sample | R² out of sample | degradation |
|---|---|---|---|---|
| NQ/GLOBEX/1day | 0.940 | 0.417 | 0.249 | 0.168 |
| NQ/RTH/1day | 0.931 | 0.430 | 0.284 | 0.146 |
| ES/RTH/1day | 0.840 | 0.457 | 0.300 | 0.157 |
| ES/GLOBEX/1day | 0.827 | 0.451 | 0.270 | 0.181 |
| NQ/RTH/1h | 0.810 | 0.336 | 0.198 | 0.138 |
| NQ/RTH/30min | 0.677 | 0.320 | 0.211 | 0.109 |
| ES/RTH/1h | 0.588 | 0.383 | 0.250 | 0.134 |
| ES/RTH/30min | 0.396 | 0.345 | 0.234 | 0.110 |

Spearman ρ = **0.762**, exact p = 0.028; Pearson r = 0.737, p = 0.037. More
reliable cells degrade *more*, which is the opposite of the naive reading and is
explained by their having more in-sample R² to lose.

**Power limitation, stated rather than buried.** There are eight distinct cells,
not sixteen — B0 and B1 are duplicates by construction. At n = 8 a two-sided
Spearman test has roughly 25% power against ρ = 0.7 at the 5% level, so a null
here would be uninformative, and this significant result rests on eight points of
which four share an instrument and four share a horizon. It is reported as a
descriptive association, not a test.

## Phase 5 — Volatility of volatility

c from the S10 fit is Var(log IV) free of proxy noise. Bootstrap interval from
S10's 2,000 joint resamples.

| cell | M | c [95%] | sd(log IV) | 1-sd vol ratio | naive Var(log RV_M) | overstatement, variance | overstatement, sd |
|---|---|---|---|---|---|---|---|
| ES/GLOBEX/1day | 276 | 1.034 [0.931, 1.116] | 1.017 | 1.663 | 1.250 | +20.9% | +9.9% |
| NQ/GLOBEX/1day | 276 | 1.085 [1.015, 1.158] | 1.042 | 1.684 | 1.155 | +6.4% | +3.1% |
| ES/RTH/1day | 78 | 1.081 [0.997, 1.161] | 1.040 | 1.682 | 1.287 | +19.1% | +9.1% |
| NQ/RTH/1day | 78 | 1.057 [0.986, 1.123] | 1.028 | 1.672 | 1.135 | +7.4% | +3.6% |
| ES/RTH/1h | 12 | 1.052 [0.947, 1.133] | 1.026 | 1.670 | 1.789 | **+70.1%** | +30.4% |
| NQ/RTH/1h | 12 | 1.425 [1.378, 1.469] | 1.194 | 1.816 | 1.759 | +23.4% | +11.1% |
| ES/RTH/30min | 6 | 0.815 [0.638, 0.948] | 0.903 | 1.571 | 2.060 | **+152.6%** | +58.9% |
| NQ/RTH/30min | 6 | 1.368 [1.308, 1.418] | 1.170 | 1.795 | 2.023 | +47.8% | +21.6% |

The one-standard-deviation volatility ratio is 1.57 to 1.82: a one-sigma move in
log integrated variance changes volatility by 57% to 82%. Naive Var(log RV) at
five-minute-equivalent sampling overstates the variance of log IV by 6% to 153%,
and the overstatement grows sharply as the horizon shortens. Every grid point is
in `phase5_vol_of_vol.csv`.

## Phase 6 — Roughness with calibrated σ_w (item 89)

S10 assumed σ_w = √1.02 = 1.010 and flagged it as its weakest assumption. Within-
window dispersion is measurable: RQ/RV² has value exactly 1 under constant
within-window volatility, and its excess measures dispersion. Measured through
`parta.quart_suite`, the Part A code path, with the synthetic passed through the
same function at the same M and window count so the finite-M bias cancels.

| cell | M | measured RQ/RV² | excess | ratio to trigamma |
|---|---|---|---|---|
| ES/GLOBEX/1day | 276 | 3.044 | +2.044 | 3.032 |
| NQ/GLOBEX/1day | 276 | 3.607 | +2.607 | 3.594 |
| ES/RTH/1day | 78 | 1.506 | +0.506 | 1.487 |
| NQ/RTH/1day | 78 | 1.586 | +0.586 | 1.565 |
| ES/RTH/1h | 12 | 0.933 | −0.067 | 0.858 |
| NQ/RTH/1h | 12 | 0.937 | −0.063 | 0.862 |
| ES/RTH/30min | 6 | 0.778 | −0.222 | 0.657 |
| NQ/RTH/30min | 6 | 0.781 | −0.219 | 0.659 |

**Calibrated σ_w runs from 1.495 to 4.805, against S10's assumed 1.010** — S10
was low by a factor of 1.5 to 4.8. The A6 sweep re-run at calibrated σ_w
(`make_a6` imported unmodified from S10, five seeds per point):

| H | ES/GLOBEX | NQ/GLOBEX | ES/RTH | NQ/RTH |
|---|---|---|---|---|
| 0.05 | −0.898 | −0.936 | −1.040 | −0.990 |
| 0.10 | −0.926 | −0.860 | −1.000 | −1.050 |
| 0.20 | −0.850 | −0.821 | −1.042 | −0.894 |
| 0.30 | −0.892 | −0.796 | −0.953 | −0.959 |
| 0.45 | −0.901 | −0.814 | −1.015 | −0.982 |
| 0.50 | −0.859 | −0.842 | −1.044 | −0.939 |
| max seed sd | 0.097 | 0.105 | 0.100 | 0.110 |
| range of b | 0.077 | 0.140 | 0.092 | 0.156 |

**The hypothesis remains NOT SUPPORTED and the inversion is again not performed.**
The map is non-monotonic in all four cells and the whole range of b across the H
sweep is at or below the between-seed SD in every one. No implied H, no comparison
against the lag-direction estimator.

**But the negative is now informative in a way S10's was not.** At calibrated
σ_w the *level* of b lands inside the observed range [−1.00, −0.41] in all four
cells, where at S10's assumed σ_w it sat at −1.06 to −1.18. S10's conclusion that
"within-window roughness of any Hurst index, at any scale tried, produces an
exponent at the reference" is **corrected**: at the measured scale it produces an
exponent at the observed value. What does not work is H. Within-window volatility
**heterogeneity** flattens the exponent; the **roughness** of that heterogeneity
does not. The mechanism is dispersion, not fractional dynamics.

## Phase 7 — The exponent as a proxy specification test (item 90)

Var(log X_M) = c + A·M^b for realized variance, the flat-top realized kernel at
the BNHLS (2009) bandwidth H* = 3.5134·ξ^(4/5)·n^(3/5), and the ZMA (2005)
two-scale estimator at its published subsample count, on identical windows. All
three estimators and both tuning rules imported unmodified from S02
`proxies_robust`. 2,000 bootstrap resamples per fit, master seed 20260825.

| cell | b RV | b RK | b TSRV | RK − RV | TSRV − RV |
|---|---|---|---|---|---|
| ES/GLOBEX/1day | −0.443 | −0.601 | −0.475 | −0.159 | −0.032 |
| NQ/GLOBEX/1day | −0.689 | −0.527 | −0.581 | +0.162 | +0.107 |
| ES/RTH/1day | −0.627 | −0.713 | −0.455 | −0.086 | +0.172 |
| NQ/RTH/1day | −0.974 | −0.729 | −0.586 | +0.245 | +0.389 |
| ES/RTH/1h | −0.466 | −0.498 | −0.477 | −0.032 | −0.011 |
| NQ/RTH/1h | −0.803 | −0.491 | −0.570 | +0.313 | +0.234 |
| ES/RTH/30min | −0.411 | −0.088 | −0.327 | +0.323 | +0.084 |
| NQ/RTH/30min | −0.701 | −0.407 | −0.439 | +0.294 | +0.262 |
| SPY/ARCX/TICK | −0.533 | −0.606 | −0.564 | −0.072 | −0.031 |
| SPY/XNAS/TICK | −0.599 | −0.671 | −0.534 | −0.072 | +0.064 |

Diagnostics by proxy (medians over 18 fits each): RMSE 0.016 / 0.035 / 0.037,
condition number 39.0 / 48.3 / 52.7, SE(b) 0.053 / 0.063 / 0.061 for
RV / RK / TSRV. Fourteen of eighteen pass the tightened screen for each proxy —
the same four RTH/30min cells fail on grid size for all three.

**The trigamma reference lies outside the 95% bootstrap interval on b in 54 of
54 fits.** Mean b is −0.631 (RV), −0.521 (RK), −0.495 (TSRV): the noise-robust
proxies are on average *flatter*, not steeper.

**Item 90's second reading holds: flat b for all three locates the anomaly in the
price process, not in realized variance.** The sign is mixed cell by cell — the
kernel is steeper than RV in 8 of 18 cells and flatter in 10 — and the pattern in
that mixture is systematic: on NQ the noise-robust proxies are flatter in every
cell (+0.11 to +0.39), on ES and SPY they are steeper in five of eight. But no
cell, on any proxy, comes near the reference. Removing microstructure noise by
two independent published methods does not recover the sampling-theory exponent.
Combined with Phase 6, the anomaly is a property of how volatility is distributed
inside the window, which no proxy for the same window can remove.

---

# Part II — Applications

The structural claim under test (item 91) is that proxy noise is second-order
where the loss surface is smooth and first-order wherever a threshold or a ratio
intervenes. All sizing runs use the S09 harness with no parameter changed; the
"best available integrated variance" is the flat-top realized kernel at the
finest grid. `ho_series`, which re-executes the S07 `series()` tail on the
holdout panel, was verified byte-identical to `series()` on the in-sample panel
across all six fields and four cells before any holdout number was used.

## Phase 8 — Risk-limit breaches (K4)

Leverage cap 2.0×, stop-out at realized volatility above 1.5× target, both fixed
in item 92. Classification under a proxy-based forecast against a
kernel-based forecast.

| cell | limit | decision points | both | spurious | missed | spurious rate | missed rate | mean spurious duration |
|---|---|---|---|---|---|---|---|---|
| ES/GLOBEX | leverage cap | 641 | 0 | 0 | 0 | 0.00% | 0.00% | — |
| NQ/GLOBEX | leverage cap | 641 | 0 | 0 | 0 | 0.00% | 0.00% | — |
| ES/RTH | leverage cap | 621 | 0 | 0 | 0 | 0.00% | 0.00% | — |
| NQ/RTH | leverage cap | 621 | 0 | 0 | 0 | 0.00% | 0.00% | — |
| ES/GLOBEX | stop-out | 641 | 20 | 2 | 13 | 0.31% | 2.03% | 1.0 |
| NQ/GLOBEX | stop-out | 641 | 21 | 1 | 6 | 0.16% | 0.94% | 1.0 |
| ES/RTH | stop-out | 621 | 20 | 4 | 14 | 0.64% | 2.25% | 1.0 |
| NQ/RTH | stop-out | 621 | 21 | 6 | 5 | 0.97% | 0.81% | 1.0 |

The leverage cap never binds at a 10% volatility target: the position would need
daily volatility below 0.32%, about 5% annualised, which the holdout never
delivered. Every spurious deleveraging episode lasted exactly one day.

Cost across the full sweep, basis points per decision point:

| cell | 0.5t | 1.0t | 2.0t | 4.0t |
|---|---|---|---|---|
| ES/GLOBEX stop-out | 0.0025 | 0.0051 | 0.0101 | 0.0203 |
| NQ/GLOBEX stop-out | 0.0003 | 0.0007 | 0.0014 | 0.0028 |
| ES/RTH stop-out | 0.0052 | 0.0105 | 0.0209 | **0.0418** |
| NQ/RTH stop-out | 0.0022 | 0.0043 | 0.0086 | 0.0172 |

**K4 FIRES, on both criteria independently.** Maximum spurious breach rate 0.97%,
below the 1% threshold in every cell; maximum cost 0.042 bps, below the 1 bp
threshold at every sweep point. Note NQ/RTH at 0.97% is close to the threshold —
the margin is one cell and six days.

The interesting number is not the spurious rate but the **missed** rate, which is
larger in three of four cells (0.81% to 2.25%). A noisy proxy under-detects
genuine volatility breaches more often than it invents false ones, because noise
inflates the estimated volatility used to size and therefore shrinks the position
that would have breached. That was not what item 92 was written to catch and it
is reported as an observation, not a determination.

## Phase 9 — Combination weights (K5)

Inverse-MSE combination over the seven-model set. MSE measured in log space so
the Phase 7 noise term is commensurate: E[MSE_i] = true MSE_i + A·M^b, so the
corrected MSE subtracts the Phase 7 fitted noise variance at that grid
(0.171, 0.054, 0.151, 0.052 for ES/GLOBEX, NQ/GLOBEX, ES/RTH, NQ/RTH).

| cell | mean \|Δw\| | max \|Δw\| | models excluded | TE naive | TE corrected | relative difference |
|---|---|---|---|---|---|---|
| ES/GLOBEX | **0.0200** | 0.0500 | 0 | 0.347097 | 0.345354 | 0.50% |
| ES/RTH | 0.0108 | 0.0198 | 0 | 0.340639 | 0.341119 | 0.14% |
| NQ/GLOBEX | 0.0040 | 0.0138 | 0 | 0.331180 | 0.330949 | 0.07% |
| NQ/RTH | 0.0045 | 0.0079 | 0 | 0.319814 | 0.319955 | 0.04% |

No corrected MSE came out at or below zero, so no model was excluded in any cell.
Turnover falls slightly under the corrected weights in all four cells and the
cost difference is at most 0.017 bps at the 4-tick point.

The seven forecasts are highly correlated in logs — median pairwise 0.775, max
0.979 — which is why a weight change of up to 0.05 moves tracking error by half a
percent. Two models, M3_HARJ and M4_HARQ, carry log-space MSEs of 1,281 and 4,465
and receive weights below 1e-4 under either scheme; they neither help nor
contaminate the comparison.

**K5 FIRES.** The tracking-error criterion passes with room to spare: 0.50%
maximum against a 5% threshold. The weight criterion passes only just —
ES/GLOBEX's mean |Δw| is 0.019960 against a threshold of 0.02, a margin of
4×10⁻⁵. If the weight criterion alone had been pre-registered, K5 would be a
coin flip on that cell. It fires because item 93 requires either criterion, and
the tracking-error one is not close.

## Phase 10 — Convexity adjustment (K6)

Brockhaus and Long (2000), second-order Taylor expansion of the square root
around E[V]: K_vol ≈ √E[V] − Var(V)/(8·E[V]^{3/2}). With V lognormal,
Var(V)/E[V]² = e^{s²} − 1, so the adjustment is √E[V]·(e^{s²} − 1)/8 with
s² = Var(log IV). Quoted on a 20% annualised variance-swap strike so the figures
are in volatility points.

| cell | s² corrected (c) | s² naive | adjustment, corrected [95%] | adjustment, naive | difference | overstatement |
|---|---|---|---|---|---|---|
| ES/GLOBEX/1day | 1.034 | 1.250 | 4.53 [3.84, 5.13] | 6.22 | **1.69** | +37.4% |
| NQ/GLOBEX/1day | 1.085 | 1.155 | 4.90 [4.40, 5.46] | 5.43 | 0.53 | +10.8% |
| ES/RTH/1day | 1.081 | 1.287 | 4.87 [4.28, 5.48] | 6.56 | 1.69 | +34.7% |
| NQ/RTH/1day | 1.057 | 1.135 | 4.69 [4.20, 5.18] | 5.28 | 0.58 | +12.4% |
| ES/RTH/1h | 1.052 | 1.789 | 4.66 [3.94, 5.26] | 12.46 | **7.80** | +167.4% |
| NQ/RTH/1h | 1.425 | 1.759 | 7.89 [7.42, 8.37] | 12.01 | 4.12 | +52.2% |
| ES/RTH/30min | 0.815 | 2.060 | 3.15 [2.23, 3.95] | 17.11 | **13.96** | **+443.3%** |
| NQ/RTH/30min | 1.368 | 2.023 | 7.32 [6.75, 7.83] | 16.40 | 9.07 | +123.9% |

**K6 DOES NOT FIRE.** The overstatement is 10.8% to 443%, against a 5% threshold,
and exceeds it in all eight cells by a wide margin. Even the best case, NQ/GLOBEX
at +10.8%, is more than double the threshold, and the bootstrap interval on c
never comes close to closing the gap.

Direction: naive s² exceeds c in every cell, so the naive convexity adjustment is
**too large** and the implied volatility-swap strike **too low**. That favours the
side that is long volatility at the quoted strike — the payer of fixed on a
volatility swap receives an artificially cheap strike.

**No options data is held. This is a pricing-bias calculation on the adjustment
term only, and no claim is made about executable P&L.** Whether the bias is
tradeable depends on bid-offer, on what convention a dealer actually uses to
estimate s², and on the variance-swap strike itself, none of which is measured here.

---

# What changes and what stands

**Changes.**

- **S09's Phase 5 partition is void and replaced** (item 87): 96/3/45 becomes
  128/1/15, with 32 of 144 candidate-cells changing status, all promotions.
- **S10's estimate of the defect's reach was half the true figure** — 16 status
  changes against 32 — because its min-positive substitution is not the right
  repair for a candidate that is legitimately zero half the time.
- **S10 Phase 6's σ_w was low by 1.5× to 4.8×.** The rejection of the roughness
  mechanism stands, but S10's accompanying statement that within-window variation
  "at any scale tried produces an exponent at the reference" is corrected: at the
  measured scale it produces an exponent at the observed value. The mechanism is
  within-window volatility dispersion, not its Hurst index.
- **The "dead in sample, strong out of sample" RS-up anomaly is dissolved**, not
  explained by a regime change: in sample was broken, out of sample was always
  right, and the corrected cell degrades normally.

**Stands.**

- **S09's K3 sizing null** (extended range, max 1.008% relative tracking-error
  difference) — untouched; the candidate set is not part of it.
- **S09's K2 INDETERMINATE** — untouched.
- **S10's determination A**, now on stronger footing: the reference lies outside
  the 95% interval on b in 54 of 54 proxy-fits, not merely 18 of 18 RV fits.
- **S10's pooling share** of a mean 36% of the gap, and its withdrawal of the
  volatility-tercile evidence.
- **S10 Phase 4**: the return distribution accounts for 8.6% of the gap.
- **K3 (proxy-error scaling): STANDS**, and Phase 7 now locates it — the anomaly
  survives two independent noise-robust proxies, so it is in the price process,
  not in realized variance.

**New.** Three results with no precedent in the programme: the exponent has been
steepening at 0.047 per year (p = 0.004, cell-clustered), so the anomaly is
shrinking; calibrated within-window volatility dispersion reproduces the observed
exponent level while its roughness does nothing; and the naive estimate of
Var(log IV) overstates the variance-to-volatility convexity adjustment by 11% to
443%, which is the first place in this programme where proxy noise has a
first-order economic consequence.

## Determinations

| kill condition | outcome | margin |
|---|---|---|
| **K4, risk-limit breaches** | **FIRES** | both criteria: max spurious rate 0.97% vs 1%, max cost 0.042 bps vs 1 bp |
| **K5, combination weights** | **FIRES** | on tracking error (0.50% vs 5%); the weight criterion passes by 4×10⁻⁵ |
| **K6, convexity** | **DOES NOT FIRE** | overstatement 10.8%–443% vs a 5% threshold, in all eight cells |

Item 91's structural claim survives its own test in a sharper form than it was
stated. Proxy noise is second-order at a threshold when the threshold is far from
where the distribution sits — the leverage cap never binds, the stop-out
misclassifies under 1% of days. It is first-order in a **ratio**: the convexity
adjustment divides a variance by a mean and the noise does not cancel, giving an
error of up to 14 volatility points on a 20-point strike. Of the three decisions
tested, the one that fails is the only one where the quantity of interest is a
function of the *variance of* the volatility estimate rather than of its level.

---

## Persisted artifacts

`results/` — `phase1_insample.csv`, `phase1_holdout.csv`, `phase1_partition_rows.csv`,
`phase1_vs_s09.csv`, `phase1_flip_band.csv`, `phase1_holdout_vs_s09.csv`,
`phase1_summary.json`, `phase2_grid_span.csv`, `phase2_decomposition.csv`,
`phase3_time_trend.csv`, `phase3_pooled_trend.json`,
`phase4_reliability_vs_degradation.csv`, `phase4_summary.json`,
`phase5_vol_of_vol.csv`, `phase5_five_minute.csv`, `phase6_partA_ratio.csv`,
`phase6_measured_ratio.csv`, `phase6_calibration.csv`, `phase6_a6cal_raw.csv`,
`phase6_a6cal_agg.csv`, `phase6_determination.json`, `phase7_proxy_fits.csv`,
`phase7_tuning.csv`, `phase7_proxy_compare.csv`, `phase7_summary.json`,
`phase8_confusion.csv`, `phase8_costs.csv`, `phase9_weights.csv`,
`phase9_forecast_corr.csv`, `phase9_sizing.csv`, `phase9_te_compare.csv`,
`phase10_convexity.csv`, `phase8910_summary.json`, `phase2345_timers.json`.

`cache/` — `a6cal_*.npz` (120 calibrated A6 runs: log-RV matrix, grid, log-IV
path, seed, H, σ_w, embedding eigenvalue diagnostics; full return panel for seed
index 0), `p7boot_*.npz` (54 × 2,000 bootstrap draws with grid, variance vector,
seed and point estimate), `k4_*.npz` (both position series, both forecasts, both
proxies, λ and the kernel bandwidth per cell), `k5_*.npz` (both combination
forecasts, position series and the seven-element weight vector per cell).

`src/` — `common11.py`, `phase1_floor.py`, `phase2345.py`, `phase6_calibrated.py`,
`phase7_proxyspec.py`, `phase8910_apps.py`.
