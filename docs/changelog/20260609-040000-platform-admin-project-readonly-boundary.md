# 平台管理员项目只读边界

## 变更内容

- 明确平台管理员在租户项目页中的定位是查看、排障和体验客户视角。
- 项目列表、项目详情和数据质量页在平台只读访问时显示统一提示。
- 保持平台租户详情页项目区域为“项目概览”，不新增创建、编辑、归档、删除项目操作。
- 继续依赖现有项目 API 权限边界：平台管理员无租户 membership 时只能访问项目 GET/read 接口，不能创建项目或配置品牌、问题集。

## 边界

- 不实现租户管理员项目管理功能。
- 不新增平台项目写 API。
- 不改变 `user_tenants` membership 和租户管理员权限语义。

## 验证

- `npm --prefix web test -- src/components/projects/__tests__/projectListPage.test.js src/components/projects/__tests__/projectDetailPage.test.js src/components/projects/__tests__/projectDataQualityPage.test.js`
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_projects_api.py -q`
- `npm --prefix web run build`
- `python scripts/validate_agents_docs.py --level ERROR`
