"""S11 shared code path.

The S09 sources are prior artifacts and are NOT edited (session stop condition).
The floor defect lives in the regression drivers `phase5_signals.main` and
`phase6_holdout.main`, not in the predictor builders: `phase5_signals.build`,
`phase6_holdout.wins` and `phase6_holdout.feature_block` all return RAW,
un-logged candidate values. Those three are imported unmodified here and only
the regression driver is re-executed with item 86's drop-on-zero rule in place
of `np.log(np.maximum(v, 1e-300))`. This is the S04-build precedent: re-execute
the driver, import everything it calls.
"""
import os, sys
import numpy as np, pandas as pd
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE,LOGS=(os.path.join(BASE,x) for x in ["results","cache","logs"])
S06=os.path.join(ROOT,"sessions","s06r-repair")
S07=os.path.join(ROOT,"sessions","s07-completion-and-spy")
S09=os.path.join(ROOT,"sessions","s09-application")
S10=os.path.join(ROOT,"sessions","s10-exponent-audit")
for p in [os.path.join(S09,"src"),os.path.join(S07,"src"),
          os.path.join(ROOT,"sessions","s05-reliability-mcs","src"),
          os.path.join(ROOT,"sessions","s01-estimator-validation","src"),
          os.path.join(S10,"src"),
          os.path.join(ROOT,"sessions","s02-mechanism-expansion","src")]:
    sys.path.insert(0,p)
CELLS=[(r,g,b,h) for g in ["GLOBEX","RTH"] for r in ["ES","NQ"] for b in ["B0","B1"]
       for h in (["1day"] if g=="GLOBEX" else ["1day","1h","30min"])]
FIVEMIN={("RTH","1day"):78,("RTH","1h"):12,("RTH","30min"):6,("GLOBEX","1day"):276}
HOR={"1day":None,"1h":60,"30min":30}
THRESH=0.02
CANDS=["RS_up","RS_down","JumpVar","Parkinson","GarmanKlass","VolumeSurprise",
       "CrossLeadLag","RealizedQuarticity","SignatureSlope"]
# the three candidates whose raw value can be exactly zero (S10 Phase 7b)
DEFECT_TOUCHED=["RS_up","RS_down","JumpVar"]
KEYMAP={"RS_up":"rsu","RS_down":"rsd","JumpVar":"jv","Parkinson":"park",
        "GarmanKlass":"gk","RealizedQuarticity":"rq"}
TICKS=[0.5,1.0,2.0,4.0]; TICKVAL={"ES":12.50,"NQ":5.00}; MULT={"ES":50.0,"NQ":20.0}
NDAY=252; TARGET_D=0.10/np.sqrt(NDAY)

def logdrop(v):
    """Item 86: a window whose predictor is zero (or negative) has no defined
    log-predictor and is dropped. Never floored, never substituted, and the
    rule looks only at the predictor."""
    v=np.asarray(v,float)
    out=np.full(v.shape,np.nan)
    m=v>0
    out[m]=np.log(v[m])
    return out,int((~m).sum())

def r2_ic(x,y):
    ok=np.isfinite(x)&np.isfinite(y)
    if ok.sum()<50: return np.nan,np.nan,int(ok.sum())
    ic=float(np.corrcoef(x[ok],y[ok])[0,1])
    return ic,ic*ic,int(ok.sum())
