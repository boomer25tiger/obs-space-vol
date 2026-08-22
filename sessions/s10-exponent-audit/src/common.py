"""S10 shared code path. Nothing here is a reimplementation of a measurement:
the window construction is the S08/S09 lambda code path verbatim (verified in
S09 Phase 3 to reproduce S08 phase4_fits.csv at max|dc|=0, max|db|=5.55e-17),
and `fitf` is S05E `fit_free` / S07 `fitf` unchanged.
Nothing here reads data dated on or after 2024-01-01.
"""
import os, sys
import numpy as np, pandas as pd
from scipy.optimize import curve_fit
from scipy.special import polygamma
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,LOGS=os.path.join(BASE,"results"),os.path.join(BASE,"logs")
S06=os.path.join(ROOT,"sessions","s06r-repair")
S07=os.path.join(ROOT,"sessions","s07-completion-and-spy")
sys.path.insert(0,os.path.join(S07,"src"))
sys.path.insert(0,os.path.join(ROOT,"sessions","s05-reliability-mcs","src"))
sys.path.insert(0,os.path.join(ROOT,"sessions","s01-estimator-validation","src"))
from phase2_rerun8 import tradeable_ext

CELLS=[(r,g,b,h) for g in ["GLOBEX","RTH"] for r in ["ES","NQ"] for b in ["B0","B1"]
       for h in (["1day"] if g=="GLOBEX" else ["1day","1h","30min"])]
GRID_EXT={("RTH","1day"):[5,6,10,13,26,78,195,389],("RTH","1h"):[4,5,6,10,12,15,20,30,60],
          ("RTH","30min"):[5,6,10,15,30],("GLOBEX","1day"):[5,6,10,12,23,46,138,276,345,1379]}
GRID_S05={("RTH","1day"):[13,26,78,195,389],("RTH","1h"):[60],("RTH","30min"):[30],
          ("GLOBEX","1day"):[23,46,138,345,1379]}
HOR={"1day":None,"1h":60,"30min":30}
SPY_GRID=[5,6,10,13,26,39,78,130,195,390,780,1560,2340,4680,11700,23400]
NPAR=3

def trig(M): return polygamma(1,np.asarray(M,float)/2.0)

def fitf(M,y):
    """S05E fit_free / S07 fitf, unchanged."""
    M=np.asarray(M,float); y=np.asarray(y,float); ok=np.isfinite(y)
    if ok.sum()<4: return None
    try:
        p,pcov=curve_fit(lambda x,c,A,b:c+A*np.power(x,b),M[ok],y[ok],
                         p0=[y[ok].min(),1.0,-0.5],maxfev=80000)
        pred=p[0]+p[1]*np.power(M[ok],p[2])
        return dict(c=float(p[0]),A=float(p[1]),b=float(p[2]),
                    rmse=float(np.sqrt(np.mean((y[ok]-pred)**2))),
                    n=int(ok.sum()),pcov=pcov)
    except Exception: return None

def fit_diag(M,y,f):
    """Jacobian condition number and asymptotic parameter correlation at the
    optimum. J columns are d/dc = 1, d/dA = M^b, d/db = A M^b log M."""
    if f is None: return dict(cond=np.nan,corr_cb=np.nan,corr_Ab=np.nan,corr_cA=np.nan)
    M=np.asarray(M,float); ok=np.isfinite(np.asarray(y,float)); M=M[ok]
    Mb=np.power(M,f["b"])
    J=np.column_stack([np.ones_like(M),Mb,f["A"]*Mb*np.log(M)])
    sv=np.linalg.svd(J,compute_uv=False)
    cond=float(sv.max()/max(sv.min(),1e-300))
    pc=f.get("pcov")
    def cr(i,j):
        if pc is None or not np.all(np.isfinite(pc)): return np.nan
        d=np.sqrt(pc[i,i]*pc[j,j])
        return float(pc[i,j]/d) if d>0 else np.nan
    return dict(cond=cond,corr_cA=cr(0,1),corr_cb=cr(0,2),corr_Ab=cr(1,2))

def screen_old(f):
    """The S08 screen: A > 0 and b < 0."""
    return bool(f and f["A"]>0 and f["b"]<0)

def screen_tight(f,npts):
    """S10 tightened screen: >= 2*NPAR grid points and |b| > 0.01, in addition."""
    return bool(screen_old(f) and npts>=2*NPAR and abs(f["b"])>0.01)

def cell_windows(root,geom,hname):
    """S08/S09 lambda code path: returns per-window returns, keep mask, dates."""
    z=np.load(os.path.join(S06,"cache",f"panel_ohlc_{root}_{geom}.npz"))
    cl=z["close"].astype(np.float64); pres=z["present"]
    ds=np.array(z["dates"],dtype="U10")
    trm,_=tradeable_ext(root,geom)
    r1=np.where(trm[:,1:]&trm[:,:-1],np.diff(cl,axis=1),0.0)
    keep=trm[:,1:]&trm[:,:-1]&pres[:,1:]&pres[:,:-1]
    wl=HOR[hname]
    if wl is None: rw,kw,nw=r1,keep,1
    else:
        nw=r1.shape[1]//wl
        rw=r1[:,:nw*wl].reshape(-1,wl); kw=keep[:,:nw*wl].reshape(-1,wl)
    live=kw.any(axis=1)
    return rw[live],kw[live],np.repeat(ds,nw)[live]

def subbars(rw,M):
    N,L=rw.shape; e=(np.arange(M+1)*L)//M
    cs=np.concatenate([np.zeros((N,1)),np.cumsum(rw,axis=1)],axis=1)
    return cs[:,e[1:]]-cs[:,e[:-1]]

def logrv_matrix(rw,Ms):
    """(n_windows, n_grid) matrix of log RV_M; NaN where RV_M is not positive."""
    out=np.full((rw.shape[0],len(Ms)),np.nan)
    used=[]
    for j,M in enumerate(Ms):
        if M>rw.shape[1]: continue
        rv=(subbars(rw,M)**2).sum(axis=1)
        out[rv>0,j]=np.log(rv[rv>0]); used.append(M)
    return out,used

def var_cols(L,idx=None):
    """Column-wise variance over the (optionally resampled) rows, NaNs skipped."""
    X=L if idx is None else L[idx]
    with np.errstate(invalid="ignore"):
        return np.nanvar(X,axis=0)

def spy_logrv_tick(ven):
    """Per-session log RV_M under the traded-tick convention, S07 phase 6
    construction (equal-count blocks of the traded sequence), unchanged."""
    zt=np.load(os.path.join(S07,"cache",f"spy_tick_{ven}.npz"))
    tpx=zt["logpx"].astype(np.float64); tcnt=zt["counts"]
    dates=np.array(zt["dates"],dtype="U10")
    starts=np.concatenate([[0],np.cumsum(tcnt)])
    S=len(tcnt); Lmax=23399
    out=np.full((S,len(SPY_GRID)),np.nan)
    for j,M in enumerate(SPY_GRID):
        Mu=min(M,Lmax)
        for i in range(S):
            a,b=starts[i],starts[i+1]; n=b-a
            if n<Mu+1: continue
            px=tpx[a:b]; e=(np.arange(Mu+1)*(n-1))//Mu
            d=np.diff(px[e]); rv=float((d*d).sum())
            if rv>0: out[i,j]=np.log(rv)
    return out,dates,[min(M,Lmax) for M in SPY_GRID]
