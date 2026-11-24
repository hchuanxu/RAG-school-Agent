'use client';

import { useMemo, useState } from 'react';
import {
  Trash2,
  RefreshCw,
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  Inbox,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/modal';
import { Spinner } from '@/components/ui/loading';
import type { Document, DocumentStatus } from '@/types';
import { cn, formatDateTime, formatFileSize } from '@/lib/utils';

export interface DocumentTableProps {
  documents: Document[];
  loading?: boolean;
  /** 当前选中的文档 ID（用于批量删除高亮） */
  selectedIds?: number[];
  onSelectChange?: (ids: number[]) => void;
  onDelete?: (doc: Document) => void;
  onReindex?: (doc: Document) => void;
  /** 分页 */
  page?: number;
  pageSize?: number;
  total?: number;
  onPageChange?: (page: number) => void;
}

type SortField = 'filename' | 'size' | 'uploaded_at' | 'chunk_count';
type SortOrder = 'asc' | 'desc';

const statusMap: Record<
  DocumentStatus,
  { label: string; variant: 'default' | 'success' | 'warning' | 'error' }
> = {
  pending: { label: '待处理', variant: 'default' },
  processing: { label: '处理中', variant: 'warning' },
  completed: { label: '已完成', variant: 'success' },
  failed: { label: '失败', variant: 'error' },
};

const fileTypeColor: Record<string, string> = {
  pdf: 'bg-error-50 text-error-600',
  docx: 'bg-primary-50 text-primary-600',
  txt: 'bg-gray-100 text-gray-600',
};

/**
 * 管理端文档表格。
 * 支持排序、分页、删除/重新索引操作及删除确认弹窗。
 */
export function DocumentTable({
  documents,
  loading = false,
  selectedIds = [],
  onSelectChange,
  onDelete,
  onReindex,
  page = 1,
  pageSize = 10,
  total = 0,
  onPageChange,
}: DocumentTableProps) {
  const [sortField, setSortField] = useState<SortField>('uploaded_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [pendingDelete, setPendingDelete] = useState<Document | null>(null);
  const [deleting, setDeleting] = useState(false);

  const sorted = useMemo(() => {
    const copy = [...documents];
    copy.sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case 'filename':
          cmp = a.filename.localeCompare(b.filename);
          break;
        case 'size':
          cmp = a.size - b.size;
          break;
        case 'chunk_count':
          cmp = a.chunk_count - b.chunk_count;
          break;
        case 'uploaded_at':
          cmp =
            new Date(a.uploaded_at).getTime() -
            new Date(b.uploaded_at).getTime();
          break;
      }
      return sortOrder === 'asc' ? cmp : -cmp;
    });
    return copy;
  }, [documents, sortField, sortOrder]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const allSelected =
    sorted.length > 0 && sorted.every((d) => selectedIds.includes(d.id));
  const toggleAll = () => {
    if (allSelected) {
      onSelectChange?.([]);
    } else {
      onSelectChange?.(sorted.map((d) => d.id));
    }
  };
  const toggleOne = (id: number) => {
    if (selectedIds.includes(id)) {
      onSelectChange?.(selectedIds.filter((i) => i !== id));
    } else {
      onSelectChange?.([...selectedIds, id]);
    }
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

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field)
      return <ChevronDown className="h-3 w-3 text-gray-300" />;
    return sortOrder === 'asc' ? (
      <ChevronUp className="h-3 w-3 text-primary-600" />
    ) : (
      <ChevronDown className="h-3 w-3 text-primary-600" />
    );
  };

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <div className="overflow-x-auto custom-scrollbar">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr className="text-left text-xs font-medium uppercase tracking-wide text-gray-500">
              {onSelectChange && (
                <th className="w-10 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={toggleAll}
                    className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                </th>
              )}
              <th className="px-4 py-3">
                <button
                  type="button"
                  onClick={() => toggleSort('filename')}
                  className="inline-flex items-center gap-1 hover:text-gray-700"
                >
                  文件名 <SortIcon field="filename" />
                </button>
              </th>
              <th className="px-4 py-3">
                <button
                  type="button"
                  onClick={() => toggleSort('size')}
                  className="inline-flex items-center gap-1 hover:text-gray-700"
                >
                  大小 <SortIcon field="size" />
                </button>
              </th>
              <th className="px-4 py-3">类型</th>
              <th className="px-4 py-3">状态</th>
              <th className="px-4 py-3">
                <button
                  type="button"
                  onClick={() => toggleSort('chunk_count')}
                  className="inline-flex items-center gap-1 hover:text-gray-700"
                >
                  切片数 <SortIcon field="chunk_count" />
                </button>
              </th>
              <th className="px-4 py-3">
                <button
                  type="button"
                  onClick={() => toggleSort('uploaded_at')}
                  className="inline-flex items-center gap-1 hover:text-gray-700"
                >
                  上传时间 <SortIcon field="uploaded_at" />
                </button>
              </th>
              <th className="px-4 py-3 text-right">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr>
                <td
                  colSpan={onSelectChange ? 8 : 7}
                  className="px-4 py-12 text-center"
                >
                  <Spinner label="加载文档列表..." />
                </td>
              </tr>
            ) : sorted.length === 0 ? (
              <tr>
                <td
                  colSpan={onSelectChange ? 8 : 7}
                  className="px-4 py-12"
                >
                  <div className="flex flex-col items-center justify-center text-center text-gray-400">
                    <Inbox className="mb-2 h-10 w-10 text-gray-300" />
                    <p className="text-sm">暂无文档</p>
                  </div>
                </td>
              </tr>
            ) : (
              sorted.map((doc) => {
                const status = statusMap[doc.status];
                const checked = selectedIds.includes(doc.id);
                return (
                  <tr
                    key={doc.id}
                    className={cn(
                      'transition-colors hover:bg-gray-50',
                      checked && 'bg-primary-50/50'
                    )}
                  >
                    {onSelectChange && (
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => toggleOne(doc.id)}
                          className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                      </td>
                    )}
                    <td className="max-w-xs px-4 py-3">
                      <p className="truncate font-medium text-gray-900">
                        {doc.filename}
                      </p>
                      {doc.error_message && (
                        <p className="mt-0.5 truncate text-xs text-error-500">
                          {doc.error_message}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {formatFileSize(doc.size)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={cn(
                          'inline-flex h-7 w-12 items-center justify-center rounded text-xs font-medium uppercase',
                          fileTypeColor[doc.file_type] || fileTypeColor.txt
                        )}
                      >
                        {doc.file_type}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={status.variant}>{status.label}</Badge>
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {doc.chunk_count ?? 0}
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {formatDateTime(doc.uploaded_at)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          type="button"
                          onClick={() => onReindex?.(doc)}
                          className="rounded p-1.5 text-gray-500 transition-colors hover:bg-primary-50 hover:text-primary-600"
                          aria-label="重新索引"
                          title="重新索引"
                        >
                          <RefreshCw className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => setPendingDelete(doc)}
                          className="rounded p-1.5 text-gray-500 transition-colors hover:bg-error-50 hover:text-error-600"
                          aria-label="删除"
                          title="删除"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      {total > 0 && (
        <div className="flex items-center justify-between border-t border-gray-100 px-4 py-3 text-sm">
          <p className="text-gray-500">
            共 <span className="font-medium text-gray-900">{total}</span> 条，
            第 {page}/{totalPages} 页
          </p>
          <div className="flex items-center gap-1">
            <Button
              variant="secondary"
              size="sm"
              disabled={page <= 1}
              onClick={() => onPageChange?.(page - 1)}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => onPageChange?.(page + 1)}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* 删除确认 */}
      <Modal
        open={!!pendingDelete}
        onClose={() => setPendingDelete(null)}
        title="删除文档"
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
            确定删除文档
            <span className="font-medium text-gray-900">
              「{pendingDelete?.filename}」
            </span>
            吗？删除后将同时移除所有切片，操作不可恢复。
          </p>
        </div>
      </Modal>
    </div>
  );
}

export default DocumentTable;
