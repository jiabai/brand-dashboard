# LLM Ping Plugin

## 概述

`llm_ping` 是工具类插件，用于向兼容 OpenAI Chat Completions 的 LLM 服务发送一次小请求，验证服务是否可访问、认证是否可用以及响应耗时是否正常。

## 插件信息

- 插件 ID：`llm_ping`
- 代码位置：`src/plugins/utils/llm_ping.py`
- 注册方式：`PluginRegistry.register(name="llm_ping", requires_llm=True)`
- 默认状态：注册默认启用，但是否运行由 `config/analysis_config.json` 中 `brand_analysis.plugins.llm_ping.enabled` 控制
- 运行方式：作为没有数据表配置的 utility plugin，由 `BrandAnalyzer.run_utility_plugins` 调用

## 配置

在 `config/analysis_config.json` 的 `brand_analysis.plugins` 中启用：

```json
{
  "brand_analysis": {
    "plugins": {
      "llm_ping": {
        "enabled": true,
        "description": "LLM服务连通性检测工具"
      }
    },
    "llm": {
      "apiKey": "your-api-key",
      "baseURL": "https://api.siliconflow.cn/v1",
      "model": "deepseek-ai/DeepSeek-V3.2-Exp",
      "timeout": 30000,
      "maxRetries": 2,
      "maxTokens": 100
    }
  }
}
```

`apiKey`、`baseURL`、`model` 等字段也可由 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`、`LLM_PROVIDER` 在配置缺失或仍为占位符时补全。

## 使用方式

推荐通过项目 CLI 触发：

```bash
python -m src -b "测试品牌" -c .\config\analysis_config.json
```

当 `llm_ping` 启用且没有 `table` 或 `datasources` 配置时，主流程会先运行该工具插件。也可以在代码中通过 `BrandAnalyzer.run_plugin("llm_ping", brand_name)` 手动调用。

## 结果结构

成功时返回：

```json
{
  "status": "success",
  "message": "LLM服务连通性良好",
  "available": true,
  "response_time": 515.74,
  "status_code": 200,
  "model_used": "deepseek-ai/DeepSeek-V3.2-Exp",
  "response_content": "测试通过，没有问题",
  "config_used": {
    "baseURL": "https://api.siliconflow.cn/v1",
    "model": "deepseek-ai/DeepSeek-V3.2-Exp",
    "timeout": 30000
  }
}
```

失败时通常返回 `status: "error"`，并包含 `status_code`、`error_type`、`error_details` 或 `timeout` 等定位信息。

## 安全注意事项

- 不要在文档、日志或测试输出中写入真实 API Key。
- `error_details` 可能包含供应商响应文本，发布前应确认其中没有敏感信息。
- 连通性测试会产生真实网络请求和可能的费用，默认测试不应依赖它。

## 维护规则

- 修改插件 ID、配置路径或调用方式时，同步更新本文件和 `docs/references/index.md`。
- 如果 LLM 配置校验规则变化，同步更新 `docs/DESIGN.md` 的配置结构约束。
