"""S06R invariant assertions (DECISIONS item 39).

Five guards, written before any repair, importable and called from INSIDE
the pipeline rather than as a separate check. Each takes the object it
guards and raises InvariantViolation naming the cell, the model and the
offending count. A violation halts; nothing here warns.
"""

import numpy as np

FLOOR = 1e-300


class InvariantViolation(AssertionError):
    pass


def assert_forecasts_positive(F, cell, model=None):
    """Every forecast strictly positive and finite after filtering, and no
    value sitting at or below the 1e-300 floor."""
    a = np.asarray(F, dtype=float)
    nonfinite = int((~np.isfinite(a)).sum())
    nonpos = int((a <= 0).sum())
    floored = int((a <= FLOOR).sum())
    if nonfinite or nonpos or floored:
        raise InvariantViolation(
            f"[assert_forecasts_positive] cell={cell} model={model}: "
            f"{nonfinite} non-finite, {nonpos} non-positive, {floored} at or "
            f"below the {FLOOR:g} floor, of {a.size} forecasts; "
            f"min={np.nanmin(a) if a.size else float('nan'):.6g}")
    return True


def assert_loss_finite(L, cell, models=None):
    """Every entry of the loss matrix finite before it reaches any MCS."""
    a = np.asarray(L, dtype=float)
    bad = ~np.isfinite(a)
    if bad.any():
        per_col = bad.sum(axis=0) if a.ndim == 2 else np.array([bad.sum()])
        names = models if models is not None else list(range(len(per_col)))
        detail = ", ".join(f"{n}={int(c)}" for n, c in zip(names, per_col)
                           if c)
        raise InvariantViolation(
            f"[assert_loss_finite] cell={cell}: {int(bad.sum())} non-finite "
            f"of {a.size} entries (shape {a.shape}); by model: {detail}")
    return True


def assert_lambda_in_unit(lam, cell, estimator):
    """Lambda within [0, 1] inclusive."""
    a = np.asarray(lam, dtype=float)
    bad = ~((a >= 0.0) & (a <= 1.0)) | ~np.isfinite(a)
    if np.any(bad):
        vals = np.atleast_1d(a)[np.atleast_1d(bad)]
        raise InvariantViolation(
            f"[assert_lambda_in_unit] cell={cell} estimator={estimator}: "
            f"{int(np.sum(bad))} of {a.size} outside [0,1]; "
            f"offending values {np.round(vals[:8], 6).tolist()}")
    return True


def assert_range_inputs(panel, cell):
    """The panel supplied to Parkinson and Garman-Klass must carry distinct
    high and low columns that are not derived from closes."""
    if not isinstance(panel, dict):
        raise InvariantViolation(
            f"[assert_range_inputs] cell={cell}: expected a dict with "
            f"'high'/'low'/'close' grids, got {type(panel).__name__}")
    missing = [k for k in ("high", "low", "close") if k not in panel]
    if missing:
        raise InvariantViolation(
            f"[assert_range_inputs] cell={cell}: panel is missing {missing}; "
            "range estimators cannot be built from closes alone")
    hi = np.asarray(panel["high"], float)
    lo = np.asarray(panel["low"], float)
    cl = np.asarray(panel["close"], float)
    if hi.shape != cl.shape or lo.shape != cl.shape:
        raise InvariantViolation(
            f"[assert_range_inputs] cell={cell}: shape mismatch "
            f"high{hi.shape} low{lo.shape} close{cl.shape}")
    if np.array_equal(hi, cl) or np.array_equal(lo, cl):
        raise InvariantViolation(
            f"[assert_range_inputs] cell={cell}: high or low is identical to "
            "close, so the range series is derived from closes")
    bad = int((hi < lo).sum())
    if bad:
        raise InvariantViolation(
            f"[assert_range_inputs] cell={cell}: {bad} bars with high < low")
    return True


def assert_effective_M(M_passed, M_effective, cell, estimator=None):
    """The M argument reaching any estimator equals the computed effective
    sub-bar count."""
    eff = np.asarray(M_effective)
    if eff.ndim == 0:
        mism = int(eff != M_passed)
        n = 1
    else:
        mism = int((eff != M_passed).sum())
        n = eff.size
    if mism:
        u = np.unique(np.atleast_1d(eff))
        raise InvariantViolation(
            f"[assert_effective_M] cell={cell} estimator={estimator}: "
            f"M passed = {M_passed} but effective count differs in {mism} of "
            f"{n} windows; distinct effective values "
            f"{u[:8].tolist()}{'...' if u.size > 8 else ''}")
    return True
