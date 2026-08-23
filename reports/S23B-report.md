# S23B report, paper insertions, path scrub and first commit

Phases 0 through 5 completed. **Phase 6 did not run: the remote does not exist on
GitHub, and creating a public repository was not authorised.** Four commits are made
locally and are ready to push.

## Phase 0

| check | result |
|---|---|
| Interpreter | `~/venvs/obs-space-vol/bin/python` |
| numpy / pandas | 2.5.2 / 3.0.5, matching |
| Physical path | not under a known sync root |
| `DECISIONS-as-run.md` digest | `e0ff2520dd484b3d816f6eea1f98b73ce0bd6687ad4b93624d3600d45317411e`, **matches** |

Before this session: 156 entries, highest number 149, gaps at 141 to 143, ten reused
numbers (13, 14, 15, 51 to 57). Items 150, 151 and 152 appended and verified at lines
910, 916 and 922.

## Phase 1, Section 3.5

**The anchor sentence in the brief is not in the file.** The brief specifies inserting
after a sentence ending "so the mechanism is established for one geometry and partial for
the other". The paper reads "The mechanism is established for one session geometry and
only partial for the other" — reworded during the post-S20 prose revision. Per the
brief's fallback, the sentence that ends Section 3.5's mechanism paragraph is:

> The roughness of the within-window path, as distinct from its dispersion, moves the
> exponent by less than its own between-seed dispersion and cannot account for the
> residual.

The caveat was inserted after that sentence. Converted verbatim, checked
character-for-character against the supplied text: **identical**.

## Phase 2, Section 5

`paper/sections/05_kill.tex` written from the supplied text, the `% STUB` comment removed,
`main.tex` repointed from `05_conditions` to `05_kill`, and the superseded
`05_conditions.tex` deleted. Verbatim check on the opening block and six probe phrases:
**all identical**.

### Numeric verification

Every claim was checked against `numbers.csv` and against Table 2's source artifacts.
**No disagreements.** Six claims had no `numbers.csv` row and were verified directly
against the artifact, then registered:

| claim in the text | artifact value | source |
|---|---|---|
| cap would first bind at 1.434 | `1.4340665802401198` | `phase4_k4.json` `leverage_cap.cap_that_would_first_bind` |
| composition differs in 20.8 percent | `0.20833333333333331` | `phase12_summary.json` `excess_rth` |
| 12.5, 43.8 and 6.3 percent | `0.125`, `0.4375`, `0.0625` | `phase12_summary.json` `by_horizon[*].excess` |
| reliability 1.001, 0.856, 0.713 | `1.000855026167171`, `0.8562407799831788`, `0.7130945742582158` | `phase12_summary.json` `by_horizon[*].lam_intercept` |
| eight before, five fire | 8, 5 | `k_table.csv` `chosen`/`determination` |
| five after, three material | 5, 3 | `k_table.csv` `chosen`/`determination` |

Twelve rows added to `numbers.csv`, now 738. Every numeric line in Section 5 carries a
citation comment.

**One qualitative statement worth flagging, left verbatim as instructed.** The text says
the placebo subtraction means "the raw effect is roughly half subset variation". The
artifact gives a raw clean-geometry rate of 0.6875 and a placebo rate of 0.4792, so the
placebo accounts for about 70 percent of the raw rate, not half. It carries no figure, so
it is not a numeric claim, and the stop condition forbids rewriting supplied text. Noted
for the author.

## Phase 3, byline and build

`\author{Cristian Gualy}`, `\date{22 August 2026}`. Build clean: no errors, no undefined
or multiply-defined labels, **zero overfull boxes**.

| # | check | result |
|---|---|---|
| 1 | Section 3.5 carries the caveat | **PASS**, opening and closing sentences both present |
| 2a | Section 5 has subsections 5.1 to 5.5 | **PASS**, all five |
| 2b | Section 5 is not a stub | **PASS**, 1,080 words between headings 5 and 6 |
| 2c | Table 2 sits inside Section 5 | **PASS**, heading 5 p8, Table 2 p9, heading 6 p10 |
| 3a | Byline renders | **PASS** |
| 3b | Date renders | **PASS** |

Two checks failed on the first build and both were fixed rather than reported away.
**Table 2 floated to page 10, past heading 6 on page 9**, because Section 5 now has body
text where before it had none; the table input was moved to follow the paragraph that
references it. Separately, check 2a reported only four subsections, which was a **fault in
the checker, not the document**: 5.5 renders as "The criterion’s record" with a
typographic apostrophe and the regex only admitted the ASCII one.

**16 pages, 15 excluding references.**

| section | pages |
|---|---|
| 1. Introduction | 1–2 |
| 2. Data and sample construction | 2–3 |
| 3. The proxy-error scaling exponent | 3–6 |
| 4. The intercept estimator | 6–8 |
| 5. Kill conditions | 8–10 |
| 6. Insertion into a regime classifier | 10–11 |
| 7. Practical implications | 11–13 |
| 8. Limitations | 13–15 |
| References | 16 |

## Phase 4, path scrub

**Before: 393 occurrences of `/Users/GualyCr` across 56 files.** Of these, 348 sat in
code and log files, 33 inside markdown code spans, and 12 bare in markdown prose.

**A 394th occurrence existed that a naive pass would have missed.**
`results/S22-figures.csv` carries the token `Users/GualyCr/venvs/obs-space-vol` with **no
leading slash**, because the S22 inventory regex captured it that way. A
`/Users/GualyCr` substitution skips it. Caught by grepping for the bare account name
rather than the full path, and handled by a third substitution pass.

The five line-break split patterns the brief warns about returned **zero** matches, both
before and after.

**After, re-grepped rather than counted: 0 occurrences in the tracked set**, other than
the 2 in `DECISIONS-as-run.md`, which is exempt under items 145 and 151. Grepping for the
bare account name, for `/Users/` under any username, and for the split patterns all
return the same: nothing outside the exempt file.

The 12 bare-in-markdown occurrences were wrapped as `` `<REPO>` `` rather than left bare,
because GitHub renders an unbackticked `<REPO>` as an unknown HTML tag and hides it.

### Files changed, 56 in total

The ten with the most occurrences: `s05a-reproducibility/logs/phase3.log` (83),
`s08-final/logs/gen8.log` (41), `s06r-repair/logs/gen.log` (34),
`s06r-repair/logs/gen2.log` (30), `s07-completion-and-spy/logs/phase2b.log` (26),
`phase2c.log` (26), `phase2.log` (25), `s05b/logs/phase2.log` (24),
`s05-reliability-mcs/logs/partde.log` (21), `s02-mechanism-expansion/logs/grid-run.log`
(18). The remaining 46 carry between 1 and 6 each, and are listed in full in the session
transcript.

### Secrets re-grep

| class | result |
|---|---|
| Absolute home paths | **0** outside the exempt file |
| API keys, secrets, tokens, private keys | **0** |
| Vendor or Databento account identifiers | **0** |
| Real email addresses | **0** |

Three strings matched the patterns and all three are benign: `git@github.com:<user>/<repo>.git`
is a placeholder URL template in two reports, the word "password" appears twice inside
audit tables stating that no passwords were found, and "Gualy" at a line end is the
author's name in prose.

### Size

| measure | value |
|---|---|
| Tracked files | 575 |
| Tracked size | 15.86 MB |
| Files over 10 MB | none |
| `.venv` / `.venv-broken-20260819` / `data/` | 510 MB / 441 MB / 183 MB, all confirmed ignored |

Ten largest tracked files: `s01/results/S01-cells.csv` 2.33 MB,
`s06r/results/phase1_invariants_on_s05.csv` 0.79 MB, `s05/results/s05_partc.csv` 0.67 MB,
`s01/results/S01-report.md` 0.66 MB, `s05/results/s05_parta.csv` 0.61 MB,
`s01/logs/progress.jsonl` 0.52 MB, `s05a/results/S05A-mcs-per-seed.csv` 0.48 MB,
`s04/results/s04_diagnostics.json` 0.46 MB, `paper/main.pdf` 0.40 MB,
`s05b/results/phase2_offending_observations.csv` 0.33 MB.

## Phase 5, commits

Local identity set, global left untouched:

| scope | name | email |
|---|---|---|
| global | `boomer25tiger` | `cgualytx@gmail.com` — **unchanged** |
| local | `Cristian Gualy` | `cgualytx@gmail.com` |

**The brief specifies "the email supplied at run time" and no email was supplied.** The
address already configured as this machine's global git email was used. All four commits
are local and unpushed, so `git rebase -i --root` or a filter can change it at no cost if
a different address is wanted.

| # | hash | contents | files |
|---|---|---|---|
| 1 | `c9cf437` | Pipeline modules, invariant test suite, environment pins and `.gitignore` | 106 |
| 2 | `b985424` | Decision log and specification | 4 |
| 3 | `842dc3f` | Session directories: reports, runlogs and result artifacts | 440 |
| 4 | `dc4d344` | Paper, figures and README | 25 |

575 files total, working tree clean, nothing untracked. The brief assigned four groups but
left seven root paths unassigned; `.gitignore`, `requirements.txt`, `requirements.lock`,
`ENVIRONMENT.md` and `ENVIRONMENT-pre-20260819.md` went into commit 1, and `results/` into
commit 3. The assignment was checked to cover all 575 with none orphaned.

**No ignored path entered the history.** The committed tree was grepped for `.venv/`,
`.venv-broken`, `data/`, `cache/`, `.npz`, `.npy`, `.parquet`, `.dbn` and `.DS_Store`, all
returning zero. The largest blob in the history is 2.33 MB.

## Phase 6, not run

```
git remote add origin https://github.com/boomer25tiger/obs-space-vol.git
git push -u origin main
```

An unauthenticated probe returns:

```
remote: Repository not found.
fatal: repository 'https://github.com/boomer25tiger/obs-space-vol.git/' not found
```

The brief states the remote "must exist on GitHub before the push". It does not. `gh` is
installed and authenticated as `boomer25tiger` with `repo` scope, so the repository could
be created from here, but **creating a public repository publishes the work irreversibly
and was not authorised by the brief**, which describes the remote as a precondition rather
than asking for it to be created. No remote was added and nothing was pushed.

To proceed, either create it in the GitHub UI, or run:

```
gh repo create boomer25tiger/obs-space-vol --public --source=. --remote=origin --push
```

## A separate finding: the local `.git` is 268 MB

`git count-objects` reports 1,213 loose objects totalling 267.80 MiB against a committed
tree of 15.86 MB. The excess is unreachable objects, almost certainly the residue of the
S18 `git add -A` that began staging the 604 MB Phase-0 extract before `.gitignore` was in
place and was reset. **Unreachable objects are not sent by push**, so this does not affect
what reaches GitHub, and nothing was pruned without being asked. `git gc --prune=now`
would reclaim it; the underlying data still exists in `data/`, so nothing would be lost.

## Files changed this session

| file | change |
|---|---|
| `DECISIONS.md` | items 150 to 152 appended; 159 entries, highest number 152 |
| `paper/sections/03_exponent.tex` | calibration caveat inserted in Section 3.5 |
| `paper/sections/05_kill.tex` | new, Section 5 body |
| `paper/sections/05_conditions.tex` | deleted, superseded |
| `paper/main.tex` | byline, date, input repointed |
| `paper/numbers.csv` | 12 rows added, now 738 |
| 56 tracked files | home paths scrubbed |
| `results/S23B-report.md` | this file |

`DECISIONS-as-run.md` untouched, digest unchanged.
