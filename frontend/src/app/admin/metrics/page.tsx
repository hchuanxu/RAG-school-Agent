'use client';

import { MetricsDashboard } from '@/components/admin/metrics-dashboard';

export default function MetricsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">评价指标</h1>
        <p className="mt-1 text-sm text-gray-500">
          量化系统效果与质量的评价指标体系
        </p>
      </div>
      <MetricsDashboard />
    </div>
  );
}
