from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Protocol

from model_drift.domain import (
    AlarmPolicy,
    ColumnStatistic,
    DriftDecision,
    MonitoringBatch,
    validate_comparable_batches,
)


class StatisticalDetector(Protocol):
    def compare(
        self,
        reference: MonitoringBatch,
        current: MonitoringBatch,
    ) -> tuple[ColumnStatistic, ...]: ...


class DecisionTelemetry(Protocol):
    def record(self, decision: DriftDecision, duration_seconds: float) -> None: ...


class NullTelemetry:
    def record(self, decision: DriftDecision, duration_seconds: float) -> None:
        del decision, duration_seconds


@dataclass(frozen=True)
class Evaluation:
    decision: DriftDecision
    duration_seconds: float


class DriftMonitor:
    def __init__(
        self,
        detector: StatisticalDetector,
        policy: AlarmPolicy,
        telemetry: DecisionTelemetry | None = None,
    ) -> None:
        self.detector = detector
        self.policy = policy
        self.telemetry = telemetry or NullTelemetry()

    def evaluate(
        self,
        reference: MonitoringBatch,
        current: MonitoringBatch,
    ) -> Evaluation:
        validate_comparable_batches(reference, current)
        started = perf_counter()
        statistics = self.detector.compare(reference, current)
        decision = self.policy.decide(statistics)
        duration_seconds = perf_counter() - started
        self.telemetry.record(decision, duration_seconds)
        return Evaluation(decision=decision, duration_seconds=duration_seconds)
