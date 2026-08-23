# S23D report, authorship rewrite, push and clone verification

**The repository is public at https://github.com/boomer25tiger/obs-space-vol.** Six
commits pushed, all authored `Cristian Gualy <208218876+boomer25tiger@users.noreply.github.com>`,
no ignored path in the history, and a fresh clone builds the paper and reproduces both
figures byte-for-byte.

## Phase 0

`DECISIONS-as-run.md` digest `e0ff2520dd484b3d816f6eea1f98b73ce0bd6687ad4b93624d3600d45317411e`,
**matches**. `.git` 4.0 MB, 0 unreachable objects, no remote configured, global identity
`boomer25tiger <cgualytx@gmail.com>` unchanged. Item 157 appended and verified at line 945.

## Phase 1, authorship, with Phase 2 reordered ahead of it

**`git filter-branch` refused to run: "Cannot rewrite branches: You have unstaged
changes."** The brief orders the amend before the sixth commit, but five files were
modified in S23C and left uncommitted, so the working tree was dirty.

Rather than stash across a history rewrite, which leaves `refs/stash` pointing at commits
that `filter-branch` is simultaneously rewriting, **the sixth commit was made first** and
the rewrite then ran over all six. The end state is what the brief specifies: every commit
carries the noreply address and no file content changed. Reported as a deviation.

Local email set to `208218876+boomer25tiger@users.noreply.github.com`; global untouched.

### Tree hashes across the rewrite

| commit | tree before | tree after | |
|---|---|---|---|
| sixth | `b2ca6416ac56512ae6b1bb6f40b1365f4d2fc257` | `b2ca6416ac56512ae6b1bb6f40b1365f4d2fc257` | same |
| S23B report | `af2d260d27d79ed1787051d3f74fe8be421400bb` | `af2d260d27d79ed1787051d3f74fe8be421400bb` | same |
| paper | `491d06ad63a4fd54baa31c9fad97c9158e26dd77` | `491d06ad63a4fd54baa31c9fad97c9158e26dd77` | same |
| sessions | `0bab6d5d78db6c9a4145a63fa2356e7300e44eb9` | `0bab6d5d78db6c9a4145a63fa2356e7300e44eb9` | same |
| decisions | `7004ddf833e378b720450279ba69f62644b011a7` | `7004ddf833e378b720450279ba69f62644b011a7` | same |
| pipeline | `09bb1bd813156635521348141b6a954b5b1973f4` | `09bb1bd813156635521348141b6a954b5b1973f4` | same |

**All six identical. No content was touched.** Commits with the noreply address: 6 of 6.
With the personal address: 0. Author name on every commit: `Cristian Gualy`. Committer
email is the noreply address on all six.

`refs/original/` backup refs deleted, reflog expired, repacked. `.git` 4.0 MB, 0
unreachable.

## Phase 2, the sixth commit

`8dd08b8` after the rewrite, **6 files**. The brief names five; `results/S23C-report.md`
was included as the sixth, since it was untracked and every prior session report is in the
repository. Tree clean afterward.

## Final six commits

| hash | author email | message |
|---|---|---|
| `c2cecce` | noreply | Pipeline modules, invariant test suite, environment pins and .gitignore |
| `5c29e1f` | noreply | Decision log and specification |
| `3773f9e` | noreply | Session directories: reports, runlogs and result artifacts |
| `d254c22` | noreply | Paper, figures and README |
| `8e8eee7` | noreply | S23B session report |
| `8dd08b8` | noreply | Section 5.4 placebo correction, README note on DECISIONS-as-run.md |

## Phase 3, create and push

```
$ gh repo create boomer25tiger/obs-space-vol --public --source=. --remote=origin --push
  https://github.com/boomer25tiger/obs-space-vol
  error: RPC failed; HTTP 400 curl 22 The requested URL returned error: 400
  send-pack: unexpected disconnect while reading sideband packet
  fatal: the remote end hung up unexpectedly
```

**The repository was created but the push failed.** The cause was HTTP/2, not payload
size: the pack is 3.84 MiB. Retried after setting two options **locally**, leaving global
config untouched:

```
$ git config --local http.version HTTP/1.1
$ git config --local http.postBuffer 524288000
$ git push -u origin main
  To https://github.com/boomer25tiger/obs-space-vol.git
   * [new branch]      main -> main
  branch 'main' set up to track 'origin/main'.
```

### Verification by fetch

| check | result |
|---|---|
| `origin/main` == local `main` | `8dd08b8a1ed1e35e5bb37f1563b891a5b861fe0f`, **in sync** |
| Commits on the remote | **6**, hashes as tabled above |
| Files on the remote | 577 |
| `.venv/`, `.venv-broken`, `data/`, `cache/` | **0 each** |
| `.npz`, `.npy`, `.parquet`, `.dbn`, `.DS_Store`, `raw_pre2024` | **0 each** |
| Visibility | public |
| Default branch | `main` |

`gh repo view` reports `diskUsage: 0`, GitHub not having recomputed it at query time; the
pushed pack is 3.84 MiB and the clone occupies 20 MB on disk.

Clone URL: `https://github.com/boomer25tiger/obs-space-vol.git`

## Phase 4, clone verification

Cloned to a temporary directory outside the working tree. **The clone was not modified.**
577 files, 20 MB on disk, 4.0 MB of git objects.

### Build

```
$ cd paper && pdflatex -interaction=nonstopmode main.tex && bibtex main && pdflatex ×2
```

**PASS.** 16 pages, exit 0, no errors. Both figures resolved through the relative path
`../figures/`, which works in a fresh clone. The only "missing file" lines are the
expected first-pass `No file main.aux` and `No file main.bbl`.

### Figure scripts

```
$ python figures/src/fig1.py
$ python figures/src/fig2.py
```

**PASS, both, exit 0.** Each emitted PDF is a different byte sequence from the committed
one, and the difference is **entirely the embedded `/CreationDate`**: after stripping that
field the files are identical, and both are 27,639 and 24,086 bytes respectively in both
copies. The scripts are deterministic, and they read only tracked artifacts.

### Invariant suite

```
$ python -m pytest sessions/s06r-repair/tests/test_invariants.py -q
  no tests ran in 0.05s
```

**This is correct behaviour, not a failure, but it reads as one.** The file is not a
pytest suite; it is a library of five assertion helpers designed to be imported and called
from inside the pipeline, which is exactly what DECISIONS item 39 specifies. Its
`test_`-prefixed filename makes pytest collect it and report nothing.

Exercised directly, the module imports cleanly and **all five assertions fire** on
violating input:

| assertion | fired |
|---|---|
| `assert_forecasts_positive` | yes, `InvariantViolation` |
| `assert_loss_finite` | yes |
| `assert_lambda_in_unit` | yes |
| `assert_range_inputs` | yes |
| `assert_effective_M` | yes |

The brief names the path `tests/test_invariants.py`; the actual path is
`sessions/s06r-repair/tests/test_invariants.py`, which is also what the README says.

### Dead paths

**3,623 distinct references to paths excluded by `.gitignore`, every one dead in a fresh
clone.** By location:

| count | location | consequence for a reader |
|---|---|---|
| 3,641 | session reports and result artifacts | descriptive, recording what a run produced; not links to follow |
| 56 | **executable source under `sessions/*/src/`, 26 files** | a reader running these hits a missing file |
| 16 | run logs | descriptive |
| 2 | `.gitignore` itself | the exclusion rules |

The source files most affected: `s05d-panel-integrity/src/report5d.py` and `run5d.py` (5
each), `s06r-repair/src/phase9_spec.py` (5), `s17-emission/src/phase12.py` and
`phase345.py` (4 each), `s03-data-noise/src/pipeline.py` (3),
`s04-repairs-diagnostics/src/build.py` (3), `s07-completion-and-spy/src/phase1_spy_inventory.py` (3).

The README does say the raw data and derived binaries are excluded and regenerable, so
this is disclosed rather than hidden. What it does not say is that the measurement scripts
themselves cannot be run without the vendor data, only the figure scripts and the build.

## Phase 5, the reader's view

The README states all five things the brief asks about: **what the project measures**
(three headline results with figures), **what the repository contains** (a path table),
**how to reproduce the figures** (a runnable block), **the environment pins** (five
packages at exact versions), and **where the pre-registration record lives**
(`DECISIONS.md`, with `DECISIONS-as-run.md` alongside).

Four things are stale or missing. Per the stop condition the clone was not modified and
none of these was fixed; they are for a later session in the working tree.

1. **The status section is wrong about Section 5.** It says "section 5 remains a stub
   whose table is generated from the determination artifacts". Section 5 was written in
   S23B and now carries subsections 5.1 through 5.5. This is the most misleading line in
   the file, since it understates the paper.
2. **The decision-log count is stale.** "155 entries numbered to 148" against an actual
   160 entries numbered to 157.
3. **The session count is stale.** "twenty-six logged sessions, S01 through S22" predates
   S23, S23B, S23C and S23D.
4. **`results/` is undocumented.** A reader sees a top-level directory with 10 files and
   no entry in the contents table. `ENVIRONMENT.md` and `ENVIRONMENT-pre-20260819.md` are
   likewise untabled.

### Top-level listing as a reader sees it

| entry | size | files | purpose evident? |
|---|---|---|---|
| `DECISIONS.md` | 68K | | yes, from the README |
| `DECISIONS-as-run.md` | 64K | | yes |
| `ENVIRONMENT.md` | 4.0K | | **not in the contents table** |
| `ENVIRONMENT-pre-20260819.md` | 8.0K | | **not in the contents table**; the date suffix is unexplained |
| `README.md` | 8.0K | | yes |
| `figures/` | 68K | 6 | yes |
| `paper/` | 788K | 27 | yes |
| `requirements.lock` / `.txt` | 4.0K each | | yes |
| `results/` | 268K | 10 | **not in the contents table** |
| `sessions/` | 15M | 535 | yes |
| `specs/` | 72K | 2 | yes |

## Deviations from the brief

1. Phases 1 and 2 were reordered, because `filter-branch` will not run on a dirty tree and
   stashing across a history rewrite is unsafe. End state unchanged and verified by tree hash.
2. The sixth commit carries six files, not the five named, adding `results/S23C-report.md`.
3. The push required `http.version=HTTP/1.1` after an HTTP 400. Both git options were set
   locally.
4. `tests/test_invariants.py` does not exist at that path; the file is at
   `sessions/s06r-repair/tests/test_invariants.py`.

`DECISIONS-as-run.md` untouched, digest unchanged. Global git identity unchanged.
