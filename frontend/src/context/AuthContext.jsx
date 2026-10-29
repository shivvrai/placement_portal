/**
 * Auth context — manages JWT tokens, current user, and login/logout state.
 * All API calls that need authentication go through this context.
 */

import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { api } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }

    if (token === 'mock_token') {
      const savedRole = localStorage.getItem('mock_role') || 'student';
      setUser({
        id: "mock_id",
        email: `${savedRole}@demo.ccip`,
        first_name: "Demo",
        last_name: savedRole.toUpperCase(),
        role: savedRole,
        is_active: true
      });
      setLoading(false);
      return;
    }

    api.get('/auth/me')
      .then(res => setUser(res.data))
      .catch(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('mock_role');
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email, password, { forceMock = false } = {}) => {
    if (forceMock || import.meta.env.VITE_USE_MOCKS === 'true') {
      const role = email.includes("admin") ? "admin"
        : email.includes("recruiter") ? "recruiter"
        : email.includes("tpo") ? "tpo"
        : email.includes("faculty") ? "faculty"
        : "student";
      const mockUser = {
        id: "mock_id",
        email: email,
        first_name: "Demo",
        last_name: role.toUpperCase(),
        role: role,
        is_active: true
      };
      localStorage.setItem('access_token', 'mock_token');
      localStorage.setItem('refresh_token', 'mock_refresh');
      localStorage.setItem('mock_role', role);
      setUser(mockUser);
      return mockUser;
    }

    try {
      const res = await api.post('/auth/login', { email, password });
      localStorage.setItem('access_token', res.data.access_token);
      localStorage.setItem('refresh_token', res.data.refresh_token);

      const me = await api.get('/auth/me');
      setUser(me.data);
      return me.data;
    } catch (err) {
      if (!err.response) {
        err.isNetworkError = true;
      }
      throw err;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('mock_role');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
