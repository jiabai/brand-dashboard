import json
from pathlib import Path

import pytest

from src.core.database_config import (
    DatabaseConfigError,
    resolve_database_config,
)


def test_versioned_analysis_config_uses_environment_placeholders():
    config_path = Path(__file__).resolve().parents[1] / "config" / "analysis_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    db_cfg = config["brand_analysis"]["database"]

    assert db_cfg == {
        "host": "${ANALYSIS_DB_HOST:-127.0.0.1}",
        "port": "${ANALYSIS_DB_PORT:-3306}",
        "user": "${ANALYSIS_DB_USER:-root}",
        "password": "${ANALYSIS_DB_PASSWORD}",
        "name": "${ANALYSIS_DB_NAME:-geo}",
    }


def test_resolve_database_config_reads_env_values(monkeypatch):
    monkeypatch.setenv("ANALYSIS_DB_HOST", "db.internal")
    monkeypatch.setenv("ANALYSIS_DB_PORT", "3307")
    monkeypatch.setenv("ANALYSIS_DB_USER", "analysis_user")
    monkeypatch.setenv("ANALYSIS_DB_PASSWORD", "secret-from-env")
    monkeypatch.setenv("ANALYSIS_DB_NAME", "brand_geo")

    resolved = resolve_database_config(
        {
            "host": "${ANALYSIS_DB_HOST:-127.0.0.1}",
            "port": "${ANALYSIS_DB_PORT:-3306}",
            "user": "${ANALYSIS_DB_USER:-root}",
            "password": "${ANALYSIS_DB_PASSWORD}",
            "name": "${ANALYSIS_DB_NAME:-geo}",
        }
    )

    assert resolved == {
        "host": "db.internal",
        "port": 3307,
        "user": "analysis_user",
        "password": "secret-from-env",
        "name": "brand_geo",
    }


def test_resolve_database_config_requires_password_env(monkeypatch):
    monkeypatch.delenv("ANALYSIS_DB_PASSWORD", raising=False)

    with pytest.raises(DatabaseConfigError, match="ANALYSIS_DB_PASSWORD"):
        resolve_database_config(
            {
                "host": "${ANALYSIS_DB_HOST:-127.0.0.1}",
                "port": "${ANALYSIS_DB_PORT:-3306}",
                "user": "${ANALYSIS_DB_USER:-root}",
                "password": "${ANALYSIS_DB_PASSWORD}",
                "name": "${ANALYSIS_DB_NAME:-geo}",
            }
        )
