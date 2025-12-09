# Repository Guidelines

## 1. Project Overview

- Brand Analysis Dashboard built with React 18 + Vite + Tailwind CSS.
- Focus on a clean, responsive dashboard UI; no backend code in this repo.
- Keep the codebase small, readable, and easy to extend with new cards/sections.

## 2. Project Structure & Modules

- Entry: `src/main.jsx` (mount) and `src/App.jsx` (root layout).
- Components: `src/components` for feature components; `src/components/ui` for reusable primitives.
- Styles: global styles in `src/App.css` and `src/index.css`; feature styles in `src/styles/*.css`.
- Utilities: shared helpers in `src/lib` (e.g. `cn.js`) and `src/utils`.

## 3. Development, Build & Test

- Install: `npm install` (use npm to keep `package-lock.json` authoritative).
- Dev server: `npm run dev` (default `http://localhost:5173`).
- Build: `npm run build` to generate `dist/`.
- Preview: `npm run preview` to serve the built app.
- When adding tests, wire them via `npm test` (Vitest + React Testing Library recommended).

## 4. Coding Style & Naming

- Use function components and hooks; prefer composition over deep prop drilling.
- Indentation: 2 spaces; ES modules only; `camelCase` for variables/functions, `PascalCase` for React components and files in `src/components`.
- Prefer Tailwind utility classes for layout/spacing; keep custom CSS in `src/styles` or component-level `.css`.
- Keep JSX mostly declarative; extract non-trivial logic to helpers in `src/utils` or `src/lib`.

## 5. Testing Guidelines

- Place tests next to components (`ComponentName.test.jsx`) or in a `__tests__` folder.
- For each new feature, add at least rendering + basic interaction tests where practical.
- Aim to keep tests fast; avoid hitting network or external services.

## 6. Git Workflow & Commit Messages

- Use Conventional Commits, e.g.:
  - `feat: 添加模型对比视图`
  - `fix: 修复加载状态闪烁`
  - `docs: 更新README文档`
- Keep commits small and focused; avoid mixing refactors with feature changes.
- Before pushing, ensure the project builds and key flows still work in the browser.

## 7. Git Hooks & agents_chat Records

- Husky pre-commit hook enforces that every commit touching code also updates an `agents_chat/` record.
- `agents_chat` file naming: `agents_chat/YYYYMMDD-HHMMSS-topic.md` (UTC or local, but be consistent).
- Each record must contain at least:
  - `## Summary` – what changed and why.
  - `## Code Highlights` – key files, components, or patterns.
  - `## Self-Tests` – manual checks or commands run (e.g. `npm run dev`, `npm run build`).
- Pre-commit also runs available npm quality scripts (`npm run lint` / `npm test` when defined).

## 8. Agent-Specific Instructions

- Prefer minimal, targeted changes; follow existing patterns in `src/components`, `src/styles`, Tailwind, and the Vite setup.
- When adding tooling (tests, linting, formatting), wire it into `package.json` scripts and document usage here or in `README.md`.
- For every substantial change, add or update an `agents_chat` record in the same commit to keep the project auditable.

## 9. tasks.md 任务列表规范

- 对于复杂或跨多次提交的工作，请在仓库根目录维护 `tasks.md`。
- 使用 Markdown 复选框表示任务状态，例如：
  - `- [ ] 实现新的品牌趋势图表组件`
  - `- [x] 增加 GooeyNav 粘性导航交互`
- 保持条目粒度清晰（可在 1–2 个提交内完成），并在任务完成后及时将 `[ ]` 更新为 `[x]`。
- 重要里程碑或需求变更，优先先更新 `tasks.md`，再开始编码，以保持对外可见的计划。

