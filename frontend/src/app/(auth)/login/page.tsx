'use client';

import { Suspense, useEffect, useState, type FormEvent } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  User as UserIcon,
  Lock,
  ArrowRight,
  UserCircle2,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Logo } from '@/components/ui/logo';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/store/use-auth-store';

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const login = useAuthStore((s) => s.login);

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [guestLoading, setGuestLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError('请输入用户名和密码');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await authApi.login({
        username: username.trim(),
        password,
      });
      login(res.user, res.access_token, res.refresh_token);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleGuest = async () => {
    setError(null);
    setGuestLoading(true);
    try {
      const res = await authApi.guest();
      login(res.user, res.access_token, res.refresh_token);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : '访客登录失败');
    } finally {
      setGuestLoading(false);
    }
  };

  // 处理 query 中的 mode：register 跳转注册页，guest 直接以访客身份登录
  useEffect(() => {
    const mode = searchParams.get('mode');
    if (mode === 'register') {
      router.replace('/register');
    } else if (mode === 'guest') {
      void handleGuest();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, router]);

  return (
    <div className="w-full max-w-md">
      {/* 标题 */}
      <div className="mb-8 text-center">
        <div className="mb-5 flex justify-center">
          <Logo size="md" />
        </div>
        <h1 className="text-2xl font-bold">
          <span className="bg-gradient-to-r from-primary-600 to-primary-400 bg-clip-text text-transparent">
            欢迎回来
          </span>
        </h1>
        <p className="mt-2 text-sm text-gray-500">
          登录启明校园智能问答，开启智能问答之旅
        </p>
      </div>

      <Card bodyPadding={false} className="p-6">
        <form onSubmit={handleLogin} className="space-y-4">
          {error && (
            <div
              className="rounded-md bg-error-50 px-3 py-2 text-sm text-error-600"
              role="alert"
            >
              {error}
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
              autoComplete="username"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
              密码
            </label>
            <Input
              type="password"
              value={password}
              onChange={setPassword}
              placeholder="请输入密码"
              leftIcon={<Lock className="h-4 w-4" />}
              autoComplete="current-password"
            />
          </div>

          <Button
            type="submit"
            className="w-full"
            loading={loading}
            rightIcon={<ArrowRight className="h-4 w-4" />}
          >
            登录
          </Button>

          <Button
            type="button"
            variant="secondary"
            className="w-full"
            onClick={handleGuest}
            loading={guestLoading}
            leftIcon={<UserCircle2 className="h-4 w-4" />}
          >
            访客登录
          </Button>
        </form>
      </Card>

      <p className="mt-6 text-center text-sm text-gray-500">
        还没有账号？
        <Link
          href="/register"
          className="font-medium text-primary-600 hover:text-primary-500"
        >
          立即注册
        </Link>
      </p>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginContent />
    </Suspense>
  );
}
