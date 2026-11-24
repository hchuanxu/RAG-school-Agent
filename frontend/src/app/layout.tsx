import type { Metadata, Viewport } from 'next';

import '@/styles/globals.css';

export const metadata: Metadata = {
  title: '启明校园智能问答',
  description:
    '基于多源知识库的启明校园智能问答，提供学生手册、奖学金政策、教务规定等一站式问答与溯源服务。',
  keywords: ['校园问答', '知识库', '智能助手', 'RAG', '启明', '校园助手'],
  authors: [{ name: 'Campus Assistant' }],
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#4f46e5',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">
        {children}
      </body>
    </html>
  );
}
