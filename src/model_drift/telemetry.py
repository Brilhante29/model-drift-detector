from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

from model_drift.domain import DriftDecision


class PrometheusTelemetry:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.evaluations = Counter(
            "model_drift_evaluations_total",
            "Total monitoring evaluations by bounded outcome.",
            labelnames=("outcome",),
            registry=self.registry,
        )
        self.alarm_state = Gauge(
            "model_drift_alarm_state",
            "One when the latest evaluation raised an alarm.",
            registry=self.registry,
        )
        self.drifted_columns = Gauge(
            "model_drift_columns",
            "Number of columns marked as drifted in the latest evaluation.",
            registry=self.registry,
        )
        self.duration = Histogram(
            "model_drift_detection_duration_seconds",
            "Duration of the statistical comparison and alarm decision.",
            buckets=(0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
            registry=self.registry,
        )

    def record(self, decision: DriftDecision, duration_seconds: float) -> None:
        outcome = "alarm" if decision.alarm else "stable"
        self.evaluations.labels(outcome=outcome).inc()
        self.alarm_state.set(1 if decision.alarm else 0)
        self.drifted_columns.set(len(decision.drifted_columns))
        self.duration.observe(duration_seconds)

    def render(self) -> str:
        return generate_latest(self.registry).decode("utf-8")
