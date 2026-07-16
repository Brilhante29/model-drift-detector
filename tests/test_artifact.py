import json

import pytest
from pydantic import ValidationError

from model_drift.artifact import load_monitoring_batch
from model_drift.fixtures import generate_batch, write_bundle


def create_bundle(tmp_path, rows=200):
    batch = generate_batch("fixture", seed=42, rows=rows)
    manifest = write_bundle(batch, tmp_path / "bundle")
    return batch, manifest


def read_manifest(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_manifest(path, content):
    path.write_text(
        json.dumps(content, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_bundle_round_trip_verifies_hash_schema_and_rows(tmp_path):
    expected, manifest = create_bundle(tmp_path)

    actual = load_monitoring_batch(manifest)

    assert actual.batch_id == expected.batch_id
    assert actual.row_count == expected.row_count
    assert tuple(actual.values) == tuple(expected.values)


def test_bundle_rejects_tampered_payload(tmp_path):
    _, manifest = create_bundle(tmp_path)
    payload = manifest.parent / "batch.csv"
    payload.write_bytes(payload.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="byte count"):
        load_monitoring_batch(manifest)


def test_bundle_rejects_wrong_hash_even_when_size_matches(tmp_path):
    _, manifest = create_bundle(tmp_path)
    content = read_manifest(manifest)
    content["data"]["sha256"] = "0" * 64
    write_manifest(manifest, content)

    with pytest.raises(ValueError, match="SHA-256"):
        load_monitoring_batch(manifest)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda data: data["data"].update(rows=data["data"]["rows"] + 1), "row count"),
        (lambda data: data["data"].update(format="jsonl"), "CSV payloads"),
        (lambda data: data["data"].update(path="../batch.csv"), "validation error"),
        (
            lambda data: data["columns"].append(data["columns"][0]),
            "unique names",
        ),
        (
            lambda data: data["columns"][0].update(nullable=True),
            "must not be nullable",
        ),
    ],
)
def test_bundle_rejects_invalid_manifest_contract(tmp_path, mutation, message):
    _, manifest = create_bundle(tmp_path)
    content = read_manifest(manifest)
    mutation(content)
    write_manifest(manifest, content)

    with pytest.raises((ValueError, ValidationError), match=message):
        load_monitoring_batch(manifest)


def test_bundle_rejects_csv_header_mismatch_after_rehash(tmp_path):
    _, manifest = create_bundle(tmp_path)
    payload_path = manifest.parent / "batch.csv"
    lines = payload_path.read_text(encoding="utf-8").splitlines()
    lines[0] = lines[0].replace("feature_0", "unexpected", 1)
    payload = ("\n".join(lines) + "\n").encode()
    payload_path.write_bytes(payload)

    import hashlib

    content = read_manifest(manifest)
    content["data"]["bytes"] = len(payload)
    content["data"]["sha256"] = hashlib.sha256(payload).hexdigest()
    write_manifest(manifest, content)

    with pytest.raises(ValueError, match="columns or order"):
        load_monitoring_batch(manifest)
