'use client';

import { useCallback, useRef, useState } from 'react';

import { useSSE } from '@/lib/hooks/use-sse';
import { useChatStore } from '@/store/use-chat-store';
import type { ChatMessage, Citation, SSEEvent } from '@/types';

export interface UseChatOptions {
  /** 当未指定会话时使用的知识库 ID 列表 */
  knowledgeBaseIds?: number[];
  /** 流式结束回调 */
  onDone?: (sessionId?: number) => void;
  /** 错误回调 */
  onError?: (error: Error) => void;
}

/**
 * 对话 Hook。
 *
 * 封装流式问答的全部交互逻辑：
 * - 发送用户问题
 * - 流式接收回答（逐 token 渲染）
 * - 接收引用溯源
 * - 管理消息列表（与 useChatStore 同步）
 * - 支持中断生成
 */
export function useChat(options: UseChatOptions = {}) {
  const { knowledgeBaseIds, onDone, onError } = options;

  const { connectSSE, abort, isStreaming } = useSSE();
  const [error, setError] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);

  // 当前正在流式输出的 assistant 消息 ID（本地维护）
  const currentMessageRef = useRef<string | null>(null);

  const {
    currentSessionId,
    addMessage,
    updateMessage,
    setCurrentSessionId,
    fetchSessions,
  } = useChatStore();

  /**
   * 发送一条问题并流式接收回答。
   */
  const sendMessage = useCallback(
    async (question: string) => {
      if (!question.trim() || isStreaming || isSending) return;

      setError(null);
      setIsSending(true);

      // 1. 立即把用户消息加入列表
      const userMessage: ChatMessage = {
        role: 'user',
        content: question,
        created_at: new Date().toISOString(),
      };
      addMessage(userMessage);

      // 2. 预插入一条空的 assistant 消息，后续流式更新
      const assistantMessageId = `temp-${Date.now()}`;
      currentMessageRef.current = assistantMessageId;
      const assistantMessage: ChatMessage = {
        id: assistantMessageId as unknown as number,
        role: 'assistant',
        content: '',
        streaming: true,
        citations: [],
        created_at: new Date().toISOString(),
      };
      addMessage(assistantMessage);

      let accumulatedContent = '';
      const citations: Citation[] = [];

      // 3. 发起 SSE 流式请求
      await connectSSE<SSEEvent>(
        '/api/v1/chat/stream',
        {
          question,
          session_id: currentSessionId,
          knowledge_base_ids: knowledgeBaseIds,
        },
        {
          onMessage: (event) => {
            switch (event.type) {
              case 'session': {
                // 后端在工作流执行前发送会话 ID
                if (event.session_id) {
                  setCurrentSessionId(event.session_id);
                }
                break;
              }
              case 'token': {
                accumulatedContent += event.content || '';
                updateMessage(assistantMessageId, {
                  content: accumulatedContent,
                  streaming: true,
                });
                break;
              }
              case 'citations': {
                // 后端一次性发送全部引用列表
                if (Array.isArray(event.citations)) {
                  citations.push(...event.citations);
                  updateMessage(assistantMessageId, { citations: [...citations] });
                }
                break;
              }
              case 'done': {
                updateMessage(assistantMessageId, {
                  content: accumulatedContent,
                  citations,
                  streaming: false,
                });
                break;
              }
              case 'error': {
                const message = event.message || '回答生成失败';
                setError(message);
                updateMessage(assistantMessageId, {
                  content: accumulatedContent || `回答生成失败：${message}`,
                  streaming: false,
                });
                break;
              }
            }
          },
          onError: (err) => {
            setError(err.message);
            updateMessage(assistantMessageId, {
              content: accumulatedContent || `请求出错：${err.message}`,
              streaming: false,
            });
            onError?.(err);
          },
          onClose: () => {
            // 确保最终状态为非流式
            updateMessage(assistantMessageId, {
              content: accumulatedContent,
              citations,
              streaming: false,
            });
          },
        }
      );

      setIsSending(false);
      currentMessageRef.current = null;
      // 流式结束后刷新会话列表，让侧边栏立即显示最新对话
      try {
        await fetchSessions();
      } catch {
        // 刷新失败不影响已显示的回答
      }
      // 使用 getState 获取最新的 session_id，避免闭包陈旧值
      onDone?.(useChatStore.getState().currentSessionId ?? undefined);
    },
    [
      isStreaming,
      isSending,
      connectSSE,
      addMessage,
      updateMessage,
      setCurrentSessionId,
      fetchSessions,
      currentSessionId,
      knowledgeBaseIds,
      onDone,
      onError,
    ]
  );

  /** 停止生成 */
  const stop = useCallback(() => {
    abort();
    if (currentMessageRef.current) {
      updateMessage(currentMessageRef.current, { streaming: false });
    }
    setIsSending(false);
  }, [abort, updateMessage]);

  return {
    sendMessage,
    stop,
    isStreaming,
    isSending,
    error,
    clearError: () => setError(null),
  };
}

export default useChat;
