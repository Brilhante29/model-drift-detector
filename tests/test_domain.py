import math

import pytest

from model_drift.domain import (
    AlarmPolicy,
    ColumnStatistic,
    MonitoringBatch,
)


def batch(values=None, roles=None):
    return MonitoringBatch(
        batch_id="batch",
        values=(
            values
            if values is not None
            else {"feature": (0.0, 1.0), "prediction": (0.2, 0.8)}
        ),
        roles=(
            roles
            if roles is not None
            else {"feature": "feature", "prediction": "prediction"}
        ),
    )


def test_monitoring_batch_is_immutable_and_reports_rows():
    result = batch()

    assert result.row_count == 2
    with pytest.raises(TypeError):
        result.values["other"] = (1.0,)


@pytest.mark.parametrize(
    ("values", "roles", "message"),
    [
        ({}, {}, "must contain monitored"),
        ({"feature": ()}, {"feature": "feature"}, "must not be empty"),
        (
            {"feature": (1.0,), "prediction": (0.1, 0.2)},
            {"feature": "feature", "prediction": "prediction"},
            "same row count",
        ),
        (
            {"feature": (math.inf,)},
            {"feature": "feature"},
            "non-finite",
        ),
        (
            {"feature": (1.0,)},
            {"other": "feature"},
            "same columns",
        ),
        (
            {"feature": (1.0,)},
            {"feature": "target"},
            "unsupported monitored role",
        ),
    ],
)
def test_monitoring_batch_rejects_invalid_content(values, roles, message):
    with pytest.raises(ValueError, match=message):
        batch(values, roles)


def test_holm_policy_requires_significance_and_effect():
    statistics = (
        ColumnStatistic("feature_0", "feature", p_value=0.001, effect_size=0.20),
        ColumnStatistic("feature_1", "feature", p_value=0.002, effect_size=0.02),
        ColumnStatistic("prediction", "prediction", p_value=0.90, effect_size=0.40),
    )

    result = AlarmPolicy(minimum_feature_drift_share=0.5).decide(statistics)

    assert result.alarm
    assert result.drifted_columns == ("feature_0",)
    assert result.feature_drift_share == 0.5
    assert not result.prediction_drifted
    assert result.columns[1].statistically_significant
    assert not result.columns[1].effect_exceeds_minimum


def test_holm_stops_rejecting_after_first_failed_hypothesis():
    statistics = (
        ColumnStatistic("feature_0", "feature", p_value=0.03, effect_size=0.30),
        ColumnStatistic("feature_1", "feature", p_value=0.04, effect_size=0.30),
        ColumnStatistic("prediction", "prediction", p_value=0.001, effect_size=0.30),
    )

    result = AlarmPolicy(minimum_feature_drift_share=1.0).decide(statistics)

    assert result.prediction_drifted
    assert not result.columns[0].statistically_significant
    assert not result.columns[1].statistically_significant


def test_prediction_drift_raises_alarm_without_feature_share():
    result = AlarmPolicy(minimum_feature_drift_share=1.0).decide(
        (
            ColumnStatistic("feature", "feature", 0.8, 0.01),
            ColumnStatistic("prediction", "prediction", 0.001, 0.30),
        )
    )

    assert result.alarm
    assert result.prediction_drifted


@pytest.mark.parametrize(
    "kwargs",
    [
        {"alpha": 0.0},
        {"minimum_effect": 1.1},
        {"minimum_feature_drift_share": 0.0},
        {"correction": "none"},
    ],
)
def test_alarm_policy_rejects_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        AlarmPolicy(**kwargs)


def test_policy_rejects_duplicate_or_missing_feature_statistics():
    policy = AlarmPolicy()
    duplicate = (
        ColumnStatistic("same", "feature", 0.1, 0.2),
        ColumnStatistic("same", "feature", 0.2, 0.2),
    )
    with pytest.raises(ValueError, match="unique"):
        policy.decide(duplicate)
    with pytest.raises(ValueError, match="feature"):
        policy.decide((ColumnStatistic("prediction", "prediction", 0.1, 0.2),))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"p_value": -0.1, "effect_size": 0.2},
        {"p_value": 0.1, "effect_size": 2.0},
        {"p_value": math.nan, "effect_size": 0.2},
    ],
)
def test_column_statistic_rejects_invalid_numbers(kwargs):
    with pytest.raises(ValueError):
        ColumnStatistic("feature", "feature", **kwargs)
