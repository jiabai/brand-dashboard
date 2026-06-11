import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const sourcePath = resolve(__dirname, '../PlatformTenantDetailPage.jsx');
const source = readFileSync(sourcePath, 'utf8');

describe('PlatformTenantDetailPage contract', () => {
  it('keeps tenant detail project content as an overview, not the workspace title', () => {
    assert.match(source, /label: '项目数'/);
    assert.match(source, /项目概览/);
    assert.match(source, /id="project-overview"/);
    assert.doesNotMatch(source, /label: '监测项目'/);
  });

  it('marks project overview actions with the tenant detail navigation source', () => {
    assert.match(source, /PROJECT_NAV_SOURCE_PLATFORM_TENANT_DETAIL/);
    assert.match(source, /scrollIntoView/);
  });

  it('does not expose tenant project management actions to platform admins', () => {
    assert.doesNotMatch(source, /新建项目/);
    assert.doesNotMatch(source, /编辑项目/);
    assert.doesNotMatch(source, /归档项目/);
    assert.doesNotMatch(source, /删除项目/);
  });

  it('renders a tenant administrator information section', () => {
    assert.match(source, /id="tenant-admin"/);
    assert.match(source, /租户管理员/);
    assert.match(source, /adminName/);
    assert.match(source, /adminEmail/);
    assert.match(source, /adminPhone/);
    assert.match(source, /管理员状态/);
  });
});

describe('PlatformTenantDetailPage emergency admin setting contract', () => {
  it('exposes an audited platform emergency admin setting entry', () => {
    assert.match(source, /fetchPlatformTenantMembers/);
    assert.match(source, /updatePlatformTenantMember/);
    assert.match(source, /SheetContent/);
    assert.match(source, /SelectItem/);
    assert.match(source, /Textarea/);
    assert.match(source, /reason/);
    assert.match(source, /role: 'admin'/);
    assert.match(source, /status: 'active'/);
  });
});

describe('PlatformTenantDetailPage resend activation contract', () => {
  it('exposes a resend activation entry for pending admins', () => {
    assert.match(source, /resendPlatformTenantActivation/);
    assert.match(source, /adminStatus === 'pending_activation'/);
    assert.match(source, /重发激活邮件/);
    assert.match(source, /getEmailDeliveryMeta/);
    assert.match(source, /新激活链接/);
    assert.match(source, /复制激活链接/);
  });

  it('keeps resend result presentation consistent with create tenant panel', () => {
    assert.match(source, /resendResult\.activationUrl/);
    assert.match(source, /AlertTitle>\{resendDeliveryMeta\.title\}/);
  });
});
