from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator, FormatChecker
from pydantic import BaseModel, ConfigDict, Field, model_validator

from model_drift.domain import MONITORED_ROLES, BatchIdentity, MonitoringBatch

MAX_MANIFEST_BYTES = 1024 * 1024
MAX_DATA_BYTES = 64 * 1024 * 1024
MAX_ROWS = 1_000_000
SAFE_NAME = r"^[A-Za-z0-9][A-Za-z0-9._-]*$"
SAFE_COLUMN = r"^[A-Za-z_][A-Za-z0-9_]*$"
SHA256_PATTERN = r"^sha256:[a-f0-9]{64}$"
BARE_SHA256_PATTERN = r"^[a-f0-9]{64}$"
VALIDATED_SCHEMA_RESOURCE = "contracts/validated-batch-manifest-v1.schema.json"

CONTRACT_DOCUMENT: dict[str, Any] = {
    "schema_version": 1,
    "id": "monitoring-observation-batch-v1",
    "kind": "tabular-feature-and-prediction-observations",
    "required_roles": ["feature", "prediction"],
    "data_types": ["float64", "int64"],
    "nullable": False,
}
CONTRACT_BYTES = (
    json.dumps(CONTRACT_DOCUMENT, sort_keys=True, separators=(",", ":")) + "\n"
).encode()
CONTRACT_DIGEST = "sha256:" + hashlib.sha256(CONTRACT_BYTES).hexdigest()


class ProducerSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    project: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=128)


class ModelSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=128)
    artifact_sha256: str = Field(pattern=SHA256_PATTERN)


class DataSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    path: str = Field(pattern=SAFE_NAME)
    format: Literal["csv", "jsonl", "parquet"]
    sha256: str = Field(pattern=BARE_SHA256_PATTERN)
    bytes: int = Field(ge=1, le=MAX_DATA_BYTES)
    rows: int = Field(ge=1, le=MAX_ROWS)


class ColumnSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    name: str = Field(min_length=1, max_length=128, pattern=SAFE_COLUMN)
    role: Literal["feature", "prediction", "target", "timestamp", "identifier"]
    data_type: Literal["float64", "int64", "string", "boolean", "datetime"]
    nullable: bool


class ValidatedBatchRef(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    path: str = Field(pattern=SAFE_NAME)
    sha256: str = Field(pattern=SHA256_PATTERN)


class MonitoringBatchManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    kind: Literal["tabular-monitoring-batch"]
    batch_id: str = Field(min_length=1, max_length=128, pattern=SAFE_NAME)
    captured_at: datetime
    producer: ProducerSpec
    model: ModelSpec
    validated_batch: ValidatedBatchRef
    data: DataSpec
    columns: tuple[ColumnSpec, ...] = Field(min_length=2, max_length=256)

    @model_validator(mode="after")
    def validate_columns(self) -> MonitoringBatchManifest:
        names = [column.name for column in self.columns]
        if len(set(names)) != len(names):
            raise ValueError("manifest columns must have unique names")
        roles = {column.role for column in self.columns}
        if "feature" not in roles or "prediction" not in roles:
            raise ValueError("manifest requires feature and prediction roles")
        for column in self.columns:
            if column.role in MONITORED_ROLES:
                if column.data_type not in {"float64", "int64"}:
                    raise ValueError(f"monitored column {column.name} must be numeric")
                if column.nullable:
                    raise ValueError(f"monitored column {column.name} must not be nullable")
        return self


class ValidatedDatasetSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    version: str = Field(min_length=1)


class ValidatedContractSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str = Field(min_length=1)
    sha256: str = Field(pattern=SHA256_PATTERN)


class ValidatedArtifactSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    uri: str = Field(min_length=1)
    format: Literal["csv"]
    sha256: str = Field(pattern=SHA256_PATTERN)
    rows: int = Field(ge=0)


class ValidatedArtifactsSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    accepted: ValidatedArtifactSpec
    quarantine: ValidatedArtifactSpec


class ValidatedQualitySpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    status: Literal["passed"]
    total_rows: int = Field(ge=0)
    accepted_rows: int = Field(ge=0)
    rejected_rows: int = Field(ge=0)
    rejected_rows_percent: float = Field(ge=0, le=100)
    reason_counts: dict[str, int]


class ValidatedBatchManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    dataset: ValidatedDatasetSpec
    contract: ValidatedContractSpec
    source: ValidatedArtifactSpec
    artifacts: ValidatedArtifactsSpec
    quality: ValidatedQualitySpec
    generated_at: datetime


def _digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _read_bytes(path: Path, limit: int, label: str) -> bytes:
    if not path.is_file():
        raise ValueError(f"{label} is not a file: {path}")
    raw = path.read_bytes()
    if len(raw) > limit:
        raise ValueError(f"{label} exceeds maximum size")
    return raw


def _resolve_payload(manifest_path: Path, relative_name: str) -> Path:
    root = manifest_path.parent.resolve(strict=True)
    candidate = manifest_path.parent / relative_name
    resolved = candidate.resolve(strict=True)
    if resolved.parent != root:
        raise ValueError("artifact path escapes the manifest directory")
    if not resolved.is_file():
        raise ValueError("artifact payload is not a file")
    return resolved


def _verify_prefixed_artifact(
    manifest_path: Path,
    artifact: ValidatedArtifactSpec,
) -> Path:
    path = _resolve_payload(manifest_path, artifact.uri)
    payload = _read_bytes(path, MAX_DATA_BYTES, "validated artifact")
    if _digest(payload) != artifact.sha256:
        raise ValueError("validated artifact SHA-256 does not match manifest")
    return path


def _read_validated_manifest(
    monitoring_path: Path,
    reference: ValidatedBatchRef,
) -> tuple[ValidatedBatchManifest, str]:
    path = _resolve_payload(monitoring_path, reference.path)
    raw = _read_bytes(path, MAX_MANIFEST_BYTES, "validated batch manifest")
    actual_digest = _digest(raw)
    if actual_digest != reference.sha256:
        raise ValueError("validated batch manifest SHA-256 does not match")
    parsed = json.loads(raw)
    schema = json.loads(
        files("model_drift").joinpath(VALIDATED_SCHEMA_RESOURCE).read_text(encoding="utf-8")
    )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(parsed)
    manifest = ValidatedBatchManifest.model_validate_json(raw)
    if manifest.contract.id != CONTRACT_DOCUMENT["id"]:
        raise ValueError("validated batch uses an unknown data contract")
    if manifest.contract.sha256 != CONTRACT_DIGEST:
        raise ValueError("validated batch data contract digest does not match")
    quality = manifest.quality
    if quality.total_rows != quality.accepted_rows + quality.rejected_rows:
        raise ValueError("validated batch row reconciliation failed")
    if manifest.source.rows != quality.total_rows:
        raise ValueError("validated source row count does not match quality summary")
    if manifest.artifacts.accepted.rows != quality.accepted_rows:
        raise ValueError("accepted row count does not match quality summary")
    if manifest.artifacts.quarantine.rows != quality.rejected_rows:
        raise ValueError("quarantine row count does not match quality summary")
    if sum(quality.reason_counts.values()) < quality.rejected_rows:
        raise ValueError("quarantine reason counts do not cover rejected rows")
    expected_percent = (
        100.0 * quality.rejected_rows / quality.total_rows if quality.total_rows else 0.0
    )
    if abs(expected_percent - quality.rejected_rows_percent) > 1e-9:
        raise ValueError("rejected row percentage does not reconcile")
    _verify_prefixed_artifact(path, manifest.source)
    _verify_prefixed_artifact(path, manifest.artifacts.accepted)
    _verify_prefixed_artifact(path, manifest.artifacts.quarantine)
    return manifest, actual_digest


def _verify_payload(path: Path, spec: DataSpec) -> bytes:
    payload = _read_bytes(path, MAX_DATA_BYTES, "data payload")
    if len(payload) != spec.bytes:
        raise ValueError("data payload byte count does not match manifest")
    if hashlib.sha256(payload).hexdigest() != spec.sha256:
        raise ValueError("data payload SHA-256 does not match manifest")
    return payload


def _feature_schema_digest(columns: tuple[ColumnSpec, ...]) -> str:
    canonical = json.dumps(
        [column.model_dump(mode="json") for column in columns],
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return _digest(canonical)


def _parse_csv(
    payload: bytes,
    manifest: MonitoringBatchManifest,
    identity: BatchIdentity,
) -> MonitoringBatch:
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError("CSV payload must be valid UTF-8") from error

    reader = csv.DictReader(io.StringIO(text, newline=""))
    expected_names = [column.name for column in manifest.columns]
    if reader.fieldnames is None:
        raise ValueError("CSV payload is missing a header")
    if len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError("CSV payload has duplicate columns")
    if reader.fieldnames != expected_names:
        raise ValueError("CSV columns or order do not match manifest")

    monitored = [column for column in manifest.columns if column.role in MONITORED_ROLES]
    values: dict[str, list[float]] = {column.name: [] for column in monitored}
    rows = 0
    for row in reader:
        if None in row or any(row[name] is None for name in expected_names):
            raise ValueError("CSV row does not match the declared columns")
        rows += 1
        if rows > MAX_ROWS:
            raise ValueError("CSV row count exceeds maximum")
        for column in monitored:
            raw_value = row[column.name]
            if raw_value == "":
                raise ValueError(f"monitored column {column.name} contains null")
            try:
                values[column.name].append(float(raw_value))
            except ValueError as error:
                raise ValueError(
                    f"monitored column {column.name} contains a non-numeric value"
                ) from error

    if rows != manifest.data.rows:
        raise ValueError("CSV row count does not match manifest")
    roles = {column.name: column.role for column in monitored}
    return MonitoringBatch(
        batch_id=manifest.batch_id,
        values={name: tuple(column) for name, column in values.items()},
        roles=roles,
        identity=identity,
    )


def load_monitoring_batch(manifest_path: Path) -> MonitoringBatch:
    manifest_path = manifest_path.resolve(strict=True)
    raw_manifest = _read_bytes(manifest_path, MAX_MANIFEST_BYTES, "manifest")
    manifest = MonitoringBatchManifest.model_validate_json(raw_manifest)
    if manifest.data.format != "csv":
        raise ValueError("this consumer currently supports CSV payloads only")

    validated, validated_digest = _read_validated_manifest(
        manifest_path, manifest.validated_batch
    )
    payload_path = _resolve_payload(manifest_path, manifest.data.path)
    payload = _verify_payload(payload_path, manifest.data)
    accepted = validated.artifacts.accepted
    if (
        _resolve_payload(manifest_path.parent / manifest.validated_batch.path, accepted.uri)
        != payload_path
    ):
        raise ValueError("validated accepted artifact does not match monitoring data")
    if accepted.sha256 != "sha256:" + manifest.data.sha256:
        raise ValueError("validated accepted digest does not match monitoring data")
    if accepted.rows != manifest.data.rows:
        raise ValueError("validated accepted row count does not match monitoring data")

    identity = BatchIdentity(
        producer_project=manifest.producer.project,
        producer_version=manifest.producer.version,
        dataset_id=validated.dataset.id,
        dataset_version=validated.dataset.version,
        contract_id=validated.contract.id,
        contract_digest=validated.contract.sha256,
        validated_manifest_digest=validated_digest,
        model_id=manifest.model.id,
        model_version=manifest.model.version,
        model_artifact_digest=manifest.model.artifact_sha256,
        captured_at=manifest.captured_at,
        artifact_digest="sha256:" + manifest.data.sha256,
        feature_schema_digest=_feature_schema_digest(manifest.columns),
    )
    return _parse_csv(payload, manifest, identity)
