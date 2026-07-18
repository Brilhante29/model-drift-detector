import copy
import json
import runpy

import pytest

MODULE = runpy.run_path("tools/aggregate_results.py")
aggregate = MODULE["aggregate"]


def raw_result(image_id="sha256:image", f1=1.0):
    matrix = [
        {
            "name": "stable-1",
            "expected_drift": False,
            "scored": True,
        }
    ]
    metrics = {
        "precision": f1,
        "recall": f1,
        "f1": f1,
        "false_positive_rate": 0.0,
        "detection_runtime_p50_ms": 2.0,
        "detection_runtime_p95_ms": 3.0,
        "blind_spot_detection_rate": 0.0,
    }
    return {
        "project": "model-drift-detector",
        "metric": "drift_alarm_f1",
        "value": f1,
        "unit": "ratio",
        "timestamp": "2026-01-01T00:00:00Z",
        "command": "docker run",
        "environment": {"image_id": image_id},
        "summary": copy.deepcopy(metrics),
        "metrics": metrics,
        "proof": {"scenario_matrix": matrix},
        "failures": 0,
    }


def write_result(path, result):
    path.write_text(json.dumps(result), encoding="utf-8")
    return path


def test_aggregate_requires_three_same_image_runs_and_preserves_samples(tmp_path):
    paths = [
        write_result(tmp_path / f"run-{index}.json", raw_result(f1=value))
        for index, value in enumerate((0.8, 1.0, 0.9), start=1)
    ]

    result = aggregate(paths, tmp_path / "summary.json")

    assert result["value"] == 0.9
    assert result["metrics"]["f1"]["samples"] == [0.8, 1.0, 0.9]
    assert result["proof"]["all_failures_preserved"] is True
    assert result["repeat"] == 3


def test_aggregate_rejects_missing_runs_image_or_failures(tmp_path):
    one = write_result(tmp_path / "one.json", raw_result())
    with pytest.raises(ValueError, match="at least three"):
        aggregate([one], tmp_path / "summary.json")

    values = [raw_result(), raw_result("other"), raw_result()]
    paths = [
        write_result(tmp_path / f"bad-{index}.json", value)
        for index, value in enumerate(values)
    ]
    with pytest.raises(ValueError, match="same immutable"):
        aggregate(paths, tmp_path / "summary.json")

    failed = raw_result()
    failed["failures"] = 1
    paths[1] = write_result(paths[1], failed)
    with pytest.raises(ValueError, match="failures"):
        aggregate(paths, tmp_path / "summary.json")
