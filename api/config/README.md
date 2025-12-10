# LLM 配置说明

该目录用于存放与 LLM 相关的本地配置文件，目前为模拟配置。

- `llm_settings.json`
  - `provider`: LLM 提供商标识，例如 `zhipuai`
  - `api_key`: 接口密钥（此处为 mock 值，勿用于生产）
  - `model`: 模型名称，例如 `glm-4.6`
  - `endpoint`: 接口地址（模拟）
  - `timeout_seconds`: 请求超时时间（秒）

后续接入真实配置时，可将该文件替换为安全的加载方式（环境变量、密钥管理）。
