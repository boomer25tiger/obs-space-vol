"""S16 shared paths, constants and the 2-state Gaussian HMM.

The HMM is NEW code: hmmlearn is not in requirements.lock and the project holds
no prior HMM, so nothing is being reimplemented that could have been imported.
It is a standard Baum-Welch EM for a two-state Gaussian hidden Markov model,
warm-started from the previous rolling window's parameters, and it is validated
against a synthetic two-state series before use.
"""
import os, sys
import numpy as np, pandas as pd
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE,LOGS=(os.path.join(BASE,x) for x in ["results","cache","logs"])
S09=os.path.join(ROOT,"sessions","s09-application")
S10=os.path.join(ROOT,"sessions","s10-exponent-audit")
S11=os.path.join(ROOT,"sessions","s11-extensions")
for p in [os.path.join(S11,"src"),os.path.join(S10,"src"),os.path.join(S09,"src"),
          os.path.join(ROOT,"sessions","s07-completion-and-spy","src"),
          os.path.join(ROOT,"sessions","s05-reliability-mcs","src"),
          os.path.join(ROOT,"sessions","s02-mechanism-expansion","src"),
          os.path.join(ROOT,"sessions","s01-estimator-validation","src")]:
    sys.path.insert(0,p)
# item 116 specification, Blake, Gandhi and Jakkula, arXiv 2510.03236
WINDOW=441; N_STATES=2; MA_LEN=5
FIVEMIN={("RTH","1day"):78,("RTH","1h"):12,("RTH","30min"):6,("GLOBEX","1day"):276}
CELLS8=[("ES","GLOBEX","1day"),("NQ","GLOBEX","1day"),
        ("ES","RTH","1day"),("NQ","RTH","1day"),
        ("ES","RTH","1h"),("NQ","RTH","1h"),
        ("ES","RTH","30min"),("NQ","RTH","30min")]
CELLS4=[("ES","GLOBEX"),("NQ","GLOBEX"),("ES","RTH"),("NQ","RTH")]
TICKS=[0.5,1.0,2.0,4.0]; TICKVAL={"ES":12.50,"NQ":5.00}; MULT={"ES":50.0,"NQ":20.0}
NDAY=252; TARGET_D=0.10/np.sqrt(252)
ARMS=["A1_raw","A2_ma5","A3_shrunk"]

def gauss_hmm_fit(x,n_iter=60,tol=1e-6,init=None):
    """Baum-Welch EM for a two-state Gaussian HMM. Returns (params, gamma)."""
    T=len(x)
    if init is None:
        q=np.quantile(x,[0.25,0.75])
        mu=np.array([q[0],q[1]]); sd=np.array([x.std(),x.std()])*0.8+1e-6
        A=np.array([[0.95,0.05],[0.05,0.95]]); pi=np.array([0.5,0.5])
    else:
        mu,sd,A,pi=(init["mu"].copy(),init["sd"].copy(),
                    init["A"].copy(),init["pi"].copy())
    ll_old=-np.inf
    for _ in range(n_iter):
        B=np.exp(-0.5*((x[:,None]-mu[None,:])/sd[None,:])**2)/(sd[None,:]*np.sqrt(2*np.pi))
        B=np.maximum(B,1e-300)
        al=np.empty((T,2)); c=np.empty(T)
        al[0]=pi*B[0]; c[0]=al[0].sum(); al[0]/=c[0]
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
        sd=np.sqrt(np.maximum((g*(x[:,None]-mu[None,:])**2).sum(axis=0)
                              /np.maximum(w,1e-300),1e-12))
        ll=float(np.log(np.maximum(c,1e-300)).sum())
        if abs(ll-ll_old)<tol*max(abs(ll),1.0): ll_old=ll; break
        ll_old=ll
    order=np.argsort(mu)                      # state 0 = low volatility
    mu,sd=mu[order],sd[order]; A=A[np.ix_(order,order)]; pi=pi[order]
    g=g[:,order]
    return dict(mu=mu,sd=sd,A=A,pi=pi,loglik=ll_old),g
