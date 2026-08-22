"""S06R Phase 9: reconstruct the frozen spec and verify artifact persistence."""
import json, os, re, sys, time
import numpy as np, pandas as pd
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
RES, CACHE = os.path.join(BASE,"results"), os.path.join(BASE,"cache")
SPECS = os.path.join(ROOT, "specs")

SPEC = """# SPEC-obs-space-vol-eval.md

Frozen record, reconstructed 2026-08-19 in S06R Phase 9 from `DECISIONS.md`,
which is the only surviving authority (the original spec documents were absent
from the repository at S03, DECISIONS item 11). Every element carries the date
it was fixed and whether it was pre-registered or added post hoc.

## 1. Model set

| model | definition | fixed | status |
|---|---|---|---|
| M1_EWMA | RiskMetrics, lambda 0.94 | 2026-08-18 (S05 PREREG Part D) | pre-registered |
| M2_HAR | Corsi (2009), lags 1/5/22 | 2026-08-18 (S05 PREREG Part D) | pre-registered |
| M3_HARJ | HAR plus max(RV-BV,0) | 2026-08-18 (S05 PREREG Part D) | pre-registered |
| M4_HARQ | Bollerslev, Patton, Quaedvlieg (2016) | 2026-08-18 (S05 PREREG Part D) | pre-registered |
| M5_RGARCH | Hansen, Huang, Shek (2012) | 2026-08-18 (S05 PREREG Part D) | pre-registered |
| M6_PARK, M6_GK | Parkinson and Garman-Klass, from TRUE bar high and low | rebuilt 2026-08-19 (item 43) | POST HOC repair of a defective construction |

Model-set reduction: where RGARCH parameters violate stationarity or the
forecasts diverge, the cell is marked RGARCH-unavailable and the set is reduced
there, with the reduction stated in every table. Fixed 2026-08-19 (item 41),
POST HOC. RGARCH is never filtered, respecified or constrained.

## 2. Estimator pair

E2 (non-overlapping contiguous halves) and E4 (asymptotic-variance route) are
retained and BOTH reported throughout; neither is primary. E1_a and E1_d are
dropped. Fixed 2026-08-19 (item 46), POST HOC, on the S05E control evidence:
E2 mean absolute error 0.006-0.012 on clean data degrading to 0.16-0.25 under
jumps; E4 0.045-0.051 clean, 0.105-0.128 under jumps.

Effective sub-bar count replaces nominal M wherever an estimator takes M.
Fixed 2026-08-19 (item 45), POST HOC.

## 3. Exclusion rules

| rule | fixed | status |
|---|---|---|
| Calendar-spread filter, root separation, CME trade-date session cut, front contract by volume, roll +/-1 | 2026-08-18 (S03 phases 2) | pre-registered (SCOPE section 3 as quoted) |
| Early close, geometry-dependent: RTH excludes any session halting before 15:00 NY; GLOBEX excludes only if the overnight is under 90% complete | 2026-08-18 (item 13, S04 R1) | POST HOC repair |
| Degraded Databento dates flagged, NOT excluded | 2026-08-18 (item 14, S04 R2) | POST HOC, deliberate non-exclusion |
| Weekend trade date reassigned to the next session | 2026-08-18 (item 15, S04 R3) | POST HOC repair |
| Non-trading windows excluded on EXCHANGE-CALENDAR grounds only, never on realized variance | 2026-08-19 (item 42) | POST HOC |

Calendar classes: EARLY_CLOSE_1300 (MLK, Presidents, Memorial, Independence,
Labor, Thanksgiving, Juneteenth from 2022) and FULL_CLOSURE_0930 (Good Friday,
and 2018-12-05 National Day of Mourning). Intraday trading halts, such as the
March 2020 circuit breakers, are NOT ex-ante determinable and are NOT excluded.

## 4. Forecast filter

Bollerslev, Patton and Quaedvlieg insanity filter on M3_HARJ and M4_HARQ:
any forecast outside the in-sample realized-variance range is replaced by the
in-sample mean. Applied identically in every cell whether or not it fires.
Fixed 2026-08-19 (item 40), POST HOC. A 100x-mean alternative is reported as a
sensitivity and is NOT adopted.

## 5. Holdout boundary

2024-01-01. Nothing on or after that date has been loaded, processed or
inspected in any session. Fixed 2026-08-18 (S03 PREREG), pre-registered,
restated unchanged 2026-08-19 (item 50).

## 6. Family size and multiplicity

The Part E family is 96 comparisons (24 cells x 2 conditioning quantiles x 2
confidence levels). No familywise correction is applied; its absence is
disclosed as a limitation, since correcting a count already seen would be worse
than disclosing it. Alongside the count, the result is reported at a single
cell chosen on the ex-ante criterion of largest effective sample, fixed before
the rerun. Fixed 2026-08-19 (item 47), POST HOC.

## 7. Kill conditions and their null abstracts

K1. The reliability correction does not change Model Confidence Set
composition.
  Null abstract: "Across 96 (cell, quantile, level) comparisons the model
  confidence set is invariant to whether evaluation conditions on the realized
  proxy or on a predetermined variable, and invariant to whether the
  information coefficient is corrected for proxy reliability. The correction
  rescales every model in a cell by a common factor and therefore cannot
  reorder them; the reliability programme is not decision-relevant for model
  selection." Fixed 2026-08-18 (item 15), pre-registered as the S05 criterion.

K2. No reliability estimator is grid-invariant.
  Null abstract: "lambda_M multiplied by Var(log RV_M) should be constant in M
  because Var(log IV) cannot depend on the sampling grid. No estimator holds it
  constant: the best achieves a max/min ratio of 1.05 and the worst 1.97, and
  the ranking is not stable across cells. Reliability as estimated here is a
  property of the grid, not of the data." Fixed 2026-08-19 (item 26), POST HOC.

K3. The measured proxy-error scaling is inconsistent with sampling theory.
  Null abstract: "Var(log RV_M) = c + A M^b fits the data with b between -0.41
  and -1.00 against a measured trigamma reference of -1.14. A positive control
  passing synthetic data through the identical code path recovers -1.19 at the
  same grid, and no arm - diurnal profile, calibrated jumps, measured padding
  or a rough volatility path - reproduces the observed flatness. The proxy
  error does not scale as sampling theory requires and the cause is not
  located." Fixed 2026-08-19 (items 36 and 37), POST HOC.

## 8. Provenance of every post-hoc element

Items 13-15 (S04 repairs), 26-32 (S05B estimator-validity additions), 33-38
(S05D/S05E panel integrity and positive control) and 39-50 (S06R repairs) were
all specified after the data they concern had been seen, and are marked POST
HOC in DECISIONS.md at the point of specification. Items 1-12, 16-25 were fixed
before the analysis they govern.
"""

def main():
    t0=time.time()
    os.makedirs(SPECS, exist_ok=True)
    open(os.path.join(SPECS,"SPEC-obs-space-vol-eval.md"),"w").write(SPEC)
    # ---- persistence verification: can every report figure be regenerated?
    need = {
      "Phase 1 invariant detection": ["results/phase1_invariants_on_s05.csv","results/phase1_summary.csv"],
      "Phase 2 close-grid check": ["results/phase2_close_grid_check.csv"],
      "Phase 2 high==low": ["results/phase2_high_eq_low.csv"],
      "Phase 2 M6 old vs new": ["results/phase2_m6_old_vs_new.csv","cache/m6_ES_GLOBEX.npz"],
      "Phase 2 E3 gate": ["results/phase2_e3_gate.csv"],
      "Phase 2 OHLC panels + present mask": ["cache/panel_ohlc_ES_GLOBEX.npz"],
      "Phase 3 calendar": ["results/phase3_calendar.csv","results/phase3_exclusion_counts.csv",
                            "results/phase3_crosscheck.csv","results/phase3_residual_uncovered.csv",
                            "cache/tradeable_ES_GLOBEX.npz"],
      "Phase 4 RGARCH params": ["results/phase4_rgarch_params.csv","results/phase4_rgarch_diagnosis.csv",
                                 "results/phase4_model_sets.csv"],
      "Phase 5 filter": ["results/phase5_filter.csv"],
      "Phase 6 lambda surface": ["results/phase6_lambda.csv","results/phase6_fits.csv",
                                  "results/phase6_effM_corr.csv","results/phase6_lambda_violations.csv"],
      "Phase 7 forecasts + loss matrices": ["cache/gen_ES_GLOBEX_B0_1day.npz",
                                             "cache/loss_ES_GLOBEX_B0_1day.npz"],
      "Phase 7 MCS + metrics": ["results/phase7_mcs.csv","results/phase7_metrics.csv",
                                 "results/phase7_composition_vs_s05.csv"],
      "Phase 8 primary result": ["results/phase8_primary.csv","results/phase8_effective_samples.csv",
                                  "results/phase8_primary_cell.json","results/phase8_s05a_indeterminate.csv"],
    }
    rows=[]
    for k,fs in need.items():
        miss=[f for f in fs if not os.path.exists(os.path.join(BASE,f))]
        rows.append(dict(report_element=k, files=";".join(fs),
                         regenerable=(len(miss)==0), missing=";".join(miss)))
    P=pd.DataFrame(rows); P.to_csv(os.path.join(RES,"phase9_persistence.csv"),index=False)
    tot=sum(os.path.getsize(os.path.join(dp,f)) for dp,_,fn in os.walk(CACHE) for f in fn)
    json.dump(dict(spec_written=os.path.join(SPECS,"SPEC-obs-space-vol-eval.md"),
                   n_elements=len(rows), n_regenerable=int(P.regenerable.sum()),
                   not_regenerable=P[~P.regenerable].report_element.tolist(),
                   cache_bytes=tot, seconds=round(time.time()-t0,1)),
              open(os.path.join(RES,"phase9_summary.json"),"w"), indent=1)
    print(P.to_string(index=False))
    print(f"\ncache {tot/1e6:.1f} MB; regenerable {int(P.regenerable.sum())}/{len(P)}")

if __name__=="__main__": main()
