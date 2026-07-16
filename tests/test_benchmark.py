from pathlib import Path

import pytest

from model_drift.benchmark import run_benchmark


def test_benchmark_scores_labeled_scenarios_and_preserves_blind_spot(tmp_path):
    output = tmp_path / "summary.json"

    result = run_benchmark(output, rows=200, command="test-command")

    assert result["metric"] == "drift_alarm_f1"
    assert result["value"] == 1.0
    assert result["summary"]["false_positive_rate"] == 0.0
    assert result["proof"]["ground_truth_available_for_model_performance"] is False
    assert result["proof"]["documented_blind_spot"].startswith("correlation-only")
    assert len(result["proof"]["scenario_matrix"]) == 22
    assert output.is_file()


def test_benchmark_rejects_undersized_batches():
    with pytest.raises(ValueError, match="at least 200"):
        run_benchmark(None, rows=199)
