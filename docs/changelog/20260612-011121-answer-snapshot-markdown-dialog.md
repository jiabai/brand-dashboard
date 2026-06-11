# 问答快照「点击查看全文」Markdown 浮窗

## 变更

- 新增 `web/src/components/ui/dialog.jsx`：居中模态 Dialog 基元，复用 `radix-ui` 的 Dialog primitive（与 `ui/sheet.jsx` 同源），含遮罩、右上角关闭、`max-h-[85vh]` 内主体滚动。
- 新增 `web/src/components/MarkdownContent.jsx`：`react-markdown` + `remark-gfm` 渲染 Markdown，组件映射自带 Tailwind 样式（无需 typography 插件）；不启用原始 HTML（无 rehype-raw），外链 `target=_blank rel=noreferrer`；各 override 只转发所需 props，不外泄内部 `node`。
- `web/src/components/AnswerSnapshotsPage.jsx`：问题/回答两列预览改为可聚焦按钮（保留截断预览 + hover「展开」提示），桌面表格与移动端列表均可点；新增 `activeRecord` state 驱动居中浮窗，头部展示行上下文（日期/平台/品牌/关键词 + 情绪/引用徽章），主体依次以 `MarkdownContent` 渲染「问题」「回答」全文，并复用 `ReferenceList` 展示引用。
- `web/package.json` / `package-lock.json`：新增 `react-markdown@^10`、`remark-gfm@^4`。
- `web/vite.config.js`：`optimizeDeps.include` 追加 `react-markdown`、`remark-gfm`——二者仅被懒加载的问答快照路由引入，预打包以避免首次进入该页时 vite 中途重优化触发动态导入失败（与 `@cp949/react-wordcloud` 同因）。

## 边界

- 纯前端：不改路由 path、不动后端取数与 `normalizeAnswerSnapshots`。浮窗只读已加载行数据，不发新请求。
- 安全：react-markdown 默认不解析原始 HTML，回答内 HTML 以纯文本呈现，无 XSS 面。
- react-markdown / remark-gfm 进入懒加载的问答快照 chunk（约 54 kB），不入主包。

## 验证

- `npm --prefix web test` → 147 pass / 0 fail（新增 markdownContent 3 例 + answerSnapshots 浮窗契约 2 例）。
- `npm --prefix web run lint` → 0 error；改动文件 0 warning（既有 8 warning 均在未改文件）。
- `npm --prefix web run build` → 成功（`✓ built`），react-markdown 进入懒加载 chunk。
- 依赖预打包：隔离 cacheDir 跑 `vite optimize`，确认 `react-markdown`、`remark-gfm` 在启动期被预打包（未触碰运行中 dev server 缓存）。
- 浮窗交互与 Markdown 实际渲染（无 jsdom，单测不覆盖）：**待人工验收**——进入问答快照，点回答/问题单元格弹出居中浮窗、Markdown 正确解析、Esc/遮罩可关闭。

## 后续

- 代码块语法高亮、复制到剪贴板按 YAGNI 未做，可后续增强。
