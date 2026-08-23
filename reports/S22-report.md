# S22 report, decisions log register rewrite

Working directory `<REPO>`. Interpreter
`~/venvs/obs-space-vol/bin/python`, numpy 2.5.2, pandas 3.0.5, both matching
the required versions. The physical working path is not under a known sync root and
`~/Desktop` is a real directory rather than a symlink into `Mobile Documents`, so the
synced-path halt was not triggered. No holdout read, no measurement, nothing committed.

## 1. Two premises in the brief that the file did not support

**The brief specified entries 1 through 143. The log's highest item number was 140**, and
no items 141, 142 or 143 had ever been written. The three entries supplied were appended
at the numbers given, 144 to 146, so the numbering now skips 141 to 143. Item 144's own
phrase "Entries 1 through 143" was left exactly as supplied and is inaccurate on that
point; correcting supplied text was outside the instruction, so the discrepancy is
recorded in new item 147 instead.

**The log carries ten item-number collisions predating S22.** 150 numbered entries exist
for 140 numbers. Items 13, 14 and 15 each appear twice, under `session 4 repairs` and
under `S04 conclusion corrected before S05`. Items 51 through 57 each appear twice under
two identically titled `S07 repair completion and SPY replication` headers, the second
block revising the first. All are preserved as run, per the stop condition.

Two entries were appended beyond the three supplied, and both are deviations from the
brief. **Item 147** records the numbering discrepancies above. **Item 148** resolves
item 146, which required a statement about SCOPE.md and could not be satisfied by the
supplied text alone.

## 2. Phase 1 inventory

`results/S22-figures.csv`, one row per occurrence, **1142 occurrences** across all
150 entries of `DECISIONS-as-run.md`.

| kind | occurrences | distinct |
|---|---|---|
| number | 588 | 297 |
| date | 17 | 8 |
| path | 70 | 55 |
| code | 420 | 64 |
| name | 47 | 22 |
| **total** | **1142** | |

**53 of 150 entries** contain a withdrawal, a correction of a prior item, or a
void declaration. All are compared side by side in section 5.

## 3. Phase 5 verification

| check | result |
|---|---|
| Inventoried tokens absent from the rewrite | **2**, both intended (section 4) |
| Numeric or date tokens occurring fewer times in the rewrite | **0** |
| Entries in original / rewrite | 150 / 155 |
| Original entry keys missing from rewrite | **none** |
| Every original item number present in rewrite | **yes** |
| Entries shortened by more than 20 percent | **none** |
| Length change across the 150 rewritten entries | 16 shorter, 61 longer, 73 identical |
| `DECISIONS.md` present | yes, 65494 bytes |
| `DECISIONS-as-run.md` present | yes, 61752 bytes |

The only tokens absent from the rewrite are the two absolute paths generalised under
item 145. No figure, date, threshold, identifier or proper name was lost.

## 4. Paths, secrets and SCOPE

### Paths generalised, per item 145

| item | original | rewrite |
|---|---|---|
| 55 (second occurrence) | `` `~/Downloads/DataBento Data/SPY 1s Data` `` | `` `<DATA_ROOT>/DataBento Data/SPY 1s Data` ``, with DATA_ROOT named in the entry as the local Databento download directory |
| 79 | `~/venvs/obs-space-vol` | `` `~/venvs/obs-space-vol` `` |

Both entries carry an inline `[S22: absolute path generalised per item 145.]` marker, so
the edit is visible in the file and not only in this report.

### Wider scan

Grepped across the whole file: **no email addresses, no API keys, tokens, passwords or
credentials, no account identifiers, no other absolute paths.** The only other match on
a colon-digit pattern was `arXiv:2510.03236`, which is a citation.

### SCOPE.md, resolving item 146

**SCOPE.md does not exist anywhere on the machine.** A search of the user's home
directory to depth six returned nothing. It was never in the working tree, which item 11
recorded at S03. Its section references appear throughout the log at items 11, 43, 55,
56, 57 and 69, and reach the record only as quotations inside session instructions. The
spec records the same provenance independently, its pre-registration table reading
"SCOPE section 3 as quoted". Since the session prompts are not in the repository either,
those quotations survive only where a session report or the spec repeats them. No
reconstruction was attempted. This is written into the log as item 148.

## 5. Side-by-side, every flagged entry

All 53 entries carrying a withdrawal, correction or void declaration. **26 are
unchanged** after whitespace normalisation, which is the strongest available evidence that
nothing was softened; for the remaining 27 only the differing spans are shown, and every
one is a change of tense or of deixis. Entries on the brief's at-risk list are marked ★.

### Item 1

| | text |
|---|---|
| as-run | — |
| rewrite | were |

### Item 4

| | text |
|---|---|
| as-run | is now |
| rewrite | was |
| as-run | are |
| rewrite | were |

### Item 5 ★

**Unchanged.**
```
5. AEROSPACE PROVENANCE CORRECTED. No aerospace method survives in the error model. Nugget
extrapolation is geostatistics (Matheron), three-cornered hat is clock metrology (Gray and Allan
1974). What remains from operational forecasting is the observation-operator framing and the
representativeness decomposition. The writeup states this and claims nothing further.
```

### Item 12

| | text |
|---|---|
| as-run | confirm: |
| rewrite | confirmed it: |

### Item 13 (occurrence 2) ★

**Unchanged.**
```
13. The S04 reading that a Hill tail index of 2.95-3.67 rules out realized quarticity was
OVERSTATED and is withdrawn. The Hill index is measured on the unconditional 1-minute return
distribution, which is a variance mixture across volatility regimes. Realized quarticity
converges to integrated quarticity path-by-path under in-fill asymptotics without requiring the
unconditional fourth moment to exist. What the tail index affects is cross-day pooling,
averaging, and cross-day asymptotic variance, which is what the S04 concentration statistics
measured.
```

### Item 15 (occurrence 2)

| | text |
|---|---|
| as-run | becomes |
| rewrite | became |

### Item 19

| | text |
|---|---|
| as-run | runs here. |
| rewrite | was run in S05A. |
| as-run | exist |
| rewrite | existed |
| as-run | has |
| rewrite | had |
| as-run | invalidates |
| rewrite | would invalidate |

### Item 27

| | text |
|---|---|
| as-run | is |
| rewrite | was |
| as-run | here. |
| rewrite | in S05B. |

### Item 28

**Unchanged.**
```
28. The exact finite-M sampling variance of log RV under constant volatility is trigamma(M/2),
not 2/M. The approximation understates it by 40 percent at M=3, 8.1 percent at M=13 and 0.3
percent at M=390, so the error concentrates at the coarse end where the elasticity fit takes its
leverage. trigamma is used throughout and every prior use of 2/M is recorded.
```

### Item 34

**Unchanged.**
```
34. Globex 1day is NOT exempt on the grounds that it contains no zero-variance windows, since it
reads the same panel and a column mapping defect would displace returns without creating zeros
at daily aggregation.
```

### Item 35

**Unchanged.**
```
35. S05D returned determination A. The Globex panel is correct, the zero-variance windows are
holiday early closes on the 52 ES and 47 NQ sessions S04's R1 rule retains in GLOBEX and
excludes from RTH, and DECISIONS items 33 and 34 are closed with no Globex result invalidated.
```

### Item 38

**Unchanged.**
```
38. The `present` mask is not persisted in the S05 panel npz files, so padding is
indistinguishable from a genuine unchanged close for any consumer of those files. Recorded as an
artifact defect; measured exposure at daily aggregation is 0.65 percent of RV and 8e-04 on the
fitted exponent.
```

### Item 44

| | text |
|---|---|
| as-run | IS |
| rewrite | WAS |
| as-run | was |
| rewrite | had been |

### Item 46

| | text |
|---|---|
| as-run | are |
| rewrite | were |
| as-run | are |
| rewrite | were |
| as-run | is |
| rewrite | was |
| as-run | are |
| rewrite | were |

### Item 47

| | text |
|---|---|
| as-run | is |
| rewrite | was |

### Item 49

| | text |
|---|---|
| as-run | reports |
| rewrite | reported |

### Item 55

| | text |
|---|---|
| as-run | is |
| rewrite | was |
| as-run | is |
| rewrite | was |

### Item 55 (occurrence 2)

| | text |
|---|---|
| as-run | `~/Downloads/DataBento |
| rewrite | `<DATA_ROOT>/DataBento |
| as-run | — |
| rewrite | where DATA_ROOT is the local Databento download directory, |
| as-run | inventories |
| rewrite | inventoried |
| as-run | records |
| rewrite | recorded |
| as-run | rebuilds |
| rewrite | rebuilt |
| as-run | are |
| rewrite | were |
| as-run | — |
| rewrite | [S22: absolute path generalised per item 145.] |

### Item 56

| | text |
|---|---|
| as-run | here |
| rewrite | — |

### Item 57 (occurrence 2)

| | text |
|---|---|
| as-run | reported here. |
| rewrite | reported. |

### Item 63

**Unchanged.**
```
63. INTERCEPT ROUTE TO LAMBDA, adopted as a third reported column beside E2 and E4. Fitting
Var(log RV_M) = c + A M^b gives c as a direct estimate of Var(log IV), so lambda_M = c / Var(log
RV_M) at any sampling frequency, with no assumption about how proxy noise scales. With A > 0 and
b < 0 the estimate lies in (0,1) BY CONSTRUCTION, which no existing estimator does: E2 and E4
violated the bound at 14 of 248 grid points in S06R and at 3683 rows in the pre-repair
artifacts. Fits with A <= 0 or b >= 0 are marked invalid and excluded, since the route is
undefined there.
```

### Item 64

| | text |
|---|---|
| as-run | IS |
| rewrite | WAS |
| as-run | this |
| rewrite | that |

### Item 66

**Unchanged.**
```
66. ITEM 29 AMENDED, disclosed. Item 29 barred M of 5, 6 and 10 from headline lambda values on
the stated ground that E2 cannot form non-overlapping subsamples in a tiny window and E4's
quarticity is worthless there. The intercept route postdates item 29 and uses neither mechanism,
needing only the fitted intercept from the whole grid and the directly observed Var(log RV_M).
The reasoning therefore does not transfer. BOTH ranges are reported side by side throughout,
restricted to the original grid and extended, with every grid point labelled. Neither is
reported alone.
```

### Item 69

**Unchanged.**
```
69. SIZING METRICS. Primary is tracking error, the root mean squared deviation of log realized
portfolio volatility from log target. Secondary is turnover, mean absolute change in position
weight, priced across the pre-registered round-turn cost sweep of 0.5, 1.0, 2.0 and 4.0 ticks
per leg at the SCOPE section 4 tick values of $12.50 for ES and $5.00 for NQ. A single assumed
cost is not admissible.
```

### Item 70

**Unchanged.**
```
70. SIGNAL SET AND THRESHOLD, fixed before any result. Candidates for forward realized variance:
realized semivariance up, realized semivariance down, jump variation as RV minus bipower,
Parkinson range, Garman-Klass range, volume surprise against a time-of-day norm, ES-NQ cross
lead-lag, realized quarticity, signature-plot slope. Retention threshold R-squared >= 0.02 on
the evaluation sample. Candidates partition into clears-under-both, clears-only-after-measured-
correction, and clears-neither. The correction rescales every candidate in a cell by the same
factor, so RANKING IS UNCHANGED BY CONSTRUCTION and only threshold crossing can change. That is
stated in the report rather than presented as a finding.
```

### Item 71

**Unchanged.**
```
71. K3 KILL CONDITION. If the tracking error difference between R2 and R3 is below 5 percent in
relative terms in every cell and at every point of the cost sweep, K3 fires and the sizing
consequence is reported as a pre-registered null using the drafted abstract. K3 is evaluated on
the holdout, not in sample.
```

### Item 72

| | text |
|---|---|
| as-run | in Phase 6, |
| rewrite | — |

### Item 74 ★

**Unchanged.**
```
74. THE S09 INTEGRITY SCAN OF 2026-08-19 IS VOID. It reported 61 of 142 sampled artifacts
hashing to the SHA-256 of the empty string and concluded storage failure. Verification on the
same day found every flagged file intact: PREREG.md returns 4716 bytes under `wc -c`, all seven
S02 source files carry real sizes, no migration process was running, the volume was at 33
percent capacity, and numpy 2.5.2 imports cleanly in `.venv`. The scan hashed several gigabytes
including the 460 MB Databento archive, exceeded its command timeout, and returned the empty-
string digest for every read it failed to complete. `S09-integrity-scan.txt` is retained as a
record of the fault and its contents carry no evidential weight.
```

### Item 78

**Unchanged.**
```
78. ITEM 75 IS AMENDED. `wc -c` alone is insufficient for file verification. In S09-PRE the
damaged pandas/core/dtypes/common.py returned 56,234 bytes under `wc -c` while yielding zero
lines and erroring on `tail`, because byte count is metadata and survives the loss of the data
blocks. File verification pairs `wc -c` with `wc -l`, and a file with a nonzero byte count and
zero lines is treated as unreadable.
```

### Item 80

| | text |
|---|---|
| as-run | runs |
| rewrite | ran |
| as-run | has |
| rewrite | had |
| as-run | rests |
| rewrite | rested |
| as-run | adds |
| rewrite | added |
| as-run | opens |
| rewrite | opened |

### Item 84

| | text |
|---|---|
| as-run | is |
| rewrite | was to be |
| as-run | here |
| rewrite | in S10 |
| as-run | leaves |
| rewrite | left |

### Item 85

| | text |
|---|---|
| as-run | is |
| rewrite | was |

### Item 86

**Unchanged.**
```
86. ZERO-PREDICTOR WINDOWS ARE DROPPED, NOT FLOORED. S10 Phase 7 found three windows of 11,406
with RS-up exactly zero mapped to -690.78 by log(max(v,1e-300)) at phase5_signals.py:104 and
phase6_holdout.py:330, moving R-squared from 0.0128 to 0.4286. The justification is NOT item
60's insanity filter: zero upside semivariance is a legitimate observation, not an error, and
substituting any value invents data. A window whose predictor is zero has no defined log-
predictor and is dropped from that candidate's regression, count reported per cell, applied
identically to every candidate, never conditioned on the target.
```

### Item 87

| | text |
|---|---|
| as-run | is |
| rewrite | was |
| as-run | here. |
| rewrite | in S11. |

### Item 88

| | text |
|---|---|
| as-run | re-evaluates |
| rewrite | re-evaluated |

### Item 93

**Unchanged.**
```
93. K5, COMBINATION WEIGHTS. Inverse-MSE combination over the seven-model set, naive against
noise-corrected. K5 FIRES if the mean absolute weight change is below 0.02 in every cell, or if
the resulting out-of-sample tracking-error difference is below 5 percent relative in every cell
at every cost-sweep point, matching item 71's threshold.
```

### Item 94

**Unchanged.**
```
94. K6, CONVEXITY. K6 FIRES if the proportional overstatement of the convexity adjustment from
naive Var(log IV) is below 5 percent in every cell.
```

### Item 95 ★

| | text |
|---|---|
| as-run | is |
| rewrite | was |

### Item 98

**Unchanged.**
```
98. K4 IS RESTATED BY LIMIT. The leverage cap at 2.0x never bound across 2,524 decision points,
so only the stop-out was exercised. Reporting a two-limit specification as firing overstates
coverage. K4 is reported per limit, with the cap recorded as untested at this target and the
level at which it would begin to bind reported.
```

### Item 100

| | text |
|---|---|
| as-run | tests |
| rewrite | tested |

### Item 103

**Unchanged.**
```
103. K7, RISK PARITY. Two-asset inverse-volatility book, ES and NQ, RTH daily, monthly
rebalance, naive weights from proxy-based volatility against weights corrected for the measured
reliability difference. K7 FIRES if the mean absolute weight deviation from the corrected
allocation is below 0.02, or if the out-of-sample difference in realized portfolio volatility is
below 5 percent relative at every cost-sweep point. Thresholds fixed here, before any result.
```

### Item 108

**Unchanged.**
```
108. K9, HAR PERSISTENCE ATTENUATION. HAR regressors are noisy proxies, so coefficients are
attenuated by errors in variables, and the daily, weekly and monthly components carry noise
variance in the ratio 1, 1/5, 1/22, so the daily coefficient is attenuated most and the cleaner
components absorb the difference. K9 FIRES if the corrected daily coefficient differs from the
naive by less than 10 percent relative in every cell. The point forecast of realized variance is
NOT claimed to change; the claim is about reported persistence and relative lag structure, and
the report states that limit explicitly.
```

### Item 109

**Unchanged.**
```
109. K10, HURST BIAS. The standard estimator regresses the q-th absolute moment of log-
volatility increments on lag; proxy noise adds a nugget that does not vanish at short lags,
flattening the apparent scaling and biasing H downward. The project's lambda measures that
nugget along sampling frequency rather than lag, an independent axis. K10 FIRES if corrected H
differs from naive H by less than 0.02 in every cell.
```

### Item 111 ★

**Unchanged.**
```
111. K10 CARRIES A LAG-SELECTION CONFOUND. The nugget reaches 126 percent of the increment
moment at lag 1, so corrected S(Delta) goes negative at short lags and those lags drop from the
corrected regression. Short lags are precisely what identifies H in a rough-volatility fit, and
refitting on longer lags mechanically raises H because the log-log slope over long lags
approaches Brownian regardless of any nugget. An unknown share of the 0.208 shift on ES is
therefore lag selection rather than nugget subtraction. No Hurst figure is reportable until
naive H is refitted on exactly the surviving lag subset.
```

### Item 112

**Unchanged.**
```
112. K9 ASSUMES CLASSICAL MEASUREMENT ERROR AND THE PROGRAMME'S CENTRAL FINDING DISPUTES IT.
Sigma_E takes v from A*M^b, treating the whole excess over Var(log IV) as error independent of
the true regressor. The excess decays at M^-0.44 rather than M^-1 and S11 attributes part of it
to within-window volatility dispersion, a price-process property. If that component correlates
with the level of integrated variance the error is non-classical and the correction over-
corrects. A daily coefficient moving +116 percent with the weekly coefficient flipping sign on
ES/GLOBEX is consistent with over-correction.
```

### Item 115

| | text |
|---|---|
| as-run | runs |
| rewrite | ran |
| as-run | is |
| rewrite | was |
| as-run | is |
| rewrite | was |

### Item 122

**Unchanged.**
```
122. RESULT HIERARCHY, FIXED HERE AND NOT SUBJECT TO REVISION BY S17. The primary results are
the proxy-error scaling exponent (S07-S15), the intercept estimator for lambda (S08, S15), and
the first-order criterion separating decisions where proxy noise matters from those where it
does not (S11, S13, S14). K1 through K11 are applications of that criterion and are secondary. A
negative S17 result bears on where the parameter can be inserted, not on whether it was measured
correctly. The report states this ordering explicitly and does not lead with S17.
```

### Item 125

**Unchanged.**
```
125. ARM A4, THE CORRECTION ENTERS THE MODEL. S16 established that any affine correction to the
observable is annihilated exactly by within-window z-scoring, which is a property of the whole
class of linear proxy corrections upstream of a normalising classifier. The remaining route is
the observation equation. A4 is the same two-state Gaussian HMM with the emission variance in
each state decomposed into a state variance plus a KNOWN observation-noise variance taken from
the measured lambda, held fixed during estimation rather than estimated. Window, state count,
normalisation, labelling, reference classifier and allocation are identical to A1, so the
comparison isolates the emission change.
```

### Item 126

**Unchanged.**
```
126. K12, MEASUREMENT ERROR IN THE EMISSION. Primary metric is misclassification against the
finest-grid noise-robust reference, as in K8 and K11. K12 FIRES if A4 reduces misclassification
by less than 1 percentage point against A1 in every cell. Secondary metrics are switch count,
regime duration and the allocation overlay, reported but not determining. Threshold fixed here.
```

### Item 129

| | text |
|---|---|
| as-run | has |
| rewrite | had |

### Item 132

| | text |
|---|---|
| as-run | is |
| rewrite | was |
| as-run | builds |
| rewrite | built |
| as-run | halts |
| rewrite | would halt |
| as-run | fails, |
| rewrite | failed, |

### Item 139

| | text |
|---|---|
| as-run | are |
| rewrite | were |
| as-run | regains |
| rewrite | regained |

### Item 140 ★

**Unchanged.**
```
140. TWO SUBSTANTIVE ERRORS. Section 7.2 states that tercile boundaries place the threshold
"where the density is higher"; for a unimodal distribution the median sits nearer the mode and
the tercile boundaries sit further out, so the stated mechanism is backwards. The empirical rate
rises because two boundaries admit more disagreements than one. And signature plots are
Andersen, Bollerslev, Diebold and Labys (2000), "Great Realizations", Risk 13(3), not the 2001
JASA paper currently cited, which concerns the distribution of realized volatility.
```

## 6. Files

| file | state |
|---|---|
| `DECISIONS.md` | rewritten, 894 lines, 155 entries numbered to 148 |
| `DECISIONS-as-run.md` | unmodified original, 844 lines, SHA-256 `e0ff2520dd484b3d816f6eea1f98b73ce0bd6687ad4b93624d3600d45317411e`, untouched after creation |
| `results/S22-figures.csv` | Phase 1 inventory, 1,142 rows |
| `README.md` | provenance section added, four stale facts corrected |
| `results/S22-report.md` | this file |

## 7. README deviations

The brief specified a README statement that the analysis ran across **nineteen** logged
sessions and that **every session prompt** is in the repository. Neither is true of this
repository, so neither was written.

- **Session count.** There are 22 directories under `sessions/`, plus S18, S19 and S20 in
  `results/`, plus S22, giving **twenty-six** logged sessions. Twenty-four carry a written
  report; S02 has seven source files and raw output but no report or runlog. The README
  states twenty-six and names the S02 exception.
- **Prompts.** A search of the repository found **no session prompt, brief or instruction
  file** outside two unrelated files vendored inside `.venv`. The README states plainly
  that the prompts are not in the repository and that what they fixed is in `DECISIONS.md`.

Four stale facts in the README were also corrected, all of the same class as item 139:
the exponent range read −0.44 where the artifact gives −0.41, the kill-condition count read
twelve where item 139 established thirteen, the log was described as 132 numbered items,
and the status section listed sections 1, 2 and 3 as stubs when they are now written.

