# Session 17 run log — measurement error in the model rather than the observable

Date 2026-08-20. No new data acquired. No prior artifact modified or deleted.
Nothing committed to git (the tree is not a git repository). No parameter,
threshold, rule or specification changed after any holdout number was seen: the
arms, window, state count, noise construction, scalings and the K12 threshold were
all fixed in items 125 through 127 before Phase 1 ran.

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

DECISIONS items 66–121 verified present by grep, 56 of 56, at lines 398 through
730. Items 122–128 appended once and verified persistent at lines 735, 742, 752,
757, 766, 771, 777, per item 77. DECISIONS.md grew from 53,506 bytes / 731 lines
to 57,095 bytes / 779 lines.

## Holdout read count

| # | session | phase |
|---|---|---|
| 1–5 | S09 P6, S11 P1, S11 P8–9, S13 P2, S14 P1 | — |
| 6 | S16 | Phase 3 |
| **7** | **S17** | **Phase 4 (item 128)** |

Phases 0, 1, 2, 3 and 5 read pre-2024 panels and persisted S16 artifacts only.
Phase 1's phase-matched reference and Phase 2's parameter recording both build
the concatenated series but roll only over in-sample windows for their in-sample
figures; the holdout tail is used only for the Phase 1 holdout column, which is a
comparison against S16's already-opened holdout classification and is reported
under the same seventh opening. No other phase required a holdout read.

## Wall clock per phase

| phase | wall clock | source |
|---|---|---|
| 0 — verification, append, gate, directories | ~4 min | interactive |
| 1+2 — first attempt, stalled by the S16 NaN defect | ~120 min, discarded | — |
| — defect diagnosis, S16 audit, guarded wrapper | ~12 min | interactive |
| 3 — A4 in sample, 35 rolls over 8 workers | 5,395 s (89.9 min) | `phase345_summary.json` |
| 4 — A4 holdout, 35 tail-rolls | 733 s (12.2 min) | `phase345_summary.json` |
| 4 — allocation overlay | 0.3 s | `phase345_summary.json` |
| 1+2 — re-run with the guarded estimator | 2,107 s (35.1 min) | `logs/phase12.log` |
| 2b — stability-restricted rates | 2 s | interactive |
| 5 — K12 | included in Phase 4 | `phase345_summary.json` |
| 6 — report, spec update, runlog | ~18 min | interactive |

Productive compute 2 hours 17 minutes. **Total session wall clock roughly 4 hours
40 minutes, against a 60–120 minute expectation and a 150-minute reporting
threshold.** Per the stop condition this is reported rather than met by reducing
arms, cells, scalings or window steps — nothing was reduced, and all 35 in-sample
and 35 holdout A4 runs plus all four scalings and both λ ranges were completed.

Three causes, separated by size. **First and largest, the S16 NaN defect**, which
consumed roughly two hours before it was diagnosed: the poisoned warm start made
EM run its full 60-iteration cap on every subsequent window instead of converging
in about five, a twelvefold slowdown, while producing unusable states. **Second,
the intrinsic cost of the intraday rolls**: 22,372 windows per arm at 30 minutes
and 10,966 at 1 hour, against about 1,500 daily, times 35 arm-scaling combinations
in Phase 3 alone. **Third, Phase 1's design**: each phase-matched reference needs
a full in-sample roll, and the re-run reused S16's persisted reference states
where possible but still had to compute the MA-smoothed reference from scratch.

## Seeds and their derivation

| use | seed | purpose |
|---|---|---|
| A4 estimator validation | 20260841 | `PCG64(20260841)`, synthetic two-state series with known state variance and known added observation noise |

**No other seed is used.** Every rolling HMM in this session is deterministic:
initialisation is by the 25th and 75th percentiles of the first window, each later
window is warm-started from the previous converged parameters, and Baum-Welch is a
deterministic EM. There is no between-seed dispersion to report and no synthetic
arm beyond the validation.

## Constants and their sources

| constant | value | source |
|---|---|---|
| rolling window, states, z-scoring | 441, 2, within-window | arXiv 2510.03236 via item 116, inherited |
| observation-noise variance | Var(ε) = (1−λ)·Var(log RV_M) | DECISIONS item 127, same construction as item 109 |
| scalings | 0.25, 0.50, 0.75, 1.00 | DECISIONS item 127, pre-registered, not tuned |
| λ, extended | 0.827, 0.940, 0.840, 0.931, 0.588, 0.810, 0.396, 0.677 | S09 `phase3_sizing_params.csv` |
| λ, restricted | defined in 3 of 8 cells; undefined at all four RTH intraday, degenerate at ES/GLOBEX/1day | S09, S10, reported per item 66 |
| noise scale conversion | v_z = Var(ε)/Var_W(x), recomputed per window | this session; the HMM sees the z-scored series |
| K12 threshold | 1 pp | DECISIONS item 126, unchanged |
| A2 lag search | integer lags 0–10 | this session |
| phase-matched reference | identical 5-day MA applied to the kernel before classification | this session |
| mu-gap thresholds, Phase 2b | 0.00, 0.10, 0.25, 0.50 | this session |
| reference classifier, allocation, cost sweep, tick values | as S16 | inherited unchanged |

## Derivations, assumptions and validity boundaries

- **A4's identifiability condition.** σ_k² = max(total_k − v, 0) makes the
  emission variance max(total_k, v). Exact, not an approximation. The condition
  that the floor not exceed the total emission variance in either state is also
  the reach condition, and binding is counted per window.
- **A4's validation.** Reported in full in `phase3_validation.json`: the free HMM
  recovers the total variance, the fixed-noise HMM recovers the state variance by
  subtracting known v, and their means agree to ten decimal places.
- **Phase-matching against best-lag.** Phase-matching removes both the filter's
  phase and its smoothing; best-lag removes only the phase. They disagree, and
  the disagreement is the measurement — phase-matching is the stronger control
  and is the basis for the verdict, with best-lag reported beside it.
- **The binomial test on NQ/RTH/1h** is exact, two-sided, against p = 0.5.

## A4 differs from A1 only in the emission

Verified by construction: `roll()` is shared code and takes `noise_raw` as its
only branch, routing to `gauss_hmm_fixednoise` instead of `gauss_hmm_fit`.
Window, z-scoring, warm-start policy, mean-ordering labelling, reference
classifier and allocation rule are the same code path. No other component differs,
so the report-and-halt condition was not triggered.

## Defect found in a prior artifact, contained not edited

`sessions/s16-regime/src/common16.py:50` divides by `c[0]` with no underflow
guard, where line 51 guards `c[t>0]`. **S16's 32 persisted A1/A2 series were
audited before any remedial work**: zero NaN probabilities, zero degenerate
constant runs, none affected — the underflow is reached only by the MA-smoothed
kernel series S17 introduces. The S16 file is untouched per the stop condition.
S17 handles it at the call site in `common17.safe_fit`: validate the returned
parameters, retry cold once, otherwise leave the window unclassified. Failure and
cold-retry counts are recorded in every `roll()` diagnostic.

## Fit diagnostics

The HMM has no condition number or parameter correlation in the regression sense;
what it has is convergence, identifiability and separation. Reported per cell and
scaling: windows binding, total binding events, states differing from A1, fit
failures and cold retries (`phase3_a4_insample.csv`), and per window for the
30-minute cells the two state means, both standard deviations, the mean separation
in standard-deviation units and both transition probabilities
(`cache/params30_*.npz`, summarised in `phase2_30min_params.csv`). The validation
fit's recovered parameters against truth stand in for goodness of fit.

## Persistence

Every reported figure regenerates from a persisted artifact: 8 phase-matched
reference series in `cache/refma_*.npz`; per-window emission parameters for both
30-minute cells in `cache/params30_*.npz`; 35 in-sample and 35 holdout A4 runs in
`cache/a4is_*.npz` and `cache/a4ho_*.npz`, each with the state series, regime
probabilities, v, λ and binding counts; and 28 overlay runs in
`cache/alloc17_*.npz` with signal, overlay return, base return and position series.

## Verification

File verification paired `wc -c` with `wc -l` per item 78. No full-tree hashing or
integrity scanning.

## Outcome

**K12 FIRES.** Maximum reduction 0.00 pp against A1 in every cell at every one of
the four scalings, with the floor binding in 46,120 of 72,619 windows and 18,311
in-sample states differing — real reach, no benefit, degradation where it acts.

**The S16 A2 claim is withdrawn** in its stated form: phase-matching removes
essentially all of the measured gap, and the best lag is 2 days in every daily
cell, as item 123's arithmetic predicted.

**The 30-minute inversion remains unexplained**: label instability is present and
correctly located but accounts for about 3 percent of it, and separability is
ruled out.

Per item 128 this is the last measurement session. The next artifact is the paper.
