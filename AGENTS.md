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
  - `feat: add model comparison view`
  - `fix: fix loading spinner flicker`
  - `docs: update README for new sections`
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
- Language policy: `agents_chat` records should be written primarily in Chinese (Simplified), while this `AGENTS.md` file must remain English-only.

## 8. Agent-Specific Instructions

- Prefer minimal, targeted changes; follow existing patterns in `src/components`, `src/styles`, Tailwind, and the Vite setup.
- When adding tooling (tests, linting, formatting), wire it into `package.json` scripts and document usage here or in `README.md`.
- For every substantial change, add or update an `agents_chat` record in the same commit to keep the project auditable.

## 9. tasks.md Task List Guidelines

- For complex or multi-commit work, maintain `tasks.md` in the repository root.
- Use Markdown checkboxes to represent task status, for example:
  - `- [ ] Implement new brand trend chart component`
  - `- [x] Add sticky GooeyNav navigation behavior`
- Keep each item small and well-scoped (ideally completable in 1–2 commits), and update `[ ]` to `[x]` as work is finished.
- For important milestones or scope changes, update `tasks.md` first and then start coding, so the plan stays visible to others.
