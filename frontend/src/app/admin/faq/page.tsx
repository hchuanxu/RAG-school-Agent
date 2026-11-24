'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  HelpCircle,
  Sparkles,
  RefreshCw,
  FileQuestion,
} from 'lucide-react';

import { FaqList } from '@/components/admin/faq-list';
import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/modal';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Spinner } from '@/components/ui/loading';
import { faqApi } from '@/lib/api';
import type { FAQ, FAQStatus } from '@/types';

interface EditForm {
  question: string;
  answer: string;
}

export default function FaqManagePage() {
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 生成 FAQ
  const [generateOpen, setGenerateOpen] = useState(false);
  const [threshold, setThreshold] = useState('3');
  const [generating, setGenerating] = useState(false);
  const [generateResult, setGenerateResult] = useState<string | null>(null);

  // 编辑
  const [editTarget, setEditTarget] = useState<FAQ | null>(null);
  const [editForm, setEditForm] = useState<EditForm>({
    question: '',
    answer: '',
  });
  const [editSubmitting, setEditSubmitting] = useState(false);

  // 操作中
  const [actingId, setActingId] = useState<number | null>(null);

  const fetchFaqs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // 一次拉取较大数量，由组件本地筛选状态
      const res = await faqApi.list(undefined, 1, 200);
      setFaqs(res.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载 FAQ 失败');
      setFaqs([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchFaqs();
  }, [fetchFaqs]);

  const stats = useMemo(() => {
    const draft = faqs.filter((f) => f.status === 'pending').length;
    const published = faqs.filter((f) => f.status === 'published').length;
    const rejected = faqs.filter((f) => f.status === 'rejected').length;
    return { total: faqs.length, draft, published, rejected };
  }, [faqs]);

  const openEdit = (faq: FAQ) => {
    setEditTarget(faq);
    setEditForm({ question: faq.question, answer: faq.answer });
    setEditSubmitting(false);
  };

  const handleEditSubmit = async () => {
    if (!editTarget) return;
    if (!editForm.question.trim() || !editForm.answer.trim()) {
      setError('问题和答案均不能为空');
      return;
    }
    setEditSubmitting(true);
    setError(null);
    try {
      const updated = await faqApi.update(editTarget.id, {
        question: editForm.question.trim(),
        answer: editForm.answer.trim(),
      });
      setFaqs((prev) =>
        prev.map((f) => (f.id === updated.id ? updated : f))
      );
      setEditTarget(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败');
    } finally {
      setEditSubmitting(false);
    }
  };

  const handlePublish = async (faq: FAQ) => {
    setActingId(faq.id);
    setError(null);
    try {
      const updated = await faqApi.publish(faq.id);
      setFaqs((prev) =>
        prev.map((f) => (f.id === updated.id ? updated : f))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : '发布失败');
    } finally {
      setActingId(null);
    }
  };

  const handleReject = async (faq: FAQ) => {
    setActingId(faq.id);
    setError(null);
    try {
      const updated = await faqApi.reject(faq.id);
      setFaqs((prev) =>
        prev.map((f) => (f.id === updated.id ? updated : f))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : '拒绝失败');
    } finally {
      setActingId(null);
    }
  };

  const handleDelete = async (faq: FAQ) => {
    setActingId(faq.id);
    setError(null);
    try {
      await faqApi.remove(faq.id);
      setFaqs((prev) => prev.filter((f) => f.id !== faq.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败');
      throw err;
    } finally {
      setActingId(null);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setGenerateResult(null);
    setError(null);
    try {
      const thr = Number(threshold);
      const res = await faqApi.generate(
        Number.isFinite(thr) && thr > 0 ? { threshold: thr } : {}
      );
      setGenerateResult(`成功生成 ${res.generated_count} 条 FAQ`);
      void fetchFaqs();
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成 FAQ 失败');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-gray-900">
            <HelpCircle className="h-5 w-5 text-primary-600" />
            FAQ 管理
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            基于高频问题自动生成 FAQ，审核发布后供学生端使用。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            leftIcon={<RefreshCw className="h-4 w-4" />}
            onClick={fetchFaqs}
            disabled={loading}
          >
            刷新
          </Button>
          <Button
            leftIcon={<Sparkles className="h-4 w-4" />}
            onClick={() => {
              setGenerateResult(null);
              setGenerateOpen(true);
            }}
          >
            生成 FAQ
          </Button>
        </div>
      </div>

      {/* 统计信息 */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="text-xs text-gray-500">FAQ 总数</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">
            {stats.total}
          </p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="text-xs text-gray-500">待审核</p>
          <p className="mt-1 text-2xl font-bold text-warning-600">
            {stats.draft}
          </p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="text-xs text-gray-500">已发布</p>
          <p className="mt-1 text-2xl font-bold text-success-600">
            {stats.published}
          </p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="text-xs text-gray-500">已拒绝</p>
          <p className="mt-1 text-2xl font-bold text-error-600">
            {stats.rejected}
          </p>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-error-50 px-4 py-3 text-sm text-error-600">
          {error}
        </div>
      )}

      {/* FAQ 列表 */}
      {loading && faqs.length === 0 ? (
        <div className="flex justify-center py-16">
          <Spinner label="加载 FAQ..." />
        </div>
      ) : faqs.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-gray-200 bg-white py-16 text-center">
          <FileQuestion className="mb-2 h-10 w-10 text-gray-300" />
          <p className="text-sm text-gray-400">暂无 FAQ</p>
          <Button
            size="sm"
            className="mt-4"
            leftIcon={<Sparkles className="h-4 w-4" />}
            onClick={() => setGenerateOpen(true)}
          >
            生成第一批 FAQ
          </Button>
        </div>
      ) : (
        <FaqList
          items={faqs}
          loading={actingId !== null && loading}
          onEdit={openEdit}
          onPublish={handlePublish}
          onReject={handleReject}
          onDelete={handleDelete}
        />
      )}

      {/* 生成 FAQ 弹窗 */}
      <Modal
        open={generateOpen}
        onClose={() => !generating && setGenerateOpen(false)}
        title="生成 FAQ"
        footer={
          <>
            <Button
              variant="ghost"
              onClick={() => setGenerateOpen(false)}
              disabled={generating}
            >
              {generateResult ? '关闭' : '取消'}
            </Button>
            {!generateResult && (
              <Button
                loading={generating}
                leftIcon={<Sparkles className="h-4 w-4" />}
                onClick={handleGenerate}
              >
                开始生成
              </Button>
            )}
          </>
        }
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            系统将基于近期高频问题自动归纳生成 FAQ 草稿，生成后可在列表中审核发布。
          </p>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
              最低提问次数阈值
            </label>
            <Input
              type="text"
              value={threshold}
              onChange={setThreshold}
              placeholder="如 3"
            />
            <p className="mt-1 text-xs text-gray-400">
              仅对提问次数 ≥ 该阈值的问题进行生成
            </p>
          </div>
          {generateResult && (
            <div className="rounded-md bg-success-50 px-3 py-2 text-sm text-success-600">
              {generateResult}
            </div>
          )}
        </div>
      </Modal>

      {/* 编辑 FAQ 弹窗 */}
      <Modal
        open={!!editTarget}
        onClose={() => setEditTarget(null)}
        title="编辑 FAQ"
        size="lg"
        footer={
          <>
            <Button variant="ghost" onClick={() => setEditTarget(null)}>
              取消
            </Button>
            <Button
              loading={editSubmitting}
              onClick={handleEditSubmit}
            >
              保存
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
              问题 <span className="text-error-500">*</span>
            </label>
            <Input
              value={editForm.question}
              onChange={(v) =>
                setEditForm((f) => ({ ...f, question: v }))
              }
              placeholder="FAQ 问题"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
              答案 <span className="text-error-500">*</span>
            </label>
            <Textarea
              value={editForm.answer}
              onChange={(v) => setEditForm((f) => ({ ...f, answer: v }))}
              placeholder="FAQ 答案"
              rows={6}
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}
