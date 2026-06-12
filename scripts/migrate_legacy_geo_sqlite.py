import argparse
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, NamedTuple


DEFAULT_SOURCE = Path("data/geo_csv/geo.db")
DEFAULT_TARGET = Path("data/geo_csv/geo_migrated.db")
DEFAULT_SCHEMA = Path("api/database/schema_sqlite.sql")


class MigrationSummary(NamedTuple):
    source_path: str
    target_path: str
    job_count: int
    project_count: int
    analysis_run_count: int
    llm_conversation_rows: int
    llm_query_job_rows: int
    qa_brand_state_rows: int
    qa_reference_rows: int


def _stable_hash(*parts: Any, length: int = 12) -> str:
    raw = "|".join("" if part is None else str(part) for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:length]


def _now_text() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _connect_source_readonly(path: Path) -> sqlite3.Connection:
    uri = "file:" + str(path).replace("\\", "/") + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _connect_target(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
            (table,),
        ).fetchone()
        is not None
    )


def _columns(connection: sqlite3.Connection, table: str) -> list[str]:
    if not _table_exists(connection, table):
        return []
    return [
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({_quote_identifier(table)})")
    ]


def _count(connection: sqlite3.Connection, table: str) -> int:
    if not _table_exists(connection, table):
        return 0
    return int(connection.execute(f"SELECT COUNT(*) FROM {_quote_identifier(table)}").fetchone()[0])


def _insert(connection: sqlite3.Connection, table: str, values: dict[str, Any]) -> None:
    columns = list(values)
    quoted_columns = ", ".join(_quote_identifier(column) for column in columns)
    placeholders = ", ".join("?" for _ in columns)
    sql = f"INSERT INTO {_quote_identifier(table)} ({quoted_columns}) VALUES ({placeholders})"
    connection.execute(sql, [values[column] for column in columns])


def _select_rows(
    connection: sqlite3.Connection,
    table: str,
    columns: list[str] | None = None,
) -> list[sqlite3.Row]:
    if not _table_exists(connection, table):
        return []
    select_columns = "*" if columns is None else ", ".join(_quote_identifier(c) for c in columns)
    return list(connection.execute(f"SELECT {select_columns} FROM {_quote_identifier(table)}"))


def _copy_common_table(source: sqlite3.Connection, target: sqlite3.Connection, table: str) -> int:
    source_columns = _columns(source, table)
    target_columns = _columns(target, table)
    common_columns = [column for column in target_columns if column in source_columns]
    if not common_columns:
        return 0
    count = 0
    for row in _select_rows(source, table, common_columns):
        _insert(target, table, {column: row[column] for column in common_columns})
        count += 1
    return count


def _job_pairs(source: sqlite3.Connection) -> list[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for table in ("llm_query_jobs", "llm_conversations", "qa_brand_state", "qa_reference"):
        if not _table_exists(source, table):
            continue
        table_columns = set(_columns(source, table))
        if "tenant_key" not in table_columns or "job_id" not in table_columns:
            continue
        for row in source.execute(
            f"""
            SELECT DISTINCT tenant_key, job_id
            FROM {_quote_identifier(table)}
            WHERE tenant_key IS NOT NULL AND job_id IS NOT NULL
            """
        ):
            pairs.add((row["tenant_key"], row["job_id"]))
    return sorted(pairs)


def _first_non_empty(
    source: sqlite3.Connection,
    tenant_key: str,
    job_id: str,
    table: str,
    column: str,
) -> Any:
    if not _table_exists(source, table) or column not in _columns(source, table):
        return None
    row = source.execute(
        f"""
        SELECT { _quote_identifier(column) } AS value
        FROM { _quote_identifier(table) }
        WHERE tenant_key = ? AND job_id = ?
          AND { _quote_identifier(column) } IS NOT NULL
          AND { _quote_identifier(column) } != ''
        ORDER BY id ASC
        LIMIT 1
        """,
        (tenant_key, job_id),
    ).fetchone()
    return row["value"] if row else None


def _date_range(source: sqlite3.Connection, tenant_key: str, job_id: str) -> tuple[Any, Any]:
    candidates: list[Any] = []
    date_sources = (
        ("llm_conversations", "generated_date"),
        ("qa_brand_state", "date"),
        ("qa_reference", "date"),
    )
    for table, column in date_sources:
        if not _table_exists(source, table) or column not in _columns(source, table):
            continue
        row = source.execute(
            f"""
            SELECT MIN({_quote_identifier(column)}) AS min_date,
                   MAX({_quote_identifier(column)}) AS max_date
            FROM {_quote_identifier(table)}
            WHERE tenant_key = ? AND job_id = ?
            """,
            (tenant_key, job_id),
        ).fetchone()
        if row and row["min_date"] is not None:
            candidates.extend([row["min_date"], row["max_date"]])
    if not candidates:
        return None, None
    return min(candidates), max(candidates)


def _timestamp_range(source: sqlite3.Connection, tenant_key: str, job_id: str) -> tuple[str, str]:
    values: list[Any] = []
    for table in ("llm_query_jobs", "llm_conversations", "qa_brand_state", "qa_reference"):
        if not _table_exists(source, table):
            continue
        for column in ("created_at", "updated_at", "extracted_at"):
            if column not in _columns(source, table):
                continue
            rows = source.execute(
                f"""
                SELECT MIN({_quote_identifier(column)}) AS min_value,
                       MAX({_quote_identifier(column)}) AS max_value
                FROM {_quote_identifier(table)}
                WHERE tenant_key = ? AND job_id = ?
                """,
                (tenant_key, job_id),
            ).fetchone()
            if rows and rows["min_value"] is not None:
                values.extend([rows["min_value"], rows["max_value"]])
    if not values:
        now = _now_text()
        return now, now
    return str(min(values)), str(max(values))


def _job_mapping(source: sqlite3.Connection) -> dict[tuple[str, str], dict[str, Any]]:
    mappings: dict[tuple[str, str], dict[str, Any]] = {}
    for tenant_key, job_id in _job_pairs(source):
        digest = _stable_hash(tenant_key, job_id)
        start_date, end_date = _date_range(source, tenant_key, job_id)
        created_at, updated_at = _timestamp_range(source, tenant_key, job_id)
        category = (
            _first_non_empty(source, tenant_key, job_id, "llm_query_jobs", "category")
            or _first_non_empty(source, tenant_key, job_id, "llm_conversations", "category")
            or _first_non_empty(source, tenant_key, job_id, "qa_brand_state", "category")
        )
        mappings[(tenant_key, job_id)] = {
            "tenant_key": tenant_key,
            "job_id": job_id,
            "project_id": f"prj_legacy_{digest}",
            "collection_job_id": f"col_legacy_{digest}",
            "analysis_run_id": f"ar_legacy_{digest}",
            "prompt_set_id": f"ps_legacy_{digest}",
            "project_name": f"Legacy GEO {job_id}",
            "category": category,
            "window_start": start_date,
            "window_end": end_date,
            "created_at": created_at,
            "updated_at": updated_at,
        }
    return mappings


def _ensure_tenant(target: sqlite3.Connection, tenant_key: str, now: str) -> None:
    exists = target.execute(
        "SELECT 1 FROM tenants WHERE tenant_key = ? LIMIT 1",
        (tenant_key,),
    ).fetchone()
    if exists:
        return
    _insert(
        target,
        "tenants",
        {
            "tenant_key": tenant_key,
            "tenant_name": f"Legacy Tenant {tenant_key}",
            "status": "active",
            "created_at": now,
            "updated_at": now,
        },
    )


def _query_count(source: sqlite3.Connection, tenant_key: str, job_id: str) -> int:
    if not _table_exists(source, "llm_query_jobs"):
        return 0
    return int(
        source.execute(
            """
            SELECT COUNT(*)
            FROM llm_query_jobs
            WHERE tenant_key = ? AND job_id = ?
            """,
            (tenant_key, job_id),
        ).fetchone()[0]
    )


def _conversation_count(source: sqlite3.Connection, tenant_key: str, job_id: str) -> int:
    if not _table_exists(source, "llm_conversations"):
        return 0
    return int(
        source.execute(
            """
            SELECT COUNT(DISTINCT conversation_id)
            FROM llm_conversations
            WHERE tenant_key = ? AND job_id = ?
            """,
            (tenant_key, job_id),
        ).fetchone()[0]
    )


def _insert_project_model(
    source: sqlite3.Connection,
    target: sqlite3.Connection,
    mappings: dict[tuple[str, str], dict[str, Any]],
) -> dict[tuple[str, str, str], str]:
    prompt_item_lookup: dict[tuple[str, str, str], str] = {}
    for key, mapping in mappings.items():
        tenant_key, job_id = key
        _ensure_tenant(target, tenant_key, mapping["created_at"])
        _insert(
            target,
            "monitoring_projects",
            {
                "tenant_key": tenant_key,
                "project_id": mapping["project_id"],
                "name": mapping["project_name"],
                "industry": None,
                "category": mapping["category"],
                "status": "active",
                "created_by": None,
                "created_at": mapping["created_at"],
                "updated_at": mapping["updated_at"],
            },
        )
        _insert_project_brands(source, target, mapping)
        _insert(
            target,
            "prompt_sets",
            {
                "tenant_key": tenant_key,
                "project_id": mapping["project_id"],
                "prompt_set_id": mapping["prompt_set_id"],
                "version": 1,
                "name": f"Legacy prompt set {job_id}",
                "status": "active",
                "created_at": mapping["created_at"],
                "updated_at": mapping["updated_at"],
            },
        )
        prompt_item_lookup.update(_insert_prompt_items(source, target, mapping))
    return prompt_item_lookup


def _parse_competitors(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [value]
        if isinstance(parsed, list):
            return [str(item) for item in parsed if str(item).strip()]
        if isinstance(parsed, str) and parsed.strip():
            return [parsed]
    return []


def _insert_project_brands(
    source: sqlite3.Connection,
    target: sqlite3.Connection,
    mapping: dict[str, Any],
) -> None:
    tenant_key = mapping["tenant_key"]
    job_id = mapping["job_id"]
    target_brands: set[str] = set()
    all_brands: dict[str, int] = {}

    if _table_exists(source, "llm_query_jobs"):
        for row in source.execute(
            """
            SELECT brand, competitor
            FROM llm_query_jobs
            WHERE tenant_key = ? AND job_id = ?
            ORDER BY id ASC
            """,
            (tenant_key, job_id),
        ):
            if row["brand"]:
                brand = str(row["brand"])
                target_brands.add(brand)
                all_brands[brand] = all_brands.get(brand, 0) + 1
            for competitor in _parse_competitors(row["competitor"]):
                all_brands[competitor] = all_brands.get(competitor, 0) + 1

    for table in ("qa_brand_state", "llm_conversations"):
        if not _table_exists(source, table) or "brand" not in _columns(source, table):
            continue
        for row in source.execute(
            f"""
            SELECT brand, COUNT(*) AS count
            FROM {_quote_identifier(table)}
            WHERE tenant_key = ? AND job_id = ? AND brand IS NOT NULL AND brand != ''
            GROUP BY brand
            """,
            (tenant_key, job_id),
        ):
            brand = str(row["brand"])
            all_brands[brand] = all_brands.get(brand, 0) + int(row["count"])

    if not target_brands and all_brands:
        target_brands.add(sorted(all_brands.items(), key=lambda item: (-item[1], item[0]))[0][0])

    for brand_name in sorted(all_brands):
        role = "target" if brand_name in target_brands else "competitor"
        _insert(
            target,
            "project_brands",
            {
                "tenant_key": tenant_key,
                "project_id": mapping["project_id"],
                "brand_id": f"br_legacy_{_stable_hash(mapping['project_id'], brand_name)}",
                "brand_name": brand_name,
                "role": role,
                "aliases": "[]",
                "status": "active",
                "created_at": mapping["created_at"],
                "updated_at": mapping["updated_at"],
            },
        )


def _prompt_candidates(
    source: sqlite3.Connection,
    mapping: dict[str, Any],
) -> list[tuple[str, str]]:
    tenant_key = mapping["tenant_key"]
    job_id = mapping["job_id"]
    candidates: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for table in ("llm_query_jobs", "llm_conversations"):
        if not _table_exists(source, table):
            continue
        required = {"keyword", "query_content"}
        if not required.issubset(set(_columns(source, table))):
            continue
        for row in source.execute(
            f"""
            SELECT keyword, query_content
            FROM {_quote_identifier(table)}
            WHERE tenant_key = ? AND job_id = ?
              AND keyword IS NOT NULL AND query_content IS NOT NULL
            ORDER BY id ASC
            """,
            (tenant_key, job_id),
        ):
            candidate = (str(row["keyword"]), str(row["query_content"]))
            if candidate not in seen:
                candidates.append(candidate)
                seen.add(candidate)
    return candidates


def _insert_prompt_items(
    source: sqlite3.Connection,
    target: sqlite3.Connection,
    mapping: dict[str, Any],
) -> dict[tuple[str, str, str], str]:
    lookup: dict[tuple[str, str, str], str] = {}
    for index, (keyword, query_content) in enumerate(_prompt_candidates(source, mapping), start=1):
        prompt_item_id = f"pi_legacy_{_stable_hash(mapping['prompt_set_id'], index, query_content)}"
        _insert(
            target,
            "prompt_items",
            {
                "tenant_key": mapping["tenant_key"],
                "prompt_set_id": mapping["prompt_set_id"],
                "prompt_item_id": prompt_item_id,
                "keyword": keyword,
                "query_content": query_content,
                "status": "active",
                "sort_order": index,
                "created_at": mapping["created_at"],
                "updated_at": mapping["updated_at"],
            },
        )
        lookup[(mapping["tenant_key"], mapping["job_id"], query_content)] = prompt_item_id
    return lookup


def _insert_collection_model(
    source: sqlite3.Connection,
    target: sqlite3.Connection,
    mappings: dict[tuple[str, str], dict[str, Any]],
    prompt_item_lookup: dict[tuple[str, str, str], str],
) -> None:
    for key, mapping in mappings.items():
        tenant_key, job_id = key
        query_count = _query_count(source, tenant_key, job_id)
        conversation_count = _conversation_count(source, tenant_key, job_id)
        _insert(
            target,
            "collection_jobs",
            {
                "tenant_key": tenant_key,
                "collection_job_id": mapping["collection_job_id"],
                "project_id": mapping["project_id"],
                "prompt_set_id": mapping["prompt_set_id"],
                "source_job_id": job_id,
                "status": "succeeded",
                "window_start": mapping["window_start"],
                "window_end": mapping["window_end"],
                "expected_task_count": query_count,
                "succeeded_task_count": conversation_count,
                "failed_task_count": 0,
                "created_by": None,
                "created_at": mapping["created_at"],
                "updated_at": mapping["updated_at"],
            },
        )
        _insert_collection_tasks(source, target, mapping, prompt_item_lookup)


def _task_candidates(
    source: sqlite3.Connection,
    mapping: dict[str, Any],
) -> list[dict[str, Any]]:
    tenant_key = mapping["tenant_key"]
    job_id = mapping["job_id"]
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    if _table_exists(source, "llm_conversations"):
        for row in source.execute(
            """
            SELECT platform, keyword, query_content, MIN(created_at) AS created_at,
                   MAX(updated_at) AS updated_at
            FROM llm_conversations
            WHERE tenant_key = ? AND job_id = ?
            GROUP BY platform, keyword, query_content
            ORDER BY MIN(id)
            """,
            (tenant_key, job_id),
        ):
            key = (str(row["platform"]), str(row["query_content"]))
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                {
                    "platform": row["platform"],
                    "keyword": row["keyword"],
                    "query_content": row["query_content"],
                    "status": "succeeded",
                    "created_at": row["created_at"] or mapping["created_at"],
                    "updated_at": row["updated_at"] or mapping["updated_at"],
                }
            )

    if not candidates and _table_exists(source, "llm_query_jobs"):
        for row in source.execute(
            """
            SELECT keyword, query_content, created_at, updated_at
            FROM llm_query_jobs
            WHERE tenant_key = ? AND job_id = ?
            ORDER BY id
            """,
            (tenant_key, job_id),
        ):
            candidates.append(
                {
                    "platform": "legacy",
                    "keyword": row["keyword"],
                    "query_content": row["query_content"],
                    "status": "pending",
                    "created_at": row["created_at"] or mapping["created_at"],
                    "updated_at": row["updated_at"] or mapping["updated_at"],
                }
            )
    return candidates


def _insert_collection_tasks(
    source: sqlite3.Connection,
    target: sqlite3.Connection,
    mapping: dict[str, Any],
    prompt_item_lookup: dict[tuple[str, str, str], str],
) -> None:
    for index, candidate in enumerate(_task_candidates(source, mapping), start=1):
        collection_task_id = f"ct_legacy_{_stable_hash(mapping['collection_job_id'], index)}"
        prompt_item_id = prompt_item_lookup.get(
            (mapping["tenant_key"], mapping["job_id"], candidate["query_content"])
        )
        _insert(
            target,
            "collection_tasks",
            {
                "tenant_key": mapping["tenant_key"],
                "collection_task_id": collection_task_id,
                "collection_job_id": mapping["collection_job_id"],
                "project_id": mapping["project_id"],
                "prompt_set_id": mapping["prompt_set_id"],
                "prompt_item_id": prompt_item_id,
                "platform": candidate["platform"],
                "query_content": candidate["query_content"],
                "run_index": 1,
                "status": candidate["status"],
                "lease_owner": None,
                "lease_until": None,
                "reserved_at": None,
                "started_at": candidate["created_at"] if candidate["status"] == "succeeded" else None,
                "finished_at": candidate["updated_at"] if candidate["status"] == "succeeded" else None,
                "attempt_count": 1 if candidate["status"] == "succeeded" else 0,
                "max_attempts": 3,
                "last_error_code": None,
                "last_error_message": None,
                "created_at": candidate["created_at"],
                "updated_at": candidate["updated_at"],
            },
        )
        if candidate["status"] == "succeeded":
            _insert(
                target,
                "collection_attempts",
                {
                    "tenant_key": mapping["tenant_key"],
                    "attempt_id": f"ca_legacy_{_stable_hash(collection_task_id)}",
                    "collection_task_id": collection_task_id,
                    "executor_id": None,
                    "status": "succeeded",
                    "started_at": candidate["created_at"],
                    "finished_at": candidate["updated_at"],
                    "error_code": None,
                    "error_message": None,
                    "raw_response_id": None,
                    "created_at": candidate["created_at"],
                    "updated_at": candidate["updated_at"],
                },
            )


def _insert_analysis_runs(
    target: sqlite3.Connection,
    mappings: dict[tuple[str, str], dict[str, Any]],
) -> None:
    for mapping in mappings.values():
        _insert(
            target,
            "analysis_runs",
            {
                "tenant_key": mapping["tenant_key"],
                "analysis_run_id": mapping["analysis_run_id"],
                "project_id": mapping["project_id"],
                "collection_job_id": mapping["collection_job_id"],
                "status": "succeeded",
                "plugin_versions": json.dumps({"legacy_migration": 1}, sort_keys=True),
                "model_config_hash": None,
                "input_watermark": mapping["job_id"],
                "started_at": mapping["created_at"],
                "finished_at": mapping["updated_at"],
                "stale_at": None,
                "error_code": None,
                "error_message": None,
                "created_at": mapping["created_at"],
                "updated_at": mapping["updated_at"],
            },
        )


def _copy_llm_query_jobs(
    source: sqlite3.Connection,
    target: sqlite3.Connection,
    mappings: dict[tuple[str, str], dict[str, Any]],
) -> int:
    source_columns = _columns(source, "llm_query_jobs")
    target_columns = _columns(target, "llm_query_jobs")
    if not source_columns or not target_columns:
        return 0
    insert_columns = [column for column in target_columns if column in source_columns]
    if "project_id" in target_columns and "project_id" not in insert_columns:
        insert_columns.insert(insert_columns.index("category"), "project_id")

    count = 0
    for row in _select_rows(source, "llm_query_jobs", source_columns):
        values = {}
        for column in insert_columns:
            if column == "project_id":
                values[column] = mappings[(row["tenant_key"], row["job_id"])]["project_id"]
            else:
                values[column] = row[column]
        _insert(target, "llm_query_jobs", values)
        count += 1
    return count


def _copy_fact_table_with_analysis_run(
    source: sqlite3.Connection,
    target: sqlite3.Connection,
    table: str,
    mappings: dict[tuple[str, str], dict[str, Any]],
) -> int:
    source_columns = _columns(source, table)
    target_columns = _columns(target, table)
    if not source_columns or not target_columns:
        return 0
    insert_columns = [column for column in target_columns if column in source_columns]
    if "analysis_run_id" in target_columns and "analysis_run_id" not in insert_columns:
        insert_columns.insert(insert_columns.index("date"), "analysis_run_id")

    count = 0
    for row in _select_rows(source, table, source_columns):
        values = {}
        for column in insert_columns:
            if column == "analysis_run_id":
                values[column] = mappings[(row["tenant_key"], row["job_id"])]["analysis_run_id"]
            else:
                values[column] = row[column]
        _insert(target, table, values)
        count += 1
    return count


def _prepare_target(target_path: Path, overwrite: bool) -> None:
    if target_path.exists():
        if not overwrite:
            raise FileExistsError(f"Target database already exists: {target_path}")
        target_path.unlink()
    for suffix in ("-wal", "-shm"):
        sidecar = Path(str(target_path) + suffix)
        if sidecar.exists():
            sidecar.unlink()
    target_path.parent.mkdir(parents=True, exist_ok=True)


def migrate_legacy_geo_sqlite(
    source_path: Path | str = DEFAULT_SOURCE,
    target_path: Path | str = DEFAULT_TARGET,
    schema_path: Path | str = DEFAULT_SCHEMA,
    *,
    overwrite: bool = False,
) -> MigrationSummary:
    source_path = Path(source_path)
    target_path = Path(target_path)
    schema_path = Path(schema_path)

    if source_path.resolve() == target_path.resolve():
        raise ValueError("Source and target database paths must be different")
    if not source_path.exists():
        raise FileNotFoundError(f"Source database not found: {source_path}")
    if not schema_path.exists():
        raise FileNotFoundError(f"SQLite schema not found: {schema_path}")

    _prepare_target(target_path, overwrite)

    source = _connect_source_readonly(source_path)
    target = _connect_target(target_path)
    try:
        target.executescript(schema_path.read_text(encoding="utf-8"))
        mappings = _job_mapping(source)

        for table in (
            "tenants",
            "users",
            "user_tenants",
            "tenant_configs",
            "invitation_codes",
            "executors",
        ):
            _copy_common_table(source, target, table)

        prompt_item_lookup = _insert_project_model(source, target, mappings)
        _insert_collection_model(source, target, mappings, prompt_item_lookup)
        _insert_analysis_runs(target, mappings)

        llm_query_job_rows = _copy_llm_query_jobs(source, target, mappings)
        _copy_common_table(source, target, "llm_conversations")
        _copy_common_table(source, target, "llm_conversation_references")
        qa_brand_state_rows = _copy_fact_table_with_analysis_run(
            source, target, "qa_brand_state", mappings
        )
        qa_reference_rows = _copy_fact_table_with_analysis_run(
            source, target, "qa_reference", mappings
        )

        target.commit()
        return MigrationSummary(
            source_path=str(source_path),
            target_path=str(target_path),
            job_count=len(mappings),
            project_count=_count(target, "monitoring_projects"),
            analysis_run_count=_count(target, "analysis_runs"),
            llm_conversation_rows=_count(target, "llm_conversations"),
            llm_query_job_rows=llm_query_job_rows,
            qa_brand_state_rows=qa_brand_state_rows,
            qa_reference_rows=qa_reference_rows,
        )
    except Exception:
        target.rollback()
        raise
    finally:
        source.close()
        target.close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate legacy GEO SQLite data into the current Brand Dashboard schema."
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = migrate_legacy_geo_sqlite(
        args.source,
        args.target,
        args.schema,
        overwrite=args.overwrite,
    )
    print(json.dumps(summary._asdict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
