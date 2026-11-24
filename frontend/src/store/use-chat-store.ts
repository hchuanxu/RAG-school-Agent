'use client';

import { create } from 'zustand';

import { chatApi } from '@/lib/api';
import type { ChatMessage, ChatSession } from '@/types';

interface ChatState {
  /** 所有会话列表 */
  sessions: ChatSession[];
  /** 当前会话 ID */
  currentSessionId: number | null;
  /** 当前会话的消息列表 */
  messages: ChatMessage[];
  /** 是否正在加载会话列表 */
  isLoadingSessions: boolean;
  /** 是否正在加载消息 */
  isLoadingMessages: boolean;

  fetchSessions: () => Promise<void>;
  createSession: (title?: string) => void;
  switchSession: (sessionId: number | null) => Promise<void>;
  deleteSession: (sessionId: number) => Promise<void>;
  renameSession: (sessionId: number, title: string) => Promise<void>;
  setCurrentSessionId: (sessionId: number) => void;
  addMessage: (message: ChatMessage) => void;
  updateMessage: (id: number | string, updates: Partial<ChatMessage>) => void;
  clearMessages: () => void;
  reset: () => void;
}

/**
 * 对话状态管理。
 */
export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  currentSessionId: null,
  messages: [],
  isLoadingSessions: false,
  isLoadingMessages: false,

  fetchSessions: async () => {
    set({ isLoadingSessions: true });
    try {
      const res = await chatApi.getHistory(1, 50);
      // 响应拦截器已拆包 response.data，res 即 PaginatedResponse 对象
      const items = (res as { items?: ChatSession[] })?.items ?? [];
      set({ sessions: items });
    } catch (err) {
      console.error('获取会话列表失败:', err);
    } finally {
      set({ isLoadingSessions: false });
    }
  },

  createSession: (title) => {
    // 本地新建空会话，待首次发送消息后由后端返回真实 session_id
    set({
      currentSessionId: null,
      messages: [],
      sessions: [
        {
          id: 0,
          user_id: 0,
          title: title || '新对话',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          message_count: 0,
        },
        ...get().sessions,
      ],
    });
  },

  switchSession: async (sessionId) => {
    if (sessionId === null) {
      set({ currentSessionId: null, messages: [] });
      return;
    }
    set({ currentSessionId: sessionId, isLoadingMessages: true });
    try {
      const messages = await chatApi.getSessionMessages(sessionId);
      set({ messages });
    } catch (err) {
      console.error('获取会话消息失败:', err);
      set({ messages: [] });
    } finally {
      set({ isLoadingMessages: false });
    }
  },

  deleteSession: async (sessionId) => {
    try {
      await chatApi.deleteSession(sessionId);
      const { currentSessionId, sessions } = get();
      set({
        sessions: sessions.filter((s) => s.id !== sessionId),
        ...(currentSessionId === sessionId
          ? { currentSessionId: null, messages: [] }
          : {}),
      });
    } catch (err) {
      console.error('删除会话失败:', err);
    }
  },

  renameSession: async (sessionId, title) => {
    try {
      await chatApi.renameSession(sessionId, title);
      set((state) => ({
        sessions: state.sessions.map((s) =>
          s.id === sessionId ? { ...s, title } : s
        ),
      }));
    } catch (err) {
      console.error('重命名会话失败:', err);
    }
  },

  setCurrentSessionId: (sessionId) =>
    set((state) => ({
      currentSessionId: sessionId,
      // 后端返回真实 session_id 后，移除本地占位会话（id=0）
      sessions:
        sessionId > 0
          ? state.sessions.filter((s) => s.id !== 0)
          : state.sessions,
    })),

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  updateMessage: (id, updates) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, ...updates } : m
      ),
    })),

  clearMessages: () => set({ messages: [] }),

  reset: () =>
    set({
      sessions: [],
      currentSessionId: null,
      messages: [],
    }),
}));

export default useChatStore;
