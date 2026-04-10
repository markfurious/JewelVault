import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tokens, setTokens] = useState({
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
  });

  useEffect(() => {
    // Check if we have tokens and fetch user info
    const initAuth = async () => {
      if (tokens.access) {
        try {
          const userData = await authApi.me();
          setUser(userData);
        } catch (error) {
          // Token might be expired, try to refresh
          if (tokens.refresh) {
            try {
              const newTokens = await authApi.refresh(tokens.refresh);
              setTokens({
                access: newTokens.access_token,
                refresh: newTokens.refresh_token,
              });
              localStorage.setItem('access_token', newTokens.access_token);
              localStorage.setItem('refresh_token', newTokens.refresh_token);
              setUser(newTokens.user);
            } catch (refreshError) {
              // Refresh failed, clear auth
              clearAuth();
            }
          } else {
            clearAuth();
          }
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const clearAuth = () => {
    setUser(null);
    setTokens({ access: null, refresh: null });
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  };

  const login = async (username, password) => {
    const data = await authApi.login(username, password);
    setTokens({
      access: data.access_token,
      refresh: data.refresh_token,
    });
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    setUser(data.user);
    return data;
  };

  const logout = () => {
    clearAuth();
  };

  const isSuperAdmin = () => {
    return user?.role === 'super_admin';
  };

  const isCompanyAdmin = () => {
    return user?.role === 'company_admin';
  };

  const isAdmin = () => {
    return user?.role === 'super_admin' || user?.role === 'company_admin';
  };

  const value = {
    user,
    loading,
    login,
    logout,
    isAdmin,
    isSuperAdmin,
    isCompanyAdmin,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
