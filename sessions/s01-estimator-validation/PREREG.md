# Pre-registration, Session 1 estimator validation

Frozen 2026-08-18, before any simulation is run. Synthetic only.

## Purpose
Compare estimators of the reliability parameter lambda = Var(log IV)/Var(log RV)
under generating processes chosen to violate each estimator's assumptions.
E4 is the reference, not a candidate. The question is whether any alternative
matches it, and where each fails.

## Success criterion, derived
Reliability enters the correction as 1/sqrt(lambda), so a relative error delta in
lambda produces approximately delta/2 in corrected IC. Session-1 power analysis put
the minimum detectable IC difference at ~0.04 on an IC near 0.30, ~13% relative.
Errors below ~26% in lambda therefore cannot flip a ranking that is detectable at all.

Report PASS/FAIL at three bands rather than one: +/-10%, +/-15%, +/-25%.
Primary band is +/-15%. A pass requires the point estimate inside the band AND a
95% bootstrap CI excluding both band edges. Failure on any single DGP is a FAIL.

## Estimators
E4 REFERENCE. Realized quarticity, Var(RV - IV) estimated as (2/M)*RQ,
   per Barndorff-Nielsen and Shephard asymptotics as used in HARQ.
E1 Nugget. Lag-0 extrapolation of the autocovariance of log RV. FOUR arms, all
   reported, none selected:
     a exponential
     b power-law
     c cubic spline
     d model-implied. For fractional log-variance,
       gamma(k) proportional to 0.5*(|k+1|^2H - 2|k|^2H + |k-1|^2H);
       for ARFIMA(0,d,0), gamma(k) ~ k^(2d-1). H or d estimated jointly.
   Lag set SWEPT over {1..5}, {1..10}, {1..22}, {2..22}. The {2..22} arm excludes
   lag 1, where a roughness cusp is most concentrated.
E2 Non-overlapping subsampling. Contiguous temporal halves of each window.
E3 Three-cornered hat. Error correlation matrix measured and reported for every
   candidate triple BEFORE application. Applied only to the triple whose maximum
   off-diagonal error correlation is lowest, and reported as INAPPLICABLE if that
   maximum exceeds 0.20. Candidate proxies: RV at each M, bipower variation,
   Parkinson, Garman-Klass, Rogers-Satchell, squared open-to-close return.
   Note that Garman-Klass contains the Parkinson range term, so that pair is
   excluded from consideration a priori.

## Data-generating processes
Latent log-variance processes:
D1 AR(1), control.
D2 ARFIMA(0,d,0), long memory.
D3 Fractional OU, rough.
D4 Fractional OU, moderately rough.
D5 D1 plus price jumps.
D6 D1 plus additive microstructure price noise.
D7 D2 plus jumps and noise, combined stress case.

D3 and D4 are decisive for E1. Roughness and measurement error both concentrate
at lag zero. Arm (d) and the {2..22} lag set exist to test whether the confound
is separable.

## Parameter sweeps
All ranges below are ASSERTED from the analyst's reading of the empirical
literature and are NOT independently verified in this session. They are swept, not
fixed, and any conclusion sensitive to position within a range is reported as such.

AR(1) persistence phi: {0.95, 0.98, 0.995}
Unconditional sd of log RV: {0.5, 0.7, 1.0}
Long-memory d: {0.35, 0.40, 0.45}
Hurst H: {0.08, 0.10, 0.16, 0.30, 0.50}
  0.50 is the non-rough control and must recover correctly for any estimator.
Jump share of total quadratic variation: {0.05, 0.10}
Noise-to-signal variance ratio: {0.001, 0.01}

## Geometry
Both session geometries from the base spec, since the base spec's primary is full
Globex and the earlier draft used RTH only.
  n = 390 intraday steps (RTH)
  n = 1380 intraday steps (full Globex)
Sampling frequencies M as divisors giving {13, 26, 78, 195} sub-intervals for
n=390 and {23, 46, 138, 345} for n=1380.

## Protocol
Windows per replication T = 2000.
Replications = 200 per cell.
Seeds: master 20260818, per-cell seeds derived deterministically and logged.
Every cell run under 5 independent master seeds; between-seed dispersion reported.
Bootstrap: 1000 resamples over replications.

## Unit tests, required before any DGP is run
U1 fBm variance scaling matches t^(2H) for H in {0.1, 0.3, 0.5, 0.7, 0.9}.
U2 fBm autocovariance matches the closed form to within Monte Carlo error.
U3 Under constant volatility and no noise, Var(RV/IV) matches 2/M.
U4 Under constant volatility, E[Parkinson] and E[Garman-Klass] match their
   analytic expectations.
U5 Under a known lambda constructed directly, every estimator recovers it.
A failing unit test halts the session. An implementation bug must not be
reportable as an estimator failure.

## Prohibited
No parameter selected after seeing results. No DGP added or removed after results
are seen. No extrapolation arm or lag set chosen post hoc; all are reported.
No estimator tuned to improve its result. Any deviation logged in DECISIONS.md.
