'use client';

import { useMemo, useState } from 'react';
import {
  Pencil,
  Send,
  XCircle,
  Trash2,
  HelpCircle,
  Inbox,
  AlertTriangle,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/modal';
import { Spinner } from '@/components/ui/loading';
import type { FAQ, FAQStatus } from '@/types';
import { cn, formatDateTime } from '@/lib/utils';

export interface FaqListProps {
  items: FAQ[];
  loading?: boolean;
  onEdit?: (faq: FAQ) => void;
  onPublish?: (faq: FAQ) => void;
  onReject?: (faq: FAQ) => void;
  onDelete?: (faq: FAQ) => void;
  /** 当前状态筛选 */
  status?: FAQStatus | 'all';
  onStatusChange?: (status: FAQStatus | 'all') => void;
}

const statusConfig: Record<
  FAQStatus,
  { label: string; variant: 'default' | 'success' | 'error' | 'warning' }
> = {
  pending: { label: '待审核', variant: 'warning' },
  published: { label: '已发布', variant: 'success' },
  rejected: { label: '已拒绝', variant: 'error' },
};

const filterOptions: { value: FAQStatus | 'all'; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'pending', label: '待审核' },
  { value: 'published', label: '已发布' },
  { value: 'rejected', label: '已拒绝' },
];

/**
 * 管理端 FAQ 列表。
 * 卡片式展示，支持状态筛选与编辑/发布/拒绝/删除操作。
 */
export function FaqList({
  items,
  loading = false,
  onEdit,
  onPublish,
  onReject,
  onDelete,
  status = 'all',
  onStatusChange,
}: FaqListProps) {
  const [activeStatus, setActiveStatus] = useState<FAQStatus | 'all'>(status);
  const [pendingDelete, setPendingDelete] = useState<FAQ | null>(null);
  const [deleting, setDeleting] = useState(false);

  const filtered = useMemo(() => {
    if (activeStatus === 'all') return items;
    return items.filter((it) => it.status === activeStatus);
  }, [items, activeStatus]);

  const handleStatus = (s: FAQStatus | 'all') => {
    setActiveStatus(s);
    onStatusChange?.(s);
  };

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    setDeleting(true);
    try {
      await onDelete?.(pendingDelete);
      setPendingDelete(null);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div>
      {/* 状态筛选 */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        {filterOptions.map((opt) => {
          const count =
            opt.value === 'all'
              ? items.length
              : items.filter((it) => it.status === opt.value).length;
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => handleStatus(opt.value)}
              className={cn(
                'inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors',
                activeStatus === opt.value
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
              )}
            >
              {opt.label}
              <span
                className={cn(
                  'inline-flex h-4 min-w-4 items-center justify-center rounded-full px-1 text-[10px]',
                  activeStatus === opt.value
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-200 text-gray-600'
                )}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* 列表 */}
      {loading ? (
        <div className="flex items-center justify-center rounded-lg border border-gray-200 bg-white py-16">
          <Spinner label="加载 FAQ..." />
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-gray-200 bg-white py-16 text-center text-gray-400">
          <Inbox className="mb-2 h-10 w-10 text-gray-300" />
          <p className="text-sm">暂无 FAQ</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {filtered.map((faq) => {
            const cfg = statusConfig[faq.status];
            return (
              <div
                key={faq.id}
                className="flex flex-col rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="flex items-start justify-between gap-2">
                  <h3 className="flex items-start gap-2 font-semibold text-gray-900">
                    <HelpCircle className="mt-0.5 h-4 w-4 shrink-0 text-primary-600" />
                    <span className="line-clamp-2">{faq.question}</span>
                  </h3>
                  <Badge variant={cfg.variant}>{cfg.label}</Badge>
                </div>

                <p className="mt-3 line-clamp-3 text-sm text-gray-600">
                  {faq.answer}
                </p>

                {faq.source_documents && faq.source_documents.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {faq.source_documents.slice(0, 3).map((src, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500"
                      >
                        {src}
                      </span>
                    ))}
                    {faq.source_documents.length > 3 && (
                      <span className="text-[10px] text-gray-400">
                        +{faq.source_documents.length - 3}
                      </span>
                    )}
                  </div>
                )}

                <div className="mt-4 flex items-center justify-between border-t border-gray-100 pt-3">
                  <span className="text-xs text-gray-400">
                    {faq.hit_count != null && (
                      <span className="mr-2">命中 {faq.hit_count} 次</span>
                    )}
                    {formatDateTime(faq.updated_at || faq.created_at)}
                  </span>
                  <div className="flex items-center gap-1">
                    {faq.status === 'pending' && (
                      <>
                        <button
                          type="button"
                          onClick={() => onPublish?.(faq)}
                          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-success-600 transition-colors hover:bg-success-50"
                        >
                          <Send className="h-3.5 w-3.5" />
                          发布
                        </button>
                        <button
                          type="button"
                          onClick={() => onReject?.(faq)}
                          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-warning-600 transition-colors hover:bg-warning-50"
                        >
                          <XCircle className="h-3.5 w-3.5" />
                          拒绝
                        </button>
                      </>
                    )}
                    <button
                      type="button"
                      onClick={() => onEdit?.(faq)}
                      className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-gray-600 transition-colors hover:bg-gray-100"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                      编辑
                    </button>
                    <button
                      type="button"
                      onClick={() => setPendingDelete(faq)}
                      className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-error-600 transition-colors hover:bg-error-50"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 删除确认 */}
      <Modal
        open={!!pendingDelete}
        onClose={() => setPendingDelete(null)}
        title="删除 FAQ"
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setPendingDelete(null)}>
              取消
            </Button>
            <Button
              variant="danger"
              loading={deleting}
              onClick={confirmDelete}
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
            确定删除该 FAQ 吗？删除后不可恢复。
          </p>
        </div>
      </Modal>
    </div>
  );
}

export default FaqList;
