'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  BookOpen,
  FileText,
  ChevronRight,
  Loader2,
  Inbox,
  FileSearch,
} from 'lucide-react';

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Modal } from '@/components/ui/modal';
import { Spinner } from '@/components/ui/loading';
import { Button } from '@/components/ui/button';
import { documentApi } from '@/lib/api';
import { useKnowledgeStore } from '@/store/use-knowledge-store';
import type { Document, KnowledgeBase } from '@/types';
import { formatDateTime, formatFileSize } from '@/lib/utils';

const fileTypeColor: Record<string, string> = {
  pdf: 'bg-error-50 text-error-600',
  docx: 'bg-primary-50 text-primary-600',
  txt: 'bg-gray-100 text-gray-600',
};

export default function KnowledgePage() {
  const router = useRouter();
  const { knowledgeBases, isLoading, fetchKnowledgeBases } = useKnowledgeStore();
  const [selectedKb, setSelectedKb] = useState<KnowledgeBase | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);

  useEffect(() => {
    void fetchKnowledgeBases();
  }, [fetchKnowledgeBases]);

  const openDocuments = async (kb: KnowledgeBase) => {
    setSelectedKb(kb);
    setDocuments([]);
    setLoadingDocs(true);
    try {
      const res = await documentApi.list(kb.id, 1, 50);
      // 响应拦截器已拆包 response.data，res 即 PaginatedResponse 对象
      setDocuments(res.items ?? []);
    } catch {
      setDocuments([]);
    } finally {
      setLoadingDocs(false);
    }
  };

  const openSummary = (doc: Document) => {
    setSelectedKb(null);
    router.push(`/dashboard/summary?doc_id=${doc.id}`);
  };

  return (
    <div className="h-full overflow-y-auto custom-scrollbar">
      <div className="mx-auto max-w-5xl p-4 md:p-6">
        {/* 页头 */}
        <div className="mb-6">
          <h1 className="flex items-center gap-2 text-xl font-bold text-gray-900">
            <BookOpen className="h-5 w-5 text-primary-600" />
            知识库浏览
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            浏览校园公开知识库，查看文档与智能总结。
          </p>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-16">
            <Spinner label="加载知识库..." />
          </div>
        ) : knowledgeBases.length === 0 ? (
          <Card bodyPadding={false} className="flex flex-col items-center justify-center py-16">
            <Inbox className="mb-2 h-10 w-10 text-gray-300" />
            <p className="text-sm text-gray-400">暂无可浏览的知识库</p>
          </Card>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {knowledgeBases.map((kb) => (
              <Card
                key={kb.id}
                hoverable
                bodyPadding={false}
                className="cursor-pointer p-5"
                onClick={() => openDocuments(kb)}
              >
                <div className="flex items-start gap-3">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
                    <BookOpen className="h-5 w-5" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="truncate font-semibold text-gray-900">
                        {kb.name}
                      </h3>
                      <ChevronRight className="h-4 w-4 shrink-0 text-gray-400" />
                    </div>
                    <p className="mt-1 line-clamp-2 text-sm text-gray-500">
                      {kb.description || '暂无描述'}
                    </p>
                    <div className="mt-3 flex items-center gap-2">
                      <Badge variant="info">
                        <FileText className="mr-1 h-3 w-3" />
                        {kb.document_count ?? 0} 篇文档
                      </Badge>
                      {kb.is_public && <Badge variant="success">公开</Badge>}
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* 文档列表弹窗 */}
      <Modal
        open={!!selectedKb}
        onClose={() => setSelectedKb(null)}
        title={selectedKb?.name ? `${selectedKb.name} · 文档列表` : '文档列表'}
        size="lg"
      >
        {loadingDocs ? (
          <div className="flex items-center justify-center py-10 text-gray-500">
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            加载文档...
          </div>
        ) : documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <Inbox className="mb-2 h-8 w-8 text-gray-300" />
            <p className="text-sm text-gray-400">该知识库暂无文档</p>
          </div>
        ) : (
          <ul className="space-y-2">
            {documents.map((doc) => (
              <li
                key={doc.id}
                className="group flex items-center gap-3 rounded-lg border border-gray-100 p-3 transition-colors hover:border-primary-200 hover:bg-primary-50/40"
              >
                <span
                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-xs font-medium uppercase ${
                    fileTypeColor[doc.file_type] || fileTypeColor.txt
                  }`}
                >
                  {doc.file_type}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-gray-900">
                    {doc.filename}
                  </p>
                  <p className="mt-0.5 flex items-center gap-2 text-xs text-gray-400">
                    <span>{formatFileSize(doc.size)}</span>
                    <span>·</span>
                    <span>{formatDateTime(doc.uploaded_at)}</span>
                    {doc.status === 'completed' && (
                      <span className="text-success-600">已处理</span>
                    )}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => openSummary(doc)}
                  leftIcon={<FileSearch className="h-3.5 w-3.5" />}
                >
                  查看总结
                </Button>
              </li>
            ))}
          </ul>
        )}
      </Modal>
    </div>
  );
}
