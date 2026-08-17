import numpy as np
import pytest

from model_drift.domain import MonitoringBatch
from model_drift.fixtures import generate_batch
from model_drift.statistics import ScipyKsDetector


def make_batch(name, values, role="feature"):
    identity = generate_batch(
        name, seed=42 if name == "reference" else 43, rows=len(values)
    ).identity
    return MonitoringBatch(
        batch_id=name,
        values={"feature": tuple(float(value) for value in values)},
        roles={"feature": role},
        identity=identity,
    )


def test_scipy_detector_exposes_ks_p_value_and_effect():
    rng = np.random.default_rng(42)
    reference = make_batch("reference", rng.normal(0, 1, 500))
    current = make_batch("current", rng.normal(1.0, 1, 500))

    result = ScipyKsDetector(minimum_samples=200).compare(reference, current)

    assert result[0].p_value < 0.001
    assert result[0].effect_size > 0.25


def test_scipy_detector_rejects_schema_and_size_mismatch():
    detector = ScipyKsDetector(minimum_samples=200)
    small = make_batch("small", range(10))
    with pytest.raises(ValueError, match="reference"):
        detector.compare(small, small)

    values = tuple(float(value) for value in range(200))
    reference = make_batch("reference", values)
    current = MonitoringBatch(
        batch_id="current",
        values={"other": values},
        roles={"other": "feature"},
        identity=generate_batch("current", seed=43, rows=200).identity,
    )
    with pytest.raises(ValueError, match="columns"):
        detector.compare(reference, current)


def test_scipy_detector_rejects_invalid_minimum():
    with pytest.raises(ValueError, match="at least two"):
        ScipyKsDetector(minimum_samples=1)
