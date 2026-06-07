-- Phase 2.2: add qa_brand_state idempotency key for mention_status reruns.
--
-- Precheck before applying this migration:
--   uv run --project api python api/scripts/check_duplicate_analysis_rows.py --limit 50
--
-- If `qa_brand_state_target_key_duplicates` returns rows, deduplicate or archive
-- those rows first. Adding this key with existing duplicates will fail.
--
-- Prefix lengths keep the composite key under InnoDB's 3072-byte utf8mb4 index
-- limit while preserving the current practical ID space: tenant_key, job_id, and
-- conversation_id are generated identifiers and are expected to be far shorter
-- than 191 characters.

ALTER TABLE `qa_brand_state`
  ADD UNIQUE KEY `uk_tenant_job_conv_brand`
    (`tenant_key`(191), `job_id`(191), `conversation_id`(191), `brand`);
