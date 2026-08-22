"""S14 shared paths and imports. Nothing is reimplemented."""
import os, sys
import numpy as np, pandas as pd
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE,LOGS=(os.path.join(BASE,x) for x in ["results","cache","logs"])
S06=os.path.join(ROOT,"sessions","s06r-repair")
S07=os.path.join(ROOT,"sessions","s07-completion-and-spy")
S09=os.path.join(ROOT,"sessions","s09-application")
S10=os.path.join(ROOT,"sessions","s10-exponent-audit")
S11=os.path.join(ROOT,"sessions","s11-extensions")
S13=os.path.join(ROOT,"sessions","s13-extension")
for p in [os.path.join(S13,"src"),os.path.join(S11,"src"),os.path.join(S10,"src"),
          os.path.join(S09,"src"),os.path.join(S07,"src"),
          os.path.join(ROOT,"sessions","s05-reliability-mcs","src"),
          os.path.join(ROOT,"sessions","s02-mechanism-expansion","src"),
          os.path.join(ROOT,"sessions","s01-estimator-validation","src")]:
    sys.path.insert(0,p)
CELLS=[(r,g,b,h) for g in ["GLOBEX","RTH"] for r in ["ES","NQ"] for b in ["B0","B1"]
       for h in (["1day"] if g=="GLOBEX" else ["1day","1h","30min"])]
CELLS4=[(r,g) for g in ["GLOBEX","RTH"] for r in ["ES","NQ"]]
FIVEMIN={("RTH","1day"):78,("RTH","1h"):12,("RTH","30min"):6,("GLOBEX","1day"):276}
TICKS=[0.5,1.0,2.0,4.0]; TICKVAL={"ES":12.50,"NQ":5.00}; MULT={"ES":50.0,"NQ":20.0}
NDAY=252; TARGET_D=0.10/np.sqrt(252)
