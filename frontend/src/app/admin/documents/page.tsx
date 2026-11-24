'use client';

import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  FileText,
  Upload,
  RefreshCw,
  Trash2,
  AlertTriangle,
} from 'lucide-react';

import { DocumentTable } from '@/components/admin/document-table';
import { UploadModal } from '@/components/admin/upload-modal';
import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/modal';
import { Spinner } from '@/components/ui/loading';
import { documentApi, knowledgeApi } from '@/lib/api';
import type { Document, KnowledgeBase } from '@/types';

function DocumentsManageInner() {
  const searchParams = useSearchParams();
  const kbIdParam = searchParams.get('kb_id');

  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKbId, setSelectedKbId] = useState<number | null>(null);
  const [loadingKb, setLoadingKb] = useState(true);

  const [documents, setDocuments] = useState<Document[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [uploadOpen, setUploadOpen] = useState(false);

  // 批量删除
  const [batchOpen, setBatchOpen] = useState(false);
  const [batchDeleting, setBatchDeleting] = useState(false);

  // 单个删除
  const [reindexingId, setReindexingId] = useState<number | null>(null);

  // 轮询定时器引用
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 拉取知识库列表
  const fetchKnowledgeBases = useCallback(async () => {
    setLoadingKb(true);
    try {
      const res = await knowledgeApi.list();
      const items = res.items || [];
      setKnowledgeBases(items);
      // 优先使用 URL 传入的 kb_id，否则取第一个
      const paramId = kbIdParam ? Number(kbIdParam) : NaN;
      if (Number.isFinite(paramId) && items.some((k) => k.id === paramId)) {
        setSelectedKbId(paramId);
      } else if (items.length > 0) {
        setSelectedKbId(items[0].id);
      }
    } catch {
      setKnowledgeBases([]);
    } finally {
      setLoadingKb(false);
    }
  }, [kbIdParam]);

  useEffect(() => {
    void fetchKnowledgeBases();
  }, [fetchKnowledgeBases]);

  // 拉取文档列表
  const fetchDocuments = useCallback(async () => {
    if (selectedKbId == null) {
      setDocuments([]);
      setTotal(0);
      return;
    }
    setLoadingDocs(true);
    setError(null);
    try {
      const res = await documentApi.list(selectedKbId, page, pageSize);
      setDocuments(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载文档失败');
      setDocuments([]);
      setTotal(0);
    } finally {
      setLoadingDocs(false);
    }
  }, [selectedKbId, page, pageSize]);

  useEffect(() => {
    void fetchDocuments();
  }, [fetchDocuments]);

  // 当有 processing 状态的文档时，每 5 秒轮询刷新
  useEffect(() => {
    const hasProcessing = documents.some((d) => d.status === 'processing');
    if (hasProcessing && selectedKbId != null) {
      pollTimerRef.current = setTimeout(() => {
        void fetchDocuments();
      }, 5000);
    }
    return () => {
      if (pollTimerRef.current) {
        clearTimeout(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, [documents, selectedKbId, fetchDocuments]);

  // 切换知识库时重置分页与选择
  useEffect(() => {
    setPage(1);
    setSelectedIds([]);
  }, [selectedKbId]);

  const handleUpload = async (file: File, onProgress: (p: number) => void) => {
    if (selectedKbId == null) throw new Error('请先选择知识库');
    await documentApi.upload(selectedKbId, file, onProgress);
  };

  const handleUploaded = () => {
    void fetchDocuments();
  };

  const handleDelete = async (doc: Document) => {
    try {
      await documentApi.remove(doc.id);
      void fetchDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败');
      throw err;
    }
  };

  const handleReindex = async (doc: Document) => {
    setReindexingId(doc.id);
    setError(null);
    try {
      await documentApi.reindex(doc.id);
      void fetchDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : '重新索引失败');
    } finally {
      setReindexingId(null);
    }
  };

  const confirmBatchDelete = async () => {
    if (selectedIds.length === 0) return;
    setBatchDeleting(true);
    setError(null);
    try {
      await Promise.all(selectedIds.map((id) => documentApi.remove(id)));
      setSelectedIds([]);
      setBatchOpen(false);
      void fetchDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : '批量删除失败');
    } finally {
      setBatchDeleting(false);
    }
  };

  const selectedKb = knowledgeBases.find((k) => k.id === selectedKbId);

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-gray-900">
            <FileText className="h-5 w-5 text-primary-600" />
            文档管理
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            上传、查看、重新索引与删除知识库文档。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            leftIcon={<RefreshCw className="h-4 w-4" />}
            onClick={fetchDocuments}
            disabled={loadingDocs || selectedKbId == null}
          >
            刷新
          </Button>
          <Button
            leftIcon={<Upload className="h-4 w-4" />}
            onClick={() => setUploadOpen(true)}
            disabled={selectedKbId == null}
          >
            上传文档
          </Button>
        </div>
      </div>

      {/* 知识库选择器 */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        {loadingKb ? (
          <Spinner label="加载知识库..." />
        ) : knowledgeBases.length === 0 ? (
          <p className="text-sm text-gray-400">
            暂无知识库，请先到「知识库管理」创建。
          </p>
        ) : (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-gray-700">
              选择知识库：
            </span>
            <div className="flex flex-wrap gap-2">
              {knowledgeBases.map((kb) => (
                <button
                  key={kb.id}
                  type="button"
                  onClick={() => setSelectedKbId(kb.id)}
                  className={
                    'inline-flex items-center rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ' +
                    (selectedKbId === kb.id
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50')
                  }
                >
                  {kb.name}
                  <span className="ml-1 text-gray-400">
                    ({kb.document_count ?? 0})
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 批量操作栏 */}
      {selectedIds.length > 0 && (
        <div className="flex items-center justify-between rounded-md bg-primary-50 px-4 py-2.5 text-sm">
          <span className="text-primary-700">
            已选择 <span className="font-semibold">{selectedIds.length}</span>{' '}
            个文档
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedIds([])}
            >
              取消选择
            </Button>
            <Button
              variant="danger"
              size="sm"
              leftIcon={<Trash2 className="h-4 w-4" />}
              onClick={() => setBatchOpen(true)}
            >
              批量删除
            </Button>
          </div>
        </div>
      )}

      {error && (
        <div className="rounded-md bg-error-50 px-4 py-3 text-sm text-error-600">
          {error}
        </div>
      )}

      {/* 文档表格 */}
      {selectedKb ? (
        <DocumentTable
          documents={documents}
          loading={loadingDocs || reindexingId !== null}
          selectedIds={selectedIds}
          onSelectChange={setSelectedIds}
          onDelete={handleDelete}
          onReindex={handleReindex}
          page={page}
          pageSize={pageSize}
          total={total}
          onPageChange={setPage}
        />
      ) : (
        <div className="flex items-center justify-center rounded-lg border border-gray-200 bg-white py-16 text-sm text-gray-400">
          {loadingKb ? '加载中...' : '请先选择一个知识库'}
        </div>
      )}

      {/* 上传弹窗 */}
      <UploadModal
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onUpload={handleUpload}
        onUploaded={handleUploaded}
      />

      {/* 批量删除确认 */}
      <Modal
        open={batchOpen}
        onClose={() => setBatchOpen(false)}
        title="批量删除文档"
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setBatchOpen(false)}>
              取消
            </Button>
            <Button
              variant="danger"
              loading={batchDeleting}
              onClick={confirmBatchDelete}
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
            确定删除选中的{' '}
            <span className="font-medium text-gray-900">
              {selectedIds.length}
            </span>{' '}
            个文档吗？此操作将同时移除所有切片，不可恢复。
          </p>
        </div>
      </Modal>
    </div>
  );
}

export default function DocumentsManagePage() {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center py-16">
          <Spinner label="加载中..." />
        </div>
      }
    >
      <DocumentsManageInner />
    </Suspense>
  );
}
