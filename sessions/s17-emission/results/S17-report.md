# Session 17 — Measurement error in the model rather than the observable

## Result hierarchy (item 122), stated first

The programme's **primary** results are the proxy-error scaling exponent
(S07–S15), the intercept estimator for λ (S08, S15), and the first-order
criterion separating decisions where proxy noise matters from those where it does
not (S11, S13, S14). K1 through K12 are **applications** of that criterion and are
secondary. S17 asks where the measured parameter can be *inserted*. Its answer is
negative, and that bears on insertion, not on measurement. Nothing below revises a
primary result.

Interpreter `~/venvs/obs-space-vol/bin/python`, numpy 2.5.2, pandas
3.0.5, outside every synced path. DECISIONS items 66–121 verified present at lines
398–730 (56 of 56); items 122–128 appended and verified at lines 735, 742, 752,
757, 766, 771, 777. **Holdout read in Phase 4 only — the seventh opening** (item
128). S17 is the last measurement session.

---

## Phase 1 — A2 lag alignment: the S16 claim is largely withdrawn

Item 123 was right. S16 compared a five-day *trailing* filter against a
*contemporaneous* reference and attributed the resulting phase mismatch to the
filter's noise treatment.

Two controls. **Phase-matched**: the identical five-day moving average applied to
the noise-robust kernel before classification, so filter and reference share their
phase and their smoothing. **Best lag**: A2's states shifted forward over integer
lags 0–10 against the unsmoothed reference, minimised.

Holdout, gap of A2 over A1 in percentage points:

| cell | S16 gap | **phase-matched gap** | best-lag gap | best lag |
|---|---|---|---|---|
| ES/GLOBEX 1day | +10.61 | **+0.16** | +5.95 | 2 |
| NQ/GLOBEX 1day | +11.86 | **+1.40** | +9.09 | 2 |
| ES/RTH 1day | +9.34 | **+1.77** | +5.18 | 2 |
| NQ/RTH 1day | +6.76 | **−3.06** | +3.25 | 2 |
| ES/RTH 1h | +9.61 | **−0.13** | +4.73 | 2 |
| NQ/RTH 1h | +38.08 | **−2.95** | +37.56 | 3 |
| ES/RTH 30min | +1.10 | **−3.42** | +0.56 | 4 |
| NQ/RTH 30min | +6.62 | **+19.65** | +4.57 | 1 |

**The best lag is 2 days in every daily cell**, exactly the lag a five-day
trailing mean induces, which is the arithmetic item 123 set out.

Under phase matching the gap is **negative in four of eight cells** and below 2 pp
in six. The one large positive, NQ/RTH/30min at +19.65, is a cell whose A1 rate is
26.5% and whose smoothed-reference rate is 46.2% — the reference itself degrades
under smoothing there, so the comparison is not informative about A2.

The two controls disagree, and the disagreement is interpretable: phase-matching
removes both the phase shift and the smoothing, best-lag removes only the phase.
The residual under best-lag alone is roughly half the S16 figure. **Phase-matching
is the better control**, because it applies the identical filter to both sides.

**Verdict: the S16 claim that the published smoothing raises misclassification is
WITHDRAWN in its stated form.** What survives is narrower: against a
contemporaneous reference the moving average costs 6.8 to 38.1 pp, but essentially
all of that is the filter's phase lag rather than a noise-handling defect. Against
a phase-matched reference it costs between −3.4 and +1.8 pp in seven of eight
cells. The item-117 objection to the moving average as an *unmotivated* treatment
stands on its own terms; the empirical case S16 built for it does not.

**NQ/RTH/1h specifically.** Item 123 asked whether A2's 46.03% is distinguishable
from chance at n = 3,726. It is — a binomial test gives p < 1e-5, roughly five
standard errors from 50% — so the cell does carry information, contrary to what
the raw figure suggests. But the phase-matched rate is **4.99%**, better than A1's
7.94%. The 38-point gap is entirely phase and scale, not accuracy.

---

## Phase 2 — The 30-minute inversion: unexplained

Item 124 flagged NQ/RTH/30min running 48.48% in sample and 26.53% out of sample,
and named label swapping under close state means as the leading candidate.

Per-window emission parameters, recorded for both 30-minute cells:

| cell | sample | mean separation | min mean gap | share gap < 0.25 | share gap < 0.10 |
|---|---|---|---|---|---|
| ES/RTH | in sample | 1.828 | 0.924 | 0.0% | 0.0% |
| ES/RTH | holdout | 1.784 | 0.840 | 0.0% | 0.0% |
| NQ/RTH | in sample | 1.709 | **0.00003** | **17.4%** | **6.9%** |
| NQ/RTH | holdout | 1.668 | 0.00044 | 6.9% | 3.0% |

**Label instability is real and is concentrated exactly where item 124 predicted**
— NQ/RTH in sample carries 17.4% near-degenerate windows against 6.9% in the
holdout, and ES/RTH carries none at all.

But it does not explain the inversion. Restricting to windows whose state means
are separated by at least 0.50:

| | unrestricted | restricted (gap ≥ 0.50) | share retained | movement |
|---|---|---|---|---|
| NQ/RTH in sample | 48.476% | 47.808% | 65.3% | **0.67 pp** |
| NQ/RTH holdout | 26.526% | 26.564% | 85.8% | **−0.04 pp** |

That accounts for **3% of a 21.95 pp inversion**. And separability is ruled out
too: mean state separation is 1.709 in sample against 1.668 in the holdout,
essentially identical.

**Verdict: neither of item 124's candidates accounts for it, and the inversion
REMAINS UNEXPLAINED.** The S16 figures are not superseded — no corrected labelling
produces materially different numbers — but they are flagged as carrying an
unexplained in-sample-to-holdout inversion. ES/RTH/30min shows no instability and
sits at chance on both sides, so its 48.8 → 47.0 movement is not an inversion and
needs no correction.

---

## Phase 3 — Arm A4 in sample

### The estimator, its identifiability condition, and its validation

With σ_k² = max(total_k − v, 0) the emission variance is **max(total_k, v)**. A4
is therefore the free-variance HMM **with a variance floor at v**, identical to A1
in every window where both states' unconstrained variances clear the floor. The
identifiability condition item 125 asks for — the fixed noise floor must not
exceed the total emission variance in either state — is also the *reach*
condition, and it is reported per window.

Validated before use on synthetic data with known state variance and known added
observation noise (seed 20260841, T = 3,000, v = 0.30):

| quantity | true | free HMM | fixed-noise HMM |
|---|---|---|---|
| state means | (−0.700, 0.800) | (−0.7165, 0.8147) | (−0.7165, 0.8147) |
| **total** emission variance | (0.4225, 0.6025) | **(0.4225, 0.5763)** | (0.4225, 0.5763) |
| **state** variance σ² | (0.1225, 0.3025) | not identified | **(0.1225, 0.2763)** |

The free HMM recovers the total; the fixed-noise HMM recovers the state variance
by subtracting known v; their means agree to ten decimal places. **The estimator
is correct, and that correctness is precisely why it cannot change a
classification except through the floor.**

### Reach, reported before any outcome

| cell | λ | v (raw, scale 1.00) | windows binding | states differing from A1 |
|---|---|---|---|---|
| ES/GLOBEX 1day | 0.827 | 0.216 | **0 of 1,461** | **0** |
| NQ/GLOBEX 1day | 0.940 | 0.069 | **0 of 1,508** | **0** |
| ES/RTH 1day | 0.840 | 0.206 | **0 of 1,461** | **0** |
| NQ/RTH 1day | 0.931 | 0.078 | **0 of 1,461** | **0** |
| ES/RTH 1h | 0.588 | 0.737 | 9,643 of 10,966 (88%) | 533 |
| NQ/RTH 1h | 0.810 | 0.334 | 848 of 10,966 (8%) | 20 |
| ES/RTH 30min | 0.396 | 1.244 | 21,756 of 22,372 (97%) | 8,340 |
| NQ/RTH 30min | 0.677 | 0.654 | 13,873 of 22,372 (62%) | 9,418 |

**The floor never binds at the daily horizon and binds in most windows
intraday**, which is what λ predicts: Var(ε) = (1−λ)·Var(log RV) is a far larger
share of a shorter window's variance. Across all cells and scalings, 46,120 of
72,619 windows bind and 18,311 in-sample states differ from A1. **Unlike S16's
observable-side correction, this one has real reach.**

### In-sample outcome

Where it acts, it mostly hurts: ES/RTH/1h **−2.34 pp** at full scaling,
ES/RTH/30min +0.21 pp, NQ/RTH/30min +1.71 pp, NQ/RTH/1h −0.05 pp. The two
improvements are in cells sitting at chance (48%), where any movement is noise.

**The restricted λ range (item 66).** Defined in only three of eight cells. At
ES/RTH/1day, λ = 0.347 gives v = 0.841, the floor binds in **100%** of windows, 80
states differ, and misclassification **worsens by 4.24 pp** in sample. That is the
S10-flagged degenerate restricted fit propagating into an application.

---

## Phase 4 — Holdout and allocation

Holdout built through the wlen-aware path at each cell's own horizon, refitting
only windows ending in the holdout, per the S16 Phase 3 correction. Window counts
641, 641, 621, 621, 3,726, 3,726, 7,452, 7,452 — the S16 defect did not recur.

| cell | A1 | A4 (scale 1.00) | reduction | states differing |
|---|---|---|---|---|
| ES/GLOBEX 1day | 1.248% | 1.248% | **0.00 pp** | 0 |
| NQ/GLOBEX 1day | 3.276% | 3.276% | **0.00 pp** | 0 |
| ES/RTH 1day | 2.254% | 2.254% | **0.00 pp** | 0 |
| NQ/RTH 1day | 5.636% | 5.636% | **0.00 pp** | 0 |
| ES/RTH 1h | 5.153% | 5.851% | **−0.70 pp** | 114 |
| NQ/RTH 1h | 7.944% | 7.944% | **0.00 pp** | 0 |
| ES/RTH 30min | 47.008% | 47.424% | **−0.42 pp** | 749 |
| NQ/RTH 30min | 26.530% | 26.557% | **−0.03 pp** | 28 |
| ES/RTH 1day, **restricted λ** | 2.254% | **12.721%** | **−10.47 pp** | 79 |

**Allocation overlay.** A4 is numerically identical to A1 at every scaling and
every cost point in all four daily cells — same return, volatility, Sharpe,
drawdown, turnover and cost — because zero states differ there. The holdout's own
directional character, which is what makes the overlay figures interpretable:
always-invested delivers Sharpe 0.690 (ES/GLOBEX), 0.643 (NQ/GLOBEX), 0.164
(ES/RTH), 0.019 (NQ/RTH) with drawdowns of −12% to −14%. It was a rising, moderate
-volatility period; an overlay that sits in cash a third of the time gives up
return it cannot recover, which is why every overlay arm including the
reference-kernel control underperforms.

---

## Phase 5 — K12 determination

**K12 FIRES.** A4 reduces misclassification by less than 1 pp against A1 in every
cell — in fact by **0.00 pp at most, at every one of the four pre-registered
scalings**.

| scaling | max reduction | states differing (holdout) | windows binding |
|---|---|---|---|
| 0.25 | **0.00 pp** | 0 | 22,033 |
| 0.50 | **0.00 pp** | 20 | 34,276 |
| 0.75 | **0.00 pp** | 272 | 49,723 |
| 1.00 | **0.00 pp** | 891 | 46,120 |

### Attribution, as item 126 requires

Item 126 asks whether the result is the emission change having no effect, the
effect being real but small, or the noise floor binding. **It is the third, and
the evidence separates it cleanly from the first.**

The floor binds in 63% of all windows and moves 18,311 in-sample and 891 holdout
states. The change is not inert — this is the opposite of S16, where the
correction had literally zero reach. It acts, and acting makes things worse or
leaves them unchanged, never better, in any cell at any scaling.

The reason is in the estimator's algebra. A floor on the emission variance cannot
sharpen a discrimination; it can only widen both densities and pull marginal
observations toward whichever state mean is nearer. Knowing the measurement-error
variance tells the model how uncertain an observation is, but in a two-state
Gaussian HMM where both states carry the *same* known noise, that uncertainty
enters both likelihoods and cancels in the posterior ratio. What does not cancel
is the floor, and the floor is unhelpful.

---

## Consolidated kill-condition record, K1 through K12

The label collision recorded in S15 stands: **K1** was used in S05 for the
MCS-composition condition and item 61 re-labelled it **K2** from S08, while spec
section 7 already used K2 for grid-invariance. Both labels are shown against
content.

| condition | labels | determination | margin | before / after item 106 |
|---|---|---|---|---|
| Reliability correction does not change MCS composition | K1 → K2 (item 61) | DOES NOT FIRE (S08); **INDETERMINATE** placebo-corrected (S09) | 48 of 72 differ; excess 20.8% but not tracking λ | before |
| No reliability estimator is grid-invariant | K2 (item 26) | **FIRES** | λ·Var(log RV) max/min 1.05 to 1.97 | before |
| Proxy-error scaling inconsistent with sampling theory | K3 (items 36/37) | **STANDS** | reference outside the 95% interval in 54 of 54 proxy-fits | before |
| Sizing consequence null | K3 sizing (item 71) | **FIRES** | max R2-vs-R3 TE difference 1.008% vs 5% | before |
| Risk-limit breaches | K4 (item 92) | **stop-out FIRES; cap UNTESTED** | 0.966% vs 1%; 0.042 bps vs 1 bp; cap bound 0 of 2,524 | before |
| Combination weights | K5 (item 93) | **FIRES** | TE difference 0.50% vs 5% | before |
| Convexity adjustment | K6 (item 94) | **DOES NOT FIRE** | overstatement 5.9–134% vs 5% | before |
| Risk parity | K7 (item 103) | **FIRES** | mean \|Δw\| 0.000145 vs 0.02 | before |
| Regime misclassification | K8 (item 107) | **DOES NOT FIRE** | analytic 7.9–13.6% vs 5% | **after** |
| HAR persistence attenuation | K9 (item 108) | **INDETERMINATE** (S15) | 4.8–116% vs 10%, spanning the threshold | **after** |
| Hurst bias | K10 (item 109) | **DOES NOT FIRE** | ΔH 0.027–0.213 vs 0.02 | **after** |
| Regime classification under an observable-side correction | K11 (item 119) | **DOES NOT FIRE** | 0.00 pp from the correction; the effect is A3 not being A2 | **after** |
| Measurement error in the emission | K12 (item 126) | **FIRES** | 0.00 pp maximum reduction at every scaling, with 63% of windows binding | **after** |

**The item-106 criterion's record.** Seven applications chosen before it: five
fire, one does not (K6), one untestable. Five chosen after it: K8 and K10 fail,
K9 is indeterminate, K11 fails, and **K12 fires** — the first post-criterion
application to do so. K12's firing does not weaken the criterion; it sharpens it.
The criterion says proxy noise is first-order where the quantity depends on the
variance of the estimate and averaging does not reduce it. A two-state HMM's
posterior depends on the *ratio* of two densities that carry the same noise, so
the noise cancels — the quantity does not depend on the estimate's variance in the
way the criterion requires, and the criterion correctly predicts a null.

---

## What S17 establishes, and what it does not

**Establishes.** S16 closed the observable-side route: any affine correction is
annihilated by within-window z-scoring. S17 closes the model-side route for this
class of model: putting the measured noise variance into the emission gives the
correction real reach — 63% of windows, 18,311 states — and no benefit anywhere.
Between them, the two sessions exhaust the routes by which a scalar reliability
parameter can enter a two-state Gaussian HMM regime classifier.

**Does not establish.** That λ is wrong, or that measurement error is irrelevant
to state-space models generally. A model whose *latent* variable is continuous —
a stochastic-volatility state-space model with a log-variance signal equation and
a known observation-error variance — is a different object, and nothing here tests
it. That is recorded as further work.

**Two corrections to S16 carried out here.** Its A2 claim is withdrawn in its
stated form; phase-matching removes essentially all of the measured gap. Its
NQ/RTH/30min inversion is diagnosed as *not* explained by either candidate and is
flagged unexplained rather than resolved.

**A defect in S16's HMM, found and contained.** `common16.py:50` divides by `c[0]`
without the underflow guard it applies at `c[t>0]` on line 51. When `pi·B[0]`
underflows, the forward pass returns NaN, the warm start propagates it, and EM
runs its full iteration cap without converging. S16's 32 persisted A1/A2 series
were audited and are clean — the underflow is reached only by the MA-smoothed
kernel series introduced here. The S16 artifact is untouched; S17 guards at the
call site and counts failures.

Per item 128 this is the last measurement session. The next artifact is the paper.

---

## Persisted artifacts

`results/` — `phase1_lag_alignment.csv`, `phase2_30min_params.csv`,
`phase2_label_stability.csv`, `phase2_stability_restricted.csv`,
`phase2_determination.json`, `phase12_summary.json`, `phase3_validation.json`,
`phase3_noise_inputs.csv`, `phase3_a4_insample.csv`, `phase4_a4_holdout.csv`,
`phase4_allocation.csv`, `phase345_summary.json`.

`cache/` — `refma_*.npz` (8 phase-matched reference state series),
`params30_*.npz` (per-window emission parameters for both 30-minute cells, in
sample and holdout), `a4is_*.npz` and `a4ho_*.npz` (35 in-sample and 35 holdout A4
runs each carrying the state series, regime probabilities, v, λ and the binding
counts), `alloc17_*.npz` (28 overlay runs with signal, overlay return, base return
and position series).

`src/` — `common17.py` (paths, the fixed-noise emission estimator, the guarded
fit wrapper and the wlen-aware cell builder), `phase12.py`, `phase345.py`.
