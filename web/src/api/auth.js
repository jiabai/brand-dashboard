import { fetchJson as fetch, postJson as post } from './client.js';

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

export const forgotPassword = (payload, options) => {
  return post('/api/v1/public/auth/forgot-password', payload, options);
};

export const resetPassword = (payload, options) => {
  return post('/api/v1/public/auth/reset-password', payload, options);
};

export const changePassword = (payload, options) => {
  return post('/api/v1/auth/change-password', payload, options);
};

export const getMe = (options) => {
  return fetch('/api/v1/auth/me', options);
};
