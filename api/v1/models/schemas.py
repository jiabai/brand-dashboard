from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AnalysisType(str, Enum):
    """分析类型枚举."""
    BRAND_RECOGNITION = "brand_recognition"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    MENTION_ANALYSIS = "mention_analysis"


class AnalysisRequest(BaseModel):
    """分析请求模型."""
    brand_name: str = Field(..., description="品牌名称")
    analysis_type: AnalysisType = Field(..., description="分析类型")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="分析参数")
    provider: Optional[str] = Field(default="openai", description="LLM提供商")
    model: Optional[str] = Field(default="gpt-3.5-turbo", description="模型名称")


class AnalysisResult(BaseModel):
    """分析结果模型."""
    result_id: str = Field(..., description="结果ID")
    brand_name: str = Field(..., description="品牌名称")
    analysis_type: AnalysisType = Field(..., description="分析类型")
    result_data: Dict[str, Any] = Field(..., description="分析结果数据")
    confidence: Optional[float] = Field(default=None, description="置信度")
    processing_time: Optional[float] = Field(default=None, description="处理时间(秒)")


class AnalysisResponse(BaseModel):
    """分析响应模型."""
    success: bool = Field(..., description="是否成功")
    data: Optional[Dict[str, Any]] = Field(default=None, description="响应数据")
    message: str = Field(..., description="响应消息")
    timestamp: datetime = Field(..., description="时间戳")


class BrandRecognitionRequest(BaseModel):
    """品牌识别请求模型."""
    text: str = Field(..., description="要分析的文本")
    context: Optional[str] = Field(default=None, description="上下文信息")
    provider: Optional[str] = Field(default="openai", description="LLM提供商")
    model: Optional[str] = Field(default="gpt-3.5-turbo", description="模型名称")


class BrandRecognitionResult(BaseModel):
    """品牌识别结果模型."""
    brands_found: List[str] = Field(..., description="发现的品牌列表")
    mentions: List[Dict[str, Any]] = Field(..., description="品牌提及详情")
    sentiment_scores: Optional[Dict[str, float]] = Field(default=None, description="情感评分")


class BrandRecognitionResponse(BaseModel):
    """品牌识别响应模型."""
    success: bool = Field(..., description="是否成功")
    data: Optional[BrandRecognitionResult] = Field(default=None, description="识别结果")
    message: str = Field(..., description="响应消息")
    timestamp: datetime = Field(..., description="时间戳")


class HealthResponse(BaseModel):
    """健康检查响应模型."""
    status: str = Field(..., description="服务状态")
    service: str = Field(..., description="服务名称")
    version: str = Field(..., description="服务版本")


class ConfigResponse(BaseModel):
    """配置响应模型."""
    success: bool = Field(..., description="是否成功")
    data: Dict[str, Any] = Field(..., description="配置数据")
    message: str = Field(..., description="响应消息")


class ErrorResponse(BaseModel):
    """错误响应模型."""
    success: bool = Field(default=False, description="是否成功")
    error: str = Field(..., description="错误信息")
    status_code: int = Field(..., description="HTTP状态码")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class PositioningRequest(BaseModel):
    industry: str = Field(..., description="行业")
    brand: str = Field(..., description="品牌")


class ConsumerQuestionsRequest(BaseModel):
    industry: str = Field(..., description="行业")
    brand: str = Field(..., description="品牌")
    keywords: List[str] = Field(..., description="关键词列表")


class QueryContentItem(BaseModel):
    keyword: str = Field(..., min_length=1, description="关键词")
    query_content: List[str] = Field(..., min_items=1, description="查询内容列表")


class QueryJobData(BaseModel):
    category: str = Field(..., min_length=1, description="分类")
    brand: Optional[str] = Field(None, min_length=1, description="品牌")
    competitor: Optional[List[str]] = Field(None, description="竞品列表")
    content: List[QueryContentItem] = Field(..., min_items=1, description="内容列表")


class LoadQueryJobsRequest(BaseModel):
    tenant_key: str = Field(..., min_length=1, description="租户Key")
    job_id: str = Field(..., min_length=1, description="任务ID")
    effective_from: datetime = Field(..., description="生效开始时间")
    effective_to: Optional[datetime] = Field(None, description="生效结束时间（NULL表示未结束）")
    executor_id: str = Field(..., min_length=1, description="执行器ID")
    total_runs: int = Field(default=15, description="总执行次数")
    executed_runs: int = Field(0, description="已执行次数")
    last_executed_date: date = Field(default_factory=date.today, description="最近执行日期")
    data: QueryJobData = Field(..., description="要加载的查询任务JSON数据")

class LoadQueryJobsResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    inserted_rows: int = Field(..., description="插入行数")
    message: str = Field(..., description="响应消息")


class ConversationReferenceItem(BaseModel):
    url: str = Field(..., min_length=1, description="引用链接")
    site_name: Optional[str] = Field(None, description="站点名称")
    cite_index: Optional[int] = Field(None, description="引用序号")


class ConversationItem(BaseModel):
    conversation_id: str = Field(..., min_length=1, description="对话ID")
    keyword: str = Field(..., min_length=1, description="关键词")
    brand: Optional[str] = Field(None, description="品牌名称")
    category: str = Field(..., min_length=1, description="商品大类")
    query_content: str = Field(..., min_length=1, description="用户提问内容")
    answer_content: str = Field(..., min_length=1, description="平台回复内容")
    extracted_at: Optional[datetime] = Field(None, description="抽取时间")
    references: Optional[List[ConversationReferenceItem]] = Field(None, description="引用列表")


class ConversationLoadRequest(BaseModel):
    tenant_key: str = Field(..., min_length=1, description="租户标识Key")
    job_id: str = Field(..., min_length=1, description="任务ID")
    platform: str = Field(..., min_length=1, description="平台名称")
    items: List[ConversationItem] = Field(..., min_items=1, description="对话批量数据")


class ConversationLoadResponse(BaseModel):
    success: bool = Field(..., description="是否处理成功")
    inserted_conversations: int = Field(..., description="新增对话数")
    inserted_references: int = Field(..., description="新增引用数")
    message: str = Field(..., description="提示消息")


class ExecutorBase(BaseModel):
    name: str = Field(..., description="执行器名称", example="香港机房-爬虫01")
    type: Optional[str] = Field(None, description="执行器类型", example="crawler")
    ip_address: str = Field(..., description="执行器允许的 IP 地址", example="47.91.22.33")


class ExecutorCreate(ExecutorBase):
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "香港机房-爬虫01",
                "ip_address": "47.91.22.33",
                "type": "crawler"
            }
        }
    }


class ExecutorResponse(ExecutorBase):
    executor_id: str = Field(..., description="执行器唯一标识符")
    status: str = Field(..., description="执行器状态")
    created_at: datetime = Field(..., description="创建时间")


class ExecutorListItem(ExecutorBase):
    executor_id: str = Field(..., description="执行器唯一标识符")
    status: str = Field(..., description="执行器状态")
    created_at: datetime = Field(..., description="创建时间")


class ExecutorRegistrationResponse(BaseModel):
    executor_id: str = Field(..., description="分发的执行器唯一标识符")
    api_key: str = Field(..., description="分发的执行器 API Key")


class QueryJobDetail(BaseModel):
    id: int = Field(..., description="任务记录唯一主键ID")
    job_id: str = Field(..., description="任务组ID")
    tenant_key: str = Field(..., description="租户Key")
    category: str = Field(..., description="分类")
    brand: Optional[str] = Field(None, description="品牌")
    competitor: Optional[List[str]] = Field(None, description="竞品列表")
    keyword: str = Field(..., description="关键词")
    query_content: str = Field(..., description="查询内容")


class QueryJobStatusItem(BaseModel):
    tenant_key: str = Field(..., description="租户Key")
    job_id: str = Field(..., description="任务ID")
    brand: Optional[str] = Field(None, description="品牌")
    competitor: Optional[List[str]] = Field(None, description="竞品列表")
    query_content: str = Field(..., description="查询内容")
    query_status: int = Field(..., description="问题生效状态")
    effective_from: datetime = Field(..., description="生效开始时间")
    effective_to: Optional[datetime] = Field(None, description="生效结束时间")


class FetchQueryJobResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    count: int = Field(..., description="任务数量")
    jobs: Optional[QueryJobDetail] = Field(None, description="任务详情")


class QueryJobStatusResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    count: int = Field(..., description="任务数量")
    jobs: List[QueryJobStatusItem] = Field(default_factory=list, description="任务状态列表")



class ReportQueryJobResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")


class TimeFrame(str, Enum):
    YESTERDAY = "yesterday"
    DAYS_7 = "7days"
    DAYS_30 = "30days"
    SPECIFIC_DAY = "specific_day"


class BrandMentionRateData(BaseModel):
    mention_rate: float = Field(..., description="品牌总提及率(百分比)")
    rank: int = Field(..., description="品牌排名")
    change: float = Field(..., description="与上一周期对比的变化(百分比)")
    question_count: int = Field(..., description="问题总数")
    mention_count: int = Field(..., description="品牌提及数量")
    first_mention_count: int = Field(..., description="首次提及品牌数量")
    analysis_date: str = Field(..., description="分析日期")
    last_updated: datetime = Field(..., description="最后更新时间")


class BrandMentionRateResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    data: BrandMentionRateData = Field(..., description="品牌总提及率数据")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class PlatformMentionRateData(BaseModel):
    name: str = Field(..., description="平台名称")
    mention_rate: float = Field(..., description="该平台上的品牌提及率(百分比)")
    first_mention_rate: float = Field(..., description="该平台上的品牌首位提及率(百分比)")
    color: str = Field(..., description="颜色")


class PlatformMentionRateResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    data: List[PlatformMentionRateData] = Field(..., description="各平台提及率数据列表")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class KeywordPlatformBrandRateItem(BaseModel):
    keyword: str = Field(..., description="关键词")
    platform: str = Field(..., description="平台")
    brand: str = Field(..., description="品牌")
    mention_rate: float = Field(..., description="提及率(比例，0~1)")
    first_mention_rate: float = Field(..., description="首位提及率(比例，0~1)")
    top3_mention_rate: float = Field(..., description="前3位提及率(比例，0~1)")


class KeywordPlatformBrandRatesResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    data: List[KeywordPlatformBrandRateItem] = Field(..., description="数据列表")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class BrandMentionTrendItem(BaseModel):
    date: str = Field(..., description="日期")
    brand: str = Field(..., description="品牌")
    platform: str = Field(..., description="平台")
    keyword: str = Field(..., description="关键词")
    mention_rate: float = Field(..., description="提及率(比例，0~1)")


class BrandMentionTrendResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    data: List[BrandMentionTrendItem] = Field(..., description="趋势数据列表")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class CitationUrlData(BaseModel):
    answer_reference_url: str = Field(..., description="引用URL")
    citation_count: int = Field(..., description="引用次数")
    total_questions: int = Field(..., description="总提问数")
    chinese_name: str = Field(..., description="中文名称")
    citation_rate: float = Field(..., description="引用率(引用次数/总提问数)")


class CitationUrlResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    data: List[CitationUrlData] = Field(..., description="引用URL统计数据列表")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class CitationTypeStatsSummary(BaseModel):
    total_rows: int = Field(..., description="总条数")
    conversations: int = Field(..., description="去重对话数")


class CitationTypeStatsItem(BaseModel):
    content_type: str = Field(..., description="引用类型")
    type_pct: float = Field(..., description="引用类型占比(百分比)")


class CitationTypeStatsResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    summary: CitationTypeStatsSummary = Field(..., description="汇总信息")
    citation_type_stats: List[CitationTypeStatsItem] = Field(
        ...,
        description="引用类型占比列表",
    )
    metadata: Dict[str, Any] = Field(..., description="元数据")


class BrandMetricsItem(BaseModel):
    brand: str = Field(..., description="品牌名称")
    mention_rate: float = Field(..., description="品牌总提及率")
    first_mention_rate: float = Field(..., description="首次提及品牌率")
    top3_mention_rate: float = Field(..., description="前3次提及品牌率")
    prompt_count: int = Field(..., description="问题总数")
    keyword_coverage: int = Field(..., description="关键词覆盖数")


class BrandMetricsResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    data: List[BrandMetricsItem] = Field(..., description="品牌总指标列表")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class AvailableDatesResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    data: List[str] = Field(..., description="日期列表 (YYYY-MM-DD)")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class FilterMetadataCombination(BaseModel):
    platform: str = Field(..., description="平台名称")
    keyword: str = Field(..., description="关键词")


class FilterMetadataData(BaseModel):
    platforms: List[str] = Field(..., description="平台列表（去重）")
    keywords: List[str] = Field(..., description="关键词列表（去重）")
    combinations: List[FilterMetadataCombination] = Field(
        ...,
        description="有效的平台与关键词组合列表",
    )


class FilterMetadataResponse(BaseModel):
    code: int = Field(..., description="状态码")
    message: str = Field(..., description="状态信息")
    data: FilterMetadataData = Field(..., description="筛选元数据")


class PlatformMetricsByBrandItem(BaseModel):
    platform: str = Field(..., description="平台名称")
    mention_rate: float = Field(..., description="平台提及率")


class PlatformMetricsByBrandData(BaseModel):
    brand: str = Field(..., description="品牌名称")
    platforms: List[PlatformMetricsByBrandItem] = Field(..., description="平台指标列表")


class PlatformMetricsByBrandResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    data: PlatformMetricsByBrandData = Field(..., description="品牌平台指标数据")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class DomainCitationRateItem(BaseModel):
    domain: str = Field(..., description="域名")
    chinese_name: str = Field(..., description="域名中文名称")
    keywords: str = Field(..., description="关键词（多个以逗号分隔）")
    content_types: str = Field(..., description="内容类型（多个以逗号分隔）")
    platforms: str = Field(..., description="中国大模型平台（多个以逗号分隔）")
    domain_citation_rate: float = Field(..., description="域名引用率")


class DomainCitationRateResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    domain_distribution: List[DomainCitationRateItem] = Field(..., description="域名引用率分布")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class PostCitationRateData(BaseModel):
    brand: str = Field(..., description="品牌名称")
    citation_source_count: int = Field(..., description="引用来源数量")
    citation_rate_by_post: float = Field(..., description="发文引用率（有发文引用的对话占比）")


class PostCitationRateResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    data: List[PostCitationRateData] = Field(..., description="数据列表")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class DomainCitationSummaryItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    domain: str = Field(..., description="域名")
    chinese_name: str = Field(..., description="域名中文名称")
    citation_count: int = Field(..., description="域名引用次数")
    keyword_coverage: int = Field(..., description="域名关键词覆盖数")
    platform_coverage: int = Field(..., description="域名平台覆盖数")
    domain_citation_rate: float = Field(
        ...,
        alias="domain-citation-rate",
        description="域名总引用率",
    )


class DomainCitationSummaryResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    domain_distribution: List[DomainCitationSummaryItem] = Field(
        ...,
        description="域名引用率汇总分布",
    )
    metadata: Dict[str, Any] = Field(..., description="元数据")
