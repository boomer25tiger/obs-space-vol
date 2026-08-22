"""Daily volatility proxies computed from intraday observed log-price paths.

All proxies target the daily integrated variance IV_t. Range proxies use the
day's observed open/high/low/close. Bipower variation is computed at the
finest sampling frequency of the geometry (documented implementation choice;
the pre-registration lists bipower variation once, not per M).
"""

import numpy as np

LOG_FLOOR = 1e-14  # floor before taking logs; occurrences are counted


def bucket_returns(path, M):
    """Returns at M sub-intervals from the (T, n+1) cumulative path."""
    n = path.shape[1] - 1
    stride = n // M
    if stride * M != n:
        raise ValueError(f"M={M} does not divide n={n}")
    b = path[:, ::stride]
    return np.diff(b, axis=1)


def rv_stats(path, M):
    """RV, RQ and contiguous-half RVs at M sub-intervals."""
    r = bucket_returns(path, M)
    r2 = r * r
    rv = r2.sum(axis=1, dtype=np.float64)
    rq = (M / 3.0) * (r2 * r2).sum(axis=1, dtype=np.float64)
    h = M // 2
    rv_h1 = r2[:, :h].sum(axis=1, dtype=np.float64)
    rv_h2 = r2[:, h:].sum(axis=1, dtype=np.float64)
    return rv, rq, rv_h1, rv_h2


def bipower(path, M):
    r = np.abs(bucket_returns(path, M))
    return (np.pi / 2.0) * (M / (M - 1.0)) \
        * (r[:, 1:] * r[:, :-1]).sum(axis=1, dtype=np.float64)


def ohlc_proxies(path):
    """Parkinson, Garman-Klass, Rogers-Satchell, squared open-to-close."""
    o = path[:, 0].astype(np.float64)
    h = path.max(axis=1).astype(np.float64) - o
    l = path.min(axis=1).astype(np.float64) - o
    c = path[:, -1].astype(np.float64) - o
    park = (h - l) ** 2 / (4.0 * np.log(2.0))
    gk = 0.5 * (h - l) ** 2 - (2.0 * np.log(2.0) - 1.0) * c * c
    rs = h * (h - c) + l * (l - c)
    oc2 = c * c
    return park, gk, rs, oc2


def safe_log(a, counter):
    """Log with a floor; counter is a 1-element list accumulating floor hits."""
    n_bad = int((a < LOG_FLOOR).sum())
    if n_bad:
        counter[0] += n_bad
        a = np.maximum(a, LOG_FLOOR)
    return np.log(a)
