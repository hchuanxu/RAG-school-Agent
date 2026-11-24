'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { GraduationCap, LogOut, User as UserIcon, Menu, MessageSquare } from 'lucide-react';

import { Avatar } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Logo } from '@/components/ui/logo';
import { useAuthStore } from '@/store/use-auth-store';
import { cn } from '@/lib/utils';

export interface HeaderProps {
  /** 是否显示汉堡菜单按钮（移动端） */
  onMenuClick?: () => void;
  /** 右侧额外操作区 */
  extra?: React.ReactNode;
  className?: string;
}

/**
 * 顶部导航栏。
 * 包含 Logo、用户菜单、退出登录，响应式适配。
 */
export function Header({ onMenuClick, extra, className }: HeaderProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const isAdminPage = pathname?.startsWith('/admin');

  // 点击外部关闭下拉菜单
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleLogout = () => {
    logout();
    setMenuOpen(false);
    router.push('/login');
  };

  return (
    <header
      className={cn(
        'sticky top-0 z-40 flex h-16 items-center justify-between border-b border-gray-200 bg-white/80 px-4 backdrop-blur-md md:px-6',
        className
      )}
    >
      {/* 左侧：Logo + 移动端菜单按钮 */}
      <div className="flex items-center gap-3">
        {onMenuClick && (
          <button
            type="button"
            className="rounded p-1.5 text-gray-600 hover:bg-gray-100 md:hidden"
            onClick={onMenuClick}
            aria-label="菜单"
          >
            <Menu className="h-5 w-5" />
          </button>
        )}
        <Link href="/" className="flex items-center gap-2">
          <Logo
            size="sm"
            showText
            textClassName="hidden font-semibold sm:inline"
          />
        </Link>
      </div>

      {/* 中间：额外操作区 */}
      {extra && <div className="hidden flex-1 justify-center md:flex">{extra}</div>}

      {/* 右侧：用户菜单 */}
      <div className="flex items-center gap-3">
        {isAuthenticated && user ? (
          <div className="relative" ref={menuRef}>
            <button
              type="button"
              className="flex items-center gap-2 rounded-full p-1 transition-colors hover:bg-gray-100"
              onClick={() => setMenuOpen((v) => !v)}
            >
              <Avatar
                src={user.avatar}
                name={user.username}
                size="sm"
              />
              <span className="hidden text-sm font-medium text-gray-700 sm:inline">
                {user.username}
              </span>
            </button>

            {menuOpen && (
              <div className="absolute right-0 mt-2 w-48 origin-top-right rounded-lg border border-gray-200 bg-white py-1 shadow-lg animate-scale-in">
                <div className="border-b border-gray-100 px-4 py-2">
                  <p className="truncate text-sm font-medium text-gray-900">
                    {user.username}
                  </p>
                  <p className="truncate text-xs text-gray-500">
                    {user.email || '校园助手用户'}
                  </p>
                </div>
                <button
                  type="button"
                  className="flex w-full items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                  onClick={() => {
                    setMenuOpen(false);
                    router.push('/dashboard/settings');
                  }}
                >
                  <UserIcon className="h-4 w-4" />
                  个人中心
                </button>
                {user.role === 'admin' && !isAdminPage && (
                  <Link
                    href="/admin"
                    className="flex w-full items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                    onClick={() => setMenuOpen(false)}
                  >
                    <GraduationCap className="h-4 w-4" />
                    管理后台
                  </Link>
                )}
                {user.role === 'admin' && isAdminPage && (
                  <Link
                    href="/dashboard"
                    className="flex w-full items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                    onClick={() => setMenuOpen(false)}
                  >
                    <MessageSquare className="h-4 w-4" />
                    返回智能问答
                  </Link>
                )}
                <button
                  type="button"
                  className="flex w-full items-center gap-2 px-4 py-2 text-sm text-error-600 hover:bg-error-50"
                  onClick={handleLogout}
                >
                  <LogOut className="h-4 w-4" />
                  退出登录
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => router.push('/login')}>
              登录
            </Button>
            <Button size="sm" onClick={() => router.push('/login?mode=register')}>
              注册
            </Button>
          </div>
        )}
      </div>
    </header>
  );
}

export default Header;
