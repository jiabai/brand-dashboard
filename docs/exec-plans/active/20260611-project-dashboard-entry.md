# 项目详情页进入看板入口实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 租户用户在项目详情页点击「进入看板」，从该项目的 job 记录中选一条，跳转到 legacy 首页看板。

**Architecture:** 后端给已有的 `GET /api/v1/query-jobs/status` 加可选 `project_id` 过滤（仓储 + 路由，向后兼容、授权不变）；前端 query-jobs 适配器透传 `project_id`，项目展示层新增「job 记录归一化」与「看板路径构造」纯函数；项目详情页加「进入看板」按钮 + 右侧 Sheet 列出 job 供选择并跳转。

**Tech Stack:** FastAPI + SQLAlchemy text SQL、pytest（内存 SQLite + TestClient）、React 18 + shadcn/ui（Sheet）、node:test 源码契约测试。

**Spec:** `docs/product-specs/20260611-project-dashboard-entry.md`

**约定与上下文（执行者必读）：**

- 门禁命令（PowerShell，仓库根目录）：
  - 后端单文件：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_query_jobs_project_link.py -q`
  - 后端全量：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`（当前基线 220 passed）
  - 后端 lint：`uv run --project api ruff check api`
  - 前端测试：`npm --prefix web test`（当前基线 129 pass）；构建：`npm --prefix web run build`
  - 文档验证：`python scripts/validate_agents_docs.py --level ERROR`
- **暂存纪律**：工作区有他人未提交在途改动。每次 commit **只 `git add` 任务点名的文件，严禁 `git add -A` / `git add .`**。
  - 本计划中 **clean（可正常 `git add`）**：`api/v1/repositories/query_jobs.py`、`api/v1/routes/query_jobs.py`、`api/tests/test_query_jobs_project_link.py`、`web/src/api/queryJobs.js`、`web/src/api/__tests__/queryJobs.test.js`（新建）、`web/src/components/projects/projectPresentation.js`、`web/src/components/projects/__tests__/projectPresentation.test.js`。
  - **DIRTY（带他人在途改动，必须 blob 构造提交）**：`web/src/components/projects/ProjectDetailPage.jsx`、`web/src/components/projects/__tests__/projectDetailPage.test.js`。
  - 动手每个任务前先 `git status --porcelain -- <file>` 复核；若 clean 文件意外变 dirty，或 dirty 文件意外变 clean，按实际情况调整（dirty 用 blob 构造：`git show HEAD:<file>` + 仅本任务增量 → `git hash-object -w --no-filters` → `git update-index --cacheinfo 100644,<hash>,<path>`；提交后用临时 worktree 或 `git show <commit>:<file>` 验证自洽，删 worktree 前先 cd 回主仓）。
- 授权事实（已核实）：`GET /query-jobs/status` 由 `get_current_tenant` 守卫（active 成员 + active 租户，任意角色；admin 必过），数据按 `tenant_key` 隔离。本计划不改授权模型。

---

### Task 1: 后端 —— `GET /query-jobs/status` 增加 `project_id` 过滤

**Files（均 clean，正常 add）:**
- Modify: `api/v1/repositories/query_jobs.py`（`list_query_jobs_status`）
- Modify: `api/v1/routes/query_jobs.py`（`list_query_jobs_status` 路由）
- Modify: `api/tests/test_query_jobs_project_link.py`（追加两个测试）

- [ ] **Step 1: 追加失败的测试**

先 Read `api/tests/test_query_jobs_project_link.py` 顶部，确认已有 fixture `query_job_project_session`、`_client`、`_token`、`_seed_admin_and_project`、以及 `text` 已导入（均已存在）。在文件末尾追加：

```python
def _insert_job(session, *, project_id, job_id, brand):
    now = datetime.now(UTC)
    session.execute(
        text(
            """
            INSERT INTO llm_query_jobs (
                tenant_key, job_id, project_id, category, brand, keyword,
                query_content, query_status, effective_from, created_at, is_deleted
            ) VALUES (
                'tn_allowed', :job_id, :project_id, 'cat', :brand, 'kw',
                'q', 1, :now, :now, 0
            )
            """
        ),
        {"job_id": job_id, "project_id": project_id, "brand": brand, "now": now},
    )


def test_status_filters_jobs_by_project_id(query_job_project_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _seed_admin_and_project(query_job_project_session, project_id="proj_active")
    now = datetime.now(UTC)
    query_job_project_session.execute(
        text(
            """
            INSERT INTO monitoring_projects (
              tenant_key, project_id, name, industry, category, status,
              created_by, created_at, updated_at
            )
            VALUES ('tn_allowed', 'proj_other', 'Other', 'auto', 'ev', 'active', 101, :now, :now)
            """
        ),
        {"now": now},
    )
    _insert_job(query_job_project_session, project_id="proj_active", job_id="job_a", brand="BrandA")
    _insert_job(query_job_project_session, project_id="proj_other", job_id="job_b", brand="BrandB")
    query_job_project_session.commit()

    client = _client(query_job_project_session)
    resp = client.get(
        "/api/v1/query-jobs/status",
        params={"tenant_key": "tn_allowed", "project_id": "proj_active"},
        headers={"Authorization": f"Bearer {_token()}"},
    )

    assert resp.status_code == 200
    jobs = resp.json()["jobs"]
    assert {j["job_id"] for j in jobs} == {"job_a"}
    assert all(j["project_id"] == "proj_active" for j in jobs)


def test_status_without_project_id_returns_all_tenant_jobs(query_job_project_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _seed_admin_and_project(query_job_project_session, project_id="proj_active")
    now = datetime.now(UTC)
    query_job_project_session.execute(
        text(
            """
            INSERT INTO monitoring_projects (
              tenant_key, project_id, name, industry, category, status,
              created_by, created_at, updated_at
            )
            VALUES ('tn_allowed', 'proj_other', 'Other', 'auto', 'ev', 'active', 101, :now, :now)
            """
        ),
        {"now": now},
    )
    _insert_job(query_job_project_session, project_id="proj_active", job_id="job_a", brand="BrandA")
    _insert_job(query_job_project_session, project_id="proj_other", job_id="job_b", brand="BrandB")
    query_job_project_session.commit()

    client = _client(query_job_project_session)
    resp = client.get(
        "/api/v1/query-jobs/status",
        params={"tenant_key": "tn_allowed"},
        headers={"Authorization": f"Bearer {_token()}"},
    )

    assert resp.status_code == 200
    assert {j["job_id"] for j in resp.json()["jobs"]} == {"job_a", "job_b"}
```

- [ ] **Step 2: 运行测试确认失败**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_query_jobs_project_link.py -q`
Expected: `test_status_filters_jobs_by_project_id` FAIL（未过滤，返回了 job_a 和 job_b），另一个可能已 PASS。

- [ ] **Step 3: 实现仓储过滤**

`api/v1/repositories/query_jobs.py` 的 `list_query_jobs_status`：函数签名加 `project_id` 参数，并在 `job_id` 子句之后加过滤。修改后函数头与 where 组装为：

```python
def list_query_jobs_status(
    db: Session,
    *,
    tenant_key: str,
    job_id: Optional[str] = None,
    project_id: Optional[str] = None,
    include_deleted: bool = False,
):
    params: Dict[str, Any] = {"tenant_key": tenant_key}
    where_clauses = ["tenant_key = :tenant_key"]

    if job_id is not None:
        where_clauses.append("job_id = :job_id")
        params["job_id"] = job_id

    if project_id is not None:
        where_clauses.append("project_id = :project_id")
        params["project_id"] = project_id

    if not include_deleted:
        where_clauses.append("is_deleted = 0")
```

（其后的 SELECT/ORDER BY/return 保持不变。）

- [ ] **Step 4: 实现路由透传**

`api/v1/routes/query_jobs.py` 的 `list_query_jobs_status` 路由（约第 217 行）：在 `job_id` 参数之后加 `project_id` 查询参数，并规范化后传入仓储。

签名加参数（放在 `job_id` 之后、`include_deleted` 之前）：

```python
    project_id: Optional[str] = Query(None, description="可选：仅查询指定项目的任务"),
```

函数体内，在现有 `normalized_job_id` 规范化之后、调用仓储之前加：

```python
    normalized_project_id = project_id.strip() if project_id else None
    if not normalized_project_id:
        normalized_project_id = None
```

并把仓储调用改为传入 `project_id=normalized_project_id`：

```python
    rows = list_query_jobs_status_records(
        db,
        tenant_key=tenant_key,
        job_id=normalized_job_id,
        project_id=normalized_project_id,
        include_deleted=include_deleted,
    )
```

- [ ] **Step 5: 运行测试确认通过**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_query_jobs_project_link.py -q`
Expected: 全部通过（原有用例 + 新增 2 个）。

- [ ] **Step 6: 后端回归与 lint**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` → 约 222 passed，0 失败。
Run: `uv run --project api ruff check api` → All checks passed!

- [ ] **Step 7: Commit**（三文件均 clean）

```powershell
git add api/v1/repositories/query_jobs.py api/v1/routes/query_jobs.py api/tests/test_query_jobs_project_link.py
git commit -m @'
feat: query-jobs 状态接口支持按 project_id 过滤

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

（PowerShell here-string 结束标记 `'@` 顶格独占一行。）

---

### Task 2: 前端数据层 —— 适配器透传 + 展示层纯函数

**Files（均 clean，正常 add）:**
- Modify: `web/src/api/queryJobs.js`
- Create: `web/src/api/__tests__/queryJobs.test.js`
- Modify: `web/src/components/projects/projectPresentation.js`
- Modify: `web/src/components/projects/__tests__/projectPresentation.test.js`

- [ ] **Step 1: 写失败的测试**

创建 `web/src/api/__tests__/queryJobs.test.js`：

```js
import test from 'node:test';
import assert from 'node:assert/strict';

import { fetchQueryJobStatus } from '../queryJobs.js';

const jsonResponse = (payload) => ({
  ok: true,
  status: 200,
  json: async () => payload,
  text: async () => JSON.stringify(payload),
});

test.afterEach(() => {
  delete globalThis.fetch;
});

test('fetchQueryJobStatus serializes project_id when provided', async () => {
  let requestedUrl;
  globalThis.fetch = async (url) => {
    requestedUrl = url;
    return jsonResponse({ success: true, count: 0, jobs: [] });
  };

  await fetchQueryJobStatus({ tenantKey: 'tn_demo', projectId: 'proj_a' });

  const parsed = new URL(requestedUrl, 'http://localhost');
  assert.equal(parsed.pathname, '/api/v1/query-jobs/status');
  assert.equal(parsed.searchParams.get('tenant_key'), 'tn_demo');
  assert.equal(parsed.searchParams.get('project_id'), 'proj_a');
});

test('fetchQueryJobStatus omits project_id when not provided', async () => {
  let requestedUrl;
  globalThis.fetch = async (url) => {
    requestedUrl = url;
    return jsonResponse({ success: true, count: 0, jobs: [] });
  };

  await fetchQueryJobStatus({ tenantKey: 'tn_demo' });

  const parsed = new URL(requestedUrl, 'http://localhost');
  assert.equal(parsed.searchParams.get('project_id'), null);
});
```

在 `web/src/components/projects/__tests__/projectPresentation.test.js` 末尾追加（先 Read 该文件确认其 import 风格与 `import { ... } from '../projectPresentation.js'`，把两个新名字加入该 import；测试风格沿用文件现有 node:test 写法）：

```js
test('normalizeProjectJobRecords maps backend job rows to camelCase', () => {
  const result = normalizeProjectJobRecords({
    jobs: [
      {
        job_id: 'job_a',
        project_id: 'proj_a',
        brand: 'BrandA',
        query_status: 1,
        effective_from: '2026-02-09T12:35:50Z',
        effective_to: null,
      },
    ],
  });
  assert.equal(result.length, 1);
  assert.equal(result[0].jobId, 'job_a');
  assert.equal(result[0].brand, 'BrandA');
  assert.equal(result[0].queryStatus, 1);
});

test('normalizeProjectJobRecords returns empty array for missing jobs', () => {
  assert.deepEqual(normalizeProjectJobRecords(null), []);
  assert.deepEqual(normalizeProjectJobRecords({}), []);
});

test('buildProjectDashboardPath builds legacy home dashboard path with brand', () => {
  assert.equal(
    buildProjectDashboardPath({ tenantKey: 'tn_demo', jobId: 'job_a', brand: 'BrandA' }),
    '/dashboard/tn_demo/job_a?brand=BrandA',
  );
});

test('buildProjectDashboardPath omits brand when empty and returns empty when missing ids', () => {
  assert.equal(buildProjectDashboardPath({ tenantKey: 'tn_demo', jobId: 'job_a' }), '/dashboard/tn_demo/job_a');
  assert.equal(buildProjectDashboardPath({ tenantKey: '', jobId: 'job_a' }), '');
  assert.equal(buildProjectDashboardPath({ tenantKey: 'tn_demo', jobId: '' }), '');
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm --prefix web test`
Expected: 新增用例 FAIL（`fetchQueryJobStatus` 未透传 project_id；`normalizeProjectJobRecords`/`buildProjectDashboardPath` 未导出）。

- [ ] **Step 3: 实现适配器透传**

`web/src/api/queryJobs.js` 的 `fetchQueryJobStatus` 改为：

```js
export const fetchQueryJobStatus = ({ tenantKey, jobId, projectId, includeDeleted = false }, options) => {
  const params = buildQueryString({
    tenant_key: tenantKey,
    job_id: jobId || undefined,
    project_id: projectId || undefined,
    include_deleted: includeDeleted ? 'true' : 'false',
  });
  return fetch(`/api/v1/query-jobs/status?${params}`, options);
};
```

- [ ] **Step 4: 实现展示层纯函数**

`web/src/components/projects/projectPresentation.js` 末尾追加（文件顶部已有 `encodePathSegment`，无需新增 import）：

```js
export const normalizeProjectJobRecords = (response) => {
  const jobs = Array.isArray(response?.jobs) ? response.jobs : [];
  return jobs.map((job) => ({
    jobId: job.job_id || '',
    projectId: job.project_id || '',
    brand: job.brand || '',
    queryStatus: job.query_status,
    effectiveFrom: job.effective_from || '',
    effectiveTo: job.effective_to || '',
  }));
};

export const buildProjectDashboardPath = ({ tenantKey, jobId, brand } = {}) => {
  const tk = encodePathSegment(tenantKey);
  const jid = encodePathSegment(jobId);
  if (!tk || !jid) return '';
  const path = `/dashboard/${tk}/${jid}`;
  const normalizedBrand = String(brand || '').trim();
  if (!normalizedBrand) return path;
  const params = new URLSearchParams({ brand: normalizedBrand });
  return `${path}?${params.toString()}`;
};
```

- [ ] **Step 5: 运行测试确认通过**

Run: `npm --prefix web test`
Expected: 全部通过（基线 129 + 新增 5 = 134 pass 左右）。

- [ ] **Step 6: Commit**（四文件均 clean）

```powershell
git add web/src/api/queryJobs.js web/src/api/__tests__/queryJobs.test.js web/src/components/projects/projectPresentation.js web/src/components/projects/__tests__/projectPresentation.test.js
git commit -m @'
feat: 前端 query-jobs 适配器透传 project_id 并新增项目看板路径与 job 归一化

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

---

### Task 3: 项目详情页「进入看板」按钮 + Sheet 选 job（⚠️ DIRTY，blob 构造）

**Files（均 DIRTY，提交 blob = `git show HEAD:<file>` + 仅本任务增量）:**
- Modify: `web/src/components/projects/ProjectDetailPage.jsx`
- Modify: `web/src/components/projects/__tests__/projectDetailPage.test.js`

前置：Task 2 已入库，所以提交树里 `web/src/components/projects/projectPresentation.js` 已含 `normalizeProjectJobRecords`/`buildProjectDashboardPath`，`web/src/api/queryJobs.js` 已透传 projectId；`getQueryJobStatusMeta` 在 `web/src/components/platform/tenantPresentation.js` 自始已有。本任务提交版引用这些标识符都成立。

- [ ] **Step 1: 写失败的契约测试**

`web/src/components/projects/__tests__/projectDetailPage.test.js` 末尾追加（先 Read 该文件确认它用 `source` 变量读取 `../ProjectDetailPage.jsx` 源码、describe/it 风格；沿用现有变量名）：

```js
describe('ProjectDetailPage dashboard entry contract', () => {
  it('exposes an enter-dashboard button that opens a job picker sheet', () => {
    assert.match(source, /进入看板/);
    assert.match(source, /fetchQueryJobStatus/);
    assert.match(source, /projectId/);
    assert.match(source, /normalizeProjectJobRecords/);
    assert.match(source, /SheetContent/);
  });

  it('navigates to the legacy dashboard for the selected job', () => {
    assert.match(source, /buildProjectDashboardPath/);
    assert.match(source, /getQueryJobStatusMeta/);
    assert.match(source, /该项目还没有采集任务/);
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm --prefix web test`
Expected: 上述 2 个契约用例 FAIL（regex 不匹配）。

- [ ] **Step 3: 实现页面改动（工作区版本）**

`web/src/components/projects/ProjectDetailPage.jsx` 改动：

(a) lucide 导入（现为 `import { ArrowLeft, Boxes, FileQuestion, FolderKanban, Gauge, RefreshCw } from 'lucide-react';`）按字母序加入 `BarChart3`：

```jsx
import { ArrowLeft, BarChart3, Boxes, FileQuestion, FolderKanban, Gauge, RefreshCw } from 'lucide-react';
```

(b) API 导入（现为 `import { fetchProjectDetail } from '@/api';`）加入 `fetchQueryJobStatus`：

```jsx
import { fetchProjectDetail, fetchQueryJobStatus } from '@/api';
```

(c) 新增 Sheet 组件导入（放在 Separator 导入之后）：

```jsx
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '../ui/sheet.jsx';
```

(d) 复用平台展示层的状态徽章（在 `import { buildPlatformTenantProjectOverviewPath } from '../platform/tenantPresentation.js';` 改为同时引入 `getQueryJobStatusMeta`）：

```jsx
import {
  buildPlatformTenantProjectOverviewPath,
  getQueryJobStatusMeta,
} from '../platform/tenantPresentation.js';
```

(e) projectPresentation 导入加入两个新函数（并入现有 `from './projectPresentation.js'` 列表，保持字母序）：

```jsx
import {
  PROJECT_NAV_SOURCE_PLATFORM_TENANT_DETAIL,
  buildProjectDashboardPath,
  buildProjectDataQualityPath,
  buildProjectListPath,
  countProjectBrandsByRole,
  getProjectStatusMeta,
  normalizeProjectDetailResponse,
  normalizeProjectJobRecords,
  readProjectNavigationSource,
} from './projectPresentation.js';
```

(f) 组件内（其它 `useState` 之后）新增状态：

```jsx
  const [dashboardSheetOpen, setDashboardSheetOpen] = useState(false);
  const [jobRecords, setJobRecords] = useState([]);
  const [isLoadingJobs, setIsLoadingJobs] = useState(false);
  const [jobsError, setJobsError] = useState('');
```

(g) 在 `openDataQuality` 之后新增 handler：

```jsx
  const openDashboardSheet = async () => {
    setDashboardSheetOpen(true);
    setIsLoadingJobs(true);
    setJobsError('');
    try {
      const response = await fetchQueryJobStatus({ tenantKey, projectId });
      setJobRecords(normalizeProjectJobRecords(response));
    } catch (loadError) {
      setJobRecords([]);
      setJobsError(loadError.message || '加载采集任务失败');
    } finally {
      setIsLoadingJobs(false);
    }
  };

  const enterDashboard = (job) => {
    const path = buildProjectDashboardPath({
      tenantKey,
      jobId: job.jobId,
      brand: job.brand,
    });
    if (path) navigate(path);
  };
```

(h) 在动作区「数据质量」按钮之后、「刷新」按钮之前加入「进入看板」按钮：

```jsx
          <Button type="button" variant="outline" onClick={openDashboardSheet}>
            <BarChart3 data-icon="inline-start" />
            进入看板
          </Button>
```

(i) 在组件返回 JSX 的最外层容器内末尾（最后一个 `</div>` 之前的合适位置，与其它顶层块并列）加入 Sheet：

```jsx
      <Sheet open={dashboardSheetOpen} onOpenChange={setDashboardSheetOpen}>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>选择采集任务进入看板</SheetTitle>
            <SheetDescription>选择该项目的一次采集，进入对应的分析看板。</SheetDescription>
          </SheetHeader>
          <div className="mt-4 grid gap-2">
            {isLoadingJobs ? (
              <div className="h-24 animate-pulse rounded-md border border-border bg-muted/45" />
            ) : null}
            {!isLoadingJobs && jobsError ? (
              <Alert variant="destructive">
                <AlertTitle>加载失败</AlertTitle>
                <AlertDescription>{jobsError}</AlertDescription>
              </Alert>
            ) : null}
            {!isLoadingJobs && !jobsError && jobRecords.length === 0 ? (
              <EmptyState
                icon={BarChart3}
                title="暂无看板数据"
                description="该项目还没有采集任务，暂无看板数据。"
              />
            ) : null}
            {!isLoadingJobs && !jobsError
              ? jobRecords.map((job) => {
                const meta = getQueryJobStatusMeta(job.queryStatus);
                return (
                  <button
                    key={`${job.jobId}-${job.brand}`}
                    type="button"
                    onClick={() => enterDashboard(job)}
                    className="flex items-center justify-between gap-3 rounded-md border border-border px-3 py-2 text-left hover:bg-muted/50"
                  >
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-medium text-foreground">{job.brand || '未命名品牌'}</span>
                      <span className="block truncate text-xs text-muted-foreground">
                        {(job.effectiveFrom || '').slice(0, 10)}
                        {job.effectiveTo ? ` ~ ${job.effectiveTo.slice(0, 10)}` : ' ~ 进行中'}
                      </span>
                    </span>
                    <Badge variant={meta.variant}>{meta.label}</Badge>
                  </button>
                );
              })
              : null}
          </div>
        </SheetContent>
      </Sheet>
```

说明：`Alert/AlertTitle/AlertDescription`、`Badge`、`EmptyState`、`navigate`、`tenantKey`、`projectId` 均为该文件既有标识符。

- [ ] **Step 4: 运行测试与构建确认通过**

Run: `npm --prefix web test` → 全部通过（约 136 pass）。
Run: `npm --prefix web run build` → 构建成功。

- [ ] **Step 5: ⚠️ blob 构造提交**

两文件 DIRTY。对每个文件：提交 blob = `git show HEAD:<file>`（HEAD 此时已含 Task 1/2 提交，但这两个文件 Task 1/2 未碰，故 HEAD 版 = 原始已提交版）+ 仅本任务上述增量，适配 HEAD 上下文（HEAD 版的导入块/动作区/JSX 结构若与工作区在途版不同，以 HEAD 实际内容为基底叠加本任务增量；不得引用 HEAD 中不存在且非本任务新增的标识符）。`git hash-object -w --no-filters` → `git update-index --cacheinfo 100644,<hash>,<path>`。

提交版自洽验证：
- 契约 5 条 regex 必须命中提交版 jsx。
- 临时 worktree 检出提交后 `node --test <worktree>/web/src/components/projects/__tests__/projectDetailPage.test.js`（源码 regex 契约，仅读文件、不需 node_modules）；删 worktree 前先 cd 回主仓。

```powershell
git commit -m @'
feat: 项目详情页新增进入看板入口与 job 选择 Sheet

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

提交后核对：`git show --stat HEAD` 恰好 2 文件；`git diff HEAD -- <两文件>` 残留仅在途 hunk、零本任务行；工作区（在途 + 本任务）完整集成，`npm --prefix web test` 与 build 仍绿。

---

### Task 4: 全量门禁、changelog、计划归档与规格状态

**Files:**
- Create: `docs/changelog/20260611-020000-project-dashboard-entry.md`
- Modify: `docs/product-specs/20260611-project-dashboard-entry.md`（状态行）
- Move: `docs/exec-plans/active/20260611-project-dashboard-entry.md` → `docs/exec-plans/completed/`
- Modify: `docs/exec-plans/active/index.md`（移除本计划行，恢复空态，提交）

- [ ] **Step 1: 运行全部门禁（真实执行并记录）**

```powershell
uv run --project api ruff check api
$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q
npm --prefix web test
npm --prefix web run build
python scripts/validate_agents_docs.py --level ERROR
```

Expected: 全部通过（后端约 222；前端约 136；构建成功；文档 0 错误）。失败先排查：本功能问题修复后重跑；他人在途问题报告 BLOCKED。

- [ ] **Step 2: 规格状态行翻转**

`docs/product-specs/20260611-project-dashboard-entry.md` 第 3 行 `> 状态：待实现，2026-06-11` 改为 `> 状态：已实现，2026-06-11`。

- [ ] **Step 3: 写 changelog**

创建 `docs/changelog/20260611-020000-project-dashboard-entry.md`：

```markdown
# 项目详情页进入看板入口

## 变更

- `GET /api/v1/query-jobs/status` 新增可选 `project_id` 查询参数，按 `tenant_key + project_id` 过滤；不传时行为不变（向后兼容）。授权沿用 `get_current_tenant`。
- 前端 `fetchQueryJobStatus` 透传 `project_id`；项目展示层新增 `normalizeProjectJobRecords` 与 `buildProjectDashboardPath` 纯函数。
- 项目详情页新增「进入看板」按钮，点击打开右侧 Sheet 列出该项目的采集 job（品牌 + 状态徽章 + 生效区间），选择后跳转 legacy 首页看板 `/dashboard/{tenantKey}/{jobId}?brand=`；无 job 显示空状态。

## 边界

- 仅项目详情页入口；用户明确选 job（不自动选最新）；落地仅首页看板。
- 不改看板页与授权模型；复用既有 `llm_query_jobs.project_id` 关联。

## 验证

- `uv run --project api ruff check api`
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`
- `npm --prefix web test`
- `npm --prefix web run build`
- `python scripts/validate_agents_docs.py --level ERROR`
```

按 Step 1 真实结果核对验证小节（附 passed 数量）。

- [ ] **Step 4: 勾选并归档 ExecPlan**

1. 本计划所有 `- [ ]` 勾成 `- [x]`。
2. `git mv docs/exec-plans/active/20260611-project-dashboard-entry.md docs/exec-plans/completed/20260611-project-dashboard-entry.md`，随后 `git add` 该 completed 路径以确保勾选后的内容（而非 HEAD 旧内容）入暂存。
3. `docs/exec-plans/active/index.md`（clean，本计划行随计划文档一起提交过）：删除本计划行、恢复为 `# Active ExecPlans\n\n当前无进行中的 ExecPlan。`，一并提交。
4. `docs/exec-plans/completed/index.md`（DIRTY，带在途行）：表格顶部加行 `| [20260611-project-dashboard-entry.md](20260611-project-dashboard-entry.md) | 项目详情页进入看板入口：用户选 job 进 legacy 首页看板 | 2026-06-11 |`——**只改工作区，不提交**。

- [ ] **Step 5: 复跑文档验证**

Run: `python scripts/validate_agents_docs.py --level ERROR` → 0 错误。

- [ ] **Step 6: Commit**

```powershell
git add docs/changelog/20260611-020000-project-dashboard-entry.md docs/product-specs/20260611-project-dashboard-entry.md docs/exec-plans/active/20260611-project-dashboard-entry.md docs/exec-plans/completed/20260611-project-dashboard-entry.md docs/exec-plans/active/index.md
git commit -m @'
docs: 项目看板入口功能 changelog、规格状态与计划归档

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

提交后核对：commit **不含** `docs/exec-plans/completed/index.md`；含 changelog（A）+ spec（M）+ 计划 rename（R）+ active/index.md（M）。

---

## 验收对照（Spec → Task）

| Spec 要求 | 覆盖 Task |
|---|---|
| 目标 1：项目详情页「进入看板」入口 | Task 3 |
| 目标 2：Sheet 列 job 供用户选 | Task 3 |
| 目标 3：选 job 跳 `/dashboard/{tenantKey}/{jobId}?brand=` | Task 2（buildProjectDashboardPath）、Task 3 |
| 目标 4：按 tenant_key + project_id 过滤 | Task 1 |
| 目标 5：无 job 空状态 | Task 3（契约含「该项目还没有采集任务」） |
| API 行为 5.1（project_id 向后兼容） | Task 1（两个测试：过滤 + 不传返回全部） |
| 安全 7.1（授权不变、租户隔离） | Task 1（get_current_tenant 链路 + tenant_key 过滤，既有保证） |
| 验收门禁 | Task 1 Step 6、Task 3 Step 4、Task 4 Step 1 |
