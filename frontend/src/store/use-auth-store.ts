'use client';

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

import type { User } from '@/types';

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;

  login: (user: User, token: string, refreshToken?: string) => void;
  logout: () => void;
  setUser: (user: User) => void;
  setToken: (token: string, refreshToken?: string) => void;
}

/**
 * 认证状态管理。
 * 通过 zustand persist 中间件持久化到 localStorage。
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,

      login: (user, token, refreshToken) => {
        set({
          user,
          token,
          refreshToken: refreshToken ?? null,
          isAuthenticated: true,
        });
        if (typeof window !== 'undefined') {
          localStorage.setItem('campus_access_token', token);
          if (refreshToken) {
            localStorage.setItem('campus_refresh_token', refreshToken);
          }
        }
      },

      logout: () => {
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
        });
        if (typeof window !== 'undefined') {
          localStorage.removeItem('campus_access_token');
          localStorage.removeItem('campus_refresh_token');
        }
      },

      setUser: (user) => set({ user }),

      setToken: (token, refreshToken) => {
        set({ token, refreshToken: refreshToken ?? null, isAuthenticated: true });
        if (typeof window !== 'undefined') {
          localStorage.setItem('campus_access_token', token);
          if (refreshToken) {
            localStorage.setItem('campus_refresh_token', refreshToken);
          }
        }
      },
    }),
    {
      name: 'campus-auth-store',
      storage: createJSONStorage(() => {
        if (typeof window === 'undefined') {
          // SSR 环境下返回 noop storage
          return {
            getItem: () => null,
            setItem: () => undefined,
            removeItem: () => undefined,
          };
        }
        return localStorage;
      }),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

export default useAuthStore;
