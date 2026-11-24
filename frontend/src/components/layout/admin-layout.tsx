'use client';

import { useState, type ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  BookOpen,
  FileText,
  Users,
  BarChart3,
  HelpCircle,
  PieChart,
  TrendingUp,
  GraduationCap,
  Menu,
  X,
} from 'lucide-react';

import { Header } from '@/components/layout/header';
import { Logo } from '@/components/ui/logo';
import { cn } from '@/lib/utils';

export interface AdminLayoutProps {
  children: ReactNode;
}

const navItems = [
  { href: '/admin', label: '仪表盘', icon: LayoutDashboard },
  { href: '/admin/knowledge', label: '知识库', icon: BookOpen },
  { href: '/admin/documents', label: '文档管理', icon: FileText },
  { href: '/admin/users', label: '用户管理', icon: Users },
  { href: '/admin/stats', label: '数据统计', icon: BarChart3 },
  { href: '/admin/faq', label: 'FAQ', icon: HelpCircle },
  { href: '/admin/analytics', label: '分析', icon: PieChart },
  { href: '/admin/metrics', label: '评价指标', icon: TrendingUp },
];

/**
 * 管理端布局。
 * 左侧导航栏 + 右侧主内容区，移动端支持折叠。
 */
export function AdminLayout({ children }: AdminLayoutProps) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const isActive = (href: string) =>
    href === '/admin' ? pathname === '/admin' : pathname.startsWith(href);

  const sidebar = (
    <div className="flex h-full flex-col bg-gray-900 text-gray-300">
      {/* Logo 区 */}
      <div className="flex h-16 items-center gap-2.5 border-b border-gray-800 px-6">
        <Logo size="sm" />
        <span className="text-base font-semibold text-white">管理后台</span>
      </div>

      {/* 导航项 */}
      <nav className="flex-1 overflow-y-auto custom-scrollbar p-3">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const active = isActive(item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
                    active
                      ? 'bg-primary-600 text-white shadow-sm'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  )}
                >
                  <item.icon
                    className={cn(
                      'h-4 w-4 transition-transform duration-200 group-hover:scale-110',
                      active && 'text-white'
                    )}
                  />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* 返回前台 */}
      <div className="border-t border-gray-800 p-3">
        <Link
          href="/dashboard"
          className="flex items-center gap-3 rounded-md px-3 py-2.5 text-sm text-gray-400 transition-colors hover:bg-gray-800 hover:text-white"
        >
          <GraduationCap className="h-4 w-4" />
          返回学生端
        </Link>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      <Header onMenuClick={() => setSidebarOpen(true)} />

      <div className="flex flex-1 overflow-hidden">
        {/* 桌面端侧边栏 */}
        <aside className="hidden w-60 shrink-0 md:block">{sidebar}</aside>

        {/* 移动端抽屉 */}
        {sidebarOpen && (
          <div className="fixed inset-0 z-50 md:hidden">
            <div
              className="absolute inset-0 bg-gray-900/50 backdrop-blur-sm animate-fade-in"
              onClick={() => setSidebarOpen(false)}
            />
            <aside className="absolute left-0 top-0 h-full w-64 animate-slide-in-left">
              <button
                type="button"
                className="absolute right-3 top-3 z-10 rounded p-1 text-gray-400 hover:bg-gray-800"
                onClick={() => setSidebarOpen(false)}
                aria-label="关闭"
              >
                <X className="h-5 w-5" />
              </button>
              {sidebar}
            </aside>
          </div>
        )}

        {/* 主内容区 */}
        <main className="flex-1 overflow-y-auto custom-scrollbar">
          <div className="mx-auto max-w-7xl p-4 md:p-6">{children}</div>
        </main>
      </div>
    </div>
  );
}

export default AdminLayout;
