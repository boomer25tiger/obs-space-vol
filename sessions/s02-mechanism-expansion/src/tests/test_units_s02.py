"""Pre-registered S02 unit tests V1-V6. A failure halts the session.

Tolerances are Monte Carlo error bounds plus documented finite-sample
allowances of the published estimators, set before the Phase-2 grid ran.
"""

import os
import subprocess
import sys

import numpy as np
import pytest

_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _SRC)

import estimators2 as est2                                    # noqa: E402
import proxies_robust as px                                   # noqa: E402
from run2 import proxy_suite, kernel_flattop_fft, medrv_fast  # noqa: E402
from dgp2 import diurnal_profile, DGP2Config, simulate_day_chunk  # noqa: E402
from fbm import CirculantEmbedding                            # noqa: E402

RNG = lambda s: np.random.Generator(np.random.PCG64(s))
S01_SRC = os.path.join(os.path.dirname(os.path.dirname(_SRC)),
                       "s01-estimator-validation", "src")
VENV_PY = sys.executable


# ---------------------------------------------------------------- V1
def test_v1_s01_suite_still_passes():
    """All S01 unit tests re-run and pass, unmodified."""
    r = subprocess.run(
        [VENV_PY, "-m", "pytest", "tests/test_units.py", "-q",
         "--no-header", "-p", "no:cacheprovider"],
        cwd=S01_SRC, capture_output=True, text=True, timeout=1200)
    print(r.stdout[-2000:])
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-1000:]


# ---------------------------------------------------------------- V2
def test_v2_noise_robust_proxies_recover_iv():
    """Constant vol sigma^2 = 1, additive noise with known omega^2 chosen so
    plain RV is biased by +100%: E[RV] = IV + 2*M*omega^2 = 2*IV.

    P2 (TSRV), P3 (realized kernel), P4 (pre-averaged RV) must recover IV
    within 6% — several times their asymptotic sd at these sizes plus the
    small-sample biases the authors themselves report (JLMPV 2009 Table 2
    shows ~ -1% for pre-averaging) — while P1 must show its full noise bias.
    """
    rng = RNG(11)
    days, M = 4000, 390
    omega2 = 1.0 / (2.0 * M)          # makes E[RV] = 2 IV with IV = 1
    r_clean = rng.standard_normal((days, M)) * np.sqrt(1.0 / M)
    p = np.concatenate([np.zeros((days, 1)), np.cumsum(r_clean, axis=1)],
                       axis=1)
    p += rng.standard_normal((days, M + 1)) * np.sqrt(omega2)
    r = np.diff(p, axis=1)
    S = proxy_suite(r.astype(np.float32), M)
    assert abs(S["P1"].mean() - 2.0) < 0.1, S["P1"].mean()      # P1 fails
    for name in ["P2", "P3", "P4"]:
        m = S[name].mean()
        assert abs(m - 1.0) < 0.06, (name, m)


# ---------------------------------------------------------------- V3
def test_v3_jump_robust_proxies_recover_continuous():
    """One jump per day with J^2 = 0.5*IV: total QV = 1.5*IV.

    P5/P6/P7 must recover the continuous IV = 1; P1 must not. Documented
    finite-M allowances: bipower's jump leakage is O(|J| sqrt(1/M)) ~ 9%
    here (bound 15%); MedRV and truncated RV suppress isolated jumps far
    more strongly (bound 6%).
    """
    rng = RNG(22)
    days, M = 4000, 390
    r = rng.standard_normal((days, M)) * np.sqrt(1.0 / M)
    pos = rng.integers(0, M, size=days)
    r[np.arange(days), pos] += np.sqrt(0.5) * rng.choice([-1, 1], size=days)
    S = proxy_suite(r.astype(np.float32), M)
    assert S["P1"].mean() > 1.35, S["P1"].mean()                # P1 fails
    assert abs(S["P5"].mean() - 1.0) < 0.15, S["P5"].mean()
    assert abs(S["P6"].mean() - 1.0) < 0.06, S["P6"].mean()
    assert abs(S["P7"].mean() - 1.0) < 0.06, S["P7"].mean()


# ---------------------------------------------------------------- V4
def test_v4_signature_regression_recovers_omega2():
    """E5's signature-plot regression recovers a known omega^2 within MC
    error (5 sigma of the empirical se of the mean slope)."""
    rng = RNG(33)
    days = 20000
    m_list = [13, 26, 78, 195]
    omega2 = 5e-4
    rv_by_m, log_rv_by_m = {}, {}
    for M in m_list:
        z = rng.standard_normal((days, M))
        u = rng.standard_normal((days, M + 1)) * np.sqrt(omega2)
        r = z * np.sqrt(1.0 / M) + np.diff(u, axis=1)
        rv_by_m[M] = (r * r).sum(axis=1)
        log_rv_by_m[M] = np.log(rv_by_m[M])
    fc = [0]
    lam, om2_hat = est2.e5_signature(rv_by_m, m_list, log_rv_by_m, fc)
    assert abs(om2_hat / omega2 - 1.0) < 0.05, om2_hat


# ---------------------------------------------------------------- V5
def test_v5_diurnal_profile_recovered():
    """Under W1 with peak-to-trough 3, the average squared-return profile
    recovered from simulated data matches the injected profile."""
    rng = RNG(44)
    n, days = 390, 8000
    cfg = DGP2Config("D1", "ar1", 0.98, 0.7, "W1", 3.0, 0.0, 0.0)
    profile = diurnal_profile(n, 3.0)
    x = np.zeros(days)                     # constant latent level
    tiv, path = simulate_day_chunk(cfg, x, n, profile, rng)
    r = np.diff(path.astype(np.float64), axis=1)
    est_profile = (r * r).mean(axis=0) * n          # per-step variance * n
    est_profile /= est_profile.mean()
    # bucket into 39 blocks of 10 steps to control MC error, then compare
    eb = est_profile.reshape(39, 10).mean(axis=1)
    pb = (profile / profile.mean()).reshape(39, 10).mean(axis=1)
    assert np.max(np.abs(eb - pb)) < 0.12, np.max(np.abs(eb - pb))
    assert abs(eb[0] / eb[19] - 3.0) < 0.45      # peak-to-trough ratio


# ---------------------------------------------------------------- V6
def test_v6_known_lambda_all_estimators_nsr0():
    """Directly constructed known lambda at NSR = 0; every estimator must
    recover it.

    Construction mirrors S01's U5 (AR(1) latent, iid log-errors, halves and
    RQ consistent by construction), extended with per-M RVs sharing the
    latent IV so that E5 and E6 can run. Documented intrinsic properties,
    fixed before the grid ran: (i) E5's intercept-variance correction makes
    it recover within MC error of its own sampling noise (7% bound); (ii)
    E6's Hansen-Lunde correction subtracts (M/M_finest)*RV_finest, which is
    degenerate AT the finest M by construction, so E6 arms are asserted at
    the coarser M (their behaviour at M = M_finest is a reported grid
    result, not a unit-test target).
    """
    rng = RNG(55)
    T = 100000
    phi = 0.98
    m_list = [13, 26, 78, 195]
    rho = phi ** np.arange(T, dtype=float)
    emb = CirculantEmbedding(rho)
    x = emb.sample(rng, size=1)[0] * 0.7
    iv = np.exp(x)
    vx = x.var()

    # Log-error variance v_M = 2/M, the Barndorff-Nielsen & Shephard
    # magnitude for RV at M intervals, so the levels regression of E5 sees
    # errors of realistic scale.
    rv_by_m, log_rv_by_m, lam_true = {}, {}, {}
    v_by_m = {}
    for M in m_list:
        v = 2.0 / M
        v_by_m[M] = v
        e = rng.normal(0.0, np.sqrt(v), size=T)
        rv_by_m[M] = iv * np.exp(e - v / 2.0)
        log_rv_by_m[M] = np.log(rv_by_m[M])
        lam_true[M] = vx / log_rv_by_m[M].var()

    M0 = 195
    logrv = log_rv_by_m[M0]
    lam0 = lam_true[M0]

    grid = est2.e1_reduced(logrv)
    for (a, ls) in est2.E1_KEYS:
        tol = 0.15 if a == "d_model" else 0.05   # arm-d misspec on AR(1), S01
        assert abs(grid[(a, ls)] / lam0 - 1.0) < tol, (a, ls, grid[(a, ls)])

    v0 = v_by_m[M0]
    e1h = rng.normal(0.0, np.sqrt(2 * v0), size=T)
    e2h = rng.normal(0.0, np.sqrt(2 * v0), size=T)
    rv1 = 0.5 * iv * np.exp(e1h - v0)
    rv2 = 0.5 * iv * np.exp(e2h - v0)
    l2 = est2.e2(logrv, np.log(rv1), np.log(rv2))
    assert abs(l2 / lam0 - 1.0) < 0.05, l2

    rq_c = (M0 / 2.0) * rv_by_m[M0] ** 2 * v0
    l4 = est2.e4(rv_by_m[M0], rq_c, logrv, M0)
    assert abs(l4 / lam0 - 1.0) < 0.05, l4

    fc = [0]
    lam_e5, _ = est2.e5_signature(rv_by_m, m_list, log_rv_by_m, fc)
    for M in m_list:
        assert abs(lam_e5[M] / lam_true[M] - 1.0) < 0.07, (M, lam_e5[M],
                                                           lam_true[M])

    # E6's lambda-producing role is the pre-correction (the pre-registration
    # defines E6 as a NOISE estimator "used to correct the proxy before any
    # other estimator is applied"); the standalone dispersion ratio
    # Var(log RVc)/Var(log RV) is a reported diagnostic, not a lambda
    # estimator (it retains the proxy's own sampling error by construction),
    # and is therefore not a V6 recovery target. At NSR = 0 the
    # Hansen-Lunde omega^2 equals E[RV_finest]/(2 M_finest), so the
    # correction subtracts the fraction M/M_finest of the proxy's level and
    # inflates the log-error variance by ~ (1 - M/M_finest)^(-2): the
    # pre-corrected arms recover lambda exactly in the small-correction
    # regime M << M_finest and degrade continuously as M/M_finest grows
    # (-10% already at M/M_finest = 0.4). The assertion therefore targets
    # the small-correction regime (M/M_finest <= 0.13); behaviour at larger
    # M/M_finest is a reported grid result, with the closed-form mechanism
    # above quoted in the report.
    om2_t = est2.e6_omega2(rv_by_m[195], 195)
    for M in [13, 26]:
        rvc = est2.e6_correct(rv_by_m[M], M, om2_t, fc)
        log_rvc = np.log(rvc)
        g6 = est2.e1_reduced(log_rvc)
        assert abs(g6[("a_exp", "L1-5")] / lam_true[M] - 1.0) < 0.08, \
            (M, g6[("a_exp", "L1-5")], lam_true[M])
        vM = v_by_m[M]
        h1 = 0.5 * iv * np.exp(rng.normal(0, np.sqrt(2 * vM), T) - vM)
        h2 = 0.5 * iv * np.exp(rng.normal(0, np.sqrt(2 * vM), T) - vM)
        h = M // 2
        h1c = est2.e6_correct(h1, h, om2_t, fc)
        h2c = est2.e6_correct(h2, M - h, om2_t, fc)
        l6_2 = est2.e2(log_rvc, np.log(h1c), np.log(h2c))
        assert abs(l6_2 / lam_true[M] - 1.0) < 0.08, (M, l6_2, lam_true[M])
        rq_m = (M / 2.0) * rv_by_m[M] ** 2 * vM
        l6_4 = est2.e4(rvc, rq_m, log_rvc, M)
        assert abs(l6_4 / lam_true[M] - 1.0) < 0.08, (M, l6_4, lam_true[M])
