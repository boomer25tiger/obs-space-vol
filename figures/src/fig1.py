"""Figure 1. Var(log RV_M) against M, log axes, with the fitted curve of
equation (3) and the trigamma reference. READS ONLY persisted artifacts; the
only computation is the plotted transformation c + A*M^b and trigamma(M/2)."""
import os, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("pdf")
import matplotlib.pyplot as plt
from scipy.special import polygamma
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R=lambda p: os.path.join(ROOT,p)
SRC=dict(
 futures_grid="sessions/s08-final/results/phase4_lambda.csv",
 fits="sessions/s10-exponent-audit/results/phase1_bootstrap.csv",
 screen="sessions/s10-exponent-audit/results/phase2_screen.csv",
 spy_arcx="sessions/s07-completion-and-spy/results/phase6_spy_grid_ARCX.csv",
 spy_xnas="sessions/s07-completion-and-spy/results/phase6_spy_grid_XNAS.csv")
G=pd.read_csv(R(SRC["futures_grid"])); F=pd.read_csv(R(SRC["fits"]))
S=pd.read_csv(R(SRC["screen"]))
keep=set(S[(S["range"]=="extended")&(S.screen_tight_pass)].cell)
prov=dict(rows_futures_grid=len(G),rows_fits=len(F),rows_screen=len(S),
          n_cells_passing_screen=len(keep))
fig,ax=plt.subplots(1,2,figsize=(7.2,3.1),sharey=False)
cols=plt.cm.viridis(np.linspace(0.05,0.9,len(keep)))
for i,cell in enumerate(sorted(keep)):
    root,geom,btag,hor=cell.split("/")
    g=G[(G.root==root)&(G.geom==geom)&(G.btag==btag)&(G.horizon==hor)].sort_values("M")
    f=F[F.cell==cell].iloc[0]
    ax[0].plot(g.M,g.var_log_rv,"o",ms=2.6,color=cols[i],alpha=.85)
    mm=np.logspace(np.log10(g.M.min()),np.log10(g.M.max()),200)
    ax[0].plot(mm,f.c+f.A*mm**f.b,"-",lw=.9,color=cols[i],alpha=.85)
for gname,Ms in [("RTH 1day",[5,6,10,13,26,78,195,389]),
                 ("GLOBEX 1day",[5,6,10,12,23,46,138,276,345,1379]),
                 ("RTH 1h",[4,5,6,10,12,15,20,30,60]),("RTH 30min",[5,6,10,15,30])]:
    mm=np.array(Ms,float)
    ax[0].plot(mm,polygamma(1,mm/2.0),"--",lw=1.0,color="0.35")
ax[0].set_xscale("log"); ax[0].set_yscale("log")
ax[0].set_xlabel("$M$ (sub-bars per window)")
ax[0].set_ylabel(r"$\mathrm{Var}(\log RV_M)$")
ax[0].set_title("Futures, twelve cells passing the screen",fontsize=9)
sp=[]
for ven,key in [("ARCX","spy_arcx"),("XNAS","spy_xnas")]:
    d=pd.read_csv(R(SRC[key])); sp.append(len(d))
    d=d[np.isfinite(d.var_log_rv_TICK)].sort_values("M_used")
    f=F[F.cell==f"SPY/{ven}/TICK"].iloc[0]
    ax[1].plot(d.M_used,d.var_log_rv_TICK,"o",ms=3.2,label=f"SPY {ven}")
    mm=np.logspace(np.log10(d.M_used.min()),np.log10(d.M_used.max()),200)
    ax[1].plot(mm,f.c+f.A*mm**f.b,"-",lw=1.0)
mm=np.logspace(np.log10(5),np.log10(23399),200)
ax[1].plot(mm,polygamma(1,mm/2.0),"--",lw=1.0,color="0.35",label="trigamma$(M/2)$")
ax[1].set_xscale("log"); ax[1].set_yscale("log")
ax[1].set_xlabel("$M$ (sub-bars per window)")
ax[1].set_title("SPY, traded-tick sampling",fontsize=9)
ax[1].legend(fontsize=7,frameon=False)
prov["rows_spy"]=sp
for a in ax: a.tick_params(labelsize=8)
fig.tight_layout(); fig.savefig(R("figures/fig1.pdf"))
prov["sources"]={k:v for k,v in SRC.items()}
prov["computed"]="c + A*M**b (equation 3, parameters read from the fits artifact) and trigamma(M/2); nothing else"
json.dump(prov,open(R("figures/fig1_provenance.json"),"w"),indent=1)
print(json.dumps(prov,indent=1))
