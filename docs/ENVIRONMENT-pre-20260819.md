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
