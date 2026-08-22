# Session 16 — Regime classification under measured reliability

The reliability correction has **exactly zero reach** under the published
specification, and this is provable before any classification is run. What the
session measures instead is that the published specification's own smoothing —
the step item 117 objects to as unmotivated — is the largest source of
misclassification in the design.

Interpreter `~/venvs/obs-space-vol/bin/python`, realpath
`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13`, numpy 2.5.2,
pandas 3.0.5, outside every synced path. DECISIONS items 66–114 verified present
at lines 398–692 (49 of 49); items 115–121 appended and verified at lines 697,
702, 709, 715, 720, 726, 730.

**Holdout reads: this is the sixth** (item 121). Prior: S09 Phase 6, S11 Phase 1,
S11 Phases 8–9, S13 Phase 2, S14 Phase 1. Read in Phase 3 only.

---

## Phase 1 — The recoverable band, reported before any classification

### The band is empty, and the reason is structural

A3 is an **affine** transform of A1: z = (1−λ)·μ + λ·x. The item-116
specification z-scores the observable **within each rolling window**. For any
window W,

> mean_W(z) = (1−λ)μ + λ·mean_W(x)  and  sd_W(z) = λ·sd_W(x)

so

> (z − mean_W(z)) / sd_W(z) = (x − mean_W(x)) / sd_W(x)

**exactly, for every λ > 0.** The z-scored input to the HMM is identical under A1
and A3. The recoverable band under the published specification is empty and the
ceiling on any improvement is **0.0 percentage points**, by construction.

Verified numerically on the first full window of every cell: maximum absolute
z-score difference **6.3×10⁻¹⁵**, identical to machine precision in 8 of 8.

### Reach of each treatment, for comparison

| treatment | share of days that can reflip |
|---|---|
| **A3, published specification** | **0.00%** — analytically impossible |
| A3 under a fixed threshold (labelled diagnostic, changes a component) | 0.04% – 0.89% (extended λ) |
| **A2, the published 5-day moving average** | **13.0% – 20.1%** |

Both λ ranges are reported per item 66 (`phase1_band.csv`). On the restricted
range λ is undefined at all four RTH intraday cells and degenerate at
ES/GLOBEX/1day (λ = −890, the S10 finding), and reaches 5.73% only at
ES/RTH/1day where the restricted λ of 0.347 is itself the cell S10 flagged.

The fixed-threshold row is a **diagnostic, not a fourth arm**: holding the K8
threshold on the raw scale instead of re-deriving it changes a component, and
item 118 fixes every component but the observable.

**The ceiling this places on K11 is zero.** No result in Phases 2–4 can attribute
any improvement to the reliability correction, whatever else it finds.

---

## Phase 2 — In-sample classification

Rolling 441-observation window stepped one at a time, two-state Gaussian HMM on
the z-scored observable, warm-started across windows, state 0 labelled low
volatility by mean ordering. The reference classification is the **same HMM run
on the finest-grid flat-top realized kernel**, so misclassification is measured
with the classifier held fixed and only the observable varying.

The HMM is new code — hmmlearn is not in `requirements.lock` and the project held
no prior HMM. It was validated before use on a synthetic two-state series:
recovered μ = (−0.573, 0.913) against a true (−0.6, 0.9), σ = (0.496, 0.807)
against (0.5, 0.8), transition matrix to within 0.006, and **98.3% state
accuracy**.

### A1 ≡ A3, empirically

| cell | n compared | states differing | max probability difference |
|---|---|---|---|
| all eight cells | 1,461 to 22,372 | **0** | ≤ 6.5×10⁻¹⁴ |

The analytic result is confirmed, not merely asserted.

### Misclassification against the noise-robust reference

| cell | A1 = A3 | **A2 (published 5-day MA)** | analytic arccos(√λ)/π |
|---|---|---|---|
| ES/GLOBEX 1day | 2.64% | **7.89%** | 13.6% |
| NQ/GLOBEX 1day | 2.12% | **8.84%** | 7.9% |
| ES/RTH 1day | 3.56% | **8.99%** | 13.1% |
| NQ/RTH 1day | 3.49% | **10.71%** | 8.4% |
| ES/RTH 1h | 5.64% | **14.19%** | 22.2% |
| NQ/RTH 1h | 6.49% | **43.60%** | 14.4% |
| ES/RTH 30min | 48.84% | 48.93% | 28.3% |
| NQ/RTH 30min | 48.48% | 48.19% | 19.3% |

Three findings, none of them about the correction:

1. **The published smoothing triples or quadruples misclassification.** A2
   reflips 8.5% to 42.9% of days relative to A1 and gets a large share of them
   wrong. One qualification stated honestly: a 5-day moving average is a lagged
   filter and the reference is contemporaneous, so part of the gap is phase lag
   rather than error — but the arm's stated purpose is to classify the *current*
   state, so the comparison is the operative one.
2. **The HMM's temporal context does what the correction cannot.** The empirical
   rate on A1 (2.1–3.6% daily) sits far below the pointwise analytic rate
   arccos(√λ)/π of 7.9–13.6%. Pooling 441 observations suppresses
   misclassification by a factor of three to six. Part of that gap is the K8
   effect — the reference shares a window with the proxy, so its errors are
   correlated and the empirical figure is a lower bound — but the direction is
   the point: state-space structure buys what an affine correction cannot.
3. **The classifier fails outright at 30 minutes.** Every arm sits at 48–49%
   against the kernel reference, indistinguishable from a coin flip. That is a
   property of the horizon, not of the observable.

---

## Phase 3 — Holdout and allocation

### A defect found and corrected, disclosed

The first Phase 3 run built the holdout portion of every cell through S11's
`ho_series`, which is the S07 `series()` body at wlen = None and therefore
produces **daily windows only**. The four 1day cells were correct; the 1h and
30min cells had 621 daily windows appended to their intraday in-sample series.
The corrected run rebuilds the holdout through `phase6_holdout.wins` at each
cell's own horizon — the wlen-aware path S11 Phase 1 used — refitting only
windows ending in the holdout and warm-starting from the last fully in-sample
window so every holdout window still sees a full 441-observation history. Holdout
window counts go from a uniform 621 to 641, 621, **3,726** and **7,452**. All
figures below are from the corrected run; the allocation overlay uses the 1day
cells and was never affected.

### Classification, in sample against holdout

| cell | arm | in sample | holdout | switches (holdout) | mean duration |
|---|---|---|---|---|---|
| ES/GLOBEX 1day | A1 = A3 | 2.64% | **1.25%** | 48 | 13.1 |
| ES/GLOBEX 1day | A2 | 7.89% | **11.86%** | 32 | 19.4 |
| NQ/GLOBEX 1day | A1 = A3 | 2.12% | 3.28% | 40 | 15.6 |
| NQ/GLOBEX 1day | A2 | 8.84% | **15.13%** | 26 | 23.7 |
| ES/RTH 1day | A1 = A3 | 3.56% | 2.25% | 48 | 12.7 |
| ES/RTH 1day | A2 | 8.99% | 11.59% | 30 | 20.0 |
| NQ/RTH 1day | A1 = A3 | 3.49% | 5.64% | 46 | 13.2 |
| NQ/RTH 1day | A2 | 10.71% | 12.40% | 26 | 23.0 |
| ES/RTH 1h | A1 = A3 | 5.64% | 5.15% | 362 | 10.3 |
| ES/RTH 1h | A2 | 14.19% | 14.76% | 182 | 20.4 |
| NQ/RTH 1h | A1 = A3 | 6.49% | 7.94% | 1,113 | 3.3 |
| NQ/RTH 1h | A2 | 43.60% | **46.03%** | 182 | 20.4 |
| ES/RTH 30min | A1 = A3 | 48.84% | 47.01% | 669 | 11.1 |
| NQ/RTH 30min | A1 = A3 | 48.48% | 26.53% | 1,345 | 5.5 |

A1 ≡ A3 holds out of sample too: **0 states differ** out of 641 to 7,452 in every
cell.

### The allocation overlay

Full exposure to the volatility-targeted book in the low state, cash in the high
state, one-day execution lag, against the always-invested book as benchmark.
Sharpe at 1.0 tick per leg, holdout:

| cell | always invested | A1 = A3 | A2 | **reference kernel** |
|---|---|---|---|---|
| ES/GLOBEX | **0.690** | −0.017 | −0.020 | 0.088 |
| NQ/GLOBEX | **0.643** | 0.356 | 0.382 | 0.233 |
| ES/RTH | **0.164** | −0.306 | −0.492 | −0.256 |
| NQ/RTH | 0.019 | −0.095 | −0.354 | — |

**The overlay destroys value in every cell at every cost point**, and the control
is what makes that interpretable: the **reference_kernel** arm classifies on the
noise-robust proxy — the best regime signal available here — and also
underperforms always-invested everywhere. The overlay's failure is therefore not
a classification-quality problem that a better observable could repair. On this
holdout the regime rule itself is value-destroying, and correcting its input
cannot change that.

Annual overlay cost runs 3.0 to 28.3 bps across the sweep
(`phase3_allocation.csv` carries all four points).

### Excess switching cost, and what the correction recovers of K8's 138 bps

A3 switches identically to A1, so **the correction recovers exactly 0 of K8's 138
basis points**. A2 switches *less* than A1 (26–32 against 40–48 on the daily
cells) because a moving average is a low-pass filter, so its switching cost is
lower while its misclassification is three to five times higher. The published
treatment buys turnover reduction at the price of accuracy; the reliability
correction buys neither.

---

## Phase 4 — K11 determination

Item 119: K11 fires if A3 reduces misclassification by less than 1 percentage
point against **both** A1 and A2 in every cell, **or** if the allocation Sharpe
difference is below 0.10 at every cost-sweep point.

| cell | A1 = A3 | A2 | reduction vs A1 | reduction vs A2 | below 1pp vs both? |
|---|---|---|---|---|---|
| ES/GLOBEX 1day | 1.25% | 11.86% | **0.00 pp** | 10.61 pp | no |
| NQ/GLOBEX 1day | 3.28% | 15.13% | **0.00 pp** | 11.86 pp | no |
| ES/RTH 1day | 2.25% | 11.59% | **0.00 pp** | 9.34 pp | no |
| NQ/RTH 1day | 5.64% | 12.40% | **0.00 pp** | 6.76 pp | no |
| ES/RTH 1h | 5.15% | 14.76% | **0.00 pp** | 9.61 pp | no |
| NQ/RTH 1h | 7.94% | 46.03% | **0.00 pp** | 38.08 pp | no |
| ES/RTH 30min | 47.01% | 48.11% | **0.00 pp** | 1.10 pp | no |
| NQ/RTH 30min | 26.53% | 33.15% | **0.00 pp** | 6.62 pp | no |

Sharpe: maximum |ΔSharpe| against A1 is **0.0000** at every sweep point; against
A2 it reaches **0.259**, exceeding 0.10 at 8 of 16 sweep points.

### **K11 DOES NOT FIRE** — and the verdict inverts what item 119 anticipated

Both clauses fail, so the letter of item 119 gives "does not fire". But item 119
was written expecting A3 to be the improvement, and the arithmetic says
otherwise:

> **Reduction attributable to the reliability correction: 0.00 pp in all eight
> cells, and 0.0000 Sharpe at all sixteen sweep points.**
> **Reduction attributable to not applying the published moving average: 1.10 to
> 38.08 pp, and up to 0.259 Sharpe.**

Every point of the measured effect is A3 *not being* A2. Had K11 been stated
against A1 alone it would have fired trivially and unanimously.

### Against the Phase 1 ceiling

Item 120 asks that the null be attributable either to the correction failing
within its band or to the band being too small to matter. **Neither applies: the
band is empty.** The measured contribution of 0.00 pp equals the Phase 1 ceiling
of 0.00 pp exactly. The correction did not fail — it was never able to act. That
distinction is the session's finding, and it was available before any
classification was run, which is why item 120 required the band first.

---

## What this establishes

**The specification annihilates the correction.** Any affine adjustment to the
observable — shrinkage toward a mean, a scale change, a units change — is
removed exactly by within-window z-scoring. This is not specific to reliability
shrinkage: it applies to the whole class of linear proxy corrections applied
upstream of a normalising classifier. For a reliability correction to have any
reach at all, one of three things must change: the normalisation must not be
re-derived on the corrected series; the correction must be non-affine; or the
correction must enter the model rather than the observable, for instance as a
known measurement-error variance in a state-space observation equation. None of
those is the published specification.

**The unmotivated step is the costly one.** Item 117 objected to the 5-day
moving average as an unmotivated noise treatment. It is worse than unmotivated:
it reflips 13–20% of days and raises misclassification against a noise-robust
reference by 1.1 to 38.1 percentage points, in every cell, in sample and out.
Removing it is the only intervention in this session that changes anything.

**And the overlay does not work regardless.** The reference-kernel control
underperforms always-invested in every cell, so the regime rule's failure on this
holdout is not attributable to the quality of the volatility observable at all.

Three limits on the above. The misclassification reference is an HMM on a
realized kernel computed from the same window as the proxy, so their errors are
positively correlated and every empirical rate here is a lower bound — the same
caveat K8 carried. At the 30-minute horizon the classifier is at chance for every
arm, so those two cells carry no information about any treatment. And the
allocation figures are a single 2024–2026 holdout under a fixed rule; they are
reported as a measured consequence of the classification, not as a strategy
claim.

---

## Persisted artifacts

`results/` — `phase1_band.csv`, `phase1_affine_verification.csv`,
`phase1_summary.json`, `phase2_insample.csv`, `phase2_agreement.csv`,
`phase2_a1_a3_identity.csv`, `phase3_classification.csv` (first run, superseded),
`phase3_classification_fixed.csv`, `phase3_identity_fixed.csv`,
`phase3_fix_summary.json`, `phase3_allocation.csv`, `phase4_k11.csv` (first run,
superseded), `phase4_sharpe.csv`, `phase4_determination.json`,
`phase4_k11_final.csv`, `phase4_k11_final.json`.

`cache/` — `is_*.npz` (24 in-sample runs: state series, regime probabilities,
reference states, dates, the observable, λ and the in-sample mean),
`ho_*.npz` (24 first-run holdout series, superseded), `hofix_*.npz` (24 corrected
holdout runs at the right horizon), `alloc_*.npz` (20 overlay runs: signal
series, overlay return series, base return series, position series and the
validity mask).

`src/` — `common16.py` (paths, constants and the validated two-state Gaussian
HMM), `phase1_band.py`, `phase234.py`, `phase3_fix.py`.
