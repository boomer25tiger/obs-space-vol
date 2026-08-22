# Session 5E run log

Generated 2026-08-19T04:39:40+00:00 (UTC).

## Wall clock per phase

| phase | wall |
|---|---|
| Phase 0 (DECISIONS append, directories) | ~1 min |
| Phase 1 trigamma reference fits | 0.0 s |
| Jump calibration (bisection, both geometries) | 1.6 s |
| Phase 2 synthetic arms (5 arms x 5 seeds x 4 grids) | 29.9 s |
| Phase 3 real-data decomposition (cache only) | 0.3 s |
| Phase 4 reports | ~2 min |

Compute total 32.0 s; session total well under the 30-minute expectation. No bottleneck.

## Seeds and derivation

- Master seed 20260819. The five arm seeds are `numpy.random.SeedSequence(20260819).generate_state(5)` = [3280325159, 10724713, 3527105160, 1168436609, 2339113406], each used as `PCG64(seed)` for one (arm, grid) replication. Every arm is run under all five, and every reported arm figure carries its between-seed standard deviation.
- The jump-calibration bisection uses a fixed internal seed 12345 on a 400-session probe so the calibration is deterministic and independent of the arm seeds.
- No other randomness enters the session; Phases 1 and 3 are deterministic.

## Calibration constants and their sources

| constant | value | source |
|---|---|---|
| Var(log IV) input | 1.02 | DECISIONS item 36, the fitted intercept 1.018 rounded to the value named in the S05E specification |
| GLOBEX truncated share target | 0.2938 | S05B `phase7_truncation_share.csv`, ES/B0/1day at M=1379 (0.293794) |
| RTH truncated share target | 0.1741 | S05B `phase7_truncation_share.csv`, ES/B0/1day at M=389 (0.174051) |
| GLOBEX sigma_j achieved | 0.481094 -> removed 0.2938 | bisection, 14 iterations |
| RTH sigma_j achieved | 0.357077 -> removed 0.1741 | bisection, 14 iterations |
| jump intensity | 1.0 per session | fixed a priori, as in S01/S02 |
| diurnal profile | measured mean per-minute squared return of the real ES panel, normalized to mean 1 | S05B cache `ret1m_ES_{GLOBEX,RTH}_B0.npz` |
| padded-column rate | 2016 0.019154, 2017 0.026621, 2018 0.018226, 2019 0.016714, 2020 0.016417, 2021 0.010990, 2022 0.004999, 2023 0.007027 | S05D `phase3_padding.csv`, GLOBEX |
| A4 Hurst | 0.1 | S05E specification |
| panel dimensions | GLOBEX 1953x1380, RTH 1901x390 | the real S05 panels |
| fill rule for A3 | `ffill(axis=1).bfill(axis=1)` | S03 `analysis.py:41`, the same rule as the real panel |

## Grids

| grid | M values |
|---|---|
| RTH 1day | 5, 6, 10, 13, 26, 78, 195, 389 |
| RTH 1h | 4, 5, 6, 10, 12, 15, 20, 30, 60 |
| RTH 30min | 5, 6, 10, 15, 30 |
| GLOBEX 1day | 5, 6, 10, 12, 23, 46, 138, 345, 1379 |

## Code path (halt condition not triggered)

Imported unmodified and used for every arm: `phase34.windows`, `phase34.subbars` (S05B); `parta.quart_suite` (S05); `estimators2.e1_reduced`, `estimators2.e2`, `estimators2.e4` (S02); `fbm.CirculantEmbedding`, `fbm.fgn_acf` (S01). Fitting uses `scipy.optimize.curve_fit` on c + A M^b with start [min(y), 1.0, -0.5], the same procedure as S05D Phase 4.

## Environment record (from ENVIRONMENT.md)

# Environment record

Captured 2026-08-19T02:24:01+00:00 (UTC) during Session 5A.

## Retroactivity statement

This file captures the environment **as of S05A**. It is retroactive for S01 through S05 **only if no package was installed or upgraded between those sessions and this one**. That condition is NOT satisfied in full; the evidence is below and the affected sessions are named.

## Python and platform

- Python 3.13.13 (CPython)
- Executable: `<REPO>`/.venv/bin/python3
- OS: macOS-14.6-arm64-arm-64bit-Mach-O
- Machine / processor: arm64 / arm
- CPU count: 8

## Thread environment (as of capture)

```text
OMP_NUM_THREADS = (unset)
MKL_NUM_THREADS = (unset)
OPENBLAS_NUM_THREADS = (unset)
VECLIB_MAXIMUM_THREADS = (unset)
NUMEXPR_NUM_THREADS = (unset)
```

## numpy.show_config() (BLAS/LAPACK backend)

```text
{
  "Compilers": {
    "c": {
      "name": "clang",
      "linker": "ld64",
      "version": "15.0.0",
      "commands": "cc"
    },
    "cython": {
      "name": "cython",
      "linker": "cython",
      "version": "3.2.9",
      "commands": "cython"
    },
    "c++": {
      "name": "clang",
      "linker": "ld64",
      "version": "15.0.0",
      "commands": "c++"
    }
  },
  "Machine Information": {
    "host": {
      "cpu": "aarch64",
      "family": "aarch64",
      "endian": "little",
      "system": "darwin"
    },
    "build": {
      "cpu": "aarch64",
      "family": "aarch64",
      "endian": "little",
      "system": "darwin"
    }
  },
  "Build Dependencies": {
    "blas": {
      "name": "accelerate",
      "found": true,
      "version": "unknown",
      "detection method": "system",
      "include directory": "unknown",
      "lib directory": "unknown",
      "openblas configuration": "unknown",
      "pc file directory": "unknown"
    },
    "lapack": {
      "name": "accelerate",
      "found": true,
      "version": "unknown",
      "detection method": "system",
      "include directory": "unknown",
      "lib directory": "unknown",
      "openblas configuration": "unknown",
      "pc file directory": "unknown"
    }
  },
  "Python Information": {
    "path": "/private/var/folders/g3/pffjr_y96bq06blnkf72x_hw0000gn/T/build-env-jzdn7by7/bin/python",
    "version": "3.13"
  },
  "SIMD Extensions": {
    "baseline": [
      "NEON",
      "NEON_FP16",
      "NEON_VFPV4",
      "ASIMD"
    ],
    "found": [
      "ASIMDHP",
      "ASIMDDP"
    ],
    "not found": [
      "ASIMDFHM"
    ]
  }
}
```

## threadpool_info()

```json
"threadpoolctl not installed; see numpy.show_config() above"
```

## pip freeze

```text
aiohappyeyeballs==2.7.1
aiohttp==3.14.3
aiosignal==1.4.0
arch==8.0.0
attrs==26.1.0
certifi==2026.7.22
charset-normalizer==3.5.1
contourpy==1.3.3
cycler==0.12.1
databento==0.83.0
databento-dbn==0.65.0
fonttools==4.63.0
frozenlist==1.8.0
idna==3.19
iniconfig==2.3.0
kiwisolver==1.5.0
matplotlib==3.11.1
multidict==6.7.1
numpy==2.5.2
packaging==26.3
pandas==3.0.5
patsy==1.0.2
pillow==12.3.0
pluggy==1.6.0
propcache==0.5.2
pyarrow==25.0.1
Pygments==2.21.0
pyparsing==3.3.2
pypdf==6.16.1
pytest==9.1.1
python-dateutil==2.9.0.post0
requests==2.34.2
scipy==1.18.0
six==1.17.0
statsmodels==0.14.6
urllib3==2.7.0
yarl==1.24.5
zstandard==0.25.0
```

## Package install/modify timestamps (dist-info mtime)

```text
six-1.17.0                         2026-08-18 09:55:32
pip-26.2.1                         2026-08-18 09:55:40
pyparsing-3.3.2                    2026-08-18 09:59:42
pillow-12.3.0                      2026-08-18 10:00:00
pluggy-1.6.0                       2026-08-18 10:00:19
pygments-2.21.0                    2026-08-18 10:00:26
packaging-26.3                     2026-08-18 10:01:14
iniconfig-2.3.0                    2026-08-18 13:12:00
cycler-0.12.1                      2026-08-18 13:12:27
kiwisolver-1.5.0                   2026-08-18 13:12:36
numpy-2.5.2                        2026-08-18 13:14:43
pytest-9.1.1                       2026-08-18 13:16:04
fonttools-4.63.0                   2026-08-18 13:16:15
python_dateutil-2.9.0.post0        2026-08-18 13:16:15
contourpy-1.3.3                    2026-08-18 13:16:35
scipy-1.18.0                       2026-08-18 13:17:12
pandas-3.0.5                       2026-08-18 13:17:20
matplotlib-3.11.1                  2026-08-18 13:21:40
pypdf-6.16.1                       2026-08-18 17:22:46
zstandard-0.25.0                   2026-08-18 18:24:02
certifi-2026.7.22                  2026-08-18 18:34:56
multidict-6.7.1                    2026-08-18 18:34:56
urllib3-2.7.0                      2026-08-18 18:34:56
aiohappyeyeballs-2.7.1             2026-08-18 18:36:23
attrs-26.1.0                       2026-08-18 18:36:23
idna-3.19                          2026-08-18 18:36:23
requests-2.34.2                    2026-08-18 18:36:23
propcache-0.5.2                    2026-08-18 18:37:09
charset_normalizer-3.5.1           2026-08-18 18:39:42
databento_dbn-0.65.0               2026-08-18 18:39:42
frozenlist-1.8.0                   2026-08-18 18:39:42
pyarrow-25.0.1                     2026-08-18 18:39:42
yarl-1.24.5                        2026-08-18 18:39:42
aiohttp-3.14.3                     2026-08-18 18:41:15
aiosignal-1.4.0                    2026-08-18 18:41:15
databento-0.83.0                   2026-08-18 18:41:15
patsy-1.0.2                        2026-08-18 21:24:34
statsmodels-0.14.6                 2026-08-18 21:24:47
arch-8.0.0                         2026-08-18 21:25:31
```

## Evidence of mid-stream environment change

Session start markers used: S01 2026-08-18 09:35, S02 2026-08-18 17:00, S03 2026-08-18 18:19, S04 2026-08-18 21:30, S05 2026-08-18 21:55, S05A 2026-08-18 22:18.

Core numerical stack (installed at S01 Phase 0, unchanged since - all four sessions' numerics ran against these exact builds):

```text
numpy-2.5.2                        2026-08-18 13:14:43
pytest-9.1.1                       2026-08-18 13:16:04
scipy-1.18.0                       2026-08-18 13:17:12
pandas-3.0.5                       2026-08-18 13:17:20
matplotlib-3.11.1                  2026-08-18 13:21:40
```

Packages added AFTER S01/S02 (evidence that the environment was not constant across the whole programme):

```text
pypdf-6.16.1                       2026-08-18 17:22:46
zstandard-0.25.0                   2026-08-18 18:24:02
databento_dbn-0.65.0               2026-08-18 18:39:42
pyarrow-25.0.1                     2026-08-18 18:39:42
databento-0.83.0                   2026-08-18 18:41:15
patsy-1.0.2                        2026-08-18 21:24:34
statsmodels-0.14.6                 2026-08-18 21:24:47
arch-8.0.0                         2026-08-18 21:25:31
```

Reading: `databento`, `databento-dbn`, `zstandard`, `pyarrow` and `pypdf` were installed during S03; `arch`, `statsmodels`, `patsy` during S05. None of them existed when S01 and S02 ran, and none is imported by S01 or S02 code, so no S01/S02 result depends on them. No package was UPGRADED or downgraded at any point: every dist-info above is a first install, and the core stack (numpy/scipy/pandas/matplotlib/pytest) carries its original S01 timestamps. Therefore this capture is valid retroactively for S01-S05 with respect to every package each session actually imported, and the caveat is limited to the fact that S01/S02 ran in a strictly smaller environment.


### pip freeze at S05E

```text
aiohappyeyeballs==2.7.1
aiohttp==3.14.3
aiosignal==1.4.0
arch==8.0.0
attrs==26.1.0
certifi==2026.7.22
charset-normalizer==3.5.1
contourpy==1.3.3
cycler==0.12.1
databento==0.83.0
databento-dbn==0.65.0
fonttools==4.63.0
frozenlist==1.8.0
idna==3.19
iniconfig==2.3.0
kiwisolver==1.5.0
matplotlib==3.11.1
multidict==6.7.1
numpy==2.5.2
packaging==26.3
pandas==3.0.5
patsy==1.0.2
pillow==12.3.0
pluggy==1.6.0
propcache==0.5.2
pyarrow==25.0.1
Pygments==2.21.0
pyparsing==3.3.2
pypdf==6.16.1
pytest==9.1.1
python-dateutil==2.9.0.post0
requests==2.34.2
scipy==1.18.0
six==1.17.0
statsmodels==0.14.6
urllib3==2.7.0
yarl==1.24.5
zstandard==0.25.0
```
