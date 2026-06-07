from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from api.v1.repositories import analysis_runs

try:
    from analysis.src.plugins.metrics.mention_status import MentionStatusPlugin
    from analysis.src.plugins.metrics.reference_status import ReferenceStatusPlugin
except ImportError:  # pragma: no cover - exercised by runtime environments only
    MentionStatusPlugin = None
    ReferenceStatusPlugin = None


@dataclass(frozen=True)
class AnalysisPluginRunResult:
    plugin_name: str
    source_table: str
    processed_records: int
    result: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CollectionAnalysisResult:
    status_code: int
    message: str
    analysis_run: object | None = None
    source_job_id: str | None = None
    target_brand: str | None = None
    competitor_brands: list[str] = field(default_factory=list)
    plugin_results: dict[str, AnalysisPluginRunResult] = field(default_factory=dict)


def _now() -> datetime:
    return datetime.now(UTC)


def _new_analysis_run_id() -> str:
    return f"analysis_run_{uuid.uuid4().hex}"


def _session_engine(db: Session):
    bind = db.get_bind()
    return getattr(bind, "engine", bind)


def _collection_job(db: Session, *, tenant_key: str, collection_job_id: str):
    return db.execute(
        text(
            """
            SELECT
              tenant_key,
              collection_job_id,
              project_id,
              source_job_id,
              status
            FROM collection_jobs
            WHERE tenant_key = :tenant_key
              AND collection_job_id = :collection_job_id
            LIMIT 1
            """
        ),
        {"tenant_key": tenant_key, "collection_job_id": collection_job_id},
    ).mappings().first()


def _project_brands(db: Session, *, tenant_key: str, project_id: str):
    return db.execute(
        text(
            """
            SELECT brand_name, role
            FROM project_brands
            WHERE tenant_key = :tenant_key
              AND project_id = :project_id
              AND status = 'active'
            ORDER BY
              CASE role
                WHEN 'target' THEN 1
                WHEN 'competitor' THEN 2
                ELSE 3
              END,
              id ASC
            """
        ),
        {"tenant_key": tenant_key, "project_id": project_id},
    ).mappings().all()


def _resolve_brand_context(
    db: Session, *, tenant_key: str, project_id: str
) -> tuple[str | None, list[str]]:
    rows = _project_brands(db, tenant_key=tenant_key, project_id=project_id)
    target = None
    competitors: list[str] = []
    for row in rows:
        brand_name = str(row["brand_name"]).strip()
        if not brand_name:
            continue
        if row["role"] == "target" and target is None:
            target = brand_name
        elif row["role"] == "competitor":
            competitors.append(brand_name)
    return target, competitors


def _fetch_rows(
    db: Session,
    *,
    table_name: str,
    tenant_key: str,
    source_job_id: str,
) -> list[dict[str, Any]]:
    if table_name not in {"llm_conversations", "llm_conversation_references"}:
        raise ValueError(f"Unsupported analysis source table: {table_name}")
    rows = db.execute(
        text(
            f"""
            SELECT *
            FROM {table_name}
            WHERE tenant_key = :tenant_key
              AND job_id = :source_job_id
            ORDER BY generated_date ASC, id ASC
            """
        ),
        {"tenant_key": tenant_key, "source_job_id": source_job_id},
    ).mappings().all()
    return [dict(row) for row in rows]


def _build_text_content(row: dict[str, Any]) -> str:
    query_content = str(row.get("query_content") or "")
    answer_content = str(row.get("answer_content") or "")
    if query_content.strip() or answer_content.strip():
        return f"用户提问：{query_content}\n\nAI回答：{answer_content}"
    return query_content or answer_content


def _plugin_config(source_table: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    fields = sorted({key for row in rows for key in row})
    return {"datasources": [{"table": source_table, "fields": fields}]}


def _configure_plugin(
    plugin: Any,
    *,
    plugin_name: str,
    source_table: str,
    rows: list[dict[str, Any]],
    db: Session,
    competitors: list[str],
) -> None:
    plugin_cfg = _plugin_config(source_table, rows)
    app_config = {
        "brand_analysis": {
            "database": {},
            "plugins": {plugin_name: plugin_cfg},
            "llm": {"enabled": False},
        }
    }
    if hasattr(plugin, "set_app_config"):
        plugin.set_app_config(app_config, plugin_cfg)
    if hasattr(plugin, "set_competitors"):
        plugin.set_competitors(competitors)
    if hasattr(plugin, "_db_engine"):
        plugin._db_engine = _session_engine(db)


def _llm_config_from_env() -> dict[str, Any]:
    return {
        "provider": os.getenv("LLM_PROVIDER") or os.getenv("ANALYSIS_LLM_PROVIDER"),
        "apiKey": os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
        "baseURL": os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL"),
        "model": os.getenv("LLM_MODEL") or os.getenv("ANALYSIS_LLM_MODEL"),
        "timeout": int(os.getenv("LLM_TIMEOUT_MS", "30000")),
    }


def _default_plugins() -> dict[str, Any]:
    if MentionStatusPlugin is None or ReferenceStatusPlugin is None:
        raise RuntimeError("analysis 插件模块不可用")
    llm_config = _llm_config_from_env()
    return {
        "mention_status": MentionStatusPlugin(llm_config=llm_config),
        "reference_status": ReferenceStatusPlugin(llm_config=llm_config),
    }


def _plugin_versions(plugins: dict[str, Any]) -> dict[str, str]:
    versions: dict[str, str] = {}
    for name, plugin in plugins.items():
        versions[name] = plugin.__class__.__name__
    return versions


def _run_plugin(
    plugin: Any,
    *,
    plugin_name: str,
    source_table: str,
    rows: list[dict[str, Any]],
    target_brand: str,
    analysis_run_id: str,
    db: Session,
    competitors: list[str],
) -> AnalysisPluginRunResult:
    _configure_plugin(
        plugin,
        plugin_name=plugin_name,
        source_table=source_table,
        rows=rows,
        db=db,
        competitors=competitors,
    )

    plugin_inputs: list[dict[str, Any]] = []
    for row in rows:
        text_content = _build_text_content(row)
        result = plugin.analyze(text_content, target_brand)
        if not isinstance(result, dict):
            result = {}
        result = dict(result)
        result["record_id"] = row.get("conversation_id") or row.get("id")
        result["analysis_run_id"] = analysis_run_id
        result["tenant_key"] = row.get("tenant_key")
        result["job_id"] = row.get("job_id")
        result["conversation_id"] = row.get("conversation_id")
        result["brand"] = row.get("brand") or target_brand
        result["category"] = row.get("category")
        result["platform"] = row.get("platform") or row.get("platform_name")
        result["keyword"] = row.get("keyword")
        result["query_content"] = row.get("query_content")
        result["url"] = row.get("url")
        result["domain"] = row.get("domain")
        result["generated_date"] = row.get("generated_date")
        result["source_row"] = row
        plugin_inputs.append(result)

    aggregate = plugin.aggregate_results(plugin_inputs)
    if not isinstance(aggregate, dict):
        aggregate = {}
    return AnalysisPluginRunResult(
        plugin_name=plugin_name,
        source_table=source_table,
        processed_records=len(plugin_inputs),
        result=aggregate,
    )


def run_collection_analysis(
    db: Session,
    *,
    tenant_key: str,
    collection_job_id: str,
    analysis_run_id: str | None = None,
    plugins: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> CollectionAnalysisResult:
    started_at = now or _now()
    run_id = analysis_run_id or _new_analysis_run_id()
    collection_job = _collection_job(
        db,
        tenant_key=tenant_key,
        collection_job_id=collection_job_id,
    )
    if collection_job is None:
        return CollectionAnalysisResult(404, "采集批次不存在")
    if collection_job["status"] != "succeeded":
        return CollectionAnalysisResult(409, "采集批次尚未成功完成")

    source_job_id = collection_job["source_job_id"] or collection_job_id
    target_brand, competitors = _resolve_brand_context(
        db,
        tenant_key=tenant_key,
        project_id=collection_job["project_id"],
    )
    if not target_brand:
        return CollectionAnalysisResult(422, "项目缺少 active target brand")

    plugin_map = plugins or _default_plugins()
    create_result = analysis_runs.create_analysis_run(
        db,
        tenant_key=tenant_key,
        analysis_run_id=run_id,
        collection_job_id=collection_job_id,
        plugin_versions=_plugin_versions(plugin_map),
        input_watermark=f"{source_job_id}:{started_at.isoformat()}",
        now=started_at,
    )
    if create_result.status_code != 200:
        return CollectionAnalysisResult(
            create_result.status_code,
            create_result.message,
            analysis_run=create_result.analysis_run,
            source_job_id=source_job_id,
            target_brand=target_brand,
            competitor_brands=competitors,
        )
    db.commit()

    start_result = analysis_runs.start_analysis_run(
        db,
        tenant_key=tenant_key,
        analysis_run_id=run_id,
        now=started_at,
    )
    if start_result.status_code != 200:
        return CollectionAnalysisResult(
            start_result.status_code,
            start_result.message,
            analysis_run=start_result.analysis_run,
            source_job_id=source_job_id,
            target_brand=target_brand,
            competitor_brands=competitors,
        )
    db.commit()

    source_rows = {
        "mention_status": (
            "llm_conversations",
            _fetch_rows(
                db,
                table_name="llm_conversations",
                tenant_key=tenant_key,
                source_job_id=source_job_id,
            ),
        ),
        "reference_status": (
            "llm_conversation_references",
            _fetch_rows(
                db,
                table_name="llm_conversation_references",
                tenant_key=tenant_key,
                source_job_id=source_job_id,
            ),
        ),
    }

    plugin_results: dict[str, AnalysisPluginRunResult] = {}
    try:
        for plugin_name, plugin in plugin_map.items():
            if plugin_name not in source_rows:
                continue
            source_table, rows = source_rows[plugin_name]
            plugin_results[plugin_name] = _run_plugin(
                plugin,
                plugin_name=plugin_name,
                source_table=source_table,
                rows=rows,
                target_brand=target_brand,
                analysis_run_id=run_id,
                db=db,
                competitors=competitors,
            )

        if not any(result.processed_records for result in plugin_results.values()):
            raise RuntimeError("采集批次没有可分析的原始数据")

        complete_result = analysis_runs.complete_analysis_run(
            db,
            tenant_key=tenant_key,
            analysis_run_id=run_id,
            status="succeeded",
            now=now or _now(),
        )
        db.commit()
        return CollectionAnalysisResult(
            complete_result.status_code,
            complete_result.message,
            analysis_run=complete_result.analysis_run,
            source_job_id=source_job_id,
            target_brand=target_brand,
            competitor_brands=competitors,
            plugin_results=plugin_results,
        )
    except Exception as exc:
        failed_result = analysis_runs.complete_analysis_run(
            db,
            tenant_key=tenant_key,
            analysis_run_id=run_id,
            status="failed",
            error_code="plugin_error",
            error_message=str(exc),
            now=now or _now(),
        )
        db.commit()
        return CollectionAnalysisResult(
            500,
            str(exc),
            analysis_run=failed_result.analysis_run,
            source_job_id=source_job_id,
            target_brand=target_brand,
            competitor_brands=competitors,
            plugin_results=plugin_results,
        )
