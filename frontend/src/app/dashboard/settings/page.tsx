'use client';

import { useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { User as UserIcon, Mail, Lock, LogOut, Save, KeyRound } from 'lucide-react';

import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Avatar } from '@/components/ui/avatar';
import { Modal } from '@/components/ui/modal';
import { userApi } from '@/lib/api';
import { useAuthStore } from '@/store/use-auth-store';
import type { User } from '@/types';

export default function SettingsPage() {
  const router = useRouter();
  const { user, setUser, logout } = useAuthStore();

  // 个人信息
  const [username, setUsername] = useState(user?.username ?? '');
  const [email, setEmail] = useState(user?.email ?? '');
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileMsg, setProfileMsg] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  // 修改密码
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordMsg, setPasswordMsg] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  // 退出确认
  const [logoutOpen, setLogoutOpen] = useState(false);

  const handleProfileSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setProfileMsg(null);
    if (!username.trim()) {
      setProfileMsg({ type: 'error', text: '用户名不能为空' });
      return;
    }
    setProfileLoading(true);
    try {
      const updated = await userApi.updateProfile({
        username: username.trim(),
        email: email.trim(),
      });
      setUser(updated);
      setProfileMsg({ type: 'success', text: '个人信息已更新' });
    } catch (err) {
      setProfileMsg({
        type: 'error',
        text: err instanceof Error ? err.message : '更新失败',
      });
    } finally {
      setProfileLoading(false);
    }
  };

  const handlePasswordSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setPasswordMsg(null);
    if (!newPassword) {
      setPasswordMsg({ type: 'error', text: '请输入新密码' });
      return;
    }
    if (newPassword.length < 6) {
      setPasswordMsg({ type: 'error', text: '新密码至少 6 个字符' });
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordMsg({ type: 'error', text: '两次输入的新密码不一致' });
      return;
    }
    setPasswordLoading(true);
    try {
      // 后端 PUT /profile 支持更新密码时一并提交
      await userApi.updateProfile({
        password: newPassword,
      } as unknown as Partial<User>);
      setPasswordMsg({ type: 'success', text: '密码已修改' });
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setPasswordMsg({
        type: 'error',
        text: err instanceof Error ? err.message : '修改密码失败',
      });
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    setLogoutOpen(false);
    router.push('/login');
  };

  return (
    <div className="h-full overflow-y-auto custom-scrollbar">
      <div className="mx-auto max-w-2xl p-4 md:p-6">
        <h1 className="mb-6 flex items-center gap-2 text-xl font-bold text-gray-900">
          <UserIcon className="h-5 w-5 text-primary-600" />
          个人设置
        </h1>

        {/* 用户头像与基本信息 */}
        <Card bodyPadding={false} className="mb-4 p-5">
          <div className="flex items-center gap-4">
            <Avatar
              src={user?.avatar}
              name={user?.username}
              size="lg"
            />
            <div className="min-w-0">
              <p className="truncate font-semibold text-gray-900">
                {user?.username}
              </p>
              <p className="truncate text-sm text-gray-500">
                {user?.email || '未设置邮箱'}
              </p>
              <p className="mt-1 text-xs text-gray-400">
                角色：{user?.role === 'admin' ? '管理员' : '学生'}
              </p>
            </div>
          </div>
        </Card>

        {/* 个人信息修改 */}
        <Card title="个人信息" className="mb-4">
          <form onSubmit={handleProfileSubmit} className="space-y-4">
            {profileMsg && (
              <div
                className={`rounded-md px-3 py-2 text-sm ${
                  profileMsg.type === 'success'
                    ? 'bg-success-50 text-success-600'
                    : 'bg-error-50 text-error-600'
                }`}
                role="alert"
              >
                {profileMsg.text}
              </div>
            )}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">
                用户名
              </label>
              <Input
                value={username}
                onChange={setUsername}
                placeholder="请输入用户名"
                leftIcon={<UserIcon className="h-4 w-4" />}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">
                邮箱
              </label>
              <Input
                type="email"
                value={email}
                onChange={setEmail}
                placeholder="请输入邮箱"
                leftIcon={<Mail className="h-4 w-4" />}
              />
            </div>
            <Button
              type="submit"
              loading={profileLoading}
              leftIcon={<Save className="h-4 w-4" />}
            >
              保存修改
            </Button>
          </form>
        </Card>

        {/* 修改密码 */}
        <Card title="修改密码" className="mb-4">
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            {passwordMsg && (
              <div
                className={`rounded-md px-3 py-2 text-sm ${
                  passwordMsg.type === 'success'
                    ? 'bg-success-50 text-success-600'
                    : 'bg-error-50 text-error-600'
                }`}
                role="alert"
              >
                {passwordMsg.text}
              </div>
            )}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">
                当前密码
              </label>
              <Input
                type="password"
                value={oldPassword}
                onChange={setOldPassword}
                placeholder="请输入当前密码"
                leftIcon={<Lock className="h-4 w-4" />}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">
                新密码
              </label>
              <Input
                type="password"
                value={newPassword}
                onChange={setNewPassword}
                placeholder="至少 6 个字符"
                leftIcon={<KeyRound className="h-4 w-4" />}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">
                确认新密码
              </label>
              <Input
                type="password"
                value={confirmPassword}
                onChange={setConfirmPassword}
                placeholder="请再次输入新密码"
                leftIcon={<KeyRound className="h-4 w-4" />}
              />
            </div>
            <Button
              type="submit"
              loading={passwordLoading}
              leftIcon={<KeyRound className="h-4 w-4" />}
            >
              修改密码
            </Button>
          </form>
        </Card>

        {/* 退出登录 */}
        <Card title="账号操作">
          <Button
            variant="danger"
            leftIcon={<LogOut className="h-4 w-4" />}
            onClick={() => setLogoutOpen(true)}
          >
            退出登录
          </Button>
        </Card>
      </div>

      {/* 退出确认 */}
      <Modal
        open={logoutOpen}
        onClose={() => setLogoutOpen(false)}
        title="退出登录"
        size="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setLogoutOpen(false)}>
              取消
            </Button>
            <Button variant="danger" onClick={handleLogout}>
              确认退出
            </Button>
          </>
        }
      >
        <p className="text-sm text-gray-600">
          确定要退出当前账号吗？退出后需要重新登录。
        </p>
      </Modal>
    </div>
  );
}
