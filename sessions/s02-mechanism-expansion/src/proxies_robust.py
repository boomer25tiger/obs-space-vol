"""Volatility proxies P1-P8 with the authors' published tuning rules.

Every function is vectorized over T daily windows. Inputs are either the
bucketed return matrix r of shape (T, M) or the observed price path
p of shape (T, M+1) at the M-grid. Delta = 1/M (one window = one time unit).

No bandwidth, window, or threshold is tuned: each rule is the published one,
cited inline. Rule plug-ins (omega^2, IQ, IV) are pooled per dataset cell,
which is the deterministic analogue of the authors' per-day plug-ins.
"""

import numpy as np
from scipy.special import gamma as gamma_fn

MU1 = np.sqrt(2.0 / np.pi)                      # E|Z|
MU43 = 2 ** (2.0 / 3.0) * gamma_fn(7.0 / 6.0) / gamma_fn(0.5)   # E|Z|^(4/3)


# ---------------------------------------------------------------- P1
def p1_rv(r):
    """Plain realized variance."""
    return (r * r).sum(axis=1, dtype=np.float64)


def rq(r, M):
    """Realized quarticity, (M/3) sum r^4 (Barndorff-Nielsen & Shephard)."""
    r2 = r * r
    return (M / 3.0) * (r2 * r2).sum(axis=1, dtype=np.float64)


# ---------------------------------------------------------------- P2
def tsrv_K(M, omega2_hat, iq_hat):
    """ZMA (2005) optimal subsample count K = c n^(2/3), eq. (58), with
    c_opt = (12 (E eps^2)^2 / (T^2 * (4/3) sigma^4 ... ))^(1/3) as in their
    eq. (63) specialized to T = 1:  c_opt = (12 omega^4 / IQ)^(1/3)."""
    c = (12.0 * omega2_hat ** 2 / max(iq_hat, 1e-300)) ** (1.0 / 3.0)
    return int(np.clip(round(c * M ** (2.0 / 3.0)), 2, max(2, M // 2)))


def p2_tsrv(p, K):
    """Two-scale realized variance, ZMA (2005) eq. (55) with the small-sample
    adjustment factor (1 - nbar/n)^(-1) (ZMA 2005, eq. (64)).

    [Y,Y]^avg over K offset grids equals the average of K-spaced squared
    price differences divided by K.
    """
    T, Mp1 = p.shape
    M = Mp1 - 1
    d = p[:, K:] - p[:, :-K]
    rv_avg = (d * d).sum(axis=1, dtype=np.float64) / K
    dr = np.diff(p, axis=1)
    rv_all = (dr * dr).sum(axis=1, dtype=np.float64)
    nbar = (M - K + 1) / K
    ts = rv_avg - (nbar / M) * rv_all
    adj = 1.0 / (1.0 - nbar / M) if nbar / M < 1.0 else 1.0
    return adj * ts


# ---------------------------------------------------------------- P3
def parzen(x):
    x = np.asarray(x, dtype=float)
    out = np.where(x <= 0.5, 1.0 - 6.0 * x ** 2 + 6.0 * x ** 3,
                   2.0 * (1.0 - x) ** 3)
    return np.where(x > 1.0, 0.0, out)


def kernel_H(M, omega2_hat, iv_hat):
    """BNHLS 'Realised kernels in practice' (2009), eq. (3):
    H* = c* xi^(4/5) n^(3/5), c* = ((12)^2/0.269)^(1/5) = 3.5134 (Parzen),
    xi^2 = omega^2 / IV, with IV estimated by a sparse RV and omega^2 by
    RV_dense/(2n)."""
    xi2 = omega2_hat / max(iv_hat, 1e-300)
    H = 3.5134 * xi2 ** (2.0 / 5.0) * M ** (3.0 / 5.0)
    return int(np.clip(round(H), 1, max(1, M - 2)))


def p3_kernel_flattop(r, H):
    """Flat-top realized kernel, BNHLS (2008, Econometrica):
    K(X) = gamma_0 + sum_{h=1}^{H} k((h-1)/H) * 2*gamma_h, Parzen k.
    End-effect jittering omitted per BNHLS (2009) practice paper (their
    mean-squared optimal jitter is m = 1, i.e. none)."""
    T, M = r.shape
    out = (r * r).sum(axis=1, dtype=np.float64)
    w = parzen((np.arange(1, H + 1) - 1.0) / H)
    for h in range(1, H + 1):
        out += 2.0 * w[h - 1] * (r[:, h:] * r[:, :-h]).sum(axis=1,
                                                           dtype=np.float64)
    return out


# ---------------------------------------------------------------- P4
def preav_kn(M, theta=1.0 / 3.0):
    """JLMPV (2009): k_n = theta * sqrt(n); the authors' own simulations use
    k_n corresponding to theta ~= 1/3 (their Section 4: 'we used kn = 51,
    which corresponds to a theta ~= 1/3'). Even k_n as in their eq. (3.13)."""
    kn = int(round(theta * np.sqrt(M)))
    kn = max(2, kn + (kn % 2))          # even, at least 2
    return min(kn, max(2, M // 2))


def _preav_bars(r, kn):
    """Pre-averaged returns  Zbar_i = sum_{j=1}^{kn-1} g(j/kn) r_{i+j},
    g(x) = min(x, 1-x)  (JLMPV 2009, eq. (3.5) and (3.11))."""
    T, M = r.shape
    g = np.minimum(np.arange(1, kn) / kn, 1.0 - np.arange(1, kn) / kn)
    nbar = M - kn + 2
    zb = np.zeros((T, nbar))
    for j in range(1, kn):
        zb += g[j - 1] * r[:, j - 1:j - 1 + nbar]
    return zb, g


def _preav_fs_adjustment(kn, psi1, psi2):
    """Finite-sample adjustment (1 - psi1*Delta/(2 theta^2 psi2))^(-1)
    = (1 - psi1/(2 kn^2 psi2))^(-1), per Christensen, Kinnebrock &
    Podolskij (2010, J. Econometrics), who apply exactly this factor to the
    modulated/pre-averaged realized variance to remove the small-kn bias of
    the JLMPV noise-correction term."""
    d = 1.0 - psi1 / (2.0 * kn * kn * psi2)
    return 1.0 / d if d > 0.05 else 1.0


def _preav_consts(kn, g):
    """Finite-sample psi analogues (JLMPV 2009, Section 4)."""
    gn = np.concatenate([[0.0], g, [0.0]])       # g(0)=g(1)=0
    psi1 = kn * ((gn[1:] - gn[:-1]) ** 2).sum()
    psi2 = (gn[1:-1] ** 2).sum() / kn
    return psi1, psi2


def p4_preav(r, kn):
    """Pre-averaged RV, JLMPV (2009) eq. (3.6), bias-corrected:
    C = sqrt(Delta)/(theta psi2) sum Zbar^2 - psi1 Delta/(2 theta^2 psi2) sum r^2
    with theta redefined as kn*sqrt(Delta) (their Section 4 practice)."""
    T, M = r.shape
    zb, g = _preav_bars(r, kn)
    psi1, psi2 = _preav_consts(kn, g)
    delta = 1.0 / M
    theta = kn * np.sqrt(delta)
    s1 = (zb * zb).sum(axis=1, dtype=np.float64)
    s2 = (r * r).sum(axis=1, dtype=np.float64)
    raw = (np.sqrt(delta) / (theta * psi2)) * s1 \
        - (psi1 * delta / (2.0 * theta ** 2 * psi2)) * s2
    return _preav_fs_adjustment(kn, psi1, psi2) * raw


def p4_preav_quarticity(r, kn):
    """Pre-averaged quarticity, JLMPV (2009) Remark 4 / eq. (3.14)."""
    T, M = r.shape
    zb, g = _preav_bars(r, kn)
    psi1, psi2 = _preav_consts(kn, g)
    delta = 1.0 / M
    theta = kn * np.sqrt(delta)
    r2 = (r * r).astype(np.float64)
    zb2 = zb * zb
    t1 = (zb2 * zb2).sum(axis=1) / (3.0 * theta ** 2 * psi2 ** 2)
    # middle term: sum_i Zbar_i^2 * sum_{j=i+kn}^{i+2kn-1} r_j^2
    cs = np.concatenate([np.zeros((T, 1)), np.cumsum(r2, axis=1)], axis=1)
    nbar = zb.shape[1]
    t2 = np.zeros(T)
    lo = np.arange(nbar) + kn
    hi = np.minimum(lo + kn, M)
    valid = lo < M
    win = cs[:, hi[valid]] - cs[:, lo[valid]]
    t2 = (zb2[:, valid] * win).sum(axis=1)
    t2 *= delta * psi1 / (theta ** 4 * psi2 ** 2)
    t3 = (r2[:, :-2] * r2[:, 2:]).sum(axis=1) \
        * delta * psi1 ** 2 / (4.0 * theta ** 4 * psi2 ** 2)
    return t1 - t2 + t3


# ---------------------------------------------------------------- P5
def p5_bipower(r):
    """Bipower variation, Barndorff-Nielsen & Shephard (2004), with the
    standard M/(M-1) small-sample factor."""
    T, M = r.shape
    a = np.abs(r)
    return (np.pi / 2.0) * (M / (M - 1.0)) \
        * (a[:, 1:] * a[:, :-1]).sum(axis=1, dtype=np.float64)


# ---------------------------------------------------------------- P6
def p6_medrv(r):
    """Median RV, Andersen, Dobrev, Schaumburg (2012):
    MedRV = pi/(6-4*sqrt(3)+pi) * M/(M-2) * sum med(|r_{i-1}|,|r_i|,|r_{i+1}|)^2."""
    T, M = r.shape
    a = np.abs(r)
    med = np.median(np.stack([a[:, :-2], a[:, 1:-1], a[:, 2:]], axis=2),
                    axis=2)
    c = np.pi / (6.0 - 4.0 * np.sqrt(3.0) + np.pi)
    return c * (M / (M - 2.0)) * (med * med).sum(axis=1, dtype=np.float64)


# ---------------------------------------------------------------- P7
def p7_truncated(r, local_var=None):
    """Truncated RV, Mancini (2009). Threshold: 3 local standard deviations
    per interval. Locality = the window: local variance from that window's
    bipower variation (jump-robust), i.e. u = 3*sqrt(BV/M)."""
    T, M = r.shape
    if local_var is None:
        local_var = p5_bipower(r)
    u = 3.0 * np.sqrt(np.maximum(local_var, 1e-300) / M)
    keep = np.abs(r) <= u[:, None]
    return (np.where(keep, r, 0.0) ** 2).sum(axis=1, dtype=np.float64)


# ---------------------------------------------------------------- P8
def p8_preav_truncated(r, kn):
    """Pre-averaged truncated RV: JLMPV (2009) pre-averaging with the
    Mancini (2009) 3-local-sd truncation applied to the pre-averaged
    returns; the truncation scale is the jump-robust median absolute
    pre-averaged return (median |Zbar| / Phi^-1(3/4) as the local sd).
    The noise bias correction of eq. (3.6) is retained."""
    T, M = r.shape
    zb, g = _preav_bars(r, kn)
    psi1, psi2 = _preav_consts(kn, g)
    delta = 1.0 / M
    theta = kn * np.sqrt(delta)
    scale = np.median(np.abs(zb), axis=1) / 0.6744897501960817
    u = 3.0 * scale
    zt = np.where(np.abs(zb) <= u[:, None], zb, 0.0)
    s1 = (zt * zt).sum(axis=1, dtype=np.float64)
    s2 = (r * r).sum(axis=1, dtype=np.float64)
    raw = (np.sqrt(delta) / (theta * psi2)) * s1 \
        - (psi1 * delta / (2.0 * theta ** 2 * psi2)) * s2
    return _preav_fs_adjustment(kn, psi1, psi2) * raw


# ---------------------------------------------------------------- quarticities
def tripower_quarticity(r, M):
    """Tripower quarticity, Barndorff-Nielsen & Shephard (2006):
    TQ = M * (M/(M-2)) * mu_{4/3}^{-3} * sum |r_i r_{i+1} r_{i+2}|^{4/3}."""
    a = np.abs(r) ** (4.0 / 3.0)
    s = (a[:, :-2] * a[:, 1:-1] * a[:, 2:]).sum(axis=1, dtype=np.float64)
    return M * (M / (M - 2.0)) * MU43 ** (-3.0) * s
