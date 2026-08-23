# S23 report, log corrections and first commit

**The session halted before Phase 5. Nothing was committed and nothing was pushed.**
Two independent stop conditions fired: four of the six Phase 3 paper checks failed, and
the Phase 4 audit flagged content that the stop conditions forbid committing. Phases 0
through 4 completed and are reported in full.

## Phase 0

| check | result |
|---|---|
| Interpreter | `~/venvs/obs-space-vol/bin/python` |
| numpy / pandas | 2.5.2 / 3.0.5, both matching |
| Physical path | `<REPO>`, not under a known sync root |
| `DECISIONS-as-run.md` digest | `e0ff2520dd484b3d816f6eea1f98b73ce0bd6687ad4b93624d3600d45317411e` |
| Digest matches the recorded value | **yes**, so the S22 verifications stand |

`DECISIONS.md` before this session: 155 entries, highest number 148, numbers 141 to 143
absent. Ten reused numbers, each occurrence located:

| item | first occurrence | second occurrence |
|---|---|---|
| 13 | line 91 | line 112 |
| 14 | line 99 | line 119 |
| 15 | line 101 | line 123 |
| 51 | line 285 | line 322 |
| 52 | line 291 | line 328 |
| 53 | line 296 | line 332 |
| 54 | line 299 | line 335 |
| 55 | line 306 | line 341 |
| 56 | line 310 | line 347 |
| 57 | line 317 | line 353 |

Item 149 appended and verified present at line 898 under a new S23 header.

## Phase 1, item 144

Corrected to "Entries 1 through 140", with `[S23: corrected from "143" per item 149.]`
placed at the end of the entry, matching where items 55 and 79 carry their S22 markers.

**A knock-on correction was required and is reported rather than made silently.** Item
147 read "Item 144's own phrase ... **is left as supplied** and is inaccurate on that
point." Correcting 144 made that sentence false. Item 147 now reads "was left as supplied
and inaccurate on that point" followed by `[S23: superseded, the phrase was corrected per
item 149.]`.

Every range and count asserted anywhere in the file was then audited. Three occurrences of
"1 through 143" remain, at items 147 and 149, and all three are **quotations of the
erroneous phrase in the course of describing it**, not assertions. No entry now asserts a
range or count the file does not support.

## Phase 2, header note

The header already carried a sentence on the item-number collisions, but it read "for the
same reason", conflating them with the K-series collisions. Replaced with a sentence that
separates them explicitly:

> Separately, and different in kind, ten item numbers are themselves reused: 13, 14, 15
> and 51 through 57 each appear twice, in every case with the second occurrence revising
> the first, and both occurrences are preserved as run.

The K-series sentence is untouched and still precedes it.

## Phase 3, paper verification — FOUR OF SIX FAILED

| # | check | result | what is present instead |
|---|---|---|---|
| 1 | Section 3.5 carries the dispersion calibration caveat | **FAIL** | Neither sentence exists anywhere in `paper/`. Section 3.5 is "Candidate explanations for the departure", four run-in paragraphs on grid dependence, pooling, alternative proxies, and heavy tails. No calibration caveat. |
| 2a | Section 5 non-empty | **FAIL in substance** | 282 words render between headings 5 and 6, but every one of them is Table 2's caption and footnote. There is no body text. |
| 2b | Section 5 has subsections 5.1 to 5.5 | **FAIL** | Zero subsections. The document's only subsections are 2.1–2.3, 3.1–3.5, 4.1–4.2, 6.1–6.3 and 7.1–7.3. |
| 2c | Table 2 sits inside Section 5 | **PASS** | Heading and table both on page 8. |
| 3a | Byline reads Cristian Gualy | **FAIL** | `main.tex` line 15 is `\author{}`. The paper has no byline. |
| 3b | `\date{}` carries the commit date | **FAIL** | `main.tex` line 16 is `\date{}`. Empty. |

Section 5 remains the stub that DECISIONS item 131 specifies, its source still carrying
the `% STUB. Section 5 is not drafted in S18` comment.

### There is no S21

The brief asks to confirm "the S21 insertions landed". **No session numbered S21 was ever
run.** There is no `sessions/s21-*` directory, no `results/S21-*` artifact, no S21 report,
and no mention of S21 in `DECISIONS.md` or `DECISIONS-as-run.md`. The three insertions the
brief describes were never made by any session.

The label appears twice in the repository, both times attached to the post-S20 prose and
formatting revision, which was recorded as sections 10 through 13 of
`results/S20-report.md` rather than as a session of its own:

- `paper/sections/03_exponent.tex:10` — `% Prose revised in S21 to the register of the realized-variance literature.`
- `paper/numbers.csv`, four rows carrying the note `registered in S21 prose pass`.

That work happened. The three insertions named in Phase 3 did not.

## Phase 4, pre-commit audit

`.gitignore` extended with `*.parquet`, `*.zst`, `*.npz`, `*.npy`, `cache/` at any depth,
and `.venv-broken-20260819/`, alongside the existing raw-data, environment and build-product
rules.

| measure | value |
|---|---|
| Whole tree | 4.1 GB |
| `.venv` / `.venv-broken-20260819` | 510 MB / 441 MB, excluded |
| Cache directories | 1.5 GB, excluded |
| `data/` raw vendor files | 183 MB, excluded per item 130 |
| **Candidate tracked set** | **574 files, 15.8 MB** |
| Files over 10 MB | **none** |
| Files over 50 MB | **none** |

Ten largest candidate files:

| size | path |
|---|---|
| 2.33 MB | `sessions/s01-estimator-validation/results/S01-cells.csv` |
| 0.79 MB | `sessions/s06r-repair/results/phase1_invariants_on_s05.csv` |
| 0.67 MB | `sessions/s05-reliability-mcs/results/s05_partc.csv` |
| 0.66 MB | `sessions/s01-estimator-validation/results/S01-report.md` |
| 0.61 MB | `sessions/s05-reliability-mcs/results/s05_parta.csv` |
| 0.52 MB | `sessions/s01-estimator-validation/logs/progress.jsonl` |
| 0.48 MB | `sessions/s05a-reproducibility/results/S05A-mcs-per-seed.csv` |
| 0.46 MB | `sessions/s04-repairs-diagnostics/results/s04_diagnostics.json` |
| 0.38 MB | `paper/main.pdf` |
| 0.33 MB | `sessions/s05b-defect-and-estimator-audit/results/phase2_offending_observations.csv` |

Untracked paths and their sizes: `.gitignore` 4K, `DECISIONS-as-run.md` 64K,
`DECISIONS.md` 68K, `ENVIRONMENT-pre-20260819.md` 8K, `ENVIRONMENT.md` 4K, `README.md` 8K,
`figures/` 68K, `paper/` 756K, `requirements.lock` 4K, `requirements.txt` 4K, `results/`
240K, `sessions/` 2.7G before exclusions, `specs/` 72K.

### Secrets and PII scan — FLAGGED

| class | result |
|---|---|
| API keys, secrets, tokens, passwords, private keys | **none** |
| Databento or vendor account identifiers | **none** |
| Real email addresses | **none**. The one match is the placeholder `git@github.com:<user>/<repo>.git` in `results/S18-report.md:148` |
| **Absolute home-directory paths** | **391 occurrences across 56 files** |

The home-path exposure is spread across the repository, not confined to the two entries
item 145 generalised:

| area | files |
|---|---|
| `sessions/s07-completion-and-spy` | 10 |
| `sessions/s09-application` | 6 |
| `sessions/s06r-repair` | 4 |
| `results/` | 4 |
| fourteen other session directories | 2 each |
| `specs/`, `s09pre`, `s05d`, `s05e`, `s05a` | 1 each |
| root: `ENVIRONMENT.md`, `ENVIRONMENT-pre-20260819.md`, `DECISIONS-as-run.md` | 3 |

Every occurrence embeds the string `~`, so a public push publishes the
author's account name and local directory layout 391 times. The stop condition reads "Do
not commit anything the Phase 4 audit flags. Report and stop."

`DECISIONS-as-run.md` is a deliberate exception: it is the unmodified record, item 145
documents its two paths, and the stop conditions forbid editing it. The other 55 files
carry no such exemption and were never reviewed for this.

## Phases 5 and 6, not run

No `git init` was needed, the repository already existed on branch `main` with **0
commits** and **0 remotes**. The configured author is `boomer25tiger`, not Cristian Gualy.

Beyond the two triggered stop conditions, Phase 6 is also underdetermined: **the brief does
not give the remote URL**, and asks to "report the remote URL to be added" without
supplying one. No remote can be added without it.

## What has to happen before this session can be re-run

1. Make the three Phase 3 insertions, or drop them from the brief: the Section 3.5
   calibration caveat, Section 5's body and subsections 5.1 to 5.5, and the byline and date
   in `main.tex`.
2. Decide the home-path question. Either scrub `~` from the 55 non-exempt
   files, or state that publishing it is acceptable and lift the Phase 4 stop condition.
3. Supply the GitHub remote URL.
4. Confirm whether the git author should be changed from `boomer25tiger` to Cristian Gualy
   globally or only for this repository.

## Files changed in this session

| file | change |
|---|---|
| `DECISIONS.md` | item 149 appended; item 144 corrected in place with S23 marker; item 147 superseded-sentence marked; header collision sentence rewritten; three overlong lines reflowed. 156 entries, highest number 149. |
| `.gitignore` | six exclusion rules added |
| `results/S23-report.md` | this file |

`DECISIONS-as-run.md` untouched, digest unchanged.
