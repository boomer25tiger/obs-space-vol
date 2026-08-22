"""Pre-registered unit tests U1-U5. A failure halts the session.

Tolerances are Monte Carlo error bounds plus, where relevant, documented
discretization allowances. They were set before the Phase-4 grid was run.
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fbm import CirculantEmbedding, fgn_acf, fbm_sample, fgn_sample  # noqa: E402
import estimators as est  # noqa: E402
from proxies import ohlc_proxies, rv_stats  # noqa: E402

RNG = lambda s: np.random.Generator(np.random.PCG64(s))


# ---------------------------------------------------------------- U1
@pytest.mark.parametrize("H", [0.1, 0.3, 0.5, 0.7, 0.9])
def test_u1_fbm_variance_scaling(H):
    """Var(B_H(t)) must scale as t^(2H)."""
    rng = RNG(101)
    paths, emb = fbm_sample(H, 128, rng, size=20000)
    assert emb.neg_eig_count == 0, f"negative embedding eigenvalues: {emb.min_eig}"
    for t in [8, 32, 128]:
        v = paths[:, t - 1].var()
        target = float(t) ** (2 * H)
        # MC rel. error of a variance over 20000 Gaussian draws ~ sqrt(2/20000)
        # = 1%; assert within 5% (5 sigma).
        assert abs(v / target - 1.0) < 0.05, (H, t, v / target)


# ---------------------------------------------------------------- U2
@pytest.mark.parametrize("H", [0.1, 0.3, 0.7, 0.9])
def test_u2_fgn_autocovariance(H):
    """Sample acf of exact fGn must match the closed form."""
    rng = RNG(202)
    N = 256
    fgn, emb = fgn_sample(H, N, rng, size=8000)
    target = fgn_acf(H, np.arange(6))
    fc = fgn - fgn.mean()
    for k in range(6):
        if k == 0:
            g = (fc * fc).mean()
        else:
            g = (fc[:, :-k] * fc[:, k:]).mean()
        # ~2e6 (correlated) products; absolute tolerance 0.01 on a unit-variance
        # process is > 5 MC sigma for every H tested.
        assert abs(g - target[k]) < 0.01, (H, k, g, target[k])


# ---------------------------------------------------------------- U3
@pytest.mark.parametrize("M", [13, 78, 195, 345])
def test_u3_var_rv_over_iv(M):
    """Constant vol, no noise: Var(RV/IV) = 2/M exactly for Gaussian returns."""
    rng = RNG(303)
    days = 200000
    z = rng.standard_normal((days, M))
    ratio = (z * z).mean(axis=1)          # RV/IV with IV = 1
    v = ratio.var()
    # Rel. MC error of the variance of a chi2_M/M mean ~ sqrt(k4/days)/ (2/M);
    # 4% covers > 5 sigma at days = 2e5 for all M tested.
    assert abs(v * M / 2.0 - 1.0) < 0.04, (M, v * M / 2.0)


# ---------------------------------------------------------------- U4
def test_u4_range_estimator_expectations():
    """Constant vol: E[Parkinson] and E[Garman-Klass] match sigma^2.

    Analytic expectations hold for the continuous-time range. A discrete
    n-step path shortens the observed range by ~ beta*sigma*sqrt(1/n) per
    extreme (beta ~= 0.5826, Broadie-Glasserman-Kou), i.e. ~1.6-2.5% downward
    bias on the squared range at n = 4096. The test window [0.95, 1.01]
    covers that documented discretization allowance plus >5 sigma of MC error
    while still catching any constant/factor implementation bug.
    """
    rng = RNG(404)
    n, days_total, chunk = 4096, 40000, 5000
    p_sum, gk_sum, cnt = 0.0, 0.0, 0
    for _ in range(days_total // chunk):
        r = rng.standard_normal((chunk, n)) * np.sqrt(1.0 / n)
        path = np.concatenate([np.zeros((chunk, 1)), np.cumsum(r, axis=1)],
                              axis=1)
        park, gk, rs, oc2 = ohlc_proxies(path)
        p_sum += park.sum()
        gk_sum += gk.sum()
        cnt += chunk
    assert 0.95 < p_sum / cnt < 1.01, p_sum / cnt
    assert 0.95 < gk_sum / cnt < 1.01, gk_sum / cnt


# ---------------------------------------------------------------- U5
def _direct_construction(rho, T, lam_target, sd, rng, M=195):
    """Data with a directly constructed, known lambda.

    Latent x has the given autocorrelation shape and sd; measurement errors
    are drawn iid so every estimator's assumptions hold by construction.
    lambda is computed from the realized sample itself so that shared
    sampling error cancels.
    """
    emb = CirculantEmbedding(rho)
    x = emb.sample(rng, size=1)[0] * sd
    v = x.var() * (1.0 - lam_target) / lam_target   # error variance
    e_full = rng.normal(0.0, np.sqrt(v), size=T)
    iv = np.exp(x)
    # Halves consistent with the full RV: RV = RV1 + RV2, each half carrying
    # an independent error of variance 2v (so the full log error variance ~ v).
    e1h = rng.normal(0.0, np.sqrt(2.0 * v), size=T)
    e2h = rng.normal(0.0, np.sqrt(2.0 * v), size=T)
    rv1 = 0.5 * iv * np.exp(e1h - v)
    rv2 = 0.5 * iv * np.exp(e2h - v)
    rv = iv * np.exp(e_full - v / 2.0)
    logrv = np.log(rv)
    rq = (M / 2.0) * rv * rv * v                     # makes E4 exact by design
    # Two extra proxies with independent errors for the three-cornered hat.
    y2 = x + rng.normal(0.0, np.sqrt(1.5 * v), size=T)
    y3 = x + rng.normal(0.0, np.sqrt(3.0 * v), size=T)
    lam_true = x.var() / logrv.var()
    return dict(x=x, logrv=logrv, rv=rv, rq=rq, rv1=rv1, rv2=rv2,
                y2=y2, y3=y3, lam_true=lam_true, M=M)


def test_u5_known_lambda_ar1():
    """AR(1) construction: E1 (arms a/b/c, all lag sets), E2, E3, E4 recover
    a known, directly constructed lambda within 5%.

    Tolerance: lambda_true is computed from the same realized sample, so the
    dominant shared sampling error cancels; residual MC error at T = 1e5 is
    well under 1% for these arms, and the exponential family (arm a) is
    exactly specified here. Arm d's fGn family is intentionally misspecified
    for an AR(1) signal; its values are printed for the record (captured in
    the report) and its correctness is asserted in the fGn construction test,
    where it is exactly specified.
    """
    rng = RNG(505)
    T = 100000
    phi = 0.98
    rho = phi ** np.arange(T, dtype=float)
    d = _direct_construction(rho, T, lam_target=0.8, sd=0.7, rng=rng)
    lam = d["lam_true"]

    grid = est.e1_grid(d["logrv"])
    for ls in est.LAG_SETS:
        for arm in ["a_exp", "b_pow", "c_spline"]:
            assert abs(grid[(arm, ls)] / lam - 1.0) < 0.05, (arm, ls, grid[(arm, ls)], lam)
        print(f"U5/AR1 arm d (misspecified, record only) {ls}: "
              f"recovery {grid[('d_model', ls)] / lam:.4f}")

    l2 = est.e2(d["logrv"], np.log(d["rv1"]), np.log(d["rv2"]))
    assert abs(l2 / lam - 1.0) < 0.05, l2

    Y = np.column_stack([d["logrv"], d["y2"], d["y3"]])
    yvar, pairvar, errcorr = est.e3_moments(Y, d["x"])
    off = np.abs(errcorr - np.eye(3)).max()
    assert off < 0.20, off   # errors independent by construction
    l3 = est.tch_lambda(yvar, pairvar, 0, 1, 2)
    assert abs(l3 / lam - 1.0) < 0.05, l3

    l4 = est.e4(d["rv"], d["rq"], d["logrv"], d["M"])
    assert abs(l4 / lam - 1.0) < 0.05, l4


def test_u5_known_lambda_fgn():
    """fGn(H=0.7) construction: arm d is exactly specified and must recover
    the known lambda; E2/E3/E4 must recover it too.

    Lag-0 extrapolation amplifies sampling noise in the autocovariances, so a
    single realization of arm d has MC sd of 4.5% (L1-5) to 13% (L2-22) at
    T = 1e5 even though the estimator is correctly specified (measured over
    30 independent realizations before this tolerance was set: mean recovery
    1.004-1.027). The assertion is therefore on the MEAN recovery over 15
    independent realizations: tolerance 0.05 (> 4 standard errors) for the
    lag sets including lag 1, and 0.09 for L2-22 whose per-draw sd is 2.5x
    larger. E2/E3/E4 are asserted per-realization at 5% as their MC error is
    far smaller.
    """
    rng = RNG(606)
    T = 100000
    rho = fgn_acf(0.7, np.arange(T))
    emb = CirculantEmbedding(rho)
    assert emb.neg_eig_count == 0, emb.min_eig

    rec = {ls: [] for ls in est.LAG_SETS}
    for rep in range(15):
        x = emb.sample(rng, size=1)[0] * 0.7
        v = x.var() * (1.0 - 0.75) / 0.75
        logrv = x + rng.normal(0.0, np.sqrt(v), size=T)
        lam = x.var() / logrv.var()
        grid = est.e1_grid(logrv)
        for ls in est.LAG_SETS:
            rec[ls].append(grid[("d_model", ls)] / lam)
    for ls in est.LAG_SETS:
        m = float(np.mean(rec[ls]))
        tol = 0.09 if ls == "L2-22" else 0.05
        print(f"U5/fGn arm d {ls}: mean recovery {m:.4f} "
              f"(per-draw sd {np.std(rec[ls]):.4f}, n=15)")
        assert abs(m - 1.0) < tol, (ls, m)

    d = _direct_construction(rho, T, lam_target=0.75, sd=0.7, rng=rng)
    lam = d["lam_true"]

    l2 = est.e2(d["logrv"], np.log(d["rv1"]), np.log(d["rv2"]))
    assert abs(l2 / lam - 1.0) < 0.05, l2

    Y = np.column_stack([d["logrv"], d["y2"], d["y3"]])
    yvar, pairvar, _ = est.e3_moments(Y, d["x"])
    l3 = est.tch_lambda(yvar, pairvar, 0, 1, 2)
    assert abs(l3 / lam - 1.0) < 0.05, l3

    l4 = est.e4(d["rv"], d["rq"], d["logrv"], d["M"])
    assert abs(l4 / lam - 1.0) < 0.05, l4
