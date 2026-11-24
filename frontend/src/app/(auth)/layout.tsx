import type { ReactNode } from 'react';

/**
 * 认证页面布局。
 * 居中卡片式布局，配以柔和的渐变背景装饰。
 */
export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="relative flex min-h-screen items-center justify-center bg-gray-50 px-4 py-10">
      {/* 背景装饰 */}
      <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute -left-40 -top-40 h-96 w-96 rounded-full bg-primary-100 blur-3xl" />
        <div className="absolute -right-40 bottom-0 h-96 w-96 rounded-full bg-primary-50 blur-3xl" />
      </div>
      {children}
    </div>
  );
}
