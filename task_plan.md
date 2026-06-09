# SQLite GEO Migration Plan

## Goal

Extract legacy data from `data/geo_csv/geo.db`, transform it to the current SQLite schema, and write it to a separate new database file without modifying the source database.

## Output

- Migration script: `scripts/migrate_legacy_geo_sqlite.py`
- Generated database: `data/geo_csv/geo_migrated.db`

## Phases

1. [in_progress] Capture source schema, target schema, and compatibility gaps.
2. [pending] Define deterministic legacy-to-project mapping.
3. [pending] Write focused migration tests first.
4. [pending] Implement migration script.
5. [pending] Generate migrated database.
6. [pending] Verify target schema, row counts, and representative repository queries.
7. [pending] Remove `TASKS.md` after the active task is complete.

## Decisions

- Source DB is read-only during migration.
- New DB is generated separately as `data/geo_csv/geo_migrated.db`.
- Use `api/database/schema_sqlite.sql` as the target schema baseline.
- Preserve legacy rows in the legacy tables and backfill new lineage fields with generated IDs where possible.

## Errors Encountered

| Error | Attempt | Resolution |
|-------|---------|------------|
