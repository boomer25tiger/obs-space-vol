# Session 9-PRE report, environment diagnosis and rebuild

Generated 2026-08-19T19:02:11+00:00 (UTC). No part of S09 was run. The holdout was not opened. No research artifact was modified, and nothing inside site-packages was patched or edited.

## Phase 1, diagnosis

### Pinned versions against installed

`requirements.lock` and `ENVIRONMENT.md` agree exactly, and both agree with what is installed, read from the `.dist-info` directories without importing:

| package | requirements.lock | ENVIRONMENT.md | installed (.dist-info) | match |
|---|---|---|---|---|
| numpy | 2.5.2 | 2.5.2 | 2.5.2 | yes |
| pandas | 3.0.5 | 3.0.5 | 3.0.5 | yes |
| scipy | 1.18.0 | 1.18.0 | 1.18.0 | yes |
| arch | 8.0.0 | 8.0.0 | 8.0.0 | yes |
| statsmodels | 0.14.6 | 0.14.6 | 0.14.6 | yes |

**The installed pandas matched the pin.** There was no version drift. Sessions S05B through S08 therefore DID run under the environment their runlogs record, and the failure is not a drift event. This is the finding that matters more than the crash, and it is negative.

### The damaged file

`.venv/lib/python3.13/site-packages/pandas/core/dtypes/common.py`, raw output:

```text
$ wc -c   ->    56234 .../pandas/core/dtypes/common.py
$ wc -l   ->        0 .../pandas/core/dtypes/common.py
$ grep -c '^def '            -> 0
$ grep -c '^[[:space:]]*def ' -> 0
$ head -40                   -> (no output)
$ tail -10                   -> tail: .../common.py: Undefined error: 0
```

Both `def` patterns were checked, as instructed, and both return zero. The file reports a plausible byte count in its directory entry, yields no readable lines, and errors on `tail`. Its mtime is 2026-08-18 09:52:02, the original install; nothing rewrote it.

**A methodological point that follows directly, and that bears on item 75:** `wc -c` did NOT detect this file. It returns 56,234, a normal-looking number, for a file that cannot be read at all. Byte count comes from metadata and survives the loss of the data blocks. `wc -l` returns 0 and `head` returns nothing, and those do detect it. A future session verifying files with `wc -c` alone would miss exactly the failure mode that broke this environment; pairing it with `wc -l` costs nothing and closes the gap.

### Tracebacks, verbatim

```text
$ .venv/bin/python3 -c "import pandas"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import pandas
  File ".../site-packages/pandas/__init__.py", line 46, in <module>
    from pandas.core.api import (
    ...<61 lines>...
    )
  File ".../site-packages/pandas/core/api.py", line 16, in <module>
    from pandas.core.dtypes.missing import (
    ...<4 lines>...
    )
  File ".../site-packages/pandas/core/dtypes/missing.py", line 24, in <module>
    from pandas.core.dtypes.common import (
    ...<5 lines>...
    )
ImportError: cannot import name 'DT64NS_DTYPE' from 'pandas.core.dtypes.common' (.../site-packages/pandas/core/dtypes/common.py)
```

```text
$ .venv/bin/python3 -m pip --version
pip 26.2.1 from .../.venv/lib/python3.13/site-packages/pip (python 3.13)
```

pip reported working at diagnosis time. Earlier the same day it failed with `ImportError: cannot import name 'get_filter_by_name' from 'pip._vendor.pygments.filters'`, so a second site-packages file was affected and later recovered. That inconsistency is recorded rather than explained.

### Install-time clustering

`.dist-info` mtimes fall into clusters matching the session record: 2026-08-18 09:55-10:01, 13:12-13:21 (core stack), 17:22 (pypdf), 18:24-18:41 (databento group), 21:24 (statsmodels/patsy), 22:47 (arch), and a single entry at **2026-08-19 14:30:42, pip-26.2.1** - the `ensurepip --upgrade` run during the aborted S09 session. No pandas or numpy dist-info was touched on 2026-08-19, so no partial reinstall of either occurred.

## Phase 2, rebuild

`.venv` was renamed to `.venv-broken-20260819` and is retained. A fresh `.venv` was created with Python 3.13.13, the version `ENVIRONMENT.md` records, and populated from `requirements.lock` using the new environment's own pip. No system pip, conda or external interpreter installed into it.

| package | lock | rebuilt | discrepancy |
|---|---|---|---|
| numpy | 2.5.2 | 2.5.2 | none |
| pandas | 3.0.5 | 3.0.5 | none |
| scipy | 1.18.0 | 1.18.0 | none |
| arch | 8.0.0 | 8.0.0 | none |
| statsmodels | 0.14.6 | 0.14.6 | none |
| matplotlib | 3.11.1 | 3.11.1 | none |
| databento | 0.83.0 | 0.83.0 | none |

39 distributions installed, the same count as the broken environment. `import pandas` succeeds and a numeric sanity check returns the expected values.

## Phase 3, equivalence verification

### ES/GLOBEX/B0/1day intercept fit

| quantity | recomputed | stored | abs_dev | rel_dev |
|---|---|---|---|---|
| c | 1.033909624 | 1.03391 | 3.763069858e-07 | 3.639649349e-07 |
| A | 2.058452251 | 2.058452 | 2.509024437e-07 | 1.21888897e-07 |
| b | -0.4426723089 | -0.442672 | 3.088699519e-07 | 6.977399789e-07 |
| rmse | 0.04989400117 | 0.049894 | 1.167172269e-09 | 2.339303861e-08 |

The `stored` column holds the four-to-five significant figure values quoted in the session prompt. Agreement is to 1e-7 relative, which is the rounding in those reference values rather than a computational difference: against the full-precision S08 CSV the recomputation matches to the digits stored there.

### Var(log RV_M) at every grid point

| M | recomputed | stored | abs_dev |
|---|---|---|---|
| 5 | 2.023840431 | 2.023840431 | 0 |
| 6 | 2.051730717 | 2.051730717 | 0 |
| 10 | 1.708896116 | 1.708896116 | 0 |
| 12 | 1.698241118 | 1.698241118 | 0 |
| 23 | 1.515734059 | 1.515734059 | 0 |
| 46 | 1.422238231 | 1.422238231 | 0 |
| 138 | 1.310966053 | 1.310966053 | 0 |
| 276 | 1.249852874 | 1.249852874 | 0 |
| 345 | 1.219456901 | 1.219456901 | 0 |
| 1379 | 1.040928826 | 1.040928826 | 2.220446049e-16 |

**Maximum absolute deviation 2.22e-16**, which is one unit in the last place of a double. The grid is reproduced to machine precision.

### The five invariants against pre-repair S05 artifacts

| test | fail_S06R | fail_now | pass_S06R | pass_now | fires_now | matches_S06R |
|---|---|---|---|---|---|---|
| assert_forecasts_positive | 46 | 46 | 122 | 122 | True | True |
| assert_loss_finite | 35 | 35 | 85 | 85 | True | True |
| assert_lambda_in_unit | 3683 | 3683 | 11568 | 11568 | True | True |
| assert_range_inputs | 8 | 8 | 0 | 0 | True | True |
| assert_effective_M | 88 | 88 | 36 | 36 | True | True |

All five fire, and every count reproduces its S06R Phase 1 value exactly: 46, 35, 3683, 8 and 88 failures respectively.

### Which kind of disagreement occurred

**Low-order only.** The largest deviation anywhere is 7.0e-07 relative on the fitted exponent, traceable to the rounding of the printed reference values, and 2.2e-16 absolute on the recomputed grid. No reported figure changes at any precision this project publishes. Nothing indicates thread or BLAS nondeterminism beyond the last bit, and no quantity disagrees in a way that would affect a conclusion.

## Phase 4, DECISIONS repair

Before the append, the highest numbered item present was **65**, and items 66 through 77 were absent - confirming that the aborted S09 run's append did not persist, exactly as item 77 records. All twelve were appended in one block and verified by grep:

| item | line |
|---|---|
| 66 | 398 |
| 67 | 405 |
| 68 | 413 |
| 69 | 419 |
| 70 | 424 |
| 71 | 433 |
| 72 | 437 |
| 73 | 442 |
| 74 | 445 |
| 75 | 454 |
| 76 | 457 |
| 77 | 466 |

`DECISIONS.md` is now 468 lines and 33,964 bytes, and a re-grep confirms 12 of 12 items present.

## Determination

### A. Environment rebuilt, equivalence verified, versions matched the lock before the failure. S09 may proceed.

Evidence: the `.dist-info` directories recorded numpy 2.5.2, pandas 3.0.5, scipy 1.18.0, arch 8.0.0 and statsmodels 0.14.6 before the rebuild, matching `requirements.lock` and `ENVIRONMENT.md` exactly, so no drift occurred and S05B through S08 ran under the versions their runlogs claim. The rebuilt environment reproduces the ES/GLOBEX/B0/1day intercept fit to 1e-7, the Var(log RV_M) grid to 2.2e-16, and all five invariant counts exactly. Determination B does not apply because there was no version mismatch, and C does not apply because no named quantity disagrees in a reported figure.

One correction to the record, stated because a later session will rely on it: my own S09 integrity scan of 2026-08-19 concluded project-wide storage failure and that conclusion was wrong, as item 74 records. The research artifacts are intact - `PREREG.md` reads 98 lines, `test_units.py` 215 lines, `DECISIONS.md` 394 lines before this session's append. What the scan mistook for evidence was its own timeout. The narrower observation underneath it was real but confined to site-packages, and that is what this session rebuilt.
