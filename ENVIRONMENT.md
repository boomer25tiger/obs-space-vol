# Environment record

Captured 2026-08-19T19:01:05+00:00 (UTC) during Session 9-PRE, immediately after the environment rebuild.

## Provenance of this record

The environment that S05A captured, and that sessions S05B through S08 ran under, failed on 2026-08-19: `pandas/core/dtypes/common.py` reported 56,234 bytes under `wc -c` but returned 0 lines and could not be read, so `pandas.core.dtypes.missing` could not import `DT64NS_DTYPE` from it. The environment was REBUILT from `requirements.lock`, not patched. The broken environment is retained at `.venv-broken-20260819`. The prior record is retained at `ENVIRONMENT-pre-20260819.md`.

**Installed versions matched `requirements.lock` exactly before the failure** (verified from `.dist-info` directories without importing): numpy 2.5.2, pandas 3.0.5, scipy 1.18.0, arch 8.0.0, statsmodels 0.14.6. There was no version drift, so sessions S05B through S08 did run under the versions their runlogs record.

Equivalence after rebuild was verified by recomputing the ES/GLOBEX/B0/1day intercept fit and the full Var(log RV_M) grid from persisted artifacts: agreement to 1e-7 on the fit (rounding in the reference values) and 2.2e-16 on the grid, with all five invariants firing at their S06R counts.

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
