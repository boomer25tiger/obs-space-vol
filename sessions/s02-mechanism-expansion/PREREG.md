# Pre-registration, Session 2 mechanism expansion and breakdown mapping

Frozen 2026-08-18, before any simulation. Synthetic only.

## Purpose
S01 showed every reliability estimator collapses under microstructure noise when fed
plain realized variance. S02 tests whether noise-robust and jump-robust proxies
restore recovery, and maps the breakdown threshold in noise-to-signal ratio for each
combination. Primary output is a THRESHOLD MAP, not a pass/fail verdict.

## Primary output
For each (estimator, proxy, DGP, geometry, M), the largest noise-to-signal ratio at
which the +/-15% band is still met. Reported as a surface. Cells that never meet the
band at any NSR are reported as such.

## Volatility proxies, all tested with every estimator
P1 RV, plain. S01 baseline, retained for comparison.
P2 Two-scale realized variance (Zhang, Mykland, Ait-Sahalia 2005).
P3 Realized kernel, flat-top Parzen (Barndorff-Nielsen, Hansen, Lunde, Shephard 2008),
   bandwidth by the authors' rule, reported not tuned.
P4 Pre-averaged realized variance (Jacod, Li, Mykland, Podolskij, Vetter 2009),
   window by the authors' rule.
P5 Bipower variation. Jump-robust, noise-sensitive.
P6 Median realized variance (Andersen, Dobrev, Schaumburg 2012).
P7 Truncated/threshold RV (Mancini 2009), threshold at 3 local standard deviations.
P8 Pre-averaged truncated RV. Noise and jump robust.

Quarticity for E4 uses the matching robust form where one exists: realized quarticity
for P1, tripower quarticity for P5-P7, pre-averaged quarticity for P4 and P8. Where no
matching form exists the cell is reported as UNAVAILABLE, never substituted.

## Estimators
E4 REFERENCE. Asymptotic-variance route, Var(log error) ~= (2/M) * Q / P^2, with Q the
   matching quarticity and P the matching proxy.
E1 Nugget, 2 arms (a exponential, d model-implied) x 2 lag sets (L1-5, L1-10).
E2 Non-overlapping contiguous halves.
E5 NEW. Signature-plot regression. Under additive noise E[RV_M] = IV + 2*M*omega^2.
   Regress RV_M on M across all available M; intercept gives IV, slope gives noise
   variance. Both feed the reliability calculation directly.
E6 NEW. Hansen-Lunde direct noise estimator, omega^2 = RV_finest / (2*n), used to
   correct the proxy before any other estimator is applied. Reported both standalone
   and as a pre-correction applied to E1, E2, E4.
E3 three-cornered hat is NOT carried forward. S01 flagged it INAPPLICABLE on every
   DGP through the pre-registered 0.20 error-correlation gate.

## Data-generating processes
Latent log-variance, window frequency:
D1 AR(1), control.
D2 ARFIMA(0,d,0), long memory.
D3 Fractional OU, rough.
D4 Fractional OU, moderately rough.

Within-window structure, applied to ALL of D1-D4 as a crossed factor:
W0 Constant within window. S01 condition, retained for comparability.
W1 Deterministic diurnal U-shape, peak-to-trough ratio swept.
W2 W1 plus stochastic within-window variation.

Contamination, crossed:
C0 None.
C1 Jumps.
C2 Microstructure noise.
C3 Jumps and noise.

W1 and W2 are the decisive cases for E2, whose S01 pass may depend on within-window
constancy.

## Parameter sweeps
All ranges are ASSERTED by the analyst and NOT measured on ES/NQ. Any conclusion
sensitive to position within a range is reported as such.

Noise-to-signal variance ratio: log-spaced, 1e-5 to 1e-1, nine points.
  This is the sweep the threshold map is built on and it is deliberately wider than
  any plausible value.
Jump share of expected total QV: {0, 0.02, 0.05, 0.10, 0.20}
Diurnal peak-to-trough variance ratio: {1, 3, 10}
Hurst H: {0.08, 0.10, 0.30, 0.50}
Long-memory d: {0.35, 0.45}
AR(1) persistence: {0.98}   (S01 showed insensitivity; fixed for compute)
Unconditional sd of latent log IV: {0.7}   (S01 showed insensitivity; fixed for compute)

## Geometry and sampling
n = 390 and n = 1380 intraday steps.
M giving {13, 26, 78, 195} for n=390 and {23, 46, 138, 345} for n=1380.

## Protocol
T = 2000 windows per replication. Replications = 200. Five master seeds, master 20260819.
Bootstrap 1000 resamples. Bands +/-10%, +/-15%, +/-25%; primary +/-15%.

## Unit tests, required before any DGP runs
V1 All S01 unit tests re-run and passing.
V2 Under constant volatility with known additive noise, P2, P3, P4 each recover IV to
   within their published asymptotic tolerance while P1 does not.
V3 Under a known jump path, P5, P6, P7 recover the continuous component while P1 does not.
V4 E5's signature-plot regression recovers a known omega^2 to within Monte Carlo error.
V5 Under W1 with a known diurnal profile, the profile is recovered from the simulated data.
V6 Under a directly constructed known lambda, every estimator recovers it at NSR = 0.
A failing unit test halts the session.

## Prohibited
No proxy, estimator, or arm selected after seeing results. No bandwidth, window, or
threshold tuned. Published parameter rules only, cited in code comments. No DGP added
or removed after results are seen. Any deviation logged in DECISIONS.md.
