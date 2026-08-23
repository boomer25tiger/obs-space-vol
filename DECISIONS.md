# Decisions log, observation-space volatility evaluation

Entries are append-only and numbered in the order the decisions were fixed, so the
numbering records sequence rather than importance and no number is ever reissued.
Every post-hoc deviation from a frozen specification carries its date and its
reasoning, and a claim later withdrawn is struck in place rather than deleted, so
that the withdrawal and the claim it retracts both remain readable. The K-series
numbering collisions are preserved as they were run, including the K1/K2 overlap
introduced at item 61 and the two distinct conditions both labelled K3; the paper
renumbers K1 through K13 cleanly and gives the mapping in the footnote to its
Table 2. Separately, and different in kind, ten item numbers are themselves
reused: 13, 14, 15 and 51 through 57 each appear twice, in every case with the
second occurrence revising the first, and both occurrences are preserved as run.
The voice of entries 1 through 140 was rewritten in S22 from the session-
instruction imperative in which each was drafted into record past tense, changing
no figure, date, threshold or withdrawal, and the unmodified original is retained
alongside this file as `DECISIONS-as-run.md`.

## 2026-08-18, session 1 reconciliation

1. Interleaved-subsample estimator REMOVED from the spec. Screening simulation
   showed replicate errors correlate by construction through interval overlap,
   biasing the estimate of measurement-error variance down by ~50% at spacing 2
   and ~86% at spacing 15, with microstructure noise contributing almost nothing
   to the failure. Non-overlapping temporal splits were retained as a separate arm.
2. Null N4 (k-sensitivity indicates violated independence) REMOVED. The failure
   mode it was written to catch cannot be diagnosed by the k-sweep, because
   increasing k worsens rather than reveals the bias.
3. Desroziers innovation diagnostic REMOVED. In the scalar-state scalar-observation
   case, writing the analysis as x_a = x_b + K(y - x_b) gives d_oa = (1-K)d_ob and
   d_ab = K*d_ob identically, so the diagnostic returns K for any K. Every gain is
   a fixed point. The method carries information only under observational
   over-determination, which this problem does not have.
4. DEPENDENCY STRUCTURE CHANGED. The reliability parameter lambda was sourced
   from the realized-quarticity route of Bollerslev, Patton and Quaedvlieg (2016),
   which has published asymptotic theory. The alternative estimators were demoted to
   a robustness comparison. The paper's central result no longer depends on any
   estimator developed here.
5. AEROSPACE PROVENANCE CORRECTED. No aerospace method survives in the error model.
   Nugget extrapolation is geostatistics (Matheron), three-cornered hat is clock
   metrology (Gray and Allan 1974). What remains from operational forecasting is the
   observation-operator framing and the representativeness decomposition. The
   writeup states this and claims nothing further.
6. Session 1 pre-registration parameters were rewritten after audit. The prior draft
   contained invented tolerances, a geometry inconsistent with the base spec
   (390 minutes against a full-Globex primary), a success criterion on a quantity
   that varies across generating processes by construction, and omitted the
   model-implied extrapolant that is available in closed form for exactly the
   processes most likely to break the nugget estimator.

## 2026-08-18, session 2 scoping

7. S01's verdict on D6/D7 was CONDITIONAL. Noise-to-signal ratios {0.001, 0.01} were
   asserted by the analyst, not measured on ES/NQ. S02 therefore reported breakdown
   thresholds across a wide swept range rather than pass/fail at asserted points.
8. S01 omitted noise-robust and jump-robust volatility proxies entirely. Every
   estimator was fed plain RV/RQ, so D6 and D7 tested the proxy, not the estimator.
   S02 added them as the primary proxy arm.
9. S01 DGPs hold integrated variance constant within each window (verified in
   code). E2's pass on D1-D4 may therefore be an artifact, since contiguous halves
   estimate the same quantity only under within-window constancy. S02 added
   within-window volatility variation and a diurnal profile.
10. E1 was reduced from 4 arms x 4 lag sets to 2 arms x 2 lag sets for compute reasons,
    retaining a_exp (baseline) and d_model (best performer on D3, 0.956 at L1-10),
    at L1-5 and L1-10. This was a compute decision citing S01 evidence, recorded here
    so it is not mistaken for post-hoc selection. The dropped combinations failed on
    D3 in every case and are documented in S01.

## 2026-08-18, session 3 documentation

11. SCOPE.md was not present anywhere in the working tree (checked at session
    start). S03 validated against the SCOPE figures quoted in the session
    instructions: 573,473 non-positive prices (matched exactly), ~91-day median
    front holding (matched: 91 ES / 89 NQ calendar days), 95-100% fill from 2016
    (matched: 95.1-100%), ~2,742 sessions from 2016 (consistent: 2,066 realized
    2016-2023 plus ~675 projected 2024-2026.6). The early-close rule as applied
    catches every session whose day portion halts before 15:00 New York: 68 per
    root, a superset of the ~18 designated half-days (day after Thanksgiving,
    July 3, Christmas Eve), because full-holiday shortened sessions (MLK,
    Presidents, Memorial, July 4, Labor, Thanksgiving) halt early in exactly the
    same way in the data. All 68 were excluded and enumerated; the 18-vs-68
    discrepancy is reported, not hidden.
12. NSR denominators: E[IV] in NSR = omega^2/E[IV] is the signature-plot
    intercept for both N1 and N2 (documented convention; the coarsest-M mean RV
    is reported alongside as the alternative denominator). N1-vs-N2 disagreement
    is reported as found; the Hansen-Lunde estimator's noise-dominance premise
    (2*n*omega^2 >> IV) fails at 1-minute bars, which S02 documented as the E6
    degeneracy, and the S03 data confirmed it: N2 exceeds N1 by roughly an order of
    magnitude everywhere.

## 2026-08-18, session 4 repairs

13. R1 split the early-close rule by geometry. RTH excludes all 68
    early-halting sessions per root (16 designated half-days plus 52
    holiday sessions); GLOBEX retains holiday sessions whose overnight is
    >= 90% complete, excluding only 16 (ES)
    / 21 (NQ). Final counts: RTH
    1901/1901 (ES/NQ), GLOBEX
    1953/1948. S03's single
    geometry-blind count was 1902/1902.
14. R2 degraded-condition dates are flagged, not excluded; 16 affected
    trade dates; all S04 diagnostics were reported with and without them.
15. R3 root cause: the weekend trade date 2018-08-05 came from two genuine
    pre-open prints (ESU8/NQU8) in the Sunday 17:59 halt minute; the +6h
    convention dates them Sunday. Patch: weekend-dated bars reassign to the
    next Monday (2 rows; -1 phantom session per root). Friday halt-window
    prints stay with Friday's session. Two S04 implementation bugs were found
    and fixed before any diagnostic ran, both logged: an over-broad first
    patch (pushed Friday prints to Saturday) and an object-dtype boolean
    inversion that collapsed the GLOBEX early-close rule to the RTH rule.

## 2026-08-18, S04 conclusion corrected before S05

13. The S04 reading that a Hill tail index of 2.95-3.67 rules out realized quarticity
    was OVERSTATED and is withdrawn. The Hill index is measured on the unconditional
    1-minute return distribution, which is a variance mixture across volatility
    regimes. Realized quarticity converges to integrated quarticity path-by-path under
    in-fill asymptotics without requiring the unconditional fourth moment to exist.
    What the tail index affects is cross-day pooling, averaging, and cross-day
    asymptotic variance, which is what the S04 concentration statistics measured.
14. E4 does not use RQ. It uses (2/M)*RQ/RV^2, which is scale-free and equals 2/M
    exactly under constant volatility. S04 reported RQ levels and never reported the
    ratio. The quantity that decides E4 was therefore unmeasured, and it was measured
    in S05.
15. PASS CRITERION CHANGED. No band on reliability recovery is used, because no
    published tolerance exists for how wrong a measurement-error estimate may be, and
    an invented band is not defensible. The criterion became whether Model Confidence
    Set composition differs between corrected and uncorrected evaluation, using the
    published MCS procedure of Hansen, Lunde and Nason (2011) at its conventional
    significance levels. The synthetic arm reports estimator error as a curve, not
    against a gate.
16. Realized kernel bandwidth uses the published rule H = 0.97 * xi^(4/5) * n^(3/5)
    with xi^2 = Var(noise)/IV, applied not tuned.

## 2026-08-18, reproducibility amendment

17. S03, S04 and S05 pinned no environment and, so far as the code shows, logged no
    seeds. S05A retrofitted what was retrofittable and determined by measurement
    whether S05 required a rerun, rather than presuming one.
18. Seed recovery was NOT attempted for the MCS bootstrap. Composition stability
    across many independent seeds was measured instead. Composition stable across
    seeds is a stronger claim than bitwise reproducibility of one draw.
19. The S03/S04 pipeline consistency test was run in S05A. Two copies of rules 1-4
    and 6 existed (S03 pipeline.main and the S04 re-execution) and nothing had
    asserted they agree. A failure would invalidate S04 and S05 downstream.
20. The comparison span and the verification cells were fixed by deterministic rule
    stated before execution, since neither could be named in advance of reading S05.
    Execution order was fixed for the same reason.

## 2026-08-18, S05 defect diagnosis and estimator validity audit

21. S05 section 5 reports M4_HARQ QLIKE of order 1e296 with R-squared near -630 and
    Spearman IC near 0.82 in the same cell. M3_HARJ shows the same pattern in two B1
    cells. S05B located and counted the responsible forecasts. No filter was applied there.
22. S05 Part E returns definite MCS compositions for cells whose section 5 loss column
    is inf or nan for every model. S05B inspected the array the MCS actually consumes
    and its non-finite handling, without re-running the MCS.
23. S05 section 5 applies one lam_hat per cell without recording which of the six
    Part C estimators produced it. S05B determined provenance by source inspection.
24. Every Part E composition and every section 5 metric was treated as unverified until
    items 21 to 23 were resolved.
25. POST-HOC ADDITION, disclosed as such. Items 26 to 32 were specified on 2026-08-18
    after the S05 report was read. They are diagnostic tests of estimator validity,
    not selections among outcomes, and no result reported in S05 is altered by them.
26. Var(log IV) is a property of the IV series at a given horizon and cannot depend on
    the sampling grid used to measure RV. Grid invariance of lambda_M * Var(log RV_M)
    is therefore an assumption-free validity test, and was adopted as the empirical
    basis for resolving item 23 in place of deferring to publication status.
27. The prior conclusion that microstructure noise is not a live explanation is
    WITHDRAWN. S03 established that noise is not binding at the 1e-2 scale tested by
    the S01 and S02 grids. It did not establish that noise is immaterial at the 1e-5
    scale relative to a target quantity of order 1e-2. The measured 4 to 10 percent
    signature-plot rise is an M-dependent RV distortion and was tested directly in S05B.
28. The exact finite-M sampling variance of log RV under constant volatility is
    trigamma(M/2), not 2/M. The approximation understates it by 40 percent at M=3,
    8.1 percent at M=13 and 0.3 percent at M=390, so the error concentrates at the
    coarse end where the elasticity fit takes its leverage. trigamma is used throughout
    and every prior use of 2/M is recorded.
29. The M grid was extended below the S05 range to M of 5, 6 and 10 where session length
    divides exactly. M=3 and below are excluded on estimator feasibility, since E2
    cannot form non-overlapping subsamples in a three-observation window and E4's
    quarticity is worthless there. Exclusion is NOT on information grounds; M=3 implies
    lambda near 0.30 and is the regime section 2.1 describes. A demonstration of that
    regime was deferred to a later session.
30. Horizons 1day, 1h and 30min were all in scope for RTH. Globex 1h and 30min were
    excluded for the whole session, since their repair belonged to a later session and
    conditional mid-session scope expansion would not be pre-registered. RTH intraday
    carries the lowest measured lambda in the study and was not dropped for convenience.
31. Boundary treatments B0 and B1 both ran on the full grid. Measured on the S05 output,
    switching treatments moves the fitted elasticity by a median 1.3 and a maximum 7.4
    percent, which is not negligible relative to the differences being tested.
32. The IC-IR column reported in S05 section 5 has no recorded definition. S05B
    established it by source inspection. The analytic ICIR attenuation result under
    heterogeneous lambda was pre-registered as an intended derivation for a later
    session and was not computed there.

## 2026-08-19, Globex panel integrity

33. S05B Phase 3 places 82.4 percent of Globex zero-variance windows at or after
    09:30 New York, concentrated at 13:00, 14:00 and 15:00, while every RTH cell over
    the same clock minutes contains none. The two panels cannot both be correct.
    Every Globex result in S03, S04, S05 and S05B was provisional until this resolved.
34. Globex 1day is NOT exempt on the grounds that it contains no zero-variance
    windows, since it reads the same panel and a column mapping defect would displace
    returns without creating zeros at daily aggregation.

## 2026-08-19, positive control on the aggregation path

35. S05D returned determination A. The Globex panel is correct, the zero-variance
    windows are holiday early closes on the 52 ES and 47 NQ sessions S04's R1 rule
    retains in GLOBEX and excludes from RTH, and DECISIONS items 33 and 34 are closed
    with no Globex result invalidated.
36. Var(log RV_M) = 1.018 + 2.082 M^(-0.439) on ES/GLOBEX/B0/1day, robust to padding
    exclusion at 8e-04. Sampling theory predicts an exponent near -1.04 on this grid.
    Noise, padding, panel construction and estimator choice are all excluded as causes.
37. No positive control had been run on the aggregation or reliability path. S05E ran
    one before any estimator was selected or any repair was specified. An estimator
    selection rule was NOT adopted until S05E returned.
38. The `present` mask is not persisted in the S05 panel npz files, so padding is
    indistinguishable from a genuine unchanged close for any consumer of those files.
    Recorded as an artifact defect; measured exposure at daily aggregation is 0.65
    percent of RV and 8e-04 on the fitted exponent.

## 2026-08-19, S06R repair and rerun

39. INVARIANT TESTS. Five assertions were written before any repair and run inside the
    pipeline, not as a separate check. Forecast positivity after filtering, loss-matrix
    finiteness before every MCS call, lambda within [0,1], range estimators receiving
    high and low columns, and effective sub-bar count matching the M passed to any
    estimator. A violation halts rather than warns.
40. FORECAST FILTER. The Bollerslev, Patton and Quaedvlieg insanity filter was applied
    to M3_HARJ and M4_HARQ, replacing any forecast outside the range of the in-sample
    realized variance with the in-sample mean. Replacement counts are reported per cell
    and per model. The filter was applied identically in every cell regardless of whether
    it fired.
41. RGARCH IS NOT FILTERED. At ES/GLOBEX/B1/30min M5_RGARCH returns 69,119 non-positive
    forecasts of 79,538, and at ES/GLOBEX/B0/30min 21,492 of 21,604 exceed one hundred
    times the in-sample RV mean. A filter would replace nearly every forecast with a
    constant and enter that constant into the confidence set under the name RGARCH.
    S06R diagnosed whether the estimated parameters violate stationarity, and where they
    did, RGARCH is reported as failing to estimate in that cell and the model set is
    reduced there with the reduction stated in every table.
42. NON-TRADING WINDOWS ARE EXCLUDED ON EXCHANGE-CALENDAR GROUNDS, NEVER ON THE BASIS
    OF REALIZED VARIANCE BEING ZERO. Excluding on measured RV would condition the
    evaluation sample on the realized proxy, which is the operation this project's own
    second result proves is not proxy-robust. The affected windows are the post-halt
    hours of the 52 ES and 47 NQ holiday sessions S05D identified, all of which are
    determinable from the CME calendar before the session begins.
43. RANGE ESTIMATORS WERE REBUILT FROM TRUE BAR HIGH AND LOW. The previous M6_PARK and
    M6_GK took max and min of the forward-filled cumulative close path, which is not a
    range estimator and carries an M-dependent downward bias. M6_GK is the sole MCS
    survivor in most GLOBEX cells, so its construction is load-bearing for the
    composition result. SCOPE section 6 confirms four prices per bar are held.
44. S01's E3 ERROR-CORRELATION GATE WAS RE-RUN on the corrected Parkinson and
    Garman-Klass series. The 0.805 correlation that triggered exclusion had been computed
    on misconstructed inputs. The outcome is reported, not presumed.
45. EFFECTIVE SUB-BAR COUNT replaces nominal M everywhere an estimator takes M as an
    argument. Because effective M depends on which minutes traded, the correlation
    between effective M and window realized volatility is reported per cell, so the
    activity coupling is measured rather than assumed negligible.
46. ADMISSIBLE ESTIMATOR PAIR. E1_a and E1_d were dropped. E1 fails on rough volatility
    by S01's own record and E1_d violates the [0,1] bound at three or four of nine grid
    points in every 1day cell. E2 and E4 were retained and BOTH are reported throughout,
    with each one's valid regime stated from the S05E control: E2 near-unbiased on clean
    data at mean absolute error 0.006 to 0.012 and degrading to 0.16 to 0.25 under
    jumps, E4 biased upward at 0.045 to 0.051 on clean data and holding at 0.105 to
    0.128 under jumps. Neither was designated primary. No further synthetic arms were run
    to break the tie, since lambda does not enter the MCS at all.
47. MULTIPLICITY. The Part E family size of 96 comparisons is stated explicitly against
    the effective sample. No familywise correction was applied and its absence is
    disclosed as a limitation, since correcting a count already seen would be worse than
    disclosing it. Alongside the count, the result is reported at a single cell chosen
    on the ex-ante criterion of largest effective sample, fixed before the rerun, because
    a count of differing cells is not a test statistic.
48. ARTIFACT PERSISTENCE. Every forecast panel, loss matrix, presence mask and lambda
    surface is written to disk. The repository must reproduce its own figures without
    re-running the pipeline.
49. LEVEL SANITY CHECK. The fitted intercept implies Var(log IV) near 1.02, so sd(log
    RV) near 1.0 and volatility ranging over a factor of about 2.7 per standard
    deviation. Five sessions examined how the proxy error scales with M and none checked
    whether its level was plausible. S06R reported the level against the sample's own
    volatility range.
50. Holdout boundary 2024-01-01 unchanged and untouched.

## 2026-08-19, S07 repair completion and SPY replication

51. EXCHANGE-DECLARED HALTS join the calendar exclusion. Circuit-breaker halts are
    recorded in the exchange log, so excluding them uses the exchange record rather
    than the realized proxy and stays inside item 42. Affected sessions identified in
    S06R Phase 3: 2020-03-09, 03-12, 03-18, 03-23, 03-24, plus 2019-02-27 and
    2020-07-01 which sit in the S04 R2 degraded-condition set and are excluded on that
    documented ground. Both classes are named individually in the spec.
52. FILTER LOWER BOUND is the smallest STRICTLY POSITIVE in-sample realized variance,
    not the in-sample minimum. S06R halted 8 cells because a zero in the warm-up made
    the lower bound zero, which admits a forecast floored at 1e-300. Post hoc revision,
    disclosed, made because the original bound is degenerate rather than because it
    produced an unwanted result.
53. RGARCH DIAGNOSIS was run in S06R on 16 cells that exclude every GLOBEX intraday
    cell, which are the 8 cells where RGARCH produced up to 87 percent non-positive
    forecasts. The question was left unanswered there and was answered in S07, on those 8
    cells.
54. MULTIPLICITY REPORTING. The S06R pre-specified cell ES/RTH/B0/30min stands as
    reported and was NOT replaced. Largest effective sample selects the cell where the
    MCS is most powerful and therefore narrows to a singleton under both schemes, which
    biases toward no difference. Two additions, both labelled post hoc: a stratified
    breakdown of the family by horizon, instrument, geometry and quantile, and a second
    pre-specified cell at the MEDIAN effective sample within the family, identified and
    logged before its comparison was computed.
55. SPY REPLICATION. The proxy-error exponent was refitted on SPY 1-second data,
    ARCX.PILLAR and XNAS.ITCH treated as two independent venue-level replications and
    never pooled. Purpose was to establish whether b near -0.44 is instrument-specific
    or general. The SPY grid spans roughly four decades of M against 2.4 for futures.
56. SPY CAVEATS FIXED IN ADVANCE. Results are labelled two-venue and cover roughly 33
    percent of consolidated volume. Microstructure noise at 1-second is NOT assumed
    negligible, unlike ES and NQ at 1-minute; the noise correction is applied and the
    primary M range is restricted to grid points where the implied bias is below a
    stated threshold. Effective sub-bar count is used throughout. SCOPE section 8.3
    does not gate this design because an exponent fit conditions on nothing, and the
    fill-versus-volatility correlation it requires is reported as a by-product.
57. SPY holdout boundary is 2024-01-01, matching futures. Nothing dated on or after it
    was read.

## 2026-08-19, S07 repair completion and SPY replication

51. EXCHANGE-DECLARED HALTS join the calendar exclusion. Circuit-breaker halts are in
    the exchange log, so excluding them uses the exchange record rather than the
    realized proxy and stays inside item 42. Sessions from S06R Phase 3: 2020-03-09,
    03-12, 03-18, 03-23, 03-24, plus 2019-02-27 and 2020-07-01 which sit in the S04 R2
    degraded-condition set and are excluded on that documented ground. Named
    individually in the spec.
52. FILTER LOWER BOUND is the smallest STRICTLY POSITIVE in-sample realized variance.
    S06R halted 8 cells because a zero in the warm-up made the bound zero, which admits
    a forecast floored at 1e-300. Post hoc revision, disclosed, made because the
    original bound is degenerate rather than because it produced an unwanted result.
53. RGARCH DIAGNOSIS in S06R ran on 16 cells excluding every GLOBEX intraday cell,
    which are the 8 where RGARCH produced up to 87 percent non-positive forecasts. The
    question was left unanswered there and was answered in S07 on those 8.
54. MULTIPLICITY. The S06R pre-specified cell ES/RTH/B0/30min stands and was NOT
    replaced. Largest effective sample selects the cell where the MCS is most powerful
    and narrows to a singleton under both schemes, biasing toward no difference. Two
    additions, both post hoc: a stratified breakdown by horizon, instrument, geometry
    and quantile, and a second pre-specified cell at the MEDIAN effective sample,
    logged before its comparison was computed.
55. SPY DATA is at `<DATA_ROOT>/DataBento Data/SPY 1s Data`, where DATA_ROOT is the
    local Databento download directory, outside the
    repository. The session inventoried it before reading, recorded a SHA-256 manifest
    into the repo, and rebuilt from raw. The derived parquets under `data/` were NOT
    consumed, because SCOPE section 3 records them carrying the uncorrected early-close
    defect in their `_daily_partial` rollup. [S22: absolute path generalised per item 145.]
56. SPY FILL IS A LIVE CONFOUND, not a caveat. Median fill of 0.667 to 0.686 means
    forward filling concentrates moves into the next traded second, inflating RV in an
    M-dependent way. On futures the same mechanism carried 0.65 percent of RV and was
    ignorable. The exponent was therefore fitted under BOTH calendar-time forward-filled
    sampling and traded-tick previous-tick sampling, and their difference is the
    measurement. A flat exponent under forward fill alone is not a replication.
57. SPY RESULTS ARE TWO-VENUE, covering roughly 33 percent of consolidated volume,
    labelled as such, with ARCX.PILLAR and XNAS.ITCH treated as independent
    replications and never pooled. Microstructure noise at 1-second is not assumed
    negligible; the noise correction is applied and the primary M range is restricted
    to grid points where implied bias stays below 1 percent. Effective sub-bar count is
    used throughout. SCOPE section 8.3 does not gate this design, since an exponent fit
    conditions on nothing, and its three required measurements are reported.
58. SPY holdout boundary is 2024-01-01, matching futures.

## 2026-08-19, S08 filter repair and K2 determination

59. THE INSANITY FILTER AS SPECIFIED WAS WRONG IN TWO WAYS, both analyst errors,
    disclosed. The observed pathology was one-sided, with forecasts driven to the
    1e-300 floor and nothing diverging upward, and a two-sided filter was prescribed.
    And it was applied to M3_HARJ and M4_HARQ alone, which handicaps the models it
    touches while M2_HAR keeps forecasts at 6.3e-03 against the same in-sample maximum
    of 1.19e-03. S07 measured the damage: the upper bound fired on 14 forecasts at
    ES/GLOBEX/B0/1day, replacing each with an in-sample mean roughly twenty times too
    small on the highest-volatility days, moving QLIKE from 0.164 to 0.555 and IC from
    0.838 to 0.753. The flag fired in 36 of 42 combinations, with replaced observations
    carrying 61 to 71 percent of mean QLIKE in the 1day cells.
60. REVISED FILTER. Lower bound only, applied identically to ALL SEVEN models. A
    forecast that is non-positive or at or below the 1e-300 floor is replaced by the
    smallest strictly positive in-sample realized variance. No upper bound. Replacement
    counts and the share of mean QLIKE carried by replaced observations are reported per
    cell and per model, and the quarter-share flag is retained as the acceptance gate.
61. THE MCS LEG IS EVALUATED AS K2. On the clean RTH geometry in S07, composition
    differed in 7 of 48 comparisons and both pre-specified cells returned no difference
    at all four comparisons, while the 15 of 24 GLOBEX rate sits where RGARCH is
    unavailable in all eight intraday cells and where the filter fired hardest. K2 was
    determined in S08 on repaired losses and reported whichever way it fell. The null
    abstract drafted before any result was seen is used verbatim if it fires.
62. RGARCH IS AN IMPLEMENTATION FAILURE, NOT A MODEL FAILURE. Omega is free with no
    variance targeting anywhere in partde.rgarch_ll, persistence reaches 60.8, phi
    reaches -30574, beta reaches 9.6e-120, and 16 of 31 refits converge in one cell.
    The paper states this as a failure of this implementation at intraday GLOBEX
    horizons and makes no claim about Realized GARCH.
63. INTERCEPT ROUTE TO LAMBDA, adopted as a third reported column beside E2 and E4.
    Fitting Var(log RV_M) = c + A M^b gives c as a direct estimate of Var(log IV), so
    lambda_M = c / Var(log RV_M) at any sampling frequency, with no assumption about how
    proxy noise scales. With A > 0 and b < 0 the estimate lies in (0,1) BY CONSTRUCTION,
    which no existing estimator does: E2 and E4 violated the bound at 14 of 248 grid
    points in S06R and at 3683 rows in the pre-repair artifacts. Fits with A <= 0 or
    b >= 0 are marked invalid and excluded, since the route is undefined there.
64. THE HOLDOUT WAS NOT OPENED IN S08. An earlier draft of that session proposed
    including it; that is superseded. The holdout opens once, at the economic validation
    of the sizing consequence, because realized tracking error on strategy returns is
    the quantity that needs it and nothing in S08 does.
65. SPY IS A ROBUSTNESS PARAGRAPH, not a second instrument leg. Traded-tick is the
    primary convention on the intercept-agreement argument, since it recovers 1.034
    against the futures range of 1.02 to 1.08 while calendar-time forward fill recovers
    1.557 for the same object. Calendar-time is the sensitivity. Three S07 SPY items are
    recorded as FAILED MEASUREMENTS rather than results: signature-plot noise returned
    negative in all twelve venue-year cells, truncated RV returned b of -6.26 and -32.59
    at RMSE 0.54 and 79.2, and several stratified fits are degenerate with intercepts of
    -141.06 and -65.74.

## 2026-08-19, S09 application

66. ITEM 29 AMENDED, disclosed. Item 29 barred M of 5, 6 and 10 from headline lambda
    values on the stated ground that E2 cannot form non-overlapping subsamples in a tiny
    window and E4's quarticity is worthless there. The intercept route postdates item 29
    and uses neither mechanism, needing only the fitted intercept from the whole grid and
    the directly observed Var(log RV_M). The reasoning therefore does not transfer.
    BOTH ranges are reported side by side throughout, restricted to the original grid and
    extended, with every grid point labelled. Neither is reported alone.
67. K2 IS NOT REPORTABLE WITHOUT A PLACEBO. S-B and S-C condition on different variables
    and therefore evaluate different subsets of days, so composition can differ because
    the data differs. The clean-geometry rate of 68.8 percent does not track lambda
    across horizons (65.6, 65.0, 70.0 percent against reliability of 0.840, 0.588,
    0.396), which is not what the section 2.2 mechanism predicts. A placebo scheme S-D
    conditioning on a second F_{t-1} variable, no proxy involvement, established the
    subset-variation baseline. The reportable quantity is the EXCESS of S-B against S-C
    over S-D against S-C, not the raw rate.
68. SIZING RULES, fixed before any result. Annualized volatility target 10 percent,
    daily rebalance, forecast from the M2_HAR model at five-minute-equivalent sampling.
    R1 no shrinkage, using the raw forecast. R2 textbook shrinkage at
    lam_theory = c / (c + trigamma(M/2)). R3 measured shrinkage at lam_intercept.
    On simulated paths only, R0 oracle sizing on known integrated variance, as the floor.
    Shrinkage applies in logs: E[log IV] = (1-lam)*mu_insample + lam*log(forecast).
69. SIZING METRICS. Primary is tracking error, the root mean squared deviation of
    log realized portfolio volatility from log target. Secondary is turnover, mean
    absolute change in position weight, priced across the pre-registered round-turn cost
    sweep of 0.5, 1.0, 2.0 and 4.0 ticks per leg at the SCOPE section 4 tick values of
    $12.50 for ES and $5.00 for NQ. A single assumed cost is not admissible.
70. SIGNAL SET AND THRESHOLD, fixed before any result. Candidates for forward realized
    variance: realized semivariance up, realized semivariance down, jump variation as
    RV minus bipower, Parkinson range, Garman-Klass range, volume surprise against a
    time-of-day norm, ES-NQ cross lead-lag, realized quarticity, signature-plot slope.
    Retention threshold R-squared >= 0.02 on the evaluation sample. Candidates partition
    into clears-under-both, clears-only-after-measured-correction, and clears-neither.
    The correction rescales every candidate in a cell by the same factor, so RANKING IS
    UNCHANGED BY CONSTRUCTION and only threshold crossing can change. That is stated in
    the report rather than presented as a finding.
71. K3 KILL CONDITION. If the tracking error difference between R2 and R3 is below 5
    percent in relative terms in every cell and at every point of the cost sweep, K3
    fires and the sizing consequence is reported as a pre-registered null using the
    drafted abstract. K3 is evaluated on the holdout, not in sample.
72. HOLDOUT OPENS ONCE, for ES and NQ from 2024-01-01 to 2026-08-14. No
    parameter, threshold, rule or specification is changed after any holdout number is
    seen. Tracking error on the holdout is measured from the strategy's own realized
    return series aggregated quarterly, where proxy attenuation is negligible, and that
    aggregation choice is stated as the reason the measurement is not circular.
73. NO FURTHER MEASUREMENT SESSION FOLLOWS S09. Roughness, vol-of-vol from the fitted
    intercept, the overnight leg, SPY as a second instrument, and cross-sectional
    reliability are recorded as further work and were not pursued.
74. THE S09 INTEGRITY SCAN OF 2026-08-19 IS VOID. It reported 61 of 142 sampled
    artifacts hashing to the SHA-256 of the empty string and concluded storage failure.
    Verification on the same day found every flagged file intact: PREREG.md returns 4716
    bytes under `wc -c`, all seven S02 source files carry real sizes, no migration
    process was running, the volume was at 33 percent capacity, and numpy 2.5.2 imports
    cleanly in `.venv`. The scan hashed several gigabytes including the 460 MB Databento
    archive, exceeded its command timeout, and returned the empty-string digest for every
    read it failed to complete. `S09-integrity-scan.txt` is retained as a record of the
    fault and its contents carry no evidential weight.
75. NO FULL-TREE HASHING OR INTEGRITY SCANNING IN ANY SESSION. Where file verification
    is needed, `wc -c` gives true byte counts in seconds and the S05A manifest is the
    reference.
76. ENVIRONMENT EVENT, 2026-08-19. The project virtual environment failed on pandas
    with an internal inconsistency between core/dtypes/common.py and core/dtypes/
    missing.py, and its pip was unusable. The environment was rebuilt from
    requirements.lock rather than patched, and the broken environment was retained at
    .venv-broken-20260819. Equivalence was verified by recomputing the ES/GLOBEX/B0/1day
    intercept fit against stored values. S09-PRE recorded whether the installed
    versions matched the lock before the rebuild; a mismatch would mean the environment
    drifted after S05A and sessions S05B through S08 did not run under the environment
    their runlogs record.
77. DECISIONS ITEMS 66-75 WERE LOST once already, appended during the aborted S09 run
    of 2026-08-19 and absent on later inspection. Any session appending to DECISIONS.md
    verifies by grep that its append persisted before proceeding.
78. ITEM 75 IS AMENDED. `wc -c` alone is insufficient for file verification. In S09-PRE
    the damaged pandas/core/dtypes/common.py returned 56,234 bytes under `wc -c` while
    yielding zero lines and erroring on `tail`, because byte count is metadata and
    survives the loss of the data blocks. File verification pairs `wc -c` with `wc -l`,
    and a file with a nonzero byte count and zero lines is treated as unreadable.
79. THE PROJECT ENVIRONMENT LIVES OUTSIDE THE iCLOUD SYNC SCOPE, at
    `~/venvs/obs-space-vol`. The failure of 2026-08-19 is most consistent
    with eviction under Optimize Mac Storage on a volume with 25 GiB free, and the pip
    vendored pygments file that failed in the morning read normally by afternoon, which
    corruption does not do and re-download does. Research artifacts remain in the synced
    directory, where eviction costs a re-download rather than a failure. Sessions verify
    at start that the active interpreter is outside any synced directory and halt
    otherwise. [S22: absolute path generalised per item 145.]

## 2026-08-19, S10 exponent validity audit

80. ITEM 73 IS AMENDED. It barred further measurement sessions. S10 ran because the
    headline exponent had never carried an uncertainty estimate: S08 Phase 4
    bootstrapped c and reported c_lo and c_hi, and reported nothing for b. Every claim
    of the form "materially flatter than sampling theory" rested on a point estimate
    with no error bar. Post hoc, disclosed. S10 added no new data and opened no holdout.
81. THE EXPONENT IS GRID-DEPENDENT BY MORE THAN HAS BEEN STATED. Across the four cells
    where both grids are defined, restricted b is -0.0001, -0.3456, -0.1445, -0.6259
    against extended -0.4427, -0.6886, -0.6274, -0.9744. The sign survives; the
    magnitude moves by up to 0.49 on the same cell and the same data. c and A*M^b are
    strongly correlated in this functional form and most information about b sits at the
    coarse end, so a three-parameter fit on eight to ten points may not support the
    quoted range as a measurement.
82. POOLING ACCOUNTS FOR PART OF THE GAP AND WAS NEVER FOLLOWED UP. S05E Phase 3 found
    within-year b steeper than pooled in 16 of 16 cells by a mean of 0.182 and steeper
    within volatility tercile in 15 of 16, so roughly a quarter of the headline anomaly
    is a pooling artifact by the project's own measurement. No within-year exponent had
    been reported for the full cell set beside the reference.
83. THE RETURN-DISTRIBUTION HYPOTHESIS WAS NEVER TESTED. trigamma(M/2) assumes Gaussian
    returns. S04 measured a tail index of 2.95 to 3.67. With heavy tails, RV built from
    few returns is dominated by the largest squared return, inflating Var(log RV_M) at
    coarse M and decaying more slowly than 1/M. Supporting evidence already held:
    truncation at 3 local SD moves the elasticity toward -1 by a mean of 0.415 with 10
    of 16 cells reaching -1.0, while adding calibrated jumps to Gaussian synthetic moved
    b by only 0.11. Arms A0 through A4 all use Gaussian innovations, so the arm that
    would catch this did not exist.
84. THE WITHIN-WINDOW ROUGHNESS HYPOTHESIS WAS NEVER TESTED EITHER. S05E's A4 arm
    generated roughness ACROSS sessions while holding volatility constant WITHIN them,
    and within-window variation is the only place a roughness effect on realized
    variance can live. A4's negative result is empty and is withdrawn. Roughness was to be
    tested in S10 only if Phase 5 left the gap open.
85. RS-UP AT ES/RTH/1h IS UNDER SUSPICION. It moved from in-sample R-squared 0.0128 to
    out-of-sample 0.237 and 0.240 while the 96 candidates clearing under both degraded
    from 0.479 to 0.313. Dead-then-strong against uniform degradation is more consistent
    with an alignment defect than a regime change. Diagnosed in sample; the holdout was
    not reopened.

## 2026-08-19, S11 defect correction, extensions and financial applications

86. ZERO-PREDICTOR WINDOWS ARE DROPPED, NOT FLOORED. S10 Phase 7 found three windows
    of 11,406 with RS-up exactly zero mapped to -690.78 by log(max(v,1e-300)) at
    phase5_signals.py:104 and phase6_holdout.py:330, moving R-squared from 0.0128 to
    0.4286. The justification is NOT item 60's insanity filter: zero upside semivariance
    is a legitimate observation, not an error, and substituting any value invents data.
    A window whose predictor is zero has no defined log-predictor and is dropped from
    that candidate's regression, count reported per cell, applied identically to every
    candidate, never conditioned on the target.
87. THE S09 PHASE 5 PARTITION IS VOID and was recomputed in S11. The defect reaches 32 of
    96 candidate-cells and flips retention in 16.
88. HOLDOUT RE-EVALUATION, DISCLOSED IN FULL. The holdout was opened once in S09 under
    defective predictor construction. S11 re-evaluated ONLY the candidates the defect
    touched, with no change to any threshold, rule, sizing parameter or specification.
    The defect is in predictor construction, not in anything the pre-registration
    protects. The sequence is reported in the paper as stated here.
89. sigma_w IS CALIBRATED, NOT CHOSEN. S10 Phase 6 flagged sigma_w as its weakest
    assumption. Within-window volatility dispersion is measurable from the excess of
    Q/P-squared over its constant-volatility value, which Part A reports at 0.81 to 1.48
    against trigamma. S11 calibrated sigma_w per cell to reproduce the measured ratio
    and re-tested the S10 roughness rejection against calibrated variation.
90. THE EXPONENT AS A PROXY SPECIFICATION TEST. Var(log X_M) = c + A*M^b was fitted for
    realized variance, the realized kernel and the two-scale estimator on identical
    data. Pre-registered reading: steeper b for the noise-robust proxies locates the
    anomaly in realized variance, flat b for all three locates it in the price process.
91. FINANCIAL APPLICATIONS, ALL PRE-REGISTERED BEFORE ANY RESULT IS SEEN. The project's
    structural result is that proxy noise is second-order where the loss surface is
    smooth and first-order wherever a threshold or a ratio intervenes. Three decisions
    of the second kind were tested: risk-limit breaches, inverse-MSE combination weights,
    and the variance-to-volatility swap convexity adjustment. Each carries a kill
    condition fixed here.
92. K4, RISK-LIMIT BREACHES. Leverage cap 2.0x and stop-out at realized volatility above
    1.5x target, both fixed here. K4 FIRES if the spurious breach rate under the proxy
    is below 1 percent of decision points in every cell, or if the cost of spurious
    breaches is below 1 basis point at every cost-sweep point.
93. K5, COMBINATION WEIGHTS. Inverse-MSE combination over the seven-model set, naive
    against noise-corrected. K5 FIRES if the mean absolute weight change is below 0.02
    in every cell, or if the resulting out-of-sample tracking-error difference is below
    5 percent relative in every cell at every cost-sweep point, matching item 71's
    threshold.
94. K6, CONVEXITY. K6 FIRES if the proportional overstatement of the convexity
    adjustment from naive Var(log IV) is below 5 percent in every cell.

## 2026-08-19, S12 correction

95. THE S11 PHASE 10 CONVEXITY MAGNITUDE IS VOID. It applied the Brockhaus-Long
    second-order expansion K_vol = sqrt(E[V]) * (1 - (exp(s2)-1)/8) at measured s2 of
    1.03 to 2.05, where Var(V)/E[V]^2 = exp(s2)-1 runs 1.8 to 6.8. The expansion needs
    that quantity small and is subtracting up to 85 percent of the strike. Under
    lognormal V the exact relation requires no expansion: E[sqrt(V)] = exp(mu/2 + s2/8)
    and sqrt(E[V]) = exp(mu/2 + s2/4), so K_vol = sqrt(E[V]) * exp(-s2/8). At s2 = 2.05
    the exact factor is 0.774 against the expansion's 0.154, a factor of five. The K6
    DETERMINATION was expected to survive since a hand recompute gives roughly 19 percent
    overstatement against a 5 percent threshold, but the reported 443 percent and 13.96
    volatility points are void.
96. THE S11 PHASE 6 MECHANISM CLAIM IS PROVISIONAL PENDING CALIBRATION VERIFICATION.
    Calibrated sigma_w of 1.495 to 4.805 implies within-window volatility varying by up
    to exp(4.8) in logs. The calibration target RQ/RV^2 has a constant-volatility value
    of exactly 1 and Part A measured 1.1 to 1.5, which under lognormal within-window
    volatility is reproduced near sigma_w = 0.6, not 4.8. Either the bisection converged
    on a far branch, or it solved against a different target than Part A measured, or
    RQ/RV^2 is far flatter in sigma_w than expected. Verified in S12 by reporting implied
    RQ/RV^2 at the calibrated value beside Part A's measurement per cell.
97. THE S11 PHASE 3 TREND p-VALUE IS NOT TRUSTWORTHY AS STATED. Cluster-robust inference
    is badly downward-biased below roughly thirty clusters and the trend used eight
    distinct cells. The point estimate of 0.047 per year stands; the t of -4.19 and
    p of 0.004 are replaced by wild cluster bootstrap.
98. K4 IS RESTATED BY LIMIT. The leverage cap at 2.0x never bound across 2,524 decision
    points, so only the stop-out was exercised. Reporting a two-limit specification as
    firing overstates coverage. K4 is reported per limit, with the cap recorded as
    untested at this target and the level at which it would begin to bind reported.
99. K4's MISSED-BREACH ASYMMETRY, observed in S11 and not written into item 92. Missed
    breach rate of 0.81 to 2.25 percent exceeds the spurious rate in three of four
    cells, because noise inflates estimated volatility and shrinks the position that
    would otherwise breach. Reported as a directional finding about proxy noise at
    risk limits, not as a kill-condition outcome.

## 2026-08-19, S13 mechanism extension, risk parity, trend structure, convexity table

100. THE WITHIN-WINDOW DISPERSION MECHANISM IS PARTIAL, NOT GENERAL. S12 narrowed
     S11's claim: the A6 exponent lands inside the observed range at 6 of 6 Hurst
     indices for both GLOBEX cells, 3 of 6 for NQ/RTH and 1 of 6 for ES/RTH. The
     mechanism explains GLOBEX and largely fails on RTH, which is the cleaner
     geometry. Something else drives the RTH anomaly and S13 tested one candidate.
101. THE OPEN-BAR CANDIDATE FOR RTH. S04 measured the 09:30 bar at 25.9 times the
     base extreme rate. A single dominant squared return at a FIXED position inside
     every window is a different object from the i.i.d. heavy tails S10 tested and
     rejected, and it is RTH-specific by construction, since GLOBEX windows open at
     18:00 into quiet. Arm A7 places one amplitude-matched dominant return at a fixed
     within-window position. Pre-registered reading: if A7 moves b into the observed
     range on RTH geometry and not on GLOBEX, the RTH residual is an open-bar effect.
102. RISK PARITY IS THE SECOND FIRST-ORDER APPLICATION. The class that matters is
     quantities depending on the VARIANCE of the estimate rather than its level.
     Inverse-volatility weighting qualifies, since E[1/sigma_hat] exceeds 1/sigma by
     approximately Var(log sigma_hat)/2 to second order, so an asset measured with
     more proxy noise is systematically overweighted. ES and NQ carry measured
     reliability of 0.84 and 0.93 at RTH daily, so a two-asset book between them is
     biased by a computable amount.
103. K7, RISK PARITY. Two-asset inverse-volatility book, ES and NQ, RTH daily,
     monthly rebalance, naive weights from proxy-based volatility against weights
     corrected for the measured reliability difference. K7 FIRES if the mean absolute
     weight deviation from the corrected allocation is below 0.02, or if the
     out-of-sample difference in realized portfolio volatility is below 5 percent
     relative at every cost-sweep point. Thresholds fixed here, before any result.
104. THE ANOMALY IS LARGELY HISTORICAL AND ITS SHAPE IS UNTESTED. At -0.047 per year
     over eight years the total movement is about 0.38 against a residual gap of
     0.357. S13 tested whether the closing is a smooth decline or a level shift at a
     date, since a break at 2020 implies a different account from a continuous trend.
105. THE HOLDOUT IS READ ONCE MORE, for the K7 application. No
     parameter, threshold, rule or specification changes. Disclosed in the paper
     alongside the S09 and S11 reads as a fourth opening, with the running count
     stated rather than described as single-use.

## 2026-08-20, S14 first-order applications

106. THE FIRST FOUR APPLICATIONS WERE CHOSEN BADLY, disclosed. K3, K4, K5 and K7 all
     fired because volatility targeting, risk limits, combination weights and risk
     parity sit where the loss surface is smooth or the contamination averages away
     with the estimation window. The operative criterion, established by S11 and S13,
     is that proxy noise is first-order only where the quantity of interest depends on
     the VARIANCE of the estimate and where more data does not reduce the
     contamination. S14 selected on that criterion.
107. K8, REGIME MISCLASSIFICATION. Days classified into volatility states by a
     threshold at the in-sample median of log realized variance, which unlike K4's
     leverage cap sits inside the distribution and binds at every decision point.
     K8 FIRES if the misclassification rate against the best available integrated-
     variance estimate is below 5 percent in every cell.
108. K9, HAR PERSISTENCE ATTENUATION. HAR regressors are noisy proxies, so
     coefficients are attenuated by errors in variables, and the daily, weekly and
     monthly components carry noise variance in the ratio 1, 1/5, 1/22, so the daily
     coefficient is attenuated most and the cleaner components absorb the difference.
     K9 FIRES if the corrected daily coefficient differs from the naive by less than
     10 percent relative in every cell. The point forecast of realized variance is NOT
     claimed to change; the claim is about reported persistence and relative lag
     structure, and the report states that limit explicitly.
109. K10, HURST BIAS. The standard estimator regresses the q-th absolute moment of
     log-volatility increments on lag; proxy noise adds a nugget that does not vanish
     at short lags, flattening the apparent scaling and biasing H downward. The
     project's lambda measures that nugget along sampling frequency rather than lag,
     an independent axis. K10 FIRES if corrected H differs from naive H by less than
     0.02 in every cell.
110. THE HOLDOUT IS READ ONCE MORE, for K8. Fifth opening. The
     running count is stated in the paper rather than describing the programme as
     single-use.

## 2026-08-20, S15 confound checks

111. K10 CARRIES A LAG-SELECTION CONFOUND. The nugget reaches 126 percent of the
     increment moment at lag 1, so corrected S(Delta) goes negative at short lags and
     those lags drop from the corrected regression. Short lags are precisely what
     identifies H in a rough-volatility fit, and refitting on longer lags mechanically
     raises H because the log-log slope over long lags approaches Brownian regardless
     of any nugget. An unknown share of the 0.208 shift on ES is therefore lag
     selection rather than nugget subtraction. No Hurst figure is reportable until
     naive H is refitted on exactly the surviving lag subset.
112. K9 ASSUMES CLASSICAL MEASUREMENT ERROR AND THE PROGRAMME'S CENTRAL FINDING
     DISPUTES IT. Sigma_E takes v from A*M^b, treating the whole excess over
     Var(log IV) as error independent of the true regressor. The excess decays at
     M^-0.44 rather than M^-1 and S11 attributes part of it to within-window volatility
     dispersion, a price-process property. If that component correlates with the level
     of integrated variance the error is non-classical and the correction over-corrects.
     A daily coefficient moving +116 percent with the weekly coefficient flipping sign
     on ES/GLOBEX is consistent with over-correction.
113. THE TREND HAS NOT BEEN TESTED AGAINST THE CONDITIONING CONTROL. S14 Phase 5 shows
     log condition number explaining 91 percent of within-cell year deviations at
     t = -23.5, and the 2022 dummy shrinking 80 percent once it enters. The linear year
     trend of -0.047 per year had never been regressed jointly against that control. If
     the year coefficient does not survive, the claim that the anomaly is shrinking is
     an artifact of fits becoming less identified in high-volatility years and comes
     out of the paper.
114. NO FURTHER MEASUREMENT SESSION FOLLOWS S15. The next artifact produced is the
     paper. Items recorded as further work stay there.

## 2026-08-20, S16 regime classification under measured reliability

115. ITEM 114 IS AMENDED, disclosed. It barred further measurement sessions. S16 ran
     because K8 measured a misclassification rate of 7.9 to 13.6 percent and a spurious
     switching cost reaching 138 basis points without ever testing whether correcting
     the observable reduces either. Post hoc, disclosed, and the rule was fixed here
     before any result was seen.
116. THE RULE IS SOURCED, NOT INVENTED. Specification from Blake, Gandhi and Jakkula
     (arXiv 2510.03236): Gaussian HMM on a z-scored smoothed realized-volatility series,
     rolling window of 441 observations stepped forward one at a time, RV from 5-minute
     returns scaled by N/n for short sessions, two regimes. The allocation overlay
     follows the Markov-switching asset allocation literature in reducing exposure
     during the high-volatility state and evaluating out of sample net of transaction
     costs.
117. THE SOURCE ASSUMES AWAY WHAT THIS PROJECT MEASURES. That paper states its 5-minute
     prices are free of microstructure noise and that its RV captures the full
     variability of prices at high frequency, then applies a 5-day moving average to the
     observable stating the purpose is for the HMM to capture structural changes rather
     than noise. The moving average is an unmotivated noise treatment. S16 replaced it
     with a shrinkage whose weight is the measured reliability.
118. THREE ARMS, FIXED HERE. A1 raw log realized variance, no smoothing. A2 the published
     5-day moving average. A3 shrinkage E[log IV | log RV] = (1-lam)*mu_insample +
     lam*log RV with lam from the intercept route, both admissible ranges reported per
     item 66. Identical HMM, window, state count and allocation across arms; the
     observable is the only thing that differs.
119. K11, REGIME CLASSIFICATION UNDER CORRECTION. Primary metric is misclassification
     against the finest-grid noise-robust proxy, as in K8. Secondary are switch count,
     turnover and cost across the pre-registered sweep, and Sharpe and maximum drawdown
     of the allocation overlay. K11 FIRES if A3 reduces misclassification by less than
     1 percentage point against BOTH A1 and A2 in every cell, or if the allocation
     Sharpe difference is below 0.10 at every cost-sweep point.
120. THE RECOVERABLE BAND IS REPORTED BEFORE ANY P&L. Shrinkage moves observations toward
     the unconditional mean and therefore can only reflip days whose raw observable lies
     within a computable band of the threshold. That band is reported per cell first, so
     the result is interpretable whichever way K11 falls.
121. HOLDOUT OPENS A SIXTH TIME. The running count is stated in the
     paper rather than describing the programme as single-use.

## 2026-08-20, S17 measurement error in the model rather than the observable

122. RESULT HIERARCHY, FIXED HERE AND NOT SUBJECT TO REVISION BY S17. The primary
     results are the proxy-error scaling exponent (S07-S15), the intercept estimator
     for lambda (S08, S15), and the first-order criterion separating decisions where
     proxy noise matters from those where it does not (S11, S13, S14). K1 through K11
     are applications of that criterion and are secondary. A negative S17 result
     bears on where the parameter can be inserted, not on whether it was measured
     correctly. The report states this ordering explicitly and does not lead with S17.
123. THE S16 A2 FINDING IS PROVISIONAL PENDING LAG ALIGNMENT. A 5-day trailing moving
     average lags by roughly two days. On ES/GLOBEX/1day, A1 switches 48 times across
     621 holdout windows, so a pure two-day shift mislabels about 96 days or 15.5
     percent against an observed A2-minus-A1 gap of 10.6 points, meaning phase lag
     alone predicts MORE disagreement than is observed. At NQ/RTH/1h the arms run on
     different time scales entirely, A1 switching 1,113 times at mean duration 3.3
     against A2's 182 at 20.4, with A2 at 46.03 percent which is chance. The claim
     that the published smoothing raises misclassification is not established until
     A2 is compared against a reference smoothed identically and against the minimum
     over integer lag shifts.
124. THE 30MIN IN-SAMPLE AGAINST HOLDOUT INVERSION IS UNEXPLAINED. NQ/RTH/30min runs
     48.48 percent in sample and 26.53 percent out of sample. Better than chance out
     of sample after chance in sample inverts the usual direction. State-label
     swapping under close state means is the leading candidate and is checkable from
     the persisted state series.
125. ARM A4, THE CORRECTION ENTERS THE MODEL. S16 established that any affine
     correction to the observable is annihilated exactly by within-window z-scoring,
     which is a property of the whole class of linear proxy corrections upstream of a
     normalising classifier. The remaining route is the observation equation. A4 is
     the same two-state Gaussian HMM with the emission variance in each state
     decomposed into a state variance plus a KNOWN observation-noise variance taken
     from the measured lambda, held fixed during estimation rather than estimated.
     Window, state count, normalisation, labelling, reference classifier and
     allocation are identical to A1, so the comparison isolates the emission change.
126. K12, MEASUREMENT ERROR IN THE EMISSION. Primary metric is misclassification
     against the finest-grid noise-robust reference, as in K8 and K11. K12 FIRES if
     A4 reduces misclassification by less than 1 percentage point against A1 in every
     cell. Secondary metrics are switch count, regime duration and the allocation
     overlay, reported but not determining. Threshold fixed here.
127. THE OBSERVATION-NOISE VARIANCE IS DERIVED, NOT TUNED. Var(eps) = (1 - lambda) *
     Var(log RV_M), the same construction item 109 used for the Hurst nugget, with
     lambda from the intercept route at both admissible and extended ranges per item
     66. No value was chosen to improve any outcome, and a sensitivity across scalings
     of 0.25, 0.50, 0.75 and 1.00 is reported so the result's dependence on the
     magnitude is visible.
128. HOLDOUT OPENS A SEVENTH TIME. Running count stated in the paper.
     S17 is the last measurement session in the programme. The next artifact is the
     paper.

## 2026-08-20, S18 paper draft and repository build

129. NO MEASUREMENT IS PERFORMED IN S18. Every figure in the paper is read from a
     persisted artifact. Any quantity that cannot be located in an artifact is reported
     as MISSING and left as a gap in the draft rather than recomputed, restated from a
     session report, or filled from context. Restating figures from memory had produced
     contradictions against emitted CSVs in five consecutive sessions, which is why the
     9.12 re-read requirement exists.
130. THE REPOSITORY IS PUBLIC. DECISIONS.md, the spec, the session reports and the
     invariant test suite are all published. Nothing is redacted, since the audit trail
     is part of the deliverable. Raw Databento data is NOT published and is excluded by
     .gitignore; the manifest of input hashes is published in its place.
131. SECTION 5 IS NOT DRAFTED IN S18. It carries K1 through K12 and its inclusion
     decisions are authorial. S18 drafted sections 4, 6, 7 and 8 against the approved
     outline and left section 5 as a stub with its table generated.
132. THE LATEX BUILD IS VERIFIED BEFORE PROSE IS FINALISED. A separate project was
     already blocked on a pandoc output-quality problem, so S18 built a minimal
     document to PDF first and would halt if the build failed, rather than discovering
     it at the end.

## 2026-08-21, S19 paper repair and completion

133. THE S18 DRAFT SHIPPED WITH ITS CENTRAL SECTION EMPTY. Abstract, Section 1, Section 2
     and Section 3 are headings with no body. Section 3 carries the scaling result that
     every later section references, so the document argues from a premise it does not
     state. Sections 4, 6, 7 and 8 were drafted as scoped; Section 3 was to be supplied
     as the register model and was neither supplied nor written.
134. THREE FIGURES FOR ONE QUANTITY. The count of in-sample states moved by the emission
     floor appears as 20,462 in the S18 draft, 18,311 in the S17 report, and 0/20/272/891
     summing to 1,183 in the S17 per-scaling table. The floor binding rate appears as
     153,613 of 294,906 windows in Section 6.2 and as 63 percent in Table 1, which
     disagree. Both were re-read from artifacts in S19. Restating figures from memory had
     produced contradictions in six consecutive sessions.
135. THE BLAKE CITATION IN THE S18 DRAFT IS WRONG. It reads "Regime detection in realized
     volatility with hidden markov models, 2025". The paper is Blake, Gandhi and Jakkula,
     "Improving S&P 500 Volatility Forecasting through Regime-Switching Methods",
     arXiv:2510.03236, 21 September 2025. Every reference in the bibliography is verified
     against a source before the build.
136. K NUMBERING IS RESOLVED FOR PUBLICATION. The K1/K2 collision from item 61 and the
     duplicate K3 are session-record artifacts. The paper renumbers cleanly and carries a
     footnote mapping paper numbering to session numbering. The repository retains the
     original labels.

## 2026-08-21, S20 Section 3 and paper corrections

137. SECTION 3 SHIPPED EMPTY TWICE. S18 and S19 both produced a document with a Section 3
     heading and no body, while the abstract, the introduction and Sections 4 through 8
     all reference its result. S20 wrote it and verified its inclusion in the built PDF
     before the session closed.
138. SECTION 2 CONTAINS FOUR DROPPED-TEXT DEFECTS. "spreads are removed at the symbol
     level", "exclusions below the estimation sample is", "consolidated tape." and
     "calendar and generated by rule." are fragments beginning mid-sentence or ending
     without a clause. They were repaired in S20 from the artifacts that supply the figures.
139. THE PAPER SAYS TWELVE KILL CONDITIONS AND TABLE 1 LISTS THIRTEEN. The renumbering
     under item 136 produced the mismatch. Thirteen is correct. The abstract and the
     introduction were corrected, and Table 1 regained the margin column dropped in the
     S19 rewrite, without which the determinations are asserted rather than evidenced.
140. TWO SUBSTANTIVE ERRORS. Section 7.2 states that tercile boundaries place the
     threshold "where the density is higher"; for a unimodal distribution the median sits
     nearer the mode and the tercile boundaries sit further out, so the stated mechanism
     is backwards. The empirical rate rises because two boundaries admit more
     disagreements than one. And signature plots are Andersen, Bollerslev, Diebold and
     Labys (2000), "Great Realizations", Risk 13(3), not the 2001 JASA paper currently
     cited, which concerns the distribution of realized volatility.

## 2026-08-22, S22 decisions log register rewrite

144. THE LOG IS REWRITTEN IN A RECORD REGISTER, NOT REDACTED. Entries 1 through 140 were
     written as session instructions, in imperative voice with phase numbers and stop
     conditions, because each was drafted inside the prompt that ran it. S22 rewrites the
     voice and preserves the substance: same entries, same numbering, same dates, same
     figures, same withdrawals. Nothing is removed and nothing is softened. The
     unmodified file is committed as DECISIONS-as-run.md and the rewrite is checked
     against it mechanically. [S23: corrected from "143" per item 149.]
145. TWO ABSOLUTE PATHS ARE GENERALISED. Items 55 and 79 contain paths under the author's
     home directory. They are replaced with relative or generic forms. The change is
     recorded here rather than made silently, since the log's claim is that it is
     append-only.
146. SCOPE.md IS NOT IN THE WORKING TREE. Item 11 records that it was absent at S03 and
     that the session validated against figures quoted in the session instructions
     instead. S22 states where the document lives and why it is not in the repository, or
     includes it.
147. THE S22 BRIEF'S PREMISES DID NOT MATCH THE FILE, recorded rather than corrected
     silently. The brief specified entries 1 through 143; the log's highest item number was
     140 and no items 141, 142 or 143 had ever been written, so the entries appended in S22
     were numbered 144 to 146 as instructed and the numbering now skips 141 through 143.
     Item 144's own phrase "entries 1 through 143" was left as supplied and inaccurate on
     that point. [S23: superseded, the phrase was corrected per item 149.] The log also
     carries ten item-number collisions that predate S22: numbers 13, 14 and 15 are each
     used twice, under the session 4 repairs header and under the S04 conclusion header, and
     numbers 51 through 57 are each used twice under two identically titled S07 headers, the
     second block revising the first. All are preserved as run.
148. SCOPE.md WAS NOT FOUND ANYWHERE ON THE MACHINE, resolving item 146. A search of the
     user's home directory to depth six returned nothing. The document was never in the
     repository and no copy survives outside it; the figures and section references
     attributed to it throughout this log, at items 11, 43, 55, 56, 57 and 69, reach the
     record only as quotations inside session instructions. Those quotations, and not the
     document, are what S03 and later sessions validated against, and the spec records
     the same provenance at its own pre-registration table with the phrase "SCOPE section
     3 as quoted". No reconstruction was attempted.

## 2026-08-22, S23 log corrections and first commit

149. ITEM 144 IS CORRECTED IN PLACE. It reads "Entries 1 through 143" and entries 141
     through 143 never existed; the log's highest item number before S22 was 140. The
     phrase is corrected to "Entries 1 through 140" with an inline marker in the style of
     item 145's path edits. Append-only means entries are not deleted, not that a factual
     error in a supplied entry stands uncorrected. Item 147 continues to record the
     numbering gap, which is a real property of the file.

## 2026-08-22, S23B paper insertions, path scrub and first commit

150. THE S21 SESSION NEVER RAN. Its prompt specified a Section 3.5 calibration caveat and
     the full text of Section 5, and the label survives only as a comment in
     03_exponent.tex and four numbers.csv notes attached to the post-S20 prose revision.
     Neither insertion reached the paper. The text is embedded in the S23B prompt itself.
     This is the fourth handoff failure of the same kind and the response is to stop
     referencing text as supplied elsewhere.
151. HOME-DIRECTORY PATHS ARE SCRUBBED FROM THE TRACKED SET. 391 occurrences of an
     absolute home path span 56 files, including session runlogs, ENVIRONMENT.md and four
     files under results/. Publishing them exposes an account name and a local directory
     layout to no purpose. The working directory is replaced with <REPO> and the home
     prefix with ~ throughout. DECISIONS-as-run.md is exempt, since it is the unmodified
     record and item 145 documents its two occurrences.
152. THE GIT AUTHOR IS SET LOCALLY FOR THIS REPOSITORY. The commit author matches the
     paper byline. The global identity is unchanged.

## 2026-08-22, S23C final correction and push

153. THE PLACEBO SENTENCE IN SECTION 5.4 IS CORRECTED. It read that the raw effect is
     "roughly half subset variation". The artifact gives a raw rate of 0.6875 against a
     placebo of 0.4792, so the placebo accounts for roughly seventy percent of the raw
     rate and the excess is 0.2083. The original phrasing understated the placebo and
     overstated what survives it. The correction was supplied by the author after S23B
     flagged the discrepancy without editing supplied text, which was the correct
     handling.
154. COMMIT AUTHORSHIP USES A GITHUB NOREPLY ADDRESS. The commit email is permanent and
     indexed once pushed. The paper byline carries the author's name where it belongs.
     The global git identity is unchanged.
155. THE OBJECT STORE IS PRUNED BEFORE THE FIRST PUSH. 1,213 unreachable loose objects,
     268 MB against 15.86 MB of tracked content, are residue from an aborted `git add -A`
     over the raw extract in S18. They are unreachable from any commit and `data/` holds
     the source, so pruning loses nothing.
156. DECISIONS-as-run.md RETAINS TWO ABSOLUTE PATHS BY DESIGN. It is committed unmodified
     as the original record and item 145 documents the two occurrences that are
     generalised everywhere else. The README states this so it is not read as an
     oversight.
157. THE COMMIT EMAIL IS 208218876+boomer25tiger@users.noreply.github.com, confirmed by
     the author. S23C halted rather than inferring it from the authenticated session,
     which is the correct handling of a value that is permanent once pushed.
158. THE README CARRIED FOUR STALE FACTS AFTER THE FIRST PUSH, corrected here. It
     described section 5 as a stub after S23B had written it, gave the log as 155 entries
     numbered to 148 against 164 and 157, gave the session count as twenty-six through
     S22, and omitted `results/`, `ENVIRONMENT.md` and `ENVIRONMENT-pre-20260819.md` from
     the contents table. The status section now also records what remains open, and the
     reproducibility section states that the per-session measurement scripts cannot run
     from a clone because they read the unpublished vendor data, which the clone
     verification in S23D established and the README did not say.
159. A COUNT OF THE LOG MUST NOT BE TYPED INTO A FILE COMMITTED ALONGSIDE AN APPEND TO
     THAT LOG. The README stated an entry count and the same commit appended item 158,
     making the figure wrong on arrival. The same trap was hit once before. The count is
     generated from DECISIONS.md at build time from S24 onward.
160. CHECKS RUN AGAINST EXTRACTED, NORMALISED TEXT, NOT SOURCE. Four checker failures
     across S20 to S23D were false positives caused by regexes meeting real typography: a
     typographic apostrophe, an underscore rendered under OT1, and two phrases wrapping
     across a line. Every check normalises whitespace and unicode punctuation before
     matching.
161. tests/test_invariants.py IS AN ASSERTION LIBRARY, NOT A PYTEST SUITE. Item 39
     specifies assertions called from inside the pipeline, so pytest reports that no
     tests ran. The paper claims twice that five invariants reproduce five silent
     pipeline failures, and a reader running pytest against a clone sees an empty suite.
     S24 adds a wrapper that exercises the five against the pre-repair S05 artifacts at
     their recorded counts. The library is unchanged.
