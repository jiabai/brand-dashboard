export const readActivationTokenFromSearch = (search = '') => {
  const params = new URLSearchParams(search);
  return params.get('token') || '';
};
