'use client';

import { Navigation } from '@/shared/Navigation';
import { OfflineExportPanel } from '@/components/offline-export-panel';

export default function ExportPage() {
  return (
    <div className="min-h-screen bg-gray-950">
      {/* Navigation */}
      <Navigation />

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <OfflineExportPanel />
      </div>
    </div>
  );
}
