# S23C report, final correction and push

Phases 0 through 4 completed. **The session halted at Phase 5: the GitHub noreply address
was not supplied.** The brief gives its form but no numeric id, and the stop condition
reads "Halt at Phase 5 if the noreply address is not supplied. Do not substitute one."
Phases 5 through 8 did not run. Nothing was pushed and no remote was added.

## Phase 0

| check | result |
|---|---|
| Interpreter | `~/venvs/obs-space-vol/bin/python` |
| numpy / pandas | 2.5.2 / 3.0.5, matching |
| Physical path | not under a known sync root |
| `DECISIONS-as-run.md` digest | `e0ff2520dd484b3d816f6eea1f98b73ce0bd6687ad4b93624d3600d45317411e`, **matches** |
| Working tree | clean at session start |

159 entries, highest number 152, gaps at 141 to 143, ten reused numbers (13, 14, 15,
51 to 57). Items 153 to 156 appended and verified at lines 927, 934, 937 and 941.

The five S23B commits, all authored `Cristian Gualy <cgualytx@gmail.com>`:

| hash | message |
|---|---|
| `c9cf437` | Pipeline modules, invariant test suite, environment pins and .gitignore |
| `b985424` | Decision log and specification |
| `842dc3f` | Session directories: reports, runlogs and result artifacts |
| `dc4d344` | Paper, figures and README |
| `08e87a1` | S23B session report |

## Phase 1, Section 5.4

Replaced as instructed. The artifact at
`sessions/s09-application/results/phase12_summary.json` gives:

| quantity | field | value |
|---|---|---|
| raw clean-geometry rate | `bc_rate_rth` | 0.6875 |
| placebo rate | `dc_rate_rth` | 0.4791666666666667 |
| excess | `excess_rth` | 0.20833333333333331 |

The placebo is **69.7 percent** of the raw rate, so "roughly seventy percent" holds. The
excess is **20.83 points**, so "the remaining twenty-one points" is consistent with the
$20.8$ percent stated earlier in the same paragraph. `k1_raw_rate_rth` and
`k1_placebo_rate_rth` registered in `numbers.csv`, now 740 rows; `k1_excess_rth` was
already present from S23B. The corrected line carries a citation comment naming all three.

## Phase 2, README

One sentence added to the Provenance section stating that `DECISIONS-as-run.md` is
committed unmodified as the original record and therefore retains the two absolute paths
that item 145 generalises elsewhere.

## Phase 3, rebuild

Build clean: no errors, no undefined or multiply-defined labels, zero overfull boxes.

| # | check | result |
|---|---|---|
| 1 | Corrected sentence renders | **PASS** |
| 2 | "roughly half subset variation" absent | **PASS** |
| 3 | Section 3.5 carries the calibration caveat | **PASS** |
| 4 | Section 5 has subsections 5.1 to 5.5 | **PASS**, typographic apostrophe allowed in 5.5 |
| 5 | Byline renders | **PASS** |
| 6 | Date renders | **PASS** |

**16 pages, 15 excluding references.**

## Phase 4, prune

`git gc --prune=now --aggressive`.

| measure | before | after |
|---|---|---|
| `.git` on disk | 268 MB | **4.0 MB** |
| Loose objects | 1,217 (267.82 MiB) | 0 |
| Packed objects | 0 in 0 packs | 698 in 1 pack, 3.84 MiB |
| Unreachable objects | 519 | **0** |

All five commit hashes unchanged, verified by diffing the full 40-character hash list
before and after:

```
08e87a1a003660edeb91a02a08a5465f7100175b
dc4d34456d988dcd61141f3b3bf3fe614eb42de6
842dc3f2e27046ccb80bfc0090ab496b75792531
b985424b106eacefcb6d4d5dbed08de438c3e014
c9cf437fe323ec5a79ce77f6fca931053005da46
```

576 files in HEAD, `git fsck` reports no problems. The 264 MB reclaimed was residue from
the aborted S18 `git add -A` over the raw extract, as item 155 records; `data/` still
holds the source, so nothing was lost.

## Phase 5, halted

The brief specifies the address "supplied at run time in the form
`<numeric-id>+boomer25tiger@users.noreply.github.com`". The form was given; **the numeric
id was not**. Per the stop condition, no address was substituted and no commit was
amended.

To make the halt actionable rather than a dead end, the id was read from the authenticated
GitHub API and is reported here **without being applied**:

```
gh api user --jq '{login:.login, id:.id}'
  {"id":208218876,"login":"boomer25tiger"}
```

The login matches the one in the brief, so the canonical address is
`208218876+boomer25tiger@users.noreply.github.com`. Confirming it is enough to resume.

## State left behind

| | |
|---|---|
| Commits | five, unamended, still `Cristian Gualy <cgualytx@gmail.com>` |
| Local identity | `Cristian Gualy <cgualytx@gmail.com>` |
| Global identity | `boomer25tiger <cgualytx@gmail.com>`, **unchanged** |
| Remotes | none |
| Pushed | nothing |

Uncommitted, being the sixth commit that Phase 6 would have made:
`DECISIONS.md`, `README.md`, `paper/main.pdf`, `paper/numbers.csv`,
`paper/sections/05_kill.tex`.

## What remains

1. Confirm `208218876+boomer25tiger@users.noreply.github.com`, or supply a different address.
2. Phase 5: set the local email, amend all five commits, verify the final tree hash is
   unchanged across the rewrite.
3. Phase 6: commit the correction as the sixth.
4. Phase 7: `gh repo create boomer25tiger/obs-space-vol --public --source=. --remote=origin --push`.
5. Phase 8: clone into a temporary directory and verify the build, the figure scripts and
   the invariant tests.

`DECISIONS-as-run.md` untouched, digest unchanged.
