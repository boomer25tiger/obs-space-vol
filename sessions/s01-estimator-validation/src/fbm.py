"""Exact simulation of stationary Gaussian processes by circulant embedding.

Davies-Harte circulant embedding, written from scratch on top of numpy's FFT
only. No external fBm package. If the embedding produces negative eigenvalues
the frequency and magnitude are recorded on the object rather than silently
approximated away; callers are expected to log them.
"""

import numpy as np


def fgn_acf(H, lags):
    """Autocovariance of fractional Gaussian noise with unit variance.

    gamma(k) = 0.5 * (|k+1|^2H - 2|k|^2H + |k-1|^2H), gamma(0) = 1.
    """
    k = np.asarray(lags, dtype=float)
    return 0.5 * (np.abs(k + 1) ** (2 * H) - 2 * np.abs(k) ** (2 * H)
                  + np.abs(k - 1) ** (2 * H))


class CirculantEmbedding:
    """Exact sampler for a stationary Gaussian series with a given acf.

    Parameters
    ----------
    acf : array of autocovariances at lags 0..N-1 for the series to generate.
    """

    def __init__(self, acf):
        acf = np.asarray(acf, dtype=float)
        self.N = len(acf)
        self.acf = acf
        # First row of the 2(N-1)-circulant: gamma_0..gamma_{N-1}, then the
        # mirrored interior lags gamma_{N-2}..gamma_1.
        c = np.concatenate([acf, acf[-2:0:-1]])
        self.m = len(c)
        lam = np.fft.fft(c).real
        tol = 1e-10 * max(lam.max(), 1.0)
        self.neg_eig_count = int((lam < -tol).sum())
        self.min_eig = float(lam.min())
        # Negative eigenvalues, when present, are clipped to zero; the count
        # and worst magnitude stay visible via neg_eig_count / min_eig.
        self.sqrt_lam = np.sqrt(np.clip(lam, 0.0, None))

    def sample(self, rng, size=1):
        """Draw `size` independent series of length N with the target acf."""
        m, half = self.m, self.m // 2
        U = rng.standard_normal((size, m))
        V = rng.standard_normal((size, m))
        w = np.empty((size, m), dtype=complex)
        w[:, 0] = np.sqrt(1.0 / m) * U[:, 0]
        w[:, half] = np.sqrt(1.0 / m) * U[:, half]
        k = np.arange(1, half)
        w[:, k] = np.sqrt(1.0 / (2 * m)) * (U[:, k] + 1j * V[:, k])
        w[:, m - k] = np.conj(w[:, k])
        x = np.fft.fft(self.sqrt_lam * w, axis=1).real
        return x[:, :self.N]


def fgn_sample(H, N, rng, size=1):
    """Exact fractional Gaussian noise (unit variance, unit spacing)."""
    emb = CirculantEmbedding(fgn_acf(H, np.arange(N)))
    return emb.sample(rng, size=size), emb


def fbm_sample(H, N, rng, size=1):
    """Exact fractional Brownian motion on integer times 1..N (B(0)=0 dropped)."""
    fgn, emb = fgn_sample(H, N, rng, size=size)
    return np.cumsum(fgn, axis=1), emb
