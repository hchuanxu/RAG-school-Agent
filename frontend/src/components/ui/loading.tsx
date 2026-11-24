'use client';

import { Loader2 } from 'lucide-react';

import { cn } from '@/lib/utils';

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  label?: string;
}

const sizeMap = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-10 w-10',
};

/**
 * 旋转加载图标。
 */
export function Spinner({ size = 'md', className, label }: SpinnerProps) {
  return (
    <span
      className={cn('inline-flex items-center gap-2', className)}
      role="status"
      aria-live="polite"
    >
      <Loader2 className={cn('animate-spin text-primary-600', sizeMap[size])} />
      {label && <span className="text-sm text-gray-500">{label}</span>}
    </span>
  );
}

/**
 * 加载点（用于打字效果）。
 */
export function TypingDots() {
  return (
    <span className="inline-flex items-center gap-1" aria-label="正在输入">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-2 w-2 rounded-full bg-gray-400 animate-typing-dot"
          style={{ animationDelay: `${i * 0.2}s` }}
        />
      ))}
    </span>
  );
}

export interface LoadingOverlayProps {
  visible: boolean;
  label?: string;
}

/**
 * 全屏加载遮罩。
 */
export function LoadingOverlay({ visible, label = '加载中...' }: LoadingOverlayProps) {
  if (!visible) return null;

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-white/60 backdrop-blur-sm"
      role="progressbar"
      aria-busy="true"
    >
      <div className="flex flex-col items-center gap-3">
        <Spinner size="lg" />
        <p className="text-sm text-gray-600">{label}</p>
      </div>
    </div>
  );
}

export default Spinner;
