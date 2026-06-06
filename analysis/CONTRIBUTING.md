# Contributing to Brand Analysis

Thank you for helping improve Brand Analysis. This project is a Python CLI/library for plugin-based brand cognition analysis over MySQL-backed AI conversation and reference data.

## Start Here

Before making a non-trivial change, read:

- `AGENTS.md`
- `WORKFLOW.md`
- `docs/ARCHITECTURE.md`
- `docs/DESIGN.md`
- `docs/SECURITY.md`

If a change modifies CLI behavior, configuration shape, plugin contracts, output JSON, database writes, or security boundaries, create or update a product spec in `docs/product-specs/` and an ExecPlan in `docs/exec-plans/active/`.

## Development Setup

```bash
git clone <your-fork-url>
cd brand_analysis
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install -e ".[dev]"
```

On Linux or macOS, activate the environment with:

```bash
source .venv/bin/activate
```

## Code Standards

- Keep plugin behavior behind `AnalysisPlugin` and `PluginRegistry`.
- Keep runtime parameters in `config/` or environment variables.
- Validate table names, fields, dates, CLI inputs and LLM configuration at boundaries.
- Do not log API keys, database passwords or sensitive prompt content.
- Follow the formatting and type-checking settings in `pyproject.toml`.

## Documentation Standards

- Root `AGENTS.md` is a short entry map, not a full manual.
- Long-lived architecture and design constraints belong in `docs/ARCHITECTURE.md`, `docs/DESIGN.md` or `docs/SECURITY.md`.
- User-visible scope belongs in `docs/product-specs/`.
- Implementation plans and recovery context belong in `docs/exec-plans/`.
- Technical references and plugin usage notes belong in `docs/references/`.
- Update `docs/index.md` and any relevant subdirectory index when moving or adding documentation.

## Verification

Run the smallest relevant checks first, then expand based on risk.

```bash
python scripts/validate_agents_docs.py --level WARN
python -m src --help
pytest
black --check src tests
isort --check-only src tests
mypy src
```

For focused checks, prefer commands such as:

```bash
pytest tests/test_unified_llm_operator.py
pytest tests/test_reference_status.py
pytest tests/test_llm_brand_recognition.py
```

Tests that require real LLM providers, network access or a live MySQL database must be marked or documented as integration/manual checks.

## Pull Request Process

1. Create a focused branch.
2. Inspect the relevant code and docs before editing.
3. Keep changes small and tied to a clear spec or task.
4. Update tests and durable documentation together.
5. Run the relevant verification commands.
6. Include Passed, Not run and Residual risk in the PR notes.

## Commit Messages

Use conventional commit prefixes where practical:

- `feat:` user-visible feature
- `fix:` bug fix
- `docs:` documentation-only change
- `refactor:` internal structure change without behavior change
- `test:` test addition or update
- `chore:` maintenance

Examples:

```text
docs: organize reference documentation
fix: validate configured datasource table names
test: cover reference status aggregation
```

## Security

Do not commit real `.env` files, API keys, database passwords, production exports or sensitive customer data. If a test or example needs credentials, use placeholders and document the required environment variables.

## Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to follow it.
