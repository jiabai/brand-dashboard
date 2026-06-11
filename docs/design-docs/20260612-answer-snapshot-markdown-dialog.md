# 问答快照「点击查看全文」Markdown 浮窗

> 状态：设计中，2026-06-12
>
> 关联：分析二级导航 `docs/design-docs/20260611-tenant-analysis-navigation.md`；目标页 `web/src/components/AnswerSnapshotsPage.jsx`；表格渲染 `web/src/components/DataTable.jsx`；现有弹层基元 `web/src/components/ui/sheet.jsx`（与本设计的 Dialog 同基于 `radix-ui` 的 Dialog primitive）。

## 背景

问答快照页「原始回答列表」用 `DataTable` 展示，问题(Prompt)列与回答(Answer)列均由页内 `AnswerText` 渲染，正文 `max-h-24 overflow-hidden` 截断，长回答看不全；移动端列表 `MobileAnswerSnapshotList` 同样截断。回答内容实为 Markdown 文本，当前以纯文本截断呈现——既读不全，也不解析格式。

## 需求

- 点击回答列（及问题列）单元格，弹出**居中模态浮窗**展示该行全文。
- 浮窗内容按 **Markdown 解析渲染**（标题/列表/表格/代码/引用/链接）。
- 桌面表格与移动端列表行为一致。
- 纯前端改动，不动后端取数与 `normalizeAnswerSnapshots` 规范化。

## 决策

**浮窗形式：居中模态 Dialog。** 最贴合「浮窗」语义、适合阅读长文与滚动。`ui/` 现有 `sheet.jsx`（右侧抽屉）、`popover.jsx`（锚定气泡）均基于 `radix-ui` 的 `Dialog`；新增一个**居中** Dialog 基元复用同一 primitive，零新依赖、与既有风格一致。不选 Sheet（偏侧栏、非居中浮窗）、不选 Popover（长文空间局促）。

**Markdown 库：`react-markdown` + `remark-gfm`。** React 原生组件、默认不渲染原始 HTML（不挂 `rehype-raw`）→ 回答内若含 HTML 以纯文本呈现，天然 XSS 安全；`remark-gfm` 支持表格/任务列表/删除线。不选 `marked` + `DOMPurify`（需手动消毒、易错）。属新增依赖，需一次 `npm install`，会更新 `package.json` 与 `package-lock.json`。

**展示范围：问题(Prompt) + 回答(Answer) 两列。** 两列内容同构、同样截断，复用同一交互；浮窗内同时渲染「问题」「回答」两段（读问题再读回答更连贯），满足「点回答看回答」。

## 组件与接线（全前端）

1. **新增 `web/src/components/ui/dialog.jsx`**：镜像 `ui/sheet.jsx`，`import { Dialog as DialogPrimitive } from "radix-ui"`，导出 `Dialog / DialogTrigger / DialogPortal / DialogOverlay / DialogContent / DialogHeader / DialogFooter / DialogTitle / DialogDescription / DialogClose`。`DialogContent` 居中（`fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2`）+ 遮罩 + 右上角关闭按钮 + `tw-animate-css` 进出场，最大高度内主体可滚动。
2. **新增 `web/src/components/MarkdownContent.jsx`**：`react-markdown` + `remark-gfm`，用 `components` 映射把 `h1-3 / p / ul / ol / li / code / pre / table / thead / th / td / blockquote / a / img / hr` 套上 Tailwind 类（无需 `@tailwindcss/typography` 插件，自包含可复用）；`a` 加 `target="_blank" rel="noreferrer"`；不启用原始 HTML。
3. **改 `web/src/components/AnswerSnapshotsPage.jsx`**：
   - 问题/回答列预览（`AnswerText`）改为**可聚焦按钮**（键盘可达），保留截断预览，加 `cursor-pointer` + hover 态 + 小「展开」提示；桌面列与移动端卡片同改。
   - 新增 `activeRecord` state；点击任一行问题/回答 → 打开 Dialog。
   - Dialog 头部展示该行上下文（日期 · 平台 · 品牌 · 关键词 + 情绪/引用徽章），主体可滚动，依次渲染「问题」「回答」两段 `MarkdownContent`。

## 数据流

数据仍由现有 `fetchAnswerSnapshots` + `normalizeAnswerSnapshots` 提供（`record.queryContent` / `record.answerContent`）。浮窗只读已加载的行数据，不发新请求。后端零改动。

## 安全

react-markdown 默认不解析原始 HTML（不引入 `rehype-raw`），回答中的 `<script>` / HTML 以纯文本展示，无 XSS 面；外链 `rel="noreferrer"`。

## 测试边界（沿用仓库 `node --test` 源码契约风格，无 jsdom）

- 扩展 `web/src/components/__tests__/answerSnapshotsPage.test.js`：断言页面接入 `Dialog` 与 `MarkdownContent`、问题/回答两列均挂可点击触发、移动端列表同样可点。
- 新增 `web/src/components/__tests__/markdownContent.test.js`：断言 `MarkdownContent` 使用 `remark-gfm`、未启用原始 HTML（安全契约）、外链带 `rel`。

## 范围外（YAGNI）

- 不做复制到剪贴板、分段折叠。
- 代码块不做语法高亮（纯样式 `pre`，将来可加）。
- 不引入 `@tailwindcss/typography`（用组件映射自包含样式）。
