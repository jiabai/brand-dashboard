# 统一LLM操作器 (Unified LLM Operator)

一个支持多种LLM SDK的统一操作器，兼容OpenAI、智谱AI、SiliconFlow、DeepSeek等多种LLM提供商。

## 特性

- 🔌 **多提供商支持**: 支持OpenAI、智谱AI、SiliconFlow、DeepSeek等
- 🔄 **统一接口**: 提供统一的API接口，无需关心底层SDK差异
- ⚡ **异步支持**: 完全支持异步操作，提高性能
- 🌊 **流式响应**: 支持流式响应，实时获取生成内容
- 💾 **智能缓存**: 内置缓存机制，减少重复请求
- 📊 **统计监控**: 提供详细的统计信息和健康检查
- 🛡️ **错误处理**: 完善的错误处理和重试机制
- 🔧 **易于扩展**: 适配器模式，易于添加新的LLM提供商

## 安装

### 基础安装

```bash
pip install openai
```

### 智谱AI支持

```bash
pip install zhipuai
```

### 完整依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 基本使用

```python
import asyncio
from src.core.llm_operator import create_openai_operator, create_zhipuai_operator

# 创建OpenAI操作器
openai_operator = create_openai_operator(
    api_key="your-openai-api-key",
    model="gpt-3.5-turbo"
)

# 创建智谱AI操作器
zhipuai_operator = create_zhipuai_operator(
    api_key="your-zhipuai-api-key",
    model="glm-4.6"
)

# 定义消息
messages = [
    {"role": "system", "content": "你是一个有用的AI助手。"},
    {"role": "user", "content": "你好，请介绍一下自己。"}
]

# 同步调用
response = openai_operator.chat_completion(messages)
print(f"响应: {response.content}")
print(f"模型: {response.model}")
print(f"提供商: {response.provider}")
print(f"响应时间: {response.response_time:.2f}秒")

# 异步调用
async def async_example():
    response = await zhipuai_operator.chat_completion_async(messages)
    print(f"异步响应: {response.content}")

asyncio.run(async_example())
```

### 2. 流式响应

```python
import asyncio

async def streaming_example():
    messages = [{"role": "user", "content": "请写一首关于春天的短诗。"}]

    print("流式响应开始:")
    async for chunk in openai_operator.chat_completion_stream_async(messages):
        if "error" in chunk:
            print(f"错误: {chunk['error']}")
            break
        elif "content" in chunk:
            print(chunk["content"], end="", flush=True)
    print("\n流式响应结束")

asyncio.run(streaming_example())
```

### 3. 多提供商对比

```python
import asyncio

async def compare_providers():
    providers = [
        create_openai_operator(api_key="openai-key", model="gpt-3.5-turbo"),
        create_zhipuai_operator(api_key="zhipuai-key", model="glm-4.6"),
        create_silicon_flow_operator(api_key="silicon-key", model="deepseek-ai/DeepSeek-V3.2-Exp")
    ]

    messages = [{"role": "user", "content": "用一句话介绍人工智能。"}]

    for i, operator in enumerate(providers):
        response = await operator.chat_completion_async(messages)
        if hasattr(response, 'content'):
            print(f"提供商{i+1}: {response.provider} - {response.content}")

asyncio.run(compare_providers())
```

## 高级功能

### 1. 自定义提供商

```python
from src.core.llm_operator import create_enhanced_llm_operator

# 创建自定义提供商操作器
custom_operator = create_enhanced_llm_operator(
    provider="custom",
    api_key="your-api-key",
    base_url="https://your-custom-api.com/v1",
    model="your-custom-model",
    temperature=0.7,
    max_tokens=1500
)
```

### 2. 缓存和统计

```python
# 启用缓存
operator = create_openai_operator(
    api_key="your-api-key",
    use_cache=True  # 默认启用
)

# 获取统计信息
stats = operator.get_stats()
print(f"总请求数: {stats['total_requests']}")
print(f"成功率: {stats['success_rate']:.2%}")
print(f"平均响应时间: {stats['average_response_time']:.2f}秒")
print(f"总token数: {stats['total_tokens']}")

# 清除缓存
operator.clear_cache()

# 健康检查
health = operator.health_check()
print(f"健康状态: {health['status']}")
```

### 3. 错误处理

```python
response = operator.chat_completion(messages)

if hasattr(response, 'content'):
    print(f"成功: {response.content}")
else:
    print(f"错误类型: {response.error_type}")
    print(f"错误信息: {response.error_message}")
    print(f"状态码: {response.status_code}")
    print(f"是否可重试: {response.retryable}")
    print(f"提供商: {response.provider}")
```

## 配置选项

### 1. 基础配置

```python
operator = create_enhanced_llm_operator(
    provider="openai",           # 提供商
    api_key="your-api-key",      # API密钥
    model="gpt-3.5-turbo",       # 模型名称
    base_url="https://api.openai.com/v1",  # 基础URL（可选）
    timeout=30000,                # 超时时间（毫秒）
    max_retries=3,                # 最大重试次数
    max_tokens=2000,              # 最大token数
    temperature=0.1,              # 温度参数
    top_p=1.0,                    # top_p参数
    frequency_penalty=0.0,        # 频率惩罚
    presence_penalty=0.0,         # 存在惩罚
    stream=False,                 # 是否流式
    use_cache=True                # 是否使用缓存
)
```

### 2. 预设配置

```python
# OpenAI配置
openai_config = {
    "provider": "openai",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-3.5-turbo"
}

# 智谱AI配置
zhipuai_config = {
    "provider": "zhipuai",
    "base_url": "https://open.bigmodel.cn/api/paas/v4",
    "model": "glm-4.6"
}

# SiliconFlow配置
silicon_flow_config = {
    "provider": "silicon_flow",
    "base_url": "https://api.siliconflow.cn/v1",
    "model": "deepseek-ai/DeepSeek-V3.2-Exp"
}

# DeepSeek配置
deepseek_config = {
    "provider": "deepseek",
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat"
}
```

## 支持的提供商

| 提供商      | 提供商代码     | 基础URL                              | 支持模型         | 特殊要求         |
| ----------- | -------------- | ------------------------------------ | ---------------- | ---------------- |
| OpenAI      | `openai`       | https://api.openai.com/v1            | GPT-3.5, GPT-4等 | 需要openai库     |
| 智谱AI      | `zhipuai`      | https://open.bigmodel.cn/api/paas/v4 | GLM-4, GLM-3等   | 需要zhipuai库    |
| SiliconFlow | `silicon_flow` | https://api.siliconflow.cn/v1        | DeepSeek, Qwen等 | OpenAI兼容       |
| DeepSeek    | `deepseek`     | https://api.deepseek.com/v1          | deepseek-chat等  | OpenAI兼容       |
| 自定义      | `custom`       | 自定义                               | 自定义           | 需要提供base_url |

## 扩展新的提供商

要添加新的LLM提供商，需要：

1. 创建新的适配器类，继承自`BaseLLMAdapter`
2. 实现`create_chat_completion`和`create_chat_completion_stream`方法
3. 注册到`LLMFactory`

```python
from src.core.llm_adapters import BaseLLMAdapter, LLMFactory, UnifiedResponse, UnifiedError

class MyLLMAdapter(BaseLLMAdapter):
    async def create_chat_completion(self, messages, **kwargs):
        # 实现聊天完成逻辑
        return UnifiedResponse(...)

    async def create_chat_completion_stream(self, messages, **kwargs):
        # 实现流式聊天完成逻辑
        yield {...}

# 注册适配器
LLMFactory.register_adapter("mylm", MyLLMAdapter)

# 使用新的提供商
operator = create_enhanced_llm_operator(
    provider="mylm",
    api_key="your-api-key",
    model="your-model"
)
```

## 最佳实践

### 1. 环境变量管理

```python
import os

# 使用环境变量存储API密钥
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_API_KEY = os.getenv("LLM_API_KEY")
SILICON_FLOW_API_KEY = os.getenv("SILICON_FLOW_API_KEY")

# 创建操作器
openai_operator = create_openai_operator(api_key=OPENAI_API_KEY)
zhipuai_operator = create_zhipuai_operator(api_key=LLM_API_KEY)
```

### 2. 错误处理和重试

```python
# 配置合适的重试次数和超时时间
operator = create_openai_operator(
    api_key="your-api-key",
    max_retries=5,      # 增加重试次数
    timeout=60000       # 增加超时时间
)

# 处理不同类型的错误
response = operator.chat_completion(messages)

if hasattr(response, 'error_message'):
    if response.status_code == 429:
        print("请求频率限制，请稍后再试")
    elif response.status_code == 401:
        print("API密钥无效")
    elif not response.retryable:
        print("不可重试错误，需要人工处理")
    else:
        print(f"其他错误: {response.error_message}")
```

### 3. 性能优化

```python
# 启用缓存避免重复请求
operator = create_openai_operator(
    api_key="your-api-key",
    use_cache=True,           # 启用缓存
    max_tokens=1000           # 合理设置token限制
)

# 使用异步操作提高效率
async def batch_requests():
    messages_list = [
        [{"role": "user", "content": "问题1"}],
        [{"role": "user", "content": "问题2"}],
        [{"role": "user", "content": "问题3"}]
    ]

    # 并发执行
    tasks = [operator.chat_completion_async(messages) for messages in messages_list]
    responses = await asyncio.gather(*tasks)

    return responses

# 监控性能指标
stats = operator.get_stats()
if stats['success_rate'] < 0.9:
    print("成功率较低，需要检查配置")
if stats['average_response_time'] > 5.0:
    print("响应时间较长，考虑更换提供商")
```

## 故障排除

### 1. 智谱AI SDK安装问题

```bash
# 确保安装正确版本的zhipuai
pip install zhipuai --upgrade

# 如果安装失败，可以尝试
pip install zhipuai -i https://pypi.org/simple/
```

### 2. API连接问题

```python
# 检查网络连接
operator = create_enhanced_llm_operator(
    provider="openai",
    api_key="your-api-key",
    timeout=60000,  # 增加超时时间
    max_retries=5   # 增加重试次数
)

# 进行健康检查
health = operator.health_check()
if health['status'] != 'healthy':
    print(f"连接问题: {health.get('error', '未知错误')}")
```

### 3. 模型不支持问题

```python
# 检查支持的模型列表
from src.core.llm_adapters import PRESET_CONFIGS

print("支持的提供商:", list(PRESET_CONFIGS.keys()))
print("OpenAI模型:", PRESET_CONFIGS['openai']['supported_models'])
print("智谱AI模型:", PRESET_CONFIGS['zhipuai']['supported_models'])
```

## 示例代码

当前仓库没有独立 `examples/` 目录。使用示例以本文件片段、`tests/test_unified_llm_operator.py` 和 `tests/test_llm_operator.py` 为准。

## 更新日志

### v1.0.0

- ✨ 支持OpenAI、智谱AI、SiliconFlow、DeepSeek等多种LLM提供商
- 🔄 提供统一的API接口
- ⚡ 支持异步操作和流式响应
- 💾 内置缓存机制和统计监控
- 🛡️ 完善的错误处理和重试机制

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 许可证

MIT License
