# Observation-space volatility evaluation

Measuring how much of the variation in a realized-variance proxy is integrated
variance rather than measurement error, and locating the decisions where that
distinction changes an answer.

## What is measured

**The proxy-error scaling exponent.** Fitting `Var(log RV_M) = c + A·M^b` across
sampling grids gives `b` between −0.41 and −0.97 against a sampling-theory
reference of −1.13 to −1.21, with the reference outside the 95% bootstrap
interval in 18 of 18 cells and in all 54 fits across three proxies (realized
variance, the flat-top realized kernel, the two-scale estimator).

**A reliability estimator.** The intercept `c` estimates `Var(log IV)`, giving
`λ = c / Var(log RV_M)`, which needs no assumption about how proxy noise scales —
which is what the scaling result removes.

**Where it matters.** Thirteen pre-registered kill conditions test whether the
measured reliability changes a decision. Proxy noise is second-order where the
loss surface is smooth or the contamination averages away with the estimation
window, and first-order where the quantity depends on the *variance* of the
estimate and more data does not reduce the contamination.

## Provenance

The analysis was produced with Claude Code across twenty-six logged sessions, S01
through S22, including the S05A to S05E, S06R and S09-PRE repair and audit
sessions. Every decision and every emitted artifact is in the repository:
per-session source under `sessions/sNN-*/src/`, emitted CSV and JSON under
`sessions/sNN-*/results/`, and a report and runlog for each session except S02,
which retains its source and raw output but no written report. The session
prompts themselves are not in the repository; what they fixed is, in
`DECISIONS.md`. `DECISIONS.md` is the pre-registration record, rewritten in S22
from session-instruction voice into record voice, and `DECISIONS-as-run.md` is
the unmodified original against which that rewrite was checked figure by figure.
Because it is committed unmodified as the original record, `DECISIONS-as-run.md`
retains the two absolute home-directory paths that item 145 generalises everywhere
else in the repository.

## Repository contents

| path | contents |
|---|---|
| `DECISIONS.md` | the decision log, 155 entries numbered to 148, append-only |
| `DECISIONS-as-run.md` | the unmodified log as written during the sessions |
| `specs/` | the specification, updated per session with determinations |
| `sessions/sNN-*/src/` | every measurement script, by session |
| `sessions/sNN-*/results/` | emitted CSV and JSON artifacts, per-session report and runlog |
| `sessions/s06r-repair/tests/` | the invariant test suite |
| `paper/` | LaTeX source, `numbers.csv` provenance table, `k_table.csv` |
| `figures/src/` | figure generators, each reading only persisted artifacts |

Nothing is redacted. The audit trail, including the sessions that found defects
in earlier sessions and the corrections they forced, is part of the deliverable.

## What is not published

Raw Databento GLBX and SPY files, and the derived binary panels and bar tables
regenerable from them, are excluded by `.gitignore` (DECISIONS item 130). The
manifest of input file hashes is published in
`sessions/s03-data-noise/results/S03-runlog.md` and
`sessions/s07-completion-and-spy/results/S07-spy-manifest.txt`. Every CSV and
JSON artifact the paper cites is tracked.

## Reproducing the figures

```bash
/path/to/venv/bin/python figures/src/fig1.py
/path/to/venv/bin/python figures/src/fig2.py
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```

Both figure scripts read only from `sessions/*/results/` and write a provenance
JSON recording every artifact path and row count they touched. `paper/numbers.csv`
carries one row per quantity cited in the draft, with its value at full precision,
the artifact path and the field it was read from.

## Environment

Pinned in `requirements.lock`: Python 3.13.13, numpy 2.5.2, pandas 3.0.5,
scipy 1.18.0, databento 0.83.0. Every session gates on those exact versions and
halts otherwise. The environment lives outside any file-sync scope (item 79).

## Status

Measurement is complete as of session 17. The paper is in draft: sections 1, 2,
3, 4, 6, 7 and 8 are written; section 5 remains a stub whose table is generated
from the determination artifacts, its inclusion decisions being authorial
(item 131).
