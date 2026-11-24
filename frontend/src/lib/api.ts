import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
  AxiosError,
} from 'axios';

import type {
  AnswerMetricsData,
  ApiResponse,
  ChatMessage,
  ChatRequest,
  ChatSession,
  Citation,
  CreateKnowledgeRequest,
  DashboardStats,
  Document,
  DocumentChunk,
  FAQ,
  FAQGenerateRequest,
  FAQUpdateRequest,
  FeedbackPayload,
  FeedbackResponse,
  GeneratedQuestion,
  HotQuestion,
  IntentDistribution,
  InvalidAnalysis,
  KeyRule,
  KnowledgeBase,
  KnowledgeBaseStats,
  LatencyMetricsData,
  LoginRequest,
  LoginResponse,
  MetricsOverview,
  MetricsPeriod,
  MetricsTrendsData,
  PaginatedResponse,
  ProcessingStatus,
  QuestionLog,
  RegisterRequest,
  RetrievalMetricsData,
  Summary,
  TrendData,
  UpdateKnowledgeRequest,
  User,
} from '@/types';

/** localStorage 中存储 access_token 的键名 */
export const ACCESS_TOKEN_KEY = 'campus_access_token';
export const REFRESH_TOKEN_KEY = 'campus_refresh_token';

/* ===========================================
   Axios 实例
   =========================================== */
const apiClient: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/* 请求拦截器：自动携带 Authorization header */
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem(ACCESS_TOKEN_KEY);
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/* 响应拦截器：统一错误处理 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response.data,
  (error: AxiosError<ApiResponse>) => {
    const status = error.response?.status;
    const message =
      error.response?.data?.message ||
      error.response?.data?.errors?.[0]?.message ||
      error.message ||
      '请求失败，请稍后重试';

    // 401 未授权：清理 token 并跳转登录
    if (status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      // 避免在登录页重复跳转
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
      }
    }

    // 统一抛出结构化错误
    return Promise.reject(
      Object.assign(new Error(message), {
        status,
        code: error.response?.data?.code,
        errors: error.response?.data?.errors,
      })
    );
  }
);

/* ===========================================
   通用请求方法
   =========================================== */
async function request<T>(config: AxiosRequestConfig): Promise<T> {
  return apiClient.request<unknown, T>(config);
}

/* ===========================================
   认证 API (auth)
   =========================================== */
export const authApi = {
  login(data: LoginRequest) {
    return request<LoginResponse>({
      method: 'POST',
      url: '/auth/login',
      data,
    });
  },
  register(data: RegisterRequest) {
    return request<LoginResponse>({
      method: 'POST',
      url: '/auth/register',
      data,
    });
  },
  guest() {
    return request<LoginResponse>({
      method: 'POST',
      url: '/auth/guest',
    });
  },
  refresh(refreshToken: string) {
    return request<{ access_token: string }>({
      method: 'POST',
      url: '/auth/refresh',
      data: { refresh_token: refreshToken },
    });
  },
  me() {
    return request<User>({ method: 'GET', url: '/auth/me' });
  },
};

/* ===========================================
   对话 API (chat)
   =========================================== */
export const chatApi = {
  /** 非流式对话 */
  chat(data: ChatRequest) {
    return request<{
      answer: string;
      citations: Citation[];
      session_id: number;
    }>({
      method: 'POST',
      url: '/chat',
      data,
    });
  },
  /** 获取会话历史列表 */
  getHistory(page = 1, pageSize = 20) {
    return request<PaginatedResponse<ChatSession>>({
      method: 'GET',
      url: '/history',
      params: { page, page_size: pageSize },
    });
  },
  /** 获取指定会话的消息列表 */
  getSessionMessages(sessionId: number) {
    return request<ChatMessage[]>({
      method: 'GET',
      url: `/history/${sessionId}`,
    });
  },
  /** 删除会话 */
  deleteSession(sessionId: number) {
    return request<{ message: string; session_id: number }>({
      method: 'DELETE',
      url: `/history/${sessionId}`,
    });
  },
  /** 重命名会话 */
  renameSession(sessionId: number, title: string) {
    return request<ChatSession>({
      method: 'PATCH',
      url: `/history/${sessionId}`,
      data: { title },
    });
  },
  /** 提交消息反馈（点赞/点踩） */
  submitFeedback(messageId: number, data: FeedbackPayload) {
    return request<{ message: string; feedback_id: number | null }>({
      method: 'POST',
      url: `/chat/messages/${messageId}/feedback`,
      data,
    });
  },
  /** 查询当前用户对消息的反馈 */
  getFeedback(messageId: number) {
    return request<FeedbackResponse>({
      method: 'GET',
      url: `/chat/messages/${messageId}/feedback`,
    });
  },
};

/* ===========================================
   知识库 API (knowledge)
   =========================================== */
export const knowledgeApi = {
  list() {
    return request<PaginatedResponse<KnowledgeBase>>({ method: 'GET', url: '/knowledge/list' });
  },
  create(data: CreateKnowledgeRequest) {
    return request<KnowledgeBase>({
      method: 'POST',
      url: '/knowledge/create',
      data,
    });
  },
  detail(knowledgeId: number) {
    return request<KnowledgeBase>({
      method: 'GET',
      url: `/knowledge/${knowledgeId}`,
    });
  },
  update(knowledgeId: number, data: UpdateKnowledgeRequest) {
    return request<KnowledgeBase>({
      method: 'PUT',
      url: `/knowledge/${knowledgeId}`,
      data,
    });
  },
  remove(knowledgeId: number) {
    return request<{ deleted: boolean; documents_count: number }>({
      method: 'DELETE',
      url: `/knowledge/${knowledgeId}`,
    });
  },
  stats(knowledgeId: number) {
    return request<KnowledgeBaseStats>({
      method: 'GET',
      url: `/knowledge/${knowledgeId}/stats`,
    });
  },
};

/* ===========================================
   文档 API (document)
   =========================================== */
export const documentApi = {
  list(knowledgeId: number, page = 1, pageSize = 20) {
    return request<PaginatedResponse<Document>>({
      method: 'GET',
      url: `/documents/${knowledgeId}/list`,
      params: { page, page_size: pageSize },
    });
  },
  upload(knowledgeId: number, file: File, onProgress?: (percent: number) => void) {
    const formData = new FormData();
    formData.append('file', file);
    return request<{ document_id: number; status: string }>({
      method: 'POST',
      url: `/documents/${knowledgeId}/upload`,
      data: formData,
      timeout: 60000,
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded * 100) / e.total));
        }
      },
    });
  },
  detail(documentId: number) {
    return request<Document>({ method: 'GET', url: `/documents/doc/${documentId}` });
  },
  remove(documentId: number) {
    return request<{ message: string; document_id: number }>({
      method: 'DELETE',
      url: `/documents/doc/${documentId}`,
    });
  },
  reindex(documentId: number) {
    return request<Document>({
      method: 'POST',
      url: `/documents/doc/${documentId}/reindex`,
    });
  },
  chunks(documentId: number) {
    return request<DocumentChunk[]>({
      method: 'GET',
      url: `/documents/doc/${documentId}/chunks`,
    });
  },
  processingStatus(knowledgeId: number) {
    return request<ProcessingStatus[]>({
      method: 'GET',
      url: `/documents/${knowledgeId}/processing-status`,
    });
  },
};

/* ===========================================
   引用溯源 API (citation)
   =========================================== */
export const citationApi = {
  detail(citationId: string) {
    return request<Citation>({
      method: 'GET',
      url: `/citation/${citationId}`,
    });
  },
};

/* ===========================================
   智能总结 API (summary)
   =========================================== */
export const summaryApi = {
  getSummary(docId: number) {
    return request<Summary>({
      method: 'GET',
      url: `/summary/document/${docId}`,
    });
  },
  regenerate(docId: number) {
    return request<Summary>({
      method: 'POST',
      url: `/summary/document/${docId}/regenerate`,
    });
  },
  status(docId: number) {
    return request<{ document_id: number; summary_status: string }>({
      method: 'GET',
      url: `/summary/document/${docId}/status`,
    });
  },
  keyRules(docId: number) {
    return request<{ document_id: number; rules: KeyRule[]; total: number }>({
      method: 'GET',
      url: `/summary/document/${docId}/rules`,
    });
  },
  questions(docId: number) {
    return request<{
      document_id: number;
      questions: GeneratedQuestion[];
      total: number;
    }>({
      method: 'GET',
      url: `/summary/document/${docId}/questions`,
    });
  },
};

/* ===========================================
   FAQ API (faq)
   =========================================== */
export const faqApi = {
  list(status?: string, page = 1, pageSize = 20) {
    return request<PaginatedResponse<FAQ>>({
      method: 'GET',
      url: '/faq',
      params: { status, page, page_size: pageSize },
    });
  },
  detail(faqId: number) {
    return request<FAQ>({ method: 'GET', url: `/faq/${faqId}` });
  },
  generate(data: FAQGenerateRequest) {
    return request<{ generated_count: number; skipped_count: number }>({
      method: 'POST',
      url: '/faq/generate',
      data,
    });
  },
  update(faqId: number, data: FAQUpdateRequest) {
    return request<FAQ>({ method: 'PUT', url: `/faq/${faqId}`, data });
  },
  publish(faqId: number) {
    return request<FAQ>({ method: 'POST', url: `/faq/${faqId}/publish` });
  },
  reject(faqId: number, reason?: string) {
    return request<FAQ>({
      method: 'POST',
      url: `/faq/${faqId}/reject`,
      data: { reason },
    });
  },
  remove(faqId: number) {
    return request<{ message: string; faq_id: number }>({
      method: 'DELETE',
      url: `/faq/${faqId}`,
    });
  },
};

/* ===========================================
   统计分析 API (analytics)
   =========================================== */
export const analyticsApi = {
  hotQuestions(period: string = 'week', topK: number = 10) {
    return request<{ period: string; total: number; items: HotQuestion[] }>({
      method: 'GET',
      url: '/analytics/hot-questions',
      params: { period, top_k: topK },
    });
  },
  trends(
    type: 'daily' | 'weekly' | 'monthly' = 'daily',
    options: { days?: number; weeks?: number; months?: number } = {}
  ) {
    return request<TrendData>({
      method: 'GET',
      url: '/analytics/trends',
      params: { type, ...options },
    });
  },
  intentDistribution(period: string = 'week') {
    return request<IntentDistribution>({
      method: 'GET',
      url: '/analytics/intent-distribution',
      params: { period },
    });
  },
  invalidAnalysis(period: string = 'month') {
    return request<InvalidAnalysis>({
      method: 'GET',
      url: '/analytics/invalid-analysis',
      params: { period },
    });
  },
  refresh() {
    return request<{ message: string; status: string }>({
      method: 'POST',
      url: '/analytics/refresh',
    });
  },
};

/* ===========================================
   用户 API (user)
   =========================================== */
export const userApi = {
  profile() {
    return request<User>({ method: 'GET', url: '/user/profile' });
  },
  updateProfile(data: Partial<User>) {
    return request<User>({ method: 'PUT', url: '/user/profile', data });
  },
  conversations() {
    return request<{ total: number; items: ChatSession[] }>({
      method: 'GET',
      url: '/user/conversations',
    });
  },
  /** 管理端：获取用户列表 */
  list(page = 1, pageSize = 20, keyword?: string) {
    return request<PaginatedResponse<User>>({
      method: 'GET',
      url: '/user',
      params: { page, page_size: pageSize, keyword },
    });
  },
  /** 管理端：更新用户角色 */
  updateRole(userId: number, role: 'user' | 'admin') {
    return request<User>({
      method: 'PUT',
      url: `/user/${userId}/role`,
      data: { role },
    });
  },
  /** 管理端：启用/禁用用户 */
  updateStatus(userId: number, isActive: boolean) {
    return request<User>({
      method: 'PUT',
      url: `/user/${userId}/status`,
      data: { is_active: isActive },
    });
  },
};

/* ===========================================
   系统统计 API (stats)
   =========================================== */
export const statsApi = {
  dashboard() {
    return request<DashboardStats>({ method: 'GET', url: '/stats/dashboard' });
  },
  usage() {
    return request<QuestionLog[]>({ method: 'GET', url: '/stats/usage' });
  },
};

/* ===========================================
   评价指标 API (metrics)
   =========================================== */
export const metricsApi = {
  overview(period: MetricsPeriod = 'week', knowledgeBaseId?: number) {
    return request<MetricsOverview>({
      method: 'GET',
      url: '/metrics/overview',
      params: { period, knowledge_base_id: knowledgeBaseId },
    });
  },
  retrieval(period: MetricsPeriod = 'week', knowledgeBaseId?: number) {
    return request<RetrievalMetricsData>({
      method: 'GET',
      url: '/metrics/retrieval',
      params: { period, knowledge_base_id: knowledgeBaseId },
    });
  },
  answer(period: MetricsPeriod = 'week', knowledgeBaseId?: number) {
    return request<AnswerMetricsData>({
      method: 'GET',
      url: '/metrics/answer',
      params: { period, knowledge_base_id: knowledgeBaseId },
    });
  },
  latency(period: MetricsPeriod = 'week', knowledgeBaseId?: number) {
    return request<LatencyMetricsData>({
      method: 'GET',
      url: '/metrics/latency',
      params: { period, knowledge_base_id: knowledgeBaseId },
    });
  },
  trends(
    metricType: 'latency' | 'retrieval' | 'answer' = 'latency',
    period: MetricsPeriod = 'week',
    knowledgeBaseId?: number,
  ) {
    return request<MetricsTrendsData>({
      method: 'GET',
      url: '/metrics/trends',
      params: { metric_type: metricType, period, knowledge_base_id: knowledgeBaseId },
    });
  },
};

export default apiClient;
