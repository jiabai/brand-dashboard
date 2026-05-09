# 项目任务清单（示例）

> 说明：用于记录复杂或跨多次提交的工作计划，使用 `[ ]` / `[x]` 表示任务状态。

## 当前里程碑

- [x] 重构 API 结构，引入 v1 版本前缀并迁移相关模块
- [x] 修正数据库 Schema 中的字段语义冲突（移除 extracted_at 的 ON UPDATE 触发器）
- [ ] 优化品牌分析仪表板布局与响应式表现
- [ ] 为核心组件补充基础渲染与交互测试
- [x] 全面审查并升级文档 (移除不存在的组件引用，统一技术栈描述)
- [x] 梳理 README，补充本地开发与部署说明
- [x] 修正并更新环境变量：重命名 VITE_DEFAULT_USER_ID 为 VITE_DEFAULT_TENANT_KEY 并更新默认业务参数 (Job ID, Tenant Key)

## 历史任务示例

- [x] 搭建 Vite + React + Tailwind 项目基础结构
