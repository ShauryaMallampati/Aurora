'use client';

import { Navigation } from '@/shared/Navigation';
import { PerformanceDashboard } from '@/components/performance-dashboard';

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-950">
      {/* Navigation */}
      <Navigation />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <PerformanceDashboard />
      </div>
    </div>
  );
}
