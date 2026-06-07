#!/usr/bin/env python3
"""Check duplicate-risk rows in legacy analysis detail tables.

The script is read-only. It reports groups that would break the Phase 2
idempotency plan before schema constraints or migrations are applied.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NamedTuple

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


class DuplicateCheck(NamedTuple):
    check_name: str
    description: str
    sql: str


class DuplicateFinding(NamedTuple):
    check_name: str
    description: str
    row_count: int
    sample_rows: list[dict[str, object]]


def build_duplicate_checks() -> tuple[DuplicateCheck, ...]:
    return (
        DuplicateCheck(
            check_name="qa_brand_state_target_key_duplicates",
            description=(
                "qa_brand_state duplicate groups for "
                "(tenant_key, job_id, conversation_id, brand)"
            ),
            sql="""
                SELECT
                    tenant_key,
                    job_id,
                    conversation_id,
                    brand,
                    COUNT(*) AS duplicate_count
                FROM qa_brand_state
                GROUP BY tenant_key, job_id, conversation_id, brand
                HAVING COUNT(*) > 1
                ORDER BY duplicate_count DESC
                LIMIT :row_limit
            """,
        ),
        DuplicateCheck(
            check_name="qa_reference_target_key_duplicates",
            description=(
                "qa_reference duplicate groups for "
                "(tenant_key, job_id, conversation_id, brand, url)"
            ),
            sql="""
                SELECT
                    tenant_key,
                    job_id,
                    conversation_id,
                    COALESCE(brand, '') AS brand_scope,
                    url,
                    COUNT(*) AS duplicate_count
                FROM qa_reference
                GROUP BY tenant_key, job_id, conversation_id, COALESCE(brand, ''), url
                HAVING COUNT(*) > 1
                ORDER BY duplicate_count DESC
                LIMIT :row_limit
            """,
        ),
        DuplicateCheck(
            check_name="qa_reference_current_key_cross_scope_collisions",
            description=(
                "qa_reference rows sharing the current key "
                "(tenant_key, conversation_id, url) across jobs or brands"
            ),
            sql="""
                SELECT
                    tenant_key,
                    conversation_id,
                    url,
                    COUNT(*) AS row_count,
                    COUNT(DISTINCT job_id) AS job_count,
                    COUNT(DISTINCT COALESCE(brand, '')) AS brand_count,
                    MIN(job_id) AS sample_job_id,
                    MIN(brand) AS sample_brand
                FROM qa_reference
                GROUP BY tenant_key, conversation_id, url
                HAVING
                    COUNT(DISTINCT job_id) > 1
                    OR COUNT(DISTINCT COALESCE(brand, '')) > 1
                ORDER BY row_count DESC
                LIMIT :row_limit
            """,
        ),
        DuplicateCheck(
            check_name="llm_conversation_references_target_key_duplicates",
            description=(
                "llm_conversation_references duplicate groups for "
                "(tenant_key, job_id, conversation_id, brand, url)"
            ),
            sql="""
                SELECT
                    tenant_key,
                    job_id,
                    conversation_id,
                    COALESCE(brand, '') AS brand_scope,
                    url,
                    COUNT(*) AS duplicate_count
                FROM llm_conversation_references
                GROUP BY tenant_key, job_id, conversation_id, COALESCE(brand, ''), url
                HAVING COUNT(*) > 1
                ORDER BY duplicate_count DESC
                LIMIT :row_limit
            """,
        ),
        DuplicateCheck(
            check_name="llm_conversation_references_current_key_cross_scope_collisions",
            description=(
                "llm_conversation_references rows sharing the current key "
                "(tenant_key, conversation_id, url) across jobs or brands"
            ),
            sql="""
                SELECT
                    tenant_key,
                    conversation_id,
                    url,
                    COUNT(*) AS row_count,
                    COUNT(DISTINCT job_id) AS job_count,
                    COUNT(DISTINCT COALESCE(brand, '')) AS brand_count,
                    MIN(job_id) AS sample_job_id,
                    MIN(brand) AS sample_brand
                FROM llm_conversation_references
                GROUP BY tenant_key, conversation_id, url
                HAVING
                    COUNT(DISTINCT job_id) > 1
                    OR COUNT(DISTINCT COALESCE(brand, '')) > 1
                ORDER BY row_count DESC
                LIMIT :row_limit
            """,
        ),
    )


def run_duplicate_checks(engine: Engine, row_limit: int = 20) -> list[DuplicateFinding]:
    findings: list[DuplicateFinding] = []

    with engine.connect() as conn:
        for duplicate_check in build_duplicate_checks():
            rows = conn.execute(
                text(duplicate_check.sql),
                {"row_limit": row_limit},
            ).mappings()
            sample_rows = [dict(row) for row in rows]
            if sample_rows:
                findings.append(
                    DuplicateFinding(
                        check_name=duplicate_check.check_name,
                        description=duplicate_check.description,
                        row_count=len(sample_rows),
                        sample_rows=sample_rows,
                    )
                )

    return findings


def format_report(findings: list[DuplicateFinding]) -> str:
    if not findings:
        return "No duplicate risks found for qa_brand_state, qa_reference, or references."

    lines = ["Duplicate analysis-row risks found:"]
    for finding in findings:
        lines.append(f"- {finding.check_name}: {finding.description}")
        lines.append(f"  sampled_groups={finding.row_count}")
        for row in finding.sample_rows:
            lines.append(
                "  "
                + json.dumps(
                    row,
                    ensure_ascii=False,
                    default=str,
                    sort_keys=True,
                )
            )

    return "\n".join(lines)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_default_engine(env_file: str | None) -> Engine:
    project_root = _project_root()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    if env_file:
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=Path(env_file))

    from api.v1.repositories.connection import get_engine

    return get_engine()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check duplicate-risk rows in analysis detail tables.",
    )
    parser.add_argument(
        "--database-url",
        help="Optional SQLAlchemy database URL. Defaults to api/v1 repository config.",
    )
    parser.add_argument(
        "--env-file",
        help="Optional .env file loaded before the default API database config.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum sample groups to print per check.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    engine = (
        create_engine(args.database_url)
        if args.database_url
        else _load_default_engine(args.env_file)
    )

    try:
        findings = run_duplicate_checks(engine, row_limit=args.limit)
    except SQLAlchemyError as exc:
        print(f"ERROR: duplicate check failed: {exc}", file=sys.stderr)
        return 2

    print(format_report(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
