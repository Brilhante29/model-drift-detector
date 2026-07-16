import json

from model_drift.cli import run
from model_drift.fixtures import generate_batch, write_bundle


def test_cli_validates_and_detects_bundles(tmp_path, capsys):
    reference = write_bundle(
        generate_batch("reference", 42, 200),
        tmp_path / "reference",
    )
    current = write_bundle(
        generate_batch("current", 200, 200, family="mean_shift"),
        tmp_path / "current",
    )

    assert run(["validate", str(reference)]) == 0
    validated = json.loads(capsys.readouterr().out)
    assert validated["valid"] is True

    assert run(["detect", str(reference), str(current)]) == 0
    detected = json.loads(capsys.readouterr().out)
    assert detected["decision"]["alarm"] is True
    assert "model_drift_evaluations_total" in detected["prometheus"]
