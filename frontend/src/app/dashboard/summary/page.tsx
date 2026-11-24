'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { FileText, ArrowLeft, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/loading';
import { SummaryView } from '@/components/summary/summary-view';
import { documentApi } from '@/lib/api';
import type { Document } from '@/types';

function SummaryPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const docIdParam = searchParams.get('doc_id');
  const docId = docIdParam ? Number(docIdParam) : NaN;

  const [document, setDocument] = useState<Document | null>(null);
  const [loadingDoc, setLoadingDoc] = useState(false);

  useEffect(() => {
    if (!Number.isFinite(docId) || docId <= 0) return;
    let cancelled = false;
    setLoadingDoc(true);
    documentApi
      .detail(docId)
      .then((res) => {
        if (!cancelled) setDocument(res);
      })
      .catch(() => {
        // 忽略，仍展示总结内容
      })
      .finally(() => {
        if (!cancelled) setLoadingDoc(false);
      });
    return () => {
      cancelled = true;
    };
  }, [docId]);

  if (!Number.isFinite(docId) || docId <= 0) {
    return (
      <div className="h-full overflow-y-auto custom-scrollbar">
        <div className="mx-auto max-w-3xl p-4 md:p-6">
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <FileText className="mb-3 h-10 w-10 text-gray-300" />
            <p className="text-sm text-gray-500">未指定有效的文档 ID</p>
            <Button
              variant="secondary"
              size="sm"
              className="mt-4"
              onClick={() => router.push('/dashboard/knowledge')}
            >
              返回知识库
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto custom-scrollbar">
      <div className="mx-auto max-w-3xl p-4 md:p-6">
        {/* 页头 */}
        <div className="mb-6">
          <Button
            variant="ghost"
            size="sm"
            className="mb-3 -ml-2"
            leftIcon={<ArrowLeft className="h-4 w-4" />}
            onClick={() => router.push('/dashboard/knowledge')}
          >
            返回知识库
          </Button>

          <div className="flex items-start gap-3">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
              <FileText className="h-5 w-5" />
            </span>
            <div className="min-w-0">
              <h1 className="truncate text-xl font-bold text-gray-900">
                {loadingDoc ? (
                  <Loader2 className="inline h-5 w-5 animate-spin text-gray-400" />
                ) : (
                  document?.filename || '文档总结'
                )}
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                智能生成的文档摘要、重点条例与可提问考点
              </p>
            </div>
          </div>
        </div>

        {loadingDoc ? (
          <div className="flex justify-center py-16">
            <Spinner label="加载文档..." />
          </div>
        ) : (
          <SummaryView
            documentId={docId}
            onAskQuestion={(q) =>
              router.push(`/dashboard?question=${encodeURIComponent(q)}`)
            }
          />
        )}
      </div>
    </div>
  );
}

export default function SummaryPage() {
  return (
    <Suspense fallback={null}>
      <SummaryPageInner />
    </Suspense>
  );
}
