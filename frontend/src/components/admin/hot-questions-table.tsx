'use client';

import { useMemo, useState } from 'react';
import { Inbox, TrendingUp } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Spinner } from '@/components/ui/loading';
import { cn } from '@/lib/utils';
import type { HotQuestion, QuestionIntent } from '@/types';

export type TimePeriod = 'day' | 'week' | 'month' | 'all';

export interface HotQuestionsTableProps {
  items: HotQuestion[];
  total?: number;
  loading?: boolean;
  period?: TimePeriod;
  onPeriodChange?: (period: TimePeriod) => void;
  /** 显示前 N 条，默认全部 */
  topK?: number;
}

const periodOptions: { value: TimePeriod; label: string }[] = [
  { value: 'day', label: '今日' },
  { value: 'week', label: '本周' },
  { value: 'month', label: '本月' },
  { value: 'all', label: '全部' },
];

const intentLabel: Record<QuestionIntent, string> = {
  campus_policy: '校园政策',
  academic: '学业教务',
  scholarship: '奖学金',
  invalid: '无效问题',
  other: '其他',
};

const intentVariant: Record<
  QuestionIntent,
  'default' | 'success' | 'warning' | 'error' | 'info'
> = {
  campus_policy: 'info',
  academic: 'success',
  scholarship: 'warning',
  invalid: 'error',
  other: 'default',
};

/**
 * 管理端热门问题表格。
 * 支持时间范围筛选、占比展示与意图标签。
 */
export function HotQuestionsTable({
  items,
  total = 0,
  loading = false,
  period = 'week',
  onPeriodChange,
}: HotQuestionsTableProps) {
  const [activePeriod, setActivePeriod] = useState<TimePeriod>(period);

  const maxCount = useMemo(
    () => items.reduce((max, it) => Math.max(max, it.count), 0),
    [items]
  );

  const handlePeriod = (p: TimePeriod) => {
    setActivePeriod(p);
    onPeriodChange?.(p);
  };

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
      {/* 顶部：标题 + 时间筛选 */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 px-5 py-4">
        <div>
          <h3 className="flex items-center gap-2 font-semibold text-gray-900">
            <TrendingUp className="h-4 w-4 text-primary-600" />
            热门问题排行
          </h3>
          <p className="mt-0.5 text-xs text-gray-500">
            共 {total || items.length} 条提问
          </p>
        </div>
        <div className="inline-flex rounded-md border border-gray-200 bg-gray-50 p-0.5">
          {periodOptions.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => handlePeriod(opt.value)}
              className={cn(
                'rounded px-3 py-1 text-xs font-medium transition-colors',
                activePeriod === opt.value
                  ? 'bg-white text-primary-600 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* 表格 */}
      <div className="overflow-x-auto custom-scrollbar">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
            <tr>
              <th className="w-14 px-5 py-3">排名</th>
              <th className="px-5 py-3">问题</th>
              <th className="px-5 py-3 text-right">提问次数</th>
              <th className="px-5 py-3">占比</th>
              <th className="px-5 py-3">意图</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr>
                <td colSpan={5} className="px-5 py-12 text-center">
                  <Spinner label="加载热门问题..." />
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-5 py-12">
                  <div className="flex flex-col items-center justify-center text-center text-gray-400">
                    <Inbox className="mb-2 h-10 w-10 text-gray-300" />
                    <p className="text-sm">暂无数据</p>
                  </div>
                </td>
              </tr>
            ) : (
              items.map((item, index) => {
                const percent =
                  total > 0 ? (item.count / total) * 100 : 0;
                const barPercent =
                  maxCount > 0 ? (item.count / maxCount) * 100 : 0;
                const rank = index + 1;
                const rankColor =
                  rank === 1
                    ? 'bg-error-500'
                    : rank === 2
                      ? 'bg-warning-500'
                      : rank === 3
                        ? 'bg-primary-500'
                        : 'bg-gray-300';
                return (
                  <tr
                    key={`${item.question}-${index}`}
                    className="transition-colors hover:bg-gray-50"
                  >
                    <td className="px-5 py-3">
                      <span
                        className={cn(
                          'inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold text-white',
                          rankColor
                        )}
                      >
                        {rank}
                      </span>
                    </td>
                    <td className="max-w-md px-5 py-3">
                      <p className="truncate font-medium text-gray-900">
                        {item.question}
                      </p>
                    </td>
                    <td className="px-5 py-3 text-right font-semibold text-gray-900">
                      {item.count}
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-20 overflow-hidden rounded-full bg-gray-100">
                          <div
                            className="h-full rounded-full bg-primary-500"
                            style={{ width: `${barPercent}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">
                          {percent.toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3">
                      {item.intent && (
                        <Badge variant={intentVariant[item.intent]}>
                          {intentLabel[item.intent]}
                        </Badge>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default HotQuestionsTable;
