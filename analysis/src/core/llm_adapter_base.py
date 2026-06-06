import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional, Union


@dataclass
class UnifiedResponse:
    """统一的响应格式"""

    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float
    status_code: int = 200
    headers: Optional[Dict[str, str]] = None


@dataclass
class UnifiedError:
    """统一的错误格式"""

    error_type: str
    error_message: str
    status_code: Optional[int] = None
    retryable: bool = True
    details: Optional[Dict[str, Any]] = None


class BaseLLMAdapter(ABC):
    """LLM适配器基类"""

    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.config = kwargs
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(f"{self.__class__.__name__}_{id(self)}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    @abstractmethod
    async def create_chat_completion(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Union[UnifiedResponse, UnifiedError]:
        """创建聊天完成"""
        pass

    @abstractmethod
    async def create_chat_completion_stream(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """创建流式聊天完成"""
        pass
