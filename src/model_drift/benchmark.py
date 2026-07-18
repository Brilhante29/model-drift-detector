from __future__ import annotations

import json
import os
import platform
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import scipy

from model_drift.application import DriftMonitor
from model_drift.artifact import load_monitoring_batch
from model_drift.domain import AlarmPolicy, DriftDecision
from model_drift.fixtures import build_scenarios, write_bundle
from model_drift.statistics import ScipyKsDetector
from model_drift.telemetry import PrometheusTelemetry


def decision_to_dict(decision: DriftDecision) -> dict[str, Any]:
    return {
        "alarm": decision.alarm,
        "feature_drift_share": decision.feature_drift_share,
        "prediction_drifted": decision.prediction_drifted,
        "drifted_columns": list(decision.drifted_columns),
        "policy": dict(decision.policy),
        "columns": [
            {
                "name": column.name,
                "role": column.role,
                "p_value": column.p_value,
                "effect_size": column.effect_size,
                "adjusted_alpha": column.adjusted_alpha,
                "statistically_significant": column.statistically_significant,
                "effect_exceeds_minimum": column.effect_exceeds_minimum,
                "drifted": column.drifted,
            }
            for column in decision.columns
        ],
    }


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def run_benchmark(
    output_path: Path | None,
    rows: int = 2_000,
    command: str = "docker run --rm model-drift-detector",
) -> dict[str, Any]:
    if rows < 200:
        raise ValueError("benchmark rows must be at least 200")

    reference_source, scenarios = build_scenarios(rows)
    telemetry = PrometheusTelemetry()
    monitor = DriftMonitor(
        detector=ScipyKsDetector(minimum_samples=200),
        policy=AlarmPolicy(),
        telemetry=telemetry,
    )

    with tempfile.TemporaryDirectory(prefix="model-drift-") as temporary:
        root = Path(temporary)
        reference_manifest = write_bundle(reference_source, root / "reference")
        reference = load_monitoring_batch(reference_manifest)

        loaded_scenarios = []
        for scenario in scenarios:
            manifest = write_bundle(scenario.batch, root / scenario.name)
            loaded_scenarios.append((scenario, load_monitoring_batch(manifest)))

        monitor.evaluate(reference, loaded_scenarios[0][1])
        scenario_results: list[dict[str, Any]] = []
        for scenario, current in loaded_scenarios:
            evaluation = monitor.evaluate(reference, current)
            scenario_results.append(
                {
                    "name": scenario.name,
                    "family": scenario.family,
                    "seed": scenario.seed,
                    "expected_drift": scenario.expected_drift,
                    "scored": scenario.scored,
                    "alarm": evaluation.decision.alarm,
                    "correct": (
                        evaluation.decision.alarm == scenario.expected_drift
                        if scenario.scored
                        else None
                    ),
                    "duration_ms": evaluation.duration_seconds * 1_000.0,
                    "drifted_columns": list(evaluation.decision.drifted_columns),
                    "feature_drift_share": evaluation.decision.feature_drift_share,
                    "prediction_drifted": evaluation.decision.prediction_drifted,
                    "columns": decision_to_dict(evaluation.decision)["columns"],
                }
            )

    scored = [result for result in scenario_results if result["scored"]]
    true_positive = sum(
        result["expected_drift"] and result["alarm"] for result in scored
    )
    false_positive = sum(
        not result["expected_drift"] and result["alarm"] for result in scored
    )
    true_negative = sum(
        not result["expected_drift"] and not result["alarm"] for result in scored
    )
    false_negative = sum(
        result["expected_drift"] and not result["alarm"] for result in scored
    )
    precision = _ratio(true_positive, true_positive + false_positive)
    recall = _ratio(true_positive, true_positive + false_negative)
    f1 = _ratio(2 * precision * recall, precision + recall)
    false_positive_rate = _ratio(false_positive, false_positive + true_negative)
    durations = np.asarray(
        [float(result["duration_ms"]) for result in scored],
        dtype=np.float64,
    )
    blind_spots = [result for result in scenario_results if not result["scored"]]
    blind_spot_detection_rate = _ratio(
        sum(result["alarm"] for result in blind_spots),
        len(blind_spots),
    )

    result = {
        "project": "model-drift-detector",
        "metric": "drift_alarm_f1",
        "value": f1,
        "unit": "ratio",
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "command": command,
        "repeat": len(scored),
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "rows_per_batch": rows,
            "scored_scenarios": len(scored),
            "container": Path("/.dockerenv").exists(),
            "image_id": os.getenv("IMAGE_ID", "not-recorded"),
        },
        "summary": {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "false_positive_rate": false_positive_rate,
            "detection_runtime_p50_ms": float(np.percentile(durations, 50)),
            "detection_runtime_p95_ms": float(np.percentile(durations, 95)),
            "blind_spot_detection_rate": blind_spot_detection_rate,
        },
        "metrics": {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "true_negative": true_negative,
            "false_negative": false_negative,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "false_positive_rate": false_positive_rate,
            "detection_runtime_p50_ms": float(np.percentile(durations, 50)),
            "detection_runtime_p95_ms": float(np.percentile(durations, 95)),
            "blind_spot_detection_rate": blind_spot_detection_rate,
        },
        "proof": {
            "reference_seed": 42,
            "scenario_truth_defined_before_detection": True,
            "monitoring_batch_contract_verified": True,
            "contract": ".portfolio/contracts/monitoring-batch.schema.json",
            "statistical_test": "two-sided Kolmogorov-Smirnov",
            "multiple_test_correction": "Holm family-wise error control",
            "alpha": 0.05,
            "minimum_ks_effect": 0.10,
            "minimum_feature_drift_share": 0.125,
            "warmup_evaluations": 1,
            "ground_truth_available_for_model_performance": False,
            "claim_boundary": "data and prediction drift proxy only",
            "documented_blind_spot": "correlation-only multivariate drift",
            "prometheus_exported": "model_drift_evaluations_total"
            in telemetry.render(),
            "scenario_matrix": scenario_results,
        },
        "failures": 0,
    }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return result
