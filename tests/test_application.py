from model_drift.application import DriftMonitor
from model_drift.domain import AlarmPolicy, ColumnStatistic, MonitoringBatch


class RecordingDetector:
    def compare(self, reference, current):
        assert reference.batch_id == "reference"
        assert current.batch_id == "current"
        return (
            ColumnStatistic("feature", "feature", 0.001, 0.30),
            ColumnStatistic("prediction", "prediction", 0.8, 0.01),
        )


class RecordingTelemetry:
    def __init__(self):
        self.calls = []

    def record(self, decision, duration_seconds):
        self.calls.append((decision, duration_seconds))


def test_application_orchestrates_ports_and_policy():
    telemetry = RecordingTelemetry()
    monitor = DriftMonitor(RecordingDetector(), AlarmPolicy(), telemetry)
    reference = MonitoringBatch(
        "reference",
        {"feature": (0.0, 1.0), "prediction": (0.2, 0.8)},
        {"feature": "feature", "prediction": "prediction"},
    )
    current = MonitoringBatch(
        "current",
        {"feature": (1.0, 2.0), "prediction": (0.2, 0.8)},
        {"feature": "feature", "prediction": "prediction"},
    )

    evaluation = monitor.evaluate(reference, current)

    assert evaluation.decision.alarm
    assert evaluation.duration_seconds >= 0
    assert telemetry.calls[0][0] == evaluation.decision
