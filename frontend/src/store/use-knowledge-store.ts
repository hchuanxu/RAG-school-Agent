'use client';

import { create } from 'zustand';

import { knowledgeApi } from '@/lib/api';
import type { KnowledgeBase } from '@/types';

interface KnowledgeState {
  /** 知识库列表 */
  knowledgeBases: KnowledgeBase[];
  /** 当前选中的知识库 */
  currentKB: KnowledgeBase | null;
  /** 是否正在加载 */
  isLoading: boolean;
  /** 错误信息 */
  error: string | null;

  fetchKnowledgeBases: () => Promise<void>;
  selectKB: (kb: KnowledgeBase | null) => void;
  selectKBById: (id: number | null) => void;
  setError: (error: string | null) => void;
}

/**
 * 知识库状态管理。
 */
export const useKnowledgeStore = create<KnowledgeState>((set, get) => ({
  knowledgeBases: [],
  currentKB: null,
  isLoading: false,
  error: null,

  fetchKnowledgeBases: async () => {
    set({ isLoading: true, error: null });
    try {
      const list = await knowledgeApi.list();
      // 后端返回 PaginatedResponse<KnowledgeBase>（含 items 字段），兼容数组形式
      const items = Array.isArray(list) ? list : list?.items ?? [];
      set({ knowledgeBases: items });

      // 若当前未选中知识库且列表非空，默认选中第一个公开库
      if (!get().currentKB && items.length > 0) {
        const publicKb = items.find((k) => k.is_public) ?? items[0];
        set({ currentKB: publicKb });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '获取知识库失败';
      set({ error: message, knowledgeBases: [] });
    } finally {
      set({ isLoading: false });
    }
  },

  selectKB: (kb) => set({ currentKB: kb }),

  selectKBById: (id) => {
    if (id === null) {
      set({ currentKB: null });
      return;
    }
    const target = get().knowledgeBases.find((k) => k.id === id);
    if (target) {
      set({ currentKB: target });
    }
  },

  setError: (error) => set({ error }),
}));

export default useKnowledgeStore;
