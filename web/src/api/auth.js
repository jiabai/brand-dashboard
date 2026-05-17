import { postJson as post } from './client.js';

export const createPlatformTenant = (payload, options) => {
  return post('/api/v1/platform/tenants', payload, options);
};

export const activateAuth = (payload, options) => {
  return post('/api/v1/public/auth/activate', payload, options);
};

export const verifyInviteCode = (payload, options) => {
  return post('/api/v1/public/users/verify-invite-code', payload, options);
};

export const registerUser = (payload, options) => {
  return post('/api/v1/public/users/register', payload, options);
};

export const login = (payload, options) => {
  return post('/api/v1/public/auth/login', payload, options);
};
