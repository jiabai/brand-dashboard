# ExecPlan: Dark Mode 主题切换

## 范围

为 Brand Dashboard 前端增加用户可操作的 Dark Mode 切换功能。

## 背景

- Tailwind 已配置 `darkMode: ["class"]`
- `index.css` 已定义完整的 `:root`（浅色）和 `.dark`（深色）CSS 变量
- 多个 shadcn/ui 组件已写 `dark:` 前缀适配
- **缺失**：没有主题状态管理、切换入口、持久化

## 决策记录

| # | 决策 | 理由 |
|---|------|------|
| 1 | 使用 React Context + `localStorage` 管理主题 | 不引入新库，符合"无聊技术优先"原则 |
| 2 | 切换按钮放在 DashboardLayout Header 右侧 | 用户全局可访问，不占用主要内容空间 |
| 3 | 默认跟随系统 `prefers-color-scheme` | 首次访问体验更自然 |
| 4 | 使用 `document.documentElement.classList` 切换 `dark` | 与 Tailwind `darkMode: ["class"]` 策略一致 |
| 5 | 修复硬编码浅色样式 | `app-shell.css` 有 `#fbfaf6`/`#f6f1e9` 渐变；`QueryJobStatus`/`SubmissionSuccess` 有 `rgba(255,255,255, ...)` glass-card |

## 任务清单

- [x] 1. 创建 `web/src/hooks/useTheme.jsx` — 主题状态、持久化、系统偏好监听
- [x] 2. 在 `main.jsx` 注入 ThemeProvider
- [x] 3. 在 `DashboardLayout.jsx` Header 添加主题切换按钮
- [x] 4. 修复 `app-shell.css` 渐变背景为 CSS 变量适配
- [x] 5. 修复 `QueryJobStatus.jsx` / `SubmissionSuccess.jsx` glass-card 颜色硬编码
- [x] 6. 运行 `npm --prefix web run build` 验证构建
- [x] 7. 运行 `npm --prefix web test` 验证测试
- [x] 8. 更新本文档 Progress

## 验证记录

| 检查项 | 状态 | 时间 |
|--------|------|------|
| 构建通过 | 通过 | 2026-05-19 |
| 测试通过 | 通过（30/30） | 2026-05-19 |
| 文档验证 | 通过 `python scripts/validate_agents_docs.py --level ERROR` | 2026-05-19 |

## 变更文件清单

### 新增
- `web/src/hooks/useTheme.jsx`
- `web/src/components/ThemeToggle.jsx`

### 修改
- `web/src/main.jsx` — 注入 ThemeProvider
- `web/src/components/DashboardLayout.jsx` — 添加 ThemeToggle
- `web/src/styles/app-shell.css` — 渐变背景改用 CSS 变量
- `web/src/components/QueryJobStatus.jsx` — glass-card 颜色改用 CSS 变量
- `web/src/components/SubmissionSuccess.jsx` — glass-card 颜色改用 CSS 变量
- `web/src/index.css` — 移除 `.text-2xl` 等类选择器上的全局行高覆盖
- `web/src/__tests__/ui-stack-migration.test.js` — 同步测试期望与实际代码

## 残余风险

- 部分业务组件可能仍有未适配的硬编码颜色，需要后续使用时逐一发现修复
