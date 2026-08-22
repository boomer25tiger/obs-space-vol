"""S07 Phase 1: SPY inventory, SHA-256 manifest, span and schema check."""
import hashlib, json, os, sys, time
import numpy as np, pandas as pd, databento as db
SPY="~/Downloads/DataBento Data/SPY 1s Data"
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES=os.path.join(BASE,"results")
VEN={"ARCX.PILLAR":("ARCX-20260815-XLE9K93W3H","arcx-pillar-20180501-20260813.ohlcv-1s.dbn.zst"),
     "XNAS.ITCH":("XNAS-20260815-SLCD8NA7UL","xnas-itch-20180501-20260813.ohlcv-1s.dbn.zst")}
def sha(p, buf=1<<22):
    h=hashlib.sha256()
    with open(p,"rb") as fh:
        while True:
            b=fh.read(buf)
            if not b: break
            h.update(b)
    return h.hexdigest()
def main():
    t0=time.time(); lines=[]; inv=[]
    lines.append("# S07 SPY manifest, SHA-256 of every file read")
    lines.append(f"# source: {SPY}")
    lines.append(f"# generated {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    for ven,(d,f) in VEN.items():
        for fn in ["metadata.json","manifest.json","condition.json",f]:
            p=os.path.join(SPY,d,fn)
            if os.path.exists(p):
                h=sha(p); sz=os.path.getsize(p)
                lines.append(f"{h}  {sz:>12}  {ven}/{fn}")
                inv.append(dict(venue=ven,file=fn,bytes=sz,sha256=h,
                                fmt=("DBN v3 zstd" if fn.endswith(".dbn.zst") else "JSON"),
                                consumed=True))
    # derived parquets present but NOT consumed (item 55)
    for fn in sorted(os.listdir(os.path.join(SPY,"data"))):
        p=os.path.join(SPY,"data",fn)
        inv.append(dict(venue="(derived)",file=f"data/{fn}",bytes=os.path.getsize(p),
                        sha256="", fmt="parquet/json", consumed=False))
    open(os.path.join(RES,"S07-spy-manifest.txt"),"w").write("\n".join(lines)+"\n")
    pd.DataFrame(inv).to_csv(os.path.join(RES,"phase1_spy_inventory.csv"),index=False)
    # ---- span, schema, session counts
    out={}
    for ven,(d,f) in VEN.items():
        store=db.DBNStore.from_file(os.path.join(SPY,d,f))
        m=store.metadata
        CUT=np.datetime64('2024-01-01T00:00:00').astype('datetime64[ns]').astype(np.int64)
        n_tot=0; n_pre=0; tmin=None; tmax=None; cols=None; sess=set()
        for arr in store.to_ndarray(count=4_000_000):
            if cols is None: cols=list(arr.dtype.names)
            ts=arr['ts_event'].astype(np.int64); n_tot+=len(arr)
            tmin=ts.min() if tmin is None else min(tmin,ts.min())
            tmax=ts.max() if tmax is None else max(tmax,ts.max())
            k=ts<CUT; n_pre+=int(k.sum())
            if k.any():
                ny=pd.DatetimeIndex(ts[k].astype('datetime64[ns]'),tz="UTC").tz_convert("America/New_York")
                mins=ny.hour*60+ny.minute
                rth=(mins>=570)&(mins<960)
                sess.update(np.unique(ny.date[rth]).tolist())
        out[ven]=dict(dataset=str(m.dataset), schema=str(m.schema),
            stype_in=str(m.stype_in), stype_out=str(m.stype_out),
            symbols=list(m.symbols), columns=cols, n_rows_total=int(n_tot),
            n_rows_pre_2024=int(n_pre),
            ts_min=str(np.datetime64(int(tmin),'ns')), ts_max=str(np.datetime64(int(tmax),'ns')),
            n_rth_sessions_pre2024=len(sess),
            spans_2018_05_01_to_2023_12_31=bool(
                np.datetime64(int(tmin),'ns')<=np.datetime64('2018-05-01T20:00:00') and
                np.datetime64(int(tmax),'ns')>=np.datetime64('2023-12-29T20:00:00')))
        print(ven, json.dumps({k:v for k,v in out[ven].items() if k!="columns"},indent=1), flush=True)
    json.dump(dict(venues=out, seconds=round(time.time()-t0,1)),
              open(os.path.join(RES,"phase1_spy_span.json"),"w"), indent=1)
    ok=all(v["spans_2018_05_01_to_2023_12_31"] for v in out.values())
    print("SPY SPAN OK:", ok, f"({time.time()-t0:.0f}s)")
if __name__=="__main__": main()
