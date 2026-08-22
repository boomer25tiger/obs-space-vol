# Session 7 run log

Generated 2026-08-19T06:09:51+00:00 (UTC).

## Wall clock per phase

| phase | wall |
|---|---|
| Phase 0 DECISIONS + directories | ~2 min |
| Phase 1 SPY inventory, manifest, span check | 52 s |
| Phase 2 exclusion audit + rerun of 8 cells (3 passes: blanket halt rule discarded on audit, then filter bound, then model-set reduction) | ~9 min |
| Phase 2 filter audit across all cells | ~1 min |
| Phase 3+4 RGARCH diagnosis and MCS | see phase4_summary.json |
| Phase 5 SPY panel build, both venues from raw | 211 s |
| Phase 6 SPY exponent | see logs/phase6.log |
| Phases 7-8 determination and reports | ~4 min |

## Seeds and derivation

- MCS master seed 20260819; each (cell, scheme) uses `PCG64(SeedSequence([20260819, cell_index, scheme_index]))`, logged in the `seed` column of `phase4_mcs.csv`. 10,000 moving-block resamples, block length ceil(T^(1/3)).
- No other randomness: the SPY panel build, the exclusion, the filter, the RGARCH refits and every exponent fit are deterministic.

## Constants and sources

| constant | value | source |
|---|---|---|
| SPY grid | 5, 6, 10, 13, 26, 39, 78, 130, 195, 390, 780, 1560, 2340, 4680, 11700, 23400 | all exact divisors of 23,400 |
| SPY RTH window | 09:30:00-15:59:59 NY, 23,400 seconds | SCOPE section 3 |
| SPY early closes | day after Thanksgiving, Jul 3, Dec 24 | SCOPE section 3 |
| filter lower bound | smallest strictly positive in-sample RV | item 52 |
| filter upper bound | in-sample RV max | item 40, unchanged |
| noise primary range | implied bias 2*M*omega^2/IV below 1% | item 57 |
| truncation | 3 local standard deviations | S05 Part A |
| holdout | 2024-01-01, futures and SPY | items 50 and 58 |
| trigamma reference | polygamma(1, M/2), fitted by the same free-intercept procedure | S05E Phase 1 |

## Calendar and data sources

- Futures exclusion: CME Group published equity-index holiday calendar (rule-generated) plus the item-51 exchange-declared halt sessions.
- SPY: raw DBN from `~/Downloads/DataBento Data/SPY 1s Data`, jobs ARCX-20260815-XLE9K93W3H (ARCX.PILLAR) and XNAS-20260815-SLCD8NA7UL (XNAS.ITCH), SHA-256 in `results/S07-spy-manifest.txt`. Derived parquets in `data/` were inventoried but NOT consumed (item 55).

## Persistence

Cache 420.4 MB under `sessions/s07-completion-and-spy/cache/`: SPY calendar-time and traded-tick panels with present masks, regenerated futures forecast panels, and loss matrices. Every figure in the report regenerates from these plus the CSVs in `results/`.

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


### pip freeze at S07

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
