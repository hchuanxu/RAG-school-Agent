'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, BookOpen, Inbox, AlertTriangle, RefreshCw } from 'lucide-react';

import { KbCard } from '@/components/admin/kb-card';
import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/modal';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Spinner } from '@/components/ui/loading';
import { knowledgeApi } from '@/lib/api';
import type { KnowledgeBase } from '@/types';

interface KbFormData {
  name: string;
  description: string;
  is_public: boolean;
}

const emptyForm: KbFormData = { name: '', description: '', is_public: true };

export default function KnowledgeManagePage() {
  const router = useRouter();
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 弹窗状态
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<KnowledgeBase | null>(null);
  const [form, setForm] = useState<KbFormData>(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // 删除
  const [pendingDelete, setPendingDelete] = useState<KnowledgeBase | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await knowledgeApi.list();
      setKnowledgeBases(res.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载知识库失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchList();
  }, [fetchList]);

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setFormError(null);
    setFormOpen(true);
  };

  const openEdit = (kb: KnowledgeBase) => {
    setEditing(kb);
    setForm({
      name: kb.name,
      description: kb.description || '',
      is_public: kb.is_public,
    });
    setFormError(null);
    setFormOpen(true);
  };

  const handleSubmit = async () => {
    if (!form.name.trim()) {
      setFormError('请输入知识库名称');
      return;
    }
    setSubmitting(true);
    setFormError(null);
    try {
      const payload = {
        name: form.name.trim(),
        description: form.description.trim() || undefined,
        is_public: form.is_public,
      };
      if (editing) {
        await knowledgeApi.update(editing.id, payload);
      } else {
        await knowledgeApi.create(payload);
      }
      setFormOpen(false);
      void fetchList();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : '保存失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleView = (kb: KnowledgeBase) => {
    // 点击卡片跳转文档管理，并预选该知识库
    router.push(`/admin/documents?kb_id=${kb.id}`);
  };

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    setDeleting(true);
    try {
      await knowledgeApi.remove(pendingDelete.id);
      setPendingDelete(null);
      void fetchList();
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-gray-900">
            <BookOpen className="h-5 w-5 text-primary-600" />
            知识库管理
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            管理校园知识库，点击卡片可进入文档管理。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            leftIcon={<RefreshCw className="h-4 w-4" />}
            onClick={fetchList}
            disabled={loading}
          >
            刷新
          </Button>
          <Button
            leftIcon={<Plus className="h-4 w-4" />}
            onClick={openCreate}
          >
            创建知识库
          </Button>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-error-50 px-4 py-3 text-sm text-error-600">
          {error}
        </div>
      )}

      {/* 列表 */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner label="加载知识库..." />
        </div>
      ) : knowledgeBases.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-gray-200 bg-white py-16 text-center">
          <Inbox className="mb-2 h-10 w-10 text-gray-300" />
          <p className="text-sm text-gray-400">暂无知识库</p>
          <Button
            size="sm"
            className="mt-4"
            leftIcon={<Plus className="h-4 w-4" />}
            onClick={openCreate}
          >
            创建第一个知识库
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {knowledgeBases.map((kb) => (
            <KbCard
              key={kb.id}
              kb={kb}
              onView={handleView}
              onEdit={openEdit}
              onDelete={setPendingDelete}
            />
          ))}
        </div>
      )}

      {/* 创建/编辑弹窗 */}
      <Modal
        open={formOpen}
        onClose={() => setFormOpen(false)}
        title={editing ? '编辑知识库' : '创建知识库'}
        footer={
          <>
            <Button variant="ghost" onClick={() => setFormOpen(false)}>
              取消
            </Button>
            <Button loading={submitting} onClick={handleSubmit}>
              {editing ? '保存修改' : '创建'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {formError && (
            <div className="rounded-md bg-error-50 px-3 py-2 text-sm text-error-600">
              {formError}
            </div>
          )}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
              知识库名称 <span className="text-error-500">*</span>
            </label>
            <Input
              value={form.name}
              onChange={(v) => setForm((f) => ({ ...f, name: v }))}
              placeholder="如：学生手册"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
              描述
            </label>
            <Textarea
              value={form.description}
              onChange={(v) => setForm((f) => ({ ...f, description: v }))}
              placeholder="简要描述知识库内容"
              rows={3}
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={form.is_public}
              onChange={(e) =>
                setForm((f) => ({ ...f, is_public: e.target.checked }))
              }
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            公开访问（学生端可见）
          </label>
        </div>
      </Modal>

      {/* 删除确认 */}
      <Modal
        open={!!pendingDelete}
        onClose={() => setPendingDelete(null)}
        title="删除知识库"
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
          <div className="text-sm text-gray-600">
            <p>
              确定删除知识库
              <span className="font-medium text-gray-900">
                「{pendingDelete?.name}」
              </span>
              吗？
            </p>
            <p className="mt-1 text-xs text-error-500">
              该操作将一并删除其下所有文档与切片，不可恢复。
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
}
