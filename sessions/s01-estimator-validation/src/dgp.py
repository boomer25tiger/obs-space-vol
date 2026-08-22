"""Data-generating processes D1-D7 of the session-1 pre-registration.

Latent daily log-variance x_t is a stationary Gaussian process (mean 0,
sd swept). Intraday log-price increments are conditionally Gaussian with
constant within-day volatility, IV_t = exp(x_t). Jumps (D5, D7) enter the
price as compound-Poisson moves excluded from IV; microstructure noise
(D6, D7) is additive iid Gaussian noise on every observed log price.

All latent processes are generated exactly through circulant embedding
(fbm.CirculantEmbedding). The fractional-OU autocovariance is computed by
numerical quadrature of its spectral density
    S(w) proportional to |w|^(1-2H) / (kappa^2 + w^2)
(Cheridito, Kawaguchi, Maejima 2003) and cached. kappa is fixed at 0.03/day,
an a-priori constant taken from the rough-volatility literature; it is not a
swept parameter of the pre-registration and is logged as an implementation
constant. At H = 0.5 this acf reduces to exp(-kappa*k), i.e. an AR(1) with
phi ~= 0.9704, which serves as the pre-registered non-rough control.
"""

import os
from dataclasses import dataclass, field

import numpy as np
from scipy.integrate import quad

from fbm import CirculantEmbedding

FOU_KAPPA = 0.03
_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_cache")


def ar1_rho(phi, K):
    return phi ** np.arange(K, dtype=float)


def arfima_rho(d, K):
    """Exact ARFIMA(0,d,0) autocorrelation via the Gamma-ratio recursion."""
    rho = np.empty(K)
    rho[0] = 1.0
    for k in range(1, K):
        rho[k] = rho[k - 1] * (k - 1 + d) / (k - d)
    return rho


def fou_rho(H, K, kappa=FOU_KAPPA):
    """Stationary fOU autocorrelation at integer lags 0..K-1, by quadrature.

    gamma(k) proportional to int_0^inf cos(k*w) * w^(1-2H)/(kappa^2+w^2) dw.
    Cached on disk because it is reused by every replication.
    """
    os.makedirs(_CACHE_DIR, exist_ok=True)
    fn = os.path.join(_CACHE_DIR, f"fou_H{H:.4f}_kap{kappa:.4f}_K{K}.npy")
    if os.path.exists(fn):
        return np.load(fn)

    def integrand(w):
        return w ** (1.0 - 2.0 * H) / (kappa ** 2 + w ** 2)

    gam = np.empty(K)
    # k = 0: plain adaptive quadrature, split at w=1 for the slow tail.
    g0a = quad(integrand, 0.0, 1.0, limit=200)[0]
    g0b = quad(integrand, 1.0, np.inf, limit=200)[0]
    gam[0] = g0a + g0b
    for k in range(1, K):
        # QAWF handles the oscillatory infinite tail.
        ga = quad(integrand, 0.0, 1.0, weight="cos", wvar=float(k), limit=200)[0]
        gb = quad(integrand, 1.0, np.inf, weight="cos", wvar=float(k),
                  limit=200)[0]
        gam[k] = ga + gb
    rho = gam / gam[0]
    np.save(fn, rho)
    return rho


@dataclass
class DGPConfig:
    dgp: str            # 'D1'..'D7'
    family: str         # 'ar1' | 'arfima' | 'fou'
    shape: float        # phi, d, or H
    sd: float           # unconditional sd of latent log-variance
    jump_share: float = 0.0
    nsr: float = 0.0
    jump_intensity: float = 1.0   # expected jumps per day (implementation const)

    def label(self):
        parts = [self.dgp, self.family, f"sh{self.shape}", f"sd{self.sd}"]
        if self.jump_share:
            parts.append(f"js{self.jump_share}")
        if self.nsr:
            parts.append(f"nsr{self.nsr}")
        return "_".join(parts)


def latent_rho(cfg, K):
    if cfg.family == "ar1":
        return ar1_rho(cfg.shape, K)
    if cfg.family == "arfima":
        return arfima_rho(cfg.shape, K)
    if cfg.family == "fou":
        return fou_rho(cfg.shape, K)
    raise ValueError(cfg.family)


def build_embedding(cfg, T):
    return CirculantEmbedding(latent_rho(cfg, T))


def simulate_latent(cfg, emb, rng):
    """Latent daily log-IV path for one replication."""
    return emb.sample(rng, size=1)[0] * cfg.sd


def simulate_day_chunk(cfg, iv_chunk, n, rng):
    """Observed intraday cumulative log-price paths for a chunk of days.

    Returns path of shape (C, n+1) in float32, with the day's opening
    observation at column 0 (noise included when nsr > 0). Chunking over
    days keeps the peak working set to a few MB per worker; the intraday
    buffers are float32, whose ~1e-7 relative rounding is orders of
    magnitude below every tolerance in this study.
    """
    C = len(iv_chunk)
    r = rng.standard_normal((C, n), dtype=np.float32)
    r *= np.sqrt(iv_chunk / n)[:, None].astype(np.float32)

    if cfg.jump_share > 0.0:
        e_iv = float(np.exp(cfg.sd ** 2 / 2.0))
        sig2_j = cfg.jump_share / (1.0 - cfg.jump_share) * e_iv \
            / cfg.jump_intensity
        njumps = rng.poisson(cfg.jump_intensity, size=C)
        tot = int(njumps.sum())
        if tot:
            day_idx = np.repeat(np.arange(C), njumps)
            step_idx = rng.integers(0, n, size=tot)
            sizes = rng.normal(0.0, np.sqrt(sig2_j), size=tot)
            np.add.at(r, (day_idx, step_idx), sizes.astype(np.float32))

    path = np.empty((C, n + 1), dtype=np.float32)
    path[:, 0] = 0.0
    np.cumsum(r, axis=1, out=path[:, 1:])

    if cfg.nsr > 0.0:
        e_iv = float(np.exp(cfg.sd ** 2 / 2.0))
        sig_u = np.float32(np.sqrt(cfg.nsr * e_iv))
        u = rng.standard_normal((C, n + 1), dtype=np.float32)
        u *= sig_u
        path += u

    return path


def build_param_grid():
    """The 105 pre-registered DGP parameter combinations."""
    PHI = [0.95, 0.98, 0.995]
    SD = [0.5, 0.7, 1.0]
    DMEM = [0.35, 0.40, 0.45]
    H_ROUGH = [0.08, 0.10, 0.16]
    H_MOD = [0.30, 0.50]
    JS = [0.05, 0.10]
    NSR = [0.001, 0.01]

    cfgs = []
    for phi in PHI:
        for sd in SD:
            cfgs.append(DGPConfig("D1", "ar1", phi, sd))
    for d in DMEM:
        for sd in SD:
            cfgs.append(DGPConfig("D2", "arfima", d, sd))
    for H in H_ROUGH:
        for sd in SD:
            cfgs.append(DGPConfig("D3", "fou", H, sd))
    for H in H_MOD:
        for sd in SD:
            cfgs.append(DGPConfig("D4", "fou", H, sd))
    for phi in PHI:
        for sd in SD:
            for js in JS:
                cfgs.append(DGPConfig("D5", "ar1", phi, sd, jump_share=js))
    for phi in PHI:
        for sd in SD:
            for nsr in NSR:
                cfgs.append(DGPConfig("D6", "ar1", phi, sd, nsr=nsr))
    for d in DMEM:
        for sd in SD:
            for js in JS:
                for nsr in NSR:
                    cfgs.append(DGPConfig("D7", "arfima", d, sd,
                                          jump_share=js, nsr=nsr))
    return cfgs


GEOMETRIES = {
    390: [13, 26, 78, 195],
    1380: [23, 46, 138, 345],
}
