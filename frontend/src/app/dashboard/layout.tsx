'use client';

import { useEffect, useState, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';

import { UserLayout } from '@/components/layout/user-layout';
import { LoadingOverlay } from '@/components/ui/loading';
import { useAuthStore } from '@/store/use-auth-store';

/**
 * 学生端布局。
 * 包裹所有 /dashboard/* 页面，负责登录校验并套用 UserLayout 外壳。
 */
export default function DashboardLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [hydrated, setHydrated] = useState(false);

  // 等待持久化 store 完成水合
  useEffect(() => {
    setHydrated(true);
  }, []);

  // 未登录跳转登录页
  useEffect(() => {
    if (hydrated && !isAuthenticated) {
      router.replace('/login');
    }
  }, [hydrated, isAuthenticated, router]);

  if (!hydrated || !isAuthenticated) {
    return <LoadingOverlay visible label="正在加载..." />;
  }

  return <UserLayout>{children}</UserLayout>;
}
