"""
提及状态插件
判断文本是否提及品牌以及是否为首位提及，输出状态映射
"""

import asyncio
import hashlib
import json
import logging
import re
from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from ...business_services.llm_brand_recognizer import LLMBrandRecognizer
from ...core.constants import get_brand_variants
from ...core.database_config import DatabaseConfigError, build_mysql_database_url
from ...core.llm_operator import LLMConfig, LLMError, LLMOperator, LLMResponse
from ...core.plugin_interface import AnalysisPlugin, PluginRegistry

logger = logging.getLogger(__name__)


@PluginRegistry.register(
    name="mention_status",
    description="提及状态插件 - 输出每条记录的品牌提及和首位提及状态",
    plugin_type="enhanced",
    requires_llm=True,
    enabled_by_default=False,
)
class MentionStatusPlugin(AnalysisPlugin):
    """提及状态插件 - 输出提及状态的映射"""

    @property
    def name(self) -> str:
        """插件名称"""
        return "mention_status"

    @property
    def description(self) -> str:
        """插件描述"""
        return "判断每条记录是否提及品牌及是否为首位提及，输出状态映射"

    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """
        初始化插件
        """
        self.llm_config = llm_config or {}
        self.llm_recognizer = None
        self._db_engine = None
        self.app_config: Dict[str, Any] = {}
        self.plugin_config: Dict[str, Any] = {}
        self.competitors: List[str] = []
        self.datasource_fields: List[str] = []

        if not self._validate_llm_config():
            logger.warning(
                "mention_status: LLM配置无效或缺失，插件可能无法正常工作。"
            )

    def set_app_config(
        self,
        app_config: Optional[Dict[str, Any]],
        plugin_config: Optional[Dict[str, Any]],
    ) -> None:
        self.app_config = app_config or {}
        self.plugin_config = plugin_config or {}
        self.datasource_fields = self._extract_datasource_fields(
            self.plugin_config
        )
        self._db_engine = None

    def _extract_datasource_fields(
        self, plugin_cfg: Dict[str, Any]
    ) -> List[str]:
        datasources = plugin_cfg.get("datasources")
        if not isinstance(datasources, list) or not datasources:
            return []
        first = datasources[0]
        if not isinstance(first, dict):
            return []
        fields = first.get("fields")
        if not isinstance(fields, list):
            return []
        return [
            f.strip() for f in fields if isinstance(f, str) and f.strip()
        ]

    def _get_db_cfg(self, config: Dict[str, Any]) -> Dict[str, Any]:
        cfg = (config.get("brand_analysis") or {}).get("database") or {}
        return cfg if isinstance(cfg, dict) else {}

    def _get_db_engine(self):
        if self._db_engine is not None:
            return self._db_engine

        try:
            url = build_mysql_database_url(self._get_db_cfg(self.app_config))
        except DatabaseConfigError:
            return None

        try:
            from sqlalchemy import create_engine

            self._db_engine = create_engine(url, pool_pre_ping=True)
            return self._db_engine
        except Exception as e:
            logger.error("mention_status: 初始化数据库引擎失败: %s", e)
            return None

    def _to_tinyint_bool(self, value: Any) -> int:
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

    def _required_str(self, answer: Dict[str, Any], key: str) -> Optional[str]:
        value = answer.get(key)
        if value is None:
            return None
        if isinstance(value, str):
            v = value.strip()
            return v if v else None
        v = str(value).strip()
        return v if v else None

    def _build_qa_brand_state_rows(
        self, answer_date: date, answers: Iterable[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], int]:
        rows: List[Dict[str, Any]] = []
        skipped = 0
        seen: Set[Tuple[Any, Any, Any, Any]] = set()

        for a in answers:
            tenant_key = self._required_str(a, "tenant_key")
            job_id = self._required_str(a, "job_id")
            analysis_run_id = self._required_str(a, "analysis_run_id")
            conversation_id = self._required_str(a, "conversation_id")
            brand = self._required_str(a, "brand")
            category = self._required_str(a, "category")
            platform = self._required_str(a, "platform")
            keyword = self._required_str(a, "keyword")
            sentiment_status = (
                self._required_str(a, "sentiment_status") or "unknown"
            )

            if not all(
                [
                    tenant_key,
                    job_id,
                    conversation_id,
                    brand,
                    category,
                    platform,
                    keyword,
                ]
            ):
                skipped += 1
                continue

            key = (tenant_key, job_id, conversation_id, brand)
            if key in seen:
                skipped += 1
                continue
            seen.add(key)

            brands_found = a.get("brands_found")
            if brands_found is not None and not isinstance(brands_found, str):
                brands_found = json.dumps(brands_found, ensure_ascii=False)

            rows.append(
                {
                    "date": answer_date,
                    "tenant_key": tenant_key,
                    "job_id": job_id,
                    "analysis_run_id": analysis_run_id,
                    "conversation_id": conversation_id,
                    "brand": brand,
                    "category": category,
                    "platform": platform,
                    "keyword": keyword,
                    "is_mentioned": self._to_tinyint_bool(
                        a.get("is_mentioned")
                    ),
                    "is_first_mentioned": self._to_tinyint_bool(
                        a.get("is_first_mentioned")
                    ),
                    "is_top3_mentioned": self._to_tinyint_bool(
                        a.get("is_top3_mentioned")
                    ),
                    "sentiment_status": sentiment_status,
                    "brands_found": brands_found,
                }
            )

        return rows, skipped

    def _insert_qa_brand_state_rows(
        self, rows: Sequence[Dict[str, Any]], chunk_size: int = 500
    ) -> int:
        if not rows:
            return 0

        engine = self._get_db_engine()
        if engine is None:
            return 0

        try:
            from sqlalchemy import text

            if engine.dialect.name == "sqlite":
                sql = text(
                    """
                    INSERT INTO qa_brand_state
                      (
                        date,
                        tenant_key,
                        job_id,
                        analysis_run_id,
                        conversation_id,
                        brand,
                        category,
                        platform,
                        keyword,
                        is_mentioned,
                        is_first_mentioned,
                        is_top3_mentioned,
                        sentiment_status,
                        brands_found
                      )
                    VALUES
                      (
                        :date,
                        :tenant_key,
                        :job_id,
                        :analysis_run_id,
                        :conversation_id,
                        :brand,
                        :category,
                        :platform,
                        :keyword,
                        :is_mentioned,
                        :is_first_mentioned,
                        :is_top3_mentioned,
                        :sentiment_status,
                        :brands_found
                      )
                    ON CONFLICT(tenant_key, job_id, conversation_id, brand)
                    DO UPDATE SET
                      date = excluded.date,
                      analysis_run_id = excluded.analysis_run_id,
                      category = excluded.category,
                      platform = excluded.platform,
                      keyword = excluded.keyword,
                      is_mentioned = excluded.is_mentioned,
                      is_first_mentioned = excluded.is_first_mentioned,
                      is_top3_mentioned = excluded.is_top3_mentioned,
                      sentiment_status = excluded.sentiment_status,
                      brands_found = excluded.brands_found,
                      updated_at = CURRENT_TIMESTAMP
                    """
                )
            else:
                # 使用 ON DUPLICATE KEY UPDATE 实现 Upsert
                # 依赖 UNIQUE KEY `uk_tenant_job_conv_brand`
                # (`tenant_key`(191), `job_id`(191), `conversation_id`(191), `brand`)
                sql = text(
                    "INSERT INTO qa_brand_state "
                    "(date, tenant_key, job_id, analysis_run_id, "
                    "conversation_id, brand, category, "
                    "platform, keyword, is_mentioned, "
                    "is_first_mentioned, is_top3_mentioned, "
                    "sentiment_status, brands_found) "
                    "VALUES "
                    "(:date, :tenant_key, :job_id, :analysis_run_id, "
                    ":conversation_id, :brand, "
                    ":category, :platform, :keyword, :is_mentioned, "
                    ":is_first_mentioned, :is_top3_mentioned, "
                    ":sentiment_status, :brands_found) "
                    "ON DUPLICATE KEY UPDATE "
                    "date = VALUES(date), "
                    "analysis_run_id = VALUES(analysis_run_id), "
                    "category = VALUES(category), "
                    "platform = VALUES(platform), "
                    "keyword = VALUES(keyword), "
                    "is_mentioned = VALUES(is_mentioned), "
                    "is_first_mentioned = VALUES(is_first_mentioned), "
                    "is_top3_mentioned = VALUES(is_top3_mentioned), "
                    "sentiment_status = VALUES(sentiment_status), "
                    "brands_found = VALUES(brands_found), "
                    "updated_at = CURRENT_TIMESTAMP"
                )

            inserted = 0
            for i in range(0, len(rows), chunk_size):
                batch_list = list(rows[i:i + chunk_size])
                if not batch_list:
                    continue

                with engine.begin() as conn:
                    conn.execute(sql, batch_list)
                    # 在 upsert 场景下，rowcount 可能大于 batch_list 长度
                    # (update 返回 2, insert 返回 1)
                    # 这里简单统计为“受影响行数”即可，或者只统计 batch 大小
                    inserted += len(batch_list)

            return inserted
        except Exception as e:
            logger.error("mention_status: qa_brand_state upsert失败: %s", e)
            return 0

    def _extract_value(
        self, result: Dict[str, Any], logical_key: str
    ) -> Optional[Any]:
        if logical_key in result and result.get(logical_key) not in (
            None,
            "",
        ):
            return result.get(logical_key)

        source_row = result.get("source_row")
        if isinstance(source_row, dict):
            if logical_key in source_row and source_row.get(
                logical_key
            ) not in (
                None,
                "",
            ):
                return source_row.get(logical_key)

        candidates = []
        lk = logical_key.lower()
        for f in self.datasource_fields:
            fl = f.lower()
            if fl == lk:
                candidates.insert(0, f)
            elif lk in fl:
                candidates.append(f)

        if isinstance(source_row, dict):
            for k in candidates:
                if k in source_row and source_row.get(k) not in (
                    None,
                    "",
                ):
                    return source_row.get(k)

        for k in candidates:
            if k in result and result.get(k) not in (None, ""):
                return result.get(k)

        return None

    def _extract_platform(self, result: Dict[str, Any]) -> Optional[str]:
        v = self._extract_value(result, "platform")
        if v is not None:
            return str(v)

        source_row = result.get("source_row")
        if isinstance(source_row, dict):
            platform_keys = [
                f
                for f in self.datasource_fields
                if re.search(r"\bplatform\b", f, re.IGNORECASE)
                or re.search(r"platform", f, re.IGNORECASE)
            ]
            for k in platform_keys:
                value = source_row.get(k)
                if value not in (None, ""):
                    return str(value)

        return None

    def _ensure_llm_initialized(self):
        """确保LLM识别器已初始化"""
        if self.llm_recognizer is not None:
            return

        if not self._validate_llm_config():
            raise ValueError(
                "LLM配置无效或缺失，无法初始化mention_status插件。"
            )

        provider = self.llm_config.get("provider", "openai")
        api_key = self.llm_config.get("apiKey") or self.llm_config.get(
            "api_key", ""
        )
        base_url = self.llm_config.get("baseURL") or self.llm_config.get(
            "base_url", ""
        )
        model = self.llm_config.get("model", "gpt-3.5-turbo")
        timeout = self.llm_config.get("timeout", 30000)
        max_retries = self.llm_config.get(
            "maxRetries"
        ) or self.llm_config.get("max_retries", 2)
        max_tokens = self.llm_config.get(
            "maxTokens"
        ) or self.llm_config.get("max_tokens", 2000)

        try:
            operator_config = LLMConfig(
                provider=provider,
                api_key=api_key,
                base_url=base_url,
                model=model,
                timeout=timeout,
                max_retries=max_retries,
                max_tokens=max_tokens,
            )
            llm_operator = LLMOperator(operator_config)
            self.llm_recognizer = LLMBrandRecognizer(llm_operator=llm_operator)
            logger.info(
                "mention_status: Lazily initialized internal LLM recognizer"
            )
        except Exception as e:
            logger.error("mention_status: 初始化LLM组件失败: %s", e)
            raise

    def _validate_llm_config(self) -> bool:
        """验证LLM配置 - 使用基类方法"""
        return super()._validate_llm_config(self.llm_config)

    def set_llm_recognizer(self, recognizer):
        """注入LLM识别器"""
        self.llm_recognizer = recognizer

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

    def analyze(self, text: str, brand_name: str) -> Dict[str, Any]:
        """同步分析接口"""
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                raise RuntimeError(
                    "Cannot call sync analyze from async context"
                )
            else:
                return asyncio.run(self.analyze_async(text, brand_name))
        except Exception as e:
            logger.error("mention_status分析失败: %s", e)
            logger.debug(
                "分析失败的文本: %s, 品牌: %s", text[:100], brand_name
            )
            return {
                "is_mentioned": False,
                "is_first_mentioned": False,
                "is_top3_mentioned": False,
                "error": str(e),
            }

    async def analyze_async(
        self, text: str, brand_name: str
    ) -> Dict[str, Any]:
        """异步分析"""
        try:
            self._ensure_llm_initialized()

            recognizer = self.llm_recognizer
            recognition_result = await recognizer.recognize_brands_async(text)
            brands_in_order = recognition_result.get("brands", [])

            async def compute_brand_state(target_brand: str) -> Dict[str, Any]:
                target_brand = (target_brand or "").strip()
                if not target_brand:
                    return {
                        "brand": None,
                        "is_mentioned": False,
                        "is_first_mentioned": False,
                        "is_top3_mentioned": False,
                        "sentiment_status": None,
                    }

                brand_variants = get_brand_variants(target_brand)
                is_mentioned = False
                is_first_mentioned = False
                is_top3_mentioned = False

                if brands_in_order:
                    # 首位提及
                    first_brand = brands_in_order[0]
                    is_first_mentioned = self._is_brand_match(
                        first_brand, brand_variants
                    )

                    # 前三提及
                    top3_brands = brands_in_order[:3]
                    is_top3_mentioned = any(
                        self._is_brand_match(brand, brand_variants)
                        for brand in top3_brands
                    )

                    # 是否提及
                    is_mentioned = any(
                        self._is_brand_match(brand, brand_variants)
                        for brand in brands_in_order
                    )

                sentiment_status = None
                if is_mentioned:
                    sentiment_score = await self._get_sentiment_score_async(
                        text, target_brand
                    )
                    if sentiment_score is not None:
                        sentiment_status = self._score_to_sentiment_status(
                            sentiment_score
                        )

                return {
                    "brand": target_brand,
                    "is_mentioned": is_mentioned,
                    "is_first_mentioned": is_first_mentioned,
                    "is_top3_mentioned": is_top3_mentioned,
                    "sentiment_status": sentiment_status,
                }

            main_state = await compute_brand_state(brand_name)
            competitor_brands = [
                c
                for c in self.competitors
                if isinstance(c, str)
                and c.strip()
                and c.strip() != (brand_name or "").strip()
            ]
            competitor_states = []
            if competitor_brands:
                competitor_states = list(
                    await asyncio.gather(
                        *(compute_brand_state(c) for c in competitor_brands)
                    )
                )

            return {
                "target_brand": (brand_name or "").strip() or None,
                "is_mentioned": main_state.get("is_mentioned", False),
                "is_first_mentioned": main_state.get(
                    "is_first_mentioned", False
                ),
                "is_top3_mentioned": main_state.get(
                    "is_top3_mentioned", False
                ),
                "sentiment_status": main_state.get("sentiment_status"),
                "brands_found": brands_in_order,
                "competitor_states": competitor_states,
            }

        except Exception as e:
            logger.error("mention_status async分析出错: %s", e)
            raise

    def aggregate_results(
        self, plugin_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        聚合结果 - 生成记录ID到状态的映射
        """
        if not plugin_results:
            return {}

        item_id_map = {}

        for result in plugin_results:
            record_id = self._extract_value(result, "record_id")
            if record_id is None:
                record_id = self._extract_value(result, "conversation_id")
            if record_id is None:
                record_id = self._extract_value(result, "id")
            record_id = (
                str(record_id) if record_id is not None else "unknown_record"
            )
            brands_found = result.get("brands_found", [])

            tenant_key = self._extract_value(result, "tenant_key")
            job_id = self._extract_value(result, "job_id")
            conversation_id = (
                self._extract_value(result, "conversation_id") or record_id
            )
            main_brand = result.get("target_brand") or self._extract_value(
                result, "brand"
            )
            category = self._extract_value(result, "category")
            keyword = self._extract_value(result, "keyword")
            platform = self._extract_platform(result)

            conversation_id_str = (
                str(conversation_id) if conversation_id is not None else None
            )
            base = {
                "tenant_key": (
                    str(tenant_key) if tenant_key is not None else None
                ),
                "job_id": str(job_id) if job_id is not None else None,
                "analysis_run_id": (
                    str(self._extract_value(result, "analysis_run_id"))
                    if self._extract_value(result, "analysis_run_id") is not None
                    else None
                ),
                "conversation_id": conversation_id_str,
                "category": str(category) if category is not None else None,
                "platform": str(platform) if platform is not None else None,
                "keyword": str(keyword) if keyword is not None else None,
                "brands_found": brands_found,
            }

            main_brand_str = (
                str(main_brand).strip() if main_brand is not None else ""
            )
            if main_brand_str:
                main_key_raw = f"{conversation_id}::{main_brand_str}"
                main_item_id = hashlib.sha256(
                    main_key_raw.encode("utf-8")
                ).hexdigest()
                item_id_map[main_item_id] = {
                    **base,
                    "brand": main_brand_str,
                    "is_mentioned": result.get("is_mentioned", False),
                    "is_first_mentioned": result.get(
                        "is_first_mentioned", False
                    ),
                    "is_top3_mentioned": result.get(
                        "is_top3_mentioned", False
                    ),
                    "sentiment_status": result.get("sentiment_status"),
                }

            competitor_states = result.get("competitor_states")
            if isinstance(competitor_states, list):
                for cs in competitor_states:
                    if not isinstance(cs, dict):
                        continue
                    cs_brand = cs.get("brand")
                    cs_brand_str = (
                        str(cs_brand).strip() if cs_brand is not None else ""
                    )
                    if not cs_brand_str:
                        continue
                    cs_key_raw = f"{conversation_id}::{cs_brand_str}"
                    cs_item_id = hashlib.sha256(
                        cs_key_raw.encode("utf-8")
                    ).hexdigest()
                    item_id_map[cs_item_id] = {
                        **base,
                        "brand": cs_brand_str,
                        "is_mentioned": cs.get("is_mentioned", False),
                        "is_first_mentioned": cs.get(
                            "is_first_mentioned", False
                        ),
                        "is_top3_mentioned": cs.get(
                            "is_top3_mentioned", False
                        ),
                        "sentiment_status": cs.get("sentiment_status"),
                    }

        total_source_records = len(plugin_results)
        brand_summaries: Dict[str, Dict[str, Any]] = {}
        for a in item_id_map.values():
            b = a.get("brand")
            if not isinstance(b, str) or not b.strip():
                continue
            bs = brand_summaries.setdefault(
                b,
                {
                    "brand": b,
                    "records": 0,
                    "mentioned_records": 0,
                    "first_mention_records": 0,
                    "top3_mention_records": 0,
                    "mention_rate": 0.0,
                    "first_mention_rate": 0.0,
                    "top3_mention_rate": 0.0,
                },
            )
            bs["records"] += 1
            if a.get("is_mentioned"):
                bs["mentioned_records"] += 1
            if a.get("is_first_mentioned"):
                bs["first_mention_records"] += 1
            if a.get("is_top3_mentioned"):
                bs["top3_mention_records"] += 1

        for bs in brand_summaries.values():
            total = int(bs.get("records") or 0)
            if total > 0:
                bs["mention_rate"] = (
                    bs.get("mentioned_records") or 0
                ) / total
                bs["first_mention_rate"] = (
                    bs.get("first_mention_records") or 0
                ) / total
                bs["top3_mention_rate"] = (
                    bs.get("top3_mention_records") or 0
                ) / total

        # 从 plugin_results 中提取第一个有效日期作为入库日期
        # 优先查找 source_row 中的 date/generated_date，其次查找 analysis_date
        answer_date = date.today()
        for res in plugin_results:
            d = self._extract_value(res, "date")
            if d is None:
                d = self._extract_value(res, "generated_date")

            if d:
                if isinstance(d, date):
                    answer_date = d
                    break
                elif isinstance(d, str):
                    try:
                        # 尝试解析常见日期格式
                        from datetime import datetime

                        if len(d) >= 10:  # YYYY-MM-DD
                            answer_date = datetime.strptime(
                                d[:10], "%Y-%m-%d"
                            ).date()
                            break
                    except Exception:
                        logger.debug("解析日期失败: %s", d, exc_info=True)

        rows, _skipped = self._build_qa_brand_state_rows(
            answer_date, item_id_map.values()
        )
        self._insert_qa_brand_state_rows(rows)

        return {
            "answers": item_id_map,
            "summary": {
                "total_records": total_source_records,
                "total_brand_records": len(item_id_map),
                "brand_summaries": brand_summaries,
            },
        }

    def _is_brand_match(
        self, text: str, brand_variants: List[str]
    ) -> bool:
        """检查匹配"""
        text_lower = text.lower().strip()
        for variant in brand_variants:
            variant_lower = variant.lower().strip()
            if variant_lower in text_lower or text_lower in variant_lower:
                return True
        return False

    async def _get_sentiment_score_async(
        self, text: str, brand_name: str
    ) -> Optional[float]:
        prompt = self._build_sentiment_prompt(text, brand_name)

        llm_operator = self.llm_recognizer.llm_operator
        response = await llm_operator.chat_completion_async(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一个专业的品牌舆情分析师。"
                        "请按照用户的要求对文本进行深度分析并返回严格的JSON格式结果。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        if isinstance(response, LLMError):
            return None

        if not isinstance(response, LLMResponse):
            return None

        try:
            parsed = json.loads(response.content)
        except json.JSONDecodeError:
            return None

        if not isinstance(parsed, dict):
            return None

        score = parsed.get("sentiment_score")
        if score is None:
            return None

        try:
            score_float = float(score)
        except (TypeError, ValueError):
            return None

        if score_float < 0:
            return 0.0
        if score_float > 1:
            return 1.0
        return score_float

    def _build_sentiment_prompt(self, text: str, brand_name: str) -> str:
        max_chars = 15000
        if len(text) > max_chars:
            text = text[:max_chars] + "...(truncated)"

        brand_variants = get_brand_variants(brand_name)
        variants_str = "、".join(brand_variants)

        lines = [
            "任务：对文本中提及品牌“"
            f"{brand_name}”（含别称：{variants_str}）的相关内容进行情绪值评分。",
            "",
            "评分要求：",
            "1. sentiment_score 必须是 0 到 1 之间的数字。",
            "2. 仅根据与该品牌相关的表述评分，不要被无关内容影响。",
            "3. 必须输出合法 JSON，且仅包含 sentiment_score 字段。",
            "",
            "文本内容：",
            text,
            "",
            "返回格式：",
            "```json",
            '{"sentiment_score": 0.85}',
            "```",
        ]
        return "\n".join(lines)

    def _score_to_sentiment_status(self, sentiment_score: float) -> str:
        if sentiment_score >= 0.7:
            return "positive"
        if sentiment_score >= 0.4:
            return "neutral"
        return "negative"
