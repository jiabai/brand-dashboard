from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_runtime_code_and_schema_do_not_define_metric_snapshots():
    checked_paths = (
        PROJECT_ROOT / "api" / "v1",
        PROJECT_ROOT / "api" / "database",
        PROJECT_ROOT / "analysis" / "database",
        PROJECT_ROOT / "web" / "src",
    )
    ignored_files = {
        PROJECT_ROOT / "api" / "tests" / "test_metric_snapshots_removed.py",
    }
    offenders: list[str] = []

    for base_path in checked_paths:
        for path in base_path.rglob("*"):
            if path in ignored_files or not path.is_file():
                continue
            if path.suffix.lower() not in {".py", ".sql", ".js", ".jsx", ".ts", ".tsx"}:
                continue
            content = path.read_text(encoding="utf-8", errors="ignore").lower()
            if "metric_snapshots" in content or "metric_snapshot" in content:
                offenders.append(str(path.relative_to(PROJECT_ROOT)))

    assert offenders == []
