from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
