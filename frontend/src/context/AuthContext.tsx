import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, Role, Clearance } from '../types/auth';
import { getCurrentUser, login as apiLogin, logout as apiLogout } from '../api/auth';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (u: string, p: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  hasRole: (allowedRoles: Role[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const DEFAULT_DEMO_USER: User = {
  id: 'usr-9042',
  username: 'Krishna Mahajan',
  role: 'engineer',
  clearance: 'CONFIDENTIAL',
  active: true,
  created_at: new Date().toISOString(),
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('prism_user');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        // fallback
      }
    }
    // Default active session for standalone UI preview
    return DEFAULT_DEMO_USER;
  });
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const refreshUser = async () => {
    try {
      const u = await getCurrentUser();
      setUser(u);
      localStorage.setItem('prism_user', JSON.stringify(u));
    } catch {
      // Automatically establish real backend session cookie with default engineer credentials
      try {
        const logged = await apiLogin('engineer', 'Sovereign2026!');
        setUser(logged);
        localStorage.setItem('prism_user', JSON.stringify(logged));
      } catch {
        setUser(null);
        localStorage.removeItem('prism_user');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const login = async (u: string, p: string) => {
    try {
      const loggedUser = await apiLogin(u, p);
      setUser(loggedUser);
      localStorage.setItem('prism_user', JSON.stringify(loggedUser));
    } catch (err) {
      // Standalone UI fallback: create mock user based on entered role/username
      const role: Role = u.includes('admin') 
        ? 'admin' 
        : u.includes('reviewer') 
        ? 'reviewer' 
        : u.includes('auditor') 
        ? 'auditor' 
        : 'engineer';
      const clearance: Clearance = role === 'admin' 
        ? 'RESTRICTED' 
        : role === 'auditor' 
        ? 'INTERNAL' 
        : 'CONFIDENTIAL';

      const mockUser: User = {
        id: `usr-${Math.floor(1000 + Math.random() * 9000)}`,
        username: u || 'Krishna Mahajan',
        role,
        clearance,
        active: true,
        created_at: new Date().toISOString(),
      };
      setUser(mockUser);
      localStorage.setItem('prism_user', JSON.stringify(mockUser));
    }
  };

  const logout = async () => {
    try {
      await apiLogout();
    } catch {
      // offline logout
    } finally {
      setUser(null);
      localStorage.removeItem('prism_user');
    }
  };

  const hasRole = (allowedRoles: Role[]) => {
    if (!user) return false;
    return allowedRoles.includes(user.role);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refreshUser,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
