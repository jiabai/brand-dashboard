import test from 'node:test';
import assert from 'node:assert/strict';

import { readActivationTokenFromSearch } from '../activation.js';

test('reads activation token from URL search params', () => {
  assert.equal(readActivationTokenFromSearch('?token=abc.def'), 'abc.def');
  assert.equal(readActivationTokenFromSearch('?foo=bar&token=abc%2Bdef'), 'abc+def');
});

test('returns empty token when URL search params do not include activation token', () => {
  assert.equal(readActivationTokenFromSearch(''), '');
  assert.equal(readActivationTokenFromSearch('?foo=bar'), '');
  assert.equal(readActivationTokenFromSearch('?token='), '');
});
