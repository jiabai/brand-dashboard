# Changelog

All notable changes to Brand Analysis are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html) where practical.

## [Unreleased]

### Added

- AI collaboration entry map in `AGENTS.md`.
- Project workflow, execution gates, architecture, design, security and quality documentation.
- `docs/references/` for metrics, plugin and LLM operator reference material.
- Documentation validator at `scripts/validate_agents_docs.py`.

### Changed

- Reorganized existing docs into the Vibe Coding document structure.
- Updated contributing guidance from the old template project to Brand Analysis-specific workflow.

## [0.1.0]

### Added

- Plugin-based brand AI cognition analysis CLI.
- Config-driven MySQL datasource analysis.
- Core metric plugins including `mention_status` and `reference_status`.
- Utility plugins including `extract_source`, `llm_ping` and `import_mention_data`.
- Unified LLM operator and provider adapter layer.
- JSON output organized by plugin and generated-date directory.
- Optional MySQL UPSERT for selected analysis results.
- Pytest-based test suite and Python tooling configuration.
