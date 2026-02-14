# 数据加载与管理 API 文档

## 📥 数据加载 API

### LLM查询任务加载接口

### 接口信息
- **路径**: `/api/v1/query-jobs/load`
- **方法**: `POST`
- **描述**: 接收原始 JSON 数据并批量加载到 `llm_query_jobs` 数据库表中。

### 请求参数 (JSON Body)

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 Key |
| job_id | string | 是 | 任务 ID |
| effective_from | string | 是 | 生效开始时间 (ISO 8601 格式) |
| effective_to | string | 否 | 生效结束时间 (ISO 8601 格式) |
| executor_id | string | 是 | 执行器 ID |
| total_runs | integer | 是 | 总执行次数 (默认: 15) |
| executed_runs | integer | 否 | 已执行次数 (默认: 0) |
| last_executed_date | string | 是 | 最近执行日期 (YYYY-MM-DD，默认: 当前日期) |
| data | object | 是 | 任务相关的查询配置数据对象 |

#### data 对象结构

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| category | string | 是 | 分类名称 |
| brand | string | 是 | 品牌名称 |
| competitor | array | 是 | 竞品名称列表 |
| content | array | 是 | 内容列表，包含关键词和查询内容 |

#### content 数组项结构

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| keyword | string | 是 | 关键词 |
| query_content | array | 是 | 查询内容（Query）列表 |

### 请求示例

```bash
curl -X POST "http://your-api.com/api/v1/query-jobs/load" \
     -H "Content-Type: application/json" \
     -d '{
  "tenant_key": "tn_1b02b3ef4fbd",
  "job_id": "job_20260123_172515_f38024e2",
  "effective_from": "2026-01-23T00:00:00",
  "effective_to": "2026-02-01T00:00:00",
  "executor_id": "exec_bbda021a",
  "total_runs": 10,
  "executed_runs": 0,
  "last_executed_date": "2026-01-23",
  "data": {
    "category": "游戏",
    "brand": "哈基桃电竞",
    "competitor": [
        "河马电竞俱乐部",
        "五九电竞俱乐部",
        "知悦电竞俱乐部",
        "黛玉电竞俱乐部"
    ],
    "content": [
        {
            "keyword": "三角洲陪玩",
            "query_content":  [
                "三角洲陪玩有什么推荐？",
                "三角洲陪玩哪家好？",
                "三角洲陪玩哪家靠谱？",
                "三角洲陪玩哪家专业？",
                "三角洲陪玩哪家服务好？",
                "三角洲陪玩哪家口碑好？",
                "三角洲陪玩哪家性价比高？",
                "三角洲陪玩哪家打手实力强？"
            ]
        },
        {
            "keyword": "三角洲陪玩俱乐部",
            "query_content":  [
                "三角洲陪玩俱乐部有什么推荐？",
                "三角洲陪玩俱乐部哪家好？",
                "三角洲陪玩俱乐部哪家靠谱？",
                "三角洲陪玩俱乐部哪家专业？",
                "三角洲陪玩俱乐部哪家服务好？",
                "三角洲陪玩俱乐部哪家口碑好？",
                "三角洲陪玩俱乐部哪家性价比高？",
                "三角洲陪玩俱乐部售后服务好？"
            ]
        }
    ]
  }
}'
```

### 响应格式

```json
{
  "success": true,
  "inserted_rows": 2,
  "message": "LLM查询任务加载成功"
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| success | boolean | 是否处理成功 |
| inserted_rows | int | 实际插入数据库的行数 |
| message | string | 提示消息 |

---

### LLM查询任务获取接口 [未使用]

### 接口信息
- **路径**: `/api/v1/query-jobs/fetch` [未使用]
- **方法**: `GET`
- **描述**: 执行器获取待执行任务。采用 Round-Robin 策略：优先选取已执行次数最少的任务，且按物理顺序排列。

### 请求参数 (Query & Header)

| 参数名 | 类型 | 必填 | 位置 | 描述 |
|--------|------|------|------|------|
| executor_id | string | 是 | Query | 执行器唯一 ID |
| X-Executor-Key | string | 是 | Header | 执行器 API Key |
| tenant_key | string | 否 | Query | 租户标识 Key (可选，用于过滤) |
| job_id | string | 否 | Query | 任务 ID (可选，用于过滤) |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/query-jobs/fetch?executor_id=exec_bbda021a&tenant_key=tn_xxx" \
     -H "X-Executor-Key: sk-xxxx-your-api-key"
```

### 响应示例

```json
{
    "success": true,
    "count": 1,
    "jobs": {
        "id": 1,
        "job_id": "job_20260123_172515_f38024e2",
        "tenant_key": "tn_1b02b3ef4fbd",
        "category": "游戏",
        "brand": "哈基桃电竞",
        "competitor": [
            "河马电竞俱乐部",
            "五九电竞俱乐部",
            "知悦电竞俱乐部",
            "黛玉电竞俱乐部"
        ],
        "keyword": "三角洲陪玩",
        "query_content": "三角洲陪玩有什么推荐？"
    }
}
```

---

### LLM查询任务状态查询接口

### 接口信息
- **路径**: `/api/v1/query-jobs/status`
- **方法**: `GET`
- **描述**: 追踪 LLM 查询 query 的执行与生效情况。该接口允许租户管理员或系统监控人员查看query的当前状态、生效生命周期（开始/结束时间）以及对应的查询内容。支持通过任务状态码识别任务是处于“等待中”、“执行中”还是“已完成/失效”状态。

### 请求参数 (Query)

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 Key |
| job_id | string | 否 | 任务 ID |
| include_deleted | boolean | 否 | 是否包含已删除任务（默认 false） |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/query-jobs/status?tenant_key=tn_1b02b3ef4fbd&job_id=job_456&include_deleted=false"
```

### 响应示例

```json
{
  "success": true,
  "count": 2,
  "jobs": [
    {
        "tenant_key": "tn_1b02b3ef4fbd",
        "job_id": "job_20260201_171229_34974f3a",
        "brand": "宝马",
        "competitor": [
            "奔驰",
            "蔚来"
        ],
        "query_content": "宝马汽车的驾驶乐趣有哪些？",
        "query_status": 1,
        "effective_from": "2026-02-01T00:00:00",
        "effective_to": "2026-02-03T00:00:00"
    },
    {
        "tenant_key": "tn_1b02b3ef4fbd",
        "job_id": "job_20260127_223236_989cc4db",
        "brand": "哈基桃电竞",
        "competitor": [
            "河马电竞",
            "五九电竞",
            "知悦电竞",
            "黛玉电竞"
        ],
        "query_content": "三角洲陪玩俱乐部售后服务好？",
        "query_status": 3,
        "effective_from": "2026-01-26T16:00:00",
        "effective_to": "2026-01-31T16:00:00"
    }
  ]
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| success | boolean | 是否成功 |
| count | int | 任务数量 |
| jobs | array | 任务状态列表 |
| jobs.tenant_key | string | 租户标识 Key |
| jobs.job_id | string | 任务 ID |
| jobs.brand | string | 品牌名称 |
| jobs.competitor | array | 竞品名称列表 |
| jobs.query_content | string | 查询内容 |
| jobs.query_status | int | 问题生效状态：<br>0: **未生效** (等待开始或手动禁用)<br>1: **生效中** (执行器正在抓取)<br>2: **已完成** (已达总执行次数)<br>3: **已失效** (超过生效结束时间) |
| jobs.effective_from | string | 生效开始时间 (ISO 8601 格式) |
| jobs.effective_to | string | 生效结束时间 (ISO 8601 格式，可为空) |

---

### LLM查询任务上报接口 [未使用]

### 接口信息
- **路径**: `/api/v1/query-jobs/report` [未使用]
- **方法**: `POST`
- **描述**: 执行器上报任务执行结果，系统将增加该任务的已执行次数，并更新最近执行日期。

### 请求参数 (Query, Header & Body)

| 参数名 | 类型 | 必填 | 位置 | 描述 |
|--------|------|------|------|------|
| executor_id | string | 是 | Query | 执行器唯一 ID |
| X-Executor-Key | string | 是 | Header | 执行器 API Key |
| id | integer | 是 | Body (JSON) | 任务记录唯一主键 ID |

### 请求示例

```bash
curl -X POST "http://localhost:8000/api/v1/query-jobs/report?executor_id=exec_bbda021a" \
     -H "X-Executor-Key: ek_d7c2a651c2b40a3f97f3642cb628844c" \
     -H "Content-Type: application/json" \
     -d "{\"id\": 1}"
```

### 响应示例

```json
{
  "success": true,
  "message": "上报成功"
}
```

---

### LLM对话入库接口 [未使用]

### 接口信息
- **路径**: `/api/v1/conversation/load` [未使用]
- **方法**: `POST`
- **描述**: 执行器批量上报对话与引用数据，写入 `llm_conversations` 与 `llm_conversation_references` 表。

### 请求参数 (Query, Header & Body)

| 参数名 | 类型 | 必填 | 位置 | 描述 |
|--------|------|------|------|------|
| executor_id | string | 是 | Query | 执行器唯一 ID |
| X-Executor-Key | string | 是 | Header | 执行器 API Key |
| tenant_key | string | 是 | Body (JSON) | 租户标识 Key |
| job_id | string | 是 | Body (JSON) | 任务 ID |
| platform | string | 是 | Body (JSON) | 平台名称 |
| items | array | 是 | Body (JSON) | 对话批量数据 |

#### items 数组项结构

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| conversation_id | string | 是 | 对话 ID（幂等主键） |
| keyword | string | 是 | 关键词 |
| brand | string | 否 | 品牌名称 |
| category | string | 是 | 商品大类 |
| query_content | string | 是 | 用户提问内容 |
| answer_content | string | 是 | 平台回复内容 |
| extracted_at | string | 否 | 抽取时间 (ISO 8601) |
| references | array | 否 | 引用列表 |

#### references 数组项结构

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| url | string | 是 | 引用链接 |
| site_name | string | 否 | 站点名称 |
| cite_index | integer | 否 | 引用序号 |

### 请求示例

```bash
curl -X POST "http://your-api.com/api/v1/conversation/load?executor_id=exec_3f2a1b9c" \
     -H "X-Executor-Key: sk-xxxx-your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
  "tenant_key": "tn_1b02b3ef4fbd",
  "job_id": "job_20260123_172515_f38024e2",
  "platform": "deepseek",
  "items": [
    {
      "conversation_id": "conversation_9f3c1a7b",
      "keyword": "三角洲陪玩",
      "brand": "哈基桃电竞",
      "category": "游戏",
      "query_content": "三角洲陪玩有什么推荐？",
      "answer_content": "……",
      "extracted_at": "2026-01-25T12:34:56Z",
      "references": [
        {
          "url": "https://www.zhihu.com/question/xxx",
          "site_name": "知乎",
          "cite_index": 1
        }
      ]
    }
  ]
}'
```

### 响应格式

```json
{
  "success": true,
  "inserted_conversations": 1,
  "inserted_references": 1,
  "message": "对话入库成功"
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| success | boolean | 是否处理成功 |
| inserted_conversations | int | 新增对话数 |
| inserted_references | int | 新增引用数 |
| message | string | 提示消息 |

---

### LLM对话获取接口 [未使用]

### 接口信息
- **路径**: `/api/v1/conversation/fetch` [未使用]
- **方法**: `GET`
- **描述**: 获取对话与引用列表，支持分页。

### 请求参数 (Query & Header)

| 参数名 | 类型 | 必填 | 位置 | 描述 |
|--------|------|------|------|------|
| executor_id | string | 是 | Query | 执行器唯一 ID |
| X-Executor-Key | string | 是 | Header | 执行器 API Key |
| tenant_key | string | 是 | Query | 租户标识 Key |
| job_id | string | 是 | Query | 任务 ID |
| platform | string | 否 | Query | 平台名称 |
| limit | integer | 否 | Query | 返回条数，默认 50 |
| cursor | string | 否 | Query | 分页游标 |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/conversation/fetch?executor_id=exec_3f2a1b9c&tenant_key=tn_xxx&job_id=job_456&platform=deepseek&limit=10" \
     -H "X-Executor-Key: sk-xxxx-your-api-key"
```

### 响应示例

```json
{
  "success": true,
  "count": 1,
  "items": [
    {
      "conversation_id": "conversation_9f3c1a7b",
      "tenant_key": "tn_1b02b3ef4fbd",
      "job_id": "job_20260123_172515_f38024e2",
      "platform": "deepseek",
      "keyword": "三角洲陪玩",
      "brand": "哈基桃电竞",
      "category": "游戏",
      "query_content": "三角洲陪玩有什么推荐？",
      "answer_content": "……",
      "extracted_at": "2026-01-25T12:34:56Z",
      "references": [
        {
          "url": "https://www.zhihu.com/question/xxx",
          "domain": "zhihu.com",
          "site_name": "知乎",
          "cite_index": 1,
          "content_type": "ugc"
        }
      ]
    }
  ],
  "next_cursor": "eyJpZCI6MTIzfQ=="
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| success | boolean | 是否处理成功 |
| count | int | 返回对话数量 |
| items | array | 对话数据列表 |
| next_cursor | string | 下一页游标 |

---

## 🛠️ 执行器管理 API (Executors) [未使用]

系统采用 **"先预设 IP，后注册取回凭据"** 的安全流程：
1. **预设**: 管理员在系统中手动创建执行器记录，并指定其固定的 `ip_address`。
2. **注册**: 执行器从预设的 IP 发起请求，通过 `/register` 接口取回自己的 `executor_id` 和 `api_key`。
3. **调用**: 执行器使用取回的凭据调用数据加载等业务接口。

### 1. 预设执行器 (Admin: Create Executor) [未使用]

**接口地址**: `POST /api/v1/executors/` [未使用]

**请求参数 (JSON Body)**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| name | string | 是 | 执行器名称（全局唯一，注册时使用） |
| ip_address | string | 是 | 执行器的固定 IP 地址 |
| type | string | 否 | 执行器类型（如: `crawler`） |

**请求示例**:
```bash
curl -X POST "http://your-api.com/api/v1/executors/" \
     -H "Content-Type: application/json" \
     -d '{
  "name": "laptop PC-query01",
  "ip_address": "192.168.31.112",
  "type": "crawler"
}'
```

**响应示例**:
```json
{
  "executor_id": "exec_3f2a1b9c",
  "name": "laptop PC-query01",
  "ip_address": "192.168.31.112",
  "type": "crawler",
  "status": "active",
  "created_at": "2024-01-23T10:00:00"
}
```

### 2. 执行器注册 (Executor: Register) [未使用]

**接口地址**: `POST /api/v1/executors/register` [未使用]

**描述**: 执行器启动时调用此接口。身份验证完全基于请求的 **来源 IP**。

**请求参数**: 无。

**请求示例**:
```bash
# 执行器只需发起一个空 Body 的 POST 请求
curl -X POST "http://your-api.com/api/v1/executors/register" \
     -H "Content-Type: application/json" \
     -d "{}"
```

**响应示例**:
```json
{
  "executor_id": "exec_3f2a1b9c",
  "api_key": "ek_7d9e2f4a5b6c8d9e0f1a2b3c4d5e6f7a"
}
```

### 3. 获取执行器列表 (List) [未使用]

**接口地址**: `GET /api/v1/executors/` [未使用]

**描述**: 获取系统中所有执行器的列表。出于安全考虑，该接口不返回 `api_key`。

**请求示例**:

```bash
curl -X GET "http://your-api.com/api/v1/executors/"
```

**响应示例**:

```json
[
  {
    "executor_id": "exec_3f2a1b9c",
    "name": "爬虫集群-A",
    "type": "crawler",
    "status": "active",
    "created_at": "2024-01-23T10:00:00"
  }
]
```

### 4. 禁用执行器 (Deactivate Executor) [未使用]

**接口地址**: `DELETE /api/v1/executors/{executor_id}` [未使用]

**描述**: 将指定执行器的状态设置为 `inactive`，禁用其访问权限。

**请求示例**:

```bash
curl -X DELETE "http://your-api.com/api/v1/executors/exec_3f2a1b9c"
```

**响应示例**:

```json
{
  "success": true,
  "message": "执行器 exec_3f2a1b9c 已禁用"
}
```

---

## 🧠 品牌策略与分析 API (LLM) [未使用]

### 品牌定位关键词生成 [未使用]

### 接口信息
- **路径**: `/api/v1/analysis/positioning-keywords` [未使用]
- **方法**: `POST`
- **描述**: 基于行业和品牌名称，利用 LLM 生成品牌定位关键词。

### 请求参数 (JSON Body)

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 Key |
| job_id | string | 是 | 任务 ID |
| industry | string | 是 | 行业名称（如：教育、汽车） |
| brand | string | 是 | 品牌名称（如：学而思、蔚来） |

### 请求示例

```bash
curl -X POST "http://your-api.com/api/v1/analysis/positioning-keywords" \
     -H "Content-Type: application/json" \
     -d '{
  "tenant_key": "tn_xxx",
  "job_id": "job_456",
  "industry": "教育",
  "brand": "学而思"
}'
```

### 响应格式

```json
[
  "关键词1",
  "关键词2",
  "关键词3"
]
```

### 实现逻辑 (LLM)
该接口目前直接调用 LLM 生成，不涉及 SQL 数据库查询。

**Prompt 模板**:
```text
你是一个品牌策略顾问。请基于品牌或产品的公开信息，直接输出一个包含5个标准化定位关键词的 JSON 数组。

要求检索品牌或产品的典型产品特征、用户评价和市场定位（可以通过搜索互联网信息进行检索），从检索结果中提取5个最核心的产品关键词
确保这些关键词：
- 精准反映产品核心优势
- 与竞品形成差异化
- 直接关联用户真实需求
- 适用于品牌营销和定位
- 仅输出 JSON 数组，不要任何解释、标注、注释或额外文本；
- 使用双引号，符合标准 JSON 格式。

现在为以下品牌或产品输出定位关键词：
{brand}
```

---

### 消费者常见问题生成 [未使用]

### 接口信息
- **路径**: `/api/v1/analysis/consumer-questions` [未使用]
- **方法**: `POST`
- **描述**: 基于行业、品牌和核心关键词，生成消费者可能会问的问题。

### 请求参数 (JSON Body)

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 Key |
| job_id | string | 是 | 任务 ID |
| industry | string | 是 | 行业名称 |
| brand | string | 是 | 品牌名称 |
| keywords | array | 是 | 关键词列表 |

### 请求示例

```bash
curl -X POST "http://your-api.com/api/v1/analysis/consumer-questions" \
     -H "Content-Type: application/json" \
     -d '{
  "tenant_key": "tn_xxx",
  "job_id": "job_456",
  "industry": "教育",
  "brand": "学而思",
  "keywords": ["奥数", "网课", "培优"]
}'
```

### 响应格式

```json
{
  "关键词1": ["问题1", "问题2"],
  "关键词2": ["问题3", "问题4"]
}
```

### 实现逻辑 (LLM)
该接口目前直接调用 LLM 生成，不涉及 SQL 数据库查询。

**Prompt 模板**:
```text
请根据{industry}行业{brand}的以下5个关键词，为每个关键词生成3个消费者在购买前可能提出的问题。

要求：
1. 每个关键词对应3个问题；
2. 每个问题应从不同角度切入（例如价格、质量、售后服务、使用体验、环保性、兼容性、安全性、品牌信誉等）；
3. 同一关键词下的3个问题之间应尽量避免内容重叠或逻辑关联；
4. 问题需贴近真实消费者的语言习惯，具有实际参考价值。

输出格式：
- 严格使用 JSON 格式，键为关键词，值为包含3个问题的数组；
- 不包含任何额外说明、注释或解释性文字。

关键词列表：
{keywords}
```
