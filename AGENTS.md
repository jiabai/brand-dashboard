# Repository Guidelines

## 1. Project Overview

- Brand Analysis Dashboard with React 18 + Vite + Tailwind (frontend) and a FastAPI service (backend).
- Frontend lives in `web/`, backend lives in `api/`; keep the codebase small, readable, and easy to extend.
- Aim for a clean, responsive dashboard UI with minimal coupling between UI and API concerns.

## 2. Project Structure & Modules

- Frontend entry: `web/src/main.jsx` (mount) and `web/src/App.jsx` (root layout).
- Components: `web/src/components` for feature components; `web/src/components/ui` for reusable primitives.
- Styles: global styles in `web/src/App.css` and `web/src/index.css`; feature styles in `web/src/styles/*.css`.
- Utilities: shared helpers in `web/src/lib` (e.g. `cn.js`) and `web/src/utils`.
- Backend entry: `api/main.py` (FastAPI app), routers in `api/routes`, schemas in `api/models`, data access in `api/repositories`, utilities in `api/utils`.

## 3. Development, Build & Test

- Frontend install: `cd web && npm install` (use npm to keep `web/package-lock.json` authoritative).
- Dev server: `npm --prefix web run dev` (default `http://localhost:3000`).
- Build: `npm --prefix web run build` to generate `web/dist/`; preview via `npm --prefix web run preview`.
- Backend install/run: `pip install -r api/requirements.txt` then `uvicorn api.main:app --reload --host 0.0.0.0 --port 8000`.
- Linting: `ruff check api` for backend; `npm --prefix web run lint/test --if-present` for frontend when scripts exist.
- When adding frontend tests, wire them via `npm --prefix web test` (Vitest + React Testing Library recommended).

## 4. Coding Style & Naming

- Use function components and hooks; prefer composition over deep prop drilling.
- Indentation: 2 spaces; ES modules only; `camelCase` for variables/functions, `PascalCase` for React components and files in `web/src/components`.
- Prefer Tailwind utility classes for layout/spacing; keep custom CSS in `web/src/styles` or component-level `.css`.
- Keep JSX mostly declarative; extract non-trivial logic to helpers in `web/src/utils` or `web/src/lib`.
- Backend: keep type hints, small routers/handlers, and reuse Pydantic models from `api/models/schemas.py`.

## 5. Testing Guidelines

- Place frontend tests next to components (`ComponentName.test.jsx`) in `web/src/**` or in a `__tests__` folder.
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
- Pre-commit runs `ruff check api` plus frontend quality scripts via `npm --prefix web run lint/test --if-present`.
- Commit linting relies on dependencies installed in `web/` (`npm install` there before committing).
- Language policy: `agents_chat` records should be written primarily in Chinese (Simplified), while this `AGENTS.md` file must remain English-only.

## 8. Agent-Specific Instructions

- Prefer minimal, targeted changes; follow existing patterns in `web/src/components`, `web/src/styles`, Tailwind, and the Vite setup; mirror backend patterns in `api/routes`/`api/models`.
- When adding tooling (tests, linting, formatting), wire it into `package.json` scripts and document usage here or in `README.md`.
- For every substantial change, add or update an `agents_chat` record in the same commit to keep the project auditable.

## 9. tasks.md Task List Guidelines

- For complex or multi-commit work, maintain `tasks.md` in the repository root.
- Use Markdown checkboxes to represent task status, for example:
  - `- [ ] Implement new brand trend chart component`
  - `- [x] Add sticky GooeyNav navigation behavior`
- Keep each item small and well-scoped (ideally completable in 1–2 commits), and update `[ ]` to `[x]` as work is finished.
- For important milestones or scope changes, update `tasks.md` first and then start coding, so the plan stays visible to others.
