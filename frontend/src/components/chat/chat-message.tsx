'use client';

import { useState } from 'react';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, ThumbsUp, ThumbsDown, Star } from 'lucide-react';

import { Avatar } from '@/components/ui/avatar';
import { TypingDots } from '@/components/ui/loading';
import { CitationList } from './citation-list';
import { chatApi } from '@/lib/api';
import type { ChatMessage as ChatMessageType, FeedbackType } from '@/types';
import { cn, formatDateTime } from '@/lib/utils';

export interface ChatMessageItemProps {
  message: ChatMessageType;
}

/** Markdown 渲染样式映射 */
const markdownComponents: Components = {
  h1: ({ children }) => (
    <h1 className="mb-3 text-xl font-bold text-gray-900">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="mb-2 text-lg font-bold text-gray-900">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="mb-2 text-base font-bold text-gray-900">{children}</h3>
  ),
  p: ({ children }) => (
    <p className="mb-2 leading-relaxed last:mb-0">{children}</p>
  ),
  ul: ({ children }) => (
    <ul className="mb-2 list-disc space-y-1 pl-5">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="mb-2 list-decimal space-y-1 pl-5">{children}</ol>
  ),
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  a: ({ children, href }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="text-primary-600 underline hover:text-primary-500"
    >
      {children}
    </a>
  ),
  code: ({ className, children }) => {
    const isBlock = /language-/.test(className || '');
    if (isBlock) {
      return (
        <code className={cn('text-xs text-gray-100', className)}>{children}</code>
      );
    }
    return (
      <code className="rounded bg-gray-100 px-1 py-0.5 text-[0.85em] text-primary-700">
        {children}
      </code>
    );
  },
  pre: ({ children }) => (
    <pre className="mb-2 overflow-x-auto rounded-lg bg-gray-900 p-3 text-xs">
      {children}
    </pre>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-primary-300 pl-3 italic text-gray-600">
      {children}
    </blockquote>
  ),
  table: ({ children }) => (
    <div className="mb-2 overflow-x-auto">
      <table className="w-full border-collapse text-xs">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border border-gray-200 bg-gray-50 px-2 py-1 text-left font-medium">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="border border-gray-200 px-2 py-1">{children}</td>
  ),
  hr: () => <hr className="my-3 border-gray-200" />,
};

/**
 * 单条消息气泡。
 * 区分 user / assistant 样式，支持 markdown 渲染、流式打字动画与引用来源。
 */
export function ChatMessageItem({ message }: ChatMessageItemProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  const isStreaming = !!message.streaming;
  const showTyping = isAssistant && isStreaming && !message.content;
  const hasCitations =
    isAssistant && !!message.citations && message.citations.length > 0;

  const [feedback, setFeedback] = useState<FeedbackType | null>(null);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [rating, setRating] = useState(0);
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  const handleFeedback = async (type: FeedbackType) => {
    if (!message.id || feedbackLoading) return;

    // 点踩：展开详细反馈表单；点赞：折叠表单
    if (type === 'downvote') {
      setShowFeedbackForm(true);
      setFeedbackSubmitted(false);
    } else {
      setShowFeedbackForm(false);
      setFeedbackSubmitted(false);
    }

    if (feedback === type) return; // 已是该状态，不重复提交
    setFeedbackLoading(true);
    try {
      await chatApi.submitFeedback(message.id, { feedback_type: type });
      setFeedback(type);
    } catch (err) {
      console.error('提交反馈失败', err);
    } finally {
      setFeedbackLoading(false);
    }
  };

  // 提交带评分与文字的详细反馈（仅在点踩后展开）
  const handleSubmitDetailedFeedback = async () => {
    if (!message.id || feedbackLoading) return;
    setFeedbackLoading(true);
    try {
      await chatApi.submitFeedback(message.id, {
        feedback_type: 'downvote',
        rating: rating || undefined,
        feedback_text: feedbackText.trim() || undefined,
      });
      setShowFeedbackForm(false);
      setFeedbackSubmitted(true);
      setRating(0);
      setFeedbackText('');
    } catch (err) {
      console.error('提交反馈失败', err);
    } finally {
      setFeedbackLoading(false);
    }
  };

  const handleCancelFeedback = () => {
    setShowFeedbackForm(false);
    setRating(0);
    setFeedbackText('');
  };

  return (
    <div
      className={cn(
        'flex w-full gap-3.5 animate-fade-in',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* 头像 */}
      {isUser ? (
        <Avatar
          name="我"
          size="md"
          className="shrink-0 bg-primary-600 text-sm text-white"
        />
      ) : (
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-primary-700 text-white shadow-sm">
          <Bot className="h-5 w-5" />
        </div>
      )}

      {/* 气泡内容 */}
      <div
        className={cn(
          'flex min-w-0 max-w-[85%] flex-col gap-1',
          isUser ? 'items-end' : 'items-start'
        )}
      >
        <div
          className={cn(
            'rounded-2xl px-5 py-3 text-base',
            isUser
              ? 'rounded-tr-sm bg-primary-600 text-white'
              : 'rounded-tl-sm bg-white text-gray-800 shadow-sm ring-1 ring-gray-100'
          )}
        >
          {showTyping ? (
            <TypingDots />
          ) : isUser ? (
            <p className="whitespace-pre-wrap break-words leading-relaxed">
              {message.content}
            </p>
          ) : (
            <div
              className={cn(
                'break-words leading-relaxed',
                '[&_p]:my-0'
              )}
            >
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={markdownComponents}
              >
                {message.content}
              </ReactMarkdown>
              {isStreaming && (
                <span className="ml-0.5 inline-block h-5 w-1.5 animate-pulse bg-primary-500 align-middle" />
              )}
            </div>
          )}
        </div>

        {/* 反馈按钮 */}
        {isAssistant && !isStreaming && message.id && (
          <div className="flex items-center gap-1 px-1">
            <button
              type="button"
              onClick={() => handleFeedback('upvote')}
              disabled={feedbackLoading}
              className={cn(
                'flex h-7 w-7 items-center justify-center rounded-full transition-colors',
                feedback === 'upvote'
                  ? 'bg-primary-100 text-primary-600'
                  : 'text-gray-400 hover:bg-gray-100 hover:text-gray-600'
              )}
              aria-label="赞"
            >
              <ThumbsUp className="h-3.5 w-3.5" />
            </button>
            <button
              type="button"
              onClick={() => handleFeedback('downvote')}
              disabled={feedbackLoading}
              className={cn(
                'flex h-7 w-7 items-center justify-center rounded-full transition-colors',
                feedback === 'downvote'
                  ? 'bg-red-100 text-red-600'
                  : 'text-gray-400 hover:bg-gray-100 hover:text-gray-600'
              )}
              aria-label="踩"
            >
              <ThumbsDown className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        {/* 点踩后的详细反馈表单：星级评分 + 文字反馈 */}
        {isAssistant && !isStreaming && showFeedbackForm && (
          <div className="mt-1 w-full max-w-md rounded-lg border border-gray-200 bg-gray-50 p-3">
            <div className="mb-2 flex items-center gap-2">
              <span className="text-xs text-gray-600">评分：</span>
              <div className="flex items-center gap-0.5">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setRating(star)}
                    className="p-0.5 transition-transform hover:scale-110"
                    aria-label={`${star} 星`}
                  >
                    <Star
                      className={cn(
                        'h-4 w-4',
                        star <= rating
                          ? 'fill-primary-500 text-primary-500'
                          : 'fill-none text-gray-300'
                      )}
                    />
                  </button>
                ))}
              </div>
            </div>
            <textarea
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value.slice(0, 200))}
              placeholder="请告诉我们哪里可以改进..."
              maxLength={200}
              rows={3}
              className="w-full resize-none rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-sm text-gray-800 placeholder-gray-400 focus:border-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-400"
            />
            <div className="mt-2 flex items-center justify-between">
              <span className="text-xs text-gray-400">
                {feedbackText.length}/200
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleCancelFeedback}
                  disabled={feedbackLoading}
                  className="rounded-md px-2.5 py-1 text-xs text-gray-500 transition-colors hover:bg-gray-200 disabled:opacity-50"
                >
                  取消
                </button>
                <button
                  type="button"
                  onClick={handleSubmitDetailedFeedback}
                  disabled={
                    feedbackLoading ||
                    (rating === 0 && !feedbackText.trim())
                  }
                  className="rounded-md bg-primary-500 px-2.5 py-1 text-xs text-white transition-colors hover:bg-primary-600 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {feedbackLoading ? '提交中...' : '提交反馈'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 提交成功提示 */}
        {isAssistant && !isStreaming && feedbackSubmitted && (
          <span className="px-1 text-xs text-primary-600">已收到您的反馈</span>
        )}

        {/* 引用来源 */}
        {hasCitations && !isStreaming && (
          <CitationList citations={message.citations!} />
        )}

        {/* 时间戳 */}
        {message.created_at && !isStreaming && (
          <span className="px-1 text-xs text-gray-400">
            {formatDateTime(message.created_at)}
          </span>
        )}
      </div>
    </div>
  );
}

export default ChatMessageItem;
