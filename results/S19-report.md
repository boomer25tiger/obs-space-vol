# Session 19 — Paper repair and completion

No measurement. No holdout read. Nothing dated on or after 2024-01-01 was read.
DECISIONS items 66–132 verified present at lines 398–796 (67 of 67); items 133–136
appended and verified at lines 803, 808, 814, 819. Interpreter gate PASS
(numpy 2.5.2, pandas 3.0.5, outside every synced path).

---

## Phase 2 could not be executed: the Section 3 text was not supplied

The brief reads `[Section 3 text as drafted, supplied separately with this
prompt.]` and no text followed. `paper/sections/03_exponent.tex` contains only the
S18 stub. The stop condition is explicit — *do not rewrite the supplied Section 3
prose, convert and verify only* — and there is nothing to convert. **Section 3
remains a stub.** I did not write it, because writing it would be the one thing
the phase forbids.

This is the second session in which Section 3 was described as supplied and was
not. Sections 1 and 2 were drafted to the register of the sections written in S18,
which were written to the same specification the brief gives for Section 3.

---

## Phase 1: numbers re-read

Item 134's "three figures for one quantity" are **three different quantities**,
not a contradiction. All are correct sums over different row sets of
`sessions/s17-emission/results/phase3_a4_insample.csv`, which holds 35 rows: 32
extended-range (8 cells × 4 scalings) and 3 restricted-range.

| figure | what it actually is |
|---|---|
| **18,311** | in-sample, extended range, **scale 1.00 only** — the headline scaling, and what S17's report cited |
| 20,382 | in-sample, extended, summed over all four scalings |
| 20,462 | all 35 rows, mixing two λ ranges — **the S18 draft's figure** |
| 1,183 | *holdout*, extended, all four scalings (0+20+272+891) — a different sample |

Floor binding, same artifact, fields `n_windows_binding` / `n_windows`:

| scaling | binding | denominator | share |
|---|---|---|---|
| 0.25 | 22,033 | 72,619 | 30.3% |
| 0.50 | 34,276 | 72,619 | 47.2% |
| 0.75 | 49,723 | 72,619 | 68.5% |
| **1.00** | **46,120** | **72,619** | **63.5%** |
| all four | 152,152 | 290,476 | 52.4% |
| all 35 rows | 153,613 | 294,906 | 52.1% |

**Table 1 was right and Section 6.2 was wrong.** The "63%" in Table 1 is the
headline-scaling figure, 63.5%. The "153,613 of 294,906" in Section 6.2 sums the
denominator across four scalings, counting the same 72,619 windows four times, and
adds a fourth λ range. It is arithmetically correct and substantively meaningless.

Screen counts (`sessions/s10-exponent-audit/results/phase2_screen.csv`, field
`screen_tight_pass`): **12 futures cells, 2 SPY venues, 14 combined**; the 12
futures are **6 distinct cells** under two boundary treatments that give identical
fits.

Gap-to-standard-error ratio (`phase1_bootstrap.csv`, fields `b`,
`b_trigamma_ref`, `b_se`): median gap **0.5169**, median SE **0.0536**, ratio
**9.65**.

### Corrections applied

| location | old | new |
|---|---|---|
| Sec 6.2, states moved | 20,462 | **18,311** |
| Sec 6.2, floor binding | 153,613 of 294,906 | **46,120 of 72,619, 63.5%** |
| Sec 4.1, gap vs SE | "roughly ten times" | **0.5169 against 0.0536, a ratio of 9.6** |
| Fig 1 left-panel title | "14 cells" | **"twelve cells"** |
| Sec 2, SPY sessions | 1,415 asserted | **1,427 in the extract, 1,415 analysed** — both stated |

`paper/numbers.csv` grew from 691 to **715 rows**. Three rows are marked
`superseded` (`k12_windows_binding`, `k12_windows_total`,
`k12_states_differ_insample`) with the reason recorded; 12 corrected or
disambiguated rows and 12 data-engineering rows were added. Disagreements are
tabulated in `results/S19-disagreements.md`.

One disagreement was found that item 134 did not flag: Section 2 asserted 1,415
SPY sessions, while `phase1_spy_span.json` reports 1,427 pre-2024 RTH sessions and
`phase6_spy_grid_ARCX.csv` reports 1,415 windows analysed. Both are artifact
values measuring different things. Neither was chosen; the text now states the
reconciliation and both are in `numbers.csv`.

---

## Phase 3: Sections 1, 2 and the abstract

Written. Abstract is **146 words**. Section 1 states the reliability coefficient,
that it is universally computed rather than measured, the exponent result, the
estimator with its bound-violation counts against both conventional alternatives,
and the first-order criterion with two application figures. Section 2 gives the
instruments, sample, session counts, both session geometries, the two-venue SPY
caveat, the sampling grids, and the four exclusion rules — with the statement that
no exclusion is conditioned on a realized quantity and why, including the earlier
revision that violated it.

---

## Phase 5: bibliography

Eleven entries, **ten fully verified against a source**, one partially.

| entry | verified | source |
|---|---|---|
| Blake, Gandhi, Jakkula 2025 | title, all three authors with initials, date, arXiv id | arxiv.org/abs/2510.03236 |
| Barndorff-Nielsen, Hansen, Lunde, Shephard 2008 | Econometrica 76(6) 1481–1536 | econometricsociety.org, Wiley |
| Barndorff-Nielsen, Shephard 2002 | JRSS-B 64(2) 253–280 | Oxford Academic, Wiley |
| Zhang, Mykland, Aït-Sahalia 2005 | JASA 100(472) 1394–1411 | Taylor & Francis |
| Corsi 2009 | J. Fin. Econometrics 7(2) 174–196 | Oxford Academic |
| Andersen, Bollerslev, Diebold, Labys 2001 | JASA 96(453) 42–55 | Taylor & Francis |
| Patton 2011 | J. Econometrics 160(1) 246–256 | ScienceDirect, RePEc |
| Bollerslev, Patton, Quaedvlieg 2016 | J. Econometrics 192(1) 1–18 | ScienceDirect, RePEc |
| Hansen, Lunde, Nason 2011 | Econometrica 79(2) 453–497 | Wiley, Econometric Society |
| Cameron, Gelbach, Miller 2008 | REStat 90(3) 414–427 | MIT Press |
| **Brockhaus, Long 2000** | author, title, *Risk*, January 2000 verified; **page range NOT verified** | risk.net; sources give 92–96, 92–95 and 92–93 |

The Brockhaus and Long entry is included **without page numbers**, with a `note`
recording that the range could not be verified. Title, authors, venue and year are
all confirmed, so the entry is not a guess; only the pages are omitted.

**Two entries were dropped**: Gatheral, Jaisson and Rosenbaum, and Cont and Das.
Both appeared in the S18 bibliography, neither is cited by name in any drafted
section, and I did not verify them. They can return when Section 3 or a roughness
discussion cites them.

The S18 Blake entry, `Regime detection in realized volatility with hidden markov
models, 2025`, was wrong in title and gave no author initials. Corrected per item
135 and confirmed against arXiv.

---

## Phases 4 and 6: repairs and formatting

- Hard equation numbers replaced with `\eqref`. The scaling fit is `eq:scaling`
  and the convexity relation `eq:kvol`; the collision is resolved.
- Kill conditions renumbered **K1–K13** for publication with a `\footnotetext`
  mapping paper numbering to session numbering, and the session label retained as
  its own column (item 136).
- Figures placed `[htbp]`; `\clearpage` before the bibliography.
- `booktabs` already loaded; table rules are `\toprule` / `\midrule` / `\bottomrule`.
- The literal `\%` in the Figure 2 annotation is removed — matplotlib is not in
  LaTeX mode there and was printing the backslash.
- **`2^7` was already correct** as `$2^{7}$` in the source; the audit found no bare
  `2^7`, no stray underscores, and no lost subscripts. `\operatorname{Var}(\log
  RV_M)`, `\sigma_k^2` and `\text{total}_k` all render as intended. The six audit
  hits on `RV_M` are legitimate math-mode subscripts.
- `microtype` remains omitted: it is not installed in this TeX distribution.

---

## Phase 7: build

| | |
|---|---|
| build | pdflatex ×3 + bibtex, **0 undefined references or citations**, bibtex rc 0 |
| output | `paper/main.pdf`, 290,373 bytes, **10 pages** |
| **page count excluding references** | **9** |
| section spans | 1: p.1, 2: pp.2–3, 3: p.3 (stub), 4: pp.3–4, 5: pp.4, 6: pp.4–6, 7: pp.6–7, 8: pp.7–8 |
| floats | Table 1 p.5, Table 2 p.6, Figures 1–2 p.9 |
| **no float after `\clearpage`** | **confirmed** — last float p.9, references p.10 |

### Citation-coverage defects

The mechanical audit flags **60 lines** carrying a numeric token without a
`numbers.csv` comment on the same line. Inspection separates these into three
kinds, and I am reporting the count rather than claiming coverage:

- **Continuation lines** — a claim spanning two or three source lines with the
  citation on the last. The majority.
- **Pure notation** — `$2/M$`, `$(0,1]$`, `$\lambda > 0$`,
  `$\sigma_k^2 = \max(\text{total}_k - v, 0)$`. Not claims.
- **Genuine gaps** — Section 2 had 19 such lines because its data-engineering
  counts were never extracted in S18. **Fixed**: 12 rows added to `numbers.csv`
  from the S03, S04 and S07 artifacts and 9 citation comments added.

The residual is a formatting property of multi-line claims, not an uncited number.
Making it mechanically clean requires one claim per source line, which would
damage the prose; I have left it and reported it.

---

## Remaining MISSING quantities

Eleven, unchanged from S18, all substantive rather than lookup failures: eight
`lambda[·/restricted_S05]` entries undefined at the RTH intraday cells because the
restricted grid has one point against three parameters, and three
`freq_required_min` entries where no grid frequency brings the convexity bias
below 5%. Both are reported as findings in Sections 4 and 7.

---

## Timing

Phase 0 ~4 min; Phase 1 ~11 min; Phase 2 blocked, ~2 min to confirm; Phase 3
~19 min; Phases 4 and 6 ~14 min; Phase 5 ~16 min including ten verification
lookups; Phase 7 ~9 min across three builds; Phase 8 ~10 min. **Roughly 85
minutes**, inside the 45–90 expectation.
