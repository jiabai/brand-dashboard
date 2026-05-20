import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

import { getMe, login as loginRequest } from '../api/auth.js';
import {
  clearAuthSession,
  normalizeAuthSession,
  readAuthSession,
  updateCurrentTenantKey,
  writeAuthSession,
} from './storage.js';

const AuthContext = createContext(null);

const getUserFromMeResponse = (response) => response?.data?.user || response?.user || null;

export const AuthProvider = ({ children }) => {
  const [session, setSession] = useState(() => readAuthSession());
  const [isInitializing, setIsInitializing] = useState(() => Boolean(readAuthSession()?.accessToken));

  const persistSession = useCallback((nextSession) => {
    const normalized = writeAuthSession(nextSession);
    setSession(normalized);
    return normalized;
  }, []);

  const logout = useCallback(() => {
    clearAuthSession();
    setSession(null);
  }, []);

  const refreshMe = useCallback(async () => {
    const current = readAuthSession();
    if (!current?.accessToken) {
      logout();
      return null;
    }

    const response = await getMe({
      authToken: current.accessToken,
      tenantKey: current.currentTenantKey,
    });
    const user = getUserFromMeResponse(response);
    if (!user) {
      logout();
      return null;
    }

    return persistSession(normalizeAuthSession({ ...current, user }, current.currentTenantKey));
  }, [logout, persistSession]);

  useEffect(() => {
    let cancelled = false;

    const hydrate = async () => {
      const stored = readAuthSession();
      if (!stored?.accessToken) {
        if (!cancelled) setIsInitializing(false);
        return;
      }

      try {
        const refreshed = await refreshMe();
        if (!cancelled && refreshed) setSession(refreshed);
      } catch {
        if (!cancelled) logout();
      } finally {
        if (!cancelled) setIsInitializing(false);
      }
    };

    hydrate();

    return () => {
      cancelled = true;
    };
  }, [logout, refreshMe]);

  const login = useCallback(
    async (payload) => {
      const response = await loginRequest(payload);
      const nextSession = normalizeAuthSession(response?.data || {});
      return persistSession(nextSession);
    },
    [persistSession],
  );

  const selectTenant = useCallback((tenantKey) => {
    const updated = updateCurrentTenantKey(tenantKey);
    if (updated) setSession(updated);
    return updated;
  }, []);

  const value = useMemo(() => {
    const tenants = session?.user?.tenants || [];
    const currentTenant =
      tenants.find((tenant) => tenant.tenantKey === session?.currentTenantKey) ||
      tenants[0] ||
      null;

    return {
      session,
      user: session?.user || null,
      tenants,
      currentTenant,
      currentTenantKey: currentTenant?.tenantKey || session?.currentTenantKey || '',
      isAuthenticated: Boolean(session?.accessToken),
      isInitializing,
      login,
      logout,
      refreshMe,
      selectTenant,
    };
  }, [isInitializing, login, logout, refreshMe, selectTenant, session]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
