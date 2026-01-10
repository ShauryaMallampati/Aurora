'use client';

import { Navigation } from '@/shared/Navigation';
import { OfflineExportPanel } from '@/components/offline-export-panel';

export default function ExportPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      <Navigation />
      <div className="max-w-4xl mx-auto px-6 py-10">
        <OfflineExportPanel />
      </div>
    </div>
  );
}
