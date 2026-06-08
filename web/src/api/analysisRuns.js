import { postJson } from './client.js';

const encodePathSegment = (value) => encodeURIComponent(String(value || '').trim());

export const retryAnalysisRun = ({
  tenantKey,
  analysisRunId,
  retryAnalysisRunId,
} = {}, options = {}) => {
  const body = retryAnalysisRunId ? { analysis_run_id: retryAnalysisRunId } : {};
  return postJson(`/api/v1/analysis-runs/${encodePathSegment(analysisRunId)}/retry`, body, {
    ...options,
    tenantKey,
  });
};
