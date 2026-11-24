'use client';

import { useEffect, useRef } from 'react';
import { Sparkles, Lightbulb } from 'lucide-react';

import { Spinner } from '@/components/ui/loading';
import { useChatStore } from '@/store/use-chat-store';
import { ChatMessageItem } from './chat-message';

export interface ChatWindowProps {
  /** 是否正在流式生成（用于滚动与提示） */
  isStreaming?: boolean;
  /** 点击建议问题 */
  onSuggest?: (question: string) => void;
}

const suggestions = [
  '学生手册中关于请假的规定有哪些？',
  '奖学金申请需要哪些材料？',
  '补办学生证的流程是什么？',
];

/**
 * 聊天窗口。
 * 渲染消息列表、空状态欢迎语与加载状态，自动滚动到底部。
 * 消息来源由 useChatStore（与 use-chat hook 同步）提供。
 */
export function ChatWindow({ isStreaming, onSuggest }: ChatWindowProps) {
  const { messages, isLoadingMessages } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  // 新消息或流式更新时滚动到底部
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, isStreaming]);

  // 空状态欢迎语
  if (messages.length === 0 && !isLoadingMessages) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <div className="mx-auto max-w-md text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-50 text-primary-600">
            <Sparkles className="h-7 w-7" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900">
            有什么可以帮你？
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            我可以基于校园知识库回答关于学生手册、奖学金、教务规定等问题。
          </p>

          {onSuggest && (
            <div className="mt-6 space-y-2">
              <p className="inline-flex items-center gap-1 text-xs font-medium text-gray-400">
                <Lightbulb className="h-3.5 w-3.5" />
                试试问我
              </p>
              <div className="grid gap-2">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => onSuggest(s)}
                    className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-left text-sm text-gray-700 transition-all hover:-translate-y-0.5 hover:border-primary-200 hover:bg-primary-50 hover:text-primary-700"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto custom-scrollbar">
      <div className="mx-auto max-w-3xl space-y-6 px-4 py-6 md:px-6">
        {isLoadingMessages && messages.length === 0 ? (
          <div className="flex justify-center py-10">
            <Spinner label="加载历史消息..." />
          </div>
        ) : (
          messages.map((m, idx) => (
            <ChatMessageItem key={m.id ?? `msg-${idx}`} message={m} />
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

export default ChatWindow;
