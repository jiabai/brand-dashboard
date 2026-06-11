# 项目看板入口改源 collection_jobs 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 项目详情页「进入看板」Sheet 的采集任务来源从 `llm_query_jobs`（每条查询一行）改为 `collection_jobs`（一次采集一行），经 `source_job_id` + 项目目标品牌进 legacy 首页看板。

**Architecture:** 新增 `GET /api/v1/projects/{project_id}/collection-jobs`（projects 路由，`get_current_tenant_for_read`），仓储查 `collection_jobs`（`source_job_id IS NOT NULL`）+ 解析项目 target 品牌；前端新增适配器与归一化/状态映射纯函数，详情页 Sheet 改源；最后删除改源后变死代码的 `normalizeProjectJobRecords`。

**Tech Stack:** FastAPI + SQLAlchemy text SQL、pytest（内存 SQLite + TestClient）、React 18 + shadcn/ui、node:test 源码契约测试。

**Spec:** `docs/product-specs/20260611-010000-project-dashboard-entry-collection-jobs.md`

**约定与上下文（执行者必读）：**

- 门禁命令（PowerShell，仓库根目录）：
  - 后端单文件：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_project_collection_jobs.py -q`
  - 后端全量：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`（当前基线 222 passed）
  - 后端 lint：`uv run --project api ruff check api`
  - 前端测试：`npm --prefix web test`（当前基线 137 pass）；构建：`npm --prefix web run build`
  - 文档验证：`python scripts/validate_agents_docs.py --level ERROR`
- **暂存纪律**：工作区有他人未提交在途改动（平台只读 notice 等）。每次 commit **只 `git add` 任务点名文件，严禁 `git add -A` / `git add .`**。
  - **clean（正常 add）**：`api/v1/repositories/projects.py`、`api/v1/services/projects.py`、`api/v1/models/schemas.py`、`api/v1/routes/projects.py`、`api/tests/test_project_collection_jobs.py`（新建）、`web/src/api/projects.js`、`web/src/api/__tests__/projects.test.js`（新建）、`web/src/components/projects/projectPresentation.js`、`web/src/components/projects/__tests__/projectPresentation.test.js`。
  - **DIRTY（blob 构造提交）**：`web/src/components/projects/ProjectDetailPage.jsx`、`web/src/components/projects/__tests__/projectDetailPage.test.js`（HEAD 版已含上一阶段提交的看板 Sheet；blob = `git show HEAD:<file>` + 仅本任务改动；工作区保留在途 + 本任务集成）。
  - 每个任务前 `git status --porcelain -- <file>` 复核。
- **顺序要求（保证每次提交都能构建/通过）**：Task 2 先**新增**前端 helper（不删旧的）；Task 3 把 ProjectDetailPage 改成引用新 helper（不再 import `normalizeProjectJobRecords`/`fetchQueryJobStatus`/`getQueryJobStatusMeta`）；Task 4 才删除已无人引用的 `normalizeProjectJobRecords`。
- 后端响应沿用 snake_case（与现有 query-jobs/status 一致），前端归一化为 camelCase。
- 授权事实（已核实）：projects 读接口用 `get_current_tenant_for_read`（active 成员或平台只读）；看板数据接口不改。`collection_jobs.source_job_id` = legacy `job_id`（看板寻址键），库内 3/3 可对应。

---

### Task 1: 后端 —— 列项目 collection_jobs 接口 + 目标品牌

**Files（均 clean，正常 add）:**
- Modify: `api/v1/repositories/projects.py`
- Modify: `api/v1/services/projects.py`
- Modify: `api/v1/models/schemas.py`
- Modify: `api/v1/routes/projects.py`
- Create: `api/tests/test_project_collection_jobs.py`

- [x] **Step 1: 写失败的测试**

创建 `api/tests/test_project_collection_jobs.py`：

```python
from datetime import UTC, datetime

import pytest
from api.v1.repositories.connection import get_db
from api.v1.routes import projects as projects_routes
from api.v1.utils.jwt_utils import create_access_token
from api.v1.utils.security import hash_password
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

TEST_SECRET = "test-secret-with-at-least-32-bytes"


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_key VARCHAR(255) NOT NULL UNIQUE,
                tenant_name VARCHAR(255) NOT NULL UNIQUE,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP, updated_at TIMESTAMP
            )"""))
        conn.execute(text("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_key VARCHAR(36) NOT NULL UNIQUE,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                is_verified BOOLEAN NOT NULL DEFAULT 1,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP, updated_at TIMESTAMP
            )"""))
        conn.execute(text("""
            CREATE TABLE user_tenants (
                user_id INTEGER NOT NULL, tenant_id INTEGER NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'admin',
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP, PRIMARY KEY (user_id, tenant_id)
            )"""))
        conn.execute(text("""
            CREATE TABLE monitoring_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_key VARCHAR(255) NOT NULL, project_id VARCHAR(128) NOT NULL,
                name VARCHAR(255) NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL,
                UNIQUE (tenant_key, project_id)
            )"""))
        conn.execute(text("""
            CREATE TABLE project_brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_key VARCHAR(255) NOT NULL, project_id VARCHAR(128) NOT NULL,
                brand_id VARCHAR(128) NOT NULL, brand_name VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'competitor',
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL
            )"""))
        conn.execute(text("""
            CREATE TABLE collection_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_key VARCHAR(255) NOT NULL, collection_job_id VARCHAR(128) NOT NULL,
                project_id VARCHAR(128) NOT NULL, source_job_id VARCHAR(255),
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                window_start TIMESTAMP, window_end TIMESTAMP,
                expected_task_count INTEGER NOT NULL DEFAULT 0,
                succeeded_task_count INTEGER NOT NULL DEFAULT 0,
                failed_task_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL,
                UNIQUE (tenant_key, collection_job_id)
            )"""))
    connection = engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield db
    db.close()
    transaction.rollback()
    connection.close()


def _client(db):
    app = FastAPI()
    app.include_router(projects_routes.router, prefix="/api/v1/projects")
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def _token(user_id=101):
    return create_access_token(user_id, TEST_SECRET)


def _seed(db):
    now = datetime.now(UTC)
    t = db.execute(text(
        "INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)"
        " VALUES ('tn_a', 'A', 'active', :now, :now)"), {"now": now})
    db.execute(text(
        "INSERT INTO users (id, user_key, email, password_hash, is_verified, status, created_at, updated_at)"
        " VALUES (101, 'u101', 'a@x.com', :ph, 1, 'active', :now, :now)"),
        {"ph": hash_password("User12345"), "now": now})
    db.execute(text(
        "INSERT INTO user_tenants (user_id, tenant_id, role, status, created_at)"
        " VALUES (101, :tid, 'admin', 'active', :now)"), {"tid": t.lastrowid, "now": now})
    for pid in ("prj_1", "prj_2"):
        db.execute(text(
            "INSERT INTO monitoring_projects (tenant_key, project_id, name, status, created_at, updated_at)"
            " VALUES ('tn_a', :pid, 'P', 'active', :now, :now)"), {"pid": pid, "now": now})
    db.execute(text(
        "INSERT INTO project_brands (tenant_key, project_id, brand_id, brand_name, role, status, created_at, updated_at)"
        " VALUES ('tn_a', 'prj_1', 'b1', 'QuickCEP', 'target', 'active', :now, :now)"), {"now": now})
    db.execute(text(
        "INSERT INTO project_brands (tenant_key, project_id, brand_id, brand_name, role, status, created_at, updated_at)"
        " VALUES ('tn_a', 'prj_1', 'b2', 'CompetitorX', 'competitor', 'active', :now, :now)"), {"now": now})
    db.commit()


def _insert_cj(db, *, cj_id, project_id, source_job_id, window_start, status="succeeded"):
    now = datetime.now(UTC)
    db.execute(text(
        "INSERT INTO collection_jobs (tenant_key, collection_job_id, project_id, source_job_id,"
        " status, window_start, window_end, expected_task_count, succeeded_task_count,"
        " failed_task_count, created_at, updated_at)"
        " VALUES ('tn_a', :cj, :pid, :sj, :st, :ws, NULL, 12, 12, 0, :now, :now)"),
        {"cj": cj_id, "pid": project_id, "sj": source_job_id, "st": status, "ws": window_start, "now": now})
    db.commit()


def test_lists_only_source_job_id_jobs_for_project_with_target_brand(session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _seed(session)
    _insert_cj(session, cj_id="col_1", project_id="prj_1", source_job_id="job_legacy_1", window_start="2026-02-09")
    _insert_cj(session, cj_id="col_2", project_id="prj_1", source_job_id=None, window_start="2026-02-10")
    _insert_cj(session, cj_id="col_other", project_id="prj_2", source_job_id="job_legacy_2", window_start="2026-02-11")

    client = _client(session)
    resp = client.get(
        "/api/v1/projects/prj_1/collection-jobs",
        headers={"Authorization": f"Bearer {_token()}", "X-Tenant-Key": "tn_a"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["target_brand"] == "QuickCEP"
    jobs = body["collection_jobs"]
    assert {j["collection_job_id"] for j in jobs} == {"col_1"}
    assert jobs[0]["source_job_id"] == "job_legacy_1"
    assert jobs[0]["status"] == "succeeded"


def test_orders_by_window_start_desc(session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _seed(session)
    _insert_cj(session, cj_id="col_old", project_id="prj_1", source_job_id="job_old", window_start="2026-01-01")
    _insert_cj(session, cj_id="col_new", project_id="prj_1", source_job_id="job_new", window_start="2026-03-01")

    client = _client(session)
    resp = client.get(
        "/api/v1/projects/prj_1/collection-jobs",
        headers={"Authorization": f"Bearer {_token()}", "X-Tenant-Key": "tn_a"},
    )
    assert [j["collection_job_id"] for j in resp.json()["collection_jobs"]] == ["col_new", "col_old"]


def test_target_brand_null_when_absent(session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _seed(session)
    _insert_cj(session, cj_id="col_2only", project_id="prj_2", source_job_id="job_p2", window_start="2026-02-09")

    client = _client(session)
    resp = client.get(
        "/api/v1/projects/prj_2/collection-jobs",
        headers={"Authorization": f"Bearer {_token()}", "X-Tenant-Key": "tn_a"},
    )
    assert resp.status_code == 200
    assert resp.json()["target_brand"] is None


def test_requires_authenticated_tenant_member(session):
    _seed(session)
    client = _client(session)
    resp = client.get(
        "/api/v1/projects/prj_1/collection-jobs",
        headers={"X-Tenant-Key": "tn_a"},
    )
    assert resp.status_code == 401
```

- [x] **Step 2: 运行确认失败**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_project_collection_jobs.py -q`
Expected: 404（路由不存在）或属性错误，多个 FAIL。

- [x] **Step 3: 仓储函数**

`api/v1/repositories/projects.py` 末尾追加（`text` 已导入；风格对照 `list_projects`/`list_project_brands`）：

```python
def list_project_collection_jobs(db: Session, *, tenant_key: str, project_id: str):
    return db.execute(
        text(
            """
            SELECT
              collection_job_id,
              source_job_id,
              status,
              window_start,
              window_end,
              expected_task_count,
              succeeded_task_count,
              failed_task_count
            FROM collection_jobs
            WHERE tenant_key = :tenant_key
              AND project_id = :project_id
              AND source_job_id IS NOT NULL
            ORDER BY window_start DESC, id DESC
            """
        ),
        {"tenant_key": tenant_key, "project_id": project_id},
    ).mappings().all()


def get_project_target_brand(db: Session, *, tenant_key: str, project_id: str):
    row = db.execute(
        text(
            """
            SELECT brand_name
            FROM project_brands
            WHERE tenant_key = :tenant_key
              AND project_id = :project_id
              AND role = 'target'
              AND status = 'active'
            ORDER BY id ASC
            LIMIT 1
            """
        ),
        {"tenant_key": tenant_key, "project_id": project_id},
    ).fetchone()
    return row[0] if row else None
```

- [x] **Step 4: 服务函数**

`api/v1/services/projects.py` 末尾追加（`project_repo` 已作为 `from api.v1.repositories import projects as project_repo` 导入——动手前 Read 确认别名）：

```python
def list_project_collection_job_entries(db, *, tenant_key, project_id):
    rows = project_repo.list_project_collection_jobs(
        db, tenant_key=tenant_key, project_id=project_id
    )
    target_brand = project_repo.get_project_target_brand(
        db, tenant_key=tenant_key, project_id=project_id
    )
    collection_jobs = [
        {
            "collection_job_id": row["collection_job_id"],
            "source_job_id": row["source_job_id"],
            "status": row["status"],
            "window_start": str(row["window_start"]) if row["window_start"] is not None else None,
            "window_end": str(row["window_end"]) if row["window_end"] is not None else None,
            "expected_task_count": row["expected_task_count"] or 0,
            "succeeded_task_count": row["succeeded_task_count"] or 0,
            "failed_task_count": row["failed_task_count"] or 0,
        }
        for row in rows
    ]
    return {"target_brand": target_brand, "collection_jobs": collection_jobs}
```

- [x] **Step 5: 响应 schema**

`api/v1/models/schemas.py` 在 `ProjectListResponse` 之后追加（`BaseModel`/`Field`/`List` 已导入）：

```python
class ProjectCollectionJobItem(BaseModel):
    collection_job_id: str
    source_job_id: str
    status: str
    window_start: str | None = None
    window_end: str | None = None
    expected_task_count: int = 0
    succeeded_task_count: int = 0
    failed_task_count: int = 0


class ProjectCollectionJobsResponse(BaseModel):
    success: bool
    target_brand: str | None = None
    collection_jobs: List[ProjectCollectionJobItem] = Field(default_factory=list)
```

- [x] **Step 6: 路由**

`api/v1/routes/projects.py`：schemas 导入块加入 `ProjectCollectionJobsResponse`（保持字母序/现有风格）。在 `get_project_data_quality` 路由之后追加：

```python
@router.get("/{project_id}/collection-jobs", response_model=ProjectCollectionJobsResponse)
async def list_project_collection_jobs(
    project_id: str,
    tenant: CurrentTenantContext = Depends(get_current_tenant_for_read),
    db: Session = Depends(get_db),
):
    result = project_service.list_project_collection_job_entries(
        db,
        tenant_key=tenant.tenant_key,
        project_id=project_id,
    )
    return ProjectCollectionJobsResponse(
        success=True,
        target_brand=result["target_brand"],
        collection_jobs=result["collection_jobs"],
    )
```

- [x] **Step 7: 运行确认通过**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_project_collection_jobs.py -q` → 4 passed。

- [x] **Step 8: 回归 + lint**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` → 约 226 passed，0 失败。
Run: `uv run --project api ruff check api` → All checks passed!

- [x] **Step 9: Commit**（五文件 clean）

```powershell
git add api/v1/repositories/projects.py api/v1/services/projects.py api/v1/models/schemas.py api/v1/routes/projects.py api/tests/test_project_collection_jobs.py
git commit -m @'
feat: 新增按项目列 collection_jobs 接口（含目标品牌、source_job_id 过滤）

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

（here-string 结束 `'@` 顶格独占一行。）

---

### Task 2: 前端数据层 —— 适配器 + 新归一化/状态映射（不删旧 helper）

**Files（均 clean）:**
- Modify: `web/src/api/projects.js`
- Create: `web/src/api/__tests__/projects.test.js`
- Modify: `web/src/components/projects/projectPresentation.js`
- Modify: `web/src/components/projects/__tests__/projectPresentation.test.js`

- [x] **Step 1: 写失败的测试**

创建 `web/src/api/__tests__/projects.test.js`：

```js
import test from 'node:test';
import assert from 'node:assert/strict';

import { fetchProjectCollectionJobs } from '../projects.js';

const jsonResponse = (payload) => ({
  ok: true,
  status: 200,
  json: async () => payload,
  text: async () => JSON.stringify(payload),
});

test.afterEach(() => {
  delete globalThis.fetch;
});

test('fetchProjectCollectionJobs hits the project collection-jobs endpoint', async () => {
  let requestedUrl;
  globalThis.fetch = async (url) => {
    requestedUrl = url;
    return jsonResponse({ success: true, target_brand: 'QuickCEP', collection_jobs: [] });
  };

  await fetchProjectCollectionJobs({ tenantKey: 'tn_a', projectId: 'prj 1' });

  const parsed = new URL(requestedUrl, 'http://localhost');
  assert.equal(parsed.pathname, '/api/v1/projects/prj%201/collection-jobs');
});
```

在 `web/src/components/projects/__tests__/projectPresentation.test.js` 末尾追加（把 `getCollectionJobStatusMeta`、`normalizeProjectCollectionJobs` 并入顶部 import）：

```js
test('getCollectionJobStatusMeta maps collection job statuses', () => {
  assert.equal(getCollectionJobStatusMeta('succeeded').label, '已完成');
  assert.equal(getCollectionJobStatusMeta('running').label, '采集中');
  assert.equal(getCollectionJobStatusMeta('failed').variant, 'destructive');
  assert.equal(getCollectionJobStatusMeta('weird').label, 'weird');
});

test('normalizeProjectCollectionJobs maps response to camelCase with targetBrand', () => {
  const result = normalizeProjectCollectionJobs({
    target_brand: 'QuickCEP',
    collection_jobs: [
      {
        collection_job_id: 'col_1',
        source_job_id: 'job_legacy_1',
        status: 'succeeded',
        window_start: '2026-02-09 00:00:00',
        window_end: null,
        expected_task_count: 12,
        succeeded_task_count: 12,
        failed_task_count: 0,
      },
    ],
  });
  assert.equal(result.targetBrand, 'QuickCEP');
  assert.equal(result.collectionJobs.length, 1);
  assert.equal(result.collectionJobs[0].collectionJobId, 'col_1');
  assert.equal(result.collectionJobs[0].sourceJobId, 'job_legacy_1');
  assert.equal(result.collectionJobs[0].windowEnd, '');
});

test('normalizeProjectCollectionJobs handles missing payload', () => {
  assert.deepEqual(normalizeProjectCollectionJobs(null), { targetBrand: '', collectionJobs: [] });
});
```

- [x] **Step 2: 运行确认失败**

Run: `npm --prefix web test` → 新用例 FAIL（导出不存在）。

- [x] **Step 3: 实现适配器**

`web/src/api/projects.js` 末尾追加：

```js
export const fetchProjectCollectionJobs = ({ tenantKey, projectId } = {}, options = {}) =>
  fetch(`/api/v1/projects/${encodePathSegment(projectId)}/collection-jobs`, {
    ...options,
    tenantKey,
  });
```

- [x] **Step 4: 实现展示层纯函数**

`web/src/components/projects/projectPresentation.js` 末尾追加（**不删** `normalizeProjectJobRecords`，本任务只新增）：

```js
export const getCollectionJobStatusMeta = (status) => {
  const normalized = String(status || '').trim();
  const map = {
    pending: { label: '待采集', variant: 'secondary' },
    running: { label: '采集中', variant: 'default' },
    succeeded: { label: '已完成', variant: 'default' },
    failed: { label: '失败', variant: 'destructive' },
    expired: { label: '已过期', variant: 'outline' },
    cancelled: { label: '已取消', variant: 'outline' },
  };
  return map[normalized] || { label: normalized || '未知', variant: 'secondary' };
};

export const normalizeProjectCollectionJobs = (response) => {
  const jobs = Array.isArray(response?.collection_jobs) ? response.collection_jobs : [];
  return {
    targetBrand: response?.target_brand || '',
    collectionJobs: jobs.map((job) => ({
      collectionJobId: job.collection_job_id || '',
      sourceJobId: job.source_job_id || '',
      status: job.status || '',
      windowStart: job.window_start || '',
      windowEnd: job.window_end || '',
      expectedTaskCount: job.expected_task_count || 0,
      succeededTaskCount: job.succeeded_task_count || 0,
      failedTaskCount: job.failed_task_count || 0,
    })),
  };
};
```

- [x] **Step 5: 运行确认通过**

Run: `npm --prefix web test` → 全绿（基线 137 + 新增 4 ≈ 141 pass）。

- [x] **Step 6: Commit**（四文件 clean）

```powershell
git add web/src/api/projects.js web/src/api/__tests__/projects.test.js web/src/components/projects/projectPresentation.js web/src/components/projects/__tests__/projectPresentation.test.js
git commit -m @'
feat: 前端新增 collection-jobs 适配器与归一化/状态映射

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

---

### Task 3: 项目详情页 Sheet 改源（⚠️ DIRTY，blob 构造）

**Files（DIRTY → blob 构造）:**
- Modify: `web/src/components/projects/ProjectDetailPage.jsx`
- Modify: `web/src/components/projects/__tests__/projectDetailPage.test.js`

前置：Task 1/2 已入库。HEAD 版 ProjectDetailPage.jsx 含上一阶段的看板 Sheet（用 `fetchQueryJobStatus`/`normalizeProjectJobRecords`/`getQueryJobStatusMeta`）。本任务把它改成 collection_jobs 源。

- [x] **Step 1: 改契约测试**

`web/src/components/projects/__tests__/projectDetailPage.test.js` 的 `dashboard entry contract` describe（上一阶段加的）：把断言改为新标识符（删掉 `fetchQueryJobStatus`/`normalizeProjectJobRecords`/`getQueryJobStatusMeta` 三条，换为下列）。该 describe 块整体替换为：

```js
describe('ProjectDetailPage dashboard entry contract', () => {
  it('exposes an enter-dashboard button that opens a collection-job picker sheet', () => {
    assert.match(source, /进入看板/);
    assert.match(source, /fetchProjectCollectionJobs/);
    assert.match(source, /normalizeProjectCollectionJobs/);
    assert.match(source, /SheetContent/);
  });

  it('navigates to the legacy dashboard via the collection job source_job_id', () => {
    assert.match(source, /buildProjectDashboardPath/);
    assert.match(source, /getCollectionJobStatusMeta/);
    assert.match(source, /sourceJobId/);
    assert.match(source, /该项目还没有采集任务/);
  });
});
```

- [x] **Step 2: 运行确认失败**

Run: `npm --prefix web test` → 这两个用例 FAIL（旧源标识符已不在断言、新标识符尚未在源码）。

- [x] **Step 3: 改 ProjectDetailPage.jsx（工作区版本）**

(a) `@/api` 导入：把 `fetchQueryJobStatus` 换成 `fetchProjectCollectionJobs`：
```jsx
import { fetchProjectDetail, fetchProjectCollectionJobs } from '@/api';
```

(b) 删除从 `'../platform/tenantPresentation.js'` 引入的 `getQueryJobStatusMeta`（恢复为仅 `buildPlatformTenantProjectOverviewPath`，若该文件只因它而多行则收回单行）：
```jsx
import { buildPlatformTenantProjectOverviewPath } from '../platform/tenantPresentation.js';
```

(c) `'./projectPresentation.js'` 导入：去掉 `normalizeProjectJobRecords`，加入 `getCollectionJobStatusMeta` 与 `normalizeProjectCollectionJobs`（保留 `buildProjectDashboardPath`）。

(d) state：新增 `targetBrand`：
```jsx
  const [targetBrand, setTargetBrand] = useState('');
```

(e) `openDashboardSheet` 改为：
```jsx
  const openDashboardSheet = async () => {
    setDashboardSheetOpen(true);
    setIsLoadingJobs(true);
    setJobsError('');
    try {
      const response = await fetchProjectCollectionJobs({ tenantKey, projectId });
      const normalized = normalizeProjectCollectionJobs(response);
      setJobRecords(normalized.collectionJobs);
      setTargetBrand(normalized.targetBrand);
    } catch (loadError) {
      setJobRecords([]);
      setTargetBrand('');
      setJobsError(loadError?.message || '加载采集任务失败');
    } finally {
      setIsLoadingJobs(false);
    }
  };
```

(f) `enterDashboard` 改为用 `sourceJobId` + `targetBrand`：
```jsx
  const enterDashboard = (job) => {
    const path = buildProjectDashboardPath({
      tenantKey,
      jobId: job.sourceJobId,
      brand: targetBrand,
    });
    if (path) navigate(path);
  };
```

(g) Sheet 内 job 行渲染整段替换为（按 collection_job 字段；key 用 collectionJobId）：
```jsx
            {!isLoadingJobs && !jobsError
              ? jobRecords.map((job) => {
                const meta = getCollectionJobStatusMeta(job.status);
                return (
                  <button
                    key={job.collectionJobId}
                    type="button"
                    onClick={() => enterDashboard(job)}
                    className="flex items-center justify-between gap-3 rounded-md border border-border px-3 py-2 text-left hover:bg-muted/50"
                  >
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-medium text-foreground">
                        {(job.windowStart || '').slice(0, 10)}
                        {job.windowEnd ? ` ~ ${job.windowEnd.slice(0, 10)}` : ' ~ 进行中'}
                      </span>
                      <span className="block truncate text-xs text-muted-foreground">
                        成功 {job.succeededTaskCount}/{job.expectedTaskCount}
                      </span>
                    </span>
                    <Badge variant={meta.variant}>{meta.label}</Badge>
                  </button>
                );
              })
              : null}
```

（加载/错误/空状态块不变；空状态文案「该项目还没有采集任务，暂无看板数据。」保留。）

- [x] **Step 4: 运行测试与构建**

Run: `npm --prefix web test` → 全绿（约 141 pass）。
Run: `npm --prefix web run build` → 成功。

- [x] **Step 5: ⚠️ blob 构造提交**

两文件 DIRTY。每个文件：提交 blob = `git show HEAD:<file>`（含上一阶段看板 Sheet）+ 仅本任务改动，适配 HEAD 上下文（HEAD 版若与工作区在途版结构不同，以 HEAD 为基底叠加本任务改动；不得引用 HEAD 不存在且非本任务新增的标识符）。`git hash-object -w --no-filters` → `git update-index --cacheinfo`。

提交版自洽验证：
- 提交版 jsx **不得**再出现 `fetchQueryJobStatus`、`normalizeProjectJobRecords`、`getQueryJobStatusMeta`；**必须**出现 `fetchProjectCollectionJobs`、`normalizeProjectCollectionJobs`、`getCollectionJobStatusMeta`、`sourceJobId`、`buildProjectDashboardPath`。
- 契约 7 条 regex 命中提交版。
- esbuild 语法校验提交版 jsx；临时 worktree 检出提交后 `node --test <wt>/web/src/components/projects/__tests__/projectDetailPage.test.js`（删 worktree 前先 cd 回主仓）。

```powershell
git commit -m @'
feat: 项目详情页看板 Sheet 改用 collection_jobs 数据源

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

提交后核对：`git show --stat HEAD` 恰好 2 文件；`git diff HEAD -- <两文件>` 残留仅在途 hunk；工作区 `npm --prefix web test` 与 build 仍绿。

---

### Task 4: 删死代码 + 全量门禁 + 文档收尾

**Files:**
- Modify: `web/src/components/projects/projectPresentation.js`（删 `normalizeProjectJobRecords`）
- Modify: `web/src/components/projects/__tests__/projectPresentation.test.js`（删其 2 个单测）
- Create: `docs/changelog/20260611-040000-project-dashboard-entry-collection-jobs.md`
- Modify: `docs/product-specs/20260611-010000-project-dashboard-entry-collection-jobs.md`（状态行）
- Move: `docs/exec-plans/active/20260611-project-dashboard-entry-collection-jobs.md` → `completed/`
- Modify: `docs/exec-plans/active/index.md`（恢复空态，提交）

- [x] **Step 1: 删死代码**

先确认无人再引用：`grep -rn "normalizeProjectJobRecords" web/src` 应只剩 `projectPresentation.js`（定义）与 `projectPresentation.test.js`（测试）——ProjectDetailPage 已在 Task 3 改掉。若仍有其它引用，停下排查。

- 从 `web/src/components/projects/projectPresentation.js` 删除 `normalizeProjectJobRecords` 函数定义。
- 从 `web/src/components/projects/__tests__/projectPresentation.test.js` 删除其顶部 import 中的 `normalizeProjectJobRecords`，以及两个相关测试（`normalizeProjectJobRecords maps backend job rows to camelCase`、`normalizeProjectJobRecords returns empty array for missing jobs`）。

- [x] **Step 2: 运行全部门禁**

```powershell
uv run --project api ruff check api
$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q
npm --prefix web test
npm --prefix web run build
python scripts/validate_agents_docs.py --level ERROR
```

Expected: ruff 通过；后端约 226 passed；前端约 139 pass（141 - 删的 2）；构建成功；文档 0 错误。失败先排查；本功能问题修复，他人在途问题报告 BLOCKED。

- [x] **Step 3: changelog**

创建 `docs/changelog/20260611-040000-project-dashboard-entry-collection-jobs.md`：

```markdown
# 项目看板入口改用 collection_jobs 数据源

## 变更

- 新增 `GET /api/v1/projects/{project_id}/collection-jobs`：按 `tenant_key + project_id` 列出该项目的采集任务（仅 `source_job_id` 非空），按时间窗倒序，并返回项目目标品牌（`project_brands.role='target'`）。
- 项目详情页「进入看板」Sheet 改源：从 `llm_query_jobs`（每条查询一行、导致重复项）改为 `collection_jobs`（一次采集一行）；每行展示状态、采集时间窗、成功/期望任务数；选择后经 `source_job_id` + 目标品牌进 legacy 首页看板。
- 前端新增 `fetchProjectCollectionJobs` 适配器、`normalizeProjectCollectionJobs` 与 `getCollectionJobStatusMeta`。
- 删除改源后变死代码的 `normalizeProjectJobRecords` 及其单测。

## 边界

- 不展示 `source_job_id` 为空的采集任务；不改 legacy 看板页与授权模型。
- 保留上一阶段 `/query-jobs/status?project_id` 过滤参数（向后兼容，未回滚）。

## 验证

- `uv run --project api ruff check api`
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`
- `npm --prefix web test`
- `npm --prefix web run build`
- `python scripts/validate_agents_docs.py --level ERROR`
```

按 Step 2 真实结果核对验证小节。

- [x] **Step 4: 规格状态 + 归档**

1. `docs/product-specs/20260611-010000-project-dashboard-entry-collection-jobs.md` 第 3 行 `状态：待实现` → `状态：已实现`。
2. 本计划所有 `- [x]` → `- [x]`（`sed -i 's/- \[ \]/- [x]/g'`）。
3. `git mv docs/exec-plans/active/20260611-project-dashboard-entry-collection-jobs.md docs/exec-plans/completed/20260611-project-dashboard-entry-collection-jobs.md`，随后 `git add` 该 completed 路径（确保勾选后内容入暂存，避免 git mv 暂存旧 blob）。核对 `git show :docs/exec-plans/completed/20260611-project-dashboard-entry-collection-jobs.md | grep -c '\- \[ \]'` 步骤列表为 0。
4. `docs/exec-plans/active/index.md`（clean）→ 恢复 `# Active ExecPlans\n\n当前无进行中的 ExecPlan。`，一并提交。
5. `docs/exec-plans/completed/index.md`（DIRTY 带在途行）：表头后插入 `| [20260611-project-dashboard-entry-collection-jobs.md](20260611-project-dashboard-entry-collection-jobs.md) | 项目看板入口改用 collection_jobs 数据源（一次采集一行，经 source_job_id 进 legacy 看板） | 2026-06-11 |`——**只改工作区，不提交**。

- [x] **Step 5: 复跑文档验证**

Run: `python scripts/validate_agents_docs.py --level ERROR` → 0 错误。

- [x] **Step 6: Commit**（不含 completed/index.md）

```powershell
git add web/src/components/projects/projectPresentation.js web/src/components/projects/__tests__/projectPresentation.test.js docs/changelog/20260611-040000-project-dashboard-entry-collection-jobs.md docs/product-specs/20260611-010000-project-dashboard-entry-collection-jobs.md docs/exec-plans/active/20260611-project-dashboard-entry-collection-jobs.md docs/exec-plans/completed/20260611-project-dashboard-entry-collection-jobs.md docs/exec-plans/active/index.md
git commit -m @'
refactor: 删除死代码 normalizeProjectJobRecords 并完成看板改源文档收尾

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

提交后核对：commit 含 projectPresentation.js/test（删函数+删测试）、changelog（A）、spec（M）、计划 rename（R）、active/index.md（M）；**不含** completed/index.md。

---

## 验收对照（Spec → Task）

| Spec 要求 | 覆盖 Task |
|---|---|
| 目标 2：新接口 collection-jobs（source_job_id 过滤） | Task 1 |
| 目标 4：目标品牌解析 | Task 1（test_target_brand_null_when_absent + 主用例断言 QuickCEP） |
| 目标 1/3/5：Sheet 改源、一次采集一行、经 source_job_id + 品牌进看板、展示状态/时间窗/任务数 | Task 2（数据层）+ Task 3（页面） |
| 目标 6：无可进看板任务空状态 | Task 3（契约含「该项目还没有采集任务」） |
| API 5.1：按时间窗倒序、租户隔离、鉴权 | Task 1（排序/隔离/401 用例） |
| 死代码清理 normalizeProjectJobRecords | Task 4 |
| 验收门禁 | Task 1 Step 8、Task 3 Step 4、Task 4 Step 2 |
