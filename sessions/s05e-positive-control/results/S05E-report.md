# Session 5E report, positive control on the aggregation and reliability path

Generated 2026-08-19T04:39:40+00:00 (UTC). Diagnosis only: no repair, no estimator selection, no prior artifact modified. Output under `sessions/s05e-positive-control/results/`.

**Code path.** Every synthetic arm is aggregated and measured by the same functions that produced the real-data numbers, imported unmodified: `phase34.windows` and `phase34.subbars` (S05B) for windowing and sub-bar aggregation, `parta.quart_suite` (S05) for RV/TRV3/RQ/TRQ3, `estimators2.e1_reduced/e2/e4` (S02) for the Part C estimators, and `fbm.CirculantEmbedding`/`fbm.fgn_acf` (S01) for the A4 rough path. Only data generation is new; the aggregation, the Var(log RV_M) computation and the estimators are not reimplemented. The real path was callable directly, so the halt condition did not trigger.

## Phase 1, reference exponent of trigamma(M/2) itself

The theoretical target is measured, not assumed. trigamma(M/2) is fitted against M on each S05B extended grid by the two procedures used on the data: the free-intercept model Var = c + A M^b, and the log-log slope.

| grid | n_points | M_min | M_max | free_c | free_A | free_b | free_rmse | loglog_b | loglog_r2 |
|---|---|---|---|---|---|---|---|---|---|
| RTH_1day | 8 | 5 | 389 | 0.0037 | 3.0574 | -1.1444 | 0.0018 | -1.0419 | 0.9996 |
| RTH_1h | 9 | 4 | 60 | 0.0135 | 3.3614 | -1.2097 | 0.0024 | -1.0870 | 0.9991 |
| RTH_30min | 5 | 5 | 30 | 0.0139 | 3.2662 | -1.1971 | 0.0009 | -1.0946 | 0.9995 |
| GLOBEX_1day | 9 | 5 | 1379 | 0.0029 | 3.0320 | -1.1386 | 0.0020 | -1.0325 | 0.9996 |

**The reference exponent is not -1.** Under the free-intercept procedure - the one used to produce the observed -0.439 - trigamma itself fits b = -1.139 on the GLOBEX 1day grid and -1.144 on RTH 1day, with the two RTH intraday grids at -1.210 and -1.197. Under the log-log procedure the same object fits -1.033 to -1.095. Adding the empirical intercept before fitting changes nothing (the `with_intercept_b` column of `phase1_trigamma_reference.csv` is identical to `free_b`, since a free intercept absorbs it). DECISIONS item 36 quoted -1.04 as the prediction, which is the log-log value; the comparator for the free-intercept fit is -1.14.

## Phase 2, synthetic positive control

Five arms, 5 seeds each, at the real panel dimensions (GLOBEX 1953x1380, RTH 1901x390). Jump size was calibrated by bisection so the finest-M truncated share matches the S05B measurement: GLOBEX sigma_j = 0.48109 achieving 0.2938 against target 0.2938; RTH sigma_j = 0.35708 achieving 0.1741 against target 0.1741.

### Fitted Var(log RV_M) = c + A M^b, by arm and grid

`b_sd` is the between-seed standard deviation over 5 seeds; no single-seed result is reported as a finding.

| arm | grid | n_seeds | b_mean | b_sd | b_min | b_max | c_mean | c_sd | A_mean | rmse_mean | var_log_iv_input_mean | recovery_error_mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | GLOBEX_1day | 5 | -1.1850 | 0.0849 | -1.2896 | -1.0855 | 1.0467 | 0.0187 | 3.3593 | 0.0079 | 1.0442 | 0.0025 |
| A0 | RTH_1day | 5 | -1.2451 | 0.1445 | -1.3965 | -1.0329 | 1.0492 | 0.0224 | 3.8279 | 0.0105 | 1.0435 | 0.0058 |
| A0 | RTH_1h | 5 | -1.1928 | 0.0414 | -1.2305 | -1.1296 | 1.0538 | 0.0158 | 3.2633 | 0.0049 | 1.0435 | 0.0103 |
| A0 | RTH_30min | 5 | -1.2168 | 0.0725 | -1.2673 | -1.0920 | 1.0595 | 0.0273 | 3.3447 | 0.0027 | 1.0435 | 0.0160 |
| A1 | GLOBEX_1day | 5 | -1.0808 | 0.1059 | -1.2256 | -0.9833 | 1.0501 | 0.0189 | 3.3430 | 0.0116 | 1.0442 | 0.0059 |
| A1 | RTH_1day | 5 | -1.1622 | 0.1191 | -1.2747 | -0.9592 | 1.0478 | 0.0241 | 3.4715 | 0.0094 | 1.0435 | 0.0043 |
| A1 | RTH_1h | 5 | -1.1937 | 0.0379 | -1.2439 | -1.1527 | 1.1351 | 0.0170 | 3.2646 | 0.0046 | 1.0435 | 0.0917 |
| A1 | RTH_30min | 5 | -1.2163 | 0.0798 | -1.2793 | -1.0785 | 1.1473 | 0.0283 | 3.3407 | 0.0021 | 1.0435 | 0.1039 |
| A2 | GLOBEX_1day | 5 | -1.0721 | 0.0801 | -1.1572 | -0.9939 | 0.8811 | 0.0238 | 3.0613 | 0.0111 | 1.0442 | -0.1631 |
| A2 | RTH_1day | 5 | -1.1421 | 0.0927 | -1.2311 | -1.0006 | 0.9090 | 0.0163 | 3.1744 | 0.0099 | 1.0435 | -0.1345 |
| A2 | RTH_1h | 5 | -1.1836 | 0.0278 | -1.2247 | -1.1534 | 1.1376 | 0.0153 | 3.1868 | 0.0048 | 1.0435 | 0.0941 |
| A2 | RTH_30min | 5 | -1.2149 | 0.0777 | -1.2995 | -1.0916 | 1.1830 | 0.0250 | 3.3316 | 0.0024 | 1.0435 | 0.1395 |
| A3 | GLOBEX_1day | 5 | -1.0712 | 0.0798 | -1.1582 | -0.9938 | 0.8810 | 0.0235 | 3.0553 | 0.0112 | 1.0442 | -0.1632 |
| A3 | RTH_1day | 5 | -1.1379 | 0.0924 | -1.2295 | -0.9994 | 0.9087 | 0.0167 | 3.1501 | 0.0098 | 1.0435 | -0.1348 |
| A3 | RTH_1h | 5 | -1.1917 | 0.0291 | -1.2256 | -1.1627 | 1.1386 | 0.0148 | 3.2264 | 0.0049 | 1.0435 | 0.0951 |
| A3 | RTH_30min | 5 | -1.2243 | 0.0809 | -1.3147 | -1.0987 | 1.1855 | 0.0255 | 3.3649 | 0.0024 | 1.0435 | 0.1421 |
| A4 | GLOBEX_1day | 5 | -1.0928 | 0.1026 | -1.2093 | -0.9304 | 1.0218 | 0.0057 | 2.8621 | 0.0088 | 1.0200 | 0.0018 |
| A4 | RTH_1day | 5 | -1.1593 | 0.0933 | -1.2710 | -1.0531 | 1.0224 | 0.0073 | 3.2059 | 0.0084 | 1.0200 | 0.0024 |
| A4 | RTH_1h | 5 | -1.2522 | 0.0738 | -1.3325 | -1.1594 | 1.0341 | 0.0093 | 3.5860 | 0.0062 | 1.0200 | 0.0141 |
| A4 | RTH_30min | 5 | -1.1863 | 0.0442 | -1.2450 | -1.1438 | 1.0281 | 0.0033 | 3.2289 | 0.0026 | 1.0200 | 0.0081 |

### A0: does the pipeline recover the reference exponent?

**Yes.** On GLOBEX 1day, A0 returns b = -1.185 (between-seed sd 0.085, range -1.290 to -1.085) against the Phase 1 reference -1.139 - a gap of 0.046, which is 0.55 between-seed standard deviations. On RTH 1day, A0 returns -1.245 (sd 0.144) against -1.144, a gap of 0.101 or 0.70 sd. Var(log IV) is recovered as the fitted intercept to within 0.0025 (GLOBEX) and 0.0058 (RTH) of its known input value 1.0442. **There is no material departure at A0, so the problem is not located in the code path**, and the remaining arms are secondary as specified.

### Which arm reproduces the observed exponent?

**None.** Across all five arms and all four grids the fitted b lies in [-1.252, -1.071], every value steeper than -1.07. The observed real-data exponents run from -0.407 to -1.003 (Phase 3), and the flattest arm is nowhere near the flattest data. Adding the measured diurnal profile (A1), calibrated jumps (A2), measured padding (A3) or a rough H=0.1 log-IV path (A4) each moves b by at most 0.114 from A0 on the GLOBEX 1day grid. The closest approach anywhere is A2/A3 on GLOBEX 1day at b = -1.072, still 0.633 away from the -0.439 that prompted this session.

Note on the intercept: A2 and A3 recover c near 0.881 against an input Var(log IV) of 1.044, i.e. calibrated jumps bias the recovered Var(log IV) downward by about 0.163, while A0, A1 and A4 recover it to three decimals.

### Part C estimators on A0 and A2 against known lambda

| arm | grid | estimator | ratio_max_min | ratio_sd | elasticity | elasticity_sd | mean_abs_error_vs_true | mean_lam | mean_lam_true |
|---|---|---|---|---|---|---|---|---|---|
| A0 | GLOBEX_1day | E1_a_exp_L1-10 | 8.2593 | 11.2752 | 0.2671 | 0.5561 | 0.8791 | 0.0040 | 0.8831 |
| A0 | GLOBEX_1day | E1_a_exp_L1-5 | 2.2140 | 0.7786 | 0.3481 | 0.6806 | 0.8800 | 0.0031 | 0.8831 |
| A0 | GLOBEX_1day | E1_d_model_L1-10 | 1.6182 | 1.0821 | -0.0229 | -- | 0.8899 | -0.0068 | 0.8831 |
| A0 | GLOBEX_1day | E1_d_model_L1-5 | 24.8784 | 39.8971 | -1.7725 | 2.3624 | 0.8781 | 0.0050 | 0.8831 |
| A0 | GLOBEX_1day | E2 | 1.0322 | 0.0154 | -1.0300 | 0.0019 | 0.0059 | 0.8829 | 0.8831 |
| A0 | GLOBEX_1day | E4 | 1.2589 | 0.0212 | -0.8971 | 0.0035 | 0.0451 | 0.9272 | 0.8831 |
| A0 | RTH_1day | E1_a_exp_L1-10 | 9.5507 | 12.4970 | 1.8762 | 2.4475 | 0.8691 | 0.0036 | 0.8727 |
| A0 | RTH_1day | E1_a_exp_L1-5 | 2.0362 | 1.0156 | 0.4356 | 0.7523 | 0.8686 | 0.0042 | 0.8727 |
| A0 | RTH_1day | E1_d_model_L1-10 | 19.3203 | 28.3212 | -0.4543 | 0.9868 | 0.8598 | 0.0130 | 0.8727 |
| A0 | RTH_1day | E1_d_model_L1-5 | 8.1013 | 10.8626 | 0.5665 | 0.7181 | 0.8816 | -0.0088 | 0.8727 |
| A0 | RTH_1day | E2 | 1.0659 | 0.0234 | -1.0427 | 0.0222 | 0.0115 | 0.8718 | 0.8727 |
| A0 | RTH_1day | E4 | 1.2715 | 0.0257 | -0.8639 | 0.0030 | 0.0508 | 0.9223 | 0.8727 |
| A2 | GLOBEX_1day | E1_a_exp_L1-10 | 17.7832 | 14.8100 | 1.3082 | 2.5980 | 1.0031 | 0.0084 | 1.0116 |
| A2 | GLOBEX_1day | E1_a_exp_L1-5 | 11.1817 | 11.4763 | 0.7466 | 1.7789 | 1.0042 | 0.0074 | 1.0116 |
| A2 | GLOBEX_1day | E1_d_model_L1-10 | 7.1599 | 12.3198 | 0.4437 | -- | 1.0607 | -0.0491 | 1.0116 |
| A2 | GLOBEX_1day | E1_d_model_L1-5 | 24.4493 | 33.9596 | 0.4439 | 0.0571 | 1.0443 | 0.0771 | 1.0116 |
| A2 | GLOBEX_1day | E2 | 1.0747 | 0.0155 | -0.3883 | 0.0164 | 0.2514 | 0.7602 | 1.0116 |
| A2 | GLOBEX_1day | E4 | 1.3778 | 0.0268 | -0.8619 | 0.0031 | 0.1280 | 0.9202 | 1.0116 |
| A2 | RTH_1day | E1_a_exp_L1-10 | 2.2457 | 2.3813 | 0.3374 | -- | 0.9830 | 0.0024 | 0.9854 |
| A2 | RTH_1day | E1_a_exp_L1-5 | 2.1584 | 1.1794 | 0.1264 | 0.2467 | 0.9817 | 0.0037 | 0.9854 |
| A2 | RTH_1day | E1_d_model_L1-10 | 7.1683 | 10.6729 | 0.2535 | 0.4123 | 0.9703 | 0.0151 | 0.9854 |
| A2 | RTH_1day | E1_d_model_L1-5 | 24.5418 | 36.8255 | 0.0373 | 0.1731 | 0.9854 | -0.0000 | 0.9854 |
| A2 | RTH_1day | E2 | 1.0852 | 0.0282 | -0.7078 | 0.0226 | 0.1610 | 0.8244 | 0.9854 |
| A2 | RTH_1day | E4 | 1.3110 | 0.0356 | -0.8663 | 0.0028 | 0.1051 | 0.9168 | 0.9854 |

Per-grid-point lambda against the known truth, A0 GLOBEX 1day, seed 0 (all seeds and grids in `phase2_estimators.csv`):

| M | E1_a_exp_L1-10 | E1_a_exp_L1-5 | E1_d_model_L1-10 | E1_d_model_L1-5 | E2 | E4 | lam_true |
|---|---|---|---|---|---|---|---|
| 5.0000 | -0.0022 | 0.0045 | -0.0023 | 0.0048 | 0.6860 | 0.8491 | 0.6817 |
| 6.0000 | -0.0161 | -0.0236 | -0.0447 | -0.0732 | 0.7245 | 0.8547 | 0.7212 |
| 10.0000 | -0.0058 | -0.0506 | -0.0065 | 0.0346 | 0.8302 | 0.8789 | 0.8330 |
| 12.0000 | -0.0544 | -0.0564 | 0.2846 | 0.1166 | 0.8532 | 0.8911 | 0.8526 |
| 23.0000 | -0.0049 | -0.0205 | -0.0107 | 0.4624 | 0.9195 | 0.9345 | 0.9167 |
| 46.0000 | -0.0058 | 0.0031 | -0.0063 | -0.0149 | 0.9587 | 0.9642 | 0.9619 |
| 138.0000 | -0.0048 | 0.0040 | -0.0053 | -0.0299 | 0.9870 | 0.9874 | 0.9900 |
| 345.0000 | -0.0057 | 0.0032 | -0.0063 | -0.0203 | 0.9943 | 0.9949 | 0.9962 |
| 1379.0000 | -0.0062 | 0.0024 | -0.0068 | -0.0190 | 0.9986 | 0.9987 | 0.9997 |

On A0, where lambda is known by construction, **E2 recovers it to a mean absolute error of 0.0059 to 0.0115** with a grid-invariance ratio of 1.032 to 1.066 and an elasticity of -1.043 to -1.030, which matches the Phase 1 log-log reference. E4 recovers it to 0.0451 to 0.0508 with a positive bias (mean lambda 0.925 against true 0.878).

**The four E1 nugget arms return lambda near zero at every grid point on A0, with a mean absolute error of about 0.87-0.89 against the truth.** This is a property of the A0 design, not evidence about E1 on real data: A0 draws log IV iid, so its autocovariance is zero at every lag >= 1 and a lag-0 extrapolation of a flat-zero autocovariance function returns zero by construction. A0 is therefore not an informative control for E1; the arm with a persistent signal is A4, on which estimators were not run because the specification restricts the estimator sweep to A0 and A2.

On A2, where calibrated jumps are present, E2's error rises to 0.161-0.251 and its elasticity flattens to -0.388, while E4's error rises to 0.105-0.128 with its elasticity nearly unchanged.

## Phase 3, decomposition on real data

S05B cache only; no panel was re-read.

### Fitted b on RV and on TRV3, every horizon, cell and boundary treatment

| root | geom | btag | horizon | n_M | b_RV | rmse_RV | b_TRV3 | rmse_TRV3 | b_shift_TRV3_minus_RV |
|---|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | 1day | 9 | -0.4393 | 0.0498 | -0.7399 | 0.0690 | -0.3006 |
| ES | GLOBEX | B1 | 1day | 9 | -0.4073 | 0.0484 | -0.9454 | 0.0810 | -0.5381 |
| ES | RTH | B0 | 1day | 8 | -0.6334 | 0.0295 | -1.0894 | 0.0675 | -0.4559 |
| ES | RTH | B0 | 1h | 9 | -0.4646 | 0.0148 | -0.7982 | 0.0274 | -0.3336 |
| ES | RTH | B0 | 30min | 5 | -0.4109 | 0.0045 | -0.5752 | 0.0084 | -0.1643 |
| ES | RTH | B1 | 1day | 8 | -0.6557 | 0.0306 | -1.0668 | 0.0662 | -0.4110 |
| ES | RTH | B1 | 1h | 9 | -0.4671 | 0.0151 | -0.7749 | 0.0263 | -0.3078 |
| ES | RTH | B1 | 30min | 5 | -0.4153 | 0.0042 | -0.5699 | 0.0102 | -0.1546 |
| NQ | GLOBEX | B0 | 1day | 9 | -0.6868 | 0.0380 | -1.0802 | 0.0372 | -0.3934 |
| NQ | GLOBEX | B1 | 1day | 9 | -0.6436 | 0.0316 | -1.0338 | 0.0336 | -0.3902 |
| NQ | RTH | B0 | 1day | 8 | -0.9765 | 0.0163 | -1.4266 | 0.0478 | -0.4501 |
| NQ | RTH | B0 | 1h | 9 | -0.8022 | 0.0118 | -1.4469 | 0.0302 | -0.6447 |
| NQ | RTH | B0 | 30min | 5 | -0.7004 | 0.0053 | -1.1676 | 0.0087 | -0.4672 |
| NQ | RTH | B1 | 1day | 8 | -1.0031 | 0.0170 | -1.5394 | 0.0659 | -0.5363 |
| NQ | RTH | B1 | 1h | 9 | -0.8052 | 0.0118 | -1.4283 | 0.0299 | -0.6230 |
| NQ | RTH | B1 | 30min | 5 | -0.6955 | 0.0053 | -1.1587 | 0.0087 | -0.4632 |

Truncation moves b more negative in every one of the 16 cells, by a mean of -0.415 and up to -0.645. Under TRV3, 10 of 16 cells reach or pass -1.0.

### Within-year and within-tercile fits against the pooled fit

| root | geom | btag | horizon | b_RV | b_year_mean | b_year_sd | b_year_min | b_year_max | n_years | b_terc_mean | b_terc_sd |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ES | GLOBEX | B0 | 1day | -0.4393 | -0.6793 | 0.1865 | -1.1244 | -0.4749 | 8 | -0.5494 | 0.0640 |
| ES | GLOBEX | B1 | 1day | -0.4073 | -0.6650 | 0.2251 | -1.2256 | -0.4347 | 8 | -0.5009 | 0.0527 |
| ES | RTH | B0 | 1day | -0.6334 | -0.8978 | 0.3645 | -1.4793 | -0.4606 | 8 | -0.7534 | 0.1889 |
| ES | RTH | B0 | 1h | -0.4646 | -0.6742 | 0.2004 | -1.1794 | -0.4832 | 8 | -0.4785 | 0.1091 |
| ES | RTH | B0 | 30min | -0.4109 | -0.5962 | 0.1353 | -0.8996 | -0.3904 | 8 | -0.4372 | 0.1594 |
| ES | RTH | B1 | 1day | -0.6557 | -0.9371 | 0.3821 | -1.5909 | -0.5048 | 8 | -0.7786 | 0.1578 |
| ES | RTH | B1 | 1h | -0.4671 | -0.6780 | 0.1979 | -1.1755 | -0.5132 | 8 | -0.4649 | 0.1156 |
| ES | RTH | B1 | 30min | -0.4153 | -0.6003 | 0.1428 | -0.9285 | -0.3947 | 8 | -0.4484 | 0.1472 |
| NQ | GLOBEX | B0 | 1day | -0.6868 | -0.8170 | 0.1239 | -1.0983 | -0.6820 | 8 | -0.7724 | 0.0834 |
| NQ | GLOBEX | B1 | 1day | -0.6436 | -0.7769 | 0.1588 | -1.1260 | -0.5529 | 8 | -0.7889 | 0.1186 |
| NQ | RTH | B0 | 1day | -0.9765 | -1.0836 | 0.2467 | -1.5041 | -0.7451 | 8 | -1.1672 | 0.1731 |
| NQ | RTH | B0 | 1h | -0.8022 | -0.9061 | 0.1347 | -1.1050 | -0.6824 | 8 | -0.9064 | 0.2127 |
| NQ | RTH | B0 | 30min | -0.7004 | -0.8825 | 0.1268 | -1.0981 | -0.6820 | 8 | -0.8031 | 0.2163 |
| NQ | RTH | B1 | 1day | -1.0031 | -1.1330 | 0.2588 | -1.5676 | -0.7649 | 8 | -1.1404 | 0.1533 |
| NQ | RTH | B1 | 1h | -0.8052 | -0.9104 | 0.1367 | -1.1095 | -0.6906 | 8 | -0.8944 | 0.2536 |
| NQ | RTH | B1 | 30min | -0.6955 | -0.8783 | 0.1205 | -1.0751 | -0.6978 | 8 | -0.7951 | 0.1798 |

**The pooled exponent is flatter than the within-year exponent in 16 of 16 cells**, by a mean of -0.182 and up to -0.281; the within-tercile mean is flatter than pooled in 15 of 16 cells, by a mean of -0.092. Between-year dispersion of b is substantial (sd 0.121 to 0.382). Pooling therefore accounts for part of the gap between the observed exponent and the Phase 1 reference, and the per-year and per-tercile fits are reported beside the pooled value rather than replacing it.

### b across horizons

| root | geom | btag | 1day | 1h | 30min |
|---|---|---|---|---|---|
| ES | GLOBEX | B0 | -0.4393 | -- | -- |
| ES | GLOBEX | B1 | -0.4073 | -- | -- |
| ES | RTH | B0 | -0.6334 | -0.4646 | -0.4109 |
| ES | RTH | B1 | -0.6557 | -0.4671 | -0.4153 |
| NQ | GLOBEX | B0 | -0.6868 | -- | -- |
| NQ | GLOBEX | B1 | -0.6436 | -- | -- |
| NQ | RTH | B0 | -0.9765 | -0.8022 | -0.7004 |
| NQ | RTH | B1 | -1.0031 | -0.8052 | -0.6955 |

The same, on TRV3:

| root | geom | btag | 1day | 1h | 30min |
|---|---|---|---|---|---|
| ES | GLOBEX | B0 | -0.7399 | -- | -- |
| ES | GLOBEX | B1 | -0.9454 | -- | -- |
| ES | RTH | B0 | -1.0894 | -0.7982 | -0.5752 |
| ES | RTH | B1 | -1.0668 | -0.7749 | -0.5699 |
| NQ | GLOBEX | B0 | -1.0802 | -- | -- |
| NQ | GLOBEX | B1 | -1.0338 | -- | -- |
| NQ | RTH | B0 | -1.4266 | -1.4469 | -1.1676 |
| NQ | RTH | B1 | -1.5394 | -1.4283 | -1.1587 |

Across horizons the exponent is flattest at 30min (-0.556 mean) and steepest at 1day (-0.681 mean), with 1h in between (-0.635). NQ RTH 1day reaches -1.003, the only real cells that approach the Phase 1 reference on RV alone.
