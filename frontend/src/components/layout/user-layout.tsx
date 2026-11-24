'use client';

import { useEffect, useState, type ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import {
  MessageSquare,
  Plus,
  Trash2,
  BookOpen,
  Clock,
  Settings,
  X,
  Pencil,
  Check,
} from 'lucide-react';

import { Header } from '@/components/layout/header';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/store/use-auth-store';
import { useChatStore } from '@/store/use-chat-store';
import { cn, formatRelativeTime, truncate } from '@/lib/utils';

export interface UserLayoutProps {
  children: ReactNode;
}

const navItems = [
  { href: '/dashboard', label: '对话', icon: MessageSquare },
  { href: '/dashboard/knowledge', label: '知识库', icon: BookOpen },
  { href: '/dashboard/history', label: '历史记录', icon: Clock },
  { href: '/dashboard/settings', label: '设置', icon: Settings },
];

/**
 * 学生端布局。
 * 左侧对话/导航侧边栏 + 右侧主内容区，移动端支持汉堡菜单。
 */
export function UserLayout({ children }: UserLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated } = useAuthStore();
  const { sessions, currentSessionId, fetchSessions, createSession, switchSession, deleteSession, renameSession } =
    useChatStore();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState('');

  // 已登录用户拉取会话列表
  useEffect(() => {
    if (isAuthenticated) {
      fetchSessions();
    }
  }, [isAuthenticated, fetchSessions]);

  // 路径变化时关闭侧边栏
  useEffect(() => {
    setSidebarOpen(false);
  }, []);

  const handleNewChat = () => {
    createSession();
    router.push('/dashboard');
  };

  const handleSelectSession = (id: number) => {
    switchSession(id);
    router.push('/dashboard');
  };

  const handleDeleteSession = async (id: number) => {
    await deleteSession(id);
  };

  const handleStartRename = (id: number, currentTitle: string) => {
    setEditingId(id);
    setEditingTitle(currentTitle);
  };

  const handleConfirmRename = async () => {
    if (editingId !== null && editingTitle.trim()) {
      await renameSession(editingId, editingTitle.trim());
    }
    setEditingId(null);
    setEditingTitle('');
  };

  const handleCancelRename = () => {
    setEditingId(null);
    setEditingTitle('');
  };

  const sidebarContent = (
    <div className="flex h-full flex-col">
      {/* 新建对话按钮 */}
      <div className="p-3">
        <Button className="w-full" leftIcon={<Plus className="h-4 w-4" />} onClick={handleNewChat}>
          新建对话
        </Button>
      </div>

      {/* 导航项 */}
      <nav className="px-3 pb-2">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const active =
              item.href === '/dashboard'
                ? pathname === '/dashboard'
                : pathname.startsWith(item.href);
            return (
              <li key={item.href}>
                <button
                  type="button"
                  onClick={() => router.push(item.href)}
                  className={cn(
                    'group flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200',
                    active
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  )}
                >
                  <item.icon
                    className={cn(
                      'h-4 w-4 transition-transform duration-200 group-hover:scale-110',
                      active && 'text-primary-600'
                    )}
                  />
                  {item.label}
                  {active && (
                    <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary-500" />
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* 对话列表 */}
      <div className="flex-1 overflow-y-auto custom-scrollbar px-3">
        <p className="px-2 py-2 text-xs font-medium uppercase tracking-wide text-gray-400">
          历史对话
        </p>
        {sessions.length === 0 ? (
          <p className="px-2 py-4 text-center text-xs text-gray-400">
            暂无对话记录
          </p>
        ) : (
          <ul className="space-y-1">
            {sessions.map((session) => (
              <li key={session.id}>
                {editingId === session.id ? (
                  /* 行内重命名编辑模式 */
                  <div className="flex items-center gap-1 rounded-md bg-gray-50 px-2 py-1">
                    <input
                      autoFocus
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleConfirmRename();
                        if (e.key === 'Escape') handleCancelRename();
                      }}
                      className="min-w-0 flex-1 rounded border border-primary-300 bg-white px-2 py-1 text-sm outline-none focus:border-primary-500"
                      placeholder="输入新名称"
                    />
                    <button
                      type="button"
                      onClick={handleConfirmRename}
                      className="shrink-0 rounded p-1 text-primary-600 hover:bg-primary-50"
                      aria-label="确认"
                    >
                      <Check className="h-3.5 w-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={handleCancelRename}
                      className="shrink-0 rounded p-1 text-gray-400 hover:bg-gray-100"
                      aria-label="取消"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ) : (
                  <div
                    className={cn(
                      'group flex cursor-pointer items-center justify-between gap-2 rounded-md px-3 py-2 text-sm transition-colors hover:bg-gray-100',
                      currentSessionId === session.id && 'bg-primary-50 text-primary-700'
                    )}
                    onClick={() => session.id > 0 && handleSelectSession(session.id)}
                  >
                    <div className="min-w-0 flex-1">
                      <p className="truncate">
                        {truncate(session.title || '新对话', 18)}
                      </p>
                      <p className="text-xs text-gray-400">
                        {formatRelativeTime(session.updated_at)}
                      </p>
                    </div>
                    {session.id > 0 && (
                      <div className="flex shrink-0 items-center opacity-0 transition-opacity group-hover:opacity-100">
                        <button
                          type="button"
                          className="rounded p-1 text-gray-400 hover:bg-primary-50 hover:text-primary-600"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStartRename(session.id, session.title || '新对话');
                          }}
                          aria-label="重命名"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                        <button
                          type="button"
                          className="rounded p-1 text-gray-400 hover:bg-error-50 hover:text-error-500"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteSession(session.id);
                          }}
                          aria-label="删除对话"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      <Header onMenuClick={() => setSidebarOpen(true)} />

      <div className="flex flex-1 overflow-hidden">
        {/* 桌面端侧边栏 */}
        <aside className="hidden w-64 shrink-0 border-r border-gray-200 bg-white md:block">
          {sidebarContent}
        </aside>

        {/* 移动端抽屉 */}
        {sidebarOpen && (
          <div className="fixed inset-0 z-50 md:hidden">
            <div
              className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm animate-fade-in"
              onClick={() => setSidebarOpen(false)}
            />
            <aside className="absolute left-0 top-0 h-full w-72 bg-white shadow-xl animate-slide-in-left">
              <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
                <span className="font-semibold text-gray-900">导航</span>
                <button
                  type="button"
                  className="rounded p-1 text-gray-400 hover:bg-gray-100"
                  onClick={() => setSidebarOpen(false)}
                  aria-label="关闭"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              {sidebarContent}
            </aside>
          </div>
        )}

        {/* 主内容区 */}
        <main className="flex-1 overflow-hidden">{children}</main>
      </div>
    </div>
  );
}

export default UserLayout;
