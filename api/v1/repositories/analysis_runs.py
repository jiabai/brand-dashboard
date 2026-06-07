import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class AnalysisRunOperationResult:
    status_code: int
    message: str
    analysis_run: object | None = None


def _serialize_json(value: Any) -> str | None:
    if value is None or isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _select_analysis_run(db: Session, *, tenant_key: str, analysis_run_id: str):
    return db.execute(
        text(
            """
            SELECT
              id,
              tenant_key,
              analysis_run_id,
              project_id,
              collection_job_id,
              status,
              plugin_versions,
              model_config_hash,
              input_watermark,
              started_at,
              finished_at,
              stale_at,
              error_code,
              error_message
            FROM analysis_runs
            WHERE tenant_key = :tenant_key
              AND analysis_run_id = :analysis_run_id
            """
        ),
        {
            "tenant_key": tenant_key,
            "analysis_run_id": analysis_run_id,
        },
    ).first()


def get_analysis_run(db: Session, *, tenant_key: str, analysis_run_id: str):
    return _select_analysis_run(
        db,
        tenant_key=tenant_key,
        analysis_run_id=analysis_run_id,
    )


def get_latest_successful_analysis_run_for_collection(
    db: Session,
    *,
    tenant_key: str,
    collection_job_id: str,
):
    return db.execute(
        text(
            """
            SELECT
              id,
              tenant_key,
              analysis_run_id,
              project_id,
              collection_job_id,
              status,
              plugin_versions,
              model_config_hash,
              input_watermark,
              started_at,
              finished_at,
              stale_at,
              error_code,
              error_message
            FROM analysis_runs
            WHERE tenant_key = :tenant_key
              AND collection_job_id = :collection_job_id
              AND status = 'succeeded'
            ORDER BY finished_at DESC, updated_at DESC, id DESC
            LIMIT 1
            """
        ),
        {
            "tenant_key": tenant_key,
            "collection_job_id": collection_job_id,
        },
    ).first()


def _select_collection_job(db: Session, *, tenant_key: str, collection_job_id: str):
    return db.execute(
        text(
            """
            SELECT tenant_key, collection_job_id, project_id, status
            FROM collection_jobs
            WHERE tenant_key = :tenant_key
              AND collection_job_id = :collection_job_id
            """
        ),
        {
            "tenant_key": tenant_key,
            "collection_job_id": collection_job_id,
        },
    ).first()


def create_analysis_run(
    db: Session,
    *,
    tenant_key: str,
    analysis_run_id: str,
    collection_job_id: str,
    now: datetime,
    plugin_versions: Any = None,
    model_config_hash: str | None = None,
    input_watermark: str | None = None,
) -> AnalysisRunOperationResult:
    if _select_analysis_run(
        db,
        tenant_key=tenant_key,
        analysis_run_id=analysis_run_id,
    ):
        return AnalysisRunOperationResult(409, "analysis_run_id 已存在")

    collection_job = _select_collection_job(
        db,
        tenant_key=tenant_key,
        collection_job_id=collection_job_id,
    )
    if collection_job is None:
        return AnalysisRunOperationResult(404, "采集批次不存在")

    db.execute(
        text(
            """
            INSERT INTO analysis_runs
              (
                tenant_key,
                analysis_run_id,
                project_id,
                collection_job_id,
                status,
                plugin_versions,
                model_config_hash,
                input_watermark,
                created_at,
                updated_at
              )
            VALUES
              (
                :tenant_key,
                :analysis_run_id,
                :project_id,
                :collection_job_id,
                'pending',
                :plugin_versions,
                :model_config_hash,
                :input_watermark,
                :now,
                :now
              )
            """
        ),
        {
            "tenant_key": tenant_key,
            "analysis_run_id": analysis_run_id,
            "project_id": collection_job.project_id,
            "collection_job_id": collection_job_id,
            "plugin_versions": _serialize_json(plugin_versions),
            "model_config_hash": model_config_hash,
            "input_watermark": input_watermark,
            "now": now,
        },
    )

    return AnalysisRunOperationResult(
        200,
        "analysis run 已创建",
        _select_analysis_run(
            db,
            tenant_key=tenant_key,
            analysis_run_id=analysis_run_id,
        ),
    )


def start_analysis_run(
    db: Session,
    *,
    tenant_key: str,
    analysis_run_id: str,
    now: datetime,
) -> AnalysisRunOperationResult:
    analysis_run = _select_analysis_run(
        db,
        tenant_key=tenant_key,
        analysis_run_id=analysis_run_id,
    )
    if analysis_run is None:
        return AnalysisRunOperationResult(404, "analysis run 不存在")

    if analysis_run.status != "pending":
        return AnalysisRunOperationResult(409, "analysis run 不处于 pending 状态")

    db.execute(
        text(
            """
            UPDATE analysis_runs
            SET
              status = 'running',
              started_at = :now,
              finished_at = NULL,
              stale_at = NULL,
              error_code = NULL,
              error_message = NULL,
              updated_at = :now
            WHERE tenant_key = :tenant_key
              AND analysis_run_id = :analysis_run_id
              AND status = 'pending'
            """
        ),
        {
            "tenant_key": tenant_key,
            "analysis_run_id": analysis_run_id,
            "now": now,
        },
    )

    return AnalysisRunOperationResult(
        200,
        "analysis run 已启动",
        _select_analysis_run(
            db,
            tenant_key=tenant_key,
            analysis_run_id=analysis_run_id,
        ),
    )


def complete_analysis_run(
    db: Session,
    *,
    tenant_key: str,
    analysis_run_id: str,
    status: str,
    now: datetime,
    error_code: str | None = None,
    error_message: str | None = None,
) -> AnalysisRunOperationResult:
    analysis_run = _select_analysis_run(
        db,
        tenant_key=tenant_key,
        analysis_run_id=analysis_run_id,
    )
    if analysis_run is None:
        return AnalysisRunOperationResult(404, "analysis run 不存在")

    if analysis_run.status != "running":
        return AnalysisRunOperationResult(409, "analysis run 不处于 running 状态")

    if status not in {"succeeded", "failed"}:
        return AnalysisRunOperationResult(400, "analysis run 完成状态无效")

    if status == "succeeded":
        error_code = None
        error_message = None

    db.execute(
        text(
            """
            UPDATE analysis_runs
            SET
              status = :status,
              finished_at = :now,
              error_code = :error_code,
              error_message = :error_message,
              updated_at = :now
            WHERE tenant_key = :tenant_key
              AND analysis_run_id = :analysis_run_id
              AND status = 'running'
            """
        ),
        {
            "tenant_key": tenant_key,
            "analysis_run_id": analysis_run_id,
            "status": status,
            "error_code": error_code,
            "error_message": error_message,
            "now": now,
        },
    )

    return AnalysisRunOperationResult(
        200,
        "analysis run 已完成",
        _select_analysis_run(
            db,
            tenant_key=tenant_key,
            analysis_run_id=analysis_run_id,
        ),
    )


def mark_analysis_run_stale(
    db: Session,
    *,
    tenant_key: str,
    analysis_run_id: str,
    reason: str | None,
    now: datetime,
) -> AnalysisRunOperationResult:
    analysis_run = _select_analysis_run(
        db,
        tenant_key=tenant_key,
        analysis_run_id=analysis_run_id,
    )
    if analysis_run is None:
        return AnalysisRunOperationResult(404, "analysis run 不存在")

    if analysis_run.status not in {"succeeded", "failed"}:
        return AnalysisRunOperationResult(
            409,
            "只有已完成或失败的 analysis run 可以标记为 stale",
        )

    db.execute(
        text(
            """
            UPDATE analysis_runs
            SET
              status = 'stale',
              stale_at = :now,
              error_code = 'stale',
              error_message = :reason,
              updated_at = :now
            WHERE tenant_key = :tenant_key
              AND analysis_run_id = :analysis_run_id
              AND status IN ('succeeded', 'failed')
            """
        ),
        {
            "tenant_key": tenant_key,
            "analysis_run_id": analysis_run_id,
            "reason": reason,
            "now": now,
        },
    )

    return AnalysisRunOperationResult(
        200,
        "analysis run 已标记 stale",
        _select_analysis_run(
            db,
            tenant_key=tenant_key,
            analysis_run_id=analysis_run_id,
        ),
    )
