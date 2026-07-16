from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from model_drift.application import DriftMonitor
from model_drift.artifact import load_monitoring_batch
from model_drift.benchmark import decision_to_dict, run_benchmark
from model_drift.domain import AlarmPolicy
from model_drift.statistics import ScipyKsDetector
from model_drift.telemetry import PrometheusTelemetry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="model-drift-detector")
    subparsers = parser.add_subparsers(dest="command", required=True)

    benchmark = subparsers.add_parser("benchmark")
    benchmark.add_argument("--rows", type=int, default=2_000)
    benchmark.add_argument(
        "--output",
        type=Path,
        default=Path(
            os.getenv(
                "BENCHMARK_OUTPUT",
                "benchmarks/results/summary.json",
            )
        ),
    )

    detect = subparsers.add_parser("detect")
    detect.add_argument("reference_manifest", type=Path)
    detect.add_argument("current_manifest", type=Path)
    detect.add_argument("--minimum-samples", type=int, default=200)

    validate = subparsers.add_parser("validate")
    validate.add_argument("manifest", type=Path)
    return parser


def _print(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def run(argv: Sequence[str] | None = None) -> int:
    arguments = list(argv if argv is not None else sys.argv[1:])
    if not arguments:
        arguments = ["benchmark"]
    args = build_parser().parse_args(arguments)

    if args.command == "benchmark":
        result = run_benchmark(output_path=args.output, rows=args.rows)
        _print(result)
        return 0

    if args.command == "validate":
        batch = load_monitoring_batch(args.manifest)
        _print(
            {
                "valid": True,
                "batch_id": batch.batch_id,
                "rows": batch.row_count,
                "columns": list(batch.values),
            }
        )
        return 0

    reference = load_monitoring_batch(args.reference_manifest)
    current = load_monitoring_batch(args.current_manifest)
    telemetry = PrometheusTelemetry()
    evaluation = DriftMonitor(
        detector=ScipyKsDetector(minimum_samples=args.minimum_samples),
        policy=AlarmPolicy(),
        telemetry=telemetry,
    ).evaluate(reference, current)
    _print(
        {
            "decision": decision_to_dict(evaluation.decision),
            "duration_seconds": evaluation.duration_seconds,
            "prometheus": telemetry.render(),
        }
    )
    return 0


def _failure_output_path(argv: Sequence[str]) -> Path:
    try:
        parsed = build_parser().parse_args(list(argv))
        if parsed.command == "benchmark":
            return parsed.output.with_name("failure.json")
    except SystemExit:
        pass
    return Path("benchmarks/results/failure.json")


def main() -> int:
    argv = sys.argv[1:] or ["benchmark"]
    try:
        return run(argv)
    except Exception as error:
        failure = {
            "project": "model-drift-detector",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "error_type": type(error).__name__,
            "error": str(error),
        }
        path = _failure_output_path(argv)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(failure, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(json.dumps(failure, sort_keys=True), file=sys.stderr)
        return 1
