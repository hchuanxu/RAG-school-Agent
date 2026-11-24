'use client';

import Link from 'next/link';
import {
  MessageSquare,
  BookOpen,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  FileSearch,
  TrendingUp,
  Bot,
  Search,
  FileCheck,
  CheckCircle2,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Logo } from '@/components/ui/logo';

const features = [
  {
    icon: MessageSquare,
    title: '智能问答',
    description: '基于多源知识库的精准回答，支持多轮对话与上下文理解，SSE 流式逐字输出。',
  },
  {
    icon: FileSearch,
    title: '答案溯源',
    description: '每条回答均附带文档引用，可定位到具体文件名、页码与所属知识库。',
  },
  {
    icon: BookOpen,
    title: '知识库管理',
    description: '支持 PDF / DOCX / TXT 文档上传，自动解析、递归切片与向量化入库。',
  },
  {
    icon: TrendingUp,
    title: '数据分析',
    description: '热门问题、意图分布、趋势统计，管理员实时掌握校园问答动态。',
  },
  {
    icon: ShieldCheck,
    title: '安全可控',
    description: 'JWT 认证、角色权限分离，内容审核 Agent 自动过滤敏感信息。',
  },
  {
    icon: Sparkles,
    title: '智能总结',
    description: '上传文档自动生成摘要、重点条例与可提问考点，4 级 JSON 解析容错。',
  },
];

const workflowSteps = [
  { icon: Search, title: '意图识别', desc: '7 类意图分类路由' },
  { icon: BookOpen, title: '文档检索', desc: '向量 + 关键词混合检索' },
  { icon: FileCheck, title: '引用溯源', desc: '提取文件名 / 页码来源' },
  { icon: Bot, title: '回答生成', desc: 'Markdown 结构化输出' },
  { icon: CheckCircle2, title: '内容审核', desc: '幻觉检测 + 敏感词过滤' },
];

export default function HomePage() {
  return (
    <div className="relative flex min-h-screen flex-col bg-white">
      {/* 全局朦胧光晕背景 */}
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -left-40 -top-40 h-[500px] w-[500px] rounded-full bg-primary-200/30 blur-[120px]" />
        <div className="absolute right-0 top-1/4 h-[420px] w-[420px] rounded-full bg-primary-100/40 blur-[110px]" />
        <div className="absolute left-1/4 top-1/2 h-[480px] w-[480px] rounded-full bg-success-50/50 blur-[130px]" />
        <div className="absolute -right-32 bottom-0 h-[400px] w-[400px] rounded-full bg-primary-50/60 blur-[100px]" />
      </div>

      {/* 顶部导航 */}
      <header className="sticky top-0 z-40 border-b border-gray-100/80 bg-white/70 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 md:px-6">
          <Link href="/" className="flex items-center gap-2">
            <Logo size="sm" showText />
          </Link>
          <div className="flex items-center gap-2">
            <Link href="/login">
              <Button variant="ghost" size="sm">
                登录
              </Button>
            </Link>
            <Link href="/login?mode=register">
              <Button size="sm">开始使用</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero 区 — 左右分栏 */}
      <section className="relative">
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 md:grid-cols-2 md:px-6 md:py-24">
          {/* 左侧：标题 + CTA */}
          <div className="flex flex-col items-start">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-primary-50 px-3.5 py-1.5 text-sm font-medium text-primary-700">
              <Sparkles className="h-4 w-4" />
              多源知识库 · 智能问答 · 答案溯源
            </span>
            <h1 className="mt-6 text-4xl font-bold leading-tight tracking-tight text-gray-900 md:text-5xl">
              启明
              <span className="bg-gradient-to-r from-primary-600 to-primary-400 bg-clip-text text-transparent">
                {' '}
                校园智能问答
              </span>
            </h1>
            <p className="mt-5 max-w-md text-lg leading-relaxed text-gray-600">
              整合学生手册、奖学金政策、教务规定等多源校园知识，基于
              RAG 与多智能体技术，为师生提供精准、可溯源的智能问答服务。
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link href="/login">
                <Button
                  size="lg"
                  rightIcon={<ArrowRight className="h-4 w-4" />}
                >
                  立即体验
                </Button>
              </Link>
              <Link href="/login?mode=guest">
                <Button variant="secondary" size="lg">
                  访客模式
                </Button>
              </Link>
            </div>

            {/* 数据指标 */}
            <div className="mt-10 flex gap-8">
              {[
                { value: '7×24', label: '全天候服务' },
                { value: '秒级', label: '响应速度' },
                { value: '100%', label: '答案可溯源' },
              ].map((item) => (
                <div key={item.label}>
                  <p className="text-2xl font-bold text-primary-600">
                    {item.value}
                  </p>
                  <p className="mt-0.5 text-sm text-gray-500">{item.label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* 右侧：聊天预览卡片 */}
          <div className="relative">
            <div className="absolute -inset-4 -z-10 rounded-3xl bg-gradient-to-br from-primary-100/50 to-primary-50/50 blur-2xl" />
            <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-xl">
              {/* 卡片头部 */}
              <div className="flex items-center gap-2.5 border-b border-gray-100 px-5 py-3.5">
                <Logo size="sm" />
                <span className="text-sm font-semibold text-gray-700">
                  智能问答
                </span>
                <span className="ml-auto flex items-center gap-1 text-xs text-gray-400">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-success-500" />
                  在线
                </span>
              </div>

              {/* 聊天内容预览 */}
              <div className="space-y-4 px-5 py-6">
                {/* 用户消息 */}
                <div className="flex justify-end">
                  <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-primary-600 px-4 py-2.5 text-sm text-white">
                    奖学金申请需要哪些材料？
                  </div>
                </div>

                {/* AI 回答 */}
                <div className="flex gap-2.5">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-primary-700">
                    <Bot className="h-4 w-4 text-white" />
                  </div>
                  <div className="max-w-[80%] space-y-2">
                    <div className="rounded-2xl rounded-tl-sm bg-gray-50 px-4 py-3 text-sm leading-relaxed text-gray-700 ring-1 ring-gray-100">
                      <p className="mb-2 font-medium text-gray-900">
                        奖学金申请所需材料：
                      </p>
                      <ul className="space-y-1 text-gray-600">
                        <li>• 奖学金申请表（教务处领取）</li>
                        <li>• 本学年成绩单（加盖公章）</li>
                        <li>• 个人陈述（不少于 800 字）</li>
                        <li>• 两名教师推荐信</li>
                      </ul>
                    </div>
                    <div className="flex items-center gap-1.5 rounded-lg bg-primary-50 px-3 py-1.5 text-xs text-primary-600">
                      <FileSearch className="h-3 w-3" />
                      来源：奖学金管理办法.pdf · 第 3 页
                    </div>
                  </div>
                </div>
              </div>

              {/* 输入框预览 */}
              <div className="border-t border-gray-100 px-5 py-3">
                <div className="flex items-center gap-2 rounded-full border border-gray-200 bg-gray-50 px-4 py-2">
                  <span className="text-sm text-gray-400">
                    输入你的问题…
                  </span>
                  <span className="ml-auto flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-primary-600 text-white">
                    <ArrowRight className="h-3.5 w-3.5" />
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 工作流展示区 */}
      <section className="border-y border-gray-100/50 bg-white/40 backdrop-blur-sm py-20">
        <div className="mx-auto max-w-6xl px-4 md:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-2xl font-bold text-gray-900 md:text-3xl">
              五智能体协同工作流
            </h2>
            <p className="mt-3 text-gray-600">
              基于 LangGraph 构建，每个问题经过五个智能体节点逐层处理，确保回答准确可信。
            </p>
          </div>

          <div className="mt-12 flex flex-col items-center gap-3 md:flex-row md:justify-between md:gap-0">
            {workflowSteps.map((step, idx) => (
              <div key={step.title} className="flex items-center gap-3 md:gap-0">
                <div className="flex flex-col items-center text-center">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white shadow-sm ring-1 ring-gray-100 transition-transform hover:scale-110 hover:shadow-md hover:ring-primary-200">
                    <step.icon className="h-6 w-6 text-primary-600" />
                  </div>
                  <p className="mt-2.5 text-sm font-semibold text-gray-900">
                    {step.title}
                  </p>
                  <p className="mt-0.5 text-xs text-gray-500">{step.desc}</p>
                </div>
                {idx < workflowSteps.length - 1 && (
                  <div className="mx-3 hidden h-px w-12 bg-gradient-to-r from-primary-300 to-primary-200 md:block" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 功能特性 */}
      <section className="bg-transparent py-20">
        <div className="mx-auto max-w-6xl px-4 md:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-2xl font-bold text-gray-900 md:text-3xl">
              为校园而生的一站式问答
            </h2>
            <p className="mt-3 text-gray-600">
              覆盖学生手册、教务规定、奖学金政策等核心场景，让信息触手可及。
            </p>
          </div>

          <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="group rounded-xl border border-gray-200 bg-white p-6 transition-all duration-300 hover:-translate-y-1 hover:border-primary-200 hover:shadow-lg hover:shadow-primary-50"
              >
                <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-primary-50 text-primary-600 transition-all duration-300 group-hover:scale-110 group-hover:bg-primary-600 group-hover:text-white">
                  <feature.icon className="h-5 w-5" />
                </span>
                <h3 className="mt-4 text-base font-semibold text-gray-900">
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA 区 */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-600 to-primary-700 py-20">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -left-20 -top-20 h-72 w-72 rounded-full bg-white/5 blur-3xl" />
          <div className="absolute -bottom-20 -right-20 h-72 w-72 rounded-full bg-white/5 blur-3xl" />
        </div>
        <div className="relative mx-auto max-w-4xl px-4 text-center md:px-6">
          <h2 className="text-3xl font-bold text-white md:text-4xl">
            准备好开始了吗？
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-primary-100">
            立即创建账号，体验智能化的校园问答服务。无需复杂配置，开箱即用。
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link href="/login?mode=register" className="w-full sm:w-auto">
              <Button
                size="lg"
                variant="secondary"
                className="w-full bg-white text-primary-700 hover:bg-gray-50"
                rightIcon={<ArrowRight className="h-4 w-4" />}
              >
                免费注册
              </Button>
            </Link>
            <Link href="/login" className="w-full sm:w-auto">
              <Button
                size="lg"
                className="w-full border border-white/30 bg-transparent text-white hover:bg-white/10"
              >
                已有账号，去登录
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* 页脚 */}
      <footer className="border-t border-gray-100/50 bg-white/50 backdrop-blur-sm py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 md:flex-row md:px-6">
          <div className="flex items-center gap-2">
            <Logo size="sm" />
            <span className="text-sm text-gray-600">
              启明校园智能问答 © {new Date().getFullYear()}
            </span>
          </div>
          <p className="text-xs text-gray-400">
            基于 Next.js + FastAPI + LangGraph 构建
          </p>
        </div>
      </footer>
    </div>
  );
}
