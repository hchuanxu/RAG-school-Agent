'use client';

import { type HTMLAttributes, type ReactNode } from 'react';

import { cn } from '@/lib/utils';

export type BadgeVariant =
  | 'default'
  | 'success'
  | 'warning'
  | 'error'
  | 'info';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  /** 是否为描边样式 */
  outline?: boolean;
  children: ReactNode;
}

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-gray-100 text-gray-700',
  success: 'bg-success-100 text-success-700',
  warning: 'bg-warning-100 text-warning-700',
  error: 'bg-error-100 text-error-700',
  info: 'bg-primary-100 text-primary-700',
};

const outlineClasses: Record<BadgeVariant, string> = {
  default: 'border border-gray-200 text-gray-700',
  success: 'border border-success-200 text-success-700',
  warning: 'border border-warning-200 text-warning-700',
  error: 'border border-error-200 text-error-700',
  info: 'border border-primary-200 text-primary-700',
};

/**
 * 标签组件。
 */
export function Badge({
  className,
  variant = 'default',
  outline = false,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        outline ? outlineClasses[variant] : variantClasses[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}

export default Badge;
