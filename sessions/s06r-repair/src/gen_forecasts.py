"""S06R generation pass: repaired series, forecasts, BPQ filter, RGARCH path.

Repairs applied here:
  - series built from the OHLC panel with the calendar exclusion (item 42)
  - M6_PARK / M6_GK from TRUE bar high and low (item 43)
  - RQ and every M-dependent quantity use the EFFECTIVE sub-bar count (item 45)
  - BPQ insanity filter on M3_HARJ and M4_HARQ (item 40), applied in every
    cell whether or not it fires
  - RGARCH parameter path recorded at every refit for the Phase 4 diagnosis;
    RGARCH is NOT filtered, respecified or constrained (item 41)
Model definitions (har_X, the RGARCH likelihood and its forecast) are
imported from S05 partde UNMODIFIED; only the inputs and the filter are new.
"""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy.signal import lfilter
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
RES, CACHE = os.path.join(BASE, "results"), os.path.join(BASE, "cache")
sys.path.insert(0, os.path.join(BASE, "tests"))
sys.path.insert(0, os.path.join(ROOT, "sessions", "s05-reliability-mcs", "src"))
from test_invariants import assert_forecasts_positive, InvariantViolation
import partde as pd5
MODELS = pd5.MODELS
HOR = {"1day": None, "1h": 60, "30min": 30}
CELLS = [(r, g, b, h) for g in ["GLOBEX", "RTH"] for r in ["ES", "NQ"]
         for b in ["B0", "B1"] for h in ["1day", "1h", "30min"]]
BOUNDARY = {"RTH": [570, 571, 959, 960], "GLOBEX": [570, 571, 959, 960, 1081]}
OFF = {"RTH": 570, "GLOBEX": 1080}

def series_from_panel(root, geom, btag, wlen):
    z = np.load(os.path.join(CACHE, f"panel_ohlc_{root}_{geom}.npz"))
    cl = z["close"].astype(np.float64); hi = z["high"].astype(np.float64)
    lo = z["low"].astype(np.float64);  op = z["open"].astype(np.float64)
    pres = z["present"]; ds = np.array(z["dates"], dtype="U10")
    tr = np.load(os.path.join(CACHE, f"tradeable_{root}_{geom}.npz"))["tradeable"]
    r1 = np.diff(cl, axis=1)
    keep = tr[:, 1:] & tr[:, :-1]
    have = pres[:, 1:] & pres[:, :-1]          # a return needs both endpoint bars
    if btag == "B1":                            # boundary minutes bridged
        for m in BOUNDARY[geom]:
            s = (m - OFF[geom]) % 1440 if geom == "GLOBEX" else m - OFF[geom]
            if 0 < s <= r1.shape[1]:
                r1[:, s - 1] = 0.0
    r1 = np.where(keep, r1, 0.0)
    S, L = r1.shape
    if wlen is None:
        nw, rw, kw, hw = 1, r1, keep, have
        HIw, LOw, OPw, CLw = hi, lo, op, cl
    else:
        nw = L // wlen
        rw = r1[:, :nw*wlen].reshape(-1, wlen)
        kw = keep[:, :nw*wlen].reshape(-1, wlen)
        hw = have[:, :nw*wlen].reshape(-1, wlen)
        HIw = hi[:, 1:1+nw*wlen].reshape(-1, wlen)
        LOw = lo[:, 1:1+nw*wlen].reshape(-1, wlen)
        OPw = op[:, 1:1+nw*wlen].reshape(-1, wlen)
        CLw = cl[:, 1:1+nw*wlen].reshape(-1, wlen)
    r2 = rw ** 2
    rv = r2.sum(axis=1)
    Meff = kw.sum(axis=1).astype(float)                    # effective sub-bars
    Mok = np.maximum(Meff, 3.0)
    a = np.abs(rw)
    bv = (np.pi/2.0) * (Mok/np.maximum(Mok-1.0,1.0)) * (a[:,1:]*a[:,:-1]).sum(axis=1)
    rq = (Mok/3.0) * (r2*r2).sum(axis=1)
    tradable_any = kw.any(axis=1)
    HIm = np.where(kw if wlen else np.ones_like(HIw, bool), HIw, -np.inf).max(axis=1)
    LOm = np.where(kw if wlen else np.ones_like(LOw, bool), LOw, np.inf).min(axis=1)
    rng_ok = np.isfinite(HIm) & np.isfinite(LOm)
    HIm = np.where(rng_ok, HIm, 0.0); LOm = np.where(rng_ok, LOm, 0.0)
    OPm = OPw[:, 0]; CLm = CLw[:, -1]
    park = (HIm - LOm) ** 2 / (4*np.log(2))
    gk = 0.5*(HIm-LOm)**2 - (2*np.log(2)-1)*(CLm-OPm)**2
    ret = rw.sum(axis=1)
    wdates = np.repeat(ds, nw)
    return dict(rv=rv, bv=bv, rq=rq, park=park, gk=np.maximum(gk, 1e-300),
                ret=ret, nw=nw, Meff=Meff, tradeable=tradable_any,
                wdates=wdates, have=hw.sum(axis=1).astype(float))

def bpq_filter(F, rv_insample_min, rv_insample_max, rv_insample_mean):
    """Bollerslev, Patton, Quaedvlieg insanity filter: a forecast outside the
    range of the in-sample realized variance is replaced by the in-sample mean."""
    bad = (F < rv_insample_min) | (F > rv_insample_max) | ~np.isfinite(F)
    out = np.where(bad, rv_insample_mean, F)
    return out, bad

def run_cell(job):
    root, geom, btag, hname = job
    t0 = time.time()
    cell = f"{root}/{geom}/{btag}/{hname}"
    S = series_from_panel(root, geom, btag, HOR[hname])
    D = S["nw"]; rv = S["rv"]
    warm = 500 if hname == "1day" else max(500, 22*D + 100)
    refit = 1 if hname == "1day" else D
    F, start, nonconv = pd5.forecasts(S, D, warm, refit, hname == "1day")
    # ---- RGARCH parameter path (Phase 4), recorded not altered
    logx = np.log(np.maximum(rv, 1e-300))
    th = np.array([0.1, 0.7, 0.25, -0.1, 1.0, -0.05, 0.05, np.log(0.4)])
    thetas = []
    for t in range(max(start, warm), len(rv), 63*D):
        th, _, ok = pd5.rgarch_fit_forecast(S["ret"][:t], logx[:t], th)
        thetas.append(dict(cell=cell, t=int(t), converged=bool(ok),
                           om=float(th[0]), beta=float(th[1]), gamma=float(th[2]),
                           xi=float(th[3]), phi=float(th[4]), tau1=float(th[5]),
                           tau2=float(th[6]), log_sigma_u=float(th[7]),
                           persistence=float(th[1] + th[2]*th[4])))
    # ---- evaluation sample: warm-up, tradeable, finite forecasts
    ok = np.ones(len(rv), bool)
    for m in MODELS: ok &= np.isfinite(F[m])
    ok[:max(start, warm)] = False
    ok &= S["tradeable"]
    rvv = rv[ok]
    ins = slice(0, max(start, warm))
    rmin, rmax, rmean = float(rv[ins].min()), float(rv[ins].max()), float(rv[ins].mean())
    filt_rows = []
    Ff = {}
    for m in MODELS:
        x = F[m][ok].copy()
        if m in ("M3_HARJ", "M4_HARQ"):
            xf, bad = bpq_filter(x, rmin, rmax, rmean)
            q_before = pd5.qlike(np.where(x > 0, x, np.nan), rvv)
            q_after = pd5.qlike(xf, rvv)
            alt, bad_alt = bpq_filter(x, 0.0, 100*rmean, rmean)
            filt_rows.append(dict(cell=cell, model=m, n_eval=int(ok.sum()),
                n_replaced=int(bad.sum()), share_replaced=float(bad.mean()),
                qlike_before=float(np.nanmean(q_before[np.isfinite(q_before)])),
                qlike_after=float(np.nanmean(q_after)),
                n_replaced_alt_100x=int(bad_alt.sum()),
                share_replaced_alt_100x=float(bad_alt.mean()),
                dates_replaced=";".join(sorted(set(
                    np.array(S["wdates"])[ok][bad].tolist()))[:40]),
                rv_min=rmin, rv_max=rmax, rv_mean=rmean))
            x = xf
        Ff[m] = x
        # Item 39: halts, never warns. The halt is captured per cell so the
        # remaining cells can still be attempted; the halted cell produces no
        # artifact and therefore reaches no MCS.
        assert_forecasts_positive(x, cell, m)
    L = np.column_stack([pd5.qlike(Ff[m], rvv) for m in MODELS])
    np.savez_compressed(os.path.join(CACHE, f"gen_{root}_{geom}_{btag}_{hname}.npz"),
        rv=rv, ok=ok, L=L, rvv=rvv, Meff=S["Meff"], wdates=S["wdates"],
        tradeable=S["tradeable"], D=D, start=start, warm=warm, nonconv=nonconv,
        **{f"F_{m}": Ff[m] for m in MODELS})
    return dict(cell=cell, n_windows=int(len(rv)), n_eval=int(ok.sum()),
                n_excluded_calendar=int((~S["tradeable"]).sum()),
                D=int(D), seconds=round(time.time()-t0, 1)), filt_rows, thetas

def main():
    from concurrent.futures import ProcessPoolExecutor, as_completed
    t0 = time.time(); meta, filt, thetas, halts = [], [], [], []
    todo = [c for c in CELLS if not os.path.exists(
        os.path.join(CACHE, f"gen_{c[0]}_{c[1]}_{c[2]}_{c[3]}.npz"))]
    print(f"generating {len(todo)} of {len(CELLS)} cells", flush=True)
    with ProcessPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(run_cell, c): c for c in todo}
        for f in as_completed(futs):
            try:
                m, fr, th = f.result()
            except InvariantViolation as e:
                cell = futs[f]
                halts.append(dict(cell="/".join(cell), phase="Phase 5 filter",
                                  assertion="assert_forecasts_positive",
                                  message=str(e)))
                print("INVARIANT HALT (cell skipped):", e, flush=True)
                continue
            meta.append(m); filt.extend(fr); thetas.extend(th)
            print(f"  {len(meta)}/{len(todo)} {m['cell']} ({m['seconds']}s)", flush=True)
    ho=os.path.join(RES,"phase5_halts.csv")
    prev=pd.read_csv(ho) if os.path.exists(ho) else pd.DataFrame()
    pd.concat([prev,pd.DataFrame(halts)]).to_csv(ho,index=False)
    gm=os.path.join(RES,"gen_meta.csv")
    prevm=pd.read_csv(gm) if os.path.exists(gm) else pd.DataFrame()
    pd.concat([prevm,pd.DataFrame(meta)]).to_csv(gm,index=False)
    fo=os.path.join(RES,"phase5_filter.csv")
    prevf=pd.read_csv(fo) if os.path.exists(fo) else pd.DataFrame()
    pd.concat([prevf,pd.DataFrame(filt)]).to_csv(fo,index=False)
    to=os.path.join(RES,"phase4_rgarch_params.csv")
    prevt=pd.read_csv(to) if os.path.exists(to) else pd.DataFrame()
    pd.concat([prevt,pd.DataFrame(thetas)]).to_csv(to,index=False)
    print(f"GEN DONE {time.time()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    main()
