import pytest

from model_drift.fixtures import build_scenarios, generate_batch


def test_fixture_generation_is_deterministic_and_has_scored_truth():
    first = generate_batch("one", seed=42, rows=200)
    second = generate_batch("two", seed=42, rows=200)

    assert first.values == second.values
    reference, scenarios = build_scenarios(rows=200)
    assert reference.row_count == 200
    assert sum(scenario.scored for scenario in scenarios) == 20
    assert {scenario.family for scenario in scenarios} == {
        "stable",
        "mean_shift",
        "scale_shift",
        "prediction_shift",
        "correlation_only",
    }


def test_fixture_rejects_unknown_family_or_too_few_rows():
    with pytest.raises(ValueError, match="unknown"):
        generate_batch("bad", 42, 200, family="other")
    with pytest.raises(ValueError, match="at least two"):
        generate_batch("bad", 42, 1)
