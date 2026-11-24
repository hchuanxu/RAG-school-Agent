'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  Search, MessageSquare, Clock, TrendingUp,
  Target, AlertTriangle, Zap, ThumbsUp,
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts';

import { StatsCard } from '@/components/admin/stats-card';
import { knowledgeApi, metricsApi } from '@/lib/api';
import { cn } from '@/lib/utils';
import type {
  KnowledgeBase, MetricsOverview, MetricsPeriod, MetricsTrendsData,
} from '@/types';

const periodOptions: Array<{ value: MetricsPeriod; label: string }> = [
  { value: 'day', label: '今日' },
  { value: 'week', label: '本周' },
  { value: 'month', label: '本月' },
  { value: 'all', label: '全部' },
];

export function MetricsDashboard() {
  const [period, setPeriod] = useState<MetricsPeriod>('week');
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [knowledgeBaseId, setKnowledgeBaseId] = useState<number | undefined>(undefined);
  const [overview, setOverview] = useState<MetricsOverview | null>(null);
  const [trends, setTrends] = useState<MetricsTrendsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [overviewRes, trendsRes] = await Promise.all([
        metricsApi.overview(period, knowledgeBaseId).catch(() => null),
        metricsApi.trends('latency', period, knowledgeBaseId).catch(() => null),
      ]);
      setOverview(overviewRes);
      setTrends(trendsRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载指标失败');
    } finally {
      setLoading(false);
    }
  }, [period, knowledgeBaseId]);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  // 拉取知识库列表用于下拉框筛选
  useEffect(() => {
    knowledgeApi
      .list()
      .then((res) => setKnowledgeBases(res.items))
      .catch(() => setKnowledgeBases([]));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-400">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center text-red-600">
        {error}
      </div>
    );
  }

  if (!overview) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-400">暂无数据</div>
      </div>
    );
  }

  const fmtPercent = (v: number) => `${(v * 100).toFixed(1)}%`;
  const fmtMs = (v: number) => v > 1000 ? `${(v / 1000).toFixed(2)}s` : `${Math.round(v)}ms`;

  return (
    <div className="space-y-6">
      {/* 时间范围切换 + 知识库筛选 */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          {periodOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setPeriod(opt.value)}
              className={cn(
                'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                period === opt.value
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-600 ring-1 ring-gray-200 hover:bg-gray-50'
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <select
          value={knowledgeBaseId ?? ''}
          onChange={(e) =>
            setKnowledgeBaseId(e.target.value ? Number(e.target.value) : undefined)
          }
          className="rounded-md px-3 py-1.5 text-sm font-medium bg-white text-gray-600 ring-1 ring-gray-200 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
          aria-label="知识库筛选"
        >
          <option value="">全部知识库</option>
          {knowledgeBases.map((kb) => (
            <option key={kb.id} value={kb.id}>
              {kb.name}
            </option>
          ))}
        </select>
      </div>

      {/* 指标卡片 */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="检索命中率"
          value={fmtPercent(overview.retrieval.hit_rate)}
          icon={Target}
          color="primary"
        />
        <StatsCard
          title="回答引用率"
          value={fmtPercent(overview.answer.citation_rate)}
          icon={MessageSquare}
          color="info"
        />
        <StatsCard
          title="P95 端到端延迟"
          value={fmtMs(overview.latency.p95_e2e_ms)}
          icon={Clock}
          color={overview.latency.p95_e2e_ms > 6000 ? 'error' : 'success'}
        />
        <StatsCard
          title="点赞数"
          value={overview.business.upvote_count}
          icon={ThumbsUp}
          color="success"
        />
      </div>

      {/* 详细指标网格 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-700">
            <Search className="h-4 w-4 text-primary-500" />
            检索质量
          </h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500">总检索次数</dt>
              <dd className="font-medium text-gray-900">{overview.retrieval.total_queries}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">平均召回数</dt>
              <dd className="font-medium text-gray-900">{overview.retrieval.avg_retrieved_count.toFixed(1)}</dd>
            </div>
          </dl>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-700">
            <AlertTriangle className="h-4 w-4 text-orange-500" />
            回答质量
          </h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500">总回答数</dt>
              <dd className="font-medium text-gray-900">{overview.answer.total_answers}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">点踩率</dt>
              <dd className="font-medium text-gray-900">{fmtPercent(overview.answer.downvote_rate)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">幻觉率</dt>
              <dd className="font-medium text-gray-900">{fmtPercent(overview.answer.hallucination_rate)}</dd>
            </div>
          </dl>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-700">
            <Zap className="h-4 w-4 text-yellow-500" />
            性能指标
          </h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500">总请求数</dt>
              <dd className="font-medium text-gray-900">{overview.latency.total_requests}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">平均 TTFT</dt>
              <dd className="font-medium text-gray-900">{fmtMs(overview.latency.avg_ttft_ms)}</dd>
            </div>
          </dl>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-700">
            <TrendingUp className="h-4 w-4 text-green-500" />
            业务价值
          </h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500">总反馈数</dt>
              <dd className="font-medium text-gray-900">{overview.business.total_feedback}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">点踩数</dt>
              <dd className="font-medium text-gray-900">{overview.business.downvote_count}</dd>
            </div>
          </dl>
        </div>
      </div>

      {/* 趋势图表 */}
      {trends && trends.items && trends.items.length > 0 && (
        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <h3 className="mb-4 text-sm font-semibold text-gray-700">端到端延迟趋势 (ms)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trends.items}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="p95_e2e_ms"
                name="P95 延迟"
                stroke="#ef4444"
                strokeWidth={2}
                dot={{ r: 3 }}
              />
              <Line
                type="monotone"
                dataKey="avg_e2e_ms"
                name="平均延迟"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default MetricsDashboard;
