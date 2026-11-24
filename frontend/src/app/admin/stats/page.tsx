'use client';

import { useCallback, useEffect, useState } from 'react';
import { BarChart3, CalendarClock, AlertCircle, Lightbulb } from 'lucide-react';

import { HotQuestionsTable, type TimePeriod } from '@/components/admin/hot-questions-table';
import { TrendCharts } from '@/components/admin/trend-charts';
import { Badge } from '@/components/ui/badge';
import { analyticsApi } from '@/lib/api';
import type {
  HotQuestion,
  IntentDistribution,
  InvalidAnalysis,
  TrendData,
} from '@/types';

export default function StatsPage() {
  const [period, setPeriod] = useState<TimePeriod>('week');
  const [hot, setHot] = useState<HotQuestion[]>([]);
  const [hotTotal, setHotTotal] = useState(0);
  const [trend, setTrend] = useState<TrendData | null>(null);
  const [intent, setIntent] = useState<IntentDistribution | null>(null);
  const [invalid, setInvalid] = useState<InvalidAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [hotRes, trendRes, intentRes, invalidRes] = await Promise.all([
        analyticsApi.hotQuestions(period, 20).catch(() => null),
        analyticsApi
          .trends(period === 'day' ? 'daily' : period === 'all' ? 'daily' : period === 'month' ? 'monthly' : 'weekly', {
            days: period === 'day' || period === 'all' ? 30 : undefined,
            weeks: period === 'week' ? 8 : undefined,
            months: period === 'month' ? 12 : undefined,
          })
          .catch(() => null),
        analyticsApi.intentDistribution(period).catch(() => null),
        analyticsApi.invalidAnalysis(period).catch(() => null),
      ]);
      setHot(hotRes?.items ?? []);
      setHotTotal(hotRes?.total ?? 0);
      setTrend(trendRes);
      setIntent(intentRes);
      setInvalid(invalidRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载统计数据失败');
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  const invalidRate =
    invalid && invalid.total > 0
      ? ((invalid.invalid_count / invalid.total) * 100).toFixed(1)
      : '0.0';

  return (
    <div className="space-y-6">
      {/* 页头 */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-gray-900">
            <BarChart3 className="h-5 w-5 text-primary-600" />
            数据统计
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            热门问题、提问趋势、意图分布与无效问题分析。
          </p>
        </div>
        <div className="inline-flex items-center gap-1 rounded-md border border-gray-200 bg-white px-2 py-1 text-xs text-gray-500">
          <CalendarClock className="h-3.5 w-3.5" />
          当前时间范围：
          {period === 'day'
            ? '今日'
            : period === 'week'
              ? '本周'
              : period === 'month'
                ? '本月'
                : '全部'}
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-error-50 px-4 py-3 text-sm text-error-600">
          {error}
        </div>
      )}

      {/* 趋势图表 */}
      <TrendCharts
        trend={trend ?? undefined}
        intent={intent ?? undefined}
        hotQuestions={hot}
        loading={loading}
        show={['trend', 'intent', 'hot']}
      />

      {/* 热门问题排行榜 */}
      <HotQuestionsTable
        items={hot}
        total={hotTotal}
        loading={loading}
        period={period}
        onPeriodChange={setPeriod}
      />

      {/* 无效问题分析 */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-lg border border-gray-200 bg-white p-5 lg:col-span-1">
          <h3 className="mb-3 flex items-center gap-2 font-semibold text-gray-900">
            <AlertCircle className="h-4 w-4 text-error-600" />
            无效问题概览
          </h3>
          {loading ? (
            <p className="py-6 text-center text-sm text-gray-400">加载中...</p>
          ) : invalid ? (
            <div className="space-y-3">
              <div className="rounded-md bg-error-50 px-4 py-3">
                <p className="text-xs text-error-600">无效问题数</p>
                <p className="mt-1 text-2xl font-bold text-error-700">
                  {invalid.invalid_count}
                </p>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">提问总数</span>
                <span className="font-medium text-gray-900">
                  {invalid.total}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">无效占比</span>
                <Badge variant="error">{invalidRate}%</Badge>
              </div>
            </div>
          ) : (
            <p className="py-6 text-center text-sm text-gray-400">
              暂无数据
            </p>
          )}
        </div>

        {/* 无效问题样本 */}
        <div className="rounded-lg border border-gray-200 bg-white p-5 lg:col-span-2">
          <h3 className="mb-3 font-semibold text-gray-900">无效问题样本</h3>
          {loading ? (
            <p className="py-6 text-center text-sm text-gray-400">加载中...</p>
          ) : invalid && invalid.samples.length > 0 ? (
            <ul className="space-y-2">
              {invalid.samples.slice(0, 8).map((s, i) => (
                <li
                  key={i}
                  className="rounded-md border border-gray-100 px-3 py-2"
                >
                  <p className="truncate text-sm text-gray-800">
                    {s.question}
                  </p>
                  {s.reason && (
                    <p className="mt-0.5 text-xs text-gray-400">
                      原因：{s.reason}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-6 text-center text-sm text-gray-400">
              暂无无效问题样本
            </p>
          )}
        </div>
      </div>

      {/* 优化建议 */}
      {invalid?.suggestions && invalid.suggestions.length > 0 && (
        <div className="rounded-lg border border-primary-200 bg-primary-50/50 p-5">
          <h3 className="mb-3 flex items-center gap-2 font-semibold text-primary-700">
            <Lightbulb className="h-4 w-4" />
            优化建议
          </h3>
          <ul className="space-y-2">
            {invalid.suggestions.map((s, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm text-gray-700"
              >
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary-500" />
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
