# Session 15 run log — confound checks

Date 2026-08-20. **The holdout was not read.** No new data acquired. No prior
artifact modified or deleted. Nothing committed to git (the tree is not a git
repository). No pre-registered threshold changed: items 107, 108 and 109 stand as
written, and the determinations below are reached against those thresholds
unaltered.

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

DECISIONS items 66–110 verified present by grep, 45 of 45, at lines 398 through
663. Items 111–114 appended once and verified persistent at lines 669, 677, 685,
692, per item 77. DECISIONS.md grew from 48,676 bytes / 665 lines to 50,681 bytes
/ 693 lines.

## Holdout read count

Unchanged at **five**: S09 Phase 6, S11 Phase 1, S11 Phases 8–9, S13 Phase 2,
S14 Phase 1. Every input to this session is a pre-2024 panel or a persisted
artifact from S09, S10, S11 or S14. No phase required a holdout read, so the
report-and-halt condition was not triggered.

## Wall clock per phase

| phase | wall clock | source |
|---|---|---|
| 0 — verification, append, gate, directories | ~3 min | interactive |
| 1 — K10 lag-selection decomposition, common window, nugget sensitivity | 0.4 s | `s15_summary.json` |
| 2 — K9 conditioning, error correlations, three Σ_E scalings | 0.5 s | `s15_summary.json` |
| 3 — trend against conditioning, 3 × 9,999 WCB plus 3 × 121-point inversion | 40.6 s | `s15_summary.json` |
| 4 — report, spec update, runlog | ~12 min | interactive |

Total compute 41.5 s. Total session wall clock including code authoring and
inspection, roughly 25 minutes, inside the 15–30 minute expectation. Phase 3
dominated, almost all of it the interval-by-inversion loop: three specifications
× 121 grid points × 1,499 replications, with a cluster-robust variance recomputed
inside every replication.

## Seeds and their derivation

| use | seed | derivation |
|---|---|---|
| Phase 3, WCB, year-only | 20260837 | `PCG64(MASTER_WCB + n_regressors)`, MASTER_WCB = 20260836 |
| Phase 3, WCB, year + log(cond) | 20260838 | same rule |
| Phase 3, WCB, year + log(cond) + A/c | 20260839 | same rule |
| Phase 3, interval by inversion | 20261336 | `PCG64(MASTER_WCB + 500)`, reset per grid point so the inversion is deterministic in β₀ |

All 3 × 9,999 bootstrap t-statistics are persisted in `cache/trend_wcb.npz` with
the master seed and the replication count. Phases 1 and 2 draw no random numbers:
the K10 decomposition is deterministic log-log arithmetic on the moment curves,
and the K9 checks are closed-form matrix algebra and sample correlations.

No synthetic arm was generated in this session, so the five-seed dispersion
requirement binds nowhere; the synthetic evidence quoted is S13's and S14's,
already carrying its own dispersion.

## Constants and their sources

| constant | value | source |
|---|---|---|
| K10 lags | 1 to 40 | S14 Phase 3 |
| K10 q values | 0.5, 1.0, 2.0 | DECISIONS item 109 |
| K10 nugget | 2·Var(ε), Var(ε) = (1 − λ)·Var(log RV_M) | DECISIONS item 109 |
| K10 C_q | 2^{q/2}·Γ((q+1)/2)/√π | E\|Z\|^q for standard normal |
| K10 survival test | corrected S(Δ) > 1e-12 | S14 Phase 3, unchanged |
| nugget sensitivity scales | 0.25, 0.50, 0.75, 1.00 | this session |
| K10 threshold | ΔH below 0.02 | DECISIONS item 109, unchanged |
| λ per cell | 0.827, 0.940, 0.840, 0.931 | S09 `phase3_sizing_params.csv`, extended range |
| v from the fitted scaling | 0.171, 0.054, 0.151, 0.051 | S11 `phase7_proxy_fits.csv`, A·M^b at the five-minute M |
| Σ_E structure | v·[[1,1/5,1/22],[1/5,1/5,1/22],[1/22,1/22,1/22]] | S14 Phase 2, derived from the shared-day structure |
| IV stand-in | flat-top realized kernel at the finest grid, BNHLS (2009) bandwidth | S02 `proxies_robust` |
| K9 threshold | daily coefficient within 10% relative | DECISIONS item 108, unchanged |
| year-fit diagnostics | c, A, A/c, condition number, RMSE per sub-fit | S14 `phase5_year_fits.csv` |
| bootstrap replications | 9,999 test, 1,499 per inversion grid point | session instruction |
| Rademacher floor at G = 8 | 2⁻⁷ = 0.0078 | 2⁸ weight vectors, sign-symmetric statistic |

## Derivations, assumptions and validity boundaries

- **K10 decomposition.** No new derivation. The identity is arithmetic: the total
  shift H_corrected(subset) − H_naive(all) equals [H_naive(subset) −
  H_naive(all)] + [H_corrected(subset) − H_naive(subset)], the first term being
  lag selection and the second nugget subtraction, with naive-on-subset reported
  as its own column per the stop condition rather than folded into either. The
  common-window comparison holds the lag set fixed and so carries no selection at
  all; it is the conservative figure.
- **K9 classical-error test.** The classical fraction is defined as 1 − ρ², the
  share of proxy-error variance orthogonal to the level, which is exact for a
  linear projection and is the sensitivity item 112 proposes. Its assumption is
  that the level-correlated component is the whole of the non-classical part; a
  non-linear dependence would not be captured, and that limit is stated. The
  measured-error scaling assumes the RV-minus-kernel difference bounds the proxy
  error from below, which holds because both are computed on the same window and
  their errors are positively correlated. **The two scalings therefore bracket
  the truth, and the bracket spans the threshold** — that is the finding, not a
  gap in the method.
- **Phase 3.** Wild cluster bootstrap with the null imposed (Cameron, Gelbach and
  Miller 2008). Validity is asymptotic in the number of clusters; at G = 8 the
  attainable floor is 2⁻⁷ and the test is saturated. Reported regardless of
  outcome.

## Code path

Imported unmodified: the S10 `common` module's `cell_windows`, `subbars`,
`logrv_matrix`, `var_cols` and `GRID_EXT`, and `proxies_robust.{p1_rv,
p3_kernel_flattop, kernel_H}` from S02. The HAR design and the log-log moment
regression are re-executed here with the same formulas S14 used, in order to add
the columns S14 did not report; nothing was reimplemented that could have been
imported, so the report-and-halt condition was not triggered.

## Fit diagnostics

Condition number, smallest eigenvalue and RMSE are reported for every fit as the
stop condition requires: Phase 1 carries RMSE for all three log-log fits and both
common-window fits in `phase1_k10_decomposition.csv`; Phase 2 carries condition
number and minimum eigenvalue for Σ_XX and for Σ_XX − Σ_E under all three
scalings, plus the HAR RMSE, in `phase2_k9_check.csv`; Phase 3 carries
cluster-robust and OLS standard errors, the variance inflation factor on year, the
within R² and the RMSE in `phase3_trend_control.csv`.

## Deviations and corrections

1. **One dead-code slice, caught before any result.** A leftover `if False`
   branch in the Phase 2 correlation call sliced the error series but not the
   regressor, raising a broadcast error on the first run. Fixed and rerun; Phase 1
   had already completed and reproduced identically.
2. **A third Σ_E scaling was added after seeing the first two.** Item 112 proposes
   scaling by the classical fraction, which the first run showed leaves the
   determination intact. The measured-error-variance scaling was added because the
   same run showed v exceeding the measurable disagreement by 2.4 to 11 times,
   which is a larger problem than the level correlation and is the one that flips
   the determination. Disclosed as a post-hoc addition; it changes no threshold
   and both scalings are reported side by side with the naive column.

## Persistence

Every reported figure regenerates from a persisted artifact: the raw q-th absolute
moment and implied S(Δ) at every lag for every cell and q in
`cache/k10_moments.npz` with the lag vector and the common window; the measured
proxy-error series, both log series, Σ_XX, the naive coefficient vector and both v
estimates per cell in `cache/k9check_*.npz`; and all 3 × 9,999 bootstrap
t-statistics in `cache/trend_wcb.npz`.

## Verification

File verification paired `wc -c` with `wc -l` per item 78. No full-tree hashing or
integrity scanning.

## Outcome

**K10 SURVIVES.** Lag selection contributes at most −0.0053 with a negative share;
on a fixed lag window of 2 to 40 the shift is 0.027 to 0.213, above threshold in
every cell at every q. Magnitude flagged as non-linearly nugget-sensitive.

**K9 WITHDRAWN as indeterminate.** The daily shift is 4.8% to 7.2% under the
measured error variance and 19% to 116% under v from A·M^b, spanning the 10%
threshold. The two scalings bracket the truth and the bracket does not resolve.

**The trend SURVIVES at −0.0105 per year**, a 78% reduction from −0.0469 once fit
conditioning is controlled, VIF 1.27, interval [−0.0211, −0.0020] at eight
clusters with the saturation caveat.

Per item 114, no further measurement session follows. The next artifact is the
paper.
