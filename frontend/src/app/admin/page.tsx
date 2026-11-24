'use client';

import { useEffect, useState } from 'react';
import {
  MessageSquare,
  BookOpen,
  Users,
  CalendarClock,
} from 'lucide-react';

import { StatsCard } from '@/components/admin/stats-card';
import { TrendCharts } from '@/components/admin/trend-charts';
import { HotQuestionsTable } from '@/components/admin/hot-questions-table';
import { analyticsApi, statsApi } from '@/lib/api';
import type {
  DashboardStats,
  HotQuestion,
  IntentDistribution,
  TrendData,
} from '@/types';

interface DashboardData {
  stats: DashboardStats | null;
  trend: TrendData | null;
  intent: IntentDistribution | null;
  hot: HotQuestion[];
  hotTotal: number;
}

export default function AdminDashboardPage() {
  const [data, setData] = useState<DashboardData>({
    stats: null,
    trend: null,
    intent: null,
    hot: [],
    hotTotal: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [stats, trend, intent, hot] = await Promise.all([
          statsApi.dashboard().catch(() => null),
          analyticsApi.trends('daily', { days: 7 }).catch(() => null),
          analyticsApi.intentDistribution('week').catch(() => null),
          analyticsApi.hotQuestions('week', 5).catch(() => null),
        ]);
        if (cancelled) return;
        setData({
          stats,
          trend,
          intent,
          hot: hot?.items ?? [],
          hotTotal: hot?.total ?? 0,
        });
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : '加载数据失败');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const { stats, trend, intent, hot, hotTotal } = data;

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div>
        <h1 className="text-xl font-bold text-gray-900">仪表盘</h1>
        <p className="mt-1 text-sm text-gray-500">
          启明校园智能问答运行概览，实时掌握使用情况。
        </p>
      </div>

      {error && (
        <div className="rounded-md bg-error-50 px-4 py-3 text-sm text-error-600">
          {error}
        </div>
      )}

      {/* 统计卡片行 */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="总对话数"
          value={loading ? '-' : stats?.total_questions ?? 0}
          icon={MessageSquare}
          color="primary"
        />
        <StatsCard
          title="知识库数"
          value={loading ? '-' : stats?.total_knowledge_bases ?? 0}
          icon={BookOpen}
          color="info"
        />
        <StatsCard
          title="用户数"
          value={loading ? '-' : stats?.total_users ?? 0}
          change={stats?.users_change}
          changeLabel="较上周"
          icon={Users}
          color="success"
        />
        <StatsCard
          title="今日提问"
          value={loading ? '-' : stats?.today_questions ?? 0}
          change={stats?.questions_change}
          changeLabel="较昨日"
          icon={CalendarClock}
          color="warning"
        />
      </div>

      {/* 趋势图表 */}
      <TrendCharts
        trend={trend ?? undefined}
        intent={intent ?? undefined}
        loading={loading}
        show={['trend', 'intent']}
      />

      {/* 热门问题 TOP5 */}
      <HotQuestionsTable
        items={hot}
        total={hotTotal}
        loading={loading}
        period="week"
      />
    </div>
  );
}
