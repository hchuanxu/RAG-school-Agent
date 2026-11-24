'use client';

import { useCallback, useRef, useState } from 'react';

import { ACCESS_TOKEN_KEY } from '@/lib/api';
import type { SSEEvent } from '@/types';

/**
 * 后端 API 基址。
 *
 * SSE 流式请求必须直连后端，绕过 Next.js dev server 的 rewrites 代理
 * （该代理会缓冲 text/event-stream 响应，导致前端无法实时接收数据块）。
 * 生产环境可通过 NEXT_PUBLIC_API_BASE_URL 覆盖。
 */
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

/**
 * 将相对的 /api/ 路径解析为直连后端的绝对 URL。
 */
function resolveSSEUrl(url: string): string {
  if (url.startsWith('/api/')) {
    return `${API_BASE_URL}${url}`;
  }
  return url;
}

export interface SSECallbacks<T = SSEEvent> {
  onMessage?: (event: T) => void;
  onError?: (error: Error) => void;
  onOpen?: () => void;
  onClose?: () => void;
}

export interface UseSSEOptions {
  /** 是否在请求体中携带 token（默认 true） */
  withAuth?: boolean;
  /** 额外请求头 */
  headers?: Record<string, string>;
}

/**
 * SSE 流式请求 Hook。
 *
 * 由于原生 EventSource 仅支持 GET 请求，此处使用 fetch + ReadableStream
 * 实现 POST 方式的 SSE 流式接收，支持随时中断。
 */
export function useSSE() {
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  /** 主动中断当前流式请求 */
  const abort = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  /**
   * 发起 SSE 流式连接。
   *
   * @param url 请求地址（相对路径，如 /api/v1/chat/stream）
   * @param data 请求体数据
   * @param callbacks 回调集合
   * @param options 额外选项
   */
  const connectSSE = useCallback(
    async <T = SSEEvent>(
      url: string,
      data: unknown,
      callbacks: SSECallbacks<T>,
      options: UseSSEOptions = {}
    ) => {
      // 若已有进行中的请求，先中断
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const controller = new AbortController();
      abortControllerRef.current = controller;
      setIsStreaming(true);

      const { withAuth = true, headers = {} } = options;

      const requestHeaders: Record<string, string> = {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        ...headers,
      };

      if (withAuth && typeof window !== 'undefined') {
        const token = localStorage.getItem(ACCESS_TOKEN_KEY);
        if (token) {
          requestHeaders.Authorization = `Bearer ${token}`;
        }
      }

      try {
        const response = await fetch(resolveSSEUrl(url), {
          method: 'POST',
          headers: requestHeaders,
          body: JSON.stringify(data),
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        if (!response.body) {
          throw new Error('响应体不可读');
        }

        callbacks.onOpen?.();

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        // 逐块读取并按 SSE 事件分隔解析
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // SSE 事件以两个换行符分隔
          const events = buffer.split('\n\n');
          // 最后一段可能不完整，保留到下一轮
          buffer = events.pop() || '';

          for (const rawEvent of events) {
            const parsed = parseSSEEvent<T>(rawEvent);
            if (parsed) {
              callbacks.onMessage?.(parsed);
            }
          }
        }

        // 处理缓冲区中最后剩余的内容
        if (buffer.trim()) {
          const parsed = parseSSEEvent<T>(buffer);
          if (parsed) {
            callbacks.onMessage?.(parsed);
          }
        }

        callbacks.onClose?.();
      } catch (err) {
        // 主动中断不视为错误
        if ((err as Error).name === 'AbortError') {
          callbacks.onClose?.();
          return;
        }
        callbacks.onError?.(err as Error);
      } finally {
        abortControllerRef.current = null;
        setIsStreaming(false);
      }
    },
    []
  );

  return { connectSSE, abort, isStreaming };
}

/**
 * 解析单条 SSE 事件文本。
 * 支持 `data: {...}` 格式。
 */
function parseSSEEvent<T>(raw: string): T | null {
  const lines = raw.split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed.startsWith('data:')) continue;

    const payload = trimmed.slice(5).trim();
    if (!payload || payload === '[DONE]') return null;

    try {
      return JSON.parse(payload) as T;
    } catch {
      // 非 JSON 数据，忽略
      return null;
    }
  }
  return null;
}

export default useSSE;
