'use client';

import { useCallback, useEffect, useState } from 'react';
import { PieChart, TrendingUp, AlertCircle, Database } from 'lucide-react';

import { TrendCharts } from '@/components/admin/trend-charts';
import { HotQuestionsTable, type TimePeriod } from '@/components/admin/hot-questions-table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/loading';
import { analyticsApi, knowledgeApi } from '@/lib/api';
import type {
  HotQuestion,
  IntentDistribution,
  InvalidAnalysis,
  KnowledgeBase,
  TrendData,
} from '@/types';

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<TimePeriod>('week');
  const [trend, setTrend] = useState<TrendData | null>(null);
  const [intent, setIntent] = useState<IntentDistribution | null>(null);
  const [hot, setHot] = useState<HotQuestion[]>([]);
  const [hotTotal, setHotTotal] = useState(0);
  const [invalid, setInvalid] = useState<InvalidAnalysis | null>(null);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [
        trendRes,
        intentRes,
        hotRes,
        invalidRes,
        kbRes,
      ] = await Promise.all([
        analyticsApi
          .trends(
            period === 'month'
              ? 'monthly'
              : period === 'week'
                ? 'weekly'
                : 'daily',
            {
              days: period === 'day' || period === 'all' ? 30 : undefined,
              weeks: period === 'week' ? 8 : undefined,
              months: period === 'month' ? 12 : undefined,
            }
          )
          .catch(() => null),
        analyticsApi.intentDistribution(period).catch(() => null),
        analyticsApi.hotQuestions(period, 10).catch(() => null),
        analyticsApi.invalidAnalysis(period).catch(() => null),
        knowledgeApi.list().catch(() => [] as KnowledgeBase[]),
      ]);
      setTrend(trendRes);
      setIntent(intentRes);
      setHot(hotRes?.items ?? []);
      setHotTotal(hotRes?.total ?? 0);
      setInvalid(invalidRes);
      setKnowledgeBases(Array.isArray(kbRes) ? kbRes : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载分析数据失败');
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  const totalDocs = knowledgeBases.reduce(
    (sum, kb) => sum + (kb.document_count ?? 0),
    0
  );
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
            <PieChart className="h-5 w-5 text-primary-600" />
            数据分析
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            综合分析提问趋势、意图分布、无效问题与知识库使用情况。
          </p>
        </div>
        <Button
          variant="secondary"
          onClick={fetchData}
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

      {/* 顶部概览 */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-primary-600" />
            <p className="text-sm text-gray-500">提问总数（区间）</p>
          </div>
          <p className="mt-2 text-2xl font-bold text-gray-900">
            {loading ? '-' : trend?.total ?? 0}
          </p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-error-600" />
            <p className="text-sm text-gray-500">无效问题占比</p>
          </div>
          <p className="mt-2 text-2xl font-bold text-error-600">
            {loading ? '-' : `${invalidRate}%`}
          </p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-success-600" />
            <p className="text-sm text-gray-500">知识库数量</p>
          </div>
          <p className="mt-2 text-2xl font-bold text-success-600">
            {loading ? '-' : knowledgeBases.length}
          </p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-warning-600" />
            <p className="text-sm text-gray-500">文档总数</p>
          </div>
          <p className="mt-2 text-2xl font-bold text-warning-600">
            {loading ? '-' : totalDocs}
          </p>
        </div>
      </div>

      {/* 时间范围选择器 */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-500">时间范围：</span>
        <div className="inline-flex rounded-md border border-gray-200 bg-white p-0.5">
          {(['day', 'week', 'month', 'all'] as TimePeriod[]).map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setPeriod(p)}
              className={
                'rounded px-3 py-1 text-xs font-medium transition-colors ' +
                (period === p
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-500 hover:text-gray-700')
              }
            >
              {p === 'day'
                ? '今日'
                : p === 'week'
                  ? '本周'
                  : p === 'month'
                    ? '本月'
                    : '全部'}
            </button>
          ))}
        </div>
      </div>

      {/* 图表区域 */}
      {loading ? (
        <div className="flex items-center justify-center rounded-lg border border-gray-200 bg-white py-16">
          <Spinner label="加载分析数据..." />
        </div>
      ) : (
        <TrendCharts
          trend={trend ?? undefined}
          intent={intent ?? undefined}
          hotQuestions={hot}
          show={['trend', 'intent', 'hot']}
        />
      )}

      {/* 知识库使用统计 */}
      <div className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-100 px-5 py-4">
          <h3 className="flex items-center gap-2 font-semibold text-gray-900">
            <Database className="h-4 w-4 text-primary-600" />
            知识库使用统计
          </h3>
        </div>
        {loading ? (
          <div className="py-12 text-center text-sm text-gray-400">
            加载中...
          </div>
        ) : knowledgeBases.length === 0 ? (
          <div className="py-12 text-center text-sm text-gray-400">
            暂无知识库
          </div>
        ) : (
          <div className="overflow-x-auto custom-scrollbar">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                <tr>
                  <th className="px-5 py-3">知识库名称</th>
                  <th className="px-5 py-3">描述</th>
                  <th className="px-5 py-3 text-right">文档数</th>
                  <th className="px-5 py-3">可见性</th>
                  <th className="px-5 py-3">状态</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {knowledgeBases.map((kb) => (
                  <tr key={kb.id} className="hover:bg-gray-50">
                    <td className="px-5 py-3 font-medium text-gray-900">
                      {kb.name}
                    </td>
                    <td className="max-w-xs px-5 py-3">
                      <p className="truncate text-gray-500">
                        {kb.description || '-'}
                      </p>
                    </td>
                    <td className="px-5 py-3 text-right font-semibold text-gray-900">
                      {kb.document_count ?? 0}
                    </td>
                    <td className="px-5 py-3">
                      <Badge variant={kb.is_public ? 'success' : 'default'}>
                        {kb.is_public ? '公开' : '私有'}
                      </Badge>
                    </td>
                    <td className="px-5 py-3">
                      <Badge
                        variant={
                          kb.status === 'inactive' ? 'default' : 'success'
                        }
                      >
                        {kb.status === 'inactive' ? '停用' : '启用'}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 无效问题分析 */}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <h3 className="mb-3 flex items-center gap-2 font-semibold text-gray-900">
            <AlertCircle className="h-4 w-4 text-error-600" />
            无效问题分析
          </h3>
          {loading ? (
            <p className="py-6 text-center text-sm text-gray-400">
              加载中...
            </p>
          ) : invalid ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between rounded-md bg-error-50 px-4 py-3">
                <div>
                  <p className="text-xs text-error-600">无效问题</p>
                  <p className="mt-0.5 text-xl font-bold text-error-700">
                    {invalid.invalid_count} / {invalid.total}
                  </p>
                </div>
                <Badge variant="error">{invalidRate}%</Badge>
              </div>
              {invalid.suggestions && invalid.suggestions.length > 0 && (
                <div>
                  <p className="mb-1.5 text-xs font-medium text-gray-500">
                    优化建议
                  </p>
                  <ul className="space-y-1">
                    {invalid.suggestions.map((s, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-1.5 text-xs text-gray-600"
                      >
                        <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-primary-500" />
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <p className="py-6 text-center text-sm text-gray-400">暂无数据</p>
          )}
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <h3 className="mb-3 font-semibold text-gray-900">无效问题样本</h3>
          {loading ? (
            <p className="py-6 text-center text-sm text-gray-400">加载中...</p>
          ) : invalid && invalid.samples.length > 0 ? (
            <ul className="space-y-2">
              {invalid.samples.slice(0, 6).map((s, i) => (
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

      {/* 热门问题 */}
      <HotQuestionsTable
        items={hot}
        total={hotTotal}
        loading={loading}
        period={period}
        onPeriodChange={setPeriod}
      />
    </div>
  );
}
