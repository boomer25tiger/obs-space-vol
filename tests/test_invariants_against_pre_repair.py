"""S24, DECISIONS item 161. A pytest wrapper around the S06R invariant assertions.

`sessions/s06r-repair/tests/test_invariants.py` is an assertion library, not a
pytest suite: item 39 specifies guards called from inside the pipeline, so pytest
collects the module and reports that no tests ran. The paper claims that the five
invariants reproduce five silent pipeline failures in the pre-repair S05 output,
and until now nothing a reader could run demonstrated that.

Each test below does two things. It asserts the recorded failure count for its
assertion in the persisted S06R artifact, so a change in the artifact fails the
test rather than passing quietly. And it round-trips the assertion: the counts are
parsed out of a recorded failure message, a minimal input reproducing them is
built, the real assertion is called, and the counts it reports are compared with
the ones on record. A change in the library's behaviour therefore also fails.

The library itself is not modified and is not imported by name from this
directory; it is loaded from its own location so that the two stay separate.
"""

import importlib.util
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "sessions" / "s06r-repair" / "tests" / "test_invariants.py"
ARTIFACT = ROOT / "artifacts" / "s06r-repair" / "phase1_invariants_on_s05.csv"

# Counts recorded in artifacts/s06r-repair/S06R-report.md, the run of the
# five assertions against the pre-repair S05 artifacts.
RECORDED = {
    "assert_forecasts_positive": 46,
    "assert_loss_finite": 35,
    "assert_lambda_in_unit": 3683,
    "assert_range_inputs": 8,
    "assert_effective_M": 88,
}


def _load_library():
    spec = importlib.util.spec_from_file_location("s06r_invariants", LIB)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


inv = _load_library()


def _failures(name):
    d = pd.read_csv(ARTIFACT)
    return d[(d["test"] == name) & (d["result"] == "FAIL")]


def _ints(pattern, text):
    m = re.search(pattern, text)
    assert m, f"recorded message did not match {pattern!r}: {text!r}"
    return [int(g) for g in m.groups()]


def _raises(fn, *args, **kwargs):
    with pytest.raises(inv.InvariantViolation) as e:
        fn(*args, **kwargs)
    return str(e.value)


def test_forecast_positivity_fires_at_46():
    """Forecasts at or below the 1e-300 floor in the pre-repair S05 output."""
    rows = _failures("assert_forecasts_positive")
    assert len(rows) == RECORDED["assert_forecasts_positive"]
    nonfinite, nonpos, floored, size = _ints(
        r"(\d+) non-finite, (\d+) non-positive, (\d+) at or below the .+? floor, "
        r"of (\d+) forecasts", rows.iloc[0]["message"])
    a = np.concatenate([
        np.full(nonfinite, np.nan),
        np.zeros(nonpos),
        np.full(floored - nonpos, inv.FLOOR / 2),
        np.ones(size - nonfinite - floored),
    ])
    msg = _raises(inv.assert_forecasts_positive, a, "replay", "replay")
    assert _ints(r"(\d+) non-finite, (\d+) non-positive, (\d+) at or below", msg) \
        == [nonfinite, nonpos, floored]


def test_loss_finiteness_fires_at_35():
    """Non-finite entries reaching the MCS in the pre-repair S05 loss matrices."""
    rows = _failures("assert_loss_finite")
    assert len(rows) == RECORDED["assert_loss_finite"]
    bad, size = _ints(r"(\d+) non-finite of (\d+) entries", rows.iloc[0]["message"])
    ncol = 7
    a = np.zeros(size, dtype=float)
    a[:bad] = np.inf
    msg = _raises(inv.assert_loss_finite, a.reshape(size // ncol, ncol), "replay")
    assert _ints(r"(\d+) non-finite of (\d+) entries", msg) == [bad, size]


def test_lambda_unit_interval_fires_at_3683():
    """Reliability estimates outside [0,1] in the pre-repair S05 lambda surface."""
    rows = _failures("assert_lambda_in_unit")
    assert len(rows) == RECORDED["assert_lambda_in_unit"]
    n_out, size = _ints(r"(\d+) of (\d+) outside \[0,1\]", rows.iloc[0]["message"])
    offending = float(re.search(r"offending values \[([-\d.eE]+)", rows.iloc[0]["message"]).group(1))
    a = np.concatenate([np.full(n_out, offending), np.full(size - n_out, 0.5)])
    msg = _raises(inv.assert_lambda_in_unit, a, "replay", "replay")
    assert _ints(r"(\d+) of (\d+) outside", msg) == [n_out, size]


def test_range_inputs_fires_at_8():
    """Panels reaching Parkinson and Garman-Klass without high and low columns."""
    rows = _failures("assert_range_inputs")
    assert len(rows) == RECORDED["assert_range_inputs"]
    missing = re.search(r"panel is missing \[([^\]]+)\]", rows.iloc[0]["message"]).group(1)
    keys = [k.strip().strip("'\"") for k in missing.split(",")]
    panel = {k: np.ones(4) for k in ("high", "low", "close") if k not in keys}
    msg = _raises(inv.assert_range_inputs, panel, "replay")
    assert sorted(k.strip().strip("'\"") for k in
                  re.search(r"panel is missing \[([^\]]+)\]", msg).group(1).split(",")) == sorted(keys)


def test_effective_M_fires_at_88():
    """The M reaching an estimator differing from the computed effective count."""
    rows = _failures("assert_effective_M")
    assert len(rows) == RECORDED["assert_effective_M"]
    passed, mism, n = _ints(
        r"M passed = (\d+) but effective count differs in (\d+) of (\d+) windows",
        rows.iloc[0]["message"])
    eff = np.full(n, passed)
    eff[:mism] = passed - 1
    msg = _raises(inv.assert_effective_M, passed, eff, "replay", "replay")
    assert _ints(r"M passed = (\d+) but effective count differs in (\d+) of (\d+) windows",
                 msg) == [passed, mism, n]


def test_artifact_is_tracked_and_readable():
    """The wrapper must run from a fresh clone, so its artifact cannot be ignored."""
    assert ARTIFACT.exists(), f"{ARTIFACT} missing; the wrapper cannot run from a clone"
    assert LIB.exists(), f"{LIB} missing"
    d = pd.read_csv(ARTIFACT)
    assert set(RECORDED) <= set(d["test"].unique())
