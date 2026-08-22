# Session 16 run log — regime classification under measured reliability

Date 2026-08-20. No new data acquired. No prior artifact modified or deleted.
Nothing committed to git (the tree is not a git repository). No parameter,
threshold, rule or specification changed after any holdout number was seen: the
three arms, the window, the state count, the allocation rule and the K11
thresholds were all fixed in items 116 through 120 before Phase 1 ran.

## Environment

| field | value |
|---|---|
| interpreter | `~/venvs/obs-space-vol/bin/python` |
| realpath | `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13` |
| Python | 3.13.13 |
| numpy | 2.5.2 (gate requires exactly this) |
| pandas | 3.0.5 (gate requires exactly this) |
| under a synced path | no |
| gate | PASS, Phase 0, before any work |
| hmmlearn | NOT installed; the HMM is new code written and validated here |

DECISIONS items 66–114 verified present by grep, 49 of 49, at lines 398 through
692. Items 115–121 appended once and verified persistent at lines 697, 702, 709,
715, 720, 726, 730, per item 77. DECISIONS.md grew from 50,681 bytes / 693 lines
to 53,506 bytes / 731 lines.

## Holdout read count

| # | session | phase |
|---|---|---|
| 1 | S09 | Phase 6 |
| 2 | S11 | Phase 1 |
| 3 | S11 | Phases 8–9 |
| 4 | S13 | Phase 2 |
| 5 | S14 | Phase 1 |
| **6** | **S16** | **Phase 3 (item 121)** |

Phases 0, 1, 2 and 4 read pre-2024 panels and persisted artifacts only. Phase 3
and its corrected rerun are the only holdout reads. No other phase required one,
so the report-and-halt condition was not triggered.

## Wall clock per phase

| phase | wall clock | source |
|---|---|---|
| 0 — verification, append, gate, directories | ~3 min | interactive |
| 1 — recoverable band, affine verification | 0.5 s | `phase1_summary.json` |
| — HMM validation and benchmark | ~1 min | interactive |
| 2 — in-sample classification, 24 tasks over 8 workers | 1,963 s (32.7 min) | `phase4_determination.json` |
| 3 — holdout, first run (superseded) | 2,740 s (45.7 min) | `phase4_determination.json` |
| 3 — allocation overlay | 0.4 s | `phase4_determination.json` |
| 3 — holdout, corrected at the right horizon | 722 s (12.0 min) | `phase3_fix_summary.json` |
| 4 — K11, recomputed on the corrected holdout | 1 s | `phase4_k11_final.json` |
| 5 — report, spec update, runlog | ~15 min | interactive |

Total compute 90 min 28 s. **Total session wall clock roughly 145 minutes,
against a 30–60 minute expectation and a 90-minute reporting threshold.** Per the
stop condition the overrun is reported rather than met by reducing arms, cells or
window steps: nothing was reduced. Two causes, in order of size. First, the
rolling HMM refits one window at a time and the intraday cells are large —
22,372 windows per arm at 30 minutes and 10,966 at 1 hour, against about 1,500
daily — so in-sample alone is 24 tasks totalling roughly 152,000 window-fits at
14 ms warm-started. Eight-way process parallelism brought that to 33 minutes of
wall clock; the critical path is a single 30-minute cell. The first holdout run
cost 46 minutes because it re-rolled each cell's full history from the first
window rather than only the holdout tail. Second, the horizon defect below forced
a 12-minute rerun of Phase 3 — which, by refitting only windows ending in the
holdout, took a quarter of the time the first run did and is the construction the
first run should have used.

## Seeds and their derivation

| use | seed | purpose |
|---|---|---|
| HMM validation | 20260840 | `PCG64(20260840)`, synthetic two-state series for the pre-use validation only |

**No other seed is used anywhere in this session.** The rolling HMM is
deterministic: initialisation is by the 25th and 75th percentiles of the first
window, every subsequent window is warm-started from the previous window's
converged parameters, and Baum-Welch is a deterministic EM. There is therefore no
between-seed dispersion to report, and no synthetic arm was generated.

## Constants and their sources

| constant | value | source |
|---|---|---|
| rolling window | 441 observations, stepped 1 | **arXiv 2510.03236**, Blake, Gandhi and Jakkula, via DECISIONS item 116 |
| regimes | 2, Gaussian HMM | **arXiv 2510.03236**, item 116 |
| observable normalisation | z-scored within each window | **arXiv 2510.03236**, item 116 |
| arm A2 smoothing | 5-day moving average | **arXiv 2510.03236**, item 116; objected to in item 117 |
| RV sampling | five-minute equivalent per cell | S05 grid, via S09 FIVEMIN |
| arm A3 shrinkage | (1−λ)·μ_insample + λ·log RV | DECISIONS item 118 |
| λ, extended range | 0.827, 0.940, 0.840, 0.931, 0.588, 0.810, 0.396, 0.677 | S09 `phase3_sizing_params.csv` |
| λ, restricted range | reported alongside per item 66; undefined at all four RTH intraday cells, degenerate at ES/GLOBEX/1day | S09, S10 |
| reference classification | same HMM on the flat-top realized kernel at the finest grid, BNHLS (2009) bandwidth | S02 `proxies_robust` |
| state labelling | state 0 = low volatility, by mean ordering | this session, applied identically to all arms |
| allocation | full exposure in the low state, cash in the high state, one-day execution lag | DECISIONS item 116, item 119 |
| volatility-targeted book | S09 R3 holdout positions, extended range | S09 `ho_pos_*_extended_R3.npz` |
| cost sweep | 0.5, 1.0, 2.0, 4.0 ticks per leg | DECISIONS item 69 |
| tick values | ES $12.50, NQ $5.00 | SCOPE section 4 |
| K11 thresholds | 1 pp misclassification, 0.10 Sharpe | DECISIONS item 119, unchanged |

## Derivations, assumptions and validity boundaries

- **The affine annihilation (Phase 1).** Exact, not an approximation, and
  unconditional in λ > 0: within-window z-scoring is invariant to any affine
  transform of the observable. Its only assumption is that the normalisation is
  re-derived on the transformed series, which is what item 116 specifies. There is
  no validity boundary because there is no expansion.
- **The analytic misclassification rate.** arccos(√λ)/π, carried over from S14
  Phase 1, exact under joint normality with median thresholds. It is a *pointwise*
  rate and the HMM is not a pointwise classifier, so it is reported as a reference
  rather than as a prediction for the HMM, and the empirical figure is separately
  a lower bound because reference and proxy share a window.
- **The fixed-threshold band.** A labelled diagnostic, not a fourth arm: holding
  the threshold on the raw scale changes a component and item 118 fixes every
  component but the observable.

## The HMM, written and validated

hmmlearn is not in `requirements.lock` and the project holds no prior HMM, so
nothing was reimplemented that could have been imported. `common16.gauss_hmm_fit`
is a standard Baum-Welch EM for a two-state Gaussian HMM with scaled
forward-backward recursions, warm-started across rolling windows. Validated
before use on a synthetic two-state series of 2,000 observations: recovered
μ = (−0.573, 0.913) against a true (−0.6, 0.9), σ = (0.496, 0.807) against
(0.5, 0.8), transition matrix to within 0.006 of truth, and **98.3% state
accuracy**. Cold fit 33 ms, warm-started 14 ms at a 441-observation window.

## Arms differ only in the observable

Verified by construction: `observables()` returns the three series and every
downstream step — window, z-scoring, state count, EM tolerance and iteration cap,
warm-start policy, state labelling, reference classifier and allocation rule — is
shared code operating on whichever series it is handed. No component differs
between arms, so the report-and-halt condition was not triggered.

## Defect found and corrected, disclosed

The first Phase 3 run built the holdout portion of every cell through S11's
`ho_series`, which is the S07 `series()` body at wlen = None and therefore yields
**daily windows only**. The four 1day cells were correct; the 1h and 30min cells
had 621 daily windows appended to their intraday in-sample series and their
holdout figures were meaningless. Corrected by rebuilding through
`phase6_holdout.wins` at each cell's own horizon — the wlen-aware path S11 Phase 1
used — refitting only windows ending in the holdout and warm-starting from a cold
fit on the last fully in-sample window, so every holdout window still sees a full
441-observation history beginning in sample. Holdout window counts go from a
uniform 621 to 641, 621, 3,726 and 7,452. The 1day classification figures and the
entire allocation overlay are unchanged and were re-verified as such. Both runs
are retained; `phase3_classification.csv` and `phase4_k11.csv` are marked
superseded and `phase3_classification_fixed.csv` and `phase4_k11_final.csv`
supersede them.

## Fit diagnostics

The HMM is not a least-squares fit and has no condition number or parameter
correlation in the regression sense; what it has is convergence and
identifiability, reported as the non-convergence count per cell and arm (zero
throughout) and the state-mean separation implied by `share_high`. The one
regression-like object in the session is the Phase 1 affine identity, reported as
a maximum absolute deviation (6.3×10⁻¹⁵) rather than an RMSE because it is an
exact identity. The validation fit's recovered parameters against truth are given
above and stand in for goodness of fit.

## Persistence

Every reported figure regenerates from a persisted artifact: 24 in-sample runs in
`cache/is_*.npz` with state series, regime probabilities, reference states, dates,
the observable, λ and the in-sample mean; 24 corrected holdout runs in
`cache/hofix_*.npz`; the 24 superseded first-run holdout series retained in
`cache/ho_*.npz`; and 20 allocation runs in `cache/alloc_*.npz` with the signal
series, overlay return series, base return series, position series and validity
mask.

## Verification

File verification paired `wc -c` with `wc -l` per item 78. No full-tree hashing or
integrity scanning.

## Outcome

**K11 DOES NOT FIRE**, and the verdict inverts what item 119 anticipated. The
reduction attributable to the reliability correction is **0.00 pp in all eight
cells and 0.0000 Sharpe at all sixteen sweep points**, equal to the Phase 1
ceiling exactly. The reduction attributable to not applying the published moving
average is 1.10 to 38.08 pp and up to 0.259 Sharpe. Had K11 been stated against A1
alone it would have fired trivially.

The correction did not fail — it was never able to act, because within-window
z-scoring annihilates any affine transform of the observable exactly.
