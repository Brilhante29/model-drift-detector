from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import uuid
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


def git_blob(root: Path, commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), "show", f"{commit}:{path}"],
        check=True,
        capture_output=True,
    ).stdout


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def metric(
    name: str,
    values: list[float],
    unit: str,
    direction: str,
    failures: int,
) -> dict[str, Any]:
    return {
        "name": name,
        "value": statistics.median(values),
        "unit": unit,
        "direction": direction,
        "samples": values,
        "failures": failures,
        "summary": {
            "min": min(values),
            "max": max(values),
            "mean": statistics.fmean(values),
            "median": statistics.median(values),
        },
    }


def build(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    workload = json.loads(git_blob(root, args.source_commit, args.workload_ref))
    workload["rows_per_batch"] = args.rows
    if args.repetitions != workload["repetitions"]:
        raise ValueError("repetitions differ from the source-locked workload")
    runs = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(Path(args.results_directory).glob("run-*.json"))
    ]
    if len(runs) != args.repetitions:
        raise ValueError("raw run count differs from workload repetitions")

    failures = sum(int(run["failures"]) for run in runs)
    if failures:
        raise ValueError(f"benchmark runs contain {failures} failure(s)")
    signatures = {
        json.dumps(run["proof"]["benchmark_signature"], sort_keys=True) for run in runs
    }
    if len(signatures) != 1:
        raise ValueError("raw benchmark signatures differ")
    signature = json.loads(next(iter(signatures)))
    expected = {
        "rows_per_batch": args.rows,
        "scored_scenarios": workload["scored_scenarios"],
        "total_scenarios": workload["total_scenarios"],
        "feature_count": workload["feature_count"],
    }
    if any(signature[name] != value for name, value in expected.items()):
        raise ValueError("raw benchmark shape differs from effective workload")
    if any(int(run.get("repeat", 0)) != 1 for run in runs):
        raise ValueError("each raw file must represent one independent repetition")

    def samples(field: str) -> list[float]:
        return [float(run["metrics"][field]) for run in runs]

    metrics = [
        metric("drift_alarm_f1", samples("f1"), "ratio", "higher_is_better", failures),
        metric("drift_precision", samples("precision"), "ratio", "higher_is_better", failures),
        metric("drift_recall", samples("recall"), "ratio", "higher_is_better", failures),
        metric(
            "false_positive_rate",
            samples("false_positive_rate"),
            "ratio",
            "lower_is_better",
            failures,
        ),
        metric(
            "detection_runtime_p95_ms",
            samples("detection_runtime_p95_ms"),
            "milliseconds",
            "lower_is_better",
            failures,
        ),
        metric(
            "blind_spot_detection_rate",
            samples("blind_spot_detection_rate"),
            "ratio",
            "target",
            failures,
        ),
    ]
    first = runs[0]
    fixture_digest = signature["fixture_digest"]
    result = {
        "schema_version": 2,
        "run_id": str(uuid.uuid4()),
        "project": "model-drift-detector",
        "benchmark_id": workload["benchmark_id"],
        "workload": {
            "version": "drift-scenario-matrix-v1",
            "fixture_digest": fixture_digest,
            "config_digest": digest(
                json.dumps(workload, sort_keys=True, separators=(",", ":")).encode()
            ),
            "warmup_iterations": workload["warmup_evaluations"],
            "measured_iterations": workload["scored_scenarios"],
            "concurrency": workload["concurrency"],
        },
        "metrics": metrics,
        "execution": {
            "command": args.command,
            "started_at": min(run["started_at"] for run in runs),
            "duration_seconds": sum(float(run["duration_seconds"]) for run in runs),
            "exit_code": 0,
            "repeat": len(runs),
        },
        "environment": {
            "runtime": f"python-{first['environment']['python']}",
            "architecture": first["environment"]["machine"],
            "hardware_class": args.hardware_class,
            "container_platform": first["environment"]["platform"],
            "numpy": first["environment"]["numpy"],
            "scipy": first["environment"]["scipy"],
            "rows_per_batch": args.rows,
        },
        "provenance": {
            "source_commit": args.source_commit,
            "clean_tree": True,
            "image_ref": args.image_ref,
            "image_digest": args.image_digest,
            "dependency_lock_digest": digest(git_blob(root, args.source_commit, args.lock_ref)),
            "producer": args.producer,
            "artifact_digest": args.artifact_digest,
        },
        "comparability_key": (
            "model-drift-detector:holm-ks-v1:"
            f"rows-{args.rows}:features-{workload['feature_count']}:"
            f"scenarios-{workload['scored_scenarios']}:"
            "effect-0_1:alpha-0_05"
        ),
    }
    schema = json.loads(
        (root / ".portfolio/contracts/benchmark-result-v2.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--results-directory", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--image-ref", required=True)
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--artifact-digest", required=True)
    parser.add_argument("--hardware-class", required=True)
    parser.add_argument("--rows", type=int, required=True)
    parser.add_argument("--repetitions", type=int, required=True)
    parser.add_argument(
        "--producer", choices=("local", "github-actions", "other-ci"), required=True
    )
    parser.add_argument("--workload-ref", default="benchmarks/workload.json")
    parser.add_argument("--lock-ref", default="constraints.lock")
    parser.add_argument("--command", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(build(args), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
