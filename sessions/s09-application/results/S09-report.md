# Session 9 — Application: sizing consequence, signal status, holdout validation

Final measurement session of the programme (item 73: none follows). Every number
below regenerates from the persisted artifacts listed in section 8. Interpreter
`~/venvs/obs-space-vol/bin/python`, numpy 2.5.2, pandas 3.0.5,
Python 3.13.13, realpath outside every synced location; the gate was verified at
session start and again inside Phase 6 immediately before the holdout opened.

Organised by decision point rather than by phase.

---

## Decision point 1 — Which grid do you fit the intercept on? (Phase 3)

Item 66 required the intercept fit on both the original S05 grid and the extended
grid, neither alone. The answer is not cosmetic: **on the original grid the
intercept route is unusable in five of eight cells.**

Extended-grid fits reproduce S08 exactly — over 16 cells, max |Δc| = 0 and
max |Δb| = 5.55e-17. So the difference below is the range, not the code.

Five-minute-equivalent reliability, both ranges (`phase3_sizing_params.csv`):

| cell | M(5-min) | restricted c | restricted b | λ_int | λ_theory | extended c | extended b | λ_int | λ_theory |
|---|---|---|---|---|---|---|---|---|---|
| ES/GLOBEX/1day | 276 | −1112.63 | −0.000102 | **−890.21** | 1.000007 | 1.0339 | −0.4427 | 0.8272 | 0.9930 |
| NQ/GLOBEX/1day | 276 | 0.9811 | −0.3456 | 0.8496 | 0.9926 | 1.0853 | −0.6886 | 0.9399 | 0.9933 |
| ES/RTH/1day | 78 | 0.4462 | −0.1445 | **0.3466** | 0.9450 | 1.0809 | −0.6274 | **0.8398** | 0.9765 |
| NQ/RTH/1day | 78 | 1.0185 | −0.6259 | 0.8976 | 0.9751 | 1.0568 | −0.9744 | 0.9313 | 0.9760 |
| ES/RTH/1h | 12 | — undefined — | | | | 1.0519 | −0.4658 | 0.5881 | 0.8530 |
| NQ/RTH/1h | 12 | — undefined — | | | | 1.4249 | −0.8032 | 0.8102 | 0.8871 |
| ES/RTH/30min | 6 | — undefined — | | | | 0.8153 | −0.4111 | 0.3958 | 0.6737 |
| NQ/RTH/30min | 6 | — undefined — | | | | 1.3684 | −0.7010 | 0.6765 | 0.7760 |

Three failure modes on the restricted range:

1. **Undefined (4 cells).** The original S05 grid holds one M at each RTH
   intraday horizon (60 for 1h, 30 for 30min). A three-parameter fit needs four
   points. No substitution was made; the cells are reported as undefined.
2. **Degenerate (1 cell).** ES/GLOBEX/1day returns b = −1.02e-4. With the power
   term flat across the grid, c and A are not separately identified; the
   optimiser drives c to −1112.63 and λ to −890. The fit reports a finite RMSE
   and passes the S08 validity screen (A > 0, b < 0), so **the existing validity
   screen does not catch this** — a nonsense λ propagates downstream unless the
   unit-interval check is applied separately, which is why every table here
   carries a `lam_in_unit` flag.
3. **Materially different where both work (ES/RTH/1day).** λ = 0.347 restricted
   against 0.840 extended, a factor of 2.4. This is the one cell where the
   restricted range gives a usable but substantively different answer, and it is
   also the cell where the sizing rules disagree most on the holdout (below).

B0 and B1 are identical in every row. The S08 λ code path rebuilds its returns
from the raw close grid and applies only the tradeability mask, so the boundary
treatment never enters the reliability estimate. That is a property of the code
path, stated here rather than presented as a finding.

**Reading.** The extended range is the only one that supports the intercept
route across the cell set. Where the restricted range is usable it either agrees
(NQ, both geometries, within 0.05) or disagrees by a factor of 2.4 (ES/RTH). Any
claim resting on λ must say which grid it was fit on.

---

## Decision point 2 — Does the reliability correction change how you size?

### 2a. On simulated paths (Phase 4) — the simulation does not decide this

Five seeds from master 20260819 (seeds logged in `phase34_meta.json`), R0–R3,
both ranges, two arms. Between-seed dispersion is small throughout: on the A2
arm, tracking-error SD across seeds is 0.006–0.012 against means near 0.58, and
turnover SD is 30–40% of the turnover mean.

| arm | ES/GLB ext | ES/RTH ext | NQ/GLB ext | NQ/RTH ext |
|---|---|---|---|---|
| A2 R2 vs R3, rel. TE diff | 3.40% | 3.00% | 1.20% | 1.00% |
| A4p R2 vs R3, rel. TE diff | 15.37% | 13.10% | 4.94% | 4.32% |

**Neither arm is a fair test of the sizing question, and I state that rather than
quote the numbers as an answer.** The A2 arm — the pre-registered S05E path — draws
log IV i.i.d. across sessions. There is nothing to forecast, so the HAR forecast
collapses to the unconditional mean, turnover falls to ~9e-5 in weight units, and
shrinking harder is mechanically better: R3 wins because λ is smaller, not because
it is measured. The A4p arm adds S05E's rough (H = 0.1) persistence, which is
strongly anti-persistent; the HAR forecast is then anti-informative, tracking error
roughly triples to 1.3–1.7 and turnover explodes to 10–170 in weight units. One arm
has no dynamics to forecast, the other has dynamics the forecaster gets backwards.

R0 confirms the harness is right: oracle tracking error is 2e-17 to 4e-17 in every
cell, i.e. exactly zero to floating point.

The sizing question is therefore decided on the holdout, where the forecast runs
on real persistent volatility. That was already the pre-registered venue (item 71:
"K3 is evaluated on the holdout, not in sample").

### 2b. On the holdout (Phase 6) — the correction is worth less than 1% of tracking error

Holdout 2024-01-01 to 2026-08-14 by CME trade date. 2,847,047 raw rows extracted,
373,743 spread rows filtered, 0 unresolved symbols, 0 weekend trade dates, 641
GLOBEX and 621 RTH sessions per root after R1 and the roll rule. Eleven degraded
dates fall in the window and are flagged, not excluded, exactly as in sample.

Extended range, ES and NQ, both geometries (`phase6_sizing_oos.csv`):

| cell | TE R1 | TE R2 | TE R3 | R3 vs R2 | turnover R1 → R3 | cost 4t R1 → R3 (bps) |
|---|---|---|---|---|---|---|
| ES/GLOBEX | 0.377979 | 0.377719 | 0.375499 | −0.588% | 0.0746 → 0.0628 | 0.2422 → 0.2039 |
| ES/RTH | 0.378079 | 0.376906 | 0.373106 | −1.008% | 0.0907 → 0.0777 | 0.2943 → 0.2521 |
| NQ/GLOBEX | 0.344571 | 0.344288 | 0.342490 | −0.522% | 0.0569 → 0.0539 | 0.0508 → 0.0481 |
| NQ/RTH | 0.335715 | 0.334662 | 0.333122 | −0.460% | 0.0687 → 0.0645 | 0.0613 → 0.0575 |

R3 beats R2 in all four cells, always by less than 1.1% of tracking error. The
direction is consistent; the magnitude is not economically interesting. The
turnover reduction is larger in relative terms (4–16%) but the level is tiny: at
the most punitive sweep point, 4 ticks per leg, the whole cost of running the
strategy is 0.05–0.29 bps, and the R2/R3 difference within that is 0.003–0.042 bps.

Cost sweep, all four points, extended range (`phase6_sizing_oos.csv`): costs scale
exactly linearly in the tick assumption, so the ratio R2:R3 is invariant across
the sweep at 15.30% (ES/GLOBEX), 12.52% (ES/RTH), 4.80% (NQ/GLOBEX), 4.08%
(NQ/RTH). Tracking error itself does not depend on the cost assumption.

**Restricted range, same holdout.** ES/GLOBEX R3 is unusable (λ = −890, TE = 106,
turnover 1.0e9 — the degenerate fit propagating). ES/RTH is the informative case:
λ = 0.347 over-shrinks, and R3 tracking error is 0.402155 against R2's 0.375567 —
**7.08% worse, and worse than doing nothing (R1, 0.378079)**. NQ cells behave like
the extended range (0.84% and 0.69%). So on the restricted range the measured
correction actively hurts in the one cell where it is both defined and different.

### 2c. In-sample against holdout degradation (Phase 7)

Same code, same frozen parameters, pre-2024 panels (`phase7_degradation.csv`):

| cell | TE in-sample (R3, ext) | TE holdout (R3, ext) | degradation |
|---|---|---|---|
| ES/GLOBEX | 0.323207 | 0.375499 | +16.2% |
| ES/RTH | 0.331999 | 0.373106 | +12.4% |
| NQ/GLOBEX | 0.303038 | 0.342490 | +13.0% |
| NQ/RTH | 0.302248 | 0.333122 | +10.2% |

Degradation is 9–18% across all rules and both ranges, and is essentially the same
for R1, R2 and R3. The holdout is harder than the estimation sample by about a
sixth of tracking error, and the choice of shrinkage rule does not change that.

Quarterly tracking error over the 11 holdout quarters (extended, R3) has mean
0.328–0.372 with SD 0.033–0.049 and a max of 0.405–0.444. Item 72's aggregation
requirement is met: the strategy's realized return series is aggregated to
quarters before tracking error is formed, at which frequency proxy attenuation is
negligible, so the measurement does not reuse the proxy whose reliability is the
object of study.

---

## Decision point 3 — Does the correction change which signals you keep? (Phases 5, 6)

Nine pre-registered candidates (item 70), threshold R² ≥ 0.02, forward realized
variance at the five-minute equivalent, 16 cells on the extended range.

**Ranking is unchanged by construction.** The correction divides every candidate
in a cell by the same λ, so within-cell ordering is invariant and only threshold
crossing can move. Stated as a property, not a finding, per item 70. The measured
data show it directly: the candidate ordering by median R² is identical before and
after correction (Garman-Klass 0.574 → 0.738, realized quarticity 0.569 → 0.730,
Parkinson 0.566 → 0.730, cross lead-lag 0.479 → 0.674, RS-up 0.312 → 0.339, RS-down
0.303 → 0.328, volume surprise 0.0431 → 0.0641, jump variation 0.00162 → 0.00223,
signature slope 0.000635 → 0.000928).

Three-way partition (`phase5_partition.csv`), extended range, 144 candidate-cells:

| partition | n |
|---|---|
| clears under both | 96 |
| clears only after the measured correction | 3 |
| clears neither | 45 |
| clears raw but not measured | 0 |

**The correction changes status in 3 of 144 cases, 2.1%.** All three are ES/RTH:
RS-up at 1h under B0 (R² 0.01276) and B1 (0.01282), and signature slope at 1day
under B1 (0.01831). All three sit in the flip band.

**The flip band.** A candidate's status can change only if its raw R² lies in
[0.02·λ, 0.02). The band width is 0.02·(1 − λ), so it is set entirely by the
cell's reliability: at ES/RTH/30min (λ = 0.396) the band is [0.0079, 0.02), the
widest in the set; at NQ/GLOBEX/1day (λ = 0.940) it is [0.0188, 0.02), narrow
enough that essentially nothing can cross. Exactly 3 of 144 candidate-cells fall
in their band, the same 3 that change status. No candidate has a raw R² anywhere
near the band in the high-reliability cells.

Restricted range, split by whether λ is in the unit interval:

| range | λ ∈ (0,1] | n | both | only-after-measured | neither | raw-only |
|---|---|---|---|---|---|---|
| restricted | yes | 54 | 42 | 1 | 11 | 0 |
| restricted | no | 18 | 0 | 0 | 4 | 14 |
| extended | yes | 144 | 96 | 3 | 45 | 0 |

The 14 "clears raw but not measured" are entirely the ES/GLOBEX degenerate cells:
dividing by λ = −890 makes every corrected R² negative, so 14 genuinely strong
candidates (median raw R² 0.534) are rejected. That is the degenerate fit
manufacturing false rejections, not a reliability effect.

**Holdout (Phase 6).** Of the 96 extended-range candidate-cells that cleared under
both in sample, 95 clear raw out of sample and 96 clear after the measured
correction. Mean R² falls from 0.479 to 0.313, a degradation of 0.166. The 45
clears-neither stay at zero (0.0033 → 0.0027). Of the 3 that cleared only after
correction, 2 clear out of sample and clear decisively — the ES/RTH 1h RS-up pair
go from R² 0.0128 in sample to 0.237 and 0.240 out of sample. The third,
signature slope at ES/RTH/B1/1day, falls to 0.0023 and does not clear. So the
correction promoted three candidates and two of them were real.

That is the strongest evidence in the session that the measured correction does
something useful — but it is three cases out of 144, and it changes retention, not
ranking or weighting.

---

## Decision point 4 — Is the S-B/S-C composition difference real? (Phases 1, 2)

Item 67 held that the raw S-B versus S-C rate is not reportable because the two
schemes condition on different variables and so evaluate different day subsets.
Phase 1 supplies the placebo: scheme S-D conditions on F_{t−1}, the previous
window's M2_HAR forecast, which carries no proxy content, at the same quantiles
q ∈ {0.80, 0.90}. Full MCS, 10,000 moving-block resamples, both confidence levels,
per-cell seeding from master 20260819.

72 comparisons available (24 of 96 halted). Raw rates and the excess
(`phase1_stratified.csv`, `phase12_summary.json`):

| stratum | n | S-B vs S-C | S-D vs S-C | excess |
|---|---|---|---|---|
| all | 72 | 66.7% | 50.0% | 16.7% |
| RTH | 48 | 68.8% | 47.9% | **20.8%** |
| GLOBEX | 24 | 62.5% | 54.2% | 8.3% |
| ES | 40 | 77.5% | 52.5% | 25.0% |
| NQ | 32 | 53.1% | 46.9% | 6.3% |
| q = 0.80 | 36 | 66.7% | 44.4% | 22.2% |
| q = 0.90 | 36 | 66.7% | 55.6% | 11.1% |

**Half the raw effect is subset variation.** The placebo, which cannot involve
proxy quality, flips MCS composition in 50% of comparisons on its own. The
reportable quantity — the excess — is 16.7% overall and 20.8% on clean geometry.

Does the excess track reliability across horizons? RTH only (`phase1_excess_by_horizon.csv`),
with λ at the finest M as the horizon's reliability:

| horizon | n | S-B vs S-C | S-D vs S-C | excess | λ (finest M) |
|---|---|---|---|---|---|
| 1day | 16 | 68.8% | 56.3% | 12.5% | 1.001 |
| 1h | 16 | 75.0% | 31.3% | **43.8%** | 0.856 |
| 30min | 16 | 62.5% | 56.3% | 6.3% | 0.713 |

**No.** The section 2.2 mechanism predicts the excess grows as reliability falls.
The observed excess is largest at the middle horizon and smallest at the least
reliable one. The five-minute-equivalent λ from Phase 3 orders the horizons the
same way (1day 0.83–0.94, 1h 0.59–0.81, 30min 0.40–0.68), so the failure to track
is not an artefact of which λ is used.

**K2 determination: INDETERMINATE.** The pre-registered logic fires only if the
excess is near zero (|excess| < 0.10, mechanism absent) and rules the mechanism in
only if the excess is large (> 0.20) *and* tracks λ. The clean-geometry excess is
0.208, above the threshold, but it does not track λ. Excluding the 7 cells whose
MCS composition is itself seed-unstable, the excess rises to 25.0% — still not
tracking. The evidence is a real residual effect of the right sign and size with
the wrong cross-horizon signature; that is neither a confirmation nor a kill.

**Phase 2, seed stability on the flipped comparisons.** 20 seeds from master
20260820 over the 19 cells whose S08 composition changed. 178 (cell, scheme, level)
rows; 165 return the identical model set under all 20 seeds; 13 vary. The modal
set contains the S08 set in 178 of 178 rows, so nothing in S08 was a seeding
accident. The 13 unstable rows are concentrated at q = 0.90 and the 1day horizon,
where the conditioned subsample is smallest, with modal frequency as low as 10 of
20 (NQ/RTH/B1/1day, S-C q0.90, mcs90). Those 7 cells are the ones excluded from
the recount above.

---

## Decision point 5 — K3 (Phase 7)

Item 71: K3 fires if the R2-versus-R3 tracking-error difference is below 5% in
relative terms in every cell and at every point of the cost sweep, evaluated on
the holdout. Tracking error does not depend on the cost assumption, so the
relative difference is identical at all four sweep points; the sweep discriminates
only the turnover charge, reported alongside.

| range | cells | max relative TE difference | verdict |
|---|---|---|---|
| **extended** | 4 | **1.008%** (ES/RTH) | **K3 FIRES** |
| restricted | 4 (3 with λ in unit) | 7.08% (ES/RTH); 27,968% including the degenerate cell | K3 DOES NOT FIRE |

**On the extended range, K3 fires.** The pre-registered null stands: replacing the
textbook shrinkage weight with the measured one changes tracking error by at most
1.008% in relative terms, in the same direction in every cell, at every point of a
cost sweep spanning an eightfold range of transaction cost. Measured reliability
is real and it is large — λ runs from 0.40 to 0.94 against a textbook 0.67 to 0.99
— but at a 10% volatility target with daily rebalancing it does not change the
position enough to matter.

On the restricted range K3 does not fire, and it fails in the wrong direction: the
one cell where the restricted λ is both defined and materially different produces
a 7.08% *deterioration*. The sizing conclusion is therefore conditional on the
extended grid, which is the second reason item 66's both-ranges requirement earned
its place.

---

## Decision point 6 — What the session settles and what it does not

Settled:

- The intercept route needs the extended grid. On the original S05 grid it is
  undefined in half the cells and degenerate in another, and the existing
  A > 0, b < 0 validity screen does not catch the degeneracy.
- Measured reliability does not change sizing to a degree worth acting on
  (K3 fires, extended range, holdout).
- Measured reliability changes signal retention in 2.1% of candidate-cells, never
  ranking, and the flip band [0.02λ, 0.02) predicts exactly which ones.
- Half the S-B/S-C composition effect is subset variation with no proxy content.
- MCS composition under the S08 seeds was not a seeding accident (178 of 178).

Not settled:

- K2 remains INDETERMINATE. A residual excess of the right size exists but does
  not track reliability across horizons.
- K3 stands from S07/S08 in its original form: proxy error decays materially more
  slowly than sampling theory predicts (b from −0.41 to −1.00 against trigamma's
  −1.14). Nothing in this session touched that, and the two K3 statements are
  independent — the sizing null firing does not resolve the scaling anomaly, it
  says the anomaly has no sizing consequence at this target and rebalance
  frequency.
- The synthetic arms available to this programme cannot adjudicate a sizing rule.
  Both S05E arms are degenerate for that purpose in opposite directions.

Per item 73, no further measurement session follows. Roughness, vol-of-vol from
the fitted intercept, the overnight leg, SPY as a second instrument, and
cross-sectional reliability remain recorded as further work and are not pursued.

---

## Persisted artifacts

Every figure above regenerates from these files under `sessions/s09-application/`.

`results/` — `phase1_sd_mcs.csv`, `phase1_comparisons.csv`, `phase1_stratified.csv`,
`phase1_excess_by_horizon.csv`, `phase2_seed_stability.csv`, `phase12_summary.json`,
`phase3_sizing_params.csv`, `phase3_s08_equivalence.csv`, `phase4_sizing_raw.csv`,
`phase4_sizing_agg.csv`, `phase4_r2_vs_r3.csv`, `phase34_meta.json`,
`phase5_signals.csv`, `phase5_partition.csv`, `phase5_status_changes.csv`,
`phase6_calendar.csv`, `phase6_sizing_oos.csv`, `phase6_te_quarterly.csv`,
`phase6_candidates_oos.csv`, `phase6_partition_oos.csv`, `phase6_summary.json`,
`phase7_sizing_insample.csv`, `phase7_degradation.csv`, `phase7_k3_inputs.csv`,
`phase7_k3.json`.

`cache/` — `sim_{arm}_{root}_{geom}_s{seed}.npz` (40 simulated paths: true IV,
five-minute-equivalent RV, forecast, log-IV path, seed, warm-up),
`ho_panel_{root}_{geom}.npz` (holdout OHLC panels, present and tradeable masks),
`ho_bars_{GLOBEX,RTH}.parquet` (holdout engineered bars),
`ho_sizing_{root}_{geom}.npz` (holdout RV, forecast, dates, frozen mu, price level),
`ho_pos_{root}_{geom}_{range}_{rule}.npz` (24 holdout position series).

`src/` — `phase12_placebo.py`, `phase34_sizing.py`, `phase5_signals.py`,
`phase6_holdout.py`, `phase7_k3.py`.

`results/S09-integrity-scan.txt` is retained under item 74 as a record of the void
scan of 2026-08-19 and carries no evidential weight.
