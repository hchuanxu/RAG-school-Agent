'use client';

import {
  forwardRef,
  type TextareaHTMLAttributes,
} from 'react';

import { cn } from '@/lib/utils';

export interface TextareaProps
  extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'onChange'> {
  error?: string;
  /** 自适应高度最大行数 */
  maxRows?: number;
  /** 受控值变化回调 */
  onChange?: (value: string) => void;
}

/**
 * 多行文本输入组件。
 */
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    { className, error, maxRows = 5, onChange, disabled, ...props },
    ref
  ) => {
    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const target = e.target;
      // 自动调整高度
      target.style.height = 'auto';
      const lineHeight = parseFloat(getComputedStyle(target).lineHeight) || 24;
      target.style.height = `${Math.min(
        target.scrollHeight,
        lineHeight * maxRows
      )}px`;
      onChange?.(target.value);
    };

    return (
      <div className="w-full">
        <textarea
          ref={ref}
          disabled={disabled}
          onChange={handleChange}
          rows={props.rows ?? 1}
          className={cn(
            'w-full resize-none rounded-md border bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 transition-colors custom-scrollbar',
            'focus:outline-none focus:ring-2 focus:ring-offset-0',
            error
              ? 'border-error-300 focus:border-error-400 focus:ring-error-200'
              : 'border-gray-200 focus:border-primary-400 focus:ring-primary-200',
            disabled && 'cursor-not-allowed bg-gray-50 opacity-60',
            className
          )}
          {...props}
        />
        {error && (
          <p className="mt-1.5 text-xs text-error-500" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

export default Textarea;
