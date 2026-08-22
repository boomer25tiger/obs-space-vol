"""Build S02-report.md from S02-cells.csv (+ missing-groups json)."""

import csv
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dgp2 import GEOMETRIES, JS_SWEEP, LATENTS, NSR_SWEEP, W_CONFIGS
from run2 import ARM_NAMES, BASE, PROXIES

RES_DIR = os.path.join(BASE, "results")
LOG_DIR = os.path.join(BASE, "logs")
DGPS = ["D1", "D2", "D3", "D4"]
DGP_SHAPES = {d: sorted({sh for (dd, _, sh) in LATENTS if dd == d})
              for d in DGPS}
W_LABELS = [f"{w}_r{ptt:g}" for (w, ptt) in W_CONFIGS]
NSRS = sorted(set(NSR_SWEEP))


def load_rows():
    rows = []
    path = os.path.join(RES_DIR, "S02-cells.csv")
    with open(path) as fh:
        for r in csv.DictReader(fh):
            for k in ["shape", "ptt", "js", "nsr", "point", "lo", "hi",
                      "seed_sd", "nan_frac"]:
                r[k] = float(r[k]) if r[k] not in ("", "nan") else np.nan
            r["n"] = int(r["n"]); r["M"] = int(r["M"])
            for k in ["pass10", "pass15", "pass25"]:
                r[k] = r[k] == "True"
            rows.append(r)
    return rows


def fmt_nsr(x):
    if x == 0:
        return "0"
    e = np.log10(x)
    return f"1e{e:.1f}".replace("e-", "e-").replace(".0", "")


def build_threshold_map(rows):
    """(arm, dgp, wlabel, js, n, M) -> dict(threshold, never, nonmono,
    incomplete)."""
    # index: pass15 by (arm, dgp, shape, wlabel, js, n, M, nsr)
    idx = defaultdict(dict)
    for r in rows:
        wl = f"{r['w']}_r{r['ptt']:g}"
        idx[(r["arm"], r["dgp"], r["wlabel"] if "wlabel" in r else wl,
             r["js"], r["n"], r["M"])].setdefault(r["nsr"], []).append(
            r["pass15"])
    out = {}
    for key, by_nsr in idx.items():
        n_shapes = len(DGP_SHAPES[key[1]])
        passes, present = [], []
        for nsr in NSRS:
            vals = by_nsr.get(nsr)
            if vals is None or len(vals) < n_shapes:
                present.append(False)
                passes.append(False)
            else:
                present.append(True)
                passes.append(all(vals))
        complete = all(present)
        passing = [NSRS[i] for i in range(len(NSRS)) if passes[i]]
        thr = max(passing) if passing else None
        nonmono = False
        if passing:
            below = [NSRS[i] for i in range(len(NSRS))
                     if NSRS[i] <= thr and present[i]]
            nonmono = any(n not in passing for n in below)
        out[key] = dict(threshold=thr, never=(not passing and complete),
                        nonmono=nonmono, complete=complete)
    return out


def main():
    rows = load_rows()
    for r in rows:
        r["wlabel"] = f"{r['w']}_r{r['ptt']:g}"
    with open(os.path.join(RES_DIR, "S02-missing.json")) as fh:
        missing = json.load(fh)
    with open(os.path.join(LOG_DIR, "unit-tests-s02.txt")) as fh:
        unit_out = fh.read().rstrip()

    tmap = build_threshold_map(rows)

    L = []
    L.append("# Session 2 report, mechanism expansion and breakdown "
             "mapping\n")
    L.append("Run date 2026-08-18. Synthetic only. Pre-registration: "
             "`../PREREG.md` (frozen before any simulation). Decisions: "
             "`../../../DECISIONS.md` items 7-10.\n")

    L.append("## Unit test output, in full\n")
    L.append("```text\n" + unit_out + "\n```\n")

    # ------------------------------------------------ threshold map
    L.append("## 1. Threshold map (primary output)\n")
    L.append(
        "Largest noise-to-signal ratio at which the +/-15% band is met "
        "(point inside the band AND 95% bootstrap CI excluding both "
        "edges, every latent shape of the DGP passing). Entries: an NSR "
        "value; `0` = passes only with no noise; `never` = no swept NSR "
        "passes, including 0; `~` after a value = non-monotone pass "
        "pattern below the threshold; `INC` = block not fully run (see "
        "section 5). Rows here are the zero-jump surface (C0+C2); the "
        "jump-crossed surfaces (C1/C3) appear in the same map keyed by "
        "js > 0 where run.\n")
    for js in JS_SWEEP:
        sub_keys = [k for k in tmap if k[3] == js]
        if not sub_keys:
            continue
        complete_any = any(tmap[k]["complete"] or tmap[k]["threshold"]
                           is not None for k in sub_keys)
        if not complete_any:
            continue
        L.append(f"### Jump share js = {js:g}\n")
        for arm in ARM_NAMES:
            keys = [k for k in sub_keys if k[0] == arm]
            if not keys:
                continue
            any_data = [k for k in keys if tmap[k]["complete"]
                        or tmap[k]["threshold"] is not None]
            if not any_data:
                continue
            L.append(f"#### {arm}\n")
            cols = [(n, M) for n in GEOMETRIES for M in GEOMETRIES[n]]
            L.append("| DGP | W | " + " | ".join(f"n{n} M{M}"
                                                 for n, M in cols) + " |")
            L.append("|---" * (len(cols) + 2) + "|")
            for dgp in DGPS:
                for wl in W_LABELS:
                    cells = []
                    for n, M in cols:
                        e = tmap.get((arm, dgp, wl, js, n, M))
                        if e is None or not (e["complete"]
                                             or e["threshold"] is not None):
                            cells.append("INC")
                        elif e["never"]:
                            cells.append("never")
                        elif e["threshold"] is None:
                            cells.append("INC")
                        else:
                            s = fmt_nsr(e["threshold"])
                            if e["nonmono"]:
                                s += "~"
                            if not e["complete"]:
                                s += "?"
                            cells.append(s)
                    L.append(f"| {dgp} | {wl} | " + " | ".join(cells) + " |")
            L.append("")

    # ------------------------------------------------ E2 W section
    L.append("## 3. E2 under W0 vs W1 and W2\n")
    L.append(
        "Recovery of E2 (contiguous halves) on P1 at zero contamination "
        "(js = 0, NSR = 0), by DGP and within-window structure. The "
        "question fixed in DECISIONS item 9: does E2's S01 pass survive "
        "within-window variation?\n")
    L.append("| DGP | shape | W | point | CI | pass15 |")
    L.append("|---|---|---|---|---|---|")
    e2rows = [r for r in rows if r["arm"] == "E2_P1" and r["js"] == 0
              and r["nsr"] == 0]
    verdicts = defaultdict(list)
    for r in sorted(e2rows, key=lambda r: (r["dgp"], r["shape"],
                                           r["wlabel"], r["n"], r["M"])):
        L.append(f"| {r['dgp']} | {r['shape']:g} | {r['wlabel']} | "
                 f"{r['point']:.3f} | [{r['lo']:.3f}, {r['hi']:.3f}] | "
                 f"{r['pass15']} |")
        verdicts[r["wlabel"].split("_")[0]].append(r["pass15"])
    L.append("")
    for wkey in ["W0", "W1", "W2"]:
        v = verdicts.get(wkey)
        if v:
            L.append(f"- {wkey}: {sum(v)}/{len(v)} cells pass the primary "
                     "band.")
    if verdicts.get("W0") and verdicts.get("W2"):
        s = ("survives" if all(verdicts["W2"]) else
             "does NOT survive" if not any(verdicts["W2"]) else
             "partially survives")
        L.append(f"\nDirect statement: E2's S01 performance {s} "
                 "within-window volatility variation (W2), and "
                 f"{'survives' if all(verdicts.get('W1', [])) else 'partially survives' if any(verdicts.get('W1', [])) else 'does NOT survive'} "
                 "a deterministic diurnal profile alone (W1).\n")

    # ------------------------------------------------ proxy dominance
    L.append("## 4. Dominant proxy by NSR decade\n")
    L.append(
        "Per estimator family and NSR (js = 0 surface): the proxy whose "
        "median |recovery - 1| across (DGP, shape, W, geometry, M) cells "
        "is smallest. Median absolute deviation in parentheses. E5/E6 "
        "are P1-only by definition and excluded.\n")
    fams = {"E1_a_L1-5": lambda a: a.startswith("E1_a_exp_L1-5"),
            "E1_a_L1-10": lambda a: a.startswith("E1_a_exp_L1-10"),
            "E1_d_L1-5": lambda a: a.startswith("E1_d_model_L1-5"),
            "E1_d_L1-10": lambda a: a.startswith("E1_d_model_L1-10"),
            "E2": lambda a: a.startswith("E2_P"),
            "E4": lambda a: a.startswith("E4_P")}
    L.append("| estimator | " + " | ".join(fmt_nsr(x) for x in NSRS) + " |")
    L.append("|---" * (len(NSRS) + 1) + "|")
    for fam, match in fams.items():
        cells = []
        for nsr in NSRS:
            best, bestv = None, None
            for p in PROXIES:
                sel = [abs(r["point"] - 1) for r in rows
                       if r["js"] == 0 and r["nsr"] == nsr
                       and match(r["arm"]) and r["arm"].endswith(p)
                       and np.isfinite(r["point"])]
                if not sel:
                    continue
                v = float(np.median(sel))
                if bestv is None or v < bestv:
                    best, bestv = p, v
            cells.append(f"{best} ({bestv:.2f})" if best else "INC")
        L.append(f"| {fam} | " + " | ".join(cells) + " |")
    L.append("")

    # ------------------------------------------------ unavailable
    L.append("## 5. UNAVAILABLE and NOT-RUN cells\n")
    L.append(
        "UNAVAILABLE by pre-registration (never substituted):\n\n"
        "- E4 x P2 (TSRV) and E4 x P3 (realized kernel): the "
        "pre-registration's matching-quarticity list assigns no matching "
        "form to these proxies.\n"
        "- E5 x P2..P8: the signature-plot regression is defined on the "
        "noise signature E[RV_M] = IV + 2*M*omega^2 of plain RV; robust "
        "proxies are constructed to remove that signature, leaving no "
        "regression slope to exploit.\n"
        "- E6 x P2..P8: the Hansen-Lunde correction subtracts plain RV's "
        "additive noise bias 2*M*omega^2, which the robust proxies do not "
        "carry.\n"
        "- E6 standalone: reported as the dispersion diagnostic "
        "Var(log RVc)/Var(log RV), not a lambda estimator (see methods "
        "notes); its lambda-producing role is the E6pre_* arms.\n")
    if missing:
        by_class = defaultdict(int)
        for m in missing:
            by_class[m["cclass"]] += 1
        L.append(f"NOT RUN (host-capacity obstruction, see run log): "
                 f"{len(missing)} of 4900 cell groups, by contamination "
                 "class: "
                 + ", ".join(f"{k}: {v}" for k, v in sorted(by_class.items()))
                 + ". Full enumeration: `S02-notrun.csv`. Each NOT-RUN "
                 "group is absent entirely (no partial seed subsets were "
                 "aggregated). The grid runner resumes idempotently: "
                 "rerun `run2.py` to continue.\n")
        with open(os.path.join(RES_DIR, "S02-notrun.csv"), "w",
                  newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(missing[0].keys()))
            w.writeheader()
            w.writerows(missing)
    else:
        L.append("NOT RUN: none; the full grid completed.\n")

    with open(os.path.join(RES_DIR, "S02-report.md"), "w") as fh:
        fh.write("\n".join(L))
    print("report written")


if __name__ == "__main__":
    main()
