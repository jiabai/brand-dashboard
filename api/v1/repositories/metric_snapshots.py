from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

METRIC_SNAPSHOT_COLUMNS = [
    "tenant_key",
    "snapshot_id",
    "project_id",
    "analysis_run_id",
    "metric_date",
    "brand_id",
    "brand_name",
    "platform",
    "keyword",
    "metric_name",
    "metric_value",
    "metric_unit",
    "metric_definition_version",
    "expected_task_count",
    "succeeded_task_count",
    "failed_task_count",
    "analyzed_answer_count",
    "coverage_rate",
    "source_watermark",
    "dimension_hash",
    "generated_at",
]

METRIC_SNAPSHOT_IDENTITY_COLUMNS = [
    "tenant_key",
    "project_id",
    "metric_date",
    "metric_name",
    "metric_definition_version",
    "analysis_run_id",
    "dimension_hash",
]


def _dialect_name(db: Session) -> str:
    bind = db.get_bind()
    return getattr(bind.dialect, "name", "")


def _upsert_sql(db: Session) -> str:
    columns = ", ".join(METRIC_SNAPSHOT_COLUMNS)
    values = ", ".join(f":{column}" for column in METRIC_SNAPSHOT_COLUMNS)
    update_columns = [
        column
        for column in METRIC_SNAPSHOT_COLUMNS
        if column not in METRIC_SNAPSHOT_IDENTITY_COLUMNS
    ]

    if _dialect_name(db) == "mysql":
        updates = ", ".join(f"{column} = VALUES({column})" for column in update_columns)
        return (
            f"INSERT INTO metric_snapshots ({columns}) VALUES ({values}) "
            f"ON DUPLICATE KEY UPDATE {updates}"
        )

    conflict_columns = ", ".join(METRIC_SNAPSHOT_IDENTITY_COLUMNS)
    updates = ", ".join(f"{column} = excluded.{column}" for column in update_columns)
    return (
        f"INSERT INTO metric_snapshots ({columns}) VALUES ({values}) "
        f"ON CONFLICT({conflict_columns}) DO UPDATE SET {updates}"
    )


def upsert_metric_snapshots(
    db: Session,
    snapshots: Sequence[Mapping[str, Any]],
) -> int:
    if not snapshots:
        return 0

    db.execute(text(_upsert_sql(db)), [dict(snapshot) for snapshot in snapshots])
    return len(snapshots)
