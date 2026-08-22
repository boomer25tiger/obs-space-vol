# Session 5 report, reliability surface and model confidence set

Run date 2026-08-18. Real data (S04 repaired panels: ES RTH 1901, ES GLOBEX 1953, NQ RTH 1901, NQ GLOBEX 1948) plus the calibrated synthetic arm. Pre-registration: `../PREREG.md`. Holdout untouched.

## 1. T1 and the resolved tripower normalisation

T1 PASSED. Correct constant mu_4/3 = 0.830861; ratio of means E[RQ]/E[TQ] on jump-free constant-volatility data = 0.99959 (tolerance 1%). The per-session mean of the RATIO carries a finite-M Jensen term (1.0164 at M=390), reported, not gated. RESOLUTION of the S04 anomaly: S04's diag.py hard-coded 1.417517 where mu_4/3 = 0.830861 belongs, understating TQ by the cube of the ratio, a factor 4.966. The 'median RQ/TQ near 6.0 in every cell' was therefore 4.97 x the true ratio; the true medians implied are 1.18-1.62, which is ordinary jump content, not an anomaly. (S04 artifacts are left as they stand; this report supersedes their RQ/TQ ratio column.)

## 2. Part A, quarticity ratio R = (2/M) Q / P^2

Pre-registered selection metric: mean share of sessions with R > 10x cell median, B0, per (root,geom,year,M) cell. Ranking (smaller = more stable):

| variant | share R > 10x median | mean p95/median |
|---|---|---|
| TRQ3_TRV3 | 0.000000 | 1.420 |
| TRQ5_TRV5 | 0.000000 | 1.685 |
| TRQ10_TRV10 | 0.000000 | 2.207 |
| TQ_BV | 0.000180 | 2.020 |
| MEDRQ_MEDRV | 0.000595 | 2.138 |
| RQ_RV | 0.002129 | 2.521 |

**Selected variant: TRQ3_TRV3** (truncated quarticity / truncated RV at 3 local sd). Selection ran before any lambda was produced.

Pooled-year distributions at the finest M, B0 (full table for every cell, including B1 and per-year rows: `s05_parta.csv`):

| root | geom | variant | median R | med/(2/M) | p95 | p99 | share>10x med | acf1 | acf10 |
|---|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | RQ_RV | 3.80e-03 | 2.62 | 1.50e-02 | 4.44e-02 | 0.0143 | 0.05 | 0.06 |
| ES | GLOBEX | TQ_BV | 3.34e-03 | 2.31 | 8.52e-03 | 1.55e-02 | 0.0026 | 0.02 | -0.00 |
| ES | GLOBEX | TRQ3_TRV3 | 1.91e-03 | 1.32 | 2.53e-03 | 3.22e-03 | 0.0000 | 0.28 | 0.20 |
| ES | GLOBEX | TRQ5_TRV5 | 2.71e-03 | 1.87 | 3.74e-03 | 5.19e-03 | 0.0000 | 0.23 | 0.13 |
| ES | GLOBEX | TRQ10_TRV10 | 3.70e-03 | 2.55 | 6.73e-03 | 9.71e-03 | 0.0000 | 0.09 | 0.05 |
| ES | GLOBEX | MEDRQ_MEDRV | 3.22e-03 | 2.22 | 7.95e-03 | 2.01e-02 | 0.0036 | 0.07 | 0.03 |
| NQ | GLOBEX | RQ_RV | 4.90e-03 | 3.38 | 2.08e-02 | 5.73e-02 | 0.0118 | 0.12 | 0.07 |
| NQ | GLOBEX | TQ_BV | 4.02e-03 | 2.78 | 1.03e-02 | 2.10e-02 | 0.0021 | 0.14 | 0.05 |
| NQ | GLOBEX | TRQ3_TRV3 | 2.15e-03 | 1.48 | 2.88e-03 | 3.54e-03 | 0.0000 | 0.20 | 0.10 |
| NQ | GLOBEX | TRQ5_TRV5 | 3.13e-03 | 2.16 | 4.25e-03 | 5.40e-03 | 0.0000 | 0.23 | 0.12 |
| NQ | GLOBEX | TRQ10_TRV10 | 4.63e-03 | 3.19 | 8.16e-03 | 1.06e-02 | 0.0000 | 0.22 | 0.12 |
| NQ | GLOBEX | MEDRQ_MEDRV | 4.19e-03 | 2.89 | 1.06e-02 | 2.43e-02 | 0.0041 | 0.12 | 0.08 |
| ES | RTH | RQ_RV | 8.02e-03 | 1.56 | 2.11e-02 | 4.20e-02 | 0.0011 | 0.08 | 0.09 |
| ES | RTH | TQ_BV | 7.03e-03 | 1.37 | 1.36e-02 | 2.17e-02 | 0.0000 | 0.11 | 0.09 |
| ES | RTH | TRQ3_TRV3 | 5.63e-03 | 1.10 | 6.98e-03 | 8.36e-03 | 0.0000 | 0.13 | 0.09 |
| ES | RTH | TRQ5_TRV5 | 7.36e-03 | 1.43 | 1.06e-02 | 1.30e-02 | 0.0000 | 0.14 | 0.09 |
| ES | RTH | TRQ10_TRV10 | 8.01e-03 | 1.56 | 1.90e-02 | 3.14e-02 | 0.0000 | 0.10 | 0.08 |
| ES | RTH | MEDRQ_MEDRV | 6.99e-03 | 1.36 | 1.39e-02 | 2.19e-02 | 0.0011 | 0.09 | 0.09 |
| NQ | RTH | RQ_RV | 9.02e-03 | 1.76 | 1.98e-02 | 3.87e-02 | 0.0005 | 0.18 | 0.13 |
| NQ | RTH | TQ_BV | 7.55e-03 | 1.47 | 1.52e-02 | 2.27e-02 | 0.0000 | 0.16 | 0.12 |
| NQ | RTH | TRQ3_TRV3 | 5.97e-03 | 1.16 | 7.42e-03 | 8.75e-03 | 0.0000 | 0.27 | 0.17 |
| NQ | RTH | TRQ5_TRV5 | 8.07e-03 | 1.57 | 1.14e-02 | 1.31e-02 | 0.0000 | 0.27 | 0.18 |
| NQ | RTH | TRQ10_TRV10 | 9.02e-03 | 1.76 | 1.90e-02 | 3.07e-02 | 0.0000 | 0.20 | 0.13 |
| NQ | RTH | MEDRQ_MEDRV | 7.83e-03 | 1.53 | 1.58e-02 | 2.33e-02 | 0.0011 | 0.19 | 0.15 |

## 3. Part C, reliability surface

Pooled (year, tercile) rows below; the full surface (9 years x 4 tercile groups x horizons x M x B0/B1, 1,928 cells x 6 estimators) is `s05_partc_wide.csv` with a disagreement column (max - min across estimators).

| root | geom | B | horizon | M | E1_a_exp_L1-5 | E1_a_exp_L1-10 | E1_d_model_L1-5 | E1_d_model_L1-10 | E2 | E4 | disagreement |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | 1day | 23 | 0.777 | 0.758 | 0.883 | 0.968 | 0.789 | 0.932 | 0.211 |
| ES | GLOBEX | B0 | 1day | 46 | 0.812 | 0.791 | 0.923 | 1.011 | 0.825 | 0.960 | 0.220 |
| ES | GLOBEX | B0 | 1day | 138 | 0.852 | 0.831 | 0.968 | 1.061 | 0.862 | 0.985 | 0.231 |
| ES | GLOBEX | B0 | 1day | 345 | 0.862 | 0.851 | 0.989 | 1.055 | 0.856 | 0.993 | 0.204 |
| ES | GLOBEX | B0 | 1day | 1380 | 0.878 | 0.867 | 0.998 | 1.091 | 0.845 | 0.998 | 0.246 |
| ES | GLOBEX | B0 | 1h | 60 | 1.461 | 1.461 | -50.648 | -9.564 | 0.997 | 1.000 | 52.109 |
| ES | GLOBEX | B0 | 30min | 30 | 1.084 | 1.206 | 1.728 | 3.503 | 0.995 | 1.000 | 2.508 |
| ES | GLOBEX | B1 | 1day | 23 | 0.779 | 0.761 | 0.885 | 0.944 | 0.790 | 0.933 | 0.183 |
| ES | GLOBEX | B1 | 1day | 46 | 0.810 | 0.790 | 0.921 | 1.010 | 0.823 | 0.961 | 0.220 |
| ES | GLOBEX | B1 | 1day | 138 | 0.852 | 0.830 | 0.968 | 1.061 | 0.861 | 0.985 | 0.231 |
| ES | GLOBEX | B1 | 1day | 345 | 0.862 | 0.850 | 0.988 | 1.054 | 0.855 | 0.993 | 0.204 |
| ES | GLOBEX | B1 | 1day | 1380 | 0.878 | 0.867 | 0.998 | 1.091 | 0.844 | 0.998 | 0.247 |
| ES | GLOBEX | B1 | 1h | 60 | 1.461 | 1.461 | -50.650 | -9.564 | 0.997 | 1.000 | 52.112 |
| ES | GLOBEX | B1 | 30min | 30 | 1.076 | 1.198 | 1.730 | 3.376 | 0.995 | 1.000 | 2.381 |
| ES | RTH | B0 | 1day | 13 | 0.767 | 0.741 | 0.885 | 0.947 | 0.807 | 0.914 | 0.206 |
| ES | RTH | B0 | 1day | 26 | 0.807 | 0.790 | 0.917 | 0.980 | 0.860 | 0.948 | 0.190 |
| ES | RTH | B0 | 1day | 78 | 0.845 | 0.817 | 0.961 | 1.028 | 0.895 | 0.979 | 0.211 |
| ES | RTH | B0 | 1day | 195 | 0.868 | 0.838 | 0.986 | 1.054 | 0.907 | 0.991 | 0.217 |
| ES | RTH | B0 | 1day | 390 | 0.873 | 0.853 | 0.992 | 1.057 | 0.912 | 0.995 | 0.205 |
| ES | RTH | B0 | 1h | 60 | 0.808 | 0.787 | 0.959 | 0.946 | 0.931 | 0.976 | 0.190 |
| ES | RTH | B0 | 30min | 30 | 0.924 | 0.812 | 1.101 | 1.024 | 0.792 | 0.999 | 0.309 |
| ES | RTH | B1 | 1day | 13 | 0.770 | 0.738 | 0.881 | 0.943 | 0.808 | 0.914 | 0.205 |
| ES | RTH | B1 | 1day | 26 | 0.813 | 0.789 | 0.916 | 0.979 | 0.862 | 0.948 | 0.190 |
| ES | RTH | B1 | 1day | 78 | 0.844 | 0.815 | 0.959 | 1.026 | 0.896 | 0.979 | 0.211 |
| ES | RTH | B1 | 1day | 195 | 0.867 | 0.836 | 0.985 | 1.053 | 0.908 | 0.991 | 0.216 |
| ES | RTH | B1 | 1day | 390 | 0.871 | 0.851 | 0.990 | 1.056 | 0.913 | 0.995 | 0.204 |
| ES | RTH | B1 | 1h | 60 | 0.813 | 0.792 | 0.965 | 0.952 | 0.932 | 0.976 | 0.185 |
| ES | RTH | B1 | 30min | 30 | 0.921 | 0.817 | 1.107 | 1.030 | 0.791 | 0.999 | 0.316 |
| NQ | GLOBEX | B0 | 1day | 23 | 0.746 | 0.728 | 0.861 | 0.917 | 0.777 | 0.922 | 0.194 |
| NQ | GLOBEX | B0 | 1day | 46 | 0.789 | 0.770 | 0.889 | 0.969 | 0.822 | 0.956 | 0.200 |
| NQ | GLOBEX | B0 | 1day | 138 | 0.828 | 0.815 | 0.941 | 1.026 | 0.868 | 0.983 | 0.211 |
| NQ | GLOBEX | B0 | 1day | 345 | 0.849 | 0.829 | 0.965 | 1.028 | 0.867 | 0.993 | 0.199 |
| NQ | GLOBEX | B0 | 1day | 1380 | 0.867 | 0.843 | 0.985 | 1.078 | 0.876 | 0.998 | 0.234 |
| NQ | GLOBEX | B0 | 1h | 60 | 1.463 | 1.463 | -33.479 | -8.687 | 0.997 | 1.000 | 34.942 |
| NQ | GLOBEX | B0 | 30min | 30 | 1.076 | 1.198 | 1.766 | 3.484 | 0.997 | 1.000 | 2.487 |
| NQ | GLOBEX | B1 | 1day | 23 | 0.748 | 0.721 | 0.864 | 0.922 | 0.778 | 0.922 | 0.201 |
| NQ | GLOBEX | B1 | 1day | 46 | 0.789 | 0.772 | 0.889 | 0.972 | 0.820 | 0.956 | 0.200 |
| NQ | GLOBEX | B1 | 1day | 138 | 0.827 | 0.816 | 0.940 | 1.027 | 0.867 | 0.983 | 0.211 |
| NQ | GLOBEX | B1 | 1day | 345 | 0.850 | 0.829 | 0.966 | 1.028 | 0.866 | 0.993 | 0.199 |
| NQ | GLOBEX | B1 | 1day | 1380 | 0.867 | 0.844 | 0.986 | 1.078 | 0.874 | 0.998 | 0.235 |
| NQ | GLOBEX | B1 | 1h | 60 | 1.463 | 1.463 | -33.481 | -8.688 | 0.997 | 1.000 | 34.944 |
| NQ | GLOBEX | B1 | 30min | 30 | 1.078 | 1.190 | 1.768 | 3.495 | 0.997 | 1.000 | 2.498 |
| NQ | RTH | B0 | 1day | 13 | 0.728 | 0.718 | 0.813 | 0.890 | 0.797 | 0.901 | 0.183 |
| NQ | RTH | B0 | 1day | 26 | 0.780 | 0.769 | 0.894 | 0.954 | 0.860 | 0.939 | 0.185 |
| NQ | RTH | B0 | 1day | 78 | 0.830 | 0.809 | 0.928 | 1.018 | 0.908 | 0.976 | 0.209 |
| NQ | RTH | B0 | 1day | 195 | 0.860 | 0.840 | 0.962 | 1.026 | 0.926 | 0.990 | 0.186 |
| NQ | RTH | B0 | 1day | 390 | 0.867 | 0.844 | 0.994 | 1.062 | 0.935 | 0.995 | 0.218 |
| NQ | RTH | B0 | 1h | 60 | 0.741 | 0.732 | 0.917 | 0.894 | 0.936 | 0.978 | 0.246 |
| NQ | RTH | B0 | 30min | 30 | 0.915 | 0.771 | 1.167 | 1.034 | 0.927 | 0.961 | 0.396 |
| NQ | RTH | B1 | 1day | 13 | 0.729 | 0.710 | 0.815 | 0.893 | 0.800 | 0.900 | 0.190 |
| NQ | RTH | B1 | 1day | 26 | 0.787 | 0.760 | 0.894 | 0.956 | 0.865 | 0.939 | 0.196 |
| NQ | RTH | B1 | 1day | 78 | 0.830 | 0.810 | 0.928 | 0.989 | 0.910 | 0.976 | 0.179 |
| NQ | RTH | B1 | 1day | 195 | 0.859 | 0.840 | 0.961 | 1.026 | 0.927 | 0.990 | 0.186 |
| NQ | RTH | B1 | 1day | 390 | 0.866 | 0.843 | 0.992 | 1.061 | 0.936 | 0.995 | 0.218 |
| NQ | RTH | B1 | 1h | 60 | 0.749 | 0.739 | 0.927 | 0.902 | 0.938 | 0.978 | 0.239 |
| NQ | RTH | B1 | 30min | 30 | 0.915 | 0.778 | 1.147 | 1.044 | 0.928 | 0.960 | 0.369 |

Estimator disagreement across pooled cells: median 0.211, p90 2.493, max 52.112. Estimators are reported separately throughout; nothing is averaged.

## 4. Part E, MCS composition

Hansen-Lunde-Nason MCS, 10,000 moving-block bootstrap resamples (seed 20260821), 75% and 90% sets, per scheme and cell. Full p-values per model: `s05_mcs.csv`.

| root | geom | B | horizon | scheme | n | MCS-75 | MCS-90 |
|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | 1day | S-A | 1453 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH |
| ES | GLOBEX | B0 | 1day | S-B_q0.80 | 291 | M4_HARQ|M5_RGARCH | M4_HARQ|M5_RGARCH |
| ES | GLOBEX | B0 | 1day | S-B_q0.90 | 146 | M4_HARQ|M5_RGARCH | M4_HARQ|M5_RGARCH |
| ES | GLOBEX | B0 | 1day | S-C_q0.80 | 291 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH |
| ES | GLOBEX | B0 | 1day | S-C_q0.90 | 146 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_GK|M6_PARK |
| ES | GLOBEX | B0 | 1h | S-A | 40996 | M6_GK | M6_GK |
| ES | GLOBEX | B0 | 1h | S-B_q0.80 | 8199 | M6_GK | M6_GK |
| ES | GLOBEX | B0 | 1h | S-B_q0.90 | 4100 | M6_GK | M6_GK |
| ES | GLOBEX | B0 | 1h | S-C_q0.80 | 8199 | M6_GK | M6_GK |
| ES | GLOBEX | B0 | 1h | S-C_q0.90 | 4100 | M6_GK | M6_GK |
| ES | GLOBEX | B0 | 30min | S-A | 21604 | M6_GK | M6_GK |
| ES | GLOBEX | B0 | 30min | S-B_q0.80 | 4321 | M6_GK | M6_GK |
| ES | GLOBEX | B0 | 30min | S-B_q0.90 | 2161 | M6_GK | M6_GK |
| ES | GLOBEX | B0 | 30min | S-C_q0.80 | 4321 | M4_HARQ | M4_HARQ |
| ES | GLOBEX | B0 | 30min | S-C_q0.90 | 2161 | M4_HARQ | M4_HARQ |
| ES | GLOBEX | B1 | 1day | S-A | 1453 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH |
| ES | GLOBEX | B1 | 1day | S-B_q0.80 | 291 | M4_HARQ|M5_RGARCH | M4_HARQ|M5_RGARCH |
| ES | GLOBEX | B1 | 1day | S-B_q0.90 | 146 | M4_HARQ|M5_RGARCH | M4_HARQ|M5_RGARCH |
| ES | GLOBEX | B1 | 1day | S-C_q0.80 | 291 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH |
| ES | GLOBEX | B1 | 1day | S-C_q0.90 | 146 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_GK|M6_PARK |
| ES | GLOBEX | B1 | 1h | S-A | 1403 | M6_GK | M6_GK |
| ES | GLOBEX | B1 | 1h | S-B_q0.80 | 281 | M2_HAR|M3_HARJ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | GLOBEX | B1 | 1h | S-B_q0.90 | 141 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | GLOBEX | B1 | 1h | S-C_q0.80 | 281 | M6_GK | M6_GK |
| ES | GLOBEX | B1 | 1h | S-C_q0.90 | 141 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | GLOBEX | B1 | 30min | S-A | 79538 | M6_GK | M6_GK |
| ES | GLOBEX | B1 | 30min | S-B_q0.80 | 15908 | M6_GK | M6_GK |
| ES | GLOBEX | B1 | 30min | S-B_q0.90 | 7954 | M6_GK | M6_GK |
| ES | GLOBEX | B1 | 30min | S-C_q0.80 | 15908 | M6_GK | M6_GK |
| ES | GLOBEX | B1 | 30min | S-C_q0.90 | 7954 | M6_GK | M6_GK |
| ES | RTH | B0 | 1day | S-A | 1401 | M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| ES | RTH | B0 | 1day | S-B_q0.80 | 280 | M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| ES | RTH | B0 | 1day | S-B_q0.90 | 140 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B0 | 1day | S-C_q0.80 | 280 | M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| ES | RTH | B0 | 1day | S-C_q0.90 | 140 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK |
| ES | RTH | B0 | 1h | S-A | 10906 | M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| ES | RTH | B0 | 1h | S-B_q0.80 | 2181 | M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| ES | RTH | B0 | 1h | S-B_q0.90 | 1091 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B0 | 1h | S-C_q0.80 | 2181 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B0 | 1h | S-C_q0.90 | 1091 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B0 | 30min | S-A | 22312 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B0 | 30min | S-B_q0.80 | 4463 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B0 | 30min | S-B_q0.90 | 2232 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B0 | 30min | S-C_q0.80 | 4463 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B0 | 30min | S-C_q0.90 | 2232 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B1 | 1day | S-A | 1401 | M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| ES | RTH | B1 | 1day | S-B_q0.80 | 280 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B1 | 1day | S-B_q0.90 | 140 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B1 | 1day | S-C_q0.80 | 280 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B1 | 1day | S-C_q0.90 | 140 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK |
| ES | RTH | B1 | 1h | S-A | 10906 | M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| ES | RTH | B1 | 1h | S-B_q0.80 | 2181 | M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| ES | RTH | B1 | 1h | S-B_q0.90 | 1091 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B1 | 1h | S-C_q0.80 | 2181 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B1 | 1h | S-C_q0.90 | 1091 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B1 | 30min | S-A | 22312 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B1 | 30min | S-B_q0.80 | 4463 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B1 | 30min | S-B_q0.90 | 2232 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B1 | 30min | S-C_q0.80 | 4463 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES | RTH | B1 | 30min | S-C_q0.90 | 2232 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | GLOBEX | B0 | 1day | S-A | 1448 | M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| NQ | GLOBEX | B0 | 1day | S-B_q0.80 | 290 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | GLOBEX | B0 | 1day | S-B_q0.90 | 145 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | GLOBEX | B0 | 1day | S-C_q0.80 | 290 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | GLOBEX | B0 | 1day | S-C_q0.90 | 145 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ|M6_PARK |
| NQ | GLOBEX | B0 | 1h | S-A | 22259 | M6_GK | M6_GK |
| NQ | GLOBEX | B0 | 1h | S-B_q0.80 | 4452 | M6_GK | M6_GK |
| NQ | GLOBEX | B0 | 1h | S-B_q0.90 | 2226 | M6_GK | M6_GK |
| NQ | GLOBEX | B0 | 1h | S-C_q0.80 | 4452 | M6_GK | M6_GK |
| NQ | GLOBEX | B0 | 1h | S-C_q0.90 | 2226 | M6_GK | M6_GK |
| NQ | GLOBEX | B0 | 30min | S-A | 80900 | M6_GK | M6_GK |
| NQ | GLOBEX | B0 | 30min | S-B_q0.80 | 16180 | M6_GK | M6_GK |
| NQ | GLOBEX | B0 | 30min | S-B_q0.90 | 8090 | M6_GK | M6_GK |
| NQ | GLOBEX | B0 | 30min | S-C_q0.80 | 16180 | M6_GK | M6_GK |
| NQ | GLOBEX | B0 | 30min | S-C_q0.90 | 8090 | M6_GK | M6_GK |
| NQ | GLOBEX | B1 | 1day | S-A | 1448 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | GLOBEX | B1 | 1day | S-B_q0.80 | 290 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | GLOBEX | B1 | 1day | S-B_q0.90 | 145 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | GLOBEX | B1 | 1day | S-C_q0.80 | 290 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | GLOBEX | B1 | 1day | S-C_q0.90 | 145 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ|M6_GK|M6_PARK |
| NQ | GLOBEX | B1 | 1h | S-A | 39503 | M6_GK | M6_GK |
| NQ | GLOBEX | B1 | 1h | S-B_q0.80 | 7901 | M6_GK | M6_GK |
| NQ | GLOBEX | B1 | 1h | S-B_q0.90 | 3951 | M6_GK | M6_GK |
| NQ | GLOBEX | B1 | 1h | S-C_q0.80 | 7901 | M6_GK | M6_GK |
| NQ | GLOBEX | B1 | 1h | S-C_q0.90 | 3951 | M6_GK | M6_GK |
| NQ | GLOBEX | B1 | 30min | S-A | 83735 | M6_GK | M6_GK |
| NQ | GLOBEX | B1 | 30min | S-B_q0.80 | 16747 | M6_GK | M6_GK |
| NQ | GLOBEX | B1 | 30min | S-B_q0.90 | 8374 | M6_GK | M6_GK |
| NQ | GLOBEX | B1 | 30min | S-C_q0.80 | 16747 | M6_GK | M6_GK |
| NQ | GLOBEX | B1 | 30min | S-C_q0.90 | 8374 | M6_GK | M6_GK |
| NQ | RTH | B0 | 1day | S-A | 1401 | M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| NQ | RTH | B0 | 1day | S-B_q0.80 | 280 | M2_HAR|M3_HARJ|M4_HARQ | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B0 | 1day | S-B_q0.90 | 140 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B0 | 1day | S-C_q0.80 | 280 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B0 | 1day | S-C_q0.90 | 140 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ|M6_PARK |
| NQ | RTH | B0 | 1h | S-A | 10906 | M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| NQ | RTH | B0 | 1h | S-B_q0.80 | 2181 | M2_HAR|M4_HARQ | M1_EWMA|M2_HAR|M4_HARQ |
| NQ | RTH | B0 | 1h | S-B_q0.90 | 1091 | M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| NQ | RTH | B0 | 1h | S-C_q0.80 | 2181 | M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| NQ | RTH | B0 | 1h | S-C_q0.90 | 1091 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B0 | 30min | S-A | 22312 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B0 | 30min | S-B_q0.80 | 4463 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B0 | 30min | S-B_q0.90 | 2232 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B0 | 30min | S-C_q0.80 | 4463 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B0 | 30min | S-C_q0.90 | 2232 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B1 | 1day | S-A | 1401 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B1 | 1day | S-B_q0.80 | 280 | M2_HAR|M4_HARQ | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B1 | 1day | S-B_q0.90 | 140 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B1 | 1day | S-C_q0.80 | 280 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B1 | 1day | S-C_q0.90 | 140 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ|M6_PARK |
| NQ | RTH | B1 | 1h | S-A | 10906 | M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| NQ | RTH | B1 | 1h | S-B_q0.80 | 2181 | M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| NQ | RTH | B1 | 1h | S-B_q0.90 | 1091 | M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| NQ | RTH | B1 | 1h | S-C_q0.80 | 2181 | M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| NQ | RTH | B1 | 1h | S-C_q0.90 | 1091 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B1 | 30min | S-A | 22312 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B1 | 30min | S-B_q0.80 | 4463 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B1 | 30min | S-B_q0.90 | 2232 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B1 | 30min | S-C_q0.80 | 4463 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ | RTH | B1 | 30min | S-C_q0.90 | 2232 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |

**Primary result, S-B vs S-C:** composition differs in 37 of 96 (cell x quantile x level) comparisons. Differing cells:

| cell | q | level | S-B set | S-C set |
|---|---|---|---|---|
| ES/GLOBEX/B0/1day | 0.80 | mcs75 | M4_HARQ|M5_RGARCH | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH |
| ES/GLOBEX/B0/1day | 0.80 | mcs90 | M4_HARQ|M5_RGARCH | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH |
| ES/GLOBEX/B0/1day | 0.90 | mcs75 | M4_HARQ|M5_RGARCH | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH |
| ES/GLOBEX/B0/1day | 0.90 | mcs90 | M4_HARQ|M5_RGARCH | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_GK|M6_PARK |
| ES/GLOBEX/B0/30min | 0.80 | mcs75 | M6_GK | M4_HARQ |
| ES/GLOBEX/B0/30min | 0.80 | mcs90 | M6_GK | M4_HARQ |
| ES/GLOBEX/B0/30min | 0.90 | mcs75 | M6_GK | M4_HARQ |
| ES/GLOBEX/B0/30min | 0.90 | mcs90 | M6_GK | M4_HARQ |
| ES/GLOBEX/B1/1day | 0.80 | mcs75 | M4_HARQ|M5_RGARCH | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH |
| ES/GLOBEX/B1/1day | 0.80 | mcs90 | M4_HARQ|M5_RGARCH | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH |
| ES/GLOBEX/B1/1day | 0.90 | mcs75 | M4_HARQ|M5_RGARCH | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH |
| ES/GLOBEX/B1/1day | 0.90 | mcs90 | M4_HARQ|M5_RGARCH | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_GK|M6_PARK |
| ES/GLOBEX/B1/1h | 0.80 | mcs75 | M2_HAR|M3_HARJ | M6_GK |
| ES/GLOBEX/B1/1h | 0.80 | mcs90 | M2_HAR|M3_HARJ|M4_HARQ | M6_GK |
| ES/RTH/B0/1day | 0.90 | mcs75 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES/RTH/B0/1day | 0.90 | mcs90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK |
| ES/RTH/B0/1h | 0.80 | mcs75 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES/RTH/B0/1h | 0.80 | mcs90 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES/RTH/B0/1h | 0.90 | mcs75 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES/RTH/B1/1day | 0.80 | mcs75 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES/RTH/B1/1day | 0.90 | mcs90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK |
| ES/RTH/B1/1h | 0.80 | mcs75 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES/RTH/B1/1h | 0.80 | mcs90 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES/RTH/B1/1h | 0.90 | mcs75 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES/RTH/B1/30min | 0.80 | mcs75 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| ES/RTH/B1/30min | 0.90 | mcs75 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ/GLOBEX/B0/1day | 0.90 | mcs90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ|M6_PARK |
| NQ/GLOBEX/B1/1day | 0.90 | mcs90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ|M6_GK|M6_PARK |
| NQ/RTH/B0/1day | 0.80 | mcs90 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ/RTH/B0/1day | 0.90 | mcs90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ|M6_PARK |
| NQ/RTH/B0/1h | 0.80 | mcs90 | M1_EWMA|M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| NQ/RTH/B0/1h | 0.90 | mcs75 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ/RTH/B0/1h | 0.90 | mcs90 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ/RTH/B1/1day | 0.80 | mcs90 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ/RTH/B1/1day | 0.90 | mcs90 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ|M6_PARK |
| NQ/RTH/B1/1h | 0.90 | mcs75 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| NQ/RTH/B1/1h | 0.90 | mcs90 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |

**IC with vs without the reliability correction:** the correction divides every model's IC by the same sqrt(lambda) within a cell, so it rescales the IC column without reordering models inside a cell; the corrected columns are in section 5 and `s05_metrics.csv`. Where lambda varies across cells the correction changes CROSS-cell comparisons; those columns are reported side by side.

## 5. IC, corrected IC, R2, corrected R2, IR, hit rate

S-A rows shown; every scheme row is in `s05_metrics.csv`.

| root | geom | B | horizon | model | lam_hat | IC(log) | IC corr | IC spear | R2 | R2 corr | IC-IR | hit | QLIKE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | 1day | M1_EWMA | 0.998 | 0.707 | 0.707 | 0.705 | 0.454 | 0.455 | 1.24 | 0.517 | 0.2921 |
| ES | GLOBEX | B0 | 1day | M2_HAR | 0.998 | 0.838 | 0.839 | 0.834 | 0.681 | 0.683 | 4.11 | 0.399 | 0.1627 |
| ES | GLOBEX | B0 | 1day | M3_HARJ | 0.998 | 0.832 | 0.833 | 0.828 | 0.671 | 0.672 | 4.07 | 0.414 | 0.1642 |
| ES | GLOBEX | B0 | 1day | M4_HARQ | 0.998 | -0.066 | -0.066 | 0.822 | -632.694 | -633.927 | 1.95 | 0.403 | 1704465726635640266832269781491433390734911383965047032187573334052409441087615184560797480183903023446999806493460080127087678374820531018357677008026686921881534497816838307908013029136950467050856654860092062388106046484226383446812687169799999851070881387763142977004640552246386661907234816.0000 |
| ES | GLOBEX | B0 | 1day | M5_RGARCH | 0.998 | 0.832 | 0.833 | 0.826 | 0.655 | 0.656 | 3.77 | 0.404 | 0.1654 |
| ES | GLOBEX | B0 | 1day | M6_GK | 0.998 | 0.766 | 0.767 | 0.760 | 0.303 | 0.303 | 3.52 | 0.494 | 0.5920 |
| ES | GLOBEX | B0 | 1day | M6_PARK | 0.998 | 0.755 | 0.756 | 0.744 | 0.236 | 0.237 | 3.24 | 0.514 | 0.6648 |
| ES | GLOBEX | B0 | 1h | M1_EWMA | 1.000 | nan | nan | 0.633 | nan | nan | 0.58 | 0.456 | inf |
| ES | GLOBEX | B0 | 1h | M2_HAR | 1.000 | nan | nan | 0.777 | nan | nan | 6.00 | 0.467 | inf |
| ES | GLOBEX | B0 | 1h | M3_HARJ | 1.000 | nan | nan | 0.776 | nan | nan | 5.92 | 0.470 | inf |
| ES | GLOBEX | B0 | 1h | M4_HARQ | 1.000 | nan | nan | 0.803 | nan | nan | 5.42 | 0.468 | inf |
| ES | GLOBEX | B0 | 1h | M5_RGARCH | 1.000 | nan | nan | 0.189 | nan | nan | 6.69 | 0.468 | nan |
| ES | GLOBEX | B0 | 1h | M6_GK | 1.000 | nan | nan | 0.779 | nan | nan | 5.58 | 0.483 | inf |
| ES | GLOBEX | B0 | 1h | M6_PARK | 1.000 | nan | nan | 0.778 | nan | nan | 5.59 | 0.479 | nan |
| ES | GLOBEX | B0 | 30min | M1_EWMA | 1.000 | nan | nan | 0.566 | nan | nan | 0.83 | 0.466 | inf |
| ES | GLOBEX | B0 | 30min | M2_HAR | 1.000 | nan | nan | 0.779 | nan | nan | 8.31 | 0.394 | inf |
| ES | GLOBEX | B0 | 30min | M3_HARJ | 1.000 | nan | nan | 0.775 | nan | nan | 8.03 | 0.396 | inf |
| ES | GLOBEX | B0 | 30min | M4_HARQ | 1.000 | nan | nan | 0.815 | nan | nan | 8.55 | 0.394 | inf |
| ES | GLOBEX | B0 | 30min | M5_RGARCH | 1.000 | nan | nan | 0.511 | nan | nan | 6.81 | 0.394 | inf |
| ES | GLOBEX | B0 | 30min | M6_GK | 1.000 | nan | nan | 0.807 | nan | nan | 7.29 | 0.438 | inf |
| ES | GLOBEX | B0 | 30min | M6_PARK | 1.000 | nan | nan | 0.806 | nan | nan | 7.17 | 0.431 | nan |
| ES | GLOBEX | B1 | 1day | M1_EWMA | 0.998 | 0.707 | 0.707 | 0.706 | 0.451 | 0.452 | 1.22 | 0.524 | 0.2918 |
| ES | GLOBEX | B1 | 1day | M2_HAR | 0.998 | 0.839 | 0.840 | 0.835 | 0.682 | 0.683 | 4.14 | 0.402 | 0.1630 |
| ES | GLOBEX | B1 | 1day | M3_HARJ | 0.998 | 0.016 | 0.016 | 0.817 | -312.960 | -313.565 | 2.98 | 0.415 | 119545987243525341990610050437670455087714620097211107464097997264753155586253773803669054057544203392914237420887070378480147159742836125203185343294495604110423622606733885407914803714987353723183375736961147383813327890715366690918043789193517462228713197790531994743698683805440051288997888.0000 |
| ES | GLOBEX | B1 | 1day | M4_HARQ | 0.998 | 0.002 | 0.002 | 0.817 | -1878.080 | -1881.715 | 1.49 | 0.404 | 1749718837332281427959535334471967108548054987799611600339133353326007175368245616607540093218287006052970603203970355249038745903173908899247079506275234175496703463970828638352578787341669362768919063602379329808262046397488051428329660328872460180782187114122026792125165004632138943236669440.0000 |
| ES | GLOBEX | B1 | 1day | M5_RGARCH | 0.998 | 0.836 | 0.836 | 0.831 | 0.674 | 0.675 | 3.79 | 0.410 | 0.1610 |
| ES | GLOBEX | B1 | 1day | M6_GK | 0.998 | 0.768 | 0.769 | 0.761 | 0.294 | 0.295 | 3.44 | 0.488 | 0.6001 |
| ES | GLOBEX | B1 | 1day | M6_PARK | 0.998 | 0.756 | 0.757 | 0.746 | 0.230 | 0.231 | 3.15 | 0.514 | 0.6690 |
| ES | GLOBEX | B1 | 1h | M1_EWMA | 1.000 | nan | nan | 0.386 | nan | nan | 0.08 | 0.432 | inf |
| ES | GLOBEX | B1 | 1h | M2_HAR | 1.000 | nan | nan | 0.696 | nan | nan | 8.72 | 0.484 | inf |
| ES | GLOBEX | B1 | 1h | M3_HARJ | 1.000 | nan | nan | 0.697 | nan | nan | 8.41 | 0.484 | inf |
| ES | GLOBEX | B1 | 1h | M4_HARQ | 1.000 | nan | nan | 0.713 | nan | nan | 9.66 | 0.486 | inf |
| ES | GLOBEX | B1 | 1h | M5_RGARCH | 1.000 | nan | nan | 0.719 | nan | nan | 9.66 | 0.479 | nan |
| ES | GLOBEX | B1 | 1h | M6_GK | 1.000 | nan | nan | 0.654 | nan | nan | 6.96 | 0.484 | inf |
| ES | GLOBEX | B1 | 1h | M6_PARK | 1.000 | nan | nan | 0.645 | nan | nan | 6.83 | 0.472 | nan |
| ES | GLOBEX | B1 | 30min | M1_EWMA | 1.000 | nan | nan | 0.658 | nan | nan | 0.90 | 0.460 | inf |
| ES | GLOBEX | B1 | 30min | M2_HAR | 1.000 | nan | nan | 0.786 | nan | nan | 5.57 | 0.390 | inf |
| ES | GLOBEX | B1 | 30min | M3_HARJ | 1.000 | nan | nan | 0.787 | nan | nan | 5.48 | 0.395 | inf |
| ES | GLOBEX | B1 | 30min | M4_HARQ | 1.000 | nan | nan | 0.819 | nan | nan | 5.22 | 0.390 | inf |
| ES | GLOBEX | B1 | 30min | M5_RGARCH | 1.000 | nan | nan | 0.009 | nan | nan | -0.01 | 0.067 | nan |
| ES | GLOBEX | B1 | 30min | M6_GK | 1.000 | nan | nan | 0.798 | nan | nan | 4.83 | 0.433 | inf |
| ES | GLOBEX | B1 | 30min | M6_PARK | 1.000 | nan | nan | 0.798 | nan | nan | 4.90 | 0.421 | nan |
| ES | RTH | B0 | 1day | M1_EWMA | 0.995 | 0.720 | 0.722 | 0.721 | 0.439 | 0.441 | 2.29 | 0.502 | 0.2997 |
| ES | RTH | B0 | 1day | M2_HAR | 0.995 | 0.834 | 0.836 | 0.821 | 0.677 | 0.681 | 3.50 | 0.358 | 0.1715 |
| ES | RTH | B0 | 1day | M3_HARJ | 0.995 | 0.812 | 0.814 | 0.803 | 0.642 | 0.645 | 3.12 | 0.384 | 0.2201 |
| ES | RTH | B0 | 1day | M4_HARQ | 0.995 | -0.057 | -0.057 | 0.803 | -634.687 | -637.974 | 1.81 | 0.356 | 741329082564666819215955183254514530198951202525934919089693814537053039659267816113972639639594800488773438384137788748254110020403366405666036812323537652177988628352415576120772695956389781892608528539807854878035669154077714506575571252122563637790136809953556784584471959015673300151959552.0000 |
| ES | RTH | B0 | 1day | M5_RGARCH | 0.995 | 0.831 | 0.834 | 0.820 | 0.666 | 0.670 | 3.67 | 0.345 | 0.2379 |
| ES | RTH | B0 | 1day | M6_GK | 0.995 | 0.763 | 0.765 | 0.749 | 0.293 | 0.295 | 3.08 | 0.440 | 0.6501 |
| ES | RTH | B0 | 1day | M6_PARK | 0.995 | 0.768 | 0.770 | 0.749 | 0.294 | 0.296 | 3.25 | 0.474 | 0.6090 |
| ES | RTH | B0 | 1h | M1_EWMA | 0.976 | 0.770 | 0.780 | 0.755 | 0.566 | 0.580 | 1.29 | 0.481 | 0.3459 |
| ES | RTH | B0 | 1h | M2_HAR | 0.976 | 0.832 | 0.842 | 0.818 | 0.645 | 0.661 | 3.37 | 0.469 | 0.2517 |
| ES | RTH | B0 | 1h | M3_HARJ | 0.976 | 0.830 | 0.840 | 0.816 | 0.644 | 0.660 | 3.38 | 0.468 | 0.2537 |
| ES | RTH | B0 | 1h | M4_HARQ | 0.976 | 0.052 | 0.052 | 0.824 | -60.573 | -62.040 | 3.01 | 0.470 | 29271147397483095971409621779253181385917682213346800960176852659871991690328361451682701923738720426336276309807469405934164413946473623305075364653187004168169296402650629874057821619681540071200136795414233287651569002030604402778712804751432527455272762873244206549793286039051081411985408.0000 |
| ES | RTH | B0 | 1h | M5_RGARCH | 0.976 | 0.805 | 0.815 | 0.796 | 0.423 | 0.434 | 3.34 | 0.460 | 0.7903 |
| ES | RTH | B0 | 1h | M6_GK | 0.976 | 0.774 | 0.783 | 0.761 | 0.225 | 0.231 | 3.15 | 0.488 | 1.2200 |
| ES | RTH | B0 | 1h | M6_PARK | 0.976 | 0.769 | 0.778 | 0.754 | 0.219 | 0.225 | 3.08 | 0.486 | 1.1809 |
| ES | RTH | B0 | 30min | M1_EWMA | 0.999 | 0.784 | 0.785 | 0.770 | 0.591 | 0.592 | 1.25 | 0.470 | 0.3539 |
| ES | RTH | B0 | 30min | M2_HAR | 0.999 | 0.853 | 0.854 | 0.838 | 0.679 | 0.680 | 4.21 | 0.415 | 0.2328 |
| ES | RTH | B0 | 30min | M3_HARJ | 0.999 | 0.853 | 0.854 | 0.838 | 0.680 | 0.681 | 4.19 | 0.416 | 0.2327 |
| ES | RTH | B0 | 30min | M4_HARQ | 0.999 | 0.105 | 0.105 | 0.847 | -28.141 | -28.170 | 3.82 | 0.416 | 9658071492949698630157590100305127026430842417169824746506603697927354342087357857252175715865168998460040096414648287567371601626431558138511915891604098618374079597126216553661215047342319020220509073846872364417441165211960709990399130050987263636977625362625722810556184614556494592999424.0000 |
| ES | RTH | B0 | 30min | M5_RGARCH | 0.999 | 0.830 | 0.831 | 0.830 | 0.404 | 0.405 | 4.53 | 0.412 | 0.8736 |
| ES | RTH | B0 | 30min | M6_GK | 0.999 | 0.795 | 0.795 | 0.782 | 0.201 | 0.202 | 3.49 | 0.451 | 1.3575 |
| ES | RTH | B0 | 30min | M6_PARK | 0.999 | 0.794 | 0.794 | 0.779 | 0.245 | 0.245 | 3.48 | 0.446 | 1.1793 |
| ES | RTH | B1 | 1day | M1_EWMA | 0.995 | 0.719 | 0.721 | 0.722 | 0.452 | 0.455 | 2.29 | 0.504 | 0.3067 |
| ES | RTH | B1 | 1day | M2_HAR | 0.995 | 0.834 | 0.836 | 0.821 | 0.676 | 0.680 | 3.49 | 0.349 | 0.1740 |
| ES | RTH | B1 | 1day | M3_HARJ | 0.995 | 0.816 | 0.818 | 0.804 | 0.648 | 0.651 | 3.26 | 0.384 | 0.1953 |
| ES | RTH | B1 | 1day | M4_HARQ | 0.995 | -0.056 | -0.056 | 0.803 | -628.775 | -632.022 | 1.81 | 0.348 | 715888129874277209692619392120804214311927594333807706861500713979451823002687886152720623825171972760086709259078183632620459195966059697197776627802224789186937996655316711422176003189192914422845620135200559008806806707750868009300504174957042274559408428471143863248695035018051485165420544.0000 |
| ES | RTH | B1 | 1day | M5_RGARCH | 0.995 | 0.827 | 0.829 | 0.817 | 0.647 | 0.651 | 3.67 | 0.345 | 0.2601 |
| ES | RTH | B1 | 1day | M6_GK | 0.995 | 0.766 | 0.768 | 0.750 | 0.302 | 0.304 | 3.12 | 0.436 | 0.6380 |
| ES | RTH | B1 | 1day | M6_PARK | 0.995 | 0.770 | 0.772 | 0.751 | 0.298 | 0.299 | 3.21 | 0.471 | 0.6185 |
| ES | RTH | B1 | 1h | M1_EWMA | 0.976 | 0.773 | 0.782 | 0.758 | 0.571 | 0.585 | 1.32 | 0.482 | 0.3433 |
| ES | RTH | B1 | 1h | M2_HAR | 0.976 | 0.835 | 0.846 | 0.821 | 0.652 | 0.668 | 3.43 | 0.470 | 0.2464 |
| ES | RTH | B1 | 1h | M3_HARJ | 0.976 | 0.834 | 0.844 | 0.820 | 0.651 | 0.667 | 3.44 | 0.468 | 0.2479 |
| ES | RTH | B1 | 1h | M4_HARQ | 0.976 | 0.053 | 0.054 | 0.828 | -60.818 | -62.300 | 3.05 | 0.470 | 26883628027347778196962910739572602573188665577711175062987455349168862854130508583806562593320762831208943260565987282484892195591991181828425867539211699554594932472130844198343941887230551391414332492096112872104513872946913646803900208322223770846585106329809459575267046606472102105055232.0000 |
| ES | RTH | B1 | 1h | M5_RGARCH | 0.976 | 0.817 | 0.827 | 0.807 | 0.530 | 0.543 | 3.41 | 0.459 | 0.6134 |
| ES | RTH | B1 | 1h | M6_GK | 0.976 | 0.777 | 0.787 | 0.764 | 0.232 | 0.238 | 3.17 | 0.492 | 1.1944 |
| ES | RTH | B1 | 1h | M6_PARK | 0.976 | 0.772 | 0.782 | 0.758 | 0.226 | 0.232 | 3.13 | 0.488 | 1.1574 |
| ES | RTH | B1 | 30min | M1_EWMA | 0.999 | 0.787 | 0.788 | 0.773 | 0.597 | 0.598 | 1.28 | 0.470 | 0.3480 |
| ES | RTH | B1 | 30min | M2_HAR | 0.999 | 0.856 | 0.856 | 0.841 | 0.684 | 0.685 | 4.22 | 0.415 | 0.2273 |
| ES | RTH | B1 | 30min | M3_HARJ | 0.999 | 0.856 | 0.856 | 0.841 | 0.685 | 0.686 | 4.21 | 0.416 | 0.2273 |
| ES | RTH | B1 | 30min | M4_HARQ | 0.999 | 0.101 | 0.101 | 0.850 | -28.326 | -28.355 | 3.92 | 0.416 | 15688179035366568088018358680099545663484281905269327345644908451823255070543682561644379694134464740728967203974970138040967680806210020529030785617083430282977905347199655069041639751131831281441387889862915190695134555812755513769547786234030713030517255551441300451743257769457869668745216.0000 |
| ES | RTH | B1 | 30min | M5_RGARCH | 0.999 | 0.845 | 0.845 | 0.838 | 0.519 | 0.520 | 4.56 | 0.412 | 0.6622 |
| ES | RTH | B1 | 30min | M6_GK | 0.999 | 0.797 | 0.798 | 0.785 | 0.206 | 0.206 | 3.49 | 0.452 | 1.3327 |
| ES | RTH | B1 | 30min | M6_PARK | 0.999 | 0.796 | 0.797 | 0.782 | 0.249 | 0.249 | 3.47 | 0.448 | 1.1578 |
| NQ | GLOBEX | B0 | 1day | M1_EWMA | 0.998 | 0.686 | 0.687 | 0.697 | 0.400 | 0.401 | 1.14 | 0.535 | 0.2642 |
| NQ | GLOBEX | B0 | 1day | M2_HAR | 0.998 | 0.823 | 0.823 | 0.834 | 0.662 | 0.664 | 2.86 | 0.406 | 0.1548 |
| NQ | GLOBEX | B0 | 1day | M3_HARJ | 0.998 | 0.819 | 0.820 | 0.831 | 0.657 | 0.658 | 2.82 | 0.408 | 0.1570 |
| NQ | GLOBEX | B0 | 1day | M4_HARQ | 0.998 | -0.008 | -0.008 | 0.828 | -339.891 | -340.563 | 2.38 | 0.404 | 467308735207140547752562985004662118496968574272547289776376851649116967662248915671841311394052852478272272010793285338826078024505672276274080846010605539443658145661268604458419921323441320134011677367953210091000771768608847112761046097248008173112761281804340985211640955739766097509875712.0000 |
| NQ | GLOBEX | B0 | 1day | M5_RGARCH | 0.998 | 0.804 | 0.805 | 0.822 | 0.430 | 0.431 | 2.70 | 0.396 | 0.4054 |
| NQ | GLOBEX | B0 | 1day | M6_GK | 0.998 | 0.737 | 0.738 | 0.748 | 0.308 | 0.309 | 2.56 | 0.504 | 0.5478 |
| NQ | GLOBEX | B0 | 1day | M6_PARK | 0.998 | 0.727 | 0.727 | 0.736 | 0.254 | 0.254 | 2.32 | 0.540 | 0.6011 |
| NQ | GLOBEX | B0 | 1h | M1_EWMA | 1.000 | nan | nan | 0.588 | nan | nan | 0.63 | 0.455 | inf |
| NQ | GLOBEX | B0 | 1h | M2_HAR | 1.000 | nan | nan | 0.781 | nan | nan | 7.12 | 0.475 | inf |
| NQ | GLOBEX | B0 | 1h | M3_HARJ | 1.000 | nan | nan | 0.778 | nan | nan | 7.10 | 0.473 | inf |
| NQ | GLOBEX | B0 | 1h | M4_HARQ | 1.000 | nan | nan | 0.795 | nan | nan | 5.74 | 0.475 | inf |
| NQ | GLOBEX | B0 | 1h | M5_RGARCH | 1.000 | nan | nan | 0.256 | nan | nan | 7.57 | 0.475 | nan |
| NQ | GLOBEX | B0 | 1h | M6_GK | 1.000 | nan | nan | 0.764 | nan | nan | 6.46 | 0.481 | inf |
| NQ | GLOBEX | B0 | 1h | M6_PARK | 1.000 | nan | nan | 0.761 | nan | nan | 6.28 | 0.482 | nan |
| NQ | GLOBEX | B0 | 30min | M1_EWMA | 1.000 | nan | nan | 0.647 | nan | nan | 0.94 | 0.462 | inf |
| NQ | GLOBEX | B0 | 30min | M2_HAR | 1.000 | nan | nan | 0.796 | nan | nan | 6.63 | 0.404 | inf |
| NQ | GLOBEX | B0 | 30min | M3_HARJ | 1.000 | nan | nan | 0.800 | nan | nan | 6.57 | 0.404 | inf |
| NQ | GLOBEX | B0 | 30min | M4_HARQ | 1.000 | nan | nan | 0.826 | nan | nan | 6.09 | 0.404 | inf |
| NQ | GLOBEX | B0 | 30min | M5_RGARCH | 1.000 | nan | nan | 0.362 | nan | nan | 6.91 | 0.404 | inf |
| NQ | GLOBEX | B0 | 30min | M6_GK | 1.000 | nan | nan | 0.811 | nan | nan | 5.74 | 0.435 | inf |
| NQ | GLOBEX | B0 | 30min | M6_PARK | 1.000 | nan | nan | 0.810 | nan | nan | 5.74 | 0.436 | nan |
| NQ | GLOBEX | B1 | 1day | M1_EWMA | 0.998 | 0.687 | 0.688 | 0.698 | 0.389 | 0.389 | 1.13 | 0.551 | 0.2672 |
| NQ | GLOBEX | B1 | 1day | M2_HAR | 0.998 | 0.824 | 0.825 | 0.835 | 0.664 | 0.665 | 2.85 | 0.409 | 0.1545 |
| NQ | GLOBEX | B1 | 1day | M3_HARJ | 0.998 | -0.017 | -0.017 | 0.808 | -1012.620 | -1014.604 | 1.57 | 0.421 | 779605469693274135171115732233990006516470555454005963839915535516249742214355092083447541445034624159203506165346249629749094387475669745025693112821859927875994086502113631220708371306347810719352450483647037766922182418416665666325026261783610340029235206184442473061669566899378017095647232.0000 |
| NQ | GLOBEX | B1 | 1day | M4_HARQ | 0.998 | -0.036 | -0.036 | 0.822 | -676.554 | -677.879 | 1.91 | 0.411 | 927848997653501370290405797671440884830036683782074930070378536216461082218641115140580203198392401693282874250473010316412718608623714058293929826407752760002686347482140500828096289171625969751434831925719089381498175547090944329187424692610672359769316120705388824919551055100036154138820608.0000 |
| NQ | GLOBEX | B1 | 1day | M5_RGARCH | 0.998 | 0.803 | 0.804 | 0.820 | 0.425 | 0.426 | 2.70 | 0.402 | 0.4132 |
| NQ | GLOBEX | B1 | 1day | M6_GK | 0.998 | 0.741 | 0.742 | 0.752 | 0.308 | 0.308 | 2.54 | 0.504 | 0.5564 |
| NQ | GLOBEX | B1 | 1day | M6_PARK | 0.998 | 0.730 | 0.731 | 0.739 | 0.248 | 0.249 | 2.28 | 0.540 | 0.6145 |
| NQ | GLOBEX | B1 | 1h | M1_EWMA | 1.000 | nan | nan | 0.629 | nan | nan | 0.65 | 0.460 | inf |
| NQ | GLOBEX | B1 | 1h | M2_HAR | 1.000 | nan | nan | 0.798 | nan | nan | 7.60 | 0.479 | inf |
| NQ | GLOBEX | B1 | 1h | M3_HARJ | 1.000 | nan | nan | 0.801 | nan | nan | 7.49 | 0.478 | inf |
| NQ | GLOBEX | B1 | 1h | M4_HARQ | 1.000 | nan | nan | 0.815 | nan | nan | 6.21 | 0.479 | inf |
| NQ | GLOBEX | B1 | 1h | M5_RGARCH | 1.000 | nan | nan | 0.239 | nan | nan | 5.02 | 0.259 | nan |
| NQ | GLOBEX | B1 | 1h | M6_GK | 1.000 | nan | nan | 0.794 | nan | nan | 6.81 | 0.484 | inf |
| NQ | GLOBEX | B1 | 1h | M6_PARK | 1.000 | nan | nan | 0.790 | nan | nan | 6.55 | 0.489 | nan |
| NQ | GLOBEX | B1 | 30min | M1_EWMA | 1.000 | nan | nan | 0.648 | nan | nan | 0.94 | 0.461 | inf |
| NQ | GLOBEX | B1 | 30min | M2_HAR | 1.000 | nan | nan | 0.796 | nan | nan | 6.43 | 0.401 | inf |
| NQ | GLOBEX | B1 | 30min | M3_HARJ | 1.000 | nan | nan | 0.803 | nan | nan | 6.44 | 0.401 | inf |
| NQ | GLOBEX | B1 | 30min | M4_HARQ | 1.000 | nan | nan | 0.823 | nan | nan | 5.84 | 0.401 | inf |
| NQ | GLOBEX | B1 | 30min | M5_RGARCH | 1.000 | nan | nan | 0.262 | nan | nan | 6.68 | 0.401 | inf |
| NQ | GLOBEX | B1 | 30min | M6_GK | 1.000 | nan | nan | 0.808 | nan | nan | 5.63 | 0.433 | inf |
| NQ | GLOBEX | B1 | 30min | M6_PARK | 1.000 | nan | nan | 0.806 | nan | nan | 5.60 | 0.434 | nan |
| NQ | RTH | B0 | 1day | M1_EWMA | 0.995 | 0.702 | 0.703 | 0.703 | 0.382 | 0.384 | 1.69 | 0.528 | 0.2715 |
| NQ | RTH | B0 | 1day | M2_HAR | 0.995 | 0.829 | 0.831 | 0.824 | 0.676 | 0.679 | 2.96 | 0.374 | 0.1521 |
| NQ | RTH | B0 | 1day | M3_HARJ | 0.995 | 0.821 | 0.823 | 0.816 | 0.664 | 0.667 | 3.06 | 0.396 | 0.1584 |
| NQ | RTH | B0 | 1day | M4_HARQ | 0.995 | -0.003 | -0.003 | 0.816 | -364.528 | -366.497 | 2.34 | 0.375 | 243220010666692850338381217700033181054799324885789001987546034995734923161866525851896204179712874775833842154312141433461361864777647818968252049720664866118533732634519461792157599795281238013126288023717057734294634837353311103187357177768383663795832139478816044244427739576777807350464512.0000 |
| NQ | RTH | B0 | 1day | M5_RGARCH | 0.995 | 0.814 | 0.817 | 0.812 | 0.142 | 0.142 | 3.10 | 0.363 | 0.6619 |
| NQ | RTH | B0 | 1day | M6_GK | 0.995 | 0.750 | 0.752 | 0.736 | 0.323 | 0.325 | 2.96 | 0.461 | 0.4765 |
| NQ | RTH | B0 | 1day | M6_PARK | 0.995 | 0.753 | 0.755 | 0.739 | 0.320 | 0.322 | 3.07 | 0.497 | 0.4672 |
| NQ | RTH | B0 | 1h | M1_EWMA | 0.978 | 0.741 | 0.749 | 0.732 | 0.493 | 0.504 | 1.08 | 0.477 | 0.3793 |
| NQ | RTH | B0 | 1h | M2_HAR | 0.978 | 0.805 | 0.814 | 0.795 | 0.597 | 0.610 | 3.24 | 0.473 | 0.3201 |
| NQ | RTH | B0 | 1h | M3_HARJ | 0.978 | 0.804 | 0.813 | 0.793 | 0.596 | 0.609 | 3.18 | 0.473 | 0.3226 |
| NQ | RTH | B0 | 1h | M4_HARQ | 0.978 | 0.046 | 0.046 | 0.795 | -55.534 | -56.772 | 3.03 | 0.474 | 51129134284266338062431403894250748037089766674518505134210846701363573042425615515127747492047739621703831607437253188847796893715554299380475455403623284173687846474140246983913135172111164028242316747301115548709444395568057921956394556813116299984661574897489493574503084902543244868452352.0000 |
| NQ | RTH | B0 | 1h | M5_RGARCH | 0.978 | 0.669 | 0.676 | 0.691 | -0.530 | -0.542 | 2.77 | 0.457 | 3.9227 |
| NQ | RTH | B0 | 1h | M6_GK | 0.978 | 0.721 | 0.729 | 0.710 | 0.240 | 0.245 | 2.84 | 0.476 | 1.4170 |
| NQ | RTH | B0 | 1h | M6_PARK | 0.978 | 0.714 | 0.722 | 0.701 | 0.224 | 0.229 | 2.74 | 0.476 | 1.4027 |
| NQ | RTH | B0 | 30min | M1_EWMA | 0.961 | 0.758 | 0.773 | 0.749 | 0.524 | 0.546 | 1.14 | 0.473 | 0.3891 |
| NQ | RTH | B0 | 30min | M2_HAR | 0.961 | 0.839 | 0.856 | 0.831 | 0.653 | 0.680 | 4.83 | 0.430 | 0.2903 |
| NQ | RTH | B0 | 30min | M3_HARJ | 0.961 | 0.839 | 0.856 | 0.831 | 0.653 | 0.679 | 4.82 | 0.430 | 0.2904 |
| NQ | RTH | B0 | 30min | M4_HARQ | 0.961 | 0.103 | 0.105 | 0.835 | -25.756 | -26.812 | 4.49 | 0.431 | 18104351273229839065592940972282031432134983636798886502084214153461573498769046809959318185971244637054313721770094251717156154674539126902780724352381224766630397625927427558725616940109857963601794716040450571178788241822603942275355065651876531564356757142573142199825483264305770415521792.0000 |
| NQ | RTH | B0 | 30min | M5_RGARCH | 0.961 | 0.777 | 0.793 | 0.771 | -0.345 | -0.359 | 4.85 | 0.423 | 2.8305 |
| NQ | RTH | B0 | 30min | M6_GK | 0.961 | 0.770 | 0.786 | 0.762 | 0.288 | 0.300 | 3.81 | 0.452 | 1.4045 |
| NQ | RTH | B0 | 30min | M6_PARK | 0.961 | 0.766 | 0.781 | 0.755 | 0.312 | 0.325 | 3.64 | 0.453 | 1.2656 |
| NQ | RTH | B1 | 1day | M1_EWMA | 0.995 | 0.703 | 0.705 | 0.706 | 0.392 | 0.394 | 1.65 | 0.527 | 0.2753 |
| NQ | RTH | B1 | 1day | M2_HAR | 0.995 | 0.828 | 0.831 | 0.823 | 0.674 | 0.678 | 2.94 | 0.372 | 0.1543 |
| NQ | RTH | B1 | 1day | M3_HARJ | 0.995 | 0.046 | 0.046 | 0.812 | -359.328 | -361.262 | 2.53 | 0.396 | 40243797409599132917107120049832384610643951974013538959051273683936707833876315436676894631836545545631257454414530382145681985164194991579320500714918400163578377857460580140579066296619772317923883203791305405587134829869857447313993317572588091721282553836244462142747119166054729642934272.0000 |
| NQ | RTH | B1 | 1day | M4_HARQ | 0.995 | -0.049 | -0.049 | 0.811 | -724.101 | -727.998 | 1.71 | 0.374 | 860060835625280908673567639196474502041076842314426516281699534319565490007466997916884390232619815239306630673752131686761682031740817467820295753928122735663721612425688206398585979329983633783691675351740290546005140531857754447923679448809920439267871791788682775808413272032793728827523072.0000 |
| NQ | RTH | B1 | 1day | M5_RGARCH | 0.995 | 0.813 | 0.815 | 0.809 | 0.203 | 0.204 | 3.07 | 0.369 | 0.6142 |
| NQ | RTH | B1 | 1day | M6_GK | 0.995 | 0.746 | 0.748 | 0.733 | 0.311 | 0.313 | 2.95 | 0.459 | 0.5007 |
| NQ | RTH | B1 | 1day | M6_PARK | 0.995 | 0.754 | 0.756 | 0.739 | 0.324 | 0.325 | 3.05 | 0.496 | 0.4695 |
| NQ | RTH | B1 | 1h | M1_EWMA | 0.978 | 0.746 | 0.754 | 0.738 | 0.504 | 0.516 | 1.12 | 0.481 | 0.3711 |
| NQ | RTH | B1 | 1h | M2_HAR | 0.978 | 0.811 | 0.820 | 0.801 | 0.609 | 0.622 | 3.31 | 0.473 | 0.3096 |
| NQ | RTH | B1 | 1h | M3_HARJ | 0.978 | 0.809 | 0.818 | 0.799 | 0.607 | 0.621 | 3.24 | 0.474 | 0.3119 |
| NQ | RTH | B1 | 1h | M4_HARQ | 0.978 | 0.089 | 0.090 | 0.802 | -27.705 | -28.328 | 3.13 | 0.474 | 31330374560172697996045247016301817595184393473335106119843451425427746985970297880209366392819345126362802062097825956848295763994472643789338391328520316061510541967535000535505501612967209446601286079074828924028599710261016381278453156010466550634031632423066598051274761714154395683258368.0000 |
| NQ | RTH | B1 | 1h | M5_RGARCH | 0.978 | 0.703 | 0.711 | 0.708 | -0.199 | -0.204 | 2.87 | 0.460 | 2.5008 |
| NQ | RTH | B1 | 1h | M6_GK | 0.978 | 0.727 | 0.735 | 0.716 | 0.252 | 0.257 | 2.90 | 0.475 | 1.3643 |
| NQ | RTH | B1 | 1h | M6_PARK | 0.978 | 0.720 | 0.728 | 0.708 | 0.236 | 0.242 | 2.79 | 0.476 | 1.3493 |
| NQ | RTH | B1 | 30min | M1_EWMA | 0.960 | 0.761 | 0.777 | 0.753 | 0.534 | 0.556 | 1.16 | 0.474 | 0.3778 |
| NQ | RTH | B1 | 30min | M2_HAR | 0.960 | 0.844 | 0.861 | 0.836 | 0.665 | 0.693 | 4.91 | 0.430 | 0.2772 |
| NQ | RTH | B1 | 30min | M3_HARJ | 0.960 | 0.844 | 0.861 | 0.836 | 0.665 | 0.693 | 4.89 | 0.430 | 0.2773 |
| NQ | RTH | B1 | 30min | M4_HARQ | 0.960 | 0.165 | 0.168 | 0.840 | -12.639 | -13.162 | 4.63 | 0.431 | 9558020981748852816081385947972315934449896637029237037261908216133946859253995519468944603208884163738978754123930166757620527217442660104116872793393833143130955344725747225610267964247015572363990728291017306208581723694464490373632273011197523411347620735126196876058378160879305937125376.0000 |
| NQ | RTH | B1 | 30min | M5_RGARCH | 0.960 | 0.786 | 0.802 | 0.780 | -0.163 | -0.170 | 4.93 | 0.423 | 2.2942 |
| NQ | RTH | B1 | 30min | M6_GK | 0.960 | 0.775 | 0.791 | 0.765 | 0.295 | 0.308 | 3.81 | 0.454 | 1.3519 |
| NQ | RTH | B1 | 30min | M6_PARK | 0.960 | 0.770 | 0.786 | 0.759 | 0.320 | 0.333 | 3.65 | 0.454 | 1.2165 |

## 6. Part F, synthetic error curves

Recovery (lambda_hat / lambda_true, mean over 200 reps x 5 seeds) at the calibrated constants; full grid `s05_partf_curves.csv`. No pass band is applied.

| nu | NSR | n | M | E1_a_L1-5 | E1_a_L1-10 | E1_d_L1-5 | E1_d_L1-10 | E2 | E4 |
|---|---|---|---|---|---|---|---|---|---|
| 3.0 | 1e-05 | 390 | 390 | 0.973 | 0.973 | 1.031 | 1.103 | 0.971 | 1.094 |
| 3.0 | 1e-05 | 1380 | 1380 | 0.914 | 0.914 | 0.968 | 1.037 | 0.892 | 0.986 |
| 3.0 | 3e-05 | 390 | 390 | 0.923 | 0.923 | 0.979 | 1.045 | 0.920 | 1.039 |
| 3.0 | 3e-05 | 1380 | 1380 | 0.781 | 0.781 | 0.828 | 0.886 | 0.738 | 0.845 |
| 3.0 | 1e-04 | 390 | 390 | 0.785 | 0.785 | 0.832 | 0.890 | 0.777 | 0.887 |
| 3.0 | 1e-04 | 1380 | 1380 | 0.515 | 0.515 | 0.546 | 0.585 | 0.459 | 0.562 |
| 3.4 | 1e-05 | 390 | 390 | 0.974 | 0.975 | 1.032 | 1.105 | 0.973 | 1.041 |
| 3.4 | 1e-05 | 1380 | 1380 | 0.916 | 0.916 | 0.969 | 1.036 | 0.895 | 0.950 |
| 3.4 | 3e-05 | 390 | 390 | 0.928 | 0.928 | 0.983 | 1.052 | 0.925 | 0.991 |
| 3.4 | 3e-05 | 1380 | 1380 | 0.787 | 0.788 | 0.834 | 0.893 | 0.746 | 0.819 |
| 3.4 | 1e-04 | 390 | 390 | 0.793 | 0.793 | 0.840 | 0.899 | 0.788 | 0.849 |
| 3.4 | 1e-04 | 1380 | 1380 | 0.520 | 0.521 | 0.552 | 0.592 | 0.466 | 0.542 |
| 4.5 | 1e-05 | 390 | 390 | 0.976 | 0.976 | 1.033 | 1.106 | 0.975 | 0.995 |
| 4.5 | 1e-05 | 1380 | 1380 | 0.918 | 0.918 | 0.972 | 1.040 | 0.898 | 0.927 |
| 4.5 | 3e-05 | 390 | 390 | 0.929 | 0.929 | 0.984 | 1.052 | 0.927 | 0.947 |
| 4.5 | 3e-05 | 1380 | 1380 | 0.791 | 0.792 | 0.839 | 0.899 | 0.752 | 0.799 |
| 4.5 | 1e-04 | 390 | 390 | 0.799 | 0.800 | 0.847 | 0.907 | 0.796 | 0.815 |
| 4.5 | 1e-04 | 1380 | 1380 | 0.525 | 0.526 | 0.557 | 0.597 | 0.472 | 0.531 |

## 7. Cells where a conclusion changes across the boundary treatment or calibration sensitivity

| quantity | cell | level | B0 | B1 |
|---|---|---|---|---|
| MCS | ES/GLOBEX/1h/S-B_q0.80 | mcs75 | M6_GK | M2_HAR|M3_HARJ |
| MCS | ES/GLOBEX/1h/S-B_q0.80 | mcs90 | M6_GK | M2_HAR|M3_HARJ|M4_HARQ |
| MCS | ES/GLOBEX/1h/S-B_q0.90 | mcs75 | M6_GK | M2_HAR|M3_HARJ|M4_HARQ |
| MCS | ES/GLOBEX/1h/S-B_q0.90 | mcs90 | M6_GK | M2_HAR|M3_HARJ|M4_HARQ |
| MCS | ES/GLOBEX/1h/S-C_q0.90 | mcs75 | M6_GK | M2_HAR|M3_HARJ|M4_HARQ |
| MCS | ES/GLOBEX/1h/S-C_q0.90 | mcs90 | M6_GK | M2_HAR|M3_HARJ|M4_HARQ |
| MCS | ES/GLOBEX/30min/S-C_q0.80 | mcs75 | M4_HARQ | M6_GK |
| MCS | ES/GLOBEX/30min/S-C_q0.80 | mcs90 | M4_HARQ | M6_GK |
| MCS | ES/GLOBEX/30min/S-C_q0.90 | mcs75 | M4_HARQ | M6_GK |
| MCS | ES/GLOBEX/30min/S-C_q0.90 | mcs90 | M4_HARQ | M6_GK |
| MCS | ES/RTH/1day/S-B_q0.80 | mcs90 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| MCS | ES/RTH/1day/S-B_q0.90 | mcs75 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| MCS | ES/RTH/1day/S-C_q0.80 | mcs75 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| MCS | ES/RTH/1day/S-C_q0.80 | mcs90 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| MCS | ES/RTH/30min/S-B_q0.80 | mcs75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M4_HARQ |
| MCS | ES/RTH/30min/S-B_q0.90 | mcs75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M4_HARQ |
| MCS | NQ/GLOBEX/1day/S-A | mcs75 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| MCS | NQ/GLOBEX/1day/S-A | mcs90 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| MCS | NQ/GLOBEX/1day/S-C_q0.90 | mcs90 | M2_HAR|M3_HARJ|M4_HARQ|M6_PARK | M2_HAR|M3_HARJ|M4_HARQ|M6_GK|M6_PARK |
| MCS | NQ/RTH/1day/S-A | mcs75 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| MCS | NQ/RTH/1day/S-A | mcs90 | M2_HAR|M4_HARQ | M2_HAR|M3_HARJ|M4_HARQ |
| MCS | NQ/RTH/1day/S-B_q0.80 | mcs75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M4_HARQ |
| MCS | NQ/RTH/1day/S-C_q0.80 | mcs75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M4_HARQ |
| MCS | NQ/RTH/1h/S-B_q0.80 | mcs90 | M1_EWMA|M2_HAR|M4_HARQ | M2_HAR|M4_HARQ |
| MCS | NQ/RTH/30min/S-A | mcs75 | M2_HAR|M3_HARJ|M4_HARQ | M2_HAR|M4_HARQ |

Synthetic-arm recovery shifts exceeding 0.10 vs the primary calibration (73):

- (E4, n=390, M=390): recovery 0.991 -> 1.094 at nu=3.0, NSR=1e-05
- (E1_a_L1-10, n=1380, M=1380): recovery 0.788 -> 0.914 at nu=3.0, NSR=1e-05
- (E1_a_L1-5, n=1380, M=1380): recovery 0.787 -> 0.914 at nu=3.0, NSR=1e-05
- (E1_d_L1-10, n=1380, M=1380): recovery 0.893 -> 1.037 at nu=3.0, NSR=1e-05
- (E1_d_L1-5, n=1380, M=1380): recovery 0.834 -> 0.968 at nu=3.0, NSR=1e-05
- (E2, n=1380, M=1380): recovery 0.746 -> 0.892 at nu=3.0, NSR=1e-05
- (E4, n=1380, M=1380): recovery 0.819 -> 0.986 at nu=3.0, NSR=1e-05
- (E1_a_L1-10, n=390, M=390): recovery 0.928 -> 0.785 at nu=3.0, NSR=1e-04
- (E1_a_L1-5, n=390, M=390): recovery 0.928 -> 0.785 at nu=3.0, NSR=1e-04
- (E1_d_L1-10, n=390, M=390): recovery 1.052 -> 0.890 at nu=3.0, NSR=1e-04
- (E1_d_L1-5, n=390, M=390): recovery 0.983 -> 0.832 at nu=3.0, NSR=1e-04
- (E2, n=390, M=390): recovery 0.925 -> 0.777 at nu=3.0, NSR=1e-04
- (E4, n=390, M=390): recovery 0.991 -> 0.887 at nu=3.0, NSR=1e-04
- (E1_a_L1-10, n=1380, M=345): recovery 0.937 -> 0.811 at nu=3.0, NSR=1e-04
- (E1_a_L1-5, n=1380, M=345): recovery 0.936 -> 0.811 at nu=3.0, NSR=1e-04
- (E1_d_L1-10, n=1380, M=345): recovery 1.061 -> 0.920 at nu=3.0, NSR=1e-04
- (E1_d_L1-5, n=1380, M=345): recovery 0.991 -> 0.860 at nu=3.0, NSR=1e-04
- (E2, n=1380, M=345): recovery 0.920 -> 0.772 at nu=3.0, NSR=1e-04
- (E1_a_L1-10, n=1380, M=1380): recovery 0.788 -> 0.515 at nu=3.0, NSR=1e-04
- (E1_a_L1-5, n=1380, M=1380): recovery 0.787 -> 0.515 at nu=3.0, NSR=1e-04
- (E1_d_L1-10, n=1380, M=1380): recovery 0.893 -> 0.585 at nu=3.0, NSR=1e-04
- (E1_d_L1-5, n=1380, M=1380): recovery 0.834 -> 0.546 at nu=3.0, NSR=1e-04
- (E2, n=1380, M=1380): recovery 0.746 -> 0.459 at nu=3.0, NSR=1e-04
- (E4, n=1380, M=1380): recovery 0.819 -> 0.562 at nu=3.0, NSR=1e-04
- (E1_a_L1-10, n=1380, M=1380): recovery 0.788 -> 0.916 at nu=3.4, NSR=1e-05
- (E1_a_L1-5, n=1380, M=1380): recovery 0.787 -> 0.916 at nu=3.4, NSR=1e-05
- (E1_d_L1-10, n=1380, M=1380): recovery 0.893 -> 1.036 at nu=3.4, NSR=1e-05
- (E1_d_L1-5, n=1380, M=1380): recovery 0.834 -> 0.969 at nu=3.4, NSR=1e-05
- (E2, n=1380, M=1380): recovery 0.746 -> 0.895 at nu=3.4, NSR=1e-05
- (E4, n=1380, M=1380): recovery 0.819 -> 0.950 at nu=3.4, NSR=1e-05
- (E1_a_L1-10, n=390, M=390): recovery 0.928 -> 0.793 at nu=3.4, NSR=1e-04
- (E1_a_L1-5, n=390, M=390): recovery 0.928 -> 0.793 at nu=3.4, NSR=1e-04
- (E1_d_L1-10, n=390, M=390): recovery 1.052 -> 0.899 at nu=3.4, NSR=1e-04
- (E1_d_L1-5, n=390, M=390): recovery 0.983 -> 0.840 at nu=3.4, NSR=1e-04
- (E2, n=390, M=390): recovery 0.925 -> 0.788 at nu=3.4, NSR=1e-04
- (E4, n=390, M=390): recovery 0.991 -> 0.849 at nu=3.4, NSR=1e-04
- (E1_a_L1-10, n=1380, M=345): recovery 0.937 -> 0.814 at nu=3.4, NSR=1e-04
- (E1_a_L1-5, n=1380, M=345): recovery 0.936 -> 0.814 at nu=3.4, NSR=1e-04
- (E1_d_L1-10, n=1380, M=345): recovery 1.061 -> 0.924 at nu=3.4, NSR=1e-04
- (E1_d_L1-5, n=1380, M=345): recovery 0.991 -> 0.863 at nu=3.4, NSR=1e-04
- (E2, n=1380, M=345): recovery 0.920 -> 0.777 at nu=3.4, NSR=1e-04
- (E4, n=1380, M=345): recovery 0.974 -> 0.847 at nu=3.4, NSR=1e-04
- (E1_a_L1-10, n=1380, M=1380): recovery 0.788 -> 0.521 at nu=3.4, NSR=1e-04
- (E1_a_L1-5, n=1380, M=1380): recovery 0.787 -> 0.520 at nu=3.4, NSR=1e-04
- (E1_d_L1-10, n=1380, M=1380): recovery 0.893 -> 0.592 at nu=3.4, NSR=1e-04
- (E1_d_L1-5, n=1380, M=1380): recovery 0.834 -> 0.552 at nu=3.4, NSR=1e-04
- (E2, n=1380, M=1380): recovery 0.746 -> 0.466 at nu=3.4, NSR=1e-04
- (E4, n=1380, M=1380): recovery 0.819 -> 0.542 at nu=3.4, NSR=1e-04
- (E1_a_L1-10, n=1380, M=1380): recovery 0.788 -> 0.918 at nu=4.5, NSR=1e-05
- (E1_a_L1-5, n=1380, M=1380): recovery 0.787 -> 0.918 at nu=4.5, NSR=1e-05
- (E1_d_L1-10, n=1380, M=1380): recovery 0.893 -> 1.040 at nu=4.5, NSR=1e-05
- (E1_d_L1-5, n=1380, M=1380): recovery 0.834 -> 0.972 at nu=4.5, NSR=1e-05
- (E2, n=1380, M=1380): recovery 0.746 -> 0.898 at nu=4.5, NSR=1e-05
- (E4, n=1380, M=1380): recovery 0.819 -> 0.927 at nu=4.5, NSR=1e-05
- (E4, n=390, M=195): recovery 1.030 -> 0.907 at nu=4.5, NSR=1e-04
- (E1_a_L1-10, n=390, M=390): recovery 0.928 -> 0.800 at nu=4.5, NSR=1e-04
- (E1_a_L1-5, n=390, M=390): recovery 0.928 -> 0.799 at nu=4.5, NSR=1e-04
- (E1_d_L1-10, n=390, M=390): recovery 1.052 -> 0.907 at nu=4.5, NSR=1e-04
- (E1_d_L1-5, n=390, M=390): recovery 0.983 -> 0.847 at nu=4.5, NSR=1e-04
- (E2, n=390, M=390): recovery 0.925 -> 0.796 at nu=4.5, NSR=1e-04
- (E4, n=390, M=390): recovery 0.991 -> 0.815 at nu=4.5, NSR=1e-04
- (E1_a_L1-10, n=1380, M=345): recovery 0.937 -> 0.818 at nu=4.5, NSR=1e-04
- (E1_a_L1-5, n=1380, M=345): recovery 0.936 -> 0.818 at nu=4.5, NSR=1e-04
- (E1_d_L1-10, n=1380, M=345): recovery 1.061 -> 0.928 at nu=4.5, NSR=1e-04
- (E1_d_L1-5, n=1380, M=345): recovery 0.991 -> 0.867 at nu=4.5, NSR=1e-04
- (E2, n=1380, M=345): recovery 0.920 -> 0.782 at nu=4.5, NSR=1e-04
- (E4, n=1380, M=345): recovery 0.974 -> 0.826 at nu=4.5, NSR=1e-04
- (E1_a_L1-10, n=1380, M=1380): recovery 0.788 -> 0.526 at nu=4.5, NSR=1e-04
- (E1_a_L1-5, n=1380, M=1380): recovery 0.787 -> 0.525 at nu=4.5, NSR=1e-04
- (E1_d_L1-10, n=1380, M=1380): recovery 0.893 -> 0.597 at nu=4.5, NSR=1e-04
- (E1_d_L1-5, n=1380, M=1380): recovery 0.834 -> 0.557 at nu=4.5, NSR=1e-04
- (E2, n=1380, M=1380): recovery 0.746 -> 0.472 at nu=4.5, NSR=1e-04
- (E4, n=1380, M=1380): recovery 0.819 -> 0.531 at nu=4.5, NSR=1e-04
