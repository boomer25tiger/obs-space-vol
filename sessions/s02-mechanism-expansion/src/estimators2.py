"""S02 estimators E1, E2, E4, E5, E6 as pre-registered.

E1 machinery (autocovariance, shape-fit extrapolants) is imported unmodified
from S01's estimators module; only the pre-registered reduced grid
(arms a_exp and d_model, lag sets L1-5 and L1-10) is evaluated.
"""

import os
import sys

import numpy as np

_S01_SRC = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))),
    "s01-estimator-validation", "src")
if _S01_SRC not in sys.path:
    sys.path.insert(0, _S01_SRC)

import estimators as s01e                     # noqa: E402

LAG_SETS = {k: v for k, v in s01e.LAG_SETS.items() if k in ("L1-5", "L1-10")}
E1_KEYS = [("a_exp", ls) for ls in LAG_SETS] + [("d_model", ls)
                                               for ls in LAG_SETS]
LOG_FLOOR = 1e-14


def safe_log(a, counter):
    n_bad = int((a < LOG_FLOOR).sum())
    if n_bad:
        counter[0] += n_bad
        a = np.maximum(a, LOG_FLOOR)
    return np.log(a)


def e1_reduced(logp):
    """E1 arms a_exp, d_model at L1-5, L1-10 on the log proxy series."""
    g = s01e.sample_autocov(logp, maxlag=10)
    g0 = g[0]
    out = {}
    for ls, lags in LAG_SETS.items():
        gk = g[lags]
        out[("a_exp", ls)] = s01e._shape_fit_extrapolant(
            gk, s01e._PHI_TAB, lags) / g0
        out[("d_model", ls)] = s01e._shape_fit_extrapolant(
            gk, s01e._H_TAB, lags) / g0
    return out


def e2(logp_full, logp_h1, logp_h2):
    a = logp_h1 - logp_h1.mean()
    b = logp_h2 - logp_h2.mean()
    return (np.dot(a, b) / len(a)) / logp_full.var()


def e4(P, Q, logP, M):
    """Pre-registered form: Var(log error) ~= (2/M) * Q / P^2.

    Output clipped to +/-1e30 so degenerate cells (floored proxies) stay
    representable in float32 storage; any |lambda| that large is reported
    as the failure it is.
    """
    v = (2.0 / M) * Q / np.maximum(P * P, 1e-300)
    return float(np.clip(1.0 - v.mean() / logP.var(), -1e30, 1e30))


def e5_signature(rv_by_m, m_list, log_rv_by_m, floor_counter):
    """Signature-plot regression (pre-registered E5).

    Per window t, OLS of RV_M(t) on M across the available M:
    intercept IVhat_t (the M -> 0 extrapolation, noise-free under
    E[RV_M] = IV + 2 M omega^2), slope/2 = omega^2_t.

    Reliability: lambda(M) = [Var(log IVhat) - mean SE_log^2] / Var(log RV_M),
    where SE_log^2 = Var(intercept_t)/IVhat_t^2 is the OLS delta-method
    sampling variance of log IVhat, subtracted because the intercept's own
    sampling error otherwise inflates the numerator mechanically (documented
    implementation decision, fixed before any grid results).

    Returns (lambda per M dict, mean omega2_hat).
    """
    ms = np.array(m_list, dtype=float)
    X = np.column_stack([np.ones_like(ms), ms])
    XtXi = np.linalg.inv(X.T @ X)
    W = XtXi @ X.T                              # (2, nM)
    Y = np.column_stack([rv_by_m[M] for M in m_list])   # (T, nM)
    beta = Y @ W.T                              # (T, 2)
    iv_hat = beta[:, 0]
    omega2_hat = 0.5 * beta[:, 1]
    resid = Y - beta @ X.T
    dof = len(m_list) - 2
    s2 = (resid * resid).sum(axis=1) / dof
    var_int = s2 * XtXi[0, 0]
    iv_pos = np.maximum(iv_hat, LOG_FLOOR)
    n_bad = int((iv_hat < LOG_FLOOR).sum())
    if n_bad:
        floor_counter[0] += n_bad
    log_iv = np.log(iv_pos)
    num = log_iv.var() - np.mean(var_int / (iv_pos * iv_pos))
    lam = {}
    for M in m_list:
        lam[M] = num / log_rv_by_m[M].var()
    return lam, float(omega2_hat.mean())


def e6_omega2(rv_finest, m_finest):
    """Hansen-Lunde direct noise estimator omega^2_t = RV_finest,t/(2 n)."""
    return rv_finest / (2.0 * m_finest)


def e6_correct(rv, M, omega2_t, floor_counter):
    """Pre-correction: RV_M - 2 M omega^2_t, floored before logs."""
    c = rv - 2.0 * M * omega2_t
    n_bad = int((c < LOG_FLOOR).sum())
    if n_bad:
        floor_counter[0] += n_bad
    return np.maximum(c, LOG_FLOOR)
