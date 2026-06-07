import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from sqlalchemy import bindparam, create_engine, text

from ...core.database_config import build_mysql_database_url, resolve_database_config
from ...core.plugin_interface import AnalysisPlugin, PluginRegistry


@dataclass(frozen=True)
class ImportStats:
    total_files: int
    succeeded_files: int
    failed_files: int
    total_answers: int
    inserted_rows: int
    skipped_rows: int
    failed_paths: List[str]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_analysis_config() -> Dict[str, Any]:
    config_path = _project_root() / "config" / "analysis_config.json"
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _get_db_cfg(config: Dict[str, Any]) -> Dict[str, Any]:
    db_cfg = (config.get("brand_analysis") or {}).get("database") or {}
    return resolve_database_config(db_cfg)


def _create_db_engine(db_cfg: Dict[str, Any]):
    url = build_mysql_database_url(db_cfg)
    return create_engine(url, pool_pre_ping=True)


def _get_import_directory(config: Dict[str, Any]) -> str:
    plugins_cfg = (config.get("brand_analysis") or {}).get("plugins") or {}
    plugin_cfg = plugins_cfg.get("import_mention_data") or {}
    directory = plugin_cfg.get("directory")
    if not isinstance(directory, str) or not directory.strip():
        raise ValueError(
            "Missing `brand_analysis.plugins.import_mention_data.directory`"
        )
    return directory.strip()


def _resolve_directory(directory: str) -> Path:
    p = Path(directory)
    if p.is_absolute():
        return p
    return _project_root() / p


def _list_json_files(directory_path: Path) -> List[Path]:
    if not directory_path.exists() or not directory_path.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    files = [p for p in directory_path.rglob("*.json") if p.is_file()]
    files.sort(key=lambda x: str(x).lower())
    return files


def _parse_date_from_payload(payload: Dict[str, Any], file_path: Path) -> date:
    date_dir = payload.get("date_directory")
    if isinstance(date_dir, str) and len(date_dir) == 8 and date_dir.isdigit():
        return datetime.strptime(date_dir, "%Y%m%d").date()

    parent = file_path.parent.name
    if len(parent) == 8 and parent.isdigit():
        return datetime.strptime(parent, "%Y%m%d").date()

    ts = payload.get("analysis_timestamp")
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts).date()
        except ValueError:
            pass

    return datetime.now().date()


def _iter_answers(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    data = payload.get("data")
    if not isinstance(data, dict):
        return []
    answers = data.get("answers")
    if isinstance(answers, dict):
        for value in answers.values():
            if isinstance(value, dict):
                yield value
        return
    if isinstance(answers, list):
        for item in answers:
            if isinstance(item, dict):
                yield item


def _to_tinyint_bool(value: Any) -> int:
    if value is True:
        return 1
    if value is False:
        return 0
    if isinstance(value, (int, float)):
        return 1 if value else 0
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"1", "true", "yes", "y", "t"}:
            return 1
        if v in {"0", "false", "no", "n", "f"}:
            return 0
    return 0


def _required_str(answer: Dict[str, Any], key: str) -> Optional[str]:
    value = answer.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        v = value.strip()
        return v if v else None
    v = str(value).strip()
    return v if v else None


def _build_insert_rows(
    answer_date: date, answers: Iterable[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], int]:
    rows: List[Dict[str, Any]] = []
    skipped = 0
    seen: Set[Tuple[Any, Any, Any]] = set()

    for a in answers:
        tenant_key = _required_str(a, "tenant_key")
        job_id = _required_str(a, "job_id")
        conversation_id = _required_str(a, "conversation_id")
        brand = _required_str(a, "brand")
        category = _required_str(a, "category")
        platform = _required_str(a, "platform")
        keyword = _required_str(a, "keyword")
        sentiment_status = _required_str(a, "sentiment_status")

        if not all(
            [
                tenant_key,
                job_id,
                conversation_id,
                brand,
                category,
                platform,
                keyword,
                sentiment_status,
            ]
        ):
            skipped += 1
            continue

        key = (tenant_key, job_id, conversation_id)
        if key in seen:
            skipped += 1
            continue
        seen.add(key)

        brands_found = a.get("brands_found")
        if brands_found is not None and not isinstance(brands_found, str):
            brands_found = json.dumps(brands_found, ensure_ascii=False)

        is_mentioned = _to_tinyint_bool(a.get("is_mentioned"))
        is_first_mentioned = _to_tinyint_bool(a.get("is_first_mentioned"))
        is_top3_mentioned = _to_tinyint_bool(a.get("is_top3_mentioned"))

        row = {
            "date": answer_date,
            "tenant_key": tenant_key,
            "job_id": job_id,
            "conversation_id": conversation_id,
            "brand": brand,
            "category": category,
            "platform": platform,
            "keyword": keyword,
            "is_mentioned": is_mentioned,
            "is_first_mentioned": is_first_mentioned,
            "is_top3_mentioned": is_top3_mentioned,
            "sentiment_status": sentiment_status,
            "brands_found": brands_found,
        }

        rows.append(row)

    return rows, skipped


def _chunks(
    items: Sequence[Dict[str, Any]], size: int
) -> Iterable[Sequence[Dict[str, Any]]]:
    if size <= 0:
        raise ValueError("chunk size must be positive")
    for i in range(0, len(items), size):
        yield items[slice(i, i + size)]


def _insert_rows(
    engine, rows: Sequence[Dict[str, Any]], chunk_size: int = 500
) -> int:
    if not rows:
        return 0

    sql = text(
        "INSERT INTO qa_brand_state "
        "(date, tenant_key, job_id, conversation_id, "
        "brand, category, platform, keyword, is_mentioned, "
        "is_first_mentioned, is_top3_mentioned, "
        "sentiment_status, brands_found) "
        "VALUES "
        "(:date, :tenant_key, :job_id, :conversation_id, "
        ":brand, :category, :platform, :keyword, :is_mentioned, "
        ":is_first_mentioned, :is_top3_mentioned, "
        ":sentiment_status, :brands_found)"
    )

    inserted = 0
    # Process in chunks
    for batch in _chunks(list(rows), chunk_size):
        batch_list = list(batch)
        conversation_ids = [
            r["conversation_id"]
            for r in batch_list
            if r.get("conversation_id")
        ]

        if not conversation_ids:
            continue

        check_sql = (
            text(
                "SELECT conversation_id FROM qa_brand_state "
                "WHERE conversation_id IN :conversation_ids"
            ).bindparams(bindparam("conversation_ids", expanding=True))
        )

        with engine.connect() as conn:
            existing_result = conn.execute(
                check_sql, {"conversation_ids": conversation_ids}
            ).fetchall()
            existing_ids = {row[0] for row in existing_result}

        # Filter out rows that already exist
        new_rows = [
            r
            for r in batch_list
            if r.get("conversation_id") not in existing_ids
        ]

        if not new_rows:
            continue

        with engine.begin() as conn:
            result = conn.execute(sql, new_rows)
            inserted += int(result.rowcount or 0)

    return inserted


def import_file_payload_to_db(
    engine, payload: Dict[str, Any], file_path: Path
) -> ImportStats:
    answer_date = _parse_date_from_payload(payload, file_path)
    answers = list(_iter_answers(payload))
    rows, skipped = _build_insert_rows(answer_date, answers)
    inserted = _insert_rows(engine, rows)
    return ImportStats(
        total_files=1,
        succeeded_files=1,
        failed_files=0,
        total_answers=len(answers),
        inserted_rows=inserted,
        skipped_rows=skipped,
        failed_paths=[],
    )


def import_directory_to_db(directory_path: Path) -> ImportStats:
    config = _load_analysis_config()
    db_cfg = _get_db_cfg(config)
    engine = _create_db_engine(db_cfg)

    files = _list_json_files(directory_path)
    total_answers = 0
    inserted_rows = 0
    skipped_rows = 0
    failed_paths: List[str] = []

    for file_path in files:
        try:
            with file_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            stats = import_file_payload_to_db(engine, payload, file_path)
            total_answers += stats.total_answers
            inserted_rows += stats.inserted_rows
            skipped_rows += stats.skipped_rows
        except Exception:
            failed_paths.append(str(file_path))

    succeeded = len(files) - len(failed_paths)
    return ImportStats(
        total_files=len(files),
        succeeded_files=succeeded,
        failed_files=len(failed_paths),
        total_answers=total_answers,
        inserted_rows=inserted_rows,
        skipped_rows=skipped_rows,
        failed_paths=failed_paths,
    )


@PluginRegistry.register(
    name="import_mention_data",
    description="从配置目录批量导入 mention_status JSON 到数据库 qa_brand_state",
    plugin_type="utility",
    requires_llm=False,
    enabled_by_default=False,
)
class ImportMentionDataPlugin(AnalysisPlugin):
    @property
    def name(self) -> str:
        return "import_mention_data"

    @property
    def description(self) -> str:
        return "从配置目录批量导入 mention_status JSON 到数据库 qa_brand_state"

    def analyze(self, text: str, brand_name: str) -> Dict[str, Any]:
        config = _load_analysis_config()
        directory = _get_import_directory(config)
        directory_path = _resolve_directory(directory)

        stats = import_directory_to_db(directory_path)
        return {
            "directory": str(directory_path),
            "total_files": stats.total_files,
            "succeeded_files": stats.succeeded_files,
            "failed_files": stats.failed_files,
            "total_answers": stats.total_answers,
            "inserted_rows": stats.inserted_rows,
            "skipped_rows": stats.skipped_rows,
            "failed_paths": stats.failed_paths,
        }
