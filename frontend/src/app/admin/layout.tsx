'use client';

import { useEffect, useState, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';

import { AdminLayout } from '@/components/layout/admin-layout';
import { LoadingOverlay } from '@/components/ui/loading';
import { useAuthStore } from '@/store/use-auth-store';

/**
 * 管理端布局。
 * 包裹所有 /admin/* 页面，负责登录校验与 admin 权限校验。
 * 非 admin 用户自动跳转至 /dashboard。
 */
export default function AdminRootLayout({
  children,
}: {
  children: ReactNode;
}) {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [hydrated, setHydrated] = useState(false);

  // 等待 persist store 完成水合
  useEffect(() => {
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    // 未登录跳转登录页
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }
    // 非 admin 跳转学生端
    if (user && user.role !== 'admin') {
      router.replace('/dashboard');
    }
  }, [hydrated, isAuthenticated, user, router]);

  if (!hydrated || !isAuthenticated || !user || user.role !== 'admin') {
    return <LoadingOverlay visible label="正在加载管理后台..." />;
  }

  return <AdminLayout>{children}</AdminLayout>;
}
