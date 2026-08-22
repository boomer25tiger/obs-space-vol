# Session 10 run log — exponent validity audit and mechanism test

Date 2026-08-19. No new data acquired, no holdout opened, no prior artifact
modified or deleted, nothing committed to git (the tree is not a git repository).

## Environment

| field | value |
|---|---|
| interpreter | `~/venvs/obs-space-vol/bin/python` |
| realpath | `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13` |
| Python | 3.13.13 |
| numpy | 2.5.2 (gate requires exactly this) |
| pandas | 3.0.5 (gate requires exactly this) |
| under ~/Desktop, ~/Documents or a synced path | no |
| gate | PASS, run at Phase 0 before any work |

DECISIONS items 66–79 verified present by grep at lines 398, 405, 413, 419, 424,
433, 437, 442, 445, 454, 457, 466, 469, 474 (14 of 14). Items 80–85 appended once
and verified persistent by grep at lines 485, 490, 497, 502, 510, 515, per item
77. DECISIONS.md grew from 34,995 bytes / 481 lines to 37,816 bytes / 519 lines.

## Wall clock per phase

| phase | wall clock | source |
|---|---|---|
| 0 — item verification, append, gate, directories | ~3 min | interactive |
| 1 — bootstrap on c, A, b: futures 38.3 s, SPY 2.9 s | 41 s | `phase12_summary.json` |
| 2 — grid sensitivity, identifiability, tightened screen | (in the same run) | `phase12_summary.json` |
| 3 — pooling, 192 sub-fits | 4.3 s | `phase3_summary.json` |
| 4 — arm A5, 140 synthetic panels | 37.6 s | `phase4_summary.json` |
| 5 — gate | instant | `phase4_summary.json` |
| 6 — arm A6, 100 synthetic panels | 52.1 s | `phase6_determination.json` |
| 7 — RS-up diagnosis | 1 s | `logs/phase7.log` |
| 7b — floor-defect reach across the S09 signal set | 4.0 s | `phase7b_summary.json` |
| 8 — report, spec update, runlog | ~15 min | interactive |

Total compute 2 min 20 s. Total session wall clock including code authoring and
inspection, roughly 75 minutes, below the 90–150 minute expectation. The expected
bottlenecks (Phases 1, 4 and 6) did not materialise as such: the fitted model has
three parameters on 5–15 points, so 36,000 bootstrap fits cost 41 seconds, and
the synthetic panels are at most 1953 × 1379.

## Seeds and their derivation

| use | master | derivation | count |
|---|---|---|---|
| Phase 1 bootstrap | 20260820 | `SeedSequence(20260820).generate_state(64)`, one per cell in `CELLS` order then SPY ARCX, XNAS | 18 used |
| Phase 4, arm A5 | 20260821 | `SeedSequence(20260821).spawn(140)`, consumed in (geom, df, subarm, seed index) order | 140 |
| Phase 6, arm A6 | 20260822 | `SeedSequence(20260822).spawn(...)`, consumed in (geom, H, seed index) order then the sensitivity leg | 100 |

Every individual seed is logged: Phase 1 in `phase12_summary.json` under
`seeds_used` and in each `cache/boot_*.npz`; Phase 4 in `phase4_seeds.csv` and
`phase4_a5_raw.csv`; Phase 6 in `phase6_a6_raw.csv`. Between-seed dispersion is
reported as `b_sd` on every synthetic row and never fewer than 5 seeds per
setting.

## Constants and their sources

| constant | value | source |
|---|---|---|
| extended grid | per (geom, horizon) | S08 `phase234.py` GRID, via S09 `phase34_sizing.py` |
| restricted grid | per (geom, horizon) | the original S05 grid, via S09 GRID_S05 |
| SPY grid | 5 … 23400, 16 points | S07 `phase6_spy_exponent.py` GRID |
| DIMS | GLOBEX (1953, 1380), RTH (1901, 390) | S05E `run5e.py` |
| VAR_LOG_IV | 1.02 | S05E, DECISIONS item 36 intercept |
| tail index range | 2.95 to 3.67 | S04, via DECISIONS item 83 |
| observed b range | −1.00 to −0.41 | S07/S08 headline, via DECISIONS item 81 |
| σ_w (A6 within-window scale) | √1.02 = 1.0100, sensitivity 0.5× and 2× | **chosen here, measured nowhere** |
| tightened screen | ≥ 2×3 grid points, \|b\| > 0.01, plus A > 0 and b < 0 | this session |
| bootstrap resamples | 2,000 | session instruction |
| minimum windows for a sub-fit | 60 | this session |

## Code path

Every measurement runs through functions imported unmodified, not
reimplementations:

- `common.cell_windows` is the S08/S09 λ code path, verified in S09 Phase 3 to
  reproduce S08 `phase4_fits.csv` at max\|Δc\| = 0 and max\|Δb\| = 5.55e-17.
- `common.fitf` is S05E `fit_free` / S07 `fitf`, unchanged.
- `common.spy_logrv_tick` is the S07 Phase 6 traded-tick construction, unchanged.
- Both synthetic arms build a return panel and then pass it through the same
  `common.logrv_matrix` / `var_cols` / `fitf` the real cells use.
- Phase 7 imports S09 `phase5_signals` and `phase6_holdout` directly and runs
  both on the same in-sample panel.
- The fBm sampler is S01 `fbm.CirculantEmbedding` / `fgn_acf`. Circulant
  eigenvalue diagnostics are recorded per run in `phase6_a6_raw.csv`
  (`emb_neg_eig`, `emb_min_eig`).

No arm required reimplementation, so the report-and-halt condition was not
triggered.

## Fit diagnostics

Condition number of the Jacobian at the optimum, asymptotic parameter
correlation from the covariance, bootstrap parameter correlation, and RMSE are
recorded for every fit: real cells in `phase1_bootstrap.csv` and
`phase1_corr.csv`, sub-fits in `phase3_subfits.csv`, synthetic runs in
`phase4_a5_raw.csv` and `phase6_a6_raw.csv`.

## Deviations and corrections

1. **Phase 3 degeneracy criterion tightened mid-phase, disclosed.** The first run
   used the S08 screen alone and admitted 16 volatility-tercile fits with
   b ≈ −1e-4 and condition numbers above 10¹⁰, producing a nonsense pooled
   share of −1.71. The criterion was tightened to add |b| > 0.01 and condition
   number < 10⁸ and the phase rerun. All 48 tercile fits are then degenerate and
   the tercile share is reported as undefined rather than as a number. The
   within-year leg is unaffected either way.
2. **Two pandas defects in Phase 4's summary, fixed, measurement unaffected.**
   `Series.map` against a non-unique index, and a `pivot_table` whose NaN `nu`
   index level cross-multiplied the rows. Both were in the aggregation after the
   simulation; the per-setting means printed identically before and after.
3. **Phase 7 import path was one directory level short**, fixed by importing
   `ROOT` from `common` rather than recomputing it.
4. **Phase 7b added.** Phase 7 as specified diagnoses one cell. Once the defect
   was identified as a floor substitution rather than an alignment error, its
   reach across the whole S09 signal set became the material question, so a
   96-row audit was added. It reads only the pre-2024 panel.

## Persistence

All 36,000 Phase 1 bootstrap draws are in `cache/boot_*.npz` with the grid, the
observed variance vector, the point estimate and the seed. All 240 synthetic runs
persist their log-RV matrix, grid, log-IV path, seed and settings; the full
minute-level return panel is persisted for seed index 0 of every setting
(14 A5 panels, 20 A6 panels), and every other panel regenerates exactly from its
logged seed through `make_a5` / `make_a6`. Every figure in the report regenerates
from these artifacts.

## Verification

File verification paired `wc -c` with `wc -l` per item 78. No full-tree hashing
or integrity scanning was performed.

## Outcome

**Determination A**: the exponent anomaly stands with uncertainty quantified —
reference outside the 95% interval on b in 18 of 18 cells, grid sensitivity
bounded below the gap, pooling accounting for a mean 36.0%, and neither mechanism
arm reproducing it. Quoted from the 14 cells passing the tightened screen,
b runs −0.443 to −0.974 against references of −1.126 to −1.210.

**RS-up**: explained by a defect, but a floor-substitution defect rather than an
alignment defect, at `phase5_signals.py:104` and `phase6_holdout.py:330`.
