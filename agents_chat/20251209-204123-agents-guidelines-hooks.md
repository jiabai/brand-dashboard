# Brand Dashboard – Agents & Hooks Update

## Summary

- Refined `AGENTS.md` to align with patterns from `orion` and `talkReplay`, including agents_chat usage and tasks.md workflow.
- Introduced Husky-based Git hooks to enforce agents_chat records and Conventional Commit messages.
- Added initial `tasks.md` checklist for planning more complex or multi-commit work.

## Code Highlights

- Updated repository guidelines in `AGENTS.md` to cover project overview, structure, coding style, testing, Git workflow, agents_chat, and tasks.md usage.
- Configured Husky hooks in `.husky/pre-commit` and `.husky/commit-msg` plus `"prepare": "husky"` in `package.json`.
- Added `commitlint.config.mjs` with conventional commit rules and installed `@commitlint/*` + `husky` as dev dependencies, updating `package-lock.json`.
- Created `agents_chat/.gitkeep` to keep the directory in Git and a starter `tasks.md` with checkbox-style tasks.

## Self-Tests

- `npm install` (ensured Husky hooks are installed and dependencies updated).
- Manual check: verified `.husky/pre-commit` enforces agents_chat filename pattern and required sections.
- Manual check: verified `.husky/commit-msg` wires commitlint against `commitlint.config.mjs`.

