# S24 report, test wrapper, Section 8 citations and checker repair

All seven phases completed. Commit `744c4fc` pushed; the remote is in sync and a fresh
clone passes every check.

## Phase 0

| check | result |
|---|---|
| Interpreter | `~/venvs/obs-space-vol/bin/python` |
| numpy / pandas | 2.5.2 / 3.0.5, matching |
| Physical path | not under a known sync root |
| `DECISIONS-as-run.md` digest | `e0ff2520dd484b3d816f6eea1f98b73ce0bd6687ad4b93624d3600d45317411e`, **matches** |
| HEAD at session start | `152e6f28d03aa8766ebade398d11426391723b80`, tree clean, remote in sync |

165 entries, highest 158, gaps at 141 to 143, ten reused numbers (13, 14, 15, 51 to 57).
Items 159, 160 and 161 appended and verified at lines 956, 960 and 965.

## Phase 1, the test wrapper

`tests/test_invariants_against_pre_repair.py`. The library at
`sessions/s06r-repair/tests/test_invariants.py` is **not modified** and is loaded from its
own location rather than imported by name.

Each test does two things rather than one. It asserts the recorded failure count in the
persisted artifact, so a change in the artifact fails the test instead of passing quietly.
And it round-trips the assertion: the counts are parsed out of a recorded failure message,
a minimal input reproducing them is built, the real assertion is called, and the counts it
reports are compared with the ones on record, so a change in the library's behaviour also
fails.

All five tests read one artifact, `sessions/s06r-repair/results/phase1_invariants_on_s05.csv`,
4,103 rows. **`git check-ignore` reports it is not ignored and `git ls-files` confirms it
is tracked**, so the wrapper runs from a clone. No test reads an excluded artifact.

| assertion | recorded | FAIL rows in the artifact | match |
|---|---|---|---|
| `assert_forecasts_positive` | 46 | 46 | yes |
| `assert_loss_finite` | 35 | 35 | yes |
| `assert_lambda_in_unit` | 3683 | 3683 | yes |
| `assert_range_inputs` | 8 | 8 | yes |
| `assert_effective_M` | 88 | 88 | yes |

```
$ python -m pytest tests/ -v
  6 items collected, 6 passed
```

Seven after `tests/test_readme_counts.py` was added in Phase 3.

## Phase 2, Section 8 citations

All nine quantities were located; none was guessed. Seven are stored directly in the S17
artifacts and three are derived as differences of two recorded fields, with the derivation
written into the `location` column rather than left implicit.

| quantity | value | artifact | field |
|---|---|---|---|
| in-sample misclassification | 0.4847577328803862 | `s17-emission/results/phase12_summary.json` | `phase2.rows[2].mis` |
| holdout misclassification | 0.26529790660225444 | same | `phase2.rows[3].mis` |
| state-mean gap threshold | 0.25 | `s17-emission/results/phase2_stability_restricted.csv` | `mu_gap_threshold` value |
| in-sample window share | 0.17428035043804757 | `phase12_summary.json` | `phase2.stability[2].share_gap_below_0p25` |
| holdout window share | 0.06896551724137931 | same | `phase2.stability[3].share_gap_below_0p25` |
| in-sample rate movement | 0.6681257061246726 pp | `phase2_stability_restricted.csv` | **derived**: misclass at `mu_gap_threshold` 0.00 minus 0.50 |
| holdout rate movement | −0.03822452156165279 pp | same | **derived**, same construction |
| inversion magnitude | 21.949542240138452 pp | same | **derived**: in-sample minus holdout at threshold 0.00 |
| in-sample mean separation | 1.7086224134645949 | `phase12_summary.json` | `phase2.rows[2].separation_mean` |
| holdout mean separation | 1.6680181295851042 | same | `phase2.rows[3].separation_mean` |

The "well-separated" restriction the paragraph refers to is `mu_gap_threshold = 0.50`, not
the 0.25 that appears earlier in the same sentence: at 0.25 the movements are +0.357 and
+0.759 points, and only at 0.50 do they reproduce the +0.67 and −0.04 the paper states.
Ten rows registered in `numbers.csv`, now 750.

**Uncited numeric lines in the document: 23 before, 16 after.** The remaining 16 are not
of the same kind:

| count | what |
|---|---|
| 11 | Table 2 data rows, each carrying a `% source:` comment naming its determination JSON, traceable but not through `numbers.csv` |
| 1 | Table 2's footnote, referring to DECISIONS item 61 |
| 2 | design constants in Section 3's table, the 2,000 bootstrap resamples and the 95 percent column header, for which no `numbers.csv` row exists |
| 2 | false positives, the `1.15` of an `\arraystretch` and the `2` in `trigamma(M/2)` |

## Phase 3, generated counts

**Mechanism.** `paper/build_readme.py` reads `DECISIONS.md`, counts the numbered entries
and takes the highest number, and rewrites the one README table row that states them.
`--check` reports staleness without writing. `tests/test_readme_counts.py` calls the same
`counts()` and fails if the README disagrees, so a stale figure cannot be committed
silently.

```
$ python paper/build_readme.py
  updated: 168 entries numbered to 161
$ python paper/build_readme.py --check
  current: 168 entries numbered to 161
```

The figure moved from 165/158 to 168/161 within this session, because Phase 0 appended
three items — which is exactly the failure mode of item 159, now caught by construction
rather than by eye.

**Other typed counts.** Grepping the tracked markdown found 21 further count-like
statements. **None is a live count of a file's own contents.** Every one is a dated record:
figures inside DECISIONS entries describing what was true when the entry was written
(391 occurrences, 56 files, 3683 rows, and item 158's quotation of the stale 155), session
reports under `results/`, `PREREG.md` files, and the specification. Those are correct as
history and must not be regenerated.

## Phase 4, checker repair

`paper/check_build.py` runs 17 checks against extracted text passed through `norm()`,
which NFKC-normalises, folds typographic quotes, apostrophes, dashes and non-breaking
spaces to ASCII, expands the `fi` and `fl` ligatures, and collapses all whitespace. The
fold touches punctuation and whitespace only and changes no alphanumeric content, so it
cannot convert a genuine content failure into a pass.

**17 of 17 pass.** The four historical false positives, tested naively and normalised:

| case | naive | normalised |
|---|---|---|
| S23B: 5.5 heading against an ASCII-apostrophe regex | FAIL | **PASS** |
| S20: artifact path underscore under OT1 | PASS | PASS |
| S23D: README MISSING phrase wrapping a line | FAIL | **PASS** |
| S23D: README entry-count phrase | PASS | PASS |

**Normalisation rescues two of the four, not all four.** The other two now pass under naive
matching because they were fixed at source earlier: the underscore by adding T1 font
encoding in S20, so it extracts as a glyph rather than a drawn rule, and the entry-count
phrase because it occupies a single table row and never wraps. All four pass; the
attribution matters.

## Phase 5, build and commit

Build clean, **16 pages, zero overfull boxes**, no undefined or multiply-defined labels.

Commit `744c4fc`, **9 files**: `DECISIONS.md`, `README.md`, `paper/build_readme.py`,
`paper/check_build.py`, `paper/main.pdf`, `paper/numbers.csv`,
`paper/sections/08_limitations.tex`, `tests/test_invariants_against_pre_repair.py`,
`tests/test_readme_counts.py`. Pushed; `origin/main` and local both at
`744c4fc206d3`. The README contents table gained a `tests/` row and its
`sessions/s06r-repair/tests/` row now says "assertion library, called from inside the
pipeline" rather than "test suite".

## Phase 6, clone verification

Cloned from the remote into a temporary directory. **The clone was not modified.** 582
files.

| check | command | result |
|---|---|---|
| Test suite | `pytest tests/` | **7 collected, 7 passed** |
| Paper build | `pdflatex ×3 + bibtex` | **PASS, 16 pages**, 0 errors, 0 overfull |
| Build checks | `python paper/check_build.py` | **17 of 17 passed** |
| Count generator | `python paper/build_readme.py --check` | current, 168 numbered to 161 |

**Nothing fails from a clone that passes in the working tree.** A reader who clones the
repository and runs `pytest tests/` now sees seven passing tests rather than the empty
suite S23D reported.

## Files added

| file | purpose |
|---|---|
| `tests/test_invariants_against_pre_repair.py` | exercises the five invariants at their recorded counts |
| `tests/test_readme_counts.py` | fails if a README count has drifted |
| `paper/build_readme.py` | generates those counts from `DECISIONS.md` |
| `paper/check_build.py` | the 17-check build harness, matching on normalised text |

`DECISIONS-as-run.md` untouched, digest unchanged. Global git identity unchanged.
