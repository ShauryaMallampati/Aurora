'use client';

import { Navigation } from '@/shared/Navigation';
import { PerformanceDashboard } from '@/components/performance-dashboard';

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      <Navigation />
      <div className="max-w-6xl mx-auto px-6 py-10">
        <PerformanceDashboard />
      </div>
    </div>
  );
}
