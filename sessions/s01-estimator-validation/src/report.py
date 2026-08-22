"""Build S01-report.md and S01-runlog.md from aggregated results."""

import csv
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run import ARM_KEYS, PROXY_NAMES, BASE
from aggregate import ALL_ARMS, BANDS

RES_DIR = os.path.join(BASE, "results")
LOG_DIR = os.path.join(BASE, "logs")
DGPS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7"]
DGP_DESC = {
    "D1": "AR(1), control",
    "D2": "ARFIMA(0,d,0), long memory",
    "D3": "Fractional OU, rough (H in {0.08, 0.10, 0.16})",
    "D4": "Fractional OU, moderately rough (H in {0.30, 0.50})",
    "D5": "AR(1) plus price jumps",
    "D6": "AR(1) plus microstructure noise",
    "D7": "ARFIMA plus jumps and noise, combined stress",
}
SWEEP_KEYS = ["shape", "sd", "js", "nsr", "n", "M"]


def load_rows():
    rows = []
    with open(os.path.join(RES_DIR, "S01-cells.csv")) as fh:
        for r in csv.DictReader(fh):
            for k in ["shape", "sd", "js", "nsr", "point", "lo", "hi",
                      "seed_sd", "nan_frac"]:
                r[k] = float(r[k]) if r[k] not in ("", "nan") else np.nan
            r["n"] = int(r["n"]); r["M"] = int(r["M"])
            for k in ["pass10", "pass15", "pass25"]:
                r[k] = (r[k] == "True") if r[k] in ("True", "False") else None
            r["inapplicable"] = r["inapplicable"] == "True"
            rows.append(r)
    return rows


def fmt(x, nd=3):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "--"
    return f"{x:.{nd}f}"


def cell_tag(r):
    bits = [f"sh={r['shape']:g}", f"sd={r['sd']:g}"]
    if r["js"]:
        bits.append(f"js={r['js']:g}")
    if r["nsr"]:
        bits.append(f"nsr={r['nsr']:g}")
    bits.append(f"n={r['n']}")
    bits.append(f"M={r['M']}")
    return ",".join(bits)


def arm_dgp_summary(rows, arm, dgp):
    sel = [r for r in rows if r["arm"] == arm and r["dgp"] == dgp]
    if not sel:
        return None
    inap = [r for r in sel if r["inapplicable"]]
    ok = [r for r in sel if not r["inapplicable"]]
    out = dict(n_cells=len(sel), n_inapplicable=len(inap))
    if ok:
        pts = np.array([r["point"] for r in ok])
        out["point"] = float(np.mean(pts))
        out["median"] = float(np.median(pts))
        out["ci"] = (float(min(r["lo"] for r in ok)),
                     float(max(r["hi"] for r in ok)))
        out["seed_sd"] = float(np.median([r["seed_sd"] for r in ok]))
        worst = max(ok, key=lambda r: abs(r["point"] - 1.0))
        out["worst"] = (worst["point"], cell_tag(worst))
        for B in BANDS:
            key = f"pass{int(B*100)}"
            fails = [r for r in ok if not r[key]]
            # Pre-registration: failure on any single cell fails the DGP.
            out[key] = (len(fails) == 0 and len(inap) == 0, len(fails))
    else:
        out["point"] = np.nan
    return out


def verdict_str(summ, B):
    key = f"pass{int(B*100)}"
    if "worst" not in summ:
        return "INAPPLICABLE"
    if summ["n_inapplicable"]:
        return f"INAPPL({summ['n_inapplicable']})"
    ok, nf = summ[key]
    return "PASS" if ok else f"FAIL({nf})"


def sweep_sensitivity(rows):
    """Cells whose primary-band conclusion flips when exactly one swept
    parameter changes."""
    idx = {}
    for r in rows:
        if r["pass15"] is None:
            continue
        key = (r["arm"], r["dgp"], r["shape"], r["sd"], r["js"], r["nsr"],
               r["n"], r["M"])
        idx[key] = r
    out = []
    seen = set()
    dims = ["shape", "sd", "js", "nsr", "n", "M"]
    for key, r in idx.items():
        for di, dim in enumerate(dims):
            for key2, r2 in idx.items():
                if key2 <= key:
                    continue
                if key2[0] != key[0] or key2[1] != key[1]:
                    continue
                diff = [i for i in range(2, 8) if key[i] != key2[i]]
                if diff != [di + 2]:
                    continue
                if r["pass15"] != r2["pass15"]:
                    tag = (key[0], key[1], dim, min(key, key2), max(key, key2))
                    if tag in seen:
                        continue
                    seen.add(tag)
                    out.append((r, r2, dim))
    return out


def main():
    rows = load_rows()
    with open(os.path.join(LOG_DIR, "unit-tests.txt")) as fh:
        unit_out = fh.read().rstrip()

    L = []
    L.append("# Session 1 report, estimator validation\n")
    L.append("Run date 2026-08-18. Synthetic data only. Pre-registration: "
             "`../PREREG.md` (frozen before any simulation). Decisions log: "
             "`../../../DECISIONS.md`.\n")

    # ---------------- unit tests
    L.append("## Unit test output, in full\n")
    L.append("U1-U5 ran and passed before any DGP simulation. A failing unit "
             "test would have halted the session.\n")
    L.append("```text\n" + unit_out + "\n```\n")

    # ---------------- implementation notes
    L.append("## Implementation constants and interpretations\n")
    L.append(
        "Recorded before the grid was run; none was chosen after seeing "
        "results.\n\n"
        "- Latent log-variance is mean-zero Gaussian; the pre-registration's "
        "\"unconditional sd of log RV\" sweep is applied as the sd of the "
        "latent log-IV process (log RV then exceeds it by the measurement-"
        "error contribution, which is what the estimators must remove).\n"
        "- Fractional OU is sampled exactly via circulant embedding of its "
        "autocovariance, computed by quadrature of the fOU spectral density; "
        "mean-reversion kappa = 0.03/day, an a-priori constant from the "
        "rough-volatility literature (not swept). At H = 0.5 the process is "
        "an exact AR(1) with phi = exp(-0.03), the pre-registered non-rough "
        "control.\n"
        "- E1 arm (d) fits gamma(k) = c * rho_fGn(k; H) with H in (0, 1) "
        "estimated jointly with c (extrapolant c). For H > 1/2 this family "
        "carries the ARFIMA asymptote k^(2d-1) with d = H - 1/2, so the two "
        "model-implied forms named in the pre-registration are one family.\n"
        "- E1 arm (b) is the geostatistical power model on the covariance "
        "side, gamma(k) = a - b*k^alpha, extrapolant a.\n"
        "- E4 maps Var(RV - IV) = (2/M) RQ to log space by the delta method: "
        "Var(e_log,t) ~= (2/M) RQ_t / RV_t^2; lambda-hat = 1 - mean(v_t)/"
        "Var(log RV).\n"
        "- Bipower variation is computed at the finest M of each geometry "
        "(the pre-registration lists it once, not per M).\n"
        "- Jumps: compound Poisson, intensity 1/day, size variance set so "
        "the jump share of expected total QV equals the swept value. Noise: "
        "additive iid Gaussian on every observed log price, variance = "
        "nsr * E[IV].\n"
        "- E3 triple selection uses the across-seed mean error-correlation "
        "matrix per (cell group, M); candidate triples contain the target "
        "RV_M and exclude the Garman-Klass/Parkinson pair a priori.\n"
        "- Recovery ratio = lambda-hat / lambda-true(rep), where lambda-true "
        "is Var(latent log IV)/Var(log RV) computed from the realized "
        "replication.\n")

    # ---------------- aggregation rules
    L.append("## Aggregation rules\n")
    L.append(
        "Cell = (DGP parameter combination, geometry n, sampling frequency "
        "M): point estimate is the grand mean recovery over 5 master seeds "
        "x 200 replications; the 95% CI is a percentile bootstrap (1000 "
        "resamples of replications within each seed, averaged across seeds, "
        "bootstrap seed 777); between-seed dispersion is the sd of the 5 "
        "per-seed means. A cell passes a band only if the point estimate is "
        "inside the band and the CI excludes both edges. Per (estimator, "
        "DGP) the verdict is PASS only if every cell passes "
        "(pre-registration: failure on any single DGP is a FAIL); FAIL(k) "
        "reports k failing cells. Tables below aggregate cells per "
        "(estimator, DGP): `point` = mean across cells, `CI env` = envelope "
        "of cell CIs, `seed sd` = median across cells, `worst cell` = point "
        "estimate farthest from 1. The full uncollapsed per-cell record "
        "(15,960 rows) is `S01-cells.csv`.\n")

    # ---------------- E1 grid
    L.append("## E1 nugget, full grid (four arms x four lag sets, "
             "no selection)\n")
    for dgp in DGPS:
        L.append(f"### {dgp}: {DGP_DESC[dgp]}\n")
        L.append("| arm | lag set | point | CI env | seed sd | worst cell | "
                 "+/-10% | +/-15% | +/-25% |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for arm, ls in ARM_KEYS:
            a = f"E1_{arm}_{ls}"
            s = arm_dgp_summary(rows, a, dgp)
            if s is None:
                continue
            w = f"{fmt(s['worst'][0])} @ {s['worst'][1]}"
            L.append(
                f"| {arm} | {ls} | {fmt(s['point'])} | "
                f"[{fmt(s['ci'][0])}, {fmt(s['ci'][1])}] | "
                f"{fmt(s['seed_sd'])} | {w} | "
                f"{verdict_str(s, 0.10)} | {verdict_str(s, 0.15)} | "
                f"{verdict_str(s, 0.25)} |")
        L.append("")

    # ---------------- E2/E3/E4
    for arm, title in [
            ("E2", "E2 non-overlapping subsampling (contiguous halves)"),
            ("E3", "E3 three-cornered hat"),
            ("E4", "E4 realized-quarticity reference")]:
        L.append(f"## {title}\n")
        L.append("| DGP | point | CI env | seed sd | worst cell | +/-10% | "
                 "+/-15% | +/-25% |")
        L.append("|---|---|---|---|---|---|---|---|")
        for dgp in DGPS:
            s = arm_dgp_summary(rows, arm, dgp)
            if s is None:
                continue
            if "worst" in s:
                w = f"{fmt(s['worst'][0])} @ {s['worst'][1]}"
                L.append(
                    f"| {dgp} | {fmt(s['point'])} | "
                    f"[{fmt(s['ci'][0])}, {fmt(s['ci'][1])}] | "
                    f"{fmt(s['seed_sd'])} | {w} | "
                    f"{verdict_str(s, 0.10)} | {verdict_str(s, 0.15)} | "
                    f"{verdict_str(s, 0.25)} |")
            else:
                L.append(f"| {dgp} | -- | -- | -- | all cells inapplicable | "
                         "INAPPLICABLE | INAPPLICABLE | INAPPLICABLE |")
        L.append("")

    # ---------------- E3 error correlation matrices
    L.append("## E3 measured error correlation matrices\n")
    L.append("Mean off-diagonal error correlations of the nine candidate "
             "proxies (errors vs true log IV), averaged over parameter "
             "combinations, seeds and replications, per DGP and geometry. "
             "Every candidate triple's correlations are entries of these "
             "matrices. Per-cell triple selection and applicability: "
             "`S01-e3-selection.csv`.\n")
    ec = np.load(os.path.join(RES_DIR, "S01-errcorr.npz"))
    for key in sorted(ec.files):
        M = ec[key]
        L.append(f"### {key}\n")
        L.append("| | " + " | ".join(PROXY_NAMES) + " |")
        L.append("|---" * (len(PROXY_NAMES) + 1) + "|")
        for i, pn in enumerate(PROXY_NAMES):
            vals = " | ".join(f"{M[i, j]:.2f}" for j in range(len(PROXY_NAMES)))
            L.append(f"| **{pn}** | {vals} |")
        L.append("")

    with open(os.path.join(RES_DIR, "S01-e3-selection.csv")) as fh:
        e3rows = list(csv.DictReader(fh))
    n_inap = sum(1 for r in e3rows if r["applicable"] == "False")
    L.append(f"E3 applicability: {len(e3rows) - n_inap} of {len(e3rows)} "
             "(cell group, M) combinations had a triple with max off-diagonal "
             f"error correlation <= 0.20; {n_inap} were INAPPLICABLE.\n")
    tri_count = defaultdict(int)
    for r in e3rows:
        if r["applicable"] == "True":
            tri_count[r["triple"]] += 1
    L.append("Selected triples (count): " + ", ".join(
        f"{t} ({c})" for t, c in
        sorted(tri_count.items(), key=lambda kv: -kv[1])) + "\n")

    # ---------------- sweep sensitivity
    L.append("## Cells where the primary-band conclusion changes across "
             "the parameter sweep\n")
    flips = sweep_sensitivity(rows)
    if not flips:
        L.append("None.\n")
    else:
        L.append(f"{len(flips)} single-parameter flips of the +/-15% verdict "
                 "(pairs of cells differing in exactly one swept parameter "
                 "with opposite PASS/FAIL):\n")
        L.append("| arm | DGP | varying | cell A | A pass15 | cell B | "
                 "B pass15 |")
        L.append("|---|---|---|---|---|---|---|")
        for r, r2, dim in flips:
            L.append(f"| {r['arm']} | {r['dgp']} | {dim} | {cell_tag(r)} | "
                     f"{r['pass15']} | {cell_tag(r2)} | {r2['pass15']} |")
        L.append("")

    with open(os.path.join(RES_DIR, "S01-report.md"), "w") as fh:
        fh.write("\n".join(L))
    print("report written:", os.path.join(RES_DIR, "S01-report.md"),
          f"({len(flips)} sweep flips)")


if __name__ == "__main__":
    main()
