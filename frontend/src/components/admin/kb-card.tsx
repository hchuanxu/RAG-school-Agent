'use client';

import { BookOpen, FileText, Pencil, Trash2, Eye } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import type { KnowledgeBase } from '@/types';

export interface KbCardProps {
  kb: KnowledgeBase;
  onView?: (kb: KnowledgeBase) => void;
  onEdit?: (kb: KnowledgeBase) => void;
  onDelete?: (kb: KnowledgeBase) => void;
}

/**
 * 管理端知识库卡片。
 * 展示名称、描述、文档数与状态，提供查看/编辑/删除操作。
 */
export function KbCard({ kb, onView, onEdit, onDelete }: KbCardProps) {
  const isActive = kb.status !== 'inactive';

  return (
    <div className="flex flex-col rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start gap-3">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
          <BookOpen className="h-5 w-5" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <h3 className="truncate font-semibold text-gray-900">{kb.name}</h3>
            <Badge variant={isActive ? 'success' : 'default'}>
              {isActive ? '启用' : '停用'}
            </Badge>
          </div>
          <p className="mt-1 line-clamp-2 text-sm text-gray-500">
            {kb.description || '暂无描述'}
          </p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <Badge variant="info">
          <FileText className="mr-1 h-3 w-3" />
          {kb.document_count ?? 0} 篇文档
        </Badge>
        {kb.is_public ? (
          <Badge variant="success">公开</Badge>
        ) : (
          <Badge variant="default">私有</Badge>
        )}
      </div>

      <div className="mt-4 flex items-center justify-end gap-2 border-t border-gray-100 pt-3">
        <button
          type="button"
          onClick={() => onView?.(kb)}
          className="inline-flex items-center gap-1 rounded-md px-2.5 py-1.5 text-xs font-medium text-primary-600 transition-colors hover:bg-primary-50"
        >
          <Eye className="h-3.5 w-3.5" />
          查看
        </button>
        <button
          type="button"
          onClick={() => onEdit?.(kb)}
          className="inline-flex items-center gap-1 rounded-md px-2.5 py-1.5 text-xs font-medium text-gray-600 transition-colors hover:bg-gray-100"
        >
          <Pencil className="h-3.5 w-3.5" />
          编辑
        </button>
        <button
          type="button"
          onClick={() => onDelete?.(kb)}
          className="inline-flex items-center gap-1 rounded-md px-2.5 py-1.5 text-xs font-medium text-error-600 transition-colors hover:bg-error-50"
        >
          <Trash2 className="h-3.5 w-3.5" />
          删除
        </button>
      </div>
    </div>
  );
}

export default KbCard;
