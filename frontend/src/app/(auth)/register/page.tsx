'use client';

import { useState, type FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  User as UserIcon,
  Mail,
  Lock,
  ArrowRight,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Logo } from '@/components/ui/logo';
import { authApi } from '@/lib/api';

interface FormErrors {
  username?: string;
  email?: string;
  password?: string;
  confirm?: string;
}

export default function RegisterPage() {
  const router = useRouter();

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const validate = (): boolean => {
    const next: FormErrors = {};
    if (!username.trim()) {
      next.username = '请输入用户名';
    } else if (username.trim().length < 3) {
      next.username = '用户名至少 3 个字符';
    }
    if (!email.trim()) {
      next.email = '请输入邮箱';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      next.email = '邮箱格式不正确';
    }
    if (!password) {
      next.password = '请输入密码';
    } else if (password.length < 6) {
      next.password = '密码至少 6 个字符';
    }
    if (!confirm) {
      next.confirm = '请再次输入密码';
    } else if (password !== confirm) {
      next.confirm = '两次输入的密码不一致';
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setServerError(null);
    if (!validate()) return;

    setLoading(true);
    try {
      await authApi.register({
        username: username.trim(),
        email: email.trim(),
        password,
      });
      router.push('/login?registered=1');
    } catch (err) {
      setServerError(
        err instanceof Error ? err.message : '注册失败，请稍后重试'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md">
      {/* 标题 */}
      <div className="mb-8 text-center">
        <div className="mb-5 flex justify-center">
          <Logo size="md" />
        </div>
        <h1 className="text-2xl font-bold">
          <span className="bg-gradient-to-r from-primary-600 to-primary-400 bg-clip-text text-transparent">
            创建账号
          </span>
        </h1>
        <p className="mt-2 text-sm text-gray-500">
          注册即可使用智能问答、答案溯源与文档总结
        </p>
      </div>

      <Card bodyPadding={false} className="p-6">
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          {serverError && (
            <div
              className="rounded-md bg-error-50 px-3 py-2 text-sm text-error-600"
              role="alert"
            >
              {serverError}
            </div>
          )}

          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
              用户名
            </label>
            <Input
              value={username}
              onChange={(v) => {
                setUsername(v);
                if (errors.username) setErrors((p) => ({ ...p, username: undefined }));
              }}
              placeholder="请输入用户名（至少 3 个字符）"
              leftIcon={<UserIcon className="h-4 w-4" />}
              error={errors.username}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
              邮箱
            </label>
            <Input
              type="email"
              value={email}
              onChange={(v) => {
                setEmail(v);
                if (errors.email) setErrors((p) => ({ ...p, email: undefined }));
              }}
              placeholder="请输入邮箱"
              leftIcon={<Mail className="h-4 w-4" />}
              error={errors.email}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
              密码
            </label>
            <Input
              type="password"
              value={password}
              onChange={(v) => {
                setPassword(v);
                if (errors.password) setErrors((p) => ({ ...p, password: undefined }));
              }}
              placeholder="请输入密码（至少 6 个字符）"
              leftIcon={<Lock className="h-4 w-4" />}
              error={errors.password}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
              确认密码
            </label>
            <Input
              type="password"
              value={confirm}
              onChange={(v) => {
                setConfirm(v);
                if (errors.confirm) setErrors((p) => ({ ...p, confirm: undefined }));
              }}
              placeholder="请再次输入密码"
              leftIcon={<Lock className="h-4 w-4" />}
              error={errors.confirm}
            />
          </div>

          <Button
            type="submit"
            className="w-full"
            loading={loading}
            rightIcon={<ArrowRight className="h-4 w-4" />}
          >
            注册
          </Button>
        </form>
      </Card>

      <p className="mt-6 text-center text-sm text-gray-500">
        已有账号？
        <Link
          href="/login"
          className="font-medium text-primary-600 hover:text-primary-500"
        >
          返回登录
        </Link>
      </p>
    </div>
  );
}
