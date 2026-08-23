"""Figure 2. Analytic misclassification arccos(sqrt(lambda))/pi against lambda,
with the measured cells at their own lambda and empirical rate. READS ONLY
persisted artifacts; the only computation is the plotted curve."""
import os, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("pdf")
import matplotlib.pyplot as plt
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R=lambda p: os.path.join(ROOT,p)
SRC=dict(k8="artifacts/s14-applications/phase1_k8_rates.csv",
         lam="artifacts/s09-application/phase3_sizing_params.csv")
K=pd.read_csv(R(SRC["k8"])); L=pd.read_csv(R(SRC["lam"]))
ins=K[(K["sample"]=="insample")&(K.split=="median")]
prov=dict(rows_k8=len(K),rows_lambda=len(L),n_marked=len(ins))
fig,ax=plt.subplots(figsize=(4.4,3.0))
lam=np.linspace(0.30,0.999,400)
ax.plot(lam,np.arccos(np.sqrt(lam))/np.pi,"-",lw=1.4,color="0.15",
        label=r"$\arccos(\sqrt{\lambda})/\pi$")
ax.plot(ins.lam_intercept,ins.analytic_rate,"o",ms=5,mfc="none",mec="0.15",
        label="analytic, at measured $\\lambda$")
ax.plot(ins.lam_intercept,ins.empirical_rate,"s",ms=5,color="C3",
        label="empirical (shared-window)")
for _,r in ins.iterrows():
    ax.plot([r.lam_intercept]*2,[r.empirical_rate,r.analytic_rate],"-",lw=.7,color="0.6")
    ax.annotate(f"{r.root}/{r.geom}",(r.lam_intercept,r.analytic_rate),
                textcoords="offset points",xytext=(4,4),fontsize=6.5,color="0.3")
lo=float(ins.rate_gap_prop.abs().min())*100; hi=float(ins.rate_gap_prop.abs().max())*100
ax.annotate(f"empirical below analytic by\n{lo:.0f}-{hi:.0f}% (shared window)",
            xy=(0.62,0.055),fontsize=7,color="0.35")
ax.set_xlabel(r"reliability $\lambda$"); ax.set_ylabel("misclassification rate")
ax.set_ylim(0,0.32); ax.tick_params(labelsize=8); ax.legend(fontsize=7,frameon=False)
fig.tight_layout(); fig.savefig(R("figures/fig2.pdf"))
prov["sources"]=SRC
prov["gap_prop_range_pct"]=[lo,hi]
prov["computed"]="arccos(sqrt(lambda))/pi over a lambda grid; all plotted points read from artifacts"
json.dump(prov,open(R("figures/fig2_provenance.json"),"w"),indent=1)
print(json.dumps(prov,indent=1))
