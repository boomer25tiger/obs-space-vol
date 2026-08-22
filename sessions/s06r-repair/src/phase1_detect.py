"""S06R Phase 1: run the invariants against the STORED S05 artifacts.

Record that the tests detect the defects they were written for, before any
repair. Read-only on prior sessions.
"""
import json, os, sys
import numpy as np, pandas as pd
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, os.path.join(BASE, "tests"))
from test_invariants import (InvariantViolation, assert_forecasts_positive,
                             assert_loss_finite, assert_lambda_in_unit,
                             assert_range_inputs, assert_effective_M)
S05 = os.path.join(ROOT, "sessions", "s05-reliability-mcs", "results")
S05A = os.path.join(ROOT, "sessions", "s05a-reproducibility", "results", "cache")
S05B = os.path.join(ROOT, "sessions", "s05b-defect-and-estimator-audit", "results")
S05BC = os.path.join(S05B, "cache")
MODELS = ["M1_EWMA","M2_HAR","M3_HARJ","M4_HARQ","M5_RGARCH","M6_PARK","M6_GK"]
rows = []

def rec(test, cell, model, passed, msg):
    rows.append(dict(test=test, cell=cell, model=model or "",
                     result="PASS" if passed else "FAIL",
                     message="" if passed else msg))

# ---- 1. forecast positivity, from the S05B regenerated forecast panels
for f in sorted(os.listdir(S05BC)):
    if not f.startswith("fc_"):
        continue
    cell = f[3:-4]
    z = np.load(os.path.join(S05BC, f))
    ok = z["ok"]
    for m in MODELS:
        F = z[f"F_{m}"][ok]
        try:
            assert_forecasts_positive(F, cell, m); rec("assert_forecasts_positive", cell, m, True, "")
        except InvariantViolation as e:
            rec("assert_forecasts_positive", cell, m, False, str(e))

# ---- 2. loss finiteness, from the S05A cached loss matrices
for f in sorted(os.listdir(S05A)):
    if not f.startswith("loss_"):
        continue
    cell = f[5:-4]
    z = np.load(os.path.join(S05A, f))
    L = z["L"]
    for key in [k for k in z.files if k.startswith("mask_")]:
        scheme = key[5:]
        Ls = L[z[key]]
        try:
            assert_loss_finite(Ls, f"{cell}/{scheme}", MODELS)
            rec("assert_loss_finite", f"{cell}/{scheme}", "", True, "")
        except InvariantViolation as e:
            rec("assert_loss_finite", f"{cell}/{scheme}", "", False, str(e))

# ---- 3. lambda in [0,1], from S05 Part C
C = pd.read_csv(os.path.join(S05, "s05_partc.csv"))
for (r_, g, b, h, M, y, t), grp in C.groupby(["root","geom","btag","horizon","M","year","tercile"]):
    cell = f"{r_}/{g}/{b}/{h}/M{M}/y{y}/t{t}"
    for _, rr in grp.iterrows():
        try:
            assert_lambda_in_unit(rr["lam"], cell, rr["estimator"])
        except InvariantViolation as e:
            rec("assert_lambda_in_unit", cell, rr["estimator"], False, str(e))
n_lam = len(C)

# ---- 4. range inputs, from the stored S05 panels
for f in sorted(os.listdir(S05)):
    if not f.startswith("panel_"):
        continue
    z = np.load(os.path.join(S05, f))
    panel = {k: z[k] for k in z.files}
    try:
        assert_range_inputs(panel, f[:-4]); rec("assert_range_inputs", f[:-4], "", True, "")
    except InvariantViolation as e:
        rec("assert_range_inputs", f[:-4], "", False, str(e))

# ---- 5. effective M vs nominal M, from the S05B grid index
G = pd.read_csv(os.path.join(S05B, "phase4_grid_index.csv"))
for _, rr in G.iterrows():
    cell = f"{rr.root}/{rr.geom}/{rr.btag}/{rr.horizon}/M{rr.M}"
    if rr.share_full_M >= 1.0:
        rec("assert_effective_M", cell, "", True, ""); continue
    n_mismatch = int(round((1 - rr.share_full_M) * rr.n_windows))
    rec("assert_effective_M", cell, "", False,
        f"[assert_effective_M] cell={cell}: M passed = {rr.M} but effective "
        f"count differs in {n_mismatch} of {rr.n_windows} windows "
        f"(share at full nominal M = {rr.share_full_M:.4f}, mean effective "
        f"M = {rr.mean_eff_M:.2f})")

R = pd.DataFrame(rows)
R.to_csv(os.path.join(BASE, "results", "phase1_invariants_on_s05.csv"), index=False)
summ = R.groupby("test")["result"].value_counts().unstack(fill_value=0)
if "FAIL" not in summ: summ["FAIL"] = 0
if "PASS" not in summ: summ["PASS"] = 0
summ["n_lambda_rows_checked"] = [n_lam if i=="assert_lambda_in_unit" else "" for i in summ.index]
summ.to_csv(os.path.join(BASE, "results", "phase1_summary.csv"))
print(summ.to_string())
print()
for t in R.test.unique():
    f = R[(R.test==t)&(R.result=="FAIL")]
    if len(f):
        print(f"--- {t}: {len(f)} failures, first: {f.message.iloc[0][:220]}")
