'use client';

import { useState, type KeyboardEvent } from 'react';
import { Square, ArrowUp } from 'lucide-react';

import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

export interface ChatInputProps {
  /** 发送消息回调 */
  onSend: (text: string) => void;
  /** 停止生成回调 */
  onStop?: () => void;
  /** 是否正在流式生成 */
  isStreaming?: boolean;
  /** 是否禁用输入 */
  disabled?: boolean;
  /** 占位提示 */
  placeholder?: string;
  /** 初始值（用于从外部预填提问，如考点提问跳转） */
  initialValue?: string;
}

/**
 * 对话输入框。
 * 胶囊式容器，集成圆形发送按钮，聚焦时呈现光晕动效。
 * 多行自适应高度，回车发送、Shift+回车换行，流式时显示停止按钮。
 */
export function ChatInput({
  onSend,
  onStop,
  isStreaming = false,
  disabled = false,
  placeholder,
  initialValue,
}: ChatInputProps) {
  const [value, setValue] = useState(initialValue ?? '');
  const [isFocused, setIsFocused] = useState(false);

  const canSend = value.trim().length > 0 && !disabled && !isStreaming;

  const send = () => {
    const text = value.trim();
    if (!text || isStreaming || disabled) return;
    onSend(text);
    setValue('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // 中文输入法组合中不触发发送
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="border-t border-gray-100 bg-white/80 px-4 py-3 backdrop-blur-sm md:px-6">
      <div className="mx-auto max-w-3xl">
        {/* 胶囊式输入容器 */}
        <div
          className={cn(
            'group relative flex items-end gap-2 rounded-[1.75rem] border-2 bg-white px-4 py-1.5 transition-all duration-300',
            isFocused
              ? 'border-primary-400 shadow-lg shadow-primary-100/80'
              : 'border-gray-200 shadow-sm hover:border-gray-300'
          )}
        >
          <Textarea
            value={value}
            onChange={setValue}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={placeholder ?? '输入你的问题…'}
            maxRows={6}
            className={cn(
              'min-h-[44px] flex-1 resize-none border-0 bg-transparent px-0 py-2 text-base text-gray-900 placeholder-gray-400',
              'focus:border-0 focus:ring-0 focus:outline-none'
            )}
            disabled={disabled && !isStreaming}
          />

          {/* 圆形操作按钮 */}
          {isStreaming ? (
            <button
              type="button"
              onClick={onStop}
              aria-label="停止生成"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-error-500 text-white shadow-md shadow-error-200 transition-all duration-300 hover:scale-105 hover:bg-error-600 active:scale-95"
            >
              <Square className="h-4 w-4 fill-current" />
            </button>
          ) : (
            <button
              type="button"
              onClick={send}
              disabled={!canSend}
              aria-label="发送消息"
              className={cn(
                'flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition-all duration-300',
                canSend
                  ? 'bg-gradient-to-br from-primary-500 to-primary-600 text-white shadow-md shadow-primary-200 hover:scale-110 hover:shadow-lg hover:shadow-primary-300 active:scale-95'
                  : 'cursor-not-allowed bg-gray-100 text-gray-300'
              )}
            >
              <ArrowUp className="h-5 w-5" />
            </button>
          )}
        </div>

        {/* 底部提示 */}
        <p className="mt-2 text-center text-xs text-gray-400 transition-opacity duration-300 group-hover:opacity-0">
          回车发送 · Shift + 回车换行
        </p>
      </div>
    </div>
  );
}

export default ChatInput;
