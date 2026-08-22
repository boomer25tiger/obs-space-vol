"""Estimators E1-E4 exactly as pre-registered.

E1 returns the full 4-arm x 4-lag-set grid, never a selection.

Arm conventions (autocovariance gamma(k) of log RV fitted on the lag set,
extrapolated to lag 0; lambda-hat = gamma_extrapolated(0) / gamma_hat(0)):
  a exponential      gamma(k) = c * phi^k, phi and c fitted (grid + closed-form
                     scale), extrapolant c.
  b power-law        gamma(k) = a - b * k^alpha (the geostatistical power
                     variogram model seen from the covariance side), alpha
                     gridded, (a, b) closed form, extrapolant a.
  c cubic spline     natural cubic spline through (k, gamma(k)), evaluated at 0.
  d model-implied    gamma(k) = c * rho_fGn(k; H), the fractional log-variance
                     form of the pre-registration, H in (0,1) estimated jointly
                     with c; extrapolant c. For H > 1/2 this family has the
                     ARFIMA-type asymptote k^(2d-1) with d = H - 1/2, which is
                     the pre-registration's stated ARFIMA form.

E2: contiguous temporal halves of each window.
E3: three-cornered hat with pre-measured error correlation matrices.
E4: realized-quarticity reference, Var(RV - IV) = (2/M) RQ per BNS asymptotics,
    mapped to log space by the delta method: Var(e_log,t) ~ (2/M) RQ_t / RV_t^2.
"""

import numpy as np
from scipy.interpolate import CubicSpline

from fbm import fgn_acf

LAG_SETS = {
    "L1-5": np.arange(1, 6),
    "L1-10": np.arange(1, 11),
    "L1-22": np.arange(1, 23),
    "L2-22": np.arange(2, 23),
}
MAXLAG = 22
ARMS = ["a_exp", "b_pow", "c_spline", "d_model"]

_PHI_GRID = np.linspace(0.30, 0.999, 240)
_H_GRID = np.linspace(0.02, 0.98, 193)
_ALPHA_GRID = np.linspace(0.05, 1.95, 96)

_K = np.arange(0, MAXLAG + 1, dtype=float)
_PHI_TAB = _PHI_GRID[:, None] ** _K[None, :]                # (240, 23)
_H_TAB = np.array([fgn_acf(H, _K) for H in _H_GRID])        # (193, 23)


def sample_autocov(y, maxlag=MAXLAG):
    """Biased (1/T) sample autocovariances at lags 0..maxlag."""
    T = len(y)
    yc = y - y.mean()
    g = np.empty(maxlag + 1)
    g[0] = np.dot(yc, yc) / T
    for k in range(1, maxlag + 1):
        g[k] = np.dot(yc[:-k], yc[k:]) / T
    return g


def _shape_fit_extrapolant(gam_k, shape_tab, lags):
    """Best single-shape fit c * s(k) over a grid of shapes; returns c."""
    S = shape_tab[:, lags]                       # (G, L)
    num = S @ gam_k                              # (G,)
    den = (S * S).sum(axis=1)
    # A degenerate shape row (identically zero on the lag set, e.g. fGn at
    # H = 0.5) carries no information; exclude it rather than divide by zero.
    ok = den > 1e-300
    c = np.zeros_like(den)
    c[ok] = num[ok] / den[ok]
    # SSE = sum(gam^2) - c^2 * den; minimizing SSE == maximizing c^2 * den.
    score = np.where(ok, c * c * den, -np.inf)
    best = np.argmax(score)
    return float(c[best])


class _PowerlawTables:
    """Precomputed per-lag-set design tables for gamma(k) = a - b*k^alpha."""

    def __init__(self, lags):
        kk = lags.astype(float)
        self.L = len(kk)
        self.KA = kk[None, :] ** _ALPHA_GRID[:, None]        # (A, L)
        self.sx = self.KA.sum(axis=1)                        # (A,)
        self.sxx = (self.KA * self.KA).sum(axis=1)
        self.det = self.L * self.sxx - self.sx * self.sx

    def extrapolant(self, gam_k):
        sy = gam_k.sum()
        sxy = self.KA @ gam_k                                # (A,)
        a = (self.sxx * sy - self.sx * sxy) / self.det
        b = (self.sx * sy - self.L * sxy) / self.det         # coeff of -k^alpha
        resid = gam_k[None, :] - (a[:, None] - b[:, None] * self.KA)
        sse = (resid * resid).sum(axis=1)
        return float(a[np.argmin(sse)])


_POW_TABLES = {name: _PowerlawTables(lags) for name, lags in LAG_SETS.items()}


def _powerlaw_extrapolant(gam_k, lags, ls_name=None):
    tab = _POW_TABLES.get(ls_name) if ls_name else None
    if tab is None:
        tab = _PowerlawTables(lags)
    return tab.extrapolant(gam_k)


def e1_grid(logrv):
    """Full E1 grid: dict[(arm, lagset)] -> lambda-hat."""
    g = sample_autocov(logrv)
    g0 = g[0]
    out = {}
    for ls_name, lags in LAG_SETS.items():
        gk = g[lags]
        out[("a_exp", ls_name)] = _shape_fit_extrapolant(gk, _PHI_TAB, lags) / g0
        out[("b_pow", ls_name)] = _powerlaw_extrapolant(gk, lags, ls_name) / g0
        cs = CubicSpline(lags.astype(float), gk, bc_type="natural",
                         extrapolate=True)
        out[("c_spline", ls_name)] = float(cs(0.0)) / g0
        out[("d_model", ls_name)] = _shape_fit_extrapolant(gk, _H_TAB, lags) / g0
    return out


def e2(logrv_full, logrv_h1, logrv_h2):
    """Non-overlapping contiguous halves: Cov(log RV1, log RV2)/Var(log RV)."""
    a = logrv_h1 - logrv_h1.mean()
    b = logrv_h2 - logrv_h2.mean()
    cov = np.dot(a, b) / len(a)
    return cov / logrv_full.var()


def e4(rv, rq, logrv, M):
    """Realized-quarticity reference in log space."""
    v = (2.0 / M) * rq / (rv * rv)
    return 1.0 - v.mean() / logrv.var()


def e3_moments(Y, x):
    """Per-replication moments for the three-cornered hat.

    Y: (T, P) log proxies. x: (T,) true latent log IV.
    Returns (yvar (P,), pairvar (P,P), errcorr (P,P)).
    """
    Yc = Y - Y.mean(axis=0)
    T = Y.shape[0]
    cov = (Yc.T @ Yc) / T
    yvar = np.diag(cov).copy()
    pairvar = yvar[:, None] + yvar[None, :] - 2.0 * cov
    E = Y - x[:, None]
    Ec = E - E.mean(axis=0)
    ecov = (Ec.T @ Ec) / T
    esd = np.sqrt(np.clip(np.diag(ecov), 1e-300, None))
    errcorr = ecov / np.outer(esd, esd)
    return yvar, pairvar, errcorr


def tch_lambda(yvar, pairvar, i, j, k):
    """Three-cornered hat estimate of lambda for target proxy i."""
    var_ei = 0.5 * (pairvar[i, j] + pairvar[i, k] - pairvar[j, k])
    return 1.0 - var_ei / yvar[i]


def e3_candidate_triples(target, P, park_idx, gk_idx):
    """Triples (target, j, k), excluding any containing both GK and Parkinson."""
    others = [p for p in range(P) if p != target]
    triples = []
    for a in range(len(others)):
        for b in range(a + 1, len(others)):
            j, k = others[a], others[b]
            if {j, k, target} >= {park_idx, gk_idx}:
                continue
            triples.append((target, j, k))
    return triples
