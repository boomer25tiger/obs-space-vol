# Pre-registration, Session 3 data engineering and noise characterisation

Frozen before any data is loaded beyond the Phase 0 inventory.

## Purpose
Build validated ES and NQ minute bars under every SCOPE section 3 rule, in both
session geometries, and measure the microstructure noise-to-signal ratio. The noise
measurement determines which region of the S02 threshold map is relevant.

## Holdout
2024-01-01 onward is NOT loaded, NOT processed, and NOT inspected in this session.
Estimation sample is 2016-01-01 to 2023-12-31.

## Noise measurement, pre-specified
Definition: NSR = omega^2 / E[IV], where omega^2 is per-observation additive log-price
noise variance and IV is daily integrated variance. Matches the S01 and S02 convention.

Two independent estimators, both reported, neither selected:
N1 Signature plot. Under additive iid noise, E[RV_M] = IV + 2*M*omega^2. Regress mean
   RV on M across all available M. Slope gives 2*omega^2, intercept gives IV.
N2 Hansen and Lunde (2006) direct estimator, omega^2 = RV_finest / (2*n).

Reported by year, by session geometry, by instrument, and by volatility tercile.
Disagreement between N1 and N2 is reported, never averaged away.

## Sampling frequencies
M giving {13, 26, 78, 195, 390} for RTH and {23, 46, 138, 345, 1380} for full Globex.

## Prohibited
No forecasting model is estimated. No reliability estimator is applied. No holdout
data is touched. Any deviation logged in DECISIONS.md.
