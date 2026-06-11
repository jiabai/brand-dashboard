import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';
import assert from 'node:assert/strict';

const accountManagementSource = () =>
  readFileSync(
    join(import.meta.dirname, '..', 'AccountManagement.jsx'),
    'utf8',
  );

test('logged-in account management page does not include admin activation workflow', () => {
  const source = accountManagementSource();

  assert.doesNotMatch(source, /TabsTrigger\s+value="activation"/);
  assert.doesNotMatch(source, /TabsContent\s+value="activation"/);
  assert.doesNotMatch(source, /activateAuth/);
  assert.doesNotMatch(source, /管理员激活/);
});

test('account management page exposes a change password form calling the authed endpoint', () => {
  const source = accountManagementSource();

  assert.match(source, /changePassword/);
  assert.match(source, /修改密码/);
  assert.match(source, /currentPassword/);
  assert.match(source, /newPassword/);
  assert.match(source, /confirmPassword/);
  assert.match(source, /两次输入的新密码不一致/);
});
