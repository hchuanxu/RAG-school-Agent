'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  Users,
  Search,
  Shield,
  UserCircle2,
  ChevronLeft,
  ChevronRight,
  Inbox,
  Ban,
  CheckCircle2,
} from 'lucide-react';

import { Avatar } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Modal } from '@/components/ui/modal';
import { Spinner } from '@/components/ui/loading';
import { userApi } from '@/lib/api';
import { useAuthStore } from '@/store/use-auth-store';
import { useDebounce } from '@/lib/hooks/use-debounce';
import type { User, UserRole } from '@/types';
import { formatDate } from '@/lib/utils';

export default function UsersManagePage() {
  const currentUser = useAuthStore((s) => s.user);
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [keyword, setKeyword] = useState('');
  const debouncedKeyword = useDebounce(keyword, 400);

  // 操作中用户 ID
  const [actingId, setActingId] = useState<number | null>(null);

  // 角色切换确认
  const [roleTarget, setRoleTarget] = useState<User | null>(null);
  const [roleSubmitting, setRoleSubmitting] = useState(false);

  // 启用/禁用确认
  const [statusTarget, setStatusTarget] = useState<User | null>(null);
  const [statusSubmitting, setStatusSubmitting] = useState(false);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await userApi.list(page, pageSize, debouncedKeyword || undefined);
      setUsers(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载用户失败');
      setUsers([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, debouncedKeyword]);

  useEffect(() => {
    void fetchUsers();
  }, [fetchUsers]);

  // 搜索时重置页码
  useEffect(() => {
    setPage(1);
  }, [debouncedKeyword]);

  const isSelf = (u: User) => currentUser?.id === u.id;

  const confirmRole = async () => {
    if (!roleTarget) return;
    const nextRole: UserRole = roleTarget.role === 'admin' ? 'user' : 'admin';
    setRoleSubmitting(true);
    setError(null);
    try {
      const updated = await userApi.updateRole(roleTarget.id, nextRole);
      setUsers((prev) =>
        prev.map((u) => (u.id === updated.id ? updated : u))
      );
      setRoleTarget(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '修改角色失败');
    } finally {
      setRoleSubmitting(false);
    }
  };

  const confirmStatus = async () => {
    if (!statusTarget) return;
    const nextActive = !statusTarget.is_active;
    setStatusSubmitting(true);
    setError(null);
    try {
      const updated = await userApi.updateStatus(statusTarget.id, nextActive);
      setUsers((prev) =>
        prev.map((u) => (u.id === updated.id ? updated : u))
      );
      setStatusTarget(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '修改状态失败');
    } finally {
      setStatusSubmitting(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div>
        <h1 className="flex items-center gap-2 text-xl font-bold text-gray-900">
          <Users className="h-5 w-5 text-primary-600" />
          用户管理
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          查看用户列表，调整角色与启用状态。
        </p>
      </div>

      {/* 搜索栏 */}
      <div className="flex items-center gap-3">
        <div className="w-full max-w-sm">
          <Input
            value={keyword}
            onChange={setKeyword}
            placeholder="搜索用户名或邮箱"
            leftIcon={<Search className="h-4 w-4" />}
          />
        </div>
        <Button
          variant="secondary"
          onClick={fetchUsers}
          disabled={loading}
        >
          刷新
        </Button>
      </div>

      {error && (
        <div className="rounded-md bg-error-50 px-4 py-3 text-sm text-error-600">
          {error}
        </div>
      )}

      {/* 用户表格 */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
        <div className="overflow-x-auto custom-scrollbar">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
              <tr>
                <th className="px-4 py-3">用户</th>
                <th className="px-4 py-3">邮箱</th>
                <th className="px-4 py-3">角色</th>
                <th className="px-4 py-3">注册时间</th>
                <th className="px-4 py-3">状态</th>
                <th className="px-4 py-3 text-right">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center">
                    <Spinner label="加载用户..." />
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12">
                    <div className="flex flex-col items-center justify-center text-center text-gray-400">
                      <Inbox className="mb-2 h-10 w-10 text-gray-300" />
                      <p className="text-sm">暂无用户</p>
                    </div>
                  </td>
                </tr>
              ) : (
                users.map((u) => {
                  const self = isSelf(u);
                  return (
                    <tr
                      key={u.id}
                      className="transition-colors hover:bg-gray-50"
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <Avatar
                            src={u.avatar}
                            name={u.username}
                            size="sm"
                          />
                          <div className="min-w-0">
                            <p className="flex items-center gap-1.5 truncate font-medium text-gray-900">
                              {u.username}
                              {self && (
                                <span className="rounded bg-primary-50 px-1 text-[10px] text-primary-600">
                                  我
                                </span>
                              )}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {u.email || '-'}
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={u.role === 'admin' ? 'info' : 'default'}
                        >
                          {u.role === 'admin' ? '管理员' : '普通用户'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {u.created_at ? formatDate(u.created_at) : '-'}
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={
                            u.is_active === false ? 'error' : 'success'
                          }
                        >
                          {u.is_active === false ? '已禁用' : '正常'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            type="button"
                            disabled={self}
                            onClick={() => {
                              setActingId(u.id);
                              setRoleTarget(u);
                            }}
                            className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-primary-600 transition-colors hover:bg-primary-50 disabled:cursor-not-allowed disabled:opacity-40"
                            title={
                              self ? '不能修改自己的角色' : '切换角色'
                            }
                          >
                            <Shield className="h-3.5 w-3.5" />
                            {u.role === 'admin' ? '降为用户' : '升为管理员'}
                          </button>
                          <button
                            type="button"
                            disabled={self}
                            onClick={() => {
                              setActingId(u.id);
                              setStatusTarget(u);
                            }}
                            className={
                              'inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40 ' +
                              (u.is_active === false
                                ? 'text-success-600 hover:bg-success-50'
                                : 'text-error-600 hover:bg-error-50')
                            }
                            title={
                              self ? '不能修改自己的状态' : '启用/禁用'
                            }
                          >
                            {u.is_active === false ? (
                              <>
                                <CheckCircle2 className="h-3.5 w-3.5" />
                                启用
                              </>
                            ) : (
                              <>
                                <Ban className="h-3.5 w-3.5" />
                                禁用
                              </>
                            )}
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
              共 <span className="font-medium text-gray-900">{total}</span>{' '}
              位用户，第 {page}/{totalPages} 页
            </p>
            <div className="flex items-center gap-1">
              <Button
                variant="secondary"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* 角色切换确认 */}
      <Modal
        open={!!roleTarget}
        onClose={() => setRoleTarget(null)}
        title="修改用户角色"
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setRoleTarget(null)}>
              取消
            </Button>
            <Button loading={roleSubmitting} onClick={confirmRole}>
              确认修改
            </Button>
          </>
        }
      >
        <div className="flex items-start gap-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary-50 text-primary-600">
            <Shield className="h-5 w-5" />
          </span>
          <div className="text-sm text-gray-600">
            <p>
              确定将用户
              <span className="font-medium text-gray-900">
                「{roleTarget?.username}」
              </span>
              的角色修改为
              <span className="font-medium text-primary-700">
                {roleTarget?.role === 'admin' ? '普通用户' : '管理员'}
              </span>
              ？
            </p>
            <p className="mt-1 text-xs text-gray-400">
              管理员可访问后台、管理知识库与用户。
            </p>
          </div>
        </div>
      </Modal>

      {/* 启用/禁用确认 */}
      <Modal
        open={!!statusTarget}
        onClose={() => setStatusTarget(null)}
        title={
          statusTarget?.is_active === false ? '启用用户' : '禁用用户'
        }
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setStatusTarget(null)}>
              取消
            </Button>
            <Button
              variant={
                statusTarget?.is_active === false ? 'primary' : 'danger'
              }
              loading={statusSubmitting}
              onClick={confirmStatus}
            >
              确认
            </Button>
          </>
        }
      >
        <div className="flex items-start gap-3">
          <span
            className={
              'flex h-9 w-9 shrink-0 items-center justify-center rounded-full ' +
              (statusTarget?.is_active === false
                ? 'bg-success-50 text-success-600'
                : 'bg-error-50 text-error-500')
            }
          >
            {statusTarget?.is_active === false ? (
              <CheckCircle2 className="h-5 w-5" />
            ) : (
              <Ban className="h-5 w-5" />
            )}
          </span>
          <p className="text-sm text-gray-600">
            {statusTarget?.is_active === false
              ? `确定启用用户「${statusTarget?.username}」？启用后用户可正常登录。`
              : `确定禁用用户「${statusTarget?.username}」？禁用后用户将无法登录。`}
          </p>
        </div>
      </Modal>

      {/* 当前 acting 状态隐藏指示，避免无提示 */}
      {actingId != null && !roleTarget && !statusTarget && null}
    </div>
  );
}
