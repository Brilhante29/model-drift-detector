from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from model_drift.domain import MonitoringBatch

FEATURE_COUNT = 8


@dataclass(frozen=True)
class Scenario:
    name: str
    family: str
    seed: int
    expected_drift: bool
    scored: bool
    batch: MonitoringBatch


def _prediction(features: np.ndarray, noise: np.ndarray) -> np.ndarray:
    logits = (
        0.65 * features[:, 0]
        - 0.50 * features[:, 1]
        + 0.35 * features[:, 2]
        + noise
    )
    return 1.0 / (1.0 + np.exp(-logits))


def generate_batch(
    batch_id: str,
    seed: int,
    rows: int,
    family: str = "stable",
) -> MonitoringBatch:
    if rows < 2:
        raise ValueError("rows must be at least two")
    rng = np.random.default_rng(seed)
    features = rng.normal(0.0, 1.0, size=(rows, FEATURE_COUNT))
    noise = rng.normal(0.0, 0.20, size=rows)

    if family == "mean_shift":
        features[:, 0] += 0.65
    elif family == "scale_shift":
        features[:, 1] *= 1.80
    elif family == "correlation_only":
        independent = features[:, 4].copy()
        features[:, 4] = 0.85 * features[:, 3] + math.sqrt(1.0 - 0.85**2) * independent
    elif family not in {"stable", "prediction_shift"}:
        raise ValueError(f"unknown scenario family: {family}")

    prediction = _prediction(features, noise)
    if family == "prediction_shift":
        prediction = np.clip(prediction + 0.20, 0.0, 1.0)

    values = {
        f"feature_{index}": tuple(float(value) for value in features[:, index])
        for index in range(FEATURE_COUNT)
    }
    values["prediction_score"] = tuple(float(value) for value in prediction)
    roles = {f"feature_{index}": "feature" for index in range(FEATURE_COUNT)}
    roles["prediction_score"] = "prediction"
    return MonitoringBatch(batch_id=batch_id, values=values, roles=roles)


def build_scenarios(rows: int) -> tuple[MonitoringBatch, tuple[Scenario, ...]]:
    reference = generate_batch("reference", seed=42, rows=rows)
    definitions = (
        ("stable", tuple(range(100, 108)), False, True),
        ("mean_shift", tuple(range(200, 204)), True, True),
        ("scale_shift", tuple(range(300, 304)), True, True),
        ("prediction_shift", tuple(range(400, 404)), True, True),
        ("correlation_only", tuple(range(500, 502)), True, False),
    )
    scenarios: list[Scenario] = []
    for family, seeds, expected_drift, scored in definitions:
        for seed in seeds:
            name = f"{family}-{seed}"
            scenarios.append(
                Scenario(
                    name=name,
                    family=family,
                    seed=seed,
                    expected_drift=expected_drift,
                    scored=scored,
                    batch=generate_batch(name, seed=seed, rows=rows, family=family),
                )
            )
    return reference, tuple(scenarios)


def write_bundle(batch: MonitoringBatch, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=False)
    columns = list(batch.values)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(columns)
    for row_index in range(batch.row_count):
        writer.writerow(
            format(batch.values[column][row_index], ".17g") for column in columns
        )
    payload = buffer.getvalue().encode("utf-8")
    data_path = directory / "batch.csv"
    data_path.write_bytes(payload)

    manifest = {
        "schema_version": 1,
        "kind": "tabular-monitoring-batch",
        "batch_id": batch.batch_id,
        "captured_at": "2026-01-01T00:00:00Z",
        "producer": {
            "project": "model-drift-detector-fixtures",
            "version": "1.0.0",
        },
        "model": {"id": "mlops-end2end-demo", "version": "1"},
        "data": {
            "path": data_path.name,
            "format": "csv",
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "rows": batch.row_count,
        },
        "columns": [
            {
                "name": name,
                "role": batch.roles[name],
                "data_type": "float64",
                "nullable": False,
            }
            for name in columns
        ],
    }
    manifest_path = directory / "monitoring-batch.manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest_path
