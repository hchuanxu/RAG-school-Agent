'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  FileText,
  ListChecks,
  HelpCircle,
  RefreshCw,
  Send,
  Inbox,
} from 'lucide-react';

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/ui/loading';
import { summaryApi } from '@/lib/api';
import type { GeneratedQuestion, KeyRule, Summary } from '@/types';
import { cn } from '@/lib/utils';

type TabKey = 'summary' | 'rules' | 'questions';

export interface SummaryViewProps {
  /** 文档 ID */
  documentId: number;
  /** 点击考点提问 */
  onAskQuestion?: (question: string) => void;
}

const tabs = [
  { key: 'summary' as const, label: '摘要', icon: FileText },
  { key: 'rules' as const, label: '重点条例', icon: ListChecks },
  { key: 'questions' as const, label: '可提问考点', icon: HelpCircle },
];

const difficultyMap: Record<string, { label: string; variant: 'success' | 'warning' | 'error' }> = {
  easy: { label: '简单', variant: 'success' },
  medium: { label: '中等', variant: 'warning' },
  hard: { label: '困难', variant: 'error' },
};

const typeMap: Record<string, string> = {
  choice: '选择题',
  short_answer: '简答题',
  essay: '论述题',
};

/**
 * 文档总结面板。
 * 切换“摘要 / 重点条例 / 可提问考点”，按需调用 summary API。
 */
export function SummaryView({ documentId, onAskQuestion }: SummaryViewProps) {
  const [tab, setTab] = useState<TabKey>('summary');
  const [summary, setSummary] = useState<Summary | null>(null);
  const [rules, setRules] = useState<KeyRule[]>([]);
  const [questions, setQuestions] = useState<GeneratedQuestion[]>([]);
  const [loaded, setLoaded] = useState<Record<TabKey, boolean>>({
    summary: false,
    rules: false,
    questions: false,
  });
  const [loading, setLoading] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSummary = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await summaryApi.getSummary(documentId);
      setSummary(res);
      setLoaded((p) => ({ ...p, summary: true }));
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取摘要失败');
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  const loadRules = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await summaryApi.keyRules(documentId);
      setRules(res.rules || []);
      setLoaded((p) => ({ ...p, rules: true }));
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取重点条例失败');
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  const loadQuestions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await summaryApi.questions(documentId);
      setQuestions(res.questions || []);
      setLoaded((p) => ({ ...p, questions: true }));
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取考点失败');
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  // 切换 tab 时按需加载
  useEffect(() => {
    if (tab === 'summary' && !loaded.summary) void loadSummary();
    else if (tab === 'rules' && !loaded.rules) void loadRules();
    else if (tab === 'questions' && !loaded.questions) void loadQuestions();
  }, [tab, loaded, loadSummary, loadRules, loadQuestions]);

  // 文档变化时重置
  useEffect(() => {
    setSummary(null);
    setRules([]);
    setQuestions([]);
    setLoaded({ summary: false, rules: false, questions: false });
    setTab('summary');
    setError(null);
  }, [documentId]);

  const handleRegenerate = async () => {
    setRegenerating(true);
    setError(null);
    try {
      const res = await summaryApi.regenerate(documentId);
      setSummary(res);
      setRules([]);
      setQuestions([]);
      setLoaded({ summary: true, rules: false, questions: false });
      setTab('summary');
    } catch (err) {
      setError(err instanceof Error ? err.message : '重新生成失败');
    } finally {
      setRegenerating(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Tab 切换 + 重新生成 */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="inline-flex rounded-lg border border-gray-200 bg-white p-1">
          {tabs.map((t) => {
            const active = tab === t.key;
            return (
              <button
                key={t.key}
                type="button"
                onClick={() => setTab(t.key)}
                className={cn(
                  'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                  active
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                )}
              >
                <t.icon className="h-4 w-4" />
                {t.label}
              </button>
            );
          })}
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={handleRegenerate}
          loading={regenerating}
          leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
        >
          重新生成
        </Button>
      </div>

      {error && (
        <div
          className="rounded-md bg-error-50 px-3 py-2 text-sm text-error-600"
          role="alert"
        >
          {error}
        </div>
      )}

      {/* 内容区 */}
      {loading ? (
        <Card bodyPadding={false} className="flex items-center justify-center p-10">
          <Spinner label="加载中..." />
        </Card>
      ) : tab === 'summary' ? (
        <Card title="文档摘要">
          {summary?.summary ? (
            <p className="whitespace-pre-wrap leading-relaxed text-gray-700">
              {summary.summary}
            </p>
          ) : (
            <EmptyState text="暂无摘要，点击“重新生成”尝试生成" />
          )}
        </Card>
      ) : tab === 'rules' ? (
        <Card title="重点条例" description={`共 ${rules.length} 条`}>
          {rules.length > 0 ? (
            <ul className="space-y-3">
              {rules.map((rule) => (
                <li
                  key={rule.id}
                  className="rounded-lg border border-gray-100 bg-gray-50/50 p-3"
                >
                  <div className="mb-1 flex items-center gap-2">
                    {rule.category && (
                      <Badge variant="info">{rule.category}</Badge>
                    )}
                    {rule.order != null && (
                      <span className="text-xs text-gray-400">
                        #{rule.order}
                      </span>
                    )}
                  </div>
                  <p className="text-sm leading-relaxed text-gray-700">
                    {rule.rule_text}
                  </p>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState text="暂无重点条例" />
          )}
        </Card>
      ) : (
        <Card title="可提问考点" description={`共 ${questions.length} 题`}>
          {questions.length > 0 ? (
            <div className="grid gap-3">
              {questions.map((q) => {
                const diff = q.difficulty ? difficultyMap[q.difficulty] : null;
                return (
                  <div
                    key={q.id}
                    className="group rounded-lg border border-gray-100 bg-white p-4 transition-all hover:border-primary-200 hover:shadow-sm"
                  >
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      {q.type && (
                        <Badge variant="default">{typeMap[q.type] || q.type}</Badge>
                      )}
                      {diff && <Badge variant={diff.variant}>{diff.label}</Badge>}
                    </div>
                    <p className="font-medium text-gray-900">{q.question}</p>
                    {q.answer && (
                      <p className="mt-2 rounded-md bg-gray-50 p-2 text-sm leading-relaxed text-gray-600">
                        {q.answer}
                      </p>
                    )}
                    {onAskQuestion && (
                      <button
                        type="button"
                        onClick={() => onAskQuestion(q.question)}
                        className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-primary-600 transition-colors hover:text-primary-500"
                      >
                        <Send className="h-3.5 w-3.5" />
                        向助手提问
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <EmptyState text="暂无可提问考点" />
          )}
        </Card>
      )}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-10 text-center">
      <Inbox className="mb-2 h-8 w-8 text-gray-300" />
      <p className="text-sm text-gray-400">{text}</p>
    </div>
  );
}

export default SummaryView;
