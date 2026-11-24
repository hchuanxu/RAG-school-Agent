'use client';

import { type HTMLAttributes, type ReactNode } from 'react';

import { cn } from '@/lib/utils';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  title?: ReactNode;
  description?: ReactNode;
  extra?: ReactNode;
  hoverable?: boolean;
  /** 是否去掉默认内边距 */
  bodyPadding?: boolean;
}

/**
 * 卡片组件。
 */
export function Card({
  className,
  title,
  description,
  extra,
  hoverable = false,
  bodyPadding = true,
  children,
  ...props
}: CardProps) {
  const hasHeader = title || extra || description;

  return (
    <div
      className={cn(
        'rounded-lg border border-gray-200 bg-white shadow-sm transition-shadow',
        hoverable && 'cursor-pointer hover:shadow-md',
        className
      )}
      {...props}
    >
      {hasHeader && (
        <div className="flex items-start justify-between border-b border-gray-100 px-5 py-4">
          <div className="min-w-0">
            {title && (
              <h3 className="truncate text-base font-semibold text-gray-900">
                {title}
              </h3>
            )}
            {description && (
              <p className="mt-1 text-sm text-gray-500">{description}</p>
            )}
          </div>
          {extra && <div className="ml-4 shrink-0">{extra}</div>}
        </div>
      )}
      <div className={cn(bodyPadding && 'p-5')}>{children}</div>
    </div>
  );
}

export default Card;
