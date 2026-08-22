"""S07 Phase 2 audit: filter impact across ALL cells, and the M3_HARJ case."""
import json, os, sys
import numpy as np, pandas as pd
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
S06=os.path.join(ROOT,"sessions","s06r-repair"); S06C=os.path.join(S06,"cache")
S05R=os.path.join(ROOT,"sessions","s05-reliability-mcs","results")
sys.path.insert(0,os.path.join(ROOT,"sessions","s05-reliability-mcs","src"))
import partde as pd5
MODELS=pd5.MODELS
CELLS=[(r,g,b,h) for g in ["GLOBEX","RTH"] for r in ["ES","NQ"]
       for b in ["B0","B1"] for h in ["1day","1h","30min"]]
rows=[]
for c in CELLS:
    p=os.path.join(CACHE,f"gen_{c[0]}_{c[1]}_{c[2]}_{c[3]}.npz")
    src="S07"
    if not os.path.exists(p):
        p=os.path.join(S06C,f"gen_{c[0]}_{c[1]}_{c[2]}_{c[3]}.npz"); src="S06R"
    if not os.path.exists(p): continue
    z=np.load(p); rv=z["rv"]; rvv=z["rvv"]; warm=int(z["warm"]); start=int(z["start"])
    ins=rv[:max(start,warm)]; rmean=float(ins.mean())
    for m in ["M3_HARJ","M4_HARQ"]:
        if f"F_{m}" not in z.files: continue
        F=z[f"F_{m}"]; ql=pd5.qlike(F,rvv)
        mask=(F==rmean)
        tot=float(ql.sum()) if np.isfinite(ql).all() else float(np.nansum(ql[np.isfinite(ql)]))
        rep_share=float(ql[mask].sum()/tot) if tot>0 and mask.any() else 0.0
        w5=float(np.sort(ql[np.isfinite(ql)])[-5:].sum()/tot) if tot>0 else np.nan
        rows.append(dict(cell="/".join(c),source=src,model=m,n_eval=int(len(F)),
            n_replaced=int(mask.sum()),share_replaced=float(mask.mean()),
            mean_qlike=float(np.nanmean(ql)),
            share_qlike_from_replaced=rep_share,share_qlike_worst5=w5,
            flag_replaced_over_quarter=bool(rep_share>0.25)))
A=pd.DataFrame(rows); A.to_csv(os.path.join(RES,"phase2_filter_audit_all_cells.csv"),index=False)
print(A.to_string(index=False))
print("\nFLAGGED (>25% of QLIKE from replaced obs):", int(A.flag_replaced_over_quarter.sum()))
# ---- the M3_HARJ ES/GLOBEX/B0/1day case
c=("ES","GLOBEX","B0","1day")
p=os.path.join(CACHE,f"gen_{'_'.join(c)}.npz")
if not os.path.exists(p): p=os.path.join(S06C,f"gen_{'_'.join(c)}.npz")
z=np.load(p); rv=z["rv"]; rvv=z["rvv"]; warm=int(z["warm"]); start=int(z["start"])
ins=rv[:max(start,warm)]; pos=ins[ins>0]
rmin_old, rmin_new, rmax, rmean = float(ins.min()), float(pos.min()), float(ins.max()), float(ins.mean())
case={}
for m in ["M3_HARJ","M4_HARQ","M2_HAR","M1_EWMA","M5_RGARCH"]:
    F=z[f"F_{m}"]; ql=pd5.qlike(F,rvv)
    case[m]=dict(mean_qlike=float(np.nanmean(ql)),
                 ic=float(np.corrcoef(np.log(F),np.log(rvv))[0,1]),
                 n_at_replacement_value=int((F==rmean).sum()),
                 n_above_rmax=int((F>rmax).sum()), max_forecast=float(F.max()))
old=pd.read_csv(os.path.join(S05R,"s05_metrics.csv"))
o=old[(old.root=="ES")&(old.geom=="GLOBEX")&(old.btag=="B0")&(old.horizon=="1day")&(old.scheme=="S-A")]
case["_s05"]={r.model:dict(qlike=float(r.qlike_mean),ic=float(r.ic_pearson_log)) for _,r in o.iterrows()}
case["_bounds"]=dict(rv_in_sample_min_including_zero=rmin_old,
                     rv_in_sample_min_strictly_positive=rmin_new,
                     rv_in_sample_max=rmax,rv_in_sample_mean=rmean)
json.dump(case,open(os.path.join(RES,"phase2_m3harj_case.json"),"w"),indent=1)
print("\nM3_HARJ case:", json.dumps({k:v for k,v in case.items() if k in ("M3_HARJ","M4_HARQ","M2_HAR","_bounds")},indent=1))
