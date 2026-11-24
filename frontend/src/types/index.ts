// ===========================================
// 启明校园智能问答 - 前端类型定义
// ===========================================

/* ---------------- 用户与认证 ---------------- */
export type UserRole = 'user' | 'admin';

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  avatar?: string;
  created_at?: string;
  last_login_at?: string;
  is_active?: boolean;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface LoginResponse extends AuthTokens {
  user: User;
}

/* ---------------- 知识库 ---------------- */
export interface KnowledgeBase {
  id: number;
  name: string;
  description?: string;
  is_public: boolean;
  document_count: number;
  created_at: string;
  updated_at?: string;
  status?: 'active' | 'inactive';
}

export interface KnowledgeBaseStats {
  knowledge_id: number;
  document_count: number;
  total_chunks: number;
  total_size: number;
}

export interface CreateKnowledgeRequest {
  name: string;
  description?: string;
  is_public?: boolean;
}

export type UpdateKnowledgeRequest = Partial<CreateKnowledgeRequest>;

/* ---------------- 文档 ---------------- */
export type DocumentStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed';

export type DocumentType = 'pdf' | 'docx' | 'txt';

export interface Document {
  id: number;
  knowledge_base_id: number;
  filename: string;
  file_type: DocumentType;
  size: number;
  status: DocumentStatus;
  chunk_count: number;
  uploaded_at: string;
  processed_at?: string;
  error_message?: string;
}

export interface DocumentChunk {
  id: number;
  document_id: number;
  chunk_index: number;
  content: string;
  page?: number;
  paragraph?: number;
}

export interface ProcessingStatus {
  document_id: number;
  filename: string;
  status: DocumentStatus;
  progress: number;
  error_message?: string;
}

/* ---------------- 对话 ---------------- */
export type MessageRole = 'user' | 'assistant' | 'system';

export interface ChatSession {
  id: number;
  user_id: number;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatMessage {
  id?: number;
  session_id?: number;
  role: MessageRole;
  content: string;
  citations?: Citation[];
  created_at?: string;
  /** 是否处于流式输出中 */
  streaming?: boolean;
}

export interface ChatRequest {
  question: string;
  session_id?: number;
  knowledge_base_ids?: number[];
}

/** SSE 流式消息事件类型 */
export type SSEEventType = 'session' | 'token' | 'citations' | 'done' | 'error';

export interface SSEEvent {
  type: SSEEventType;
  content?: string;
  data?: Citation | unknown;
  citations?: Citation[];
  message?: string;
  session_id?: number;
  message_id?: number;
}

/* ---------------- 引用溯源 ---------------- */
export interface Citation {
  citation_id?: string;
  document_id?: number;
  filename?: string;
  /** 后端字段名（与 filename 同义） */
  file_name?: string;
  knowledge_base_name?: string;
  /** 后端字段名（与 knowledge_base_name 同义） */
  knowledge_base?: string;
  page?: number;
  paragraph?: number;
  chunk_index?: number;
  content_preview?: string;
  full_content?: string;
  similarity_score?: number;
  uploaded_at?: string;
}

/* ---------------- FAQ ---------------- */
export type FAQStatus = 'pending' | 'published' | 'rejected';

export interface FAQ {
  id: number;
  question: string;
  answer: string;
  source_documents?: string[];
  status: FAQStatus;
  created_at: string;
  updated_at?: string;
  hit_count?: number;
}

export interface FAQGenerateRequest {
  threshold?: number;
}

export interface FAQUpdateRequest {
  question?: string;
  answer?: string;
  source_documents?: string[];
}

/* ---------------- 问题日志 ---------------- */
export type QuestionIntent =
  | 'campus_policy'
  | 'academic'
  | 'scholarship'
  | 'invalid'
  | 'other';

export type QuestionLogValidity = 'valid' | 'invalid';

export interface QuestionLog {
  id: number;
  user_id?: number;
  session_id?: number;
  question: string;
  intent: QuestionIntent;
  is_valid: QuestionLogValidity;
  response_time?: number;
  created_at: string;
}

/* ---------------- 智能总结 ---------------- */
export interface Summary {
  document_id: number;
  summary: string;
  status: DocumentStatus;
  created_at?: string;
}

export interface KeyRule {
  id: number;
  document_id: number;
  rule_text: string;
  category?: string;
  order?: number;
}

export interface GeneratedQuestion {
  id: number;
  document_id: number;
  question: string;
  answer?: string;
  type?: 'choice' | 'short_answer' | 'essay';
  difficulty?: 'easy' | 'medium' | 'hard';
}

/* ---------------- 统计分析 ---------------- */
export interface HotQuestion {
  question: string;
  count: number;
  intent?: QuestionIntent;
}

export interface TrendDataPoint {
  date: string;
  count: number;
  valid_count?: number;
  invalid_count?: number;
}

export interface TrendData {
  type: 'daily' | 'weekly' | 'monthly';
  total: number;
  items: TrendDataPoint[];
}

export interface IntentDistributionItem {
  intent: QuestionIntent;
  count: number;
  percentage: number;
}

export interface IntentDistribution {
  period: string;
  total: number;
  items: IntentDistributionItem[];
}

export interface InvalidAnalysis {
  period: string;
  total: number;
  invalid_count: number;
  samples: Array<{
    question: string;
    reason?: string;
    created_at: string;
  }>;
  suggestions?: string[];
}

export interface DashboardStats {
  total_questions: number;
  total_knowledge_bases: number;
  total_users: number;
  today_questions: number;
  questions_change?: number;
  users_change?: number;
}

/* ---------------- 通用响应 ---------------- */
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
  errors?: Array<{
    field: string;
    message: string;
  }>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/* ---------------- 评价指标 ---------------- */
export type MetricsPeriod = 'day' | 'week' | 'month' | 'all';

export interface RetrievalMetricsData {
  period: string;
  total_queries: number;
  hit_rate: number;
  mrr: number;
  avg_retrieved_count: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  trends: Array<{ date: string; count: number; hits: number }>;
}

export interface AnswerMetricsData {
  period: string;
  answer: {
    total_answers: number;
    citation_rate: number;
    avg_citation_count: number;
    hallucination_rate: number;
    rejection_rate: number;
    avg_retry_count: number;
    avg_answer_length: number;
  };
  feedback: {
    upvote_count: number;
    downvote_count: number;
    total_feedback: number;
    downvote_rate: number;
    avg_rating: number | null;
  };
}

export interface LatencyMetricsData {
  period: string;
  total_requests: number;
  avg_ttft_ms: number;
  p50_ttft_ms: number;
  p95_ttft_ms: number;
  avg_e2e_ms: number;
  p50_e2e_ms: number;
  p95_e2e_ms: number;
  p99_e2e_ms: number;
  avg_retrieval_latency_ms: number;
  avg_generation_latency_ms: number;
  qpm: number;
}

export interface MetricsOverview {
  period: string;
  retrieval: {
    total_queries: number;
    hit_rate: number;
    avg_retrieved_count: number;
  };
  answer: {
    total_answers: number;
    citation_rate: number;
    downvote_rate: number;
    hallucination_rate: number;
  };
  latency: {
    total_requests: number;
    avg_ttft_ms: number;
    p95_e2e_ms: number;
  };
  business: {
    total_feedback: number;
    upvote_count: number;
    downvote_count: number;
  };
}

export interface MetricsTrendItem {
  date: string;
  count?: number;
  hits?: number;
  total?: number;
  citations?: number;
  downvotes?: number;
  avg_e2e_ms?: number;
  p95_e2e_ms?: number;
}

export interface MetricsTrendsData {
  metric_type: string;
  period: string;
  items: MetricsTrendItem[];
}

export type FeedbackType = 'upvote' | 'downvote';

export interface FeedbackPayload {
  feedback_type: FeedbackType;
  rating?: number;
  feedback_text?: string;
}

export interface FeedbackResponse {
  feedback_type: FeedbackType | null;
  rating: number | null;
  feedback_text: string | null;
}
