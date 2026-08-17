from dataclasses import replace
from datetime import UTC, datetime

import pytest

from model_drift.application import DriftMonitor
from model_drift.domain import AlarmPolicy, BatchIdentity, ColumnStatistic, MonitoringBatch


def identity(name, captured_at):
    return BatchIdentity(
        producer_project="producer",
        producer_version="1",
        dataset_id="dataset",
        dataset_version=name,
        contract_id="contract",
        contract_digest="sha256:" + "1" * 64,
        validated_manifest_digest="sha256:" + ("2" if name == "reference" else "3") * 64,
        model_id="model",
        model_version="1",
        model_artifact_digest="sha256:" + "4" * 64,
        captured_at=captured_at,
        artifact_digest="sha256:" + ("5" if name == "reference" else "6") * 64,
        feature_schema_digest="sha256:" + "7" * 64,
    )


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
        identity("reference", datetime(2026, 1, 1, tzinfo=UTC)),
    )
    current = MonitoringBatch(
        "current",
        {"feature": (1.0, 2.0), "prediction": (0.2, 0.8)},
        {"feature": "feature", "prediction": "prediction"},
        identity("current", datetime(2026, 2, 1, tzinfo=UTC)),
    )

    evaluation = monitor.evaluate(reference, current)

    assert evaluation.decision.alarm
    assert evaluation.duration_seconds >= 0
    assert telemetry.calls[0][0] == evaluation.decision


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("model_version", "model_version"),
        ("contract_digest", "contract_digest"),
        ("feature_schema_digest", "feature_schema_digest"),
    ],
)
def test_application_rejects_incompatible_identity(field, message):
    reference = MonitoringBatch(
        "reference",
        {"feature": (0.0, 1.0), "prediction": (0.2, 0.8)},
        {"feature": "feature", "prediction": "prediction"},
        identity("reference", datetime(2026, 1, 1, tzinfo=UTC)),
    )
    current_identity = replace(
        identity("current", datetime(2026, 2, 1, tzinfo=UTC)),
        **{field: "other" if not field.endswith("digest") else "sha256:" + "8" * 64},
    )
    current = MonitoringBatch(
        "current",
        {"feature": (1.0, 2.0), "prediction": (0.2, 0.8)},
        {"feature": "feature", "prediction": "prediction"},
        current_identity,
    )
    with pytest.raises(ValueError, match=message):
        DriftMonitor(RecordingDetector(), AlarmPolicy()).evaluate(reference, current)


def test_application_rejects_same_artifact_and_reverse_time():
    reference_identity = identity("reference", datetime(2026, 2, 1, tzinfo=UTC))
    reference = MonitoringBatch(
        "reference",
        {"feature": (0.0, 1.0), "prediction": (0.2, 0.8)},
        {"feature": "feature", "prediction": "prediction"},
        reference_identity,
    )
    current = MonitoringBatch(
        "current",
        {"feature": (1.0, 2.0), "prediction": (0.2, 0.8)},
        {"feature": "feature", "prediction": "prediction"},
        replace(
            identity("current", datetime(2026, 1, 1, tzinfo=UTC)),
            artifact_digest=reference_identity.artifact_digest,
        ),
    )
    with pytest.raises(ValueError, match="artifacts must differ"):
        DriftMonitor(RecordingDetector(), AlarmPolicy()).evaluate(reference, current)
