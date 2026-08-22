"""S06R Phase 4 support: record the RGARCH parameter path per available cell."""
import os, sys, time
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=os.path.dirname(os.path.dirname(BASE))
RES,CACHE=os.path.join(BASE,"results"),os.path.join(BASE,"cache")
sys.path.insert(0,os.path.join(ROOT,"sessions","s05-reliability-mcs","src"))
import partde as pd5

def one(f):
    cell=f[4:-4].replace("_","/",3)
    parts=f[4:-4].split("_"); cell="/".join(parts)
    z=np.load(os.path.join(CACHE,f))
    rv=z["rv"]; D=int(z["D"]); warm=int(z["warm"]); start=int(z["start"])
    # window returns are needed for the RGARCH likelihood; recover from L-free store
    ret=z["F_M1_EWMA"]*0.0  # placeholder replaced below
    logx=np.log(np.maximum(rv,1e-300))
    # reconstruct window returns from the panel the same way gen did
    root,geom,btag,hname=parts
    zz=np.load(os.path.join(CACHE,f"panel_ohlc_{root}_{geom}.npz"))
    cl=zz["close"].astype(np.float64)
    tr=np.load(os.path.join(CACHE,f"tradeable_{root}_{geom}.npz"))["tradeable"]
    r1=np.where(tr[:,1:]&tr[:,:-1], np.diff(cl,axis=1), 0.0)
    wl={"1day":None,"1h":60,"30min":30}[hname]
    if wl is None: ret=r1.sum(axis=1)
    else:
        nw=r1.shape[1]//wl; ret=r1[:,:nw*wl].reshape(-1,wl).sum(axis=1)
    ret=ret[:len(rv)]
    th=np.array([0.1,0.7,0.25,-0.1,1.0,-0.05,0.05,np.log(0.4)])
    rows=[]
    for t in range(max(start,warm), len(rv), 63*D):
        th,_,ok=pd5.rgarch_fit_forecast(ret[:t], logx[:t], th)
        rows.append(dict(cell=cell,t=int(t),converged=bool(ok),om=float(th[0]),
            beta=float(th[1]),gamma=float(th[2]),xi=float(th[3]),phi=float(th[4]),
            tau1=float(th[5]),tau2=float(th[6]),log_sigma_u=float(th[7]),
            persistence=float(th[1]+th[2]*th[4])))
    return rows

if __name__=="__main__":
    t0=time.time()
    files=sorted(f for f in os.listdir(CACHE) if f.startswith("gen_"))
    out=[]
    with ProcessPoolExecutor(max_workers=6) as ex:
        futs={ex.submit(one,f):f for f in files}
        for fu in as_completed(futs):
            out.extend(fu.result()); print(f"  {futs[fu]} done", flush=True)
    pd.DataFrame(out).to_csv(os.path.join(RES,"phase4_rgarch_params.csv"),index=False)
    print(f"theta rows {len(out)} in {time.time()-t0:.0f}s")
