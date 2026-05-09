# Align dashboard.json with Implementation and Documentation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Align the OpenAPI specification in `api/docs/dashboard.json` with the actual FastAPI implementation in `api/v1/routes/dashboard.py` and the documentation in `api/docs/DASHBOARD_API_README.md`, specifically for the `/citation-domain-stats` endpoint and its related models.

**Architecture:** Update the OpenAPI JSON file to include missing parameters and fields identified during cross-referencing.

**Tech Stack:** OpenAPI 3.1.0, JSON

---

### Task 1: Update `/api/v1/dashboard/citation-domain-stats` parameters in `dashboard.json`

**Files:**
- Modify: `api/docs/dashboard.json`

**Step 1: Add the `platform` parameter to the `/api/v1/dashboard/citation-domain-stats` endpoint**

Add the following parameter to the `parameters` array of the `/api/v1/dashboard/citation-domain-stats` GET method:

```json
          {
            "name": "platform",
            "in": "query",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "description": "中国大模型平台",
              "title": "Platform"
            },
            "description": "中国大模型平台"
          }
```

### Task 2: Update `DomainCitationRateItem` schema in `dashboard.json`

**Files:**
- Modify: `api/docs/dashboard.json`

**Step 1: Add missing fields to `DomainCitationRateItem` properties**

Add `keyword`, `content_type`, and `platform` to the `properties` object of `DomainCitationRateItem`.

```json
          "keyword": {
            "type": "string",
            "title": "Keyword",
            "description": "关键词"
          },
          "content_type": {
            "type": "string",
            "title": "Content Type",
            "description": "内容类型"
          },
          "platform": {
            "type": "string",
            "title": "Platform",
            "description": "中国大模型平台"
          }
```

**Step 2: Update the `required` list for `DomainCitationRateItem`**

Add the new fields to the `required` array.

```json
        "required": [
          "domain",
          "chinese_name",
          "keyword",
          "content_type",
          "platform",
          "domain-citation-rate"
        ]
```

### Task 3: Update `DomainCitationRateResponse` metadata schema in `dashboard.json`

**Files:**
- Modify: `api/docs/dashboard.json`

**Step 1: Add `platform` and `calculation_method` to the metadata properties**

Update the `metadata` schema within `DomainCitationRateResponse` to match the implementation.

```json
              "platform": {
                "anyOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "null"
                  }
                ],
                "description": "中国大模型平台"
              },
              "calculation_method": {
                "type": "string",
                "description": "计算方法"
              },
              "row_count": {
                "type": "integer",
                "description": "数据行数"
              }
```

### Task 4: Verify and Commit

**Step 1: Review the changes in `dashboard.json`**

Ensure the JSON is valid and all fields match `dashboard.py`.

**Step 2: Commit changes**

```bash
git add api/docs/dashboard.json
git commit -m "docs: align dashboard.json with implementation for citation-domain-stats"
```
