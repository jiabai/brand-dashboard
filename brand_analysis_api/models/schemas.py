"""API数据模型和模式定义."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

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
