'use client';

import { useMemo } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Inbox } from 'lucide-react';

import { Spinner } from '@/components/ui/loading';
import type {
  HotQuestion,
  IntentDistribution,
  QuestionIntent,
  TrendData,
} from '@/types';

export interface TrendChartsProps {
  trend?: TrendData;
  intent?: IntentDistribution;
  hotQuestions?: HotQuestion[];
  loading?: boolean;
  /** 显示哪些图表：默认全部 */
  show?: ('trend' | 'intent' | 'hot')[];
}

const intentLabel: Record<QuestionIntent, string> = {
  campus_policy: '校园政策',
  academic: '学业教务',
  scholarship: '奖学金',
  invalid: '无效问题',
  other: '其他',
};

const PIE_COLORS = [
  '#4f46e5',
  '#10b981',
  '#f59e0b',
  '#ef4444',
  '#6366f1',
  '#94a3b8',
];

/**
 * 管理端趋势图表集合。
 * 包含：提问趋势折线图、意图分布饼图、热门问题 TOP10 柱状图。
 */
export function TrendCharts({
  trend,
  intent,
  hotQuestions = [],
  loading = false,
  show = ['trend', 'intent', 'hot'],
}: TrendChartsProps) {
  const trendData = useMemo(
    () =>
      (trend?.items ?? []).map((it) => ({
        date: it.date,
        count: it.count,
        valid: it.valid_count ?? 0,
        invalid: it.invalid_count ?? 0,
      })),
    [trend]
  );

  const intentData = useMemo(
    () =>
      (intent?.items ?? []).map((it) => ({
        name: intentLabel[it.intent] || it.intent,
        value: it.count,
        percentage: it.percentage,
      })),
    [intent]
  );

  const hotData = useMemo(
    () =>
      hotQuestions
        .slice(0, 10)
        .map((it) => ({
          name:
            it.question.length > 12
              ? it.question.slice(0, 12) + '...'
              : it.question,
          count: it.count,
        })),
    [hotQuestions]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center rounded-lg border border-gray-200 bg-white py-16">
        <Spinner label="加载图表数据..." />
      </div>
    );
  }

  const Empty = ({ text }: { text: string }) => (
    <div className="flex h-64 flex-col items-center justify-center text-center text-gray-400">
      <Inbox className="mb-2 h-10 w-10 text-gray-300" />
      <p className="text-sm">{text}</p>
    </div>
  );

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {/* 提问趋势折线图 - 占满一行 */}
      {show.includes('trend') && (
        <div className="rounded-lg border border-gray-200 bg-white p-5 lg:col-span-2">
          <h3 className="mb-4 font-semibold text-gray-900">提问趋势</h3>
          {trendData.length === 0 ? (
            <Empty text="暂无趋势数据" />
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={trendData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#4f46e5" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e5e7eb' }}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: 8,
                    border: '1px solid #e5e7eb',
                    fontSize: 12,
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Area
                  type="monotone"
                  dataKey="count"
                  name="提问总数"
                  stroke="#4f46e5"
                  strokeWidth={2}
                  fill="url(#colorCount)"
                />
                <Line
                  type="monotone"
                  dataKey="valid"
                  name="有效提问"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="invalid"
                  name="无效提问"
                  stroke="#ef4444"
                  strokeWidth={2}
                  dot={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      )}

      {/* 意图分布饼图 */}
      {show.includes('intent') && (
        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <h3 className="mb-4 font-semibold text-gray-900">意图分布</h3>
          {intentData.length === 0 ? (
            <Empty text="暂无分布数据" />
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={intentData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  innerRadius={50}
                  label={({ name, percentage }) =>
                    `${name} ${percentage.toFixed(0)}%`
                  }
                  labelLine={false}
                  style={{ fontSize: 12 }}
                >
                  {intentData.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={PIE_COLORS[index % PIE_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    borderRadius: 8,
                    border: '1px solid #e5e7eb',
                    fontSize: 12,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      )}

      {/* 热门问题 TOP10 柱状图 */}
      {show.includes('hot') && (
        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <h3 className="mb-4 font-semibold text-gray-900">
            热门问题 TOP10
          </h3>
          {hotData.length === 0 ? (
            <Empty text="暂无热门问题数据" />
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={hotData}
                layout="vertical"
                margin={{ top: 5, right: 20, bottom: 5, left: 80 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis
                  type="number"
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e5e7eb' }}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                  tickLine={false}
                  axisLine={false}
                  width={80}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: 8,
                    border: '1px solid #e5e7eb',
                    fontSize: 12,
                  }}
                />
                <Bar
                  dataKey="count"
                  name="提问次数"
                  fill="#4f46e5"
                  radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      )}
    </div>
  );
}

export default TrendCharts;
