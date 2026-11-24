'use client';

import { type HTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

export interface AvatarProps extends HTMLAttributes<HTMLDivElement> {
  /** 头像图片地址 */
  src?: string;
  /** 显示名称（用于生成首字母 fallback） */
  name?: string;
  /** 尺寸 */
  size?: 'sm' | 'md' | 'lg';
}

const sizeClasses = {
  sm: 'h-8 w-8 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-12 w-12 text-base',
};

/**
 * 头像组件。
 * 优先显示图片，无图片时显示名称首字母。
 */
export function Avatar({
  className,
  src,
  name,
  size = 'md',
  ...props
}: AvatarProps) {
  const initials = name
    ? name
        .trim()
        .split(/\s+/)
        .slice(0, 2)
        .map((w) => w[0]?.toUpperCase())
        .join('')
    : '?';

  return (
    <div
      className={cn(
        'inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-primary-100 font-medium text-primary-700',
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={src}
          alt={name || 'avatar'}
          className="h-full w-full object-cover"
          referrerPolicy="no-referrer"
        />
      ) : (
        <span>{initials}</span>
      )}
    </div>
  );
}

export default Avatar;
