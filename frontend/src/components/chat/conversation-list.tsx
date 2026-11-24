'use client';

import { Plus, MessageSquare, Trash2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/loading';
import type { ChatSession } from '@/types';
import { cn, formatRelativeTime, truncate } from '@/lib/utils';

export interface ConversationListProps {
  /** 会话列表 */
  sessions: ChatSession[];
  /** 当前选中的会话 ID */
  currentSessionId?: number | null;
  /** 选择会话 */
  onSelect?: (id: number) => void;
  /** 删除会话 */
  onDelete?: (id: number) => void;
  /** 新建会话 */
  onNew?: () => void;
  /** 是否加载中 */
  loading?: boolean;
  /** 空状态文案 */
  emptyText?: string;
  className?: string;
}

/**
 * 对话历史列表（可复用）。
 * 用于侧边栏、移动端抽屉或独立的历史页面。
 */
export function ConversationList({
  sessions,
  currentSessionId,
  onSelect,
  onDelete,
  onNew,
  loading = false,
  emptyText = '暂无对话记录',
  className,
}: ConversationListProps) {
  return (
    <div className={cn('flex h-full flex-col', className)}>
      {onNew && (
        <div className="p-3">
          <Button
            className="w-full"
            leftIcon={<Plus className="h-4 w-4" />}
            onClick={onNew}
          >
            新建对话
          </Button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto custom-scrollbar px-3 pb-3">
        {loading ? (
          <div className="flex justify-center py-6">
            <Spinner size="sm" label="加载中..." />
          </div>
        ) : sessions.length === 0 ? (
          <div className="px-2 py-6 text-center">
            <MessageSquare className="mx-auto mb-2 h-6 w-6 text-gray-300" />
            <p className="text-xs text-gray-400">{emptyText}</p>
          </div>
        ) : (
          <ul className="space-y-1">
            {sessions.map((session) => {
              const active = currentSessionId === session.id;
              const selectable = session.id > 0;
              return (
                <li key={session.id}>
                  <div
                    className={cn(
                      'group flex cursor-pointer items-center justify-between gap-2 rounded-md px-3 py-2 text-sm transition-colors hover:bg-gray-100',
                      active && 'bg-primary-50 text-primary-700'
                    )}
                    onClick={() => selectable && onSelect?.(session.id)}
                  >
                    <div className="min-w-0 flex-1">
                      <p
                        className={cn(
                          'truncate',
                          active ? 'font-medium text-primary-700' : 'text-gray-700'
                        )}
                      >
                        {truncate(session.title || '新对话', 22)}
                      </p>
                      <p className="text-xs text-gray-400">
                        {formatRelativeTime(session.updated_at)}
                      </p>
                    </div>

                    {selectable && onDelete && (
                      <button
                        type="button"
                        className="shrink-0 rounded p-1 text-gray-400 opacity-0 transition-opacity hover:bg-error-50 hover:text-error-500 group-hover:opacity-100"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDelete(session.id);
                        }}
                        aria-label="删除对话"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

export default ConversationList;
