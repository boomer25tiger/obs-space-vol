"""S09 Phase 7: K3 determination (item 71), plus the in-sample sizing baseline
that the in-sample-versus-holdout degradation is measured against.

The in-sample baseline runs the SAME sizing code on the pre-2024 panels with
the SAME frozen parameters. No parameter, threshold or rule is changed; this
adds a measurement, it does not alter a holdout number.
"""
import json, os, sys, time
import numpy as np, pandas as pd
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
S06=os.path.join(ROOT,"sessions","s06r-repair")
sys.path.insert(0,os.path.join(BASE,"src"))
sys.path.insert(0,os.path.join(ROOT,"sessions","s07-completion-and-spy","src"))
sys.path.insert(0,os.path.join(ROOT,"sessions","s05-reliability-mcs","src"))
from phase6_holdout import wins, feature_block, score, har_oos, FIVEMIN, TICKS, \
    TICKVAL, MULT, TARGET_D
from phase2_rerun8 import tradeable_ext
import partde as pd5
def main():
    t0=time.time()
    P3=pd.read_csv(os.path.join(RES,"phase3_sizing_params.csv"))
    rows=[]
    for geom in ["GLOBEX","RTH"]:
        for root in ["ES","NQ"]:
            z=np.load(os.path.join(S06,"cache",f"panel_ohlc_{root}_{geom}.npz"))
            trm,ds=tradeable_ext(root,geom)
            M5=FIVEMIN[(geom,"1day")]
            rw,kw,HIw,LOw,OPw,CLw,live,nw=wins(
                {k:z[k] for k in ["open","high","low","close"]},z["present"],trm,
                "B0",geom,"1day")
            f=feature_block(rw[live],kw[live],HIw[live],LOw[live],OPw[live],
                            CLw[live],M5,"1day")
            rv=f["rv"]; T=len(rv)
            warm=max(500,24)                      # same warm-up as the S07 1day path
            F=har_oos(rv,warm,1)                  # expanding window, evaluated after warm
            mu=float(np.log(rv[:warm][rv[:warm]>0]).mean())
            px=float(np.exp(z["close"].astype(np.float64)[live]).mean())
            qtr=pd.to_datetime(np.array(ds,dtype="U10")[live]).to_period("Q").astype(str).values
            sub=P3[(P3.root==root)&(P3.geom==geom)&(P3.btag=="B0")&(P3.horizon=="1day")]
            for rng_tag in ["restricted_S05","extended"]:
                rr=sub[sub.range==rng_tag]
                if not len(rr) or not bool(rr.iloc[0].valid): continue
                lt=float(rr.iloc[0].lam_theory); lm=float(rr.iloc[0].lam_intercept)
                for rule,lam in [("R1",None),("R2",lt),("R3",lm)]:
                    d,w=score(rv[warm:],F[warm:],lam,mu,TICKVAL[root],MULT[root],px,
                              qtr[warm:])
                    d.pop("_qtab")
                    rows.append(dict(root=root,geom=geom,range=rng_tag,rule=rule,
                        lam_used=(lam if lam is not None else np.nan),**d))
    IS=pd.DataFrame(rows); IS.to_csv(os.path.join(RES,"phase7_sizing_insample.csv"),index=False)
    HO=pd.read_csv(os.path.join(RES,"phase6_sizing_oos.csv"))
    m=IS.merge(HO,on=["root","geom","range","rule"],suffixes=("_is","_oos"))
    m["te_degradation"]=m.te_oos-m.te_is
    m["te_degradation_pct"]=100*(m.te_oos/m.te_is-1)
    m[["root","geom","range","rule","lam_used_is","te_is","te_oos","te_degradation",
       "te_degradation_pct","turnover_is","turnover_oos"]].to_csv(
        os.path.join(RES,"phase7_degradation.csv"),index=False)
    # ---------------- K3, item 71, on the holdout
    k=HO.pivot_table(index=["root","geom","range"],columns="rule",
        values=["te","turnover"]+[f"cost_{t}t_bps" for t in TICKS]).reset_index()
    k.columns=["_".join([c for c in col if c]) for col in k.columns]
    k["rel_te_diff_pct"]=100*(k.te_R2-k.te_R3).abs()/k.te_R2
    k["r3_better"]=k.te_R3<k.te_R2
    k["lam_R3_in_unit"]=HO.set_index(["root","geom","range"]).loc[
        list(zip(k.root,k.geom,k["range"]))].query("rule=='R3'").lam_used.values
    k["lam_R3_in_unit"]=(k["lam_R3_in_unit"]>0)&(k["lam_R3_in_unit"]<=1)
    for t in TICKS:
        k[f"rel_netcost_diff_pct_{t}t"]=100*(
            k[f"cost_{t}t_bps_R2"]-k[f"cost_{t}t_bps_R3"]).abs()/k[f"cost_{t}t_bps_R2"]
    k.to_csv(os.path.join(RES,"phase7_k3_inputs.csv"),index=False)
    det={}
    for rng_tag in ["restricted_S05","extended"]:
        s=k[k["range"]==rng_tag]
        sv=s[s.lam_R3_in_unit]
        det[rng_tag]=dict(
            n_cells=int(len(s)),n_cells_lambda_in_unit=int(len(sv)),
            max_rel_te_diff_pct=float(s.rel_te_diff_pct.max()),
            max_rel_te_diff_pct_valid_lambda=float(sv.rel_te_diff_pct.max()) if len(sv) else None,
            all_below_5pct=bool((s.rel_te_diff_pct<5.0).all()),
            all_below_5pct_valid_lambda=bool((sv.rel_te_diff_pct<5.0).all()) if len(sv) else None,
            cells_at_or_above_5pct=[f"{r}/{g}" for r,g,v in
                zip(s.root,s.geom,s.rel_te_diff_pct) if v>=5.0],
            K3=("FIRES" if bool((s.rel_te_diff_pct<5.0).all()) else "DOES NOT FIRE"))
    det["note_cost_sweep"]=("Tracking error does not depend on the cost assumption, so "
        "the relative R2-vs-R3 tracking-error difference is identical at all four sweep "
        "points; the sweep discriminates only the turnover charge, reported alongside.")
    json.dump(det,open(os.path.join(RES,"phase7_k3.json"),"w"),indent=1)
    print(k[["root","geom","range","te_R1","te_R2","te_R3","rel_te_diff_pct",
             "r3_better","lam_R3_in_unit"]].to_string(index=False))
    print(); print(json.dumps(det,indent=1))
    print(); print("in-sample vs holdout:")
    print(m[["root","geom","range","rule","te_is","te_oos","te_degradation_pct",
             "turnover_is","turnover_oos"]].to_string(index=False))
    print(f"PHASE7 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
