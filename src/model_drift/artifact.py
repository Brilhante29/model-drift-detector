from __future__ import annotations

import csv
import hashlib
import io
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from model_drift.domain import MONITORED_ROLES, MonitoringBatch


MAX_MANIFEST_BYTES = 1024 * 1024
MAX_DATA_BYTES = 64 * 1024 * 1024
MAX_ROWS = 1_000_000
SAFE_NAME = r"^[A-Za-z0-9][A-Za-z0-9._-]*$"
SAFE_COLUMN = r"^[A-Za-z_][A-Za-z0-9_]*$"
SHA256_PATTERN = r"^[a-f0-9]{64}$"


class ProducerSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    project: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=128)


class ModelSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=128)


class DataSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    path: str = Field(pattern=SAFE_NAME)
    format: Literal["csv", "jsonl", "parquet"]
    sha256: str = Field(pattern=SHA256_PATTERN)
    bytes: int = Field(ge=1, le=MAX_DATA_BYTES)
    rows: int = Field(ge=1, le=MAX_ROWS)


class ColumnSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    name: str = Field(min_length=1, max_length=128, pattern=SAFE_COLUMN)
    role: Literal["feature", "prediction", "target", "timestamp", "identifier"]
    data_type: Literal["float64", "int64", "string", "boolean", "datetime"]
    nullable: bool


class MonitoringBatchManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    kind: Literal["tabular-monitoring-batch"]
    batch_id: str = Field(min_length=1, max_length=128, pattern=SAFE_NAME)
    captured_at: datetime
    producer: ProducerSpec
    model: ModelSpec
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
                    raise ValueError(
                        f"monitored column {column.name} must be numeric"
                    )
                if column.nullable:
                    raise ValueError(
                        f"monitored column {column.name} must not be nullable"
                    )
        return self


def _read_manifest(path: Path) -> MonitoringBatchManifest:
    if not path.is_file():
        raise ValueError(f"manifest is not a file: {path}")
    raw = path.read_bytes()
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ValueError("manifest exceeds maximum size")
    return MonitoringBatchManifest.model_validate_json(raw)


def _resolve_payload(manifest_path: Path, relative_name: str) -> Path:
    root = manifest_path.parent.resolve(strict=True)
    candidate = manifest_path.parent / relative_name
    resolved = candidate.resolve(strict=True)
    if resolved.parent != root:
        raise ValueError("data path escapes the manifest directory")
    if not resolved.is_file():
        raise ValueError("data payload is not a file")
    return resolved


def _verify_payload(path: Path, spec: DataSpec) -> bytes:
    actual_size = path.stat().st_size
    if actual_size > MAX_DATA_BYTES:
        raise ValueError("data payload exceeds maximum size")
    if actual_size != spec.bytes:
        raise ValueError("data payload byte count does not match manifest")
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != spec.sha256:
        raise ValueError("data payload SHA-256 does not match manifest")
    return payload


def _parse_csv(
    payload: bytes,
    manifest: MonitoringBatchManifest,
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

    monitored = [
        column for column in manifest.columns if column.role in MONITORED_ROLES
    ]
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
    )


def load_monitoring_batch(manifest_path: Path) -> MonitoringBatch:
    manifest_path = manifest_path.resolve(strict=True)
    manifest = _read_manifest(manifest_path)
    if manifest.data.format != "csv":
        raise ValueError("this consumer currently supports CSV payloads only")
    payload_path = _resolve_payload(manifest_path, manifest.data.path)
    payload = _verify_payload(payload_path, manifest.data)
    return _parse_csv(payload, manifest)
