'use client';

import { Suspense, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

import { ChatWindow } from '@/components/chat/chat-window';
import { ChatInput } from '@/components/chat/chat-input';
import { useChat } from '@/lib/hooks/use-chat';
import { useKnowledgeStore } from '@/store/use-knowledge-store';

function ChatPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const prefill = searchParams.get('question') ?? '';

  const { currentKB } = useKnowledgeStore();
  const { sendMessage, stop, isStreaming, isSending } = useChat({
    knowledgeBaseIds: currentKB?.id ? [currentKB.id] : undefined,
  });

  // 从 URL 携带的 question 自动发起提问（如考点“向助手提问”跳转）
  const sentRef = useRef(false);
  useEffect(() => {
    if (prefill && !sentRef.current) {
      sentRef.current = true;
      void sendMessage(prefill);
      // 清理 URL，避免刷新重复发送
      router.replace('/dashboard');
    }
  }, [prefill, sendMessage, router]);

  return (
    <div className="flex h-full flex-col bg-gray-50">
      <ChatWindow isStreaming={isStreaming} onSuggest={(q) => sendMessage(q)} />
      <ChatInput
        onSend={sendMessage}
        onStop={stop}
        isStreaming={isStreaming}
        disabled={isSending}
      />
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={null}>
      <ChatPageInner />
    </Suspense>
  );
}
