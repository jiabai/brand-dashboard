import argparse
import json
import logging
import os
import re
import uuid
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

from .business_services.llm_brand_recognizer import LLMBrandRecognizer
from .core.database_config import (
    DatabaseConfigError,
    build_mysql_database_url,
    resolve_database_config,
)
from .core.plugin_interface import PluginRegistry
from .core.plugin_manager import PluginManager

# 配置根日志记录器
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BrandAnalyzer:
    """品牌分析器主类"""

    def __init__(self, config_path: Optional[str] = None):
        try:
            self.config = self._load_config(config_path)

            self._validate_config(self.config)

            # 使用插件管理器
            logger.info("Using PluginManager...")
            self.plugin_manager = PluginManager(self.config)
            self._db_engine = None
            self.llm_recognizer = None
            self.competitors: List[str] = []

            # 验证插件管理器是否正确初始化
            if self.plugin_manager is None:
                raise RuntimeError("Failed to initialize PluginManager")

        except Exception as e:
            logger.error("Failed to initialize BrandAnalyzer: %s", e)
            raise

    def set_competitors(self, competitors: List[str]) -> None:
        normalized: List[str] = []
        for c in competitors or []:
            if not isinstance(c, str):
                continue
            v = c.strip()
            if not v:
                continue
            if v not in normalized:
                normalized.append(v)
        self.competitors = normalized

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件"""
        candidate_paths: List[Path] = []
        if config_path:
            candidate_paths.append(Path(config_path))

        default_config_path = (
            Path(__file__).resolve().parent.parent / "config" / "analysis_config.json"
        )
        project_root = Path(__file__).resolve().parent.parent
        env_path = project_root / ".env"
        if load_dotenv and env_path.exists():
            load_dotenv(dotenv_path=env_path)
        candidate_paths.append(default_config_path)

        last_error: Optional[Exception] = None

        for path in candidate_paths:
            if not path.exists():
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                if not isinstance(config, dict) or not config:
                    raise ValueError("Configuration must be a non-empty object")
                brand_cfg = config.get("brand_analysis")
                if isinstance(brand_cfg, dict):
                    llm_cfg = brand_cfg.get("llm")
                    if isinstance(llm_cfg, dict):
                        env_mapping = {
                            "LLM_API_KEY": "apiKey",
                            "LLM_BASE_URL": "baseURL",
                            "LLM_MODEL": "model",
                            "LLM_PROVIDER": "provider",
                        }
                        for env_key, config_key in env_mapping.items():
                            env_val = os.environ.get(env_key)
                            if env_val:
                                current_val = llm_cfg.get(config_key)
                                if (
                                    not current_val
                                    or current_val == "your-api-key-here"
                                ):
                                    llm_cfg[config_key] = env_val
                logger.info("Successfully loaded config from %s", path)
                return config
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON format in config file %s: %s", path, e)
                raise
            except Exception as e:
                last_error = e
                logger.error("Failed to load config from %s: %s", path, e)

        if not default_config_path.exists():
            logger.warning("Default config file not found at %s", default_config_path)

        logger.error("No valid configuration found")
        raise FileNotFoundError("No valid configuration file found") from last_error

    def _extract_plugin_datasources(
        self, plugin_name: str, plugin_cfg: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        datasources = plugin_cfg.get("datasources")
        if isinstance(datasources, list) and datasources:
            normalized: List[Dict[str, Any]] = []
            for ds in datasources:
                if not isinstance(ds, dict):
                    continue
                table = ds.get("table")
                if not isinstance(table, str) or not table.strip():
                    continue
                table_name = table.strip()
                if not re.match(r"^[A-Za-z0-9_]+$", table_name):
                    continue
                fields = ds.get("fields")
                if fields is None:
                    normalized.append({"table": table_name, "fields": None})
                    continue
                if not isinstance(fields, list):
                    normalized.append({"table": table_name, "fields": None})
                    continue
                field_list = [
                    str(f).strip() for f in fields if isinstance(f, str) and f.strip()
                ]
                normalized.append(
                    {"table": table_name, "fields": field_list if field_list else None}
                )
            if normalized:
                return normalized

        table_name = plugin_cfg.get("table")
        if isinstance(table_name, str):
            table_name = table_name.strip()
        if table_name and re.match(r"^[A-Za-z0-9_]+$", table_name):
            fields = plugin_cfg.get("fields")
            if isinstance(fields, list):
                field_list = [
                    str(f).strip() for f in fields if isinstance(f, str) and f.strip()
                ]
                return [{"table": str(table_name), "fields": field_list or None}]
            return [{"table": str(table_name), "fields": None}]

        return []

    def _validate_config(self, config: Dict[str, Any]) -> None:
        errors: List[str] = []

        if not isinstance(config, dict) or not config:
            raise ValueError("Invalid or empty configuration")

        brand_cfg = config.get("brand_analysis")
        if not isinstance(brand_cfg, dict):
            errors.append("Missing or invalid `brand_analysis` object")
            raise ValueError("; ".join(errors))

        plugins_cfg = brand_cfg.get("plugins")
        if not isinstance(plugins_cfg, dict) or not plugins_cfg:
            errors.append("Missing or invalid `brand_analysis.plugins` object")

        llm_cfg = brand_cfg.get("llm", {})
        db_cfg = brand_cfg.get("database", {})

        enabled_plugins: List[Tuple[str, Dict[str, Any]]] = []
        if isinstance(plugins_cfg, dict):
            for plugin_name, plugin_cfg in plugins_cfg.items():
                if not isinstance(plugin_name, str) or not plugin_name.strip():
                    errors.append("Invalid plugin name in `brand_analysis.plugins`")
                    continue

                if not isinstance(plugin_cfg, dict):
                    errors.append(f"Invalid plugin config for `{plugin_name}`")
                    continue

                enabled = plugin_cfg.get("enabled", True)
                if not isinstance(enabled, bool):
                    errors.append(
                        f"`brand_analysis.plugins.{plugin_name}.enabled` must be bool"
                    )
                    continue

                if enabled:
                    enabled_plugins.append((plugin_name, plugin_cfg))

                table_name = plugin_cfg.get("table")
                if table_name is not None and not isinstance(table_name, str):
                    errors.append(
                        f"`brand_analysis.plugins.{plugin_name}.table` must be string"
                    )
                if isinstance(table_name, str):
                    if table_name.strip() and not re.match(
                        r"^[A-Za-z0-9_]+$", table_name.strip()
                    ):
                        errors.append(
                            f"`brand_analysis.plugins.{plugin_name}.table` "
                            "has invalid value"
                        )

                datasources = plugin_cfg.get("datasources")
                if datasources is not None and not isinstance(datasources, list):
                    errors.append(
                        (
                            f"`brand_analysis.plugins.{plugin_name}.datasources` "
                            "must be list"
                        )
                    )
                if isinstance(datasources, list):
                    for idx, ds in enumerate(datasources):
                        ds_path = (
                            f"`brand_analysis.plugins.{plugin_name}.datasources[{idx}]`"
                        )
                        if not isinstance(ds, dict):
                            errors.append(f"{ds_path} must be object")
                            continue
                        ds_table = ds.get("table")
                        if not isinstance(ds_table, str) or not ds_table.strip():
                            errors.append(f"{ds_path}.table must be string")
                            continue
                        if not re.match(r"^[A-Za-z0-9_]+$", ds_table.strip()):
                            errors.append(f"{ds_path}.table has invalid value")
                        ds_fields = ds.get("fields")
                        if ds_fields is not None:
                            if not isinstance(ds_fields, list) or not all(
                                isinstance(f, str) for f in ds_fields
                            ):
                                errors.append(
                                    f"{ds_path}.fields must be list of strings"
                                )

                output_path = plugin_cfg.get("output")
                if output_path is not None and not isinstance(output_path, str):
                    errors.append(
                        f"`brand_analysis.plugins.{plugin_name}.output` must be string"
                    )

        plugins_need_db = any(
            bool(self._extract_plugin_datasources(name, cfg))
            for name, cfg in enabled_plugins
        )
        if plugins_need_db:
            ok, msg = self._validate_database_config(db_cfg)
            if not ok:
                errors.append(msg)

        plugins_need_llm = any(
            name in {"mention_status", "extract_source", "llm_ping"}
            for name, _ in enabled_plugins
        )
        if plugins_need_llm:
            ok, msg = self._validate_llm_config(llm_cfg)
            if not ok:
                errors.append(msg)

        if errors:
            raise ValueError("; ".join(errors))

    def _validate_database_config(self, db_cfg: Any) -> Tuple[bool, str]:
        try:
            resolve_database_config(db_cfg)
            return True, ""
        except DatabaseConfigError as exc:
            return False, str(exc)

    def _validate_llm_config(self, llm_cfg: Any) -> Tuple[bool, str]:
        if not isinstance(llm_cfg, dict) or not llm_cfg:
            return False, "Missing or invalid `brand_analysis.llm` object"

        enabled = llm_cfg.get("enabled", True)
        if not isinstance(enabled, bool):
            return False, "`brand_analysis.llm.enabled` must be bool"
        if not enabled:
            return (
                False,
                "`brand_analysis.llm.enabled` is false while LLM plugins are enabled",
            )

        api_key = self._get_first_present(llm_cfg, ["apiKey", "api_key"], "")
        base_url = self._get_first_present(llm_cfg, ["baseURL", "base_url"], "")
        model = self._get_first_present(llm_cfg, ["model"], "")

        if (
            not isinstance(api_key, str)
            or not api_key.strip()
            or api_key == "your-api-key-here"
        ):
            return False, "Missing or invalid `brand_analysis.llm.apiKey`"
        if not isinstance(base_url, str) or not base_url.strip():
            return False, "Missing or invalid `brand_analysis.llm.baseURL`"
        if not isinstance(model, str) or not model.strip():
            return False, "Missing or invalid `brand_analysis.llm.model`"

        timeout = self._get_first_present(llm_cfg, ["timeout"], 30000)
        if not isinstance(timeout, int) or timeout <= 0:
            return False, "Invalid `brand_analysis.llm.timeout`"
        max_retries = self._get_first_present(
            llm_cfg, ["maxRetries", "max_retries"], 2
        )
        if not isinstance(max_retries, int) or max_retries < 0:
            return False, "Invalid `brand_analysis.llm.maxRetries`"
        max_tokens = self._get_first_present(
            llm_cfg, ["maxTokens", "max_tokens"], 2000
        )
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            return False, "Invalid `brand_analysis.llm.maxTokens`"

        return True, ""

    def analyze_text(
        self,
        text: str,
        brand_name: str,
        plugins_to_run: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if self.plugin_manager is None:
            logger.error("Plugin manager is None!")
            return {"error": "Plugin manager not initialized"}

        # 获取启用的插件列表
        if plugins_to_run:
            enabled_plugins = plugins_to_run
        else:
            enabled_plugins = self._get_enabled_plugins()

        # 初始化LLM识别器（如果需要）
        llm_recognizer = (
            self._get_llm_recognizer()
            if self._needs_llm_recognizer(enabled_plugins)
            else None
        )

        # 运行启用的插件
        plugin_results = {}

        for plugin_name in enabled_plugins:
            plugin = self.plugin_manager.get_plugin(plugin_name)
            if plugin is None:
                logger.warning("Plugin %s is None!", plugin_name)
                continue

            try:
                # 如果插件需要LLM识别器，设置它
                if hasattr(plugin, "set_llm_recognizer") and llm_recognizer:
                    plugin.set_llm_recognizer(llm_recognizer)
                if hasattr(plugin, "set_competitors"):
                    plugin.set_competitors(self.competitors)

                result = plugin.analyze(text, brand_name)
                plugin_results[plugin_name] = result
            except Exception as e:
                plugin_results[plugin_name] = self._handle_plugin_exception(
                    plugin_name, e
                )

        result: Dict[str, Any] = {
            "brand_name": brand_name,
            "analysis_timestamp": self._get_timestamp(),
            "config_used": self.config,
            "metrics": plugin_results,
            "summary": {},
        }

        return result

    def _handle_plugin_exception(
        self, plugin_name: str, exc: Exception
    ) -> Dict[str, str]:
        logger.error("Plugin %s error: %s", plugin_name, exc, exc_info=True)
        return {"error": str(exc)}

    def _get_enabled_plugins(self) -> list:
        enabled_plugins = []

        # 检查插件配置
        plugins_config = (
            self.config.get("brand_analysis", {}).get("plugins", {})
        )

        for plugin_name, plugin_config in plugins_config.items():
            if plugin_config.get("enabled", True):
                # Include all enabled plugins. Utility plugins are allowed.
                enabled_plugins.append(plugin_name)

        # 如果没有配置启用的插件，返回空列表并记录日志
        if not enabled_plugins:
            logger.info("No plugins are enabled in the configuration")
            return []

        logger.debug("final enabled_plugins: %s", enabled_plugins)
        return enabled_plugins

    def run_plugin(
        self, plugin_name: str, brand_name: str = ""
    ) -> Dict[str, Any]:
        plugin = self.plugin_manager.get_plugin(plugin_name)
        if plugin is None:
            error_message = (
                f"Plugin not found or not enabled: {plugin_name}"
            )
            return {"error": error_message}
        try:
            return plugin.analyze("", brand_name)
        except Exception as e:
            return {"error": str(e)}

    def _save_plugin_batch_result(
        self, plugin_name: str, data: Any, date_dir: str, brand_name: str
    ):
        """
        保存插件的批处理结果到指定目录

        Args:
            plugin_name: 插件名称
            data: 插件分析结果
            date_dir: 日期目录名称
            brand_name: 品牌名称
        """
        try:
            # 获取插件配置
            plugins_config = (
                self.config.get("brand_analysis", {}).get("plugins", {})
            )
            plugin_config = plugins_config.get(plugin_name, {})
            output_base_dir = plugin_config.get("output")

            if not output_base_dir:
                logger.debug(
                    "No output directory configured for plugin %s, "
                    "skipping save",
                    plugin_name,
                )
                return

            # 构建输出路径: output_base / date_dir
            output_dir = os.path.join(output_base_dir, date_dir)

            # 确保目录存在
            os.makedirs(output_dir, exist_ok=True)

            # 生成带时间戳的文件名（格式：时间戳_uuid.json）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{uuid.uuid4()}.json"
            output_path = os.path.join(output_dir, filename)

            # 构建保存的数据结构
            save_data = {
                "brand_name": brand_name,
                "plugin_name": plugin_name,
                "analysis_timestamp": self._get_timestamp(),
                "date_directory": date_dir,
                "data": data,
            }

            def _json_default(obj: Any):
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                raise TypeError(
                    f"Object of type {type(obj).__name__} is not JSON serializable"
                )

            # 保存文件
            with open(output_path, "w", encoding="utf-8") as f:
                # 检查配置是否需要pretty print
                pretty_print = (
                    self.config.get("brand_analysis", {})
                    .get("output", {})
                    .get("pretty_print", False)
                )
                if pretty_print:
                    json.dump(
                        save_data,
                        f,
                        ensure_ascii=False,
                        indent=2,
                        default=_json_default,
                    )
                else:
                    json.dump(
                        save_data, f, ensure_ascii=False, default=_json_default
                    )

            logger.info(
                "Saved result for plugin %s to %s", plugin_name, output_path
            )

        except Exception as e:
            logger.error(
                "Failed to save result for plugin %s: %s", plugin_name, e
            )

    def analyze_configured_sources(
        self,
        brand_name: str,
        tenant_key: Optional[str] = None,
        job_id: Optional[str] = None,
        platform: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        根据配置的数据源（数据库表）批量分析品牌相关文本。

        1. 按数据表将启用的插件分组；
        2. 逐表读取数据，按日期分批调用插件分析；
        3. 聚合所有批次结果并返回；
        4. 各插件结果已按配置自动落盘，无需外部再保存。
        """

        enabled_plugins = self._get_enabled_plugins()
        plugins_config = (
            self.config.get("brand_analysis", {}).get("plugins", {})
        )

        table_to_plugins: Dict[str, List[str]] = defaultdict(list)
        table_to_fields: Dict[str, set] = defaultdict(set)

        for plugin_name in enabled_plugins:
            # Check plugin type first
            plugin_registry_info = PluginRegistry.get_plugin_info(
                plugin_name
            )
            if plugin_registry_info and plugin_registry_info.get("type") == "utility":
                logger.debug(
                    "Skipping utility plugin %s in table analysis", plugin_name
                )
                continue

            plugin_config = plugins_config.get(plugin_name, {})
            datasources = self._extract_plugin_datasources(
                plugin_name, plugin_config
            )
            if not datasources:
                logger.error(
                    (
                        "Plugin %s has no valid datasource configuration. "
                        "It will be skipped."
                    ),
                    plugin_name,
                )
                continue

            for ds in datasources:
                table_name = ds["table"]
                table_to_plugins[table_name].append(plugin_name)
                fields = ds.get("fields")
                if isinstance(fields, list) and fields:
                    table_to_fields[table_name].update(fields)

        if not table_to_plugins:
            if enabled_plugins:
                return {
                    "error": (
                        "No plugins with datasource/table configuration found. "
                        "If you intended to run a utility plugin, "
                        "use --run-plugin."
                    )
                }
            return {"error": "No valid database tables configured in plugins"}

        if self._get_database_engine() is None:
            return {"error": "Database is not configured or invalid"}

        # 2. 分析每个表
        total_records_processed = 0
        has_records = False

        for table_name, plugins in table_to_plugins.items():
            desired_fields = (
                sorted(table_to_fields.get(table_name, set()))
                if table_to_fields.get(table_name)
                else None
            )
            records_count = self._process_data_table(
                table_name,
                plugins,
                brand_name,
                desired_fields=desired_fields,
                tenant_key=tenant_key,
                job_id=job_id,
                platform=platform,
                start_date=start_date,
                end_date=end_date,
            )
            if records_count > 0:
                has_records = True
                total_records_processed += records_count

        if not has_records:
            return {"error": "No valid analysis results from any record"}

        return {"total_records_processed": total_records_processed}

    def _get_database_engine(self):
        if self._db_engine is not None:
            return self._db_engine

        db_cfg = self.config.get("brand_analysis", {}).get("database", {})
        try:
            url = build_mysql_database_url(db_cfg)
        except DatabaseConfigError as exc:
            logger.error("Database config invalid: %s", exc)
            return None

        try:
            from sqlalchemy import create_engine

            self._db_engine = create_engine(url, pool_pre_ping=True)
            return self._db_engine
        except Exception as e:
            logger.error("Failed to initialize database engine: %s", e)
            return None

    def _fetch_table_rows(
        self,
        table_name: str,
        brand_name: str,
        desired_fields: Optional[List[str]] = None,
        tenant_key: Optional[str] = None,
        job_id: Optional[str] = None,
        platform: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        if not isinstance(brand_name, str) or not brand_name.strip():
            logger.error("brand_name is required and cannot be empty")
            return []

        if not re.match(r"^[A-Za-z0-9_]+$", table_name or ""):
            logger.error("Invalid table name: %s", table_name)
            return []

        engine = self._get_database_engine()
        if engine is None:
            logger.warning(
                "Database is not configured, cannot read table: %s", table_name
            )
            return []

        try:
            from sqlalchemy import MetaData, Table, asc, inspect, select

            inspector = inspect(engine)
            available_columns = {
                c.get("name") for c in inspector.get_columns(table_name)
            }
            if desired_fields:
                selected_fields = [
                    f for f in desired_fields if f in available_columns
                ]
            else:
                selected_fields = [
                    c for c in available_columns if isinstance(c, str)
                ]

            if not selected_fields:
                logger.error(
                    "Table %s has no expected columns, cannot read rows",
                    table_name,
                )
                return []

            order_by_fields = [
                f for f in ["generated_date", "id"] if f in available_columns
            ]

            rows: List[Dict[str, Any]] = []
            metadata = MetaData()
            table = Table(table_name, metadata, autoload_with=engine)
            columns = [table.c[f] for f in selected_fields if f in table.c]
            stmt = select(*columns)

            if (
                "brand" in available_columns
                and isinstance(brand_name, str)
                and brand_name.strip()
            ):
                stmt = stmt.where(table.c.brand == brand_name.strip())
            elif isinstance(brand_name, str) and brand_name.strip():
                logger.warning(
                    "Table %s has no brand column, skipping brand filter",
                    table_name,
                )

            if tenant_key and "tenant_key" in available_columns:
                stmt = stmt.where(table.c.tenant_key == tenant_key)

            if job_id and "job_id" in available_columns:
                stmt = stmt.where(table.c.job_id == job_id)

            if platform:
                platform_value = str(platform).strip()
                if platform_value:
                    if "platform" in available_columns:
                        stmt = stmt.where(table.c.platform == platform_value)
                    elif "platform_name" in available_columns:
                        stmt = stmt.where(
                            table.c.platform_name == platform_value
                        )
                    else:
                        logger.warning(
                            "Table %s has no platform column, skipping platform filter",
                            table_name,
                        )

            if "generated_date" in available_columns:
                if start_date and end_date:
                    stmt = stmt.where(
                        table.c.generated_date.between(start_date, end_date)
                    )
                elif start_date:
                    stmt = stmt.where(table.c.generated_date >= start_date)
                elif end_date:
                    stmt = stmt.where(table.c.generated_date <= end_date)

            for field in order_by_fields:
                stmt = stmt.order_by(asc(table.c[field]))

            with engine.connect() as conn:
                rows = [dict(r) for r in conn.execute(stmt).mappings().all()]

            return rows
        except Exception as e:
            logger.error("Failed to read table %s: %s", table_name, e)
            return []

    def _build_text_content_from_row(self, row: Dict[str, Any]) -> str:
        query_content = row.get("query_content")
        answer_content = row.get("answer_content")

        if query_content is not None or answer_content is not None:
            qc = str(query_content or "")
            ac = str(answer_content or "")
            if qc.strip() or ac.strip():
                return f"用户提问：{qc}\n\nAI回答：{ac}"

        for key in ["text", "content", "message", "answer"]:
            v = row.get(key)
            if isinstance(v, str) and v.strip():
                return v

        try:
            raw = json.dumps(row, ensure_ascii=False, default=str)
        except Exception:
            raw = str(row)

        if len(raw) > 20000:
            raw = raw[:20000] + "...(truncated)"
        return raw

    def _process_data_table(
        self,
        table_name: str,
        plugins: List[str],
        brand_name: str,
        desired_fields: Optional[List[str]] = None,
        tenant_key: Optional[str] = None,
        job_id: Optional[str] = None,
        platform: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        rows = self._fetch_table_rows(
            table_name,
            brand_name,
            desired_fields=desired_fields,
            tenant_key=tenant_key,
            job_id=job_id,
            platform=platform,
            start_date=start_date,
            end_date=end_date,
        )
        if not rows:
            return 0

        date_dir_rows: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for row in rows:
            date_obj = row.get("generated_date")
            if isinstance(date_obj, (datetime, date)):
                date_dir = date_obj.strftime("%Y%m%d")
            else:
                date_dir = "unknown_date"
            date_dir_rows[date_dir].append(row)

        total_processed = 0
        for date_dir, batch_rows in date_dir_rows.items():
            count = self._process_table_batch(
                table_name, date_dir, batch_rows, plugins, brand_name
            )
            total_processed += count

        return total_processed

    def _process_table_batch(
        self,
        table_name: str,
        date_dir: str,
        rows: List[Dict[str, Any]],
        plugins: List[str],
        brand_name: str,
    ) -> int:
        logger.info(
            "Processing table batch: %s/%s with %d rows",
            table_name,
            date_dir,
            len(rows),
        )
        batch_results: List[Dict[str, Any]] = []

        for row in rows:
            text_content = self._build_text_content_from_row(row)

            row_id = row.get("id")
            conversation_id = row.get("conversation_id")
            if not conversation_id:
                conversation_id = (
                    f"id_{row_id}" if row_id is not None else str(uuid.uuid4())
                )

            analysis_result = self.analyze_text(
                text_content,
                brand_name,
                plugins_to_run=plugins,
            )
            if isinstance(analysis_result, dict) and "error" not in analysis_result:
                metrics = analysis_result.get("metrics")
                if not isinstance(metrics, dict):
                    continue

                result: Dict[str, Any] = {"metrics": metrics}
                result["record_id"] = conversation_id
                result["conversation_id"] = conversation_id
                result["tenant_key"] = row.get("tenant_key")
                result["job_id"] = row.get("job_id")
                result["brand"] = row.get("brand") or brand_name
                result["category"] = row.get("category")
                platform = row.get("platform") or row.get("platform_name")
                result["platform"] = platform
                result["keyword"] = row.get("keyword")
                result["source_row"] = row
                batch_results.append(result)

        if batch_results:
            batch_aggregated = self._aggregate_results(batch_results)

            if "metrics" in batch_aggregated:
                for (
                    plugin_name,
                    plugin_data,
                ) in batch_aggregated["metrics"].items():
                    if plugin_name in plugins:
                        self._save_plugin_batch_result(
                            plugin_name, plugin_data, date_dir, brand_name
                        )

        return len(batch_results)

    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        聚合多个记录的分析结果

        Args:
            results: 多个记录的分析结果

        Returns:
            聚合后的分析结果
        """
        if not results:
            return {"error": "No results to aggregate"}

        plugin_names = self._get_all_plugin_names(results)
        aggregated_metrics = self._aggregate_plugin_results(
            results, plugin_names
        )
        return {"metrics": aggregated_metrics}

    def _get_all_plugin_names(self, results: List[Dict[str, Any]]) -> set:
        """获取所有插件名称"""
        plugin_names = set()
        for result in results:
            if "metrics" in result:
                plugin_names.update(result["metrics"].keys())
        return plugin_names

    def _aggregate_plugin_results(
        self, results: List[Dict[str, Any]], plugin_names: set
    ) -> Dict[str, Any]:
        """聚合所有插件的结果"""
        aggregated_metrics = {}

        for plugin_name in plugin_names:
            plugin_results = self._collect_plugin_results(results, plugin_name)
            if not plugin_results:
                continue

            plugin_instance = self.plugin_manager.get_plugin(plugin_name)
            if plugin_instance:
                aggregated_metrics[plugin_name] = (
                    plugin_instance.aggregate_results(plugin_results)
                )
            else:
                logger.warning(
                    "Plugin instance for %s not found during aggregation",
                    plugin_name,
                )

        return aggregated_metrics

    def _collect_plugin_results(
        self, results: List[Dict[str, Any]], plugin_name: str
    ) -> list:
        """收集单个插件的所有结果"""
        plugin_results = []
        for result in results:
            if "metrics" in result and plugin_name in result["metrics"]:
                p_res = result["metrics"][plugin_name]
                if isinstance(p_res, dict):
                    if "record_id" in result:
                        p_res["record_id"] = result["record_id"]

                    for key in [
                        "conversation_id",
                        "tenant_key",
                        "job_id",
                        "brand",
                        "category",
                        "platform",
                        "keyword",
                        "source_row",
                    ]:
                        if key in result:
                            p_res[key] = result[key]
                plugin_results.append(p_res)
        return plugin_results

    def _get_first_present(
        self, data: Dict[str, Any], keys: List[str], default: Any = None
    ) -> Any:
        for key in keys:
            value = data.get(key)
            if value is not None and value != "":
                return value
        return default

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().isoformat()

    def _needs_llm_recognizer(self, enabled_plugins: list) -> bool:
        """检查是否需要LLM识别器"""
        for plugin_name in enabled_plugins:
            plugin_info = self.plugin_manager.get_plugin_info(plugin_name)
            if plugin_info and plugin_info.get("requires_llm", False):
                return True
        return False

    def _get_llm_recognizer(self):
        """获取LLM品牌识别器"""
        # 如果已经初始化过，直接返回
        if self.llm_recognizer:
            return self.llm_recognizer

        try:
            # 从配置中获取LLM设置
            llm_config = self.config.get("brand_analysis", {}).get("llm", {})
            ok, msg = self._validate_llm_config(llm_config)
            if not ok:
                logger.warning(
                    "%s, LLM-based plugins will use fallback logic", msg
                )
                return None

            provider = self._get_first_present(
                llm_config, ["provider"], "openai"
            )
            api_key = self._get_first_present(
                llm_config, ["apiKey", "api_key"], ""
            )
            model = self._get_first_present(
                llm_config, ["model"], "gpt-3.5-turbo"
            )
            timeout = self._get_first_present(llm_config, ["timeout"], 30000)
            max_retries = self._get_first_present(
                llm_config, ["maxRetries", "max_retries"], 2
            )
            max_tokens = self._get_first_present(
                llm_config, ["maxTokens", "max_tokens"], 2000
            )

            recognizer = LLMBrandRecognizer(
                provider=provider,
                api_key=api_key,
                model=model,
                timeout=timeout,
                max_retries=max_retries,
                max_tokens=max_tokens,
            )

            # 缓存实例
            self.llm_recognizer = recognizer
            return recognizer
        except ImportError:
            logger.warning(
                "LLM recognizer module not found, "
                "LLM-based plugins will use fallback logic"
            )
            return None
        except Exception as e:
            logger.warning(
                "Failed to initialize LLM recognizer: %s, "
                "LLM-based plugins will use fallback logic",
                e,
            )
            return None

    def run_utility_plugins(self, brand_name: str) -> Dict[str, Any]:
        """
        运行所有已启用且未配置 table 的 utility 插件
        """
        enabled_plugins = self._get_enabled_plugins()
        results = {}
        has_error = False

        for plugin_name in enabled_plugins:
            # Check if it's a utility plugin
            plugin_registry_info = PluginRegistry.get_plugin_info(plugin_name)
            is_utility = (
                plugin_registry_info
                and plugin_registry_info.get("type") == "utility"
            )

            # Check if it has a table config (handled by analyze_configured_sources)
            plugin_config = (
                self.config.get("brand_analysis", {})
                .get("plugins", {})
                .get(plugin_name, {})
            )
            has_table = bool(plugin_config.get("table")) or bool(
                plugin_config.get("datasources")
            )

            # If it's a utility plugin OR has no table config, run it here
            # (Assuming non-table plugins are standalone utilities)
            if is_utility and not has_table:
                logger.info("Running utility plugin: %s", plugin_name)
                res = self.run_plugin(plugin_name, brand_name)
                results[plugin_name] = res
                if "error" in res:
                    logger.error(
                        "Plugin %s failed: %s", plugin_name, res["error"]
                    )
                    has_error = True
                else:
                    logger.info(
                        "Plugin %s completed successfully", plugin_name
                    )

        if has_error:
            return {
                "error": "One or more utility plugins failed",
                "details": results,
            }

        return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="品牌AI认知分析工具")

    parser.add_argument("-b", "--brand", help="品牌名称")
    parser.add_argument("-c", "--config", help="配置文件路径")
    parser.add_argument(
        "--tenant-key", help="租户tenant_key（可选）", default=None
    )
    parser.add_argument(
        "--job-id", help="任务job_id（可选）", default=None
    )
    parser.add_argument("--platform", help="平台platform（可选）", default=None)
    parser.add_argument(
        "--start-date", help="开始日期 (YYYYMMDD)", default=None
    )
    parser.add_argument(
        "--end-date", help="结束日期 (YYYYMMDD)", default=None
    )
    parser.add_argument(
        "--competitors",
        help='竞品列表(JSON数组字符串)，如 ["A","B"]',
        default=None,
    )

    args = parser.parse_args()

    # 创建分析器
    analyzer = BrandAnalyzer(args.config)

    if not args.brand:
        logger.error("错误: 缺少品牌名称参数 -b/--brand")
        return 1

    brand_name = args.brand
    competitors: List[str] = []
    if args.competitors:
        raw = str(args.competitors).strip()
        parsed: Any = None
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None

        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, str) and item.strip():
                    competitors.append(item.strip())
        else:
            s = raw
            if s.startswith("@(") and s.endswith(")"):
                s = s[2:-1]
            if s.startswith("[") and s.endswith("]"):
                s = s[1:-1]
            parts = [
                p.strip() for p in re.split(r"[,\r\n]+", s) if p.strip()
            ]
            for p in parts:
                v = p.strip().strip('"').strip("'").strip()
                if v:
                    competitors.append(v)

            if raw and not competitors:
                logger.error(
                    "错误: competitors 参数解析失败。示例: "
                    '--competitors "[\\"A\\",\\"B\\"]"'
                )
                return 1

    analyzer.set_competitors(competitors)

    # 1. 自动运行配置中启用的工具类插件
    utility_results = analyzer.run_utility_plugins(brand_name)
    if "error" in utility_results:
        # 如果工具插件失败，是否终止？这里选择记录但不强制终止，除非非常严重
        # 但既然是 utility (如 import)，失败可能影响后续，所以这里仅 log
        logger.warning(
            "Utility plugins execution had errors: %s", utility_results
        )

    # 2. 运行基于表的数据分析
    tenant_key = (
        str(args.tenant_key).strip() if args.tenant_key else None
    )
    job_id = str(args.job_id).strip() if args.job_id else None
    platform = str(args.platform).strip() if args.platform else None

    start_date = None
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, "%Y%m%d").date()
        except ValueError:
            logger.error(
                "错误: --start-date 格式不正确，请使用 YYYYMMDD"
            )
            return 1

    end_date = None
    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, "%Y%m%d").date()
        except ValueError:
            logger.error("错误: --end-date 格式不正确，请使用 YYYYMMDD")
            return 1

    result = analyzer.analyze_configured_sources(
        brand_name,
        tenant_key=tenant_key,
        job_id=job_id,
        platform=platform,
        start_date=start_date,
        end_date=end_date,
    )

    # 检查是否有错误
    if "error" in result:
        # 如果是因为没有配置 table 插件，但我们成功运行了 utility 插件，则不应报错
        if (
            "No plugins with 'table' configuration found" in result["error"]
            and utility_results
            and "error" not in utility_results
        ):
            logger.info("仅运行了工具类插件，未配置表分析插件。")
            return 0

        logger.error("错误: %s", result["error"])
        return 1

    # 移除文件保存逻辑，因为现在由 analyzer 内部处理保存
    logger.info("分析完成！结果已按配置保存到各自的输出目录。")
    return 0


if __name__ == "__main__":
    exit(main())
