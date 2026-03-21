'use client';

import { useState } from 'react';
import { Download, FileJson, Globe, Info, AlertCircle } from 'lucide-react';

interface ExportConfig {
  includeModels: boolean;
  includeSimulationLogs: boolean;
  includeDocumentation: boolean;
  includeWebDemo: boolean;
  maxLogSize: number;
}

export function OfflineExportPanel() {
  const [exportConfig, setExportConfig] = useState<ExportConfig>({
    includeModels: true,
    includeSimulationLogs: true,
    includeDocumentation: true,
    includeWebDemo: true,
    maxLogSize: 500, // MB
  });

  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [exportStatus, setExportStatus] = useState<'idle' | 'exporting' | 'completed' | 'error'>('idle');

  const estimateSize = (): string => {
    let size = 0;
    if (exportConfig.includeModels) size += 250; // model files
    if (exportConfig.includeSimulationLogs) size += exportConfig.maxLogSize;
    if (exportConfig.includeDocumentation) size += 50;
    if (exportConfig.includeWebDemo) size += 100;
    return `~${size} MB`;
  };

  const handleExport = async () => {
    setIsExporting(true);
    setExportStatus('exporting');
    setExportProgress(10);

    try {
      const response = await fetch('/api/export/offline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(exportConfig),
      });

      if (response.ok) {
        setExportProgress(70);
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'aurora-offline-manifest.json';
        a.click();
        URL.revokeObjectURL(url);

        setExportStatus('completed');
        setExportProgress(100);
      } else {
        setExportStatus('error');
      }
    } catch (error) {
      console.error('Export error:', error);
      setExportStatus('error');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-md border border-slate-700 bg-slate-900 p-6">
        <div className="flex items-center gap-3 mb-2">
          <FileJson className="w-6 h-6 text-slate-300" />
          <h2 className="text-2xl font-semibold text-white">Offline export</h2>
        </div>
        <p className="text-slate-400">Generate a downloadable manifest for offline review.</p>
      </div>

      {/* What's Included */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
          <Info className="w-5 h-5 text-blue-400" />
          Export Contents
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            {
              name: 'Trained Models',
              description: 'PPO + Hybrid agent model checkpoints',
              checked: exportConfig.includeModels,
              key: 'includeModels',
              size: '~250 MB',
            },
            {
              name: 'Run Logs',
              description: 'JSON logs from training and evaluation runs',
              checked: exportConfig.includeSimulationLogs,
              key: 'includeSimulationLogs',
              size: `~${exportConfig.maxLogSize} MB`,
            },
            {
              name: 'Documentation',
              description: 'Project README, training guide, architecture docs',
              checked: exportConfig.includeDocumentation,
              key: 'includeDocumentation',
              size: '~50 MB',
            },
            {
              name: 'Web Export',
              description: 'Next.js static export for browser viewing',
              checked: exportConfig.includeWebDemo,
              key: 'includeWebDemo',
              size: '~100 MB',
            },
          ].map((item) => (
            <label key={item.key} className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={item.checked}
                onChange={(e) =>
                  setExportConfig({
                    ...exportConfig,
                    [item.key]: e.target.checked,
                  })
                }
                className="w-4 h-4 mt-1"
              />
              <div className="flex-1">
                <p className="font-medium text-white">{item.name}</p>
                <p className="text-sm text-gray-400">{item.description}</p>
                <p className="text-xs text-gray-500 mt-1">{item.size}</p>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Export Options */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="font-semibold text-white mb-4">Manifest options</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Max Log Size</label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="50"
                max="1000"
                step="50"
                value={exportConfig.maxLogSize}
                onChange={(e) =>
                  setExportConfig({
                    ...exportConfig,
                    maxLogSize: parseInt(e.target.value),
                  })
                }
                className="flex-1 h-2 bg-slate-700 rounded-lg"
              />
              <span className="text-sm font-semibold text-white w-24">{exportConfig.maxLogSize} MB</span>
            </div>
            <p className="text-xs text-gray-400 mt-2">Limit run logs to conserve space</p>
          </div>

          <div className="rounded-md border border-slate-700 bg-slate-950 p-3">
            <p className="text-sm text-slate-300">
              <strong>Estimated offline bundle size:</strong> {estimateSize()}
            </p>
          </div>
        </div>
      </div>

      {/* Export Progress */}
      {isExporting && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="font-semibold text-white mb-4">Manifest download progress</h3>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm text-gray-300">Preparing manifest...</span>
                <span className="text-sm font-semibold text-white">{exportProgress}%</span>
              </div>
              <div className="w-full h-3 overflow-hidden rounded-md bg-slate-700">
                <div
                  className="h-full bg-blue-600 transition-all duration-300"
                  style={{ width: `${exportProgress}%` }}
                />
              </div>
            </div>

            <div className="text-sm text-gray-400">
              {exportProgress < 30 && 'Reading selected export settings...'}
              {exportProgress >= 30 && exportProgress < 60 && 'Listing available runs...'}
              {exportProgress >= 60 && exportProgress < 90 && 'Building manifest JSON...'}
              {exportProgress >= 90 && 'Ready to download...'}
            </div>
          </div>
        </div>
      )}

      {/* Export Status */}
      {exportStatus === 'completed' && (
        <div className="bg-emerald-900/20 border border-emerald-700 rounded-lg p-6">
          <p className="text-emerald-300 flex items-center gap-2">
            <strong>Manifest downloaded.</strong> The offline export manifest has been saved.
          </p>
        </div>
      )}

      {exportStatus === 'error' && (
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-6">
          <p className="text-red-300 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            <strong>Export Failed</strong> - Please try again
          </p>
        </div>
      )}

      {/* Manifest Preview */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
          <FileJson className="w-5 h-5 text-blue-400" />
          Manifest preview
        </h3>

        <div className="font-mono text-sm text-gray-300 space-y-1 bg-black/30 p-4 rounded">
          <p>aurora-offline-manifest.json</p>
          <p className="pl-4">{"{"}</p>
          <p className="pl-8">timestamp</p>
          <p className="pl-8">config</p>
          <p className="pl-8">availableRuns</p>
          <p className="pl-8">contents</p>
          <p className="pl-8">version</p>
          <p className="pl-8">source</p>
          <p className="pl-8">estimatedSize</p>
          <p className="pl-4">{"}"}</p>
        </div>
      </div>

      {/* Judge Information */}
      <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-6">
        <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
          <Globe className="w-5 h-5 text-blue-400" />
          Offline review
        </h3>
        <ul className="text-sm text-blue-300 space-y-2">
          <li>Downloads a JSON manifest only, not a packaged archive.</li>
          <li>The manifest records the selected models, logs, docs, and demo flags.</li>
          <li>Use it as the source of truth for any downstream offline assembly.</li>
        </ul>
      </div>

      {/* Export Button */}
      <div className="flex gap-4">
        <button
          onClick={handleExport}
          disabled={isExporting || exportStatus === 'completed'}
          className="flex flex-1 items-center justify-center gap-2 rounded-md border border-blue-600 bg-blue-600 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:border-slate-700 disabled:bg-slate-700"
        >
          <Download className="w-5 h-5" />
          {isExporting ? 'Generating manifest...' : exportStatus === 'completed' ? 'Manifest downloaded' : 'Download manifest'}
        </button>

        {exportStatus === 'completed' && (
          <button
            onClick={() => {
              setExportStatus('idle');
              setExportProgress(0);
            }}
            className="rounded-md border border-slate-700 px-6 py-3 font-semibold text-white transition hover:bg-slate-800"
          >
            Export Again
          </button>
        )}
      </div>

      {/* USB Kit Info */}
      <div className="rounded-md border border-slate-700 bg-slate-950 p-6">
        <p className="text-sm leading-relaxed text-slate-300">
          The downloaded file is a manifest that can be inspected or handed off to an offline bundling step.
        </p>
      </div>
    </div>
  );
}
