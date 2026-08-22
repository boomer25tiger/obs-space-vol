# Session 9 run log — application, sizing consequence, signal status, holdout

Date 2026-08-19. This is the S09 RERUN, executed after the aborted S09 run of the
same day (item 74) and the S09-PRE environment rebuild (items 76, 79).

## Environment

Interpreter `~/venvs/obs-space-vol/bin/python`, realpath
`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13`, Python
3.13.13, numpy 2.5.2, pandas 3.0.5. Outside every synced location. Neither
`.venv` nor `.venv-broken-20260819` in the project directory was used; neither
was modified or deleted.

The interpreter/import gate was run twice, as required: once at session start
before any phase, and again inside `phase6_holdout.py` immediately before the
holdout was extracted. Both PASS, both logged (`logs/phase6.log` line 1 carries
the second one).

## Wall clock per phase

| phase | wall clock | source |
|---|---|---|
| 0 — DECISIONS verification, items 78-79 append, directories, gate | ~4 min | interactive |
| 1 — placebo scheme S-D, full MCS | 709.5 s (11m50s) | `phase12_summary.json` |
| 2 — seed stability, 20 seeds over 19 flipped cells | 123.4 s | `phase12_summary.json` |
| 3 — five-minute-equivalent table, both ranges | 3.6 s | `phase34_meta.json` |
| 4 — sizing on simulated paths, 2 arms × 5 seeds | 7.8 s | `phase34_meta.json` |
| 5 — signal status, 9 candidates | 13 s | `logs/phase5.log` |
| 6 — HOLDOUT: extract 2.7 s, engineer 54.8 s, panels + sizing + candidates | 107.8 s | `phase6_summary.json` |
| 7 — K3 determination + in-sample sizing baseline | 4 s | `logs/phase7.log` |
| 8 — report, spec update, runlog | ~15 min | interactive |

Total compute 16 min 10 s. Total session wall clock including code authoring and
inspection between phases, roughly 100 minutes, inside the 90-150 minute
expectation and well inside the 180-minute stop condition. Phase 1 dominated, as
predicted; Phase 4 did not, because the simulated panels are small relative to
the 10,000-resample MCS.

## Seeds

| use | master | derivation |
|---|---|---|
| Phase 1 MCS per cell | 20260819 | `np.random.SeedSequence([20260819, ci, 100+si])` |
| Phase 2 seed stability | 20260820 | 20 independent draws |
| Phase 4 simulation | 20260819 | `SeedSequence(20260819).generate_state(5)` → 3280325159, 10724713, 3527105160, 1168436609, 2339113406 |

Between-seed dispersion is reported in `phase4_sizing_agg.csv` as `te_sd` and
`turnover_sd` on every row, and in `phase4_sizing_raw.csv` per seed.

## Holdout discipline

The holdout opened exactly once, in Phase 6. Phases 1 through 5 read only the
S06R/S07/S08 pre-2024 artifacts. Phase 6 streamed the DBN from UTC 2023-12-31 so
that the first holdout trade date is complete, then kept only trade dates in
[2024-01-01, 2026-08-14]; the 2023-12-31 bars are in-sample data used solely to
close the boundary session and enter no holdout statistic.

No parameter, threshold, rule or specification was changed after any holdout
number was seen. The reliability parameters, both ranges, were frozen in Phase 3
and read from `phase3_sizing_params.csv` by Phases 6 and 7 without modification.

## Deviations and corrections, all before the holdout opened

1. **Phase 4 second arm, disclosed.** The pre-registered path is the S05E
   generator. Its A2 arm draws log IV i.i.d., which makes the shrinkage
   comparison degenerate (nothing to forecast). I added an A4p arm using S05E's
   own rough-path machinery (`fbm.CirculantEmbedding`, `fgn_acf`, H = 0.1) at the
   cell's measured intercept, keeping the diurnal profile and calibrated jumps.
   It is degenerate in the opposite direction. Both are reported; neither is used
   for the K3 determination, which item 71 places on the holdout regardless.
2. **Phase 4 scope.** Run at B0 and the 1day horizon only. λ is identical for B0
   and B1 by construction (the S08 λ code path never applies the boundary rule),
   and the sizing rule is a daily rebalance. Stated in the report.
3. **Range-mask bug, found and fixed before any result was used.** The 1day
   branch pairs an L-column return array with an (L+1)-column price grid; the
   high/low mask must be the full-width grid, as in S07 `series()`. Phase 5 raised
   a broadcast error, the fix was applied to Phase 5 and Phase 6 identically, and
   nothing had been computed under the wrong mask.
4. **Phase 5 partition split by `lam_in_unit`, added before Phase 6.** The first
   run showed 14 candidates "clearing raw but not measured" on the restricted
   range. All 14 were the ES/GLOBEX cells whose restricted λ is −890, so the
   corrected R² is negative by arithmetic. The partition is now reported split by
   whether λ lies in (0,1]. No threshold, rule or candidate changed; the
   three-way partition of item 70 is reported unchanged within each split.
5. **Phase 7 in-sample sizing baseline.** The degradation comparison needs a real
   in-sample sizing number, which Phase 4 does not supply (it is synthetic). Phase
   7 runs the same sizing code on the pre-2024 panels with the same frozen
   parameters. This adds a measurement; it changes no holdout number.
6. **Timer variable shadowing in `phase34_sizing.py`.** A `for t in TICKS:` loop
   rebound the phase-4 start time, so the first `phase34_meta.json` recorded an
   epoch value instead of an elapsed one. Fixed and rerun; the run is
   deterministic and `phase3_sizing_params.csv` and `phase4_sizing_agg.csv` are
   byte-identical before and after (`diff -q`, both clean).

## Verification performed

- DECISIONS items 66-77 verified present by grep at lines 398, 405, 413, 419,
  424, 433, 437, 442, 445, 454, 457, 466 (12 of 12) before any work. Not
  re-appended, per the session stop condition.
- Items 78 and 79 appended once and verified persistent by grep at lines 469 and
  474, per item 77.
- Extended-grid intercept fits verified against S08 `phase4_fits.csv` over 16
  cells: max |Δc| = 0, max |Δb| = 5.55e-17 (`phase3_s08_equivalence.csv`).
- Oracle sizing R0 returns tracking error 2e-17 to 4e-17 in every cell, confirming
  the sizing harness is correct.
- No full-tree hashing or integrity scanning was performed (items 75, 78). Where
  files were verified, `wc -c` was paired with `wc -l`.
- Not committed to git; the working tree is not a git repository.
- No prior artifact was modified or deleted, including `.venv-broken-20260819`
  and `results/S09-integrity-scan.txt`.

## Holdout engineering counts

2,847,047 raw rows extracted from UTC 2023-12-31; 0 unresolved symbols; 373,743
spread rows filtered; 2,473,304 rows in the holdout window after root and trade
date filtering; 0 weekend trade dates before or after the R3 patch (the patch
reassigned 0 rows, against 1 affected date in sample). R1 excluded 27 RTH and 7
GLOBEX sessions per root. The roll rule excluded 30 sessions per root per
geometry. Final: 621 RTH and 641 GLOBEX sessions per root. Eleven degraded dates
fall in the window (2024-09-18, 2025-09-17, 2025-09-24, 2025-11-28, 2026-01-31,
2026-03-15, 2026-03-16, 2026-03-21, 2026-04-10, 2026-05-24, 2026-07-30) and are
flagged, not excluded, matching the in-sample R2 treatment.

The item-51 halt sessions are all pre-2024, so the presence-based extension to
the calendar exclusion is a no-op on the holdout; the CME calendar rule for
2024-2027 is generated by the same `cme_holidays` function and persisted at
`phase6_calendar.csv`.

## Outcome

K2 (placebo-corrected): INDETERMINATE. K3 sizing null (item 71): FIRES on the
extended range, DOES NOT FIRE on the restricted range. K3 (proxy-error scaling):
STANDS, untouched and independent. Per item 73, no further measurement session
follows.
