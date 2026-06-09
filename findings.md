# SQLite GEO Migration Findings

## Known Source State

- `data/geo_csv/geo.db` is the legacy SQLite DB with data.
- Actual legacy tables: `executors`, `invitation_codes`, `llm_conversation_references`, `llm_conversations`, `llm_query_jobs`, `qa_brand_state`, `qa_reference`, `tenant_configs`, `tenants`, `user_tenants`, `users`.
- The legacy DB is missing current project/lifecycle/read-model tables such as `monitoring_projects`, `project_brands`, `prompt_sets`, `prompt_items`, `collection_jobs`, `collection_tasks`, `collection_attempts`, `analysis_runs`, `alert_rules`, `alert_events`, `generated_reports`, and `qa_brand_summary`.
- Missing current columns in existing tables: `llm_query_jobs.project_id`, `qa_brand_state.analysis_run_id`, `qa_reference.analysis_run_id`.

## Migration Assumptions

- Each `(tenant_key, job_id)` group becomes one `monitoring_projects` row and one `collection_jobs` row.
- Each `(tenant_key, job_id)` group gets one synthetic `analysis_runs` row with status `succeeded`.
- Legacy `llm_query_jobs` rows are linked to their generated project by `project_id`.
- `qa_brand_state` and `qa_reference` rows are linked to their generated analysis run by `analysis_run_id`.
- Project brands are inferred from distinct `qa_brand_state.brand` values and `llm_query_jobs.brand`; the most frequent brand per project is marked `target`, remaining brands are `competitor`.

## Open Risks

- The legacy data does not contain true project names, prompt set versions, collection task history, or actual analysis run lifecycle events. Those must be synthesized.
- Generated lifecycle data is compatibility scaffolding, not historical operational truth.
