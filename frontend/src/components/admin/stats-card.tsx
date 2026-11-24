'use client';

import type { ReactNode } from 'react';
import { ArrowDownRight, ArrowUpRight, type LucideIcon } from 'lucide-react';

import { cn } from '@/lib/utils';

export interface StatsCardProps {
  title: string;
  value: string | number;
  /** 变化百分比，正数上升，负数下降 */
  change?: number;
  /** 变化标签，例如 "较昨日" */
  changeLabel?: string;
  icon: LucideIcon;
  /** 图标背景色主题 */
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info';
  className?: string;
  children?: ReactNode;
}

const colorClasses: Record<
  NonNullable<StatsCardProps['color']>,
  { bg: string; text: string }
> = {
  primary: 'bg-primary-50 text-primary-600',
  success: 'bg-success-50 text-success-600',
  warning: 'bg-warning-50 text-warning-600',
  error: 'bg-error-50 text-error-600',
  info: 'bg-primary-50 text-primary-600',
};

/**
 * 管理端统计卡片。
 * 展示数值与变化趋势（上升绿色 / 下降红色）。
 */
export function StatsCard({
  title,
  value,
  change,
  changeLabel,
  icon: Icon,
  color = 'primary',
  className,
  children,
}: StatsCardProps) {
  const isUp = typeof change === 'number' && change > 0;
  const isDown = typeof change === 'number' && change < 0;
  const theme = colorClasses[color];

  return (
    <div
      className={cn(
        'rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="mt-2 text-2xl font-bold text-gray-900">{value}</p>
        </div>
        <span
          className={cn(
            'flex h-11 w-11 shrink-0 items-center justify-center rounded-lg',
            theme.bg,
            theme.text
          )}
        >
          <Icon className="h-5 w-5" />
        </span>
      </div>

      {typeof change === 'number' && (
        <div className="mt-3 flex items-center gap-1.5 text-xs">
          <span
            className={cn(
              'inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 font-medium',
              isUp && 'bg-success-50 text-success-600',
              isDown && 'bg-error-50 text-error-600',
              !isUp && !isDown && 'bg-gray-100 text-gray-500'
            )}
          >
            {isUp && <ArrowUpRight className="h-3 w-3" />}
            {isDown && <ArrowDownRight className="h-3 w-3" />}
            {change > 0 ? `+${change}` : change}%
          </span>
          {changeLabel && <span className="text-gray-400">{changeLabel}</span>}
        </div>
      )}

      {children}
    </div>
  );
}

export default StatsCard;
