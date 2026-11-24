'use client';

import { cn } from '@/lib/utils';

export interface LogoProps {
  /** 尺寸 */
  size?: 'sm' | 'md' | 'lg';
  /** 是否显示文字名称 */
  showText?: boolean;
  /** 额外类名 */
  className?: string;
  /** 文字额外类名 */
  textClassName?: string;
}

/** 图标方块尺寸 */
const boxClasses = {
  sm: 'h-9 w-9 rounded-lg',
  md: 'h-14 w-14 rounded-2xl',
  lg: 'h-16 w-16 rounded-2xl',
};

/** 名称字号 */
const nameClasses = {
  sm: 'text-lg',
  md: 'text-2xl',
  lg: 'text-3xl',
};

/** QM 单体 Logo SVG — Q 圆环内嵌 M 山峰 */
function QMMonogram({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 44 44"
      fill="none"
      className={cn('text-white', className)}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Q: 圆环 */}
      <circle cx="20" cy="19" r="14" stroke="currentColor" strokeWidth="2.8" />
      {/* Q: 尾巴 — 从圆环右下延伸出 */}
      <path
        d="M 29 28 L 38 37"
        stroke="currentColor"
        strokeWidth="2.8"
        strokeLinecap="round"
      />
      {/* M: 山峰造型 — 嵌入 Q 圆环内部 */}
      <path
        d="M 11 29 L 15 13 L 19 23 L 23 13 L 27 29"
        stroke="currentColor"
        strokeWidth="2.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/**
 * 启明校园智能问答 — QM Logo 组件。
 * 渐变方块 + QM 字母创意组合 SVG，可选展示系统名称。
 */
export function Logo({
  size = 'sm',
  showText = false,
  className,
  textClassName,
}: LogoProps) {
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      {/* QM 图标 */}
      <div
        className={cn(
          'flex items-center justify-center bg-gradient-to-br from-primary-500 to-primary-700 shadow-sm ring-1 ring-white/20',
          boxClasses[size]
        )}
      >
        <QMMonogram className="h-[72%] w-[72%]" />
      </div>

      {/* 系统名称 */}
      {showText && (
        <span
          className={cn(
            'font-bold text-gray-900',
            nameClasses[size],
            textClassName
          )}
        >
          启明校园智能问答
        </span>
      )}
    </div>
  );
}

export default Logo;
