from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any


AGGREGATED_METRICS = (
    "precision",
    "recall",
    "f1",
    "false_positive_rate",
    "detection_runtime_p50_ms",
    "detection_runtime_p95_ms",
    "blind_spot_detection_rate",
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("project") != "model-drift-detector":
        raise ValueError(f"{path} belongs to another project")
    if value.get("metric") != "drift_alarm_f1" or value.get("unit") != "ratio":
        raise ValueError(f"{path} has an incompatible benchmark contract")
    if value.get("failures") != 0:
        raise ValueError(f"{path} contains benchmark failures")
    return value


def _scenario_signature(result: dict[str, Any]) -> tuple:
    matrix = result.get("proof", {}).get("scenario_matrix", [])
    return tuple(
        (item.get("name"), item.get("expected_drift"), item.get("scored"))
        for item in matrix
    )


def aggregate(paths: list[Path], output: Path) -> dict[str, Any]:
    if len(paths) < 3:
        raise ValueError("at least three raw benchmark results are required")
    loaded = [_load(path) for path in paths]

    image_ids = {item["environment"].get("image_id") for item in loaded}
    if len(image_ids) != 1 or image_ids == {"not-recorded"} or None in image_ids:
        raise ValueError("all runs must record the same immutable image_id")

    signatures = {_scenario_signature(item) for item in loaded}
    if len(signatures) != 1 or not next(iter(signatures)):
        raise ValueError("all runs must contain the same non-empty scenario matrix")

    result = deepcopy(loaded[0])
    result["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    result["value"] = median(float(item["value"]) for item in loaded)
    result["repeat"] = len(loaded)
    result["results"] = [path.as_posix() for path in paths]
    result["environment"]["aggregated_runs"] = len(loaded)
    result["summary"] = {}
    result["metrics"] = {}
    for name in AGGREGATED_METRICS:
        samples = [float(item["metrics"][name]) for item in loaded]
        result["summary"][name] = median(samples)
        result["metrics"][name] = {
            "median": median(samples),
            "min": min(samples),
            "max": max(samples),
            "samples": samples,
        }
    result["proof"] = {
        "aggregate": "median with min, max, and all samples",
        "raw_results": [path.name for path in paths],
        "image_id": next(iter(image_ids)),
        "scenario_signature": [list(item) for item in next(iter(signatures))],
        "all_failures_preserved": True,
        "source_proof": loaded[0]["proof"],
    }
    result["failures"] = sum(int(item["failures"]) for item in loaded)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = aggregate(sorted(args.inputs), args.output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
