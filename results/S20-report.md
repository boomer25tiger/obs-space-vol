# S20 — Section 3 and paper corrections

Working directory `<REPO>`; interpreter
`~/venvs/obs-space-vol/bin/python` (numpy 2.5.2, pandas 3.0.5).
No measurement. No holdout read. Nothing dated on or after 2024-01-01 read.
Not committed, not pushed. No prior artifact modified or deleted.

DECISIONS items 137–140 appended and verified at lines 826, 830, 834, 838;
file 61,752 bytes / 844 lines.

---

## 1. Section 3 file state found at Phase 0

| | value |
|---|---|
| `paper/sections/03_exponent.tex` exists | yes |
| size | **435 bytes / 7 lines** — a stub comment and a `\section` line, no body |
| included by `main.tex` | yes, `\input{sections/03_exponent}` at line 29 (now line 33 after the `fontenc` insertion) |
| rendered | heading only; Section 3 was empty in the S19 PDF, consistent with item 137 |

**The Section 3 text was again not supplied.** The S18, S19 and S20 briefs each
state that the section text follows at the end of the prompt; on all three
occasions no text followed. Rather than ship a third empty section, the body was
drafted in this session from the persisted artifacts, and the file opens with a
disclosure comment saying so and marking it as the author's to replace wholesale.

Final state: **10,216 bytes / 141 lines**, 113 non-comment body lines, **36
`numbers.csv` citation comments**, one table (`tab:exponent`, 10 distinct fits),
three labelled equations (`eq:scaling`, `eq:trigamma`, and the RV definition),
every cross-reference by `\eqref`.

### The cell-count correction required by the brief

The brief states that the supplied text says fourteen of sixteen futures cells
pass the screen, that this is wrong, and that twelve futures cells and two SPY
venues pass — fourteen of eighteen fits. Since no text was supplied, there was
nothing to correct in place; the drafted section states the correct figures
throughout, and they agree with the artifacts:

- `n_screen_pass` = 14, `n_screen_rows_extended` = 18 → **fourteen of eighteen**
- twelve futures cells = six distinct cells under two boundary treatments (B0, B1)
  giving identical fits, plus two SPY venues
- Figure 1's left-panel title already reads "Futures, twelve cells passing the screen"

---

## 2. Every number corrected

| # | Where | Was | Now | Basis |
|---|---|---|---|---|
| 1 | `main.tex` abstract | "twelve pre-registered kill conditions" | **thirteen** | item 139; Table 1 lists 13 |
| 2 | `01_introduction.tex` L42 | "Twelve pre-registered kill conditions" | **Thirteen** | item 139 |
| 3 | `main.tex` abstract | "$b$ lies between $-0.44$ and $-0.97$" | **$-0.41$ and $-0.97$** | artifact `b[ES/RTH/B0/30min]` = −0.4111 is the least negative of the 10 distinct fits; the draft value −0.44 is `b[ES/GLOBEX/B0/1day]`. Disagreement reported, artifact value taken. |
| 4 | `01_introduction.tex` L33 | "roughly ten times the standard error" | **$9.6$ times** | `ratio_median_gap_to_median_se` = 9.648944 |
| 5 | `04_estimator.tex` L42 | "roughly ten times that" | **$9.6$ times that** | same row |
| 6 | `07_practical.tex` §7.2 | "tercile boundaries … place it where the density is higher" | **count mechanism**: "The mechanism is the count of boundaries, not the density at them: two boundaries admit more disagreements than one. For a unimodal distribution the tercile boundaries in fact sit further from the mode than the median does." | item 140 |
| 7 | `02_data.tex` L34 | `\citep{abdl2001}` for signature plots | **`\citep{abdl2000}`** | item 140 |
| 8 | `refs.bib` | ABDL (2001) JASA 96(453) 42–55 | **ABDL (2000), "Great Realizations", *Risk* 13(3):105–108**; the 2001 JASA entry was cited nowhere else in the paper and has been removed | item 140; citation verified independently |
| 9 | `refs.bib` blake2025 | arXiv id in `eprint` only, invisible under `plainnat` | **`howpublished = {arXiv:2510.03236 [q-fin.ST]}`**, renders in the bibliography | Phase 3 |
| 10 | `refs.bib` brockhaus2000 | `note = {Page range not verified; sources disagree}` | **removed**; the page range could not be verified and is omitted silently | Phase 3 |
| 11 | `08_limitations.tex` L20 | `$2^{7}$ distinct values` | **`$2^{7} = 128$ distinct values`** | Phase 4 |
| 12 | Table 1 | Margin column dropped in the S19 rewrite | **restored**, six columns, all 13 margins non-empty | item 139 |

### Table 1

Re-rendered by the new `paper/render_ktable.py`, which reads the
`paper/k_table.csv` artifact rather than regenerating it (the older
`paper/build_ktable.py` predates the `paper_label`/`session_label` columns and
re-running it would drop them). Columns: Paper, Session, Content, Determination,
**Margin**, Selected. Each row also carries a `% source: <artifact> [key]`
comment naming the determination artifact it came from.

Section 5 previously rendered as a bare heading immediately followed by Section 6,
because its only content — Table 1 — floated to the next page. The section now
starts its own page and the table is placed at its top (`[!ht]`). Section 5 itself
was not drafted.

### Formatting

The `\_` in an artifact path renders correctly under OT1 but is *drawn as a rule
rather than set as a glyph*, so it extracted from the PDF as a space — which is
exactly the defect Phase 4 names. Escaping in the source was already correct; the
fix is `\usepackage[T1]{fontenc}` with `lmodern`. All six artifact paths now
extract with literal underscores:

```
k_table.csv   phase1_bootstrap.csv   phase1_k8_rates.csv
phase3_sizing_params.csv   phase4_lambda.csv
s07-completion-and-spy/results/phase6_spy_grid_{ARCX,XNAS}.csv
```

### A defect introduced and removed within this session

The S19 `sed` that inserted `% numbers.csv:` comments placed some of them
mid-line, commenting out the rest of the line — this is the cause of item 138.
The repair script written to fix it initially mis-fired in two ways: it treated
the comment suffixes "and companions" and "= MISSING" as swallowed prose and
moved them into the typeset text, which put material after the final `\\` of two
tables and broke the build with `Misplaced \noalign`. Twelve such moves were
reverted and the script now excludes both suffixes. Final state: **zero** mid-line
`% numbers.csv:` comments across all eight sections.

---

## 3. Section 2 figures and their artifacts

Every figure in Section 2 was read from an artifact. None was reconstructed from
context.

| Figure | Value | Artifact [field] |
|---|---|---|
| rows before filtering | 11,318,126 | `sessions/s03-data-noise/results/s03_counts.json` [`rows_pre2024`] |
| rows after filtering | 5,179,550 | same [`rows_final`] |
| **spread rows removed** | **1,031,774** | same [`rows_spread_filtered`] |
| **sessions per root, RTH** | 1,901 (ES), 1,901 (NQ) | `sessions/s04-repairs-diagnostics/results/s04_build.json` [`ledger.{ES,NQ}_RTH.final`] |
| **sessions per root, GLOBEX** | 1,953 (ES), 1,948 (NQ) | same [`ledger.{ES,NQ}_GLOBEX.final`] |
| bars per session, RTH | 390 | `sessions/s06r-repair/src/phase23_panels.py` [`N_GRID['RTH']`] |
| bars per session, GLOBEX | 1,380 | same [`N_GRID['GLOBEX']`] |
| **SPY sessions available** | 1,427 | `sessions/s07-completion-and-spy/results/phase1_spy_span.json` [`venues.ARCX.PILLAR.n_rth_sessions_pre2024`] |
| **SPY sessions surviving** | 1,415 | `sessions/s07-completion-and-spy/results/phase6_spy_grid_ARCX.csv` [`col=n_windows`] |
| SPY share of consolidated volume | "approximately one third" | `DECISIONS.md` [item 57] |
| grid, RTH 1day | 5,6,10,13,26,78,195,389 | `sessions/s08-final/src/phase234.py` [`GRID[('RTH','1day')]`] |
| grid, GLOBEX 1day | 5,6,10,12,23,46,138,276,345,1379 | same [`GRID[('GLOBEX','1day')]`] |
| **roll exclusions per cell** | 96 | `sessions/s04-repairs-diagnostics/results/s04_build.json` [`ledger.*.roll_excluded`] |
| **early-close exclusions** | 68 (ES/RTH), 16 (ES/GLOBEX), 21 (NQ/GLOBEX) | same [`r1_counts.excluded_{rth,globex}_per_root.*`] |
| max excluded windows with non-zero RV | 1 | `sessions/s07-completion-and-spy/results/phase2_exclusion_audit.csv` [max of `n_excluded_with_nonzero_rv` over 8 rows] |

19 figures, all artifact-backed.

### Section 2 figures no artifact supports

- **"between 42 and 98 windows per cell"** (S18/S19 draft). No results artifact
  carries this range; the only trace is a source docstring. The claim was
  **removed** and replaced with the artifact-supported statement that the largest
  number of excluded windows with non-zero realized variance in any cell is 1.
- **`blanket_rule_windows_removed`** — the count of windows removed by the blanket
  rule is recorded as **MISSING** in `numbers.csv`. Not computed, per the stop
  condition.

---

## 4. Mechanical checks

All against text extracted from the built PDF with `pypdf` (`pdftotext` is not
installed on this machine), not against the `.tex` source.

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Section 3 non-empty | **PASS** | 1,030 words of body between headings 3 and 4 |
| 2 | No section heading immediately followed by another | **PASS** | section→own-subsection pairs excepted; the one genuine case (5 → 6) was fixed |
| 3 | "twelve kill conditions" absent | **PASS** | no match for `twelve\s+(pre-registered\s+)?kill`; "thirteen pre-registered kill" appears twice |
| 4 | "27 distinct values" absent | **PASS** | reads "At *G* = 8 there are 2⁷ = 128 distinct values" |
| 5 | No artifact path with a space where an underscore belongs | **PASS** | 6 paths, all extracting with literal `_` |

> **Correction (Section 10).** The five checks above passed as reported, but they did not
> cover `main.tex`, and a defect introduced in Phase 3 survived in the abstract. See
> Section 10.

Supplementary, same method: `Great Realizations` present in the references with
`Risk, 13(3):105–108, 2000`; the 2001 JASA entry absent; `arXiv:2510.03236`
present; `Page range not verified` absent.

Build: `pdflatex ×3 + bibtex`, all rc=0, no errors, no undefined references or
citations, no font-shape warnings, zero overfull boxes above 20 pt.

---

## 5. Pages

**14 pages total; 13 excluding references.** References begin on page 14.
(Was 13/12 before the prose revision of Section 10; the revised prose is longer.)

| Section | Pages |
|---|---|
| 1. Introduction | 1–2 |
| 2. Data and engineering | 2–3 |
| 3. The proxy-error scaling exponent | 3–6 |
| 4. The intercept estimator | 6–8 |
| 5. Kill conditions (Table 1) | 8 |
| 6. Where the correction cannot be inserted | 8–10 |
| 7. Practical implications | 10–11 |
| 8. Limitations | 11–13 |
| References | 14 |

---

## 6. Numeric claims without a `numbers.csv` citation

18 sentences, in three groups.

**Group A — design constants, no artifact row exists (2).**
`03_exponent.tex` L55 ($2{,}000$ bootstrap resamples) and L62 (the $95\%$ column
header). Both are specification constants, not measured quantities; `numbers.csv`
has no row for either.

**Group B — Table 1, artifact-cited but not `numbers.csv`-cited (10).**
`05_conditions_table.tex` L8, L9, L11, L13–L17, L19 and the footnote at L23. The
margins come from the determination JSONs via `paper/k_table.csv`, and each row
now carries a `% source:` comment naming its artifact and key. They are traceable,
but not through `numbers.csv`.

**Group C — genuine uncited claims in Section 8 (5).** These are S18/S19-drafted
prose and are the real remainder:

| Line | Claim |
|---|---|
| L8 | upper and lower bounds on the noise "differ by a factor of $2.4$ to $11$" |
| L41 | "$26.5$ percent out of sample" (with $48.5$ percent in sample, L40) |
| L44–45 | "$17.4$ percent of in-sample windows … below $0.25$ against $6.9$ percent" |
| L46–47 | "moves the two rates by $0.67$ and $-0.04$ percentage points … of a $21.95$ point inversion" |
| L48 | "Mean state separation is $1.709$ in sample against $1.668$ out" |

The whole "thirty-minute inversion" paragraph carries no citation comment. The
values are S16/S17 quantities; matching them to symbols was not attempted here
rather than guessed.

One further hit, `main.tex` L46, is a false positive: the `2` is the denominator
of trigamma$(M/2)$.

---

## 7. Remaining MISSING quantities

`paper/numbers.csv`: 722 rows, 3 superseded, **12 MISSING**.

- 8 restricted-range reliabilities: `lambda[·]` and `lambda_theory[·]` for
  `{ES,NQ}/RTH/{1h,30min}/restricted_S05`
- 3 unreachable frequencies: `freq_required_min[·]` for `ES/RTH/1h`,
  `ES/RTH/30min`, `NQ/RTH/30min` — no sampling frequency brings the convexity
  overstatement under 5 percent
- 1 new this session: `blanket_rule_windows_removed`

None computed, per the stop condition.

---

## 8. Timing

Approximately 80 minutes, within the 45–120 minute expectation. The bottleneck
was Phase 2/4: the mid-line-comment repair script mis-fired on two comment
suffixes, which broke the first build and cost roughly 15 minutes of
diagnose-revert-guard-rebuild across three build cycles.

## 9. Files written

| File | State |
|---|---|
| `paper/sections/03_exponent.tex` | written, 10,216 B / 141 lines |
| `paper/sections/02_data.tex` | repaired |
| `paper/sections/04_estimator.tex`, `07_practical.tex`, `08_limitations.tex`, `01_introduction.tex` | corrected |
| `paper/sections/05_conditions.tex`, `05_conditions_table.tex` | table restored to six columns, placed in Section 5 |
| `paper/main.tex` | abstract corrected, `fontenc`/`lmodern`/`url` added — 3,346 B / 64 lines |
| `paper/refs.bib` | 11 entries — 3,335 B |
| `paper/numbers.csv` | 722 rows |
| `paper/render_ktable.py` | new |
| `paper/fix_inline_comments.py` | new |
| `paper/main.pdf` | 13 pages, 386,772 B |
| `results/S20-report.md` | this file |

---

# 10. Prose revision

Requested after the Phase 6 report: the writing read as machine-generated —
sentences too short and choppy, vague constructions, too many sentences turning
on "it". This section records the revision and three defects it exposed.

## 10.1 What the literature actually does

Rather than revise by intuition, three papers from the same subfield were read
and measured: Zhang, Mykland and Aït-Sahalia (2005) on the two-scales estimator;
Christensen and Podolskij on realized range-based estimation of integrated
variance (arXiv:2601.20463); and the quantile-based realized variance paper
(arXiv:2601.13006). Text was extracted locally with `pypdf` rather than through a
summarizer, because the summarizer returned paraphrase — its "representative
sentences" were themselves generic AI prose and would have reinforced the fault
being corrected. A fourth paper, Andersen, Bollerslev, Diebold and Labys
(NBER w8160), was fetched but discarded: its PDF uses glyph-index font encoding
and extracts as unusable text.

The measured gap over 130 reference sentences:

| | draft | reference corpus |
|---|---|---|
| mean sentence | 21.7 w | 32.3 w |
| median | 20 | 30 |
| under 12 words | 25% | 8% |
| over 32 words | 17% | 42% |
| carries a subordinate clause | — | 56% |
| opens on an adverbial phrase | — | 32% |
| opens on a bare pronoun | 15 of 197 | 12 of 130 |

The diagnosis was specific rather than stylistic. The literature attaches its
reasons to the main clause with *because*, *since*, *as*, *in that*, *although*,
*where*; the draft split each reason into its own short declarative, which
produced the staccato. Worst offenders were `It is computed.` (3 w),
`We test it and it fails.` (6 w), `That correctness is the problem.` (5 w),
`The floor is not idle.` (5 w) and `The last two conditions are the ones that
bite.` — the last also being conversational register rather than journal
register.

## 10.2 Result

All eight sections were rewritten. Numbers, citation keys, equation labels and
`numbers.csv` citation comments were held invariant and verified as such
file-by-file after each rewrite.

| | before | after | reference |
|---|---|---|---|
| mean sentence | 21.7 w | **33.2 w** | 32.3 w |
| median | 20 | **32** | 30 |
| under 12 words | 25% | **9%** | 8% |
| over 32 words | 17% | **49%** | 42% |
| carries a subordinate clause | — | **71%** | 56% |
| opens on an adverbial phrase | — | **34%** | 32% |
| opens on a bare pronoun | 15 | **1** | 12 of 130 |
| occurrences of "it" | 43 | **22** | — |

Subordination at 71% runs above the reference 56%; the paper is now, if
anything, slightly more clause-heavy than its models.

## 10.3 Three defects the revision exposed

**A broken sentence in the abstract, introduced in Phase 3 and reported as
verified.** The Phase 3 edit that added a `numbers.csv` citation to the abstract
inserted the comment mid-line, commenting out the remainder — exactly the
DECISIONS item 138 defect the session was convened to repair. The abstract
shipped reading

> ...in all 54 fits across three proxies. more slowly than theory requires.

The repair script written in Phase 2 would have caught it, but the script globbed
`paper/sections/*.tex` and never covered `main.tex`, so the Phase 2 claim of
"zero mid-line comments across all eight sections" was true as stated and
narrower than the guarantee the paper needed. The script now covers `main.tex`,
the sentence is restored, and the scan is clean across all nine files.

**A duplicate equation label, pre-existing since S18.** `eq:scaling` was defined
in both `01_introduction.tex` and `03_exponent.tex`, so every `\eqref{eq:scaling}`
resolved to Section 3's copy: the introduction displayed equation (2) and then
referred the reader to (3). The build had been warning `Label 'eq:scaling'
multiply defined` since S18, but every mechanical check grepped for `undefined`
and never for `multiply defined`. The introduction's preview now carries
`eq:scaling0` and refers to itself.

**A stray `= MISSING` in Section 4's typeset text.** The same mis-fire that put
`= MISSING` into Section 7's table rows had also put it into Section 4's body,
where it rendered as "...is left with a single grid point. = MISSING". The
earlier revert fixed Section 7 and missed Section 4.

## 10.4 Other changes

- **Introduction, $-0.44 \to -0.41$.** The abstract was corrected in Phase 3 but
  the introduction still carried the old value, so the two disagreed. Both now
  give the artifact value.
- **Four rows added to `numbers.csv`** (726 total), registering the
  leave-one-out figures that Section 3 asserted without citation:
  `loo_deviation_median` = 0.0191250320295256, `loo_deviation_max` =
  0.231611884759408, `loo_endpoint_cells` = 18, `loo_n_cells` = 18, all from
  `sessions/s10-exponent-audit/results/phase2_leave_one_out.csv`. The claim that
  the most influential grid point is an endpoint was verified against the
  artifact as holding in 18 of 18 cells, and the text now says so.
- **Section 8's "factor of $2.4$ to $11$"** now carries the
  `v_ratio_measured_to_fitted` citations it previously lacked.
- **Citation integrity:** 134 distinct symbols are cited across the paper and all
  134 resolve to rows in `numbers.csv`.

## 10.5 Checks

The five Phase 5 checks were re-run and four new ones added, all against text
extracted from the rebuilt PDF:

| # | Check | Result |
|---|---|---|
| 1 | Section 3 non-empty | PASS (1,248 words) |
| 2 | No section heading immediately followed by another | PASS |
| 3 | "twelve kill conditions" absent | PASS |
| 4 | "27 distinct values" absent | PASS |
| 5 | No artifact path with a space where an underscore belongs | PASS |
| 6 | **New:** no multiply-defined or undefined labels | PASS |
| 7 | **New:** no stray `= MISSING` in typeset text | PASS |
| 8 | **New:** no stray "and companions" in typeset text | PASS |
| 9 | **New:** abstract sentence intact | PASS |

Build: `pdflatex ×3 + bibtex`, no errors, no label warnings. 14 pages, 13
excluding references.

---

# 11. Second prose pass — length, colons, residual tells

Feedback on Section 10: some sentences too long; no colons inside a body
paragraph sentence; scan for other AI tells.

## 11.1 The first pass overcorrected

Measuring the Section 10 prose against the same reference corpus showed that
fixing the choppiness had introduced a different set of tics. Subordination had
been bought with a handful of connectives used far past the rate at which the
literature uses them.

| tell | Section 10 draft | reference | ratio |
|---|---|---|---|
| "rather than" | 13.0 per 100 sentences | 0.5 | **26×** |
| "so that" | 12.3 | 0.8 | **15×** |
| em-dash | 6.2 | 0.5 | **12×** |
| "therefore" | 9.6 | 1.3 | **7×** |
| "precisely"/"exactly" | 6.2 | 0.0 | — |
| pseudo-cleft ("what X does is…") | 4.1 | 0.0 | — |
| mid-sentence colon | 11.6 | 7.4 | 1.6× |

Nineteen instances of "rather than", eighteen of "so that", fourteen of
"therefore". Forty-five sentences ran over 40 words and twenty-five over 48, the
longest at 80.

## 11.2 Two moves, and the overshoot between them

The first correction cut the tells and split the long sentences, which
overshot in the opposite direction: mean sentence length fell to 21.4 words,
below even the original 21.7 that had prompted the complaint, with only four
sentences over 40 words against the reference corpus's sixty. Splitting is not
the only way to shorten a sentence, and used alone it restores the staccato.

The second correction merged roughly thirty over-split pairs using semicolons and
plain conjunctions, which had headroom (semicolons stood at 3.6 per 100 sentences
against the reference's 10.2). Final state:

| | original | pass 1 | pass 2 split | **final** | reference |
|---|---|---|---|---|---|
| mean words | 21.7 | 33.3 | 21.4 | **27.2** | 26.9 |
| median | 20 | 32 | 21 | **27** | 24 |
| under 12 words | 25% | 9% | 16% | **7%** | 11% |
| over 40 words | — | 45 | 4 | **19** | 60 |
| over 48 words | — | 25 | 0 | **5** | 34 |
| longest | — | 80 | 46 | **57** | 109 |

Tells, per 100 sentences, final against reference: em-dash 0.0 / 0.5;
mid-sentence colon 0.6 / 7.4; semicolon 6.9 / 10.2; "rather than" 1.1 / 0.5;
"so that" 0.6 / 0.8; "therefore" 0.6 / 1.3; pseudo-cleft 0.0 / 0.0;
"precisely"/"exactly" 1.1 / 0.0.

## 11.3 Colons

Zero mid-sentence colons remain in body prose. Two survive elsewhere and are
deliberate:

- **Table 1's footnote** carried one and has been rewritten to drop it.
- **Figure 1's caption** uses `Left:` and `Right:` as panel labels, which is
  standard figure-caption convention rather than a body-paragraph sentence.
  Retained; say the word and they go.

## 11.4 Wider tell sweep

Eighteen further patterns were scanned across all body prose. Every one returns
zero: "it is worth noting", "notably"/"importantly"/"crucially",
"moreover"/"furthermore"/"additionally", "delve"/"underscore"/"highlight"/"shed
light", "not only … but also", "in conclusion"/"overall"/"in summary",
"key"/"crucial"/"vital"/"pivotal", "when it comes to", "plays a role", "that
said", stacked hedges such as "may potentially", and "this suggests".

Three matches were inspected and kept, all being literal technical usage rather
than filler: "leverage" in "the extreme frequencies exert the greatest leverage
on a fitted slope"; "a range of" in "with a range of $23.6$ to $61.1$ percent",
a literal statistical range; and the two instances each of "rather than" and
"exactly", which are load-bearing ($\psi'(M/2)$ holding *exactly* under Gaussian
returns, and standardisation annihilating an affine correction *exactly*).

Sentence-opening and paragraph-opening distributions were checked for formulaic
repetition. Across 52 paragraphs no opening formula repeats. Bare-pronoun
sentence openers stand at 0, against 28 in the reference corpus, so the paper is
more conservative here than its models.

## 11.5 One defect caught by an assertion

A chained replacement in Section 4 dropped the word "optimum" from "the
asymptotic correlation at the optimum", because an earlier replacement in the
same run had already rewritten the surrounding text. The edit script asserted a
unique match on every replacement, the follow-up replacement found zero matches,
and the run aborted rather than writing a silently truncated sentence. Repaired
and verified in the rebuilt PDF.

## 11.6 Checks

Eleven checks, all against text extracted from the rebuilt PDF: the nine from
Section 10.5, plus **(10)** numbers, citation keys, equation labels and
`numbers.csv` citation symbols unchanged from the pre-revision baseline, verified
file-by-file across all ten source files, and **(11)** all 134 cited symbols
resolve to rows in `numbers.csv`. All pass. Build clean, no errors, no label
warnings. 14 pages, 13 excluding references.

---

# 12. Headings and formatting

Feedback: section and subsection titles read as machine-written ("What the result
is not"); the bold run-in headings under Section 3.5 terminate in a period rather
than a colon; check the rest of the formatting.

## 12.1 Heading convention, taken from the reference papers

Headings were extracted from the same three papers used for the prose pass. The
convention is uniform and specific. Every heading is a **noun phrase naming the
object under discussion**, in sentence case, with no rhetorical framing and no
negation: "A semimartingale framework", "Return-based estimation of integrated
variance", "The distribution of the range", "Properties of realized range-based
variance", "Construction of the estimator", "Asymptotic properties", "Finite
sample performance and noise robustness", "Empirical illustration", "Concluding
remarks". Nothing of the form "What X should be" or "Where X cannot be" appears
anywhere in the three papers.

Thirteen headings were renamed on that pattern:

| was | now |
|---|---|
| 2. Data and engineering | Data and sample construction |
| 2.3 Exclusions | Session exclusions |
| 3.1 The fit | Specification and estimation |
| 3.2 **What the exponent should be** | The sampling-theory reference |
| 3.3 The result | Fitted exponents |
| 3.4 Admissibility | Admissibility of the fits |
| 3.5 **What the result is not** | Candidate explanations for the departure |
| 4.2 The composition of $A M^{b}$ | Composition of $A M^{b}$ |
| 6. **Where the correction cannot be inserted** | Insertion into a regime classifier |
| 6.1 The observable | Shrinkage of the observable |
| 6.2 The observation equation | Noise in the observation equation |
| 6.3 **What is not tested** | Scope of the negative results |
| 7.2 Misclassification from a practitioner's own $\lambda$ | Misclassification at a median threshold |

Section 3.5 previously opened straight into its run-in headings, which worked
only because the old title set up a list of negations. A one-sentence lead now
carries that work.

## 12.2 Run-in headings

All ten now terminate in a colon. Four of them also carried the negation framing
and were renamed to neutral noun phrases, the rejection being what the text says
rather than what the label asserts. One was a full sentence rather than a label.

| was | now |
|---|---|
| **Not a grid artifact.** | **Grid dependence:** |
| **Not entirely pooling.** | **Pooling across calendar years:** |
| **Not a property of realized variance alone.** | **Alternative proxies:** |
| **Not heavy tails, and not a localized feature.** | **Heavy tails and localized features:** |
| **The mechanism is partial.** | **Partial mechanism:** |
| **Two correlated instruments.** etc. | **Two correlated instruments:** etc. |

Renaming "Not entirely pooling" is also more accurate than the original, since
pooling is the one candidate that is *partly* accepted, accounting for a mean
$36.0$ percent of the gap.

## 12.3 Rest of the formatting

Audited and corrected:

- **Table float placement.** Tables 2 and 3 used `[htbp]` and `[t]`. Both now
  `[htbp]`. Table 1 keeps `[!ht]`, which is deliberate: it is the whole content of
  Section 5 and must not float out of it.
- **Table sizing.** Table 3 was set at body size while Tables 1 and 2 were
  `\footnotesize`. All three are now `\footnotesize`.
- **Table 2 column headers** mixed capitalized and lowercase entries
  ("interval", "reference", "cond."). Now capitalized consistently, with "cond."
  expanded to "Condition", and the caption gained a sentence saying what RMSE and
  the condition number describe.

Audited and found already consistent, so left alone:

- **Equation references.** "Equation~(5)" is capitalized at sentence start and
  lowercase mid-sentence throughout, which is the standard rule. All four
  instances already followed it.
- **Display-equation punctuation.** Each display carries the punctuation its
  sentence requires — comma where the sentence continues into a subordinate
  clause, period where it ends, nothing where the syntax runs straight on. All
  eight already correct.
- **Cross-reference style.** `Section~\ref`, `Table~\ref`, `Figure~\ref`
  uniformly, with non-breaking spaces. No prose describes a section by a title
  that has now changed, since every cross-reference resolves through `\ref`.
- **Figure captions.** `Left:` and `Right:` panel labels retained as standard
  figure-caption convention.

## 12.4 Checks

Fifteen checks against the rebuilt PDF. The eleven from Section 11.6, plus:

| # | Check | Result |
|---|---|---|
| 12 | Headings uniformly sentence case | PASS (24 headings) |
| 13 | All run-in headings end in a colon | PASS (10 headings) |
| 14 | Table float specs consistent | PASS |
| 15 | All tables `\footnotesize` | PASS |

Two of these initially reported FAIL against the document, and both were bugs in
the checking scripts rather than in the paper. The heading regex treated the `M`
of `$A M^{b}$` as a title-cased word, and the `\paragraph{...}` capture used
`[^}]*`, which terminates at the inner brace of `^{b}` and so never saw the
trailing colon. Both were rewritten with balanced-brace parsing and math
stripping, after which the document passed. Recording this because the first
result was a false alarm, not a fix.

Build clean, no errors, no label warnings. 14 pages, 13 excluding references.

---

# 13. Paragraph spacing and the kill-conditions table

## 13.1 Paragraph spacing

`\parskip` was zero, the article-class default, so consecutive paragraphs were
separated by nothing but a first-line indent. Set to `5pt plus 1.5pt minus 1pt`
with the indent retained, which is the conservative choice: dropping the indent
for a full block style would have changed the document's register rather than
just its spacing.

## 13.2 The table: what was actually wrong

The page was rendered to an image and inspected rather than reasoned about from
source, which is how the first defect was found. Three separate faults:

**Text printing on top of adjacent text.** The Determination column was
`p{2.3cm}`, and `INDETERMINATE` is wider than that. LaTeX cannot break an
unhyphenated word, so it set the word overfull and let it run into the Margin
column, printing over the text there. The build log had been carrying the
evidence all along, as two `Overfull \hbox (15.8691pt too wide)` warnings on the
K1 and K10 rows. Nothing had ever grepped the log for overfull boxes.

**Stretched interword spacing.** The `p{}` columns justify by default, and in
measures this narrow that produced gaps wide enough to read as broken alignment:
"sizing&nbsp;&nbsp;&nbsp;&nbsp;consequence null", "DOES&nbsp;&nbsp;&nbsp;&nbsp;NOT FIRE",
"stop-out FIRES;&nbsp;&nbsp;&nbsp;&nbsp;cap UNTESTED".

**Hyphenation shredding words** at these widths: "estima-tor",
"misclassifi-cation", "combi-nation", "at-tenuation".

## 13.3 Fixes

- **`\raggedright` in all three text columns**, via `array` and
  `>{\raggedright\arraybackslash}p{...}`. This removes both the stretched spacing
  and most of the hyphenation, since ragged setting does not need to pad lines.
- **Determination widened** from `2.3cm` to `3.0cm`, taken from the available
  slack rather than from Content. Both `INDETERMINATE` and `DOES NOT FIRE` now
  set on one line. Content `3.3cm`, Margin `4.3cm`.
- **Soft-hyphen hints** on `INDETERMINATE` and `UNTESTED` as a safety net, so
  neither can ever overflow again if the column is narrowed later. These are
  discretionary hyphens inserted at render time and inert unless a break is
  needed; the values in `k_table.csv` are untouched.
- **`\abovetopsep` set to 6pt.** The caption's last line was sitting directly on
  the `\toprule`, so the rule read as an underline on the caption text.
- **`\arraystretch` 1.15** for row separation, and `@{}` on the outer columns so
  the rules align flush with the first and last column.

Result: **zero overfull boxes in the document**, against two before.

## 13.4 Three unreferenced floats

Cross-checking every `\label` against every `\ref` turned up three floats that
the text never pointed at: the exponent table, the kill-conditions table, and
Figure 1. A float that is never referenced is a defect regardless of how it
looks.

- Section 3.3 now opens by referring to `Table~\ref{tab:exponent}` and
  `Figure~\ref{fig:scaling}`.
- The kill-conditions table is referenced from the **introduction**, not from
  Section 5, so that the Section 5 stub stays untouched per item 131.

Unreferenced `\label`s on sections themselves were left alone; those are
available anchors, not defects.

## 13.5 A numbering note

DECISIONS item 139 and Sections 10 through 12 of this report call the
kill-conditions table "Table 1". **In the built document it is Table 2**, because
the exponent table in Section 3 comes first. No cross-reference is affected,
since every reference resolves through `\ref`, but the report's wording and the
document's numbering do not match, and the document is right.

## 13.6 Checks

Eighteen checks, all passing. The fifteen from Section 12.4, plus:

| # | Check | Result |
|---|---|---|
| 16 | Zero overfull boxes | PASS (0 overfull, 9 underfull) |
| 17 | Every table and figure referenced in text | PASS (5 floats) |
| 18 | `\parskip` set | PASS |

Check 10 (numbers, citations, labels and symbols unchanged) initially reported
FAIL on `05_conditions_table.tex` and `main.tex`. Both were the comparator
counting layout dimensions — `3.0cm`, `5pt`, `1.15` — as data. Re-run with
dimensions, column specs and `\setlength` arguments excluded, all ten files hold
on data numbers, citation keys, labels and `numbers.csv` symbols. This is the
second time a check has cried wolf on the paper, so it is worth being explicit:
nothing in the data changed in this pass, and the failures were in the checking
code.

Build clean, no errors, no label warnings, no overfull boxes. 14 pages, 13
excluding references.
