"""S17 shared code: paths, the A4 fixed-noise emission estimator, and the
wlen-aware cell builder (the S16 Phase 3 correction, applied from the start).
"""
import os, sys
import numpy as np, pandas as pd
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE,LOGS=(os.path.join(BASE,x) for x in ["results","cache","logs"])
S09=os.path.join(ROOT,"sessions","s09-application")
S16=os.path.join(ROOT,"sessions","s16-regime")
for p in [os.path.join(S16,"src"),
          os.path.join(ROOT,"sessions","s11-extensions","src"),
          os.path.join(ROOT,"sessions","s10-exponent-audit","src"),
          os.path.join(S09,"src"),
          os.path.join(ROOT,"sessions","s07-completion-and-spy","src"),
          os.path.join(ROOT,"sessions","s05-reliability-mcs","src"),
          os.path.join(ROOT,"sessions","s02-mechanism-expansion","src"),
          os.path.join(ROOT,"sessions","s01-estimator-validation","src")]:
    sys.path.insert(0,p)
from common16 import (WINDOW,N_STATES,MA_LEN,FIVEMIN,CELLS8,CELLS4,TICKS,TICKVAL,
                      MULT,NDAY,TARGET_D,gauss_hmm_fit)
from common import cell_windows,subbars
from proxies_robust import p1_rv,p3_kernel_flattop,kernel_H
import phase6_holdout as p6
SCALINGS=[0.25,0.50,0.75,1.00]

def safe_fit(z,init=None,v=None):
    """Guarded wrapper. S16 `common16.gauss_hmm_fit` divides by c[0] without the
    underflow guard it applies at c[t>0] (common16.py:50 against :51), so when
    pi*B[0] underflows the forward pass returns NaN, the warm start carries NaN
    into every later window and EM runs its full iteration cap without
    converging. S16's own series were audited and are clean -- the underflow is
    reached only by the MA-smoothed kernel series introduced here -- so the S16
    artifact is left untouched and the failure is handled at the call site:
    validate the returned parameters, retry cold once, and otherwise leave the
    window unclassified and count it."""
    for attempt,ini in enumerate((init,None)):
        with np.errstate(all="ignore"):
            p,g=(gauss_hmm_fit(z,init=ini) if v is None
                 else gauss_hmm_fixednoise(z,v,init=ini))
        arrs=[p["mu"],p.get("sd",p.get("s2")),p["A"],p["pi"]]
        if all(np.isfinite(a).all() for a in arrs) and np.isfinite(g).all():
            return p,g,attempt
    return None,None,2

def gauss_hmm_fixednoise(x,v,n_iter=60,tol=1e-6,init=None):
    """Two-state Gaussian HMM whose emission variance in state k is
    sigma_k^2 + v with v KNOWN and held fixed. Only sigma_k^2, the state means
    and the transition matrix are estimated.

    IDENTIFIABILITY. sigma_k^2 = total_k - v must be non-negative, so the fixed
    noise floor must not exceed the total emission variance in either state.
    Where it does, sigma_k^2 clamps at zero and the emission variance is v. The
    estimator is therefore exactly the free-variance HMM with a variance FLOOR
    at v, and it differs from A1 only in windows where the floor binds. The
    binding count is returned and reported.
    """
    T=len(x)
    if init is None:
        q=np.quantile(x,[0.25,0.75])
        mu=np.array([q[0],q[1]]); s2=np.maximum(np.array([x.var(),x.var()])*0.64-v,1e-9)
        A=np.array([[0.95,0.05],[0.05,0.95]]); pi=np.array([0.5,0.5])
    else:
        mu,s2,A,pi=(init["mu"].copy(),init["s2"].copy(),
                    init["A"].copy(),init["pi"].copy())
    ll_old=-np.inf; nbind=0
    for _ in range(n_iter):
        var=s2+v; sd=np.sqrt(var)
        B=np.exp(-0.5*((x[:,None]-mu[None,:])/sd[None,:])**2)/(sd[None,:]*np.sqrt(2*np.pi))
        B=np.maximum(B,1e-300)
        al=np.empty((T,2)); c=np.empty(T)
        al[0]=pi*B[0]; c[0]=al[0].sum(); al[0]/=max(c[0],1e-300)
        for t in range(1,T):
            al[t]=(al[t-1]@A)*B[t]; c[t]=al[t].sum(); al[t]/=max(c[t],1e-300)
        be=np.empty((T,2)); be[-1]=1.0
        for t in range(T-2,-1,-1):
            be[t]=A@(B[t+1]*be[t+1]); be[t]/=max(be[t].sum(),1e-300)
        g=al*be; g/=np.maximum(g.sum(axis=1,keepdims=True),1e-300)
        xi=np.zeros((2,2))
        for t in range(T-1):
            m=(al[t][:,None]*A)*(B[t+1]*be[t+1])[None,:]
            xi+=m/max(m.sum(),1e-300)
        A=xi/np.maximum(xi.sum(axis=1,keepdims=True),1e-300)
        pi=g[0]/max(g[0].sum(),1e-300)
        w=g.sum(axis=0)
        mu=(g*x[:,None]).sum(axis=0)/np.maximum(w,1e-300)
        tot=(g*(x[:,None]-mu[None,:])**2).sum(axis=0)/np.maximum(w,1e-300)
        nbind=int((tot<v).sum())
        s2=np.maximum(tot-v,0.0)
        ll=float(np.log(np.maximum(c,1e-300)).sum())
        if abs(ll-ll_old)<tol*max(abs(ll),1.0): ll_old=ll; break
        ll_old=ll
    order=np.argsort(mu)
    mu,s2=mu[order],s2[order]; A=A[np.ix_(order,order)]; pi=pi[order]; g=g[:,order]
    return dict(mu=mu,s2=s2,A=A,pi=pi,v=v,loglik=ll_old,n_bind=nbind),g

def build_cell(root,geom,hname,with_holdout):
    """Five-minute-equivalent log RV and log realized kernel, at the cell's OWN
    horizon on both sides. The wlen-aware holdout path, per the S16 correction."""
    M5=FIVEMIN[(geom,hname)]
    rw,kw,ds=cell_windows(root,geom,hname)
    rv=p1_rv(subbars(rw,M5)); pos=rv>0
    Mf=rw.shape[1]
    om2=float((rw**2).sum(axis=1).mean()/(2.0*Mf))
    Hk=kernel_H(Mf,om2,float(rv[pos].mean()))
    rk=np.maximum(p3_kernel_flattop(rw,Hk),1e-300)
    x=np.log(rv[pos]); r=np.log(rk[pos]); n_is=len(x)
    if with_holdout:
        z=np.load(os.path.join(S09,"cache",f"ho_panel_{root}_{geom}.npz"))
        rwh,kwh,HIw,LOw,OPw,CLw,live,nw=p6.wins(
            {k:z[k] for k in ["open","high","low","close"]},z["present"],
            z["tradeable"],"B0",geom,hname)
        rwh=rwh[live]
        rvh=p1_rv(subbars(rwh,M5)); posh=rvh>0
        rkh=np.maximum(p3_kernel_flattop(rwh,Hk),1e-300)
        x=np.concatenate([x,np.log(rvh[posh])])
        r=np.concatenate([r,np.log(rkh[posh])])
    return x,r,n_is,int(Hk)

def roll(v_series,noise_raw=None,start=None,record_params=False):
    """Rolling 441-window, one step at a time, z-scored within window.
    noise_raw is Var(eps) on the RAW scale; it is divided by the window variance
    so the floor is expressed on the z-scored scale the HMM actually sees."""
    T=len(v_series); st=np.full(T,-1,np.int8); pr=np.full(T,np.nan)
    par=[] if record_params else None
    init=None; nbind_tot=0; nwin_bind=0; nwin=0; nfail=0; nretry=0
    lo=WINDOW if start is None else max(WINDOW,start+1)
    if start is not None and start+1>WINDOW:
        w0=v_series[start+1-WINDOW:start+1]
        if np.isfinite(w0).all() and w0.std()>0:
            z0=(w0-w0.mean())/w0.std()
            init,_,_=safe_fit(z0,None,None if noise_raw is None
                              else noise_raw/max(w0.var(),1e-12))
    for e in range(lo,T+1):
        w=v_series[e-WINDOW:e]
        if not np.isfinite(w).all(): continue
        s=w.std()
        if s<=0: continue
        z=(w-w.mean())/s; nwin+=1
        vz=None if noise_raw is None else noise_raw/max(w.var(),1e-12)
        p,g,att=safe_fit(z,init,vz)
        if p is None:
            nfail+=1; init=None; continue
        if att==1: nretry+=1
        if vz is not None:
            nbind_tot+=p["n_bind"]; nwin_bind+=int(p["n_bind"]>0)
        init=p
        st[e-1]=int(g[-1,1]>0.5); pr[e-1]=float(g[-1,1])
        if record_params:
            sd=(p["sd"] if noise_raw is None else np.sqrt(p["s2"]+p["v"]))
            par.append((e-1,p["mu"][0],p["mu"][1],sd[0],sd[1],
                        float(abs(p["mu"][1]-p["mu"][0])/max(sd.mean(),1e-12)),
                        float(p["A"][0,1]),float(p["A"][1,0])))
    return st,pr,par,dict(n_windows=nwin,n_bind_total=nbind_tot,
                          n_windows_binding=nwin_bind,n_fit_failures=nfail,
                          n_cold_retries=nretry)

def metrics(st,ref,tag):
    ok=(st>=0)&(ref>=0); n=int(ok.sum())
    if n<10: return dict(sample=tag,n=n)
    a,b=st[ok],ref[ok]; dis=a!=b
    runs=[];cur=1
    for i in range(1,len(a)):
        if a[i]==a[i-1]: cur+=1
        else: runs.append(cur); cur=1
    runs.append(cur)
    return dict(sample=tag,n=n,misclass=float(dis.mean()),
        both_high=int(((a==1)&(b==1)).sum()),spurious_high=int(((a==1)&(b==0)).sum()),
        spurious_low=int(((a==0)&(b==1)).sum()),both_low=int(((a==0)&(b==0)).sum()),
        switches=int(np.abs(np.diff(a)).sum()),
        mean_regime_duration=float(np.mean(runs)),share_high=float(a.mean()))
