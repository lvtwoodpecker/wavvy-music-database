// src/context/AuthContext.jsx
/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const storedUser = localStorage.getItem('auth_user');
      return storedUser ? JSON.parse(storedUser) : null;
    } catch (error) {
      console.error('Failed to parse stored user data:', error);
      localStorage.removeItem('auth_user');
      return null;
    }
  });
  
  const [token, setToken] = useState(() => {
    try {
      return localStorage.getItem('auth_token') || null;
    } catch (error) {
      console.error('Failed to retrieve auth token:', error);
      return null;
    }
  });
  
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    try {
      const hasToken = !!localStorage.getItem('auth_token');
      const hasUser = !!localStorage.getItem('auth_user');
      return hasToken && hasUser;
    } catch (error) {
      console.error('Failed to check authentication state:', error);
      return false;
    }
  });

  const login = (authToken, userData) => {
    setToken(authToken);
    setUser(userData);
    setIsAuthenticated(true);
    localStorage.setItem('auth_token', authToken);
    localStorage.setItem('auth_user', JSON.stringify(userData));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  };

  const value = {
    user,
    token,
    isAuthenticated,
    loading: false,
    login,
    logout,
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
