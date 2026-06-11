import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const loginViewSource = readFileSync(resolve(__dirname, '../LoginView.jsx'), 'utf8');
const appSource = readFileSync(resolve(__dirname, '../../App.jsx'), 'utf8');

describe('LoginView password reset contract', () => {
  it('exposes a forgot password entry and a reset tab', () => {
    assert.match(loginViewSource, /忘记密码？/);
    assert.match(loginViewSource, /value="reset"/);
    assert.match(loginViewSource, /grid-cols-4/);
    assert.match(loginViewSource, /forgotPassword/);
    assert.match(loginViewSource, /resetPassword/);
    assert.match(loginViewSource, /发送重置邮件/);
    assert.match(loginViewSource, /重置密码/);
  });

  it('keeps token autofill route-aware for activate and reset', () => {
    assert.match(loginViewSource, /location\.pathname === '\/reset-password'/);
    assert.match(loginViewSource, /location\.pathname === '\/activate'/);
  });
});

describe('App reset-password route contract', () => {
  it('routes /reset-password to the login view reset tab', () => {
    assert.match(appSource, /path="\/reset-password"/);
    assert.match(appSource, /defaultTab="reset"/);
  });
});
