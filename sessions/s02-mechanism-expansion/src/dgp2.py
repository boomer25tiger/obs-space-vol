"""S02 data-generating processes: D1-D4 latent daily log-variance crossed
with within-window structure W0/W1/W2 and contamination C0-C3.

Latent daily processes reuse the exact circulant-embedding machinery of S01
(fbm.CirculantEmbedding and the S01 acf functions, imported unmodified).

Within-window structure:
  W0  constant variance within the window (the S01 condition).
  W1  deterministic diurnal U-shape m(u) = a + b(2u-1)^2, u in (0,1),
      normalized to mean 1 on the intraday grid; peak-to-trough ratio
      rho = (a+b)/a swept.
  W2  W1 times a stochastic intraday factor f = exp(zeta*eta - zeta^2/2),
      eta an AR(1) across intraday steps with unit stationary variance and
      half-life fixed a priori at 60 steps (one hour at 1-minute sampling);
      zeta = 0.5 fixed a priori. E[f] = 1 so the expected profile is W1's.

True IV_t is the realized within-window sum sum_i sigma^2_{t,i} / n, which
under W2 differs stochastically from exp(x_t); lambda_true always uses this
realized IV.

Contamination: jumps are compound Poisson (intensity 1/day fixed a priori,
size variance set so the jump share of expected total QV equals the swept
value); microstructure noise is additive iid Gaussian on every observed log
price with variance nsr * E[IV]. Identical mechanics to S01.
"""

import os
import sys
from dataclasses import dataclass

import numpy as np
from scipy.signal import lfilter

_S01_SRC = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))),
    "s01-estimator-validation", "src")
if _S01_SRC not in sys.path:
    sys.path.insert(0, _S01_SRC)

from fbm import CirculantEmbedding                     # noqa: E402
from dgp import ar1_rho, arfima_rho, fou_rho           # noqa: E402

W2_ZETA = 0.5          # a-priori intraday log-vol dispersion
W2_HALFLIFE = 60.0     # steps; one hour at 1-minute sampling
JUMP_INTENSITY = 1.0   # expected jumps per day


@dataclass
class DGP2Config:
    dgp: str          # 'D1'..'D4'
    family: str       # 'ar1' | 'arfima' | 'fou'
    shape: float      # phi, d, or H
    sd: float         # 0.7 fixed
    w: str            # 'W0' | 'W1' | 'W2'
    ptt: float        # diurnal peak-to-trough ratio (1 for W0)
    jump_share: float
    nsr: float

    def label(self):
        parts = [self.dgp, self.family, f"sh{self.shape}",
                 self.w, f"r{self.ptt:g}",
                 f"js{self.jump_share:g}", f"nsr{self.nsr:g}"]
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


def diurnal_profile(n, ptt):
    """U-shape m(u) = a + b(2u-1)^2 with (a+b)/a = ptt, grid mean exactly 1."""
    u = (np.arange(n) + 0.5) / n
    base = (2.0 * u - 1.0) ** 2
    if ptt <= 1.0:
        return np.ones(n)
    m = 1.0 + (ptt - 1.0) * base      # trough 1, peak ptt
    return m / m.mean()


def simulate_latent(cfg, emb, rng):
    return emb.sample(rng, size=1)[0] * cfg.sd


def simulate_day_chunk(cfg, x_chunk, n, profile, rng):
    """Chunk of days -> (true_iv (C,), observed path (C, n+1) float32).

    Per-step variance: exp(x_t) * m_i * f_{t,i} / n. true_iv is its exact
    within-day sum (the realized integrated variance, jump-free).
    """
    C = len(x_chunk)
    base = np.exp(x_chunk)                          # (C,)
    step_var = np.outer(base / n, profile)          # (C, n)

    if cfg.w == "W2":
        phi = np.exp(-np.log(2.0) / W2_HALFLIFE)
        innov_sd = np.float32(np.sqrt(1.0 - phi * phi))
        eps = rng.standard_normal((C, n), dtype=np.float32)
        eps *= innov_sd
        eps[:, 0] = rng.standard_normal(C).astype(np.float32)  # stationary start
        eta = lfilter([1.0], [1.0, -phi], eps, axis=1)
        f = np.exp((W2_ZETA * eta - 0.5 * W2_ZETA ** 2).astype(np.float32))
        step_var = step_var * f

    true_iv = step_var.sum(axis=1, dtype=np.float64)

    r = rng.standard_normal((C, n), dtype=np.float32)
    r *= np.sqrt(step_var).astype(np.float32)

    if cfg.jump_share > 0.0:
        e_iv = float(np.exp(cfg.sd ** 2 / 2.0))
        sig2_j = cfg.jump_share / (1.0 - cfg.jump_share) * e_iv \
            / JUMP_INTENSITY
        njumps = rng.poisson(JUMP_INTENSITY, size=C)
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

    return true_iv, path


LATENTS = [
    ("D1", "ar1", 0.98),
    ("D2", "arfima", 0.35), ("D2", "arfima", 0.45),
    ("D3", "fou", 0.08), ("D3", "fou", 0.10),
    ("D4", "fou", 0.30), ("D4", "fou", 0.50),
]
W_CONFIGS = [("W0", 1.0), ("W1", 1.0), ("W1", 3.0), ("W1", 10.0),
             ("W2", 1.0), ("W2", 3.0), ("W2", 10.0)]
NSR_SWEEP = [0.0] + list(np.logspace(-5, -1, 9))
JS_SWEEP = [0.0, 0.02, 0.05, 0.10, 0.20]
GEOMETRIES = {390: [13, 26, 78, 195], 1380: [23, 46, 138, 345]}
SD_FIXED = 0.7


def contamination_class(js, nsr):
    if js == 0.0 and nsr == 0.0:
        return "C0"
    if js > 0.0 and nsr == 0.0:
        return "C1"
    if js == 0.0 and nsr > 0.0:
        return "C2"
    return "C3"


def build_param_grid():
    """All (latent x W x contamination) combinations, priority-ordered
    C0 -> C2 -> C1 -> C3 so the primary threshold-map cells complete first."""
    cfgs = []
    for dgp, fam, sh in LATENTS:
        for w, ptt in W_CONFIGS:
            for js in JS_SWEEP:
                for nsr in NSR_SWEEP:
                    cfgs.append(DGP2Config(dgp, fam, sh, SD_FIXED, w, ptt,
                                           js, nsr))
    # Priority: the C0+C2 block per (latent, W) completes the primary
    # threshold-map rows for that combination across the full NSR sweep;
    # C1 next, C3 last. Within a class, blocks complete one (latent, W)
    # at a time so partial progress still yields whole threshold rows.
    prio = {"C0": 0, "C2": 0, "C1": 1, "C3": 2}
    cfgs.sort(key=lambda c: (prio[contamination_class(c.jump_share, c.nsr)],
                             c.dgp, c.shape, c.w, c.ptt, c.jump_share, c.nsr))
    return cfgs
