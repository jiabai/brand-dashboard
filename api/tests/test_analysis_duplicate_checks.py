import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def _load_check_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / (
        "check_duplicate_analysis_rows.py"
    )
    spec = importlib.util.spec_from_file_location("check_duplicate_analysis_rows", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def duplicate_check_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE qa_brand_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_key TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    brand TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE qa_reference (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_key TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    brand TEXT,
                    url TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE llm_conversation_references (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_key TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    brand TEXT,
                    url TEXT NOT NULL
                )
                """
            )
        )

    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def test_duplicate_checks_report_target_key_duplicates_and_current_key_collisions(
    duplicate_check_session,
):
    checks = _load_check_module()
    duplicate_check_session.execute(
        text(
            """
            INSERT INTO qa_brand_state (tenant_key, job_id, conversation_id, brand)
            VALUES
              ('tenant_a', 'job_1', 'conv_1', 'brand_a'),
              ('tenant_a', 'job_1', 'conv_1', 'brand_a')
            """
        )
    )
    duplicate_check_session.execute(
        text(
            """
            INSERT INTO qa_reference (tenant_key, job_id, conversation_id, brand, url)
            VALUES
              ('tenant_a', 'job_1', 'conv_1', 'brand_a', 'https://example.com/a'),
              ('tenant_a', 'job_1', 'conv_1', 'brand_a', 'https://example.com/a'),
              ('tenant_a', 'job_2', 'conv_1', 'brand_b', 'https://example.com/a')
            """
        )
    )
    duplicate_check_session.execute(
        text(
            """
            INSERT INTO llm_conversation_references
              (tenant_key, job_id, conversation_id, brand, url)
            VALUES
              ('tenant_a', 'job_1', 'conv_1', 'brand_a', 'https://example.com/a'),
              ('tenant_a', 'job_1', 'conv_1', 'brand_a', 'https://example.com/a'),
              ('tenant_a', 'job_2', 'conv_1', 'brand_b', 'https://example.com/a')
            """
        )
    )
    duplicate_check_session.commit()

    findings = checks.run_duplicate_checks(duplicate_check_session.bind, row_limit=10)

    check_names = {finding.check_name for finding in findings}
    assert check_names == {
        "qa_brand_state_target_key_duplicates",
        "qa_reference_target_key_duplicates",
        "qa_reference_current_key_cross_scope_collisions",
        "llm_conversation_references_target_key_duplicates",
        "llm_conversation_references_current_key_cross_scope_collisions",
    }
    assert all(finding.sample_rows for finding in findings)


def test_duplicate_checks_return_empty_result_for_clean_data(duplicate_check_session):
    checks = _load_check_module()
    duplicate_check_session.execute(
        text(
            """
            INSERT INTO qa_brand_state (tenant_key, job_id, conversation_id, brand)
            VALUES ('tenant_a', 'job_1', 'conv_1', 'brand_a')
            """
        )
    )
    duplicate_check_session.execute(
        text(
            """
            INSERT INTO qa_reference (tenant_key, job_id, conversation_id, brand, url)
            VALUES ('tenant_a', 'job_1', 'conv_1', 'brand_a', 'https://example.com/a')
            """
        )
    )
    duplicate_check_session.execute(
        text(
            """
            INSERT INTO llm_conversation_references
              (tenant_key, job_id, conversation_id, brand, url)
            VALUES ('tenant_a', 'job_1', 'conv_1', 'brand_a', 'https://example.com/a')
            """
        )
    )
    duplicate_check_session.commit()

    findings = checks.run_duplicate_checks(duplicate_check_session.bind, row_limit=10)

    assert findings == []
    assert "No duplicate risks found" in checks.format_report(findings)


def test_cli_returns_two_when_required_tables_are_missing(capsys):
    checks = _load_check_module()

    exit_code = checks.main(["--database-url", "sqlite:///:memory:"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: duplicate check failed" in captured.err
