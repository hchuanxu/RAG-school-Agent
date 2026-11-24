'use client';

import { useState } from 'react';
import {
  ChevronDown,
  FileText,
  Loader2,
  BookOpen,
  Hash,
  Percent,
} from 'lucide-react';

import { Modal } from '@/components/ui/modal';
import { Badge } from '@/components/ui/badge';
import { citationApi } from '@/lib/api';
import type { Citation } from '@/types';
import { cn } from '@/lib/utils';

export interface CitationListProps {
  citations: Citation[];
  className?: string;
  /** 默认是否展开 */
  defaultExpanded?: boolean;
}

/**
 * 引用来源列表。
 * 折叠式展示回答所依据的文档片段，点击可查看详情。
 */
export function CitationList({
  citations,
  className,
  defaultExpanded = false,
}: CitationListProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const [active, setActive] = useState<Citation | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  if (!citations || citations.length === 0) return null;

  const handleView = async (c: Citation) => {
    setActive(c);
    if (c.citation_id) {
      setLoadingDetail(true);
      try {
        const detail = await citationApi.detail(c.citation_id);
        setActive(detail);
      } catch {
        // 拉取详情失败时保留传入的引用信息
      } finally {
        setLoadingDetail(false);
      }
    }
  };

  const similarity = (c: Citation) =>
    typeof c.similarity_score === 'number'
      ? Math.round(c.similarity_score * 100)
      : null;

  return (
    <div className={cn('mt-2', className)}>
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="inline-flex items-center gap-1 text-xs font-medium text-primary-600 transition-colors hover:text-primary-500"
      >
        <ChevronDown
          className={cn(
            'h-3.5 w-3.5 transition-transform',
            expanded && 'rotate-180'
          )}
        />
        引用来源（{citations.length}）
      </button>

      {expanded && (
        <ul className="mt-2 space-y-1.5">
          {citations.map((c, idx) => {
            const score = similarity(c);
            return (
              <li key={c.citation_id ?? idx}>
                <button
                  type="button"
                  onClick={() => handleView(c)}
                  className="flex w-full items-center gap-2 rounded-md border border-gray-200 bg-gray-50 px-2.5 py-1.5 text-left text-xs transition-colors hover:border-primary-200 hover:bg-primary-50"
                >
                  <FileText className="h-3.5 w-3.5 shrink-0 text-gray-400" />
                  <span className="min-w-0 flex-1 truncate text-gray-700">
                    {c.filename || c.file_name || `文档 ${c.document_id ?? idx + 1}`}
                  </span>
                  {c.page != null && (
                    <span className="inline-flex items-center gap-0.5 text-gray-400">
                      <Hash className="h-3 w-3" />
                      {c.page}
                    </span>
                  )}
                  {c.paragraph != null && (
                    <span className="text-gray-400">·{c.paragraph}段</span>
                  )}
                  {score != null && (
                    <Badge variant="info" outline className="shrink-0">
                      <Percent className="mr-0.5 h-3 w-3" />
                      {score}%
                    </Badge>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      )}

      {/* 详情弹窗 */}
      <Modal
        open={!!active}
        onClose={() => setActive(null)}
        title="引用详情"
        size="md"
      >
        {loadingDetail ? (
          <div className="flex items-center justify-center py-8 text-gray-500">
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            加载中...
          </div>
        ) : active ? (
          <div className="space-y-3">
            <div className="flex items-start gap-2">
              <FileText className="mt-0.5 h-4 w-4 shrink-0 text-primary-600" />
              <div className="min-w-0">
                <p className="font-medium text-gray-900">
                  {active.filename || active.file_name || `引用详情`}
                </p>
                {(active.knowledge_base_name || active.knowledge_base) && (
                  <p className="mt-0.5 inline-flex items-center gap-1 text-xs text-gray-500">
                    <BookOpen className="h-3 w-3" />
                    {active.knowledge_base_name || active.knowledge_base}
                  </p>
                )}
              </div>
            </div>

            <div className="flex flex-wrap gap-2 text-xs">
              {active.page != null && (
                <Badge variant="default">页码：{active.page}</Badge>
              )}
              {active.paragraph != null && (
                <Badge variant="default">段落：{active.paragraph}</Badge>
              )}
              {similarity(active) != null && (
                <Badge variant="info">相似度：{similarity(active)}%</Badge>
              )}
            </div>

            <div className="rounded-md bg-gray-50 p-3 text-sm leading-relaxed text-gray-700">
              {active.full_content ||
                active.content_preview ||
                '暂无详细内容'}
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
}

export default CitationList;
