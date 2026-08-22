"""S07 Phase 5: SPY panels from RAW DBN, RTH, pre-2024, venues separate.

Two panels per venue (item 56):
  CAL  calendar-time 23,400-second grid, forward filled, matching the futures
       construction.
  TICK traded-tick, holding only seconds with an actual bar, with its own
       index; sub-bars are equal-COUNT blocks of the traded sequence.
Derived parquets under data/ are NOT consumed (item 55).
"""
import json, os, sys, time
import numpy as np, pandas as pd, databento as db
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
sys.path.insert(0,os.path.join(ROOT,"sessions","s06r-repair","tests"))
from test_invariants import assert_range_inputs, assert_effective_M
SPY="~/Downloads/DataBento Data/SPY 1s Data"
VEN={"ARCX":("ARCX-20260815-XLE9K93W3H","arcx-pillar-20180501-20260813.ohlcv-1s.dbn.zst"),
     "XNAS":("XNAS-20260815-SLCD8NA7UL","xnas-itch-20180501-20260813.ohlcv-1s.dbn.zst")}
NSEC=23400; CUT=np.datetime64('2024-01-01T00:00:00').astype('datetime64[ns]').astype(np.int64)

def designated_early(d):
    """SCOPE section 3 early closes: day after Thanksgiving, Jul 3, Dec 24."""
    return ((d.month==11 and d.dayofweek==4 and 23<=d.day<=29) or
            (d.month==7 and d.day==3) or (d.month==12 and d.day==24))

def build(ven):
    d,f=VEN[ven]; t0=time.time()
    store=db.DBNStore.from_file(os.path.join(SPY,d,f))
    parts=[]
    for arr in store.to_ndarray(count=4_000_000):
        ts=arr['ts_event'].astype(np.int64)
        k=ts<CUT
        if not k.any(): continue
        a=arr[k]; ts=ts[k]
        ny=pd.DatetimeIndex(ts.astype('datetime64[ns]'),tz="UTC").tz_convert("America/New_York")
        sod=ny.hour*3600+ny.minute*60+ny.second
        rth=(sod>=34200)&(sod<57600)
        if not rth.any(): continue
        parts.append(pd.DataFrame(dict(
            date=np.array(ny.date)[rth].astype("datetime64[D]"),
            slot=(sod[rth]-34200).astype(np.int32),
            o=a['open'][rth].astype(np.int64), h=a['high'][rth].astype(np.int64),
            l=a['low'][rth].astype(np.int64), c=a['close'][rth].astype(np.int64),
            v=a['volume'][rth].astype(np.int64))))
    df=pd.concat(parts,ignore_index=True); del parts
    dts=pd.DatetimeIndex(np.sort(df.date.unique()))
    keep=~np.array([designated_early(x) for x in dts])
    n_early=int((~keep).sum()); dts=dts[keep]
    didx={d_:i for i,d_ in enumerate(dts)}
    df=df[df.date.isin(set(dts))]
    ri=df.date.map(didx).values.astype(np.int64); ci=df.slot.values
    S=len(dts)
    grids={}
    for col,nm in [("o","open"),("h","high"),("l","low"),("c","close")]:
        g=np.full((S,NSEC),np.nan,dtype=np.float32)
        g[ri,ci]=np.log(df[col].values/1e9).astype(np.float32)
        grids[nm]=g
    present=~np.isnan(grids["close"])
    close=pd.DataFrame(grids["close"]).ffill(axis=1).bfill(axis=1).values.astype(np.float32)
    for nm in ["open","high","low"]:
        grids[nm]=np.where(present,grids[nm],close).astype(np.float32)
    grids["close"]=close
    assert_range_inputs({k:v for k,v in grids.items()}, f"SPY/{ven}")
    np.savez_compressed(os.path.join(CACHE,f"spy_cal_{ven}.npz"),
        dates=dts.strftime("%Y-%m-%d").values.astype("U10"), present=present, **grids)
    # ---- traded-tick panel: per session, the sequence of traded closes
    order=np.lexsort((ci,ri))
    ri_s,ci_s=ri[order],ci[order]
    cl_s=np.log(df["c"].values[order]/1e9).astype(np.float32)
    counts=np.bincount(ri_s,minlength=S)
    np.savez_compressed(os.path.join(CACHE,f"spy_tick_{ven}.npz"),
        dates=dts.strftime("%Y-%m-%d").values.astype("U10"),
        row=ri_s.astype(np.int32), slot=ci_s.astype(np.int32), logpx=cl_s,
        counts=counts.astype(np.int32))
    # ---- diagnostics
    yrs=dts.year.values
    fill=present.mean(axis=1)
    r1=np.diff(close.astype(np.float64),axis=1)
    rv=(np.where(present[:,1:]&present[:,:-1],r1,0.0)**2).sum(axis=1)
    vol=np.sqrt(np.maximum(rv,0))
    offpenny=np.zeros(S)
    cl_int=df["c"].values
    op=pd.DataFrame(dict(r=ri,off=(cl_int%10_000_000!=0))).groupby("r")["off"].mean()
    offpenny[op.index.values]=op.values
    rows=[]
    for y in sorted(set(yrs.tolist())):
        m=yrs==y
        rows.append(dict(venue=ven,year=int(y),n_sessions=int(m.sum()),
            median_fill=float(np.median(fill[m])),mean_fill=float(fill[m].mean()),
            padded_share=float(1-fill[m].mean()),
            off_penny_close_share=float(offpenny[m].mean()),
            corr_fill_vol=float(np.corrcoef(fill[m],vol[m])[0,1]) if m.sum()>3 else np.nan))
    tod=pd.DataFrame(dict(slot=np.arange(NSEC),fill=present.mean(axis=0)))
    tod["half_hour"]=tod.slot//1800
    tod_agg=tod.groupby("half_hour")["fill"].mean().reset_index()
    tod_agg["ny_clock"]=[f"{9+(34200+h*1800)//3600-9:02d}:{((34200+h*1800)%3600)//60:02d}"
                          for h in tod_agg.half_hour]
    tod_agg["venue"]=ven
    # fill by year conditioned on volatility tercile
    cond=[]
    for y in sorted(set(yrs.tolist())):
        m=yrs==y; q=np.quantile(vol[m],[1/3,2/3]); t=np.searchsorted(q,vol[m])
        for k in [0,1,2]:
            s=t==k
            if s.sum(): cond.append(dict(venue=ven,year=int(y),vol_tercile=k+1,
                n=int(s.sum()),mean_fill=float(fill[m][s].mean())))
    return (dict(venue=ven,n_sessions=S,n_early_excluded=n_early,
                 n_rows=int(len(df)),seconds=round(time.time()-t0,1),
                 corr_fill_vol_pooled=float(np.corrcoef(fill,vol)[0,1]),
                 median_fill=float(np.median(fill)),mean_fill=float(fill.mean())),
            rows, tod_agg, cond)

def main():
    t0=time.time(); meta=[];yr=[];tods=[];conds=[]
    for ven in VEN:
        if os.path.exists(os.path.join(CACHE,f"spy_cal_{ven}.npz")):
            print("skip",ven,flush=True); continue
        m,rows,tod,cond=build(ven)
        meta.append(m); yr.extend(rows); tods.append(tod); conds.extend(cond)
        print(json.dumps(m),flush=True)
    if meta:
        pd.DataFrame(meta).to_csv(os.path.join(RES,"phase5_spy_meta.csv"),index=False)
        pd.DataFrame(yr).to_csv(os.path.join(RES,"phase5_spy_by_year.csv"),index=False)
        pd.concat(tods).to_csv(os.path.join(RES,"phase5_spy_fill_by_tod.csv"),index=False)
        pd.DataFrame(conds).to_csv(os.path.join(RES,"phase5_spy_fill_by_vol.csv"),index=False)
    print(f"SPY PANELS DONE {time.time()-t0:.0f}s",flush=True)
if __name__=="__main__": main()
