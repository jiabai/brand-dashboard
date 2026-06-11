# 问答快照 Markdown 浮窗 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline) 或 superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 问答快照页问题/回答列可点击，弹出居中模态浮窗，用 Markdown 渲染该行问题与回答全文。

**Architecture:** 新增居中 Dialog 基元（复用 `radix-ui` Dialog，与 `ui/sheet.jsx` 同源）+ 可复用 `MarkdownContent`（react-markdown + remark-gfm，组件映射自包含样式，不渲染原始 HTML）；`AnswerSnapshotsPage` 把两列预览改为可聚焦按钮并以 `activeRecord` state 驱动浮窗。后端零改动。

**Tech Stack:** React 18、vite、radix-ui Dialog、react-markdown、remark-gfm、Tailwind v4、`node --test`（源码契约风格，无 jsdom）。

设计文档：`docs/design-docs/20260612-answer-snapshot-markdown-dialog.md`

---

## File Structure

- Create `web/src/components/ui/dialog.jsx` — 居中模态 Dialog 基元（镜像 `ui/sheet.jsx`）。
- Create `web/src/components/MarkdownContent.jsx` — Markdown 渲染组件（react-markdown + remark-gfm + 组件映射）。
- Create `web/src/components/__tests__/markdownContent.test.js` — MarkdownContent 安全/能力源码契约。
- Modify `web/src/components/AnswerSnapshotsPage.jsx` — 两列预览改按钮 + activeRecord state + Dialog 接线。
- Modify `web/src/components/__tests__/answerSnapshotsPage.test.js` — 扩展浮窗接线契约。
- Modify `web/package.json` / `web/package-lock.json` — 新增 `react-markdown`、`remark-gfm`。

---

### Task 1: 新增依赖

**Files:** Modify `web/package.json`, `web/package-lock.json`

- [ ] **Step 1:** 确认 `package.json` / lock 当前在共享脏分支上为 clean（`git status --short -- web/package.json web/package-lock.json` 无输出），避免与他人在途改动冲突。
- [ ] **Step 2:** `npm --prefix web install react-markdown remark-gfm --legacy-peer-deps`（只装这两个，写入 dependencies）。
- [ ] **Step 3:** `npm --prefix web run build` 验证依赖可解析、构建成功。

---

### Task 2: 居中 Dialog 基元

**Files:** Create `web/src/components/ui/dialog.jsx`

- [ ] **Step 1:** 镜像 `ui/sheet.jsx`：`import { Dialog as DialogPrimitive } from "radix-ui"`，导出 `Dialog / DialogTrigger / DialogPortal / DialogClose / DialogOverlay / DialogContent / DialogHeader / DialogFooter / DialogTitle / DialogDescription`。`DialogOverlay` 半透明遮罩 + `tw-animate-css` 淡入；`DialogContent` 居中（`fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2`）、`max-h-[85vh]`、`flex flex-col`、右上角 `DialogClose`（`XIcon`），主体区滚动交给消费方。样式 token 与 `sheet.jsx` 保持一致（`bg-background`、`border`、`rounded-lg`、`shadow-lg`）。
- [ ] **Step 2:** `npm --prefix web run lint` → 该文件 0 warning。

---

### Task 3: MarkdownContent（先写失败测试）

**Files:** Create `web/src/components/MarkdownContent.jsx`, `web/src/components/__tests__/markdownContent.test.js`

- [ ] **Step 1: 写失败测试**（源码契约，沿用仓库风格：读 `.jsx` 文本断言）

```js
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(resolve(__dirname, '../MarkdownContent.jsx'), 'utf8');

describe('MarkdownContent rendering contract', () => {
  it('uses react-markdown with remark-gfm', () => {
    assert.match(source, /from ['"]react-markdown['"]/);
    assert.match(source, /from ['"]remark-gfm['"]/);
    assert.match(source, /remarkPlugins=\{\[remarkGfm\]\}/);
  });

  it('does NOT enable raw HTML rendering (no rehype-raw)', () => {
    assert.doesNotMatch(source, /rehype-raw/);
    assert.doesNotMatch(source, /dangerouslySetInnerHTML/);
  });

  it('opens links safely in a new tab', () => {
    assert.match(source, /rel=['"]noreferrer['"]/);
    assert.match(source, /target=['"]_blank['"]/);
  });
});
```

- [ ] **Step 2:** Run `npm --prefix web test` → 期望该套 FAIL（文件不存在）。
- [ ] **Step 3: 写实现** — `MarkdownContent({ content })`：`<ReactMarkdown remarkPlugins={[remarkGfm]} components={{...}}>{content || ''}</ReactMarkdown>`；`components` 把 `h1/h2/h3 p ul ol li code pre table thead tbody tr th td blockquote a img hr` 映射为带 Tailwind 类的元素；`a` 固定 `target="_blank" rel="noreferrer"`；不引入 `rehype-raw`。外层 `div.space-y-3.text-sm.leading-relaxed.break-words`。
- [ ] **Step 4:** Run `npm --prefix web test` → 期望该套 PASS。

---

### Task 4: AnswerSnapshotsPage 接线（先扩展契约测试）

**Files:** Modify `web/src/components/AnswerSnapshotsPage.jsx`, `web/src/components/__tests__/answerSnapshotsPage.test.js`

- [ ] **Step 1: 扩展失败测试** —在既有 `answerSnapshotsPage.test.js` 追加：

```js
describe('AnswerSnapshotsPage detail dialog contract', () => {
  it('wires the markdown dialog', () => {
    assert.match(source, /from '\.\/ui\/dialog\.jsx'/);
    assert.match(source, /from '\.\/MarkdownContent\.jsx'/);
    assert.match(source, /<MarkdownContent/);
  });
  it('makes prompt and answer previews clickable buttons', () => {
    // 预览可点击：以 button + onClick 打开浮窗
    assert.match(source, /activeRecord/);
    assert.match(source, /<button/);
  });
});
```

- [ ] **Step 2:** Run `npm --prefix web test` → 期望新套 FAIL。
- [ ] **Step 3: 实现接线** —
  - import `Dialog, DialogContent, DialogHeader, DialogTitle` 等与 `MarkdownContent`。
  - 新增 `const [activeRecord, setActiveRecord] = useState(null);`。
  - 把 `AnswerText` 预览包成 `<button type="button" onClick={() => setActiveRecord(record)} className="...text-left hover:... cursor-pointer">`（保留截断预览 + 小「展开」提示），桌面 `columns` 的 query/answer 列与 `MobileAnswerSnapshotList` 卡片同改（给 `MobileAnswerSnapshotList` 传 `onOpen`）。
  - 页面底部渲染受控 `<Dialog open={Boolean(activeRecord)} onOpenChange={(open) => !open && setActiveRecord(null)}>`：头部展示 `dateLabel · platform · brand · keyword` + 情绪/引用徽章；主体 `overflow-y-auto`，依次 `问题` → `<MarkdownContent content={activeRecord?.queryContent} />`、`回答` → `<MarkdownContent content={activeRecord?.answerContent} />`。
- [ ] **Step 4:** Run `npm --prefix web test` → 全绿（含既有 142 例）。

---

### Task 5: 门禁与收尾

- [ ] **Step 1:** `npm --prefix web test` → 全绿。
- [ ] **Step 2:** `npm --prefix web run lint` → 改动文件 0 warning。
- [ ] **Step 3:** `npm --prefix web run build` → 成功。
- [ ] **Step 4:** 写 changelog `docs/changelog/20260612-HHMMSS-answer-snapshot-markdown-dialog.md`（变更/边界/验证/后续）；本计划由 `active/` 移入 `completed/` 并更新两个 `index.md`。
- [ ] **Step 5: 提交（共享脏分支暂存纪律：只 `git add` 本任务文件，禁 `git add -A`）** — 一次 feat 提交含：`web/package.json`、`web/package-lock.json`、`ui/dialog.jsx`、`MarkdownContent.jsx`、`AnswerSnapshotsPage.jsx`、两个测试文件；docs 收尾（changelog + plan 归档 + index）可单独一次 docs 提交。Conventional Commits（中文）。

---

## Self-Review

- **Spec coverage:** 居中 Dialog（Task 2）✓；react-markdown+gfm（Task 3）✓；两列点击+移动端一致（Task 4）✓；安全不渲染原始 HTML（Task 3 测试）✓；纯前端不动取数（全程未触 api/utils）✓。
- **Placeholder scan:** 各步均有具体命令/测试代码/接线点，无 TBD。组件 Tailwind 类细节按设计文档「样式意图」在实现时落定，非占位。
- **Type/命名一致:** `activeRecord` / `setActiveRecord`、`MarkdownContent`、`content` prop、`ui/dialog.jsx` 导出名贯穿 Task 3/4 一致。
