export const ROUTES = {
  projects: {
    viewKey: 'projects',
    path: '/projects/:tenantKey',
    routeSegment: 'projects',
    menuLabel: '监测项目',
    menuIcon: 'FolderKanbanOutlined',
    menuSection: 'main',
    requiresJobId: false,
  },
  'project-detail': {
    viewKey: 'project-detail',
    path: '/projects/:tenantKey/:projectId',
    routeSegment: 'projects',
    menuLabel: '项目详情',
    menuIcon: 'FolderKanbanOutlined',
    menuSection: 'hidden',
    requiresJobId: false,
    requiresProjectId: true,
  },
  home: {
    viewKey: 'home',
    path: '/dashboard/:tenantKey/:jobId',
    routeSegment: 'dashboard',
    menuLabel: '首页',
    menuIcon: 'HomeOutlined',
    menuSection: 'main',
    requiresJobId: true,
  },
  trend: {
    viewKey: 'trend',
    path: '/trend/:tenantKey/:jobId',
    routeSegment: 'trend',
    menuLabel: '趋势分析',
    menuIcon: 'LineChartOutlined',
    menuSection: 'main',
    requiresJobId: true,
  },
  platforms: {
    viewKey: 'platforms',
    path: '/platforms/:tenantKey/:jobId',
    routeSegment: 'platforms',
    menuLabel: '分平台分析',
    menuIcon: 'BarChartOutlined',
    menuSection: 'main',
    requiresJobId: true,
  },
  sources: {
    viewKey: 'sources',
    path: '/sources/:tenantKey/:jobId',
    routeSegment: 'sources',
    menuLabel: '信源分析',
    menuIcon: 'MessageOutlined',
    menuSection: 'main',
    requiresJobId: true,
  },
  sentiment: {
    viewKey: 'sentiment',
    path: '/sentiment/:tenantKey/:jobId',
    routeSegment: 'sentiment',
    menuLabel: '情感分析',
    menuIcon: 'SmileOutlined',
    menuSection: 'main',
    requiresJobId: true,
  },
  snapshots: {
    viewKey: 'snapshots',
    path: '/snapshots/:tenantKey/:jobId',
    routeSegment: 'snapshots',
    menuLabel: '问答快照',
    menuIcon: 'PictureOutlined',
    menuSection: 'main',
    requiresJobId: true,
  },
  settings: {
    viewKey: 'settings',
    menuLabel: '品牌设置',
    menuIcon: 'SettingOutlined',
    menuSection: 'main',
    disabled: true,
    requiresJobId: true,
  },
  accounts: {
    viewKey: 'accounts',
    path: '/accounts/:tenantKey',
    routeSegment: 'accounts',
    menuLabel: '账户管理',
    menuIcon: 'UserOutlined',
    menuSection: 'main',
    requiresJobId: false,
  },
  subscribe: {
    viewKey: 'subscribe',
    menuLabel: '订阅',
    menuIcon: 'BookOutlined',
    menuSection: 'main',
    disabled: true,
    requiresJobId: false,
  },
  'task-load': {
    viewKey: 'task-load',
    path: '/tasks/:tenantKey/new',
    parentSegment: 'tasks',
    taskAction: 'new',
    menuLabel: '新建任务',
    menuIcon: 'PlusOutlined',
    menuSection: 'task',
    requiresJobId: false,
  },
  'task-status': {
    viewKey: 'task-status',
    path: '/tasks/:tenantKey/status',
    parentSegment: 'tasks',
    taskAction: 'status',
    menuLabel: '任务状态',
    menuIcon: 'UnorderedListOutlined',
    menuSection: 'task',
    requiresJobId: false,
  },
};

export const DEFAULT_VIEW_KEY = 'home';

export const ROUTE_DEFINITIONS = Object.values(ROUTES);

export const getRouteByViewKey = (viewKey) =>
  ROUTES[viewKey] || ROUTES[DEFAULT_VIEW_KEY];

export const getRouteByPathSegment = (segment) =>
  ROUTE_DEFINITIONS.find((route) => route.routeSegment === segment);

export const getRouteByTaskAction = (taskAction) =>
  ROUTE_DEFINITIONS.find((route) => route.parentSegment === 'tasks' && route.taskAction === taskAction);

export const getRoutableRoutes = () =>
  ROUTE_DEFINITIONS.filter((route) => Boolean(route.path));

export const getSidebarMenuRoutes = () =>
  ROUTE_DEFINITIONS.filter((route) => route.menuSection === 'main');

export const getTaskMenuRoutes = () =>
  ROUTE_DEFINITIONS.filter((route) => route.menuSection === 'task');
