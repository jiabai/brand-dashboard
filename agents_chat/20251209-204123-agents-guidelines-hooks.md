## 项目：Brand Dashboard – Agents & Hooks 更新说明

## Summary

- 调整并细化 `AGENTS.md`，对齐 `orion` 和 `talkReplay` 中的模式，明确 agents_chat 使用方式以及 `tasks.md` 工作流。
- 新增基于 Husky 的 Git 钩子，用于强制每次提交带上 agents_chat 记录，并校验 Conventional Commits 提交信息。
- 增加初始版本的 `tasks.md` 任务清单，方便拆分复杂或多次提交的工作。

## Code Highlights

- 在 `AGENTS.md` 中补充项目概览、目录结构、编码风格、测试策略、Git 工作流、agents_chat 规范以及 `tasks.md` 使用说明。
- 配置 `.husky/pre-commit` 与 `.husky/commit-msg`，并在 `package.json` 中加入 `"prepare": "husky"`，让安装依赖时自动安装钩子。
- 新增 `commitlint.config.mjs`，配置 Conventional Commits 规则，并在 devDependencies 中加入 `@commitlint/*` 与 `husky`，同步更新 `package-lock.json`。
- 创建 `agents_chat` 目录与示例记录文件，同时提供初始 `tasks.md`，采用复选框形式管理任务。

## Self-Tests

- 执行 `npm install`，确认 Husky 钩子自动安装且依赖无明显错误。
- 人工检查 `.husky/pre-commit` 是否正确校验 agents_chat 文件命名与必需章节。
- 人工检查 `.husky/commit-msg` 是否正确调用 `commitlint` 并使用 `commitlint.config.mjs` 中的配置。
