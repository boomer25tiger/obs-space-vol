"""S11 Phase 1: floor-defect correction, S09 Phase 5 partition recomputed,
and the item-88 holdout re-evaluation of the touched candidates only."""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common11 import (BASE,RES,CACHE,ROOT,S06,S07,S09,CELLS,FIVEMIN,HOR,THRESH,
                      CANDS,DEFECT_TOUCHED,KEYMAP,logdrop,r2_ic)
import phase5_signals as p5          # build() imported unmodified
import phase6_holdout as p6          # wins(), feature_block() imported unmodified
from phase2_rerun8 import tradeable_ext

def features(d,other_rv,volmap,wd,hname):
    """Assemble the nine predictors as RAW values. The three transforms that
    are not a plain log (volume surprise, cross lead-lag, signature slope) keep
    the S09 construction; only the log step changes, in the caller."""
    raw={k:d[v][:-1] for k,v in KEYMAP.items()}
    lv=np.log(np.maximum(pd.Series(wd).map(volmap).astype(float).values,1.0))
    vs=np.nan_to_num(lv-pd.Series(lv).rolling(22,min_periods=5).mean().values,nan=0.0)
    m=min(len(other_rv)-1,len(raw["RS_up"]))
    cl=np.full(len(raw["RS_up"]),np.nan); cl[:m]=other_rv[:m]
    return raw,vs,cl,d["slope"][:-1]

def evaluate(d,other_rv,volmap,wd,hname,rows,tag,cellinfo):
    rv=d["rv"]
    y,n_y_dropped=logdrop(rv[1:])                # target: dropped where undefined
    raw,vs,cl,slope=features(d,other_rv,volmap,wd,hname)
    for c in CANDS:
        if c in KEYMAP:
            x,ndrop=logdrop(raw[c])
        elif c=="VolumeSurprise": x,ndrop=vs,0
        elif c=="SignatureSlope": x,ndrop=slope,0
        else:                                     # CrossLeadLag: the other root's log RV
            x,ndrop=logdrop(cl)
        ic,r2,n=r2_ic(x,y)
        rows.append(dict(**cellinfo,sample=tag,candidate=c,n=n,
            n_dropped_predictor=int(ndrop),
            share_dropped=float(ndrop/max(len(y),1)),
            n_dropped_target=int(n_y_dropped),ic=ic,r2=r2))

def main():
    t0=time.time(); timers={}
    P3=pd.read_csv(os.path.join(S09,"results","phase3_sizing_params.csv"))
    S09P5=pd.read_csv(os.path.join(S09,"results","phase5_signals.csv"))
    rows=[]
    # ---------------- in sample, pre-2024
    t=time.time()
    CROSS={}
    for geom in ["GLOBEX","RTH"]:
        for root in ["ES","NQ"]:
            for h in (["1day"] if geom=="GLOBEX" else ["1day","1h","30min"]):
                CROSS[(root,geom,h)]=p5.build(root,geom,"B0",h)
    VOL={}
    for geom in ["GLOBEX","RTH"]:
        for root in ["ES","NQ"]:
            VOL[(root,geom)]=p5.volume_series(root,geom)
    for root,geom,btag,hname in CELLS:
        other="NQ" if root=="ES" else "ES"
        d=p5.build(root,geom,btag,hname)
        wd=pd.to_datetime(d["wdates"][:-1])
        evaluate(d,CROSS[(other,geom,hname)]["rv"],VOL[(root,geom)],wd,hname,rows,
                 "insample",dict(root=root,geom=geom,btag=btag,horizon=hname))
    timers["insample"]=round(time.time()-t,1)
    # ---------------- holdout, item 88: only the candidates the defect touched
    t=time.time()
    HVOL={}
    for geom in ["GLOBEX","RTH"]:
        dd=pd.read_parquet(os.path.join(S09,"cache",f"ho_bars_{geom}.parquet"),
                           columns=["root","tdate","volume"])
        for root in ["ES","NQ"]:
            HVOL[(root,geom)]=dd[dd.root==root].groupby("tdate")["volume"].sum()
    HP={}
    for geom in ["GLOBEX","RTH"]:
        for root in ["ES","NQ"]:
            z=np.load(os.path.join(S09,"cache",f"ho_panel_{root}_{geom}.npz"))
            HP[(root,geom)]=z
    HCROSS={}
    for geom in ["GLOBEX","RTH"]:
        for root in ["ES","NQ"]:
            for h in (["1day"] if geom=="GLOBEX" else ["1day","1h","30min"]):
                z=HP[(root,geom)]
                rw,kw,HIw,LOw,OPw,CLw,live,nw=p6.wins(
                    {k:z[k] for k in ["open","high","low","close"]},z["present"],
                    z["tradeable"],"B0",geom,h)
                HCROSS[(root,geom,h)]=p6.feature_block(
                    rw[live],kw[live],HIw[live],LOw[live],OPw[live],CLw[live],
                    FIVEMIN[(geom,h)],h)
    hrows=[]
    for root,geom,btag,hname in CELLS:
        other="NQ" if root=="ES" else "ES"
        z=HP[(root,geom)]
        rw,kw,HIw,LOw,OPw,CLw,live,nw=p6.wins(
            {k:z[k] for k in ["open","high","low","close"]},z["present"],
            z["tradeable"],btag,geom,hname)
        d=p6.feature_block(rw[live],kw[live],HIw[live],LOw[live],OPw[live],CLw[live],
                           FIVEMIN[(geom,hname)],hname)
        ds=np.array(z["dates"],dtype="U10")
        wd=pd.to_datetime(np.repeat(ds,nw)[live][:-1])
        y,_=logdrop(d["rv"][1:])
        for c in DEFECT_TOUCHED:                  # item 88: touched candidates only
            x,ndrop=logdrop(d[KEYMAP[c]][:-1])
            ic,r2,n=r2_ic(x,y)
            hrows.append(dict(root=root,geom=geom,btag=btag,horizon=hname,
                candidate=c,n_oos=n,n_dropped_predictor=int(ndrop),
                share_dropped=float(ndrop/max(len(y),1)),ic_oos=ic,r2_oos=r2))
    timers["holdout"]=round(time.time()-t,1)
    IS=pd.DataFrame(rows); IS.to_csv(os.path.join(RES,"phase1_insample.csv"),index=False)
    HO=pd.DataFrame(hrows); HO.to_csv(os.path.join(RES,"phase1_holdout.csv"),index=False)
    # ---------------- partition, corrected, extended range only (the usable one)
    L=P3[P3.range=="extended"][["root","geom","btag","horizon","lam_intercept",
                                "lam_theory","valid"]]
    M=IS[IS["sample"]=="insample"].merge(L,on=["root","geom","btag","horizon"],how="left")
    M=M[M.valid==True].copy()
    M["r2_corr_measured"]=M.r2/M.lam_intercept
    M["keep_raw"]=M.r2>=THRESH
    M["keep_measured"]=M.r2_corr_measured>=THRESH
    M["band_lo"]=THRESH*M.lam_intercept; M["band_hi"]=THRESH
    M["in_flip_band"]=(M.r2>=M.band_lo)&(M.r2<THRESH)
    M.to_csv(os.path.join(RES,"phase1_partition_rows.csv"),index=False)
    part=dict(n=len(M),
        clears_under_both=int((M.keep_raw&M.keep_measured).sum()),
        clears_only_after_measured=int(((~M.keep_raw)&M.keep_measured).sum()),
        clears_neither=int(((~M.keep_raw)&(~M.keep_measured)).sum()),
        clears_raw_but_not_measured=int((M.keep_raw&(~M.keep_measured)).sum()),
        in_flip_band=int(M.in_flip_band.sum()))
    old=S09P5[S09P5.range=="extended"]
    part_s09=dict(n=len(old),
        clears_under_both=int((old.keep_raw&old.keep_measured).sum()),
        clears_only_after_measured=int(((~old.keep_raw)&old.keep_measured).sum()),
        clears_neither=int(((~old.keep_raw)&(~old.keep_measured)).sum()),
        clears_raw_but_not_measured=int((old.keep_raw&(~old.keep_measured)).sum()),
        in_flip_band=int(old.in_flip_band.sum()))
    cmp=M.merge(old[["root","geom","btag","horizon","candidate","r2_raw",
                     "keep_raw","keep_measured"]],
                on=["root","geom","btag","horizon","candidate"],
                suffixes=("_s11","_s09"))
    cmp["status_changed"]=(cmp.keep_raw_s11!=cmp.keep_raw_s09)|\
                          (cmp.keep_measured_s11!=cmp.keep_measured_s09)
    cmp.to_csv(os.path.join(RES,"phase1_vs_s09.csv"),index=False)
    ch=cmp[cmp.status_changed]
    # ---- flip band per cell
    fb=M.groupby(["root","geom","btag","horizon"]).agg(
        lam=("lam_intercept","first"),band_lo=("band_lo","first"),
        band_hi=("band_hi","first"),n_in_band=("in_flip_band","sum")).reset_index()
    fb["band_width"]=fb.band_hi-fb.band_lo
    fb.to_csv(os.path.join(RES,"phase1_flip_band.csv"),index=False)
    # ---- holdout comparison against S09
    s09h=pd.read_csv(os.path.join(S09,"results","phase6_candidates_oos.csv"))
    s09h=s09h[(s09h.range=="extended")&(s09h.candidate.isin(DEFECT_TOUCHED))]
    hc=HO.merge(s09h[["root","geom","btag","horizon","candidate","r2_oos","r2_is"]],
                on=["root","geom","btag","horizon","candidate"],
                suffixes=("_s11","_s09"))
    hc=hc.merge(M[["root","geom","btag","horizon","candidate","r2"]].rename(
        columns={"r2":"r2_is_s11"}),on=["root","geom","btag","horizon","candidate"])
    hc.to_csv(os.path.join(RES,"phase1_holdout_vs_s09.csv"),index=False)
    o=dict(partition_s11=part,partition_s09=part_s09,
        n_status_changed=int(ch.shape[0]),
        changed_cells=[f"{r}/{g}/{b}/{h} {c}" for r,g,b,h,c in
                       zip(ch.root,ch.geom,ch.btag,ch.horizon,ch.candidate)],
        n_dropped_total=int(IS.n_dropped_predictor.sum()),
        drop_rule_references_target=False,
        drop_rule_statement=("logdrop() reads only the predictor vector; the target "
            "is dropped separately and identically for all nine candidates where "
            "log RV_{t+1} is undefined, which is a missing-target drop, not "
            "selection on the target's value."),
        timers=timers)
    json.dump(o,open(os.path.join(RES,"phase1_summary.json"),"w"),indent=1)
    print("=== drop counts by candidate (in sample) ===")
    print(IS.groupby("candidate").agg(cells=("n","size"),
        cells_with_drops=("n_dropped_predictor",lambda s:(s>0).sum()),
        total_dropped=("n_dropped_predictor","sum"),
        max_share=("share_dropped","max")).to_string())
    print(); print("S09 partition:",json.dumps(part_s09))
    print("S11 partition:",json.dumps(part))
    print(f"\nstatus changed: {len(ch)} of {len(cmp)}")
    if len(ch): print(ch[["root","geom","btag","horizon","candidate","r2_raw","r2","keep_raw_s09","keep_raw_s11","keep_measured_s09","keep_measured_s11"]].to_string(index=False))
    print("\n=== holdout, touched candidates ===")
    print(hc[["root","geom","btag","horizon","candidate","r2_is","r2_is_s11",
              "r2_oos_s09","r2_oos_s11","n_dropped_predictor"]].to_string(index=False))
    print(f"PHASE1 DONE {time.time()-t0:.0f}s")
if __name__=="__main__": main()
