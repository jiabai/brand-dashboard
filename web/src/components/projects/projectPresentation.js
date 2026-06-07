const encodePathSegment = (value) => encodeURIComponent(String(value || '').trim());

export const normalizeProjectListResponse = (response) => {
  const projects = Array.isArray(response?.projects) ? response.projects : [];
  return {
    count: Number.isFinite(response?.count) ? response.count : projects.length,
    projects,
  };
};

export const normalizeProjectDetailResponse = (response) => {
  const project = response?.project;
  if (!project || typeof project !== 'object') {
    return null;
  }

  return {
    ...project,
    brands: Array.isArray(project.brands) ? project.brands : [],
    prompt_sets: Array.isArray(project.prompt_sets)
      ? project.prompt_sets.map((promptSet) => ({
        ...promptSet,
        items: Array.isArray(promptSet.items) ? promptSet.items : [],
      }))
      : [],
  };
};

export const getProjectStatusMeta = (status) => {
  const normalized = String(status || '').trim();
  const map = {
    active: { label: '运行中', variant: 'default' },
    paused: { label: '已暂停', variant: 'secondary' },
    archived: { label: '已归档', variant: 'outline' },
    draft: { label: '配置中', variant: 'secondary' },
  };
  return map[normalized] || { label: normalized || '未知', variant: 'secondary' };
};

export const buildProjectListPath = ({ tenantKey } = {}) => {
  const nextTenantKey = String(tenantKey || '').trim();
  if (!nextTenantKey) return '';
  return `/projects/${encodePathSegment(nextTenantKey)}`;
};

export const buildProjectDetailPath = ({ tenantKey, projectId } = {}) => {
  const nextTenantKey = String(tenantKey || '').trim();
  const nextProjectId = String(projectId || '').trim();
  if (!nextTenantKey || !nextProjectId) return '';
  return `/projects/${encodePathSegment(nextTenantKey)}/${encodePathSegment(nextProjectId)}`;
};

export const countProjectBrandsByRole = (brands = []) => {
  const items = Array.isArray(brands) ? brands : [];
  return items.reduce(
    (acc, brand) => {
      const role = brand?.role || 'watch_only';
      if (role === 'target') acc.target += 1;
      else if (role === 'competitor') acc.competitor += 1;
      else acc.watchOnly += 1;
      return acc;
    },
    { target: 0, competitor: 0, watchOnly: 0 },
  );
};
