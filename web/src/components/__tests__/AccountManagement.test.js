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

test('join team page does not include tenant opening or login workflows', () => {
  const source = accountManagementSource();

  assert.doesNotMatch(source, /login as loginApi/);
  assert.doesNotMatch(source, /loginApi/);
  assert.doesNotMatch(source, /TabsTrigger\s+value="login"/);
  assert.doesNotMatch(source, /TabsContent\s+value="login"/);
  assert.doesNotMatch(source, /账户登录/);
  assert.doesNotMatch(source, /登录并获取访问令牌/);
  assert.doesNotMatch(source, /TabsTrigger\s+value="tenant"/);
  assert.doesNotMatch(source, /TabsContent\s+value="tenant"/);
  assert.doesNotMatch(source, /租户开通/);
  assert.doesNotMatch(source, /进入平台租户管理/);
});

test('join team page keeps invite verification and employee registration as the only workflows', () => {
  const source = accountManagementSource();

  assert.match(source, /加入团队与邀请注册/);
  assert.match(source, /邀请码核验/);
  assert.match(source, /员工注册/);
  assert.match(source, /verifyInviteCode/);
  assert.match(source, /registerUser/);
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
