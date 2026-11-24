'use client';

import {
  forwardRef,
  type InputHTMLAttributes,
  type ReactNode,
} from 'react';

import { cn } from '@/lib/utils';

export type InputType = 'text' | 'password' | 'email' | 'search';

export interface InputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  type?: InputType;
  error?: string;
  /** 左侧图标 */
  leftIcon?: ReactNode;
  /** 右侧图标 */
  rightIcon?: ReactNode;
  /** 受控值变化回调 */
  onChange?: (value: string) => void;
}

/**
 * 输入框组件。
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      type = 'text',
      error,
      leftIcon,
      rightIcon,
      onChange,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <div className="w-full">
        <div className="relative">
          {leftIcon && (
            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              {leftIcon}
            </span>
          )}
          <input
            ref={ref}
            type={type}
            disabled={disabled}
            onChange={(e) => onChange?.(e.target.value)}
            className={cn(
              'w-full rounded-md border bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-offset-0',
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
              error
                ? 'border-error-300 focus:border-error-400 focus:ring-error-200'
                : 'border-gray-200 focus:border-primary-400 focus:ring-primary-200',
              disabled && 'cursor-not-allowed bg-gray-50 opacity-60',
              className
            )}
            {...props}
          />
          {rightIcon && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
              {rightIcon}
            </span>
          )}
        </div>
        {error && (
          <p className="mt-1.5 text-xs text-error-500" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
