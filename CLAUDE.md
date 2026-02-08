# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Brand Analysis Dashboard with React 18 + Vite + Tailwind (frontend in `web/`) and FastAPI (backend in `api/`). Bilingual project with Chinese documentation and English AGENTS.md guidelines.

## Commands

### Frontend (web/)
```bash
cd web && npm install          # Install dependencies
npm --prefix web run dev       # Dev server at http://localhost:3000
npm --prefix web run build     # Build to web/dist/
npm --prefix web run test      # Run tests
```

### Backend (api/)
```bash
pip install -r api/requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Linting
```bash
ruff check api                 # Backend linting (ruff config in api/pyproject.toml)
```

### Docker
```bash
docker compose -f docker-compose.dev.yml up --build   # Dev mode
docker compose -f docker-compose.prod.yml up --build  # Production mode
```

## Architecture

- **Frontend entry**: `web/src/main.jsx` (mount) → `web/src/App.jsx` (root layout)
- **Components**: `web/src/components/` for features, `web/src/components/ui/` for shadcn/ui primitives
- **Utilities**: `web/src/lib/` (e.g., `cn.js` for classname merging), `web/src/utils/`
- **Styles**: Global in `web/src/App.css` and `web/src/index.css`; feature styles in `web/src/styles/*.css`
- **Path alias**: `@` maps to `web/src` (configured in `web/vite.config.js`)

- **Backend entry**: `api/main.py` (FastAPI app)
- **API docs**: http://localhost:8000/api/v1/docs (Swagger), http://localhost:8000/api/v1/redoc

## Coding Conventions

- 2 spaces indentation, ES modules only
- `camelCase` for variables/functions, `PascalCase` for React components
- Prefer Tailwind utility classes; custom CSS goes in `web/src/styles/`
- Backend: type hints required, reuse Pydantic models from `api/models/schemas.py`

## Git Workflow

- **Conventional Commits**: `feat:`, `fix:`, `docs:`, etc.
- **Pre-commit hook** runs `ruff check api` and frontend lint/test scripts
- **Change records**: Every code commit must include an `agents_chat/YYYYMMDD-HHMMSS-topic.md` file (in Chinese) containing Summary, Code Highlights, and Self-Tests sections
- **Task tracking**: Use `tasks.md` with Markdown checkboxes for multi-commit work

## Environment Variables

Frontend (`web/.env.local`):
- `VITE_API_TARGET` - Backend URL
- `VITE_USE_MOCK` - Enable mock data

Backend (`api/.env`):
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_CHARSET`
