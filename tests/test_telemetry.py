from model_drift.domain import AlarmPolicy, ColumnStatistic
from model_drift.telemetry import PrometheusTelemetry


def test_prometheus_telemetry_uses_bounded_labels():
    decision = AlarmPolicy().decide(
        (
            ColumnStatistic("feature", "feature", 0.001, 0.3),
            ColumnStatistic("prediction", "prediction", 0.8, 0.01),
        )
    )
    telemetry = PrometheusTelemetry()

    telemetry.record(decision, 0.012)
    output = telemetry.render()

    assert 'model_drift_evaluations_total{outcome="alarm"} 1.0' in output
    assert "model_drift_alarm_state 1.0" in output
    assert "model_drift_columns 1.0" in output
    assert "batch_id" not in output
