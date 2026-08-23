# Session 18 — Paper draft and repository build

No measurement was performed. The holdout was not read. Nothing dated on or after
2024-01-01 was read. Every figure in the draft is read from a persisted artifact
and every numeric claim cites its row in `paper/numbers.csv` as a LaTeX comment on
the same line.

Interpreter `~/venvs/obs-space-vol/bin/python`, numpy 2.5.2, pandas
3.0.5, outside every synced path. DECISIONS items 66–128 verified present at lines
398–777 (63 of 63); items 129–132 appended and verified at lines 783, 789, 793,
796.

---

## Build outcome

| | |
|---|---|
| engines available | pdflatex, xelatex, lualatex (TeX Live 2023), latexmk 4.81; **tectonic absent** |
| minimal verification build | rc 0, 2 s, 95,035 bytes, 1 page, with equation, multi-column header, figure and resolved citation |
| final build | **rc 0**, 3 passes plus bibtex, **0 undefined references or citations** |
| output | `paper/main.pdf`, 249,454 bytes, **8 pages** |
| pandoc | not used |

Two build failures were hit and fixed. `microtype.sty` is not present in this TeX
installation and was dropped — it is purely cosmetic. `bibtex` exited 2 on the
arXiv entry because I had written the author field with trailing commas; the entry
now carries surnames only, which is all DECISIONS item 116 records.

### Page count

Eight pages total, against a six-page target excluding references.

| section | pages |
|---|---|
| 1 Introduction (stub) | 1 |
| 2 Data (stub) | 1 |
| 3 Exponent (stub) | 1 |
| 4 Estimator | 1–2 |
| 5 Kill conditions (stub + generated table) | 2–3 |
| 6 Where the correction cannot be inserted | 2–4 |
| 7 Practical implications | 4–5 |
| 8 Limitations | 5–6 |
| Figure 1, Figure 2 (full width, floated) | 7–8 |
| References | 8 |

The drafted prose and tables occupy pages 1 through 6, which meets the target. The
overrun is the two full-width figures, which float to pages 7 and 8, with the
bibliography sharing page 8. **Nothing was cut.** The count is not yet informative:
four of eight sections and the abstract are stubs, so the body will grow.

---

## MISSING quantities

`paper/numbers.csv` holds **691 rows**. Eleven are MISSING, listed in full in
`results/S18-missing.csv`. **None is a lookup failure — all eleven are substantive
absences, and each is a result in its own right.**

| quantity | count | why absent |
|---|---|---|
| `lambda[·/restricted_S05]` and `lambda_theory[·/restricted_S05]` at ES/RTH 1h, ES/RTH 30min, NQ/RTH 1h, NQ/RTH 30min | 8 | On the restricted grid these cells carry one grid point against three fitted parameters, so λ is undefined. This is the item-66 finding and is reported as such in section 4. |
| `freq_required_min` at ES/RTH 1h, ES/RTH 30min, NQ/RTH 30min | 3 | No sampling frequency in the grid brings the convexity bias below 5%. Reported as "unreachable" in Table 2 of section 7. |

Two genuine lookup failures were found and fixed during extraction rather than
left as MISSING: the S05E trigamma reference uses column `free_b` not `b`, and the
localized-feature bound lives in S14 not S13. Both were traced to the correct
artifact and the values read.

---

## Discrepancies between the brief and the artifacts

Three, all resolved in favour of the artifacts.

**"The fourteen futures cells passing the screen."** The screen artifact gives
**12 futures cells and 2 SPY venues, 14 in total**. The four RTH/30min cells fail
on grid size (5 points against a 6-point requirement). Figure 1 plots 12 futures
in its left panel and both SPY venues in its right, and the caption states the
split. The 12 futures cells are 6 distinct cells under two boundary treatments
that give identical fits, which the caption also states.

**`paper/sections/03_exponent.tex` was described as supplied and is the register
model.** It was not present in the working tree at Phase 0 and `paper/` did not
exist. No approved outline file was present either. Sections 4, 6, 7 and 8 were
drafted against the register described in the brief — first person plural, result
stated with its value before it is characterised, assumptions referenced by
number, no signposting, uncomfortable results stated with their mechanical
explanation and the innocent reading dismissed by a count where the count supports
dismissal. Sections 1, 2 and 3 are stubs carrying a comment recording this.

**The S12 trend-control artifact.** The brief located it at
`sessions/s12-correction/results/phase3_trend_control.csv`; it is at
`sessions/s15-confounds/results/phase3_trend_control.csv`. Read from there.

---

## Sections where the outline required a quantity no artifact contains

None. Every quantity the outline enumerated was located, with the eleven
substantive absences above, each of which is itself a measured finding rather than
a gap.

One quantity was sourced from `DECISIONS.md` rather than a CSV: the holdout read
count of seven, which is recorded in items 72, 88, 105, 110, 121 and 128 rather
than emitted by any measurement script. It is entered in `numbers.csv` with that
provenance.

---

## Figures

| figure | artifacts read | rows | computed |
|---|---|---|---|
| Figure 1 | S08 `phase4_lambda.csv` (128), S10 `phase1_bootstrap.csv` (18), S10 `phase2_screen.csv` (34), S07 `phase6_spy_grid_{ARCX,XNAS}.csv` (16 each) | as listed | `c + A·M^b` from parameters read from the fits artifact, and trigamma(M/2). Nothing else. |
| Figure 2 | S14 `phase1_k8_rates.csv` (8), S09 `phase3_sizing_params.csv` (32) | 4 cells marked | `arccos(√λ)/π` over a λ grid. All plotted points read from artifacts. |

Each script writes a provenance JSON recording paths and row counts.

---

## Repository

Initialised. Not committed and not pushed.

| | |
|---|---|
| files tracked after exclusions | **569** |
| tracked size | **14 MB** |
| working tree | 4.1 GB |
| excluded: raw Databento | 183 MB |
| excluded: session caches | 1.3 GB |
| excluded: derived panels, bar tables, `results/raw/` | ~1.2 GB |
| excluded: virtual environments | 951 MB |

`.gitignore` excludes raw vendor data and every derived binary regenerable from
it — `.npz`, `.npy`, `.parquet`, `results/raw/`, `results/cache/`, `p4tmp/` — while
tracking every CSV and JSON artifact the paper cites. The largest tracked file is
`sessions/s01-estimator-validation/results/S01-cells.csv` at 2.3 MB.

To add a remote and push, the user would run:

```bash
cd <REPO>
git add -A
git commit -m "Observation-space volatility evaluation: measurement, audit trail and paper draft"
git branch -M main
git remote add origin git@github.com:<user>/<repo>.git
git push -u origin main
```

I have not run any of these. Note that `git add -A` on the full tree before
`.gitignore` was in place began staging the 604 MB Phase-0 extract and had to be
reset; the exclusions are now in place and the same command stages 14 MB.

---

## Timing

| phase | wall clock |
|---|---|
| 0 verification, append, directories | ~4 min |
| 1 engine check and minimal build | ~3 min |
| 2 figure generation | ~2 min |
| 3 number extraction, two lookup fixes | ~14 min |
| 4 drafting sections 4, 6, 7, 8 and the section 5 table | ~28 min |
| 5 assembly, two build failures, bibtex cycle | ~13 min |
| 6 repository, four rounds of exclusion refinement | ~22 min |
| 7 report | ~10 min |

Roughly 100 minutes against a 45–90 minute expectation, under the 120-minute
threshold. Nothing was dropped. The two largest overruns were the repository
phase, where the exclusion set had to be refined four times because 1.4 GB of
derived binaries sat in `results/` rather than in `cache/`, and one `git add -A`
that timed out at ten minutes against the unexcluded tree.
