# Session 10 — Exponent validity audit and mechanism test

The headline exponent of this programme has been quoted since S07 as "b between
−0.41 and −1.00 against a trigamma reference of −1.14", and has never carried an
error bar (item 80). S10 puts one on it, bounds the grid and pooling artifacts,
and tests the two mechanisms that were never tested. No new data, no holdout.

Interpreter `~/venvs/obs-space-vol/bin/python`, realpath
`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13`, numpy
2.5.2, pandas 3.0.5, outside every synced location. DECISIONS items 66–79
verified present at lines 398–474; items 80–85 appended and verified at lines
485, 490, 497, 502, 510, 515.

---

## Phase 1 — Uncertainty on b

2,000 joint bootstrap resamples over sessions per cell, master seed 20260820,
extended grid, 16 futures cells plus both SPY venues under the traded-tick
convention. The trigamma reference is fitted by the identical free-intercept
procedure applied to trigamma(M/2) on the same grid, which is S05E Phase 1's
construction unchanged.

| cell | n grid | b | 95% interval | SE(b) | trigamma ref | ref inside? | P(b > ref) | cond |
|---|---|---|---|---|---|---|---|---|
| ES/GLOBEX/B0/1day | 10 | −0.4427 | [−0.5508, −0.3398] | 0.0537 | −1.1377 | no | 1.0000 | 25.0 |
| ES/GLOBEX/B1/1day | 10 | −0.4427 | [−0.5461, −0.3412] | 0.0535 | −1.1377 | no | 1.0000 | 25.0 |
| NQ/GLOBEX/B0/1day | 10 | −0.6886 | [−0.8022, −0.5780] | 0.0579 | −1.1377 | no | 1.0000 | 39.0 |
| NQ/GLOBEX/B1/1day | 10 | −0.6886 | [−0.7999, −0.5762] | 0.0575 | −1.1377 | no | 1.0000 | 39.0 |
| ES/RTH/B0/1day | 8 | −0.6274 | [−0.7558, −0.4982] | 0.0658 | −1.1444 | no | 1.0000 | 36.5 |
| ES/RTH/B0/1h | 9 | −0.4658 | [−0.5345, −0.4004] | 0.0341 | −1.2097 | no | 1.0000 | 37.4 |
| ES/RTH/B0/30min | 5 | −0.4111 | [−0.4843, −0.3422] | 0.0365 | −1.1971 | no | 1.0000 | 97.8 |
| ES/RTH/B1/1day | 8 | −0.6274 | [−0.7570, −0.5077] | 0.0640 | −1.1444 | no | 1.0000 | 36.5 |
| ES/RTH/B1/1h | 9 | −0.4658 | [−0.5320, −0.4034] | 0.0323 | −1.2097 | no | 1.0000 | 37.4 |
| ES/RTH/B1/30min | 5 | −0.4111 | [−0.4780, −0.3423] | 0.0347 | −1.1971 | no | 1.0000 | 97.8 |
| NQ/RTH/B0/1day | 8 | −0.9744 | [−1.1255, −0.8353] | 0.0756 | −1.1444 | no | 0.9870 | 70.5 |
| NQ/RTH/B0/1h | 9 | −0.8032 | [−0.8944, −0.7150] | 0.0459 | −1.2097 | no | 1.0000 | 48.4 |
| NQ/RTH/B0/30min | 5 | −0.7010 | [−0.7976, −0.6092] | 0.0483 | −1.1971 | no | 1.0000 | 73.9 |
| NQ/RTH/B1/1day | 8 | −0.9744 | [−1.1264, −0.8289] | 0.0766 | −1.1444 | no | 0.9845 | 70.5 |
| NQ/RTH/B1/1h | 9 | −0.8032 | [−0.8971, −0.7208] | 0.0451 | −1.2097 | no | 1.0000 | 48.4 |
| NQ/RTH/B1/30min | 5 | −0.7010 | [−0.7959, −0.6096] | 0.0482 | −1.1971 | no | 1.0000 | 73.9 |
| SPY/ARCX/TICK | 15 | −0.5333 | [−0.6807, −0.3896] | 0.0736 | −1.1262 | no | 1.0000 | 23.2 |
| SPY/XNAS/TICK | 15 | −0.5985 | [−0.7628, −0.4468] | 0.0809 | −1.1262 | no | 1.0000 | 27.3 |

**The reference lies outside the 95% interval on b in 18 of 18 cells.** Median
SE(b) is 0.054, maximum 0.081, against a gap to the reference of 0.17 to 0.79.
The bootstrap probability that b is at least as flat as measured is 1.0000 in 16
cells and 0.987 / 0.985 in the two NQ/RTH/1day cells, which are the closest
approach anywhere in the set.

Item 81's identifiability concern is real and is now quantified rather than
asserted. Bootstrap corr(c, b) runs from −0.065 to −0.973 and the asymptotic
correlation at the optimum from −0.748 to −0.993, worst in the five-point 30min
cells; bootstrap corr(A, b) has median −0.894. The parameters are strongly
coupled — and the bootstrap interval on b already prices that coupling in,
because it resamples the data and refits all three jointly. Coupled parameters
widen the interval; they do not move it onto the reference.

Full 3×3 correlation matrices per cell are in `phase1_corr.csv`; all 36,000
bootstrap draws are in `cache/boot_*.npz`.

---

## Phase 2 — Grid sensitivity and identifiability

**Leave-one-out.** Dropping each grid point in turn moves b by a median of
0.0191 and a maximum of 0.2316 across all 18 cells. The most influential point
is an endpoint in every single cell — the coarsest M in ten cells, the finest in
six, M = 11700 in both SPY venues. That is the expected signature of a power
law: the endpoints carry the leverage.

Crucially, **grid sensitivity does not approach the gap**: the largest
single-point influence anywhere is 0.232, against a cell-by-cell gap to the
reference of 0.170 to 0.788 and a median gap of 0.483.

**Restricted against extended.** In the four cells where both grids are defined:

| cell | b extended | cond | b restricted | cond | deviation |
|---|---|---|---|---|---|
| ES/GLOBEX/1day | −0.4427 | 25.0 | −0.000123 | **4.99e11** | 0.4425 |
| NQ/GLOBEX/1day | −0.6886 | 39.0 | −0.3456 | 59.7 | 0.3430 |
| ES/RTH/1day | −0.6274 | 36.5 | −0.1445 | 391.2 | 0.4829 |
| NQ/RTH/1day | −0.9744 | 70.5 | −0.6259 | 98.3 | 0.3485 |

Item 81's figure of "up to 0.49" is confirmed at 0.483. But the condition numbers
say which of the two grids is carrying the information: 25–70 on the extended
grid against 60 to 5×10¹¹ on the restricted one. The ES/GLOBEX restricted fit is
not a different measurement of the same quantity, it is a numerically singular
fit.

**Tightened screen** (≥ 2 × 3 = 6 grid points, |b| > 0.01, in addition to A > 0
and b < 0): 14 of 34 fits pass, against 26 of 34 under the old A > 0, b < 0
screen. Failures:

- **The extended grid loses 4 of 18**: the four RTH/30min cells, on point count
  alone (5 points, three parameters). Their b values are −0.411 and −0.701 with
  bootstrap SEs of 0.035–0.048, so the failure is grid size, not a wild estimate.
- **The restricted grid loses all 16**: ten defined fits fail on point count
  (5 < 6), and eight are undefined at one grid point.
- **The ES/GLOBEX/1day restricted case that item 81 named fails on both new
  criteria at once** — 5 points, and |b| = 1.23e-4 against the 0.01 floor. Under
  the old screen it passed, carrying λ = −890 into S09 Phase 5 and manufacturing
  14 false signal rejections there. The tightened screen catches it.

---

## Phase 3 — Pooling

Sub-fits within each year and within each volatility tercile, 192 fits over 16
cells, beside the pooled value and the reference.

**The volatility-tercile leg of item 82 does not survive.** All 48 tercile
sub-fits are degenerate: 32 return A < 0 with |b| between 2 and 67, and the other
16 return the flat-power pathology (b ≈ −1e-4, c ≈ −300 to −900, condition
number 10¹⁰ to 10¹²). Zero are usable. The reason is mechanical: sorting sessions
on realized volatility removes precisely the cross-sectional variation in log IV
that identifies the intercept, so c and A·M^b are no longer separately
identified within a tercile. S05E's "steeper within volatility tercile in 15 of
16" was computed on fits of this kind and is withdrawn here.

**The within-year leg does survive**, and reproduces S05E closely. All 128 year
sub-fits are clean.

| cell | pooled b | within-year mean | sd | years steeper | reference | share of gap |
|---|---|---|---|---|---|---|
| ES/GLOBEX/1day | −0.4427 | −0.6823 | 0.202 | 8/8 | −1.1377 | 0.345 |
| NQ/GLOBEX/1day | −0.6886 | −0.8159 | 0.138 | 7/8 | −1.1377 | 0.284 |
| ES/RTH/1day | −0.6274 | −0.8836 | 0.375 | 6/8 | −1.1444 | 0.495 |
| ES/RTH/1h | −0.4658 | −0.6753 | 0.214 | 8/8 | −1.2097 | 0.282 |
| ES/RTH/30min | −0.4111 | −0.5964 | 0.144 | 7/8 | −1.1971 | 0.236 |
| NQ/RTH/1day | −0.9744 | −1.0783 | 0.254 | 5/8 | −1.1444 | 0.611 |
| NQ/RTH/1h | −0.8032 | −0.9073 | 0.144 | 6/8 | −1.2097 | 0.256 |
| NQ/RTH/30min | −0.7010 | −0.8832 | 0.136 | 7/8 | −1.1971 | 0.367 |

(B0 and B1 are identical; eight distinct cells shown.)

Within-year b is steeper than pooled by a mean of **0.176**, against S05E's
0.182 — an independent reproduction on the full cell set. Mean within-year b is
steeper than pooled in 16 of 16 cells.

**Pooling accounts for a mean 36.0% of the pooled-to-reference gap** (median
31.4%, range 23.6% to 61.1%). After removing it, the residual gap between the
within-year exponent and the reference averages **0.357** and remains in the
same direction in every cell. Item 82's "roughly a quarter" is close; the honest
figure is a third, and a third is not the whole thing.

---

## Phase 4 — Return distribution (arm A5)

Arm A5 is S05E's A0 with the innovation law replaced by a Student-t standardised
to unit variance. Everything downstream — sub-bar aggregation, Var(log RV_M),
the free-intercept fit — is `common.logrv_matrix` / `var_cols` / `fitf`, the same
functions the real cells use. Seven settings, five seeds each, master 20260821,
both geometries, all 140 panels persisted.

For each setting a second sub-arm runs at Var(log IV) = 0. That arm has no
integrated-variance variation at all, so its Var(log RV_M) curve *is* the
sampling variance of log RV under that innovation law — the heavy-tailed
generalisation of trigamma(M/2), and the correct reference for that setting.

| geom | setting | b (signal) | seed sd | move vs Gaussian | b of its own reference arm | in [−1.00, −0.41]? |
|---|---|---|---|---|---|---|
| GLOBEX | Gaussian | −1.2091 | 0.085 | — | −1.1120 | no |
| GLOBEX | ν = 2.95 | −1.1420 | 0.170 | +0.067 | −1.1379 | no |
| GLOBEX | ν = 3 | −1.2202 | 0.069 | −0.011 | −1.1772 | no |
| GLOBEX | ν = 3.67 | −1.0980 | 0.108 | +0.111 | −1.1258 | no |
| GLOBEX | ν = 4 | −1.1220 | 0.067 | +0.087 | −1.1338 | no |
| GLOBEX | ν = 6 | −1.1668 | 0.131 | +0.042 | −1.1200 | no |
| GLOBEX | ν = 10 | −1.1834 | 0.075 | +0.026 | −1.0899 | no |
| RTH | Gaussian | −1.1847 | 0.121 | — | −1.1186 | no |
| RTH | ν = 2.95 | −1.0885 | 0.114 | +0.096 | −1.1537 | no |
| RTH | ν = 3 | −1.1578 | 0.124 | +0.027 | −1.1172 | no |
| RTH | ν = 3.67 | −1.2306 | 0.088 | −0.046 | −1.1680 | no |
| RTH | ν = 4 | −1.1194 | 0.107 | +0.065 | −1.1616 | no |
| RTH | ν = 6 | −1.1207 | 0.066 | +0.064 | −1.1242 | no |
| RTH | ν = 10 | −1.1555 | 0.082 | +0.029 | −1.1526 | no |

**The return distribution does not account for the gap.** At the S04 measured
tail index the move from Gaussian is +0.067 to +0.111 (GLOBEX) and +0.096 to
−0.046 (RTH). Between-seed SD is 0.066 to 0.170, so **every one of those moves is
inside seed noise**, and two of the six move in the wrong direction. Expressed as
a share of the real gap (0.572 GLOBEX, 0.343 RTH), the mean is **8.6%**, the
maximum 28.0%, and one setting is negative. No setting enters the observed range
at any degrees of freedom, and there is no monotone trend in ν.

**Is the anomaly the data departing from the reference, or the reference being
wrong?** The reference arms answer it directly. Under Student-t innovations the
sampling-variance exponent stays at −1.09 to −1.18, moving by at most 0.065 from
the Gaussian value and never approaching the observed range. Heavy tails inflate
the *level* of Var(log RV_M) at coarse M, as item 83 argued, but they do not
change its *decay rate*. The reference is not wrong; the data depart from it.

The Gaussian signal arm reproducing b = −1.18 to −1.21 against an analytic
trigamma exponent of −1.11 to −1.14 is the positive control, and matches S05E's
−1.19 on the same code path.

---

## Phase 5 — Gate

A5 accounts for a mean 8.6% of the gap, far below half, with every setting inside
seed noise and none entering the observed range. **The gap is not closed. Phase 6
runs.** Decision recorded in `phase4_summary.json` and `phase6_determination.json`.

---

## Phase 6 — Within-window roughness (arm A6)

Arm A6 is A0 with the log volatility path varying *within* each window as
fractional Brownian motion at Hurst index H, correcting the defect item 84
identifies in A4. The across-session log-IV law is unchanged, so the within-window
mechanism is the only thing that moves. Six H values, five seeds each, master
20260822, both geometries.

σ_w, the within-window log-volatility scale, is measured nowhere in this
programme. It is set to √(VAR_LOG_IV) = 1.010 so that within-window dispersion
equals across-session dispersion, and a sensitivity leg runs at 0.5× and 2×.
**That is a choice, not a measurement**, and it is the weakest assumption in this
phase.

| H | b (GLOBEX) | seed sd | b (RTH) | seed sd |
|---|---|---|---|---|
| 0.05 | −1.1399 | 0.111 | −1.0832 | 0.103 |
| 0.10 | −1.0625 | 0.084 | −1.1758 | 0.094 |
| 0.20 | −1.0614 | 0.074 | −1.0499 | 0.087 |
| 0.30 | −1.0785 | 0.130 | −1.0974 | 0.065 |
| 0.45 | −1.0994 | 0.077 | −1.0589 | 0.066 |
| 0.50 | −1.1262 | 0.086 | −1.1705 | 0.065 |

**The hypothesis is not supported and the inversion is not performed.** The map
is non-monotonic in both geometries — GLOBEX turns twice, RTH four times — and
the *entire range of b across the whole H sweep* (0.079 GLOBEX, 0.126 RTH) is
smaller than the largest between-seed SD (0.130, 0.103). No H enters the observed
range. Under the pre-registered rule (map not monotonic, or separation within
seed noise), the phase stops here: no implied H per cell, no comparison against
the lag-direction estimator.

The negative result is not a sampler artifact: the circulant embedding returned
**zero negative eigenvalues** across all 100 A6 runs, with a minimum eigenvalue of
1.50e-4, so every fBm path is exact rather than clipped.

The sensitivity leg does not rescue it. At 2× σ_w the flattest result anywhere is
b = −0.978 (GLOBEX, H = 0.05) and −1.004 (RTH, H = 0.50) — a move of about 0.16
from doubling the within-window vol-of-vol, still nowhere near the observed
−0.411 to −0.688. At 0.5× σ_w b sits at −1.10 to −1.16. Within-window roughness
of any Hurst index, at any scale tried, produces an exponent at the reference.

---

## Phase 7 — RS-up at ES/RTH/1h

Both S09 code paths were run on the same in-sample panel, so any difference is
the code and not the data.

**It is not an alignment defect.** The two paths produce byte-identical RV and
byte-identical RS-up over all 11,406 windows, and identical R² to 1e-17
(0.01276153611486536 both ways). The lag is a clean one-window shift — predictor
on windows 0…T−2, target on windows 1…T−1 — and windows are disjoint index blocks
of the minute grid by construction, so there is no overlap between a predictor
window and its target in either path.

**It is a floor-substitution defect.** Three windows of 11,406 (0.026%) have
RS-up exactly zero, because no five-minute sub-bar in the hour had a positive
return. The transform `np.log(np.maximum(v, 1e-300))` maps those to −690.78,
against a normal range of about −20 to −8. Three points do this:

| treatment | R² |
|---|---|
| as run in S09 (floor at 1e-300) | **0.0128** |
| the three floored windows dropped | **0.4286** |
| floor replaced by the smallest strictly positive RS-up | **0.4287** |

The defect is at [phase5_signals.py:104](sessions/s09-application/src/phase5_signals.py:104),
`feats[k]=np.log(np.maximum(d[v][:-1],1e-300))`, and identically at
[phase6_holdout.py:330](sessions/s09-application/src/phase6_holdout.py:330). It is
the same 1e-300 floor that DECISIONS item 60 already banned for the forecast
insanity filter, applied here to a predictor that can legitimately be zero.

**So the 0.0128 → 0.237 movement is explained, and the explanation is a defect —
but a floor-substitution defect, not an alignment defect.** The out-of-sample
value of 0.237 is close to the repaired in-sample value of 0.429 and to nothing
else; the holdout window simply contained no zero-semivariance hour. The zero
rate in sample is not stable over time either: two occurrences in 2016, one in
2019, none in the other six years.

**Reach across the S09 signal set.** Of 96 candidate-cells (six log-transformed
candidates × 16 cells), 32 contain at least one zero and **16 change retention
status once the floor is repaired** — RS-up and RS-down at all eight RTH intraday
cells, with R² lifts of 0.18 to 0.48. Parkinson, Garman-Klass and realized
quarticity contain no zeros anywhere and are untouched, which is exactly why they
behaved normally out of sample.

Jump variation is a separate case, not a floor artifact: it is legitimately zero
in 21% to 49% of windows because RV ≤ BV that often. Neither the floored nor the
repaired version clears the threshold in any cell, so its status does not change,
but a log transform is the wrong transform for it and that should be recorded
rather than repaired.

This corrects S09's Phase 5 partition for RS-up and RS-down. It does not touch
S09's headline determinations — the K3 sizing null and the K2 placebo result do
not involve the candidate set.

---

## Determination

**A holds. The exponent anomaly stands, with uncertainty quantified.**

- The trigamma reference lies outside the 95% bootstrap interval on b in
  **18 of 18 cells**. Median SE(b) is 0.054 against a median gap of 0.483, and
  the bootstrap probability that b is at least as flat as measured is ≥ 0.985
  everywhere and 1.0000 in 16 of 18.
- **Grid sensitivity is bounded and below the gap.** Leave-one-out moves b by a
  median 0.019 and at most 0.232, against gaps of 0.170 to 0.788. The
  restricted-grid deviation of up to 0.483 that item 81 raises is real but is
  not a rival measurement: those fits carry condition numbers of 60 to 5×10¹¹
  and all 16 fail the tightened screen, while the extended-grid fits sit at
  25–98.
- **Pooling is bounded and stated: a mean 36.0% of the gap** (median 31.4%,
  range 23.6%–61.1%), leaving a residual of 0.357 in the same direction in every
  cell. Item 82's tercile evidence is withdrawn as degenerate; its within-year
  evidence reproduces at 0.176 against S05E's 0.182.
- **No mechanism arm reproduces it.** Student-t innovations at the measured tail
  index account for 8.6% of the gap on average, inside seed noise, with the
  correct heavy-tailed reference moving by at most 0.065 — so the reference is
  not wrong. Within-window fractional volatility produces a non-monotonic map
  whose entire range is smaller than its own seed noise, at any Hurst index and
  at three within-window scales.

The qualification that belongs on A: under the tightened screen the measurement
stands on **14 of 18 cells**, not 18. The four RTH/30min cells fail on grid size
(5 points, 3 parameters), though their estimates are among the tightest in the
set (SE 0.035–0.048). Anyone quoting the range should quote it from the 14, which
gives b from −0.443 to −0.974 against references of −1.126 to −1.210.

**RS-up is not explained by an alignment defect.** It is explained by a
floor-substitution defect: `log(max(v, 1e-300))` applied to a predictor that is
legitimately zero in three of 11,406 windows, at `phase5_signals.py:104` and
`phase6_holdout.py:330`. Repairing it moves the in-sample R² from 0.0128 to
0.4286 and changes retention status in 16 of 96 candidate-cells.

---

## Persisted artifacts

`results/` — `phase1_bootstrap.csv`, `phase1_corr.csv`, `phase12_summary.json`,
`phase2_leave_one_out.csv`, `phase2_grid_compare.csv`, `phase2_screen.csv`,
`phase3_subfits.csv`, `phase3_pooling.csv`, `phase3_summary.json`,
`phase4_a5_raw.csv`, `phase4_a5_agg.csv`, `phase4_a5_summary.csv`,
`phase4_share.csv`, `phase4_seeds.csv`, `phase4_summary.json`,
`phase6_a6_raw.csv`, `phase6_a6_agg.csv`, `phase6_determination.json`,
`phase7_rsup.json`, `phase7_zero_rate_by_year.csv`, `phase7b_floor_audit.csv`,
`phase7b_summary.json`.

`cache/` — `boot_*.npz` (18 files, 36,000 bootstrap draws with the grid, the
observed variance vector, the seed and the point estimate),
`spy_tick_logrv_{ARCX,XNAS}.npz` (per-session traded-tick log RV matrices),
`a5_*.npz` (140 A5 runs: log-RV matrix, grid, log-IV path, seed, ν; full return
panel for seed index 0 of each setting), `a6_*.npz` (100 A6 runs, same contents
plus H, σ_w and the circulant-embedding eigenvalue diagnostics).

`src/` — `common.py`, `phase12_uncertainty.py`, `phase3_pooling.py`,
`phase4_arm_a5.py`, `phase6_arm_a6.py`, `phase7_rsup.py`, `phase7b_audit.py`.
