import ast
from pathlib import Path

FORBIDDEN_DOMAIN_IMPORTS = {
    "scipy",
    "numpy",
    "pydantic",
    "prometheus_client",
    "evidently",
    "airflow",
    "mlflow",
    "fastapi",
    "boto3",
}


def imported_roots(path):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_domain_and_application_do_not_depend_on_framework_adapters():
    for path in (
        "src/model_drift/domain.py",
        "src/model_drift/application.py",
    ):
        assert not (imported_roots(path) & FORBIDDEN_DOMAIN_IMPORTS)
