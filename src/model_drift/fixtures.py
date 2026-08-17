from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from model_drift.artifact import CONTRACT_DIGEST, CONTRACT_DOCUMENT
from model_drift.domain import BatchIdentity, MonitoringBatch

FEATURE_COUNT = 8
REFERENCE_CAPTURED_AT = datetime(2026, 1, 1, tzinfo=UTC)
CURRENT_CAPTURED_AT = datetime(2026, 2, 1, tzinfo=UTC)
MODEL_ID = "mlops-end2end-demo"
MODEL_VERSION = "1"
MODEL_ARTIFACT_DIGEST = (
    "sha256:" + hashlib.sha256(f"{MODEL_ID}:{MODEL_VERSION}".encode()).hexdigest()
)


@dataclass(frozen=True)
class Scenario:
    name: str
    family: str
    seed: int
    expected_drift: bool
    scored: bool
    batch: MonitoringBatch


def _prediction(features: np.ndarray, noise: np.ndarray) -> np.ndarray:
    logits = 0.65 * features[:, 0] - 0.50 * features[:, 1] + 0.35 * features[:, 2] + noise
    return 1.0 / (1.0 + np.exp(-logits))


def _columns(roles: dict[str, str]) -> list[dict[str, object]]:
    return [
        {
            "name": name,
            "role": role,
            "data_type": "float64",
            "nullable": False,
        }
        for name, role in roles.items()
    ]


def _csv_payload(values: dict[str, tuple[float, ...]]) -> bytes:
    columns = list(values)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(columns)
    rows = len(next(iter(values.values())))
    for row_index in range(rows):
        writer.writerow(format(values[column][row_index], ".17g") for column in columns)
    return buffer.getvalue().encode()


def _validated_manifest(
    *,
    batch_id: str,
    captured_at: datetime,
    payload_digest: str,
    payload_rows: int,
    quarantine_bytes: bytes,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "dataset": {"id": "customer-risk-observations", "version": batch_id},
        "contract": {"id": CONTRACT_DOCUMENT["id"], "sha256": CONTRACT_DIGEST},
        "source": {
            "uri": "batch.csv",
            "format": "csv",
            "sha256": payload_digest,
            "rows": payload_rows,
        },
        "artifacts": {
            "accepted": {
                "uri": "batch.csv",
                "format": "csv",
                "sha256": payload_digest,
                "rows": payload_rows,
            },
            "quarantine": {
                "uri": "quarantine.csv",
                "format": "csv",
                "sha256": "sha256:" + hashlib.sha256(quarantine_bytes).hexdigest(),
                "rows": 0,
            },
        },
        "quality": {
            "status": "passed",
            "total_rows": payload_rows,
            "accepted_rows": payload_rows,
            "rejected_rows": 0,
            "rejected_rows_percent": 0.0,
            "reason_counts": {},
        },
        "generated_at": captured_at.isoformat().replace("+00:00", "Z"),
    }


def _canonical_json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def generate_batch(
    batch_id: str,
    seed: int,
    rows: int,
    family: str = "stable",
    captured_at: datetime = CURRENT_CAPTURED_AT,
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
    payload = _csv_payload(values)
    payload_digest = "sha256:" + hashlib.sha256(payload).hexdigest()
    quarantine = (",".join(values) + "\n").encode()
    validated = _canonical_json(
        _validated_manifest(
            batch_id=batch_id,
            captured_at=captured_at,
            payload_digest=payload_digest,
            payload_rows=rows,
            quarantine_bytes=quarantine,
        )
    )
    schema_digest = (
        "sha256:"
        + hashlib.sha256(
            json.dumps(_columns(roles), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    identity = BatchIdentity(
        producer_project="mlops-end2end",
        producer_version="observation-export-v1",
        dataset_id="customer-risk-observations",
        dataset_version=batch_id,
        contract_id=str(CONTRACT_DOCUMENT["id"]),
        contract_digest=CONTRACT_DIGEST,
        validated_manifest_digest="sha256:" + hashlib.sha256(validated).hexdigest(),
        model_id=MODEL_ID,
        model_version=MODEL_VERSION,
        model_artifact_digest=MODEL_ARTIFACT_DIGEST,
        captured_at=captured_at,
        artifact_digest=payload_digest,
        feature_schema_digest=schema_digest,
    )
    return MonitoringBatch(
        batch_id=batch_id,
        values=values,
        roles=roles,
        identity=identity,
    )


def build_scenarios(rows: int) -> tuple[MonitoringBatch, tuple[Scenario, ...]]:
    reference = generate_batch(
        "reference", seed=42, rows=rows, captured_at=REFERENCE_CAPTURED_AT
    )
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
    payload = _csv_payload(dict(batch.values))
    data_digest = "sha256:" + hashlib.sha256(payload).hexdigest()
    if data_digest != batch.identity.artifact_digest:
        raise ValueError("fixture payload digest differs from batch identity")
    data_path = directory / "batch.csv"
    data_path.write_bytes(payload)

    quarantine = (",".join(batch.values) + "\n").encode()
    (directory / "quarantine.csv").write_bytes(quarantine)
    validated = _canonical_json(
        _validated_manifest(
            batch_id=batch.batch_id,
            captured_at=batch.identity.captured_at,
            payload_digest=data_digest,
            payload_rows=batch.row_count,
            quarantine_bytes=quarantine,
        )
    )
    validated_digest = "sha256:" + hashlib.sha256(validated).hexdigest()
    if validated_digest != batch.identity.validated_manifest_digest:
        raise ValueError("validated manifest digest differs from batch identity")
    validated_path = directory / "validated-batch.manifest.json"
    validated_path.write_bytes(validated)

    manifest = {
        "schema_version": 1,
        "kind": "tabular-monitoring-batch",
        "batch_id": batch.batch_id,
        "captured_at": batch.identity.captured_at.isoformat().replace("+00:00", "Z"),
        "producer": {
            "project": batch.identity.producer_project,
            "version": batch.identity.producer_version,
        },
        "model": {
            "id": batch.identity.model_id,
            "version": batch.identity.model_version,
            "artifact_sha256": batch.identity.model_artifact_digest,
        },
        "validated_batch": {
            "path": validated_path.name,
            "sha256": validated_digest,
        },
        "data": {
            "path": data_path.name,
            "format": "csv",
            "sha256": data_digest.removeprefix("sha256:"),
            "bytes": len(payload),
            "rows": batch.row_count,
        },
        "columns": _columns(dict(batch.roles)),
    }
    manifest_path = directory / "monitoring-batch.manifest.json"
    manifest_path.write_bytes(_canonical_json(manifest))
    return manifest_path
