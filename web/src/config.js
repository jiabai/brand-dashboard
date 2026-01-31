/**
 * 全局配置管理
 * 从环境变量中读取配置，并提供默认值
 */

export const CONFIG = {
  // API 配置
  API_TARGET: import.meta.env.VITE_API_TARGET || 'http://localhost:8000',
  USE_MOCK: import.meta.env.VITE_USE_MOCK === 'true',

  // 默认业务参数
  DEFAULT_TENANT_KEY: 'tn_1b02b3ef4fbd',
  DEFAULT_JOB_ID: 'job_20260102_125104_7fad76ad',
  DEFAULT_BRAND: '新东方',
};

export default CONFIG;
