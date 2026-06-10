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
