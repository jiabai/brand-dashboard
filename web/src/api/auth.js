import { postJson as post } from './client.js';

export const createPlatformTenant = (payload) => {
  return post('/api/v1/platform/tenants', payload);
};

export const activateAuth = (payload) => {
  return post('/api/v1/public/auth/activate', payload);
};

export const verifyInviteCode = (payload) => {
  return post('/api/v1/public/users/verify-invite-code', payload);
};

export const registerUser = (payload) => {
  return post('/api/v1/public/users/register', payload);
};

export const login = (payload) => {
  return post('/api/v1/public/auth/login', payload);
};
