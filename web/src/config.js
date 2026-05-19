/**
 * 全局配置管理
 * 从环境变量中读取配置，并提供默认值
 */

const viteEnv = import.meta.env || {};

export const CONFIG = {
  // API 配置
  API_TARGET: viteEnv.VITE_API_TARGET || 'http://localhost:8000',
  USE_MOCK: viteEnv.VITE_USE_MOCK === 'true',

  // 默认业务参数
  DEFAULT_TENANT_KEY: viteEnv.VITE_DEFAULT_TENANT_KEY || 'tn_1b02b3ef4fbd',
  DEFAULT_JOB_ID: viteEnv.VITE_DEFAULT_JOB_ID || 'job_20260127_223236_989cc4db',
  DEFAULT_BRAND: viteEnv.VITE_DEFAULT_BRAND || '哈基桃电竞',
  DEFAULT_EXECUTOR_ID: viteEnv.VITE_DEFAULT_EXECUTOR_ID || 'exec_bbda021a',
  DEFAULT_INCLUDE_DELETED: viteEnv.VITE_DEFAULT_INCLUDE_DELETED || 'false',
};

export default CONFIG;
