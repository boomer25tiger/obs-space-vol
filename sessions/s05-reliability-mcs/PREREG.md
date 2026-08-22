# Pre-registration, Session 5 reliability surface and model confidence set

Frozen before any estimation. Real data plus a synthetic arm calibrated to S03/S04
measurements.

## Holdout
2024-01-01 onward is NOT loaded, processed, or inspected. Estimation sample
2016-01-01 to 2023-12-31. Repaired panels from S04: ES RTH 1901, ES GLOBEX 1953,
NQ RTH 1901, NQ GLOBEX 1948 sessions.

## Calibration constants, measured not asserted
Noise-to-signal ratio: 3e-5 primary (S03 N1 full-sample range 1.2e-5 to 9.0e-5).
  Sensitivity at 1e-5 and 1e-4. S03 N2 is NOT used; S03 established it degenerates to
  IV/(2n) at 1-minute sampling.
Hill tail index: 3.4 primary (S04 range 2.95 to 3.67). Sensitivity at 3.0 and 4.5.
Boundary-minute extreme elevation: 09:30 at 25.9x, 15:59 at 20.6x, 18:01 at 7.5x base.

## Part A, the quarticity ratio (answers the S04 gap)
Report the full distribution of R = (2/M) * Q / P^2 per session, where Q is quarticity
and P the matching variance proxy, for every combination below. Under constant
volatility R = 2/M exactly, which is the reference line.
  Quarticity variants: realized, tripower, truncated at 3/5/10 local sd, median.
  Matching proxies: RV, bipower, truncated RV, median RV.
Reported per year, per root, per geometry, per M: median, IQR, p95, p99, the share of
sessions where R exceeds 10x its median, and the serial correlation of log R at lags
1-10. A variant whose R is unstable is unusable regardless of its RQ level.

Unit test T1: the tripower quarticity normalisation constant is verified against
mu_{4/3}^{-3} on simulated jump-free constant-volatility data, where RQ/TQ must equal
1.00 within Monte Carlo error. S04 reported a median near 6.0 in every cell, which is
too stable across regimes to be jump content. A failing T1 halts and reports.

## Part B, boundary minutes as a crossed factor
Every Part A and Part C quantity is computed twice:
  B0 all minutes.
  B1 excluding 09:30, 09:31, 15:59, 16:00, 18:01 New York.
Both reported, neither selected.

## Part C, reliability surface
lambda = Var(log IV) / Var(log RV), estimated by:
  E4 asymptotic-variance route, using the Part A variant with the most stable R.
     Selection is by the pre-registered stability metric in Part A, computed before
     any lambda is produced, and the chosen variant is recorded in the report.
  E1 nugget, arms a (exponential) and d (model-implied), lag sets L1-5 and L1-10.
  E2 non-overlapping contiguous halves.
Surface dimensions: horizon (30 min, 1 hour, 1 day), sampling M, instrument,
geometry, calendar year, volatility tercile. Disagreement across estimators is
reported, never averaged.

## Part D, forecasting models, pre-registered, no tuning
M1 RiskMetrics EWMA, lambda 0.94.
M2 HAR (Corsi 2009), lags 1/5/22 at daily, matched multiples intraday.
M3 HAR-J, jump component max(RV - BV, 0).
M4 HARQ (Bollerslev, Patton, Quaedvlieg 2016), coefficient scaled by sqrt(RQ).
M5 Realized GARCH (Hansen, Huang, Shek 2012).
M6 Range-based, Parkinson and Garman-Klass.
No feature selection, no hyperparameter search. Expanding-window estimation with a
pre-registered warm-up. Forecasts one step ahead at each horizon.

## Part E, the decision criterion
Model Confidence Set (Hansen, Lunde, Nason 2011), block bootstrap, 10,000 resamples,
reported at both 75% and 90% confidence, the authors' conventional levels.
Computed under three evaluation schemes:
  S-A unweighted QLIKE.
  S-B tail-conditional QLIKE, conditioning on realised RV in its upper tail.
  S-C tail-conditional QLIKE, conditioning on a predetermined variable (the forecast),
      which eliminates selection on proxy noise by construction.
Conditioning quantiles 0.80 and 0.90. The 0.95 quantile is NOT computed: S04 put those
cells at 95-97 sessions and MC6 put that size at 40% power.

PRIMARY RESULT: whether MCS composition differs between S-B and S-C, and between
IC computed with and without the reliability correction.

Also report, for every model and scheme: IC (Pearson on logs and Spearman),
reliability-corrected IC, out-of-sample R^2 measured and corrected, IC information
ratio from rolling windows, and hit rate.

## Part F, synthetic arm
Regenerate the S01 estimator comparison at the calibrated constants above: tail index
3.4, NSR 3e-5, with boundary-minute elevation and a diurnal profile matching the S04
measurements. Report estimator error as a curve across the parameter sweep. NO pass
band is applied.

## Prohibited
No model tuned. No quarticity variant, truncation level, or lag set selected on the
basis of a lambda or MCS result; the Part A stability metric is the only selection and
it runs first. No holdout data touched. Any deviation logged in DECISIONS.md.
