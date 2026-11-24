'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Clock, Trash2, MessageSquare, Inbox, AlertTriangle } from 'lucide-react';

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/loading';
import { Modal } from '@/components/ui/modal';
import { useChatStore } from '@/store/use-chat-store';
import type { ChatSession } from '@/types';
import { formatRelativeTime, formatDateTime } from '@/lib/utils';

interface SessionGroup {
  label: string;
  items: ChatSession[];
}

function groupSessions(sessions: ChatSession[]): SessionGroup[] {
  const today: ChatSession[] = [];
  const yesterday: ChatSession[] = [];
  const earlier: ChatSession[] = [];

  const now = new Date();
  const startOfToday = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate()
  ).getTime();
  const startOfYesterday = startOfToday - 24 * 60 * 60 * 1000;

  for (const s of sessions) {
    const t = new Date(s.updated_at).getTime();
    if (t >= startOfToday) today.push(s);
    else if (t >= startOfYesterday) yesterday.push(s);
    else earlier.push(s);
  }

  return [
    { label: '今天', items: today },
    { label: '昨天', items: yesterday },
    { label: '更早', items: earlier },
  ].filter((g) => g.items.length > 0);
}

export default function HistoryPage() {
  const router = useRouter();
  const {
    sessions,
    isLoadingSessions,
    fetchSessions,
    switchSession,
    deleteSession,
  } = useChatStore();

  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    void fetchSessions();
  }, [fetchSessions]);

  const groups = useMemo(() => groupSessions(sessions), [sessions]);
  const pendingDelete = sessions.find((s) => s.id === deleteId) || null;

  const handleOpen = (id: number) => {
    void switchSession(id);
    router.push('/dashboard');
  };

  const handleConfirmDelete = async () => {
    if (deleteId == null) return;
    setDeleting(true);
    try {
      await deleteSession(deleteId);
      setDeleteId(null);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto custom-scrollbar">
      <div className="mx-auto max-w-3xl p-4 md:p-6">
        {/* 页头 */}
        <div className="mb-6">
          <h1 className="flex items-center gap-2 text-xl font-bold text-gray-900">
            <Clock className="h-5 w-5 text-primary-600" />
            历史记录
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            查看你的全部对话历史，点击可继续对话。
          </p>
        </div>

        {isLoadingSessions && sessions.length === 0 ? (
          <div className="flex justify-center py-16">
            <Spinner label="加载历史记录..." />
          </div>
        ) : groups.length === 0 ? (
          <Card bodyPadding={false} className="flex flex-col items-center justify-center py-16">
            <Inbox className="mb-2 h-10 w-10 text-gray-300" />
            <p className="text-sm text-gray-400">暂无对话历史</p>
            <Button
              variant="secondary"
              size="sm"
              className="mt-4"
              onClick={() => router.push('/dashboard')}
            >
              开始新对话
            </Button>
          </Card>
        ) : (
          <div className="space-y-6">
            {groups.map((group) => (
              <div key={group.label}>
                <h2 className="mb-2 px-1 text-xs font-medium uppercase tracking-wide text-gray-400">
                  {group.label}
                </h2>
                <Card bodyPadding={false} className="divide-y divide-gray-100">
                  {group.items.map((session) => (
                    <div
                      key={session.id}
                      className="group flex cursor-pointer items-center gap-3 px-4 py-3 transition-colors hover:bg-gray-50"
                      onClick={() => session.id > 0 && handleOpen(session.id)}
                    >
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
                        <MessageSquare className="h-4 w-4" />
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-gray-900">
                          {session.title || '新对话'}
                        </p>
                        <p className="mt-0.5 text-xs text-gray-400">
                          {formatRelativeTime(session.updated_at)}
                          <span className="mx-1">·</span>
                          {formatDateTime(session.updated_at)}
                        </p>
                      </div>
                      <Badge variant="default" className="shrink-0">
                        {session.message_count ?? 0} 条
                      </Badge>
                      <button
                        type="button"
                        className="shrink-0 rounded p-1.5 text-gray-400 opacity-0 transition-opacity hover:bg-error-50 hover:text-error-500 group-hover:opacity-100"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (session.id > 0) setDeleteId(session.id);
                        }}
                        aria-label="删除"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </Card>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 删除确认 */}
      <Modal
        open={deleteId != null}
        onClose={() => setDeleteId(null)}
        title="删除对话"
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setDeleteId(null)}>
              取消
            </Button>
            <Button
              variant="danger"
              loading={deleting}
              onClick={handleConfirmDelete}
            >
              确认删除
            </Button>
          </>
        }
      >
        <div className="flex items-start gap-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-error-50 text-error-500">
            <AlertTriangle className="h-5 w-5" />
          </span>
          <p className="text-sm text-gray-600">
            确定删除对话
            <span className="font-medium text-gray-900">
              「{pendingDelete?.title || '新对话'}」
            </span>
            吗？删除后不可恢复。
          </p>
        </div>
      </Modal>
    </div>
  );
}
