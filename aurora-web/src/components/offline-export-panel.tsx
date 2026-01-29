'use client';

import { useState } from 'react';
import { Download, FileJson, Package, Globe, Save, Info, AlertCircle } from 'lucide-react';

interface ExportConfig {
  includeModels: boolean;
  includeSimulationLogs: boolean;
  includeDocumentation: boolean;
  includeWebDemo: boolean;
  format: 'zip' | 'tar.gz';
  maxLogSize: number;
}

export function OfflineExportPanel() {
  const [exportConfig, setExportConfig] = useState<ExportConfig>({
    includeModels: true,
    includeSimulationLogs: true,
    includeDocumentation: true,
    includeWebDemo: true,
    format: 'zip',
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
    setExportProgress(0);

    try {
      // Simulate export progress
      for (let i = 0; i <= 100; i += 10) {
        await new Promise((resolve) => setTimeout(resolve, 500));
        setExportProgress(i);
      }

      // Trigger download
      const response = await fetch('/api/export/offline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(exportConfig),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `aurora-offline-${new Date().toISOString().split('T')[0]}.${
          exportConfig.format === 'zip' ? 'zip' : 'tar.gz'
        }`;
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
      <div className="bg-gradient-to-r from-emerald-900 to-teal-900 border border-emerald-700 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-2">
          <Package className="w-8 h-8 text-emerald-300" />
          <h2 className="text-2xl font-bold text-white">Offline Export</h2>
        </div>
        <p className="text-emerald-200">Generate portable AURORA package for offline demo and judge review</p>
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
              name: 'Simulation Logs',
              description: 'JSON logs from training + evaluation runs',
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
              name: 'Web Demo',
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
        <h3 className="font-semibold text-white mb-4">Export Options</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">File Format</label>
            <div className="flex gap-4">
              {(['zip', 'tar.gz'] as const).map((format) => (
                <label key={format} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="format"
                    value={format}
                    checked={exportConfig.format === format}
                    onChange={(e) =>
                      setExportConfig({
                        ...exportConfig,
                        format: e.target.value as 'zip' | 'tar.gz',
                      })
                    }
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-gray-300">
                    {format === 'zip' ? '.ZIP (Windows/Mac/Linux)' : '.TAR.GZ (Linux/Mac)'}
                  </span>
                </label>
              ))}
            </div>
          </div>

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
            <p className="text-xs text-gray-400 mt-2">Limit simulation logs to conserve space</p>
          </div>

          <div className="bg-blue-900/20 border border-blue-700 rounded p-3">
            <p className="text-sm text-blue-300">
              <strong>📦 Total Package Size:</strong> {estimateSize()}
            </p>
          </div>
        </div>
      </div>

      {/* Export Progress */}
      {isExporting && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="font-semibold text-white mb-4">Export Progress</h3>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm text-gray-300">Packaging files...</span>
                <span className="text-sm font-semibold text-white">{exportProgress}%</span>
              </div>
              <div className="w-full h-3 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all duration-300"
                  style={{ width: `${exportProgress}%` }}
                />
              </div>
            </div>

            <div className="text-sm text-gray-400">
              {exportProgress < 30 && 'Collecting model files...'}
              {exportProgress >= 30 && exportProgress < 60 && 'Compressing simulation logs...'}
              {exportProgress >= 60 && exportProgress < 90 && 'Building documentation...'}
              {exportProgress >= 90 && 'Finalizing package...'}
            </div>
          </div>
        </div>
      )}

      {/* Export Status */}
      {exportStatus === 'completed' && (
        <div className="bg-emerald-900/20 border border-emerald-700 rounded-lg p-6">
          <p className="text-emerald-300 flex items-center gap-2">
            ✅ <strong>Export Complete!</strong> Your offline package has been downloaded.
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

      {/* Package Contents Preview */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h3 className="font-semibold text-white mb-4">Package Structure</h3>

        <div className="font-mono text-sm text-gray-300 space-y-1 bg-black/30 p-4 rounded">
          <p>aurora-offline/</p>
          <p className="pl-4">├── models/</p>
          <p className="pl-8">│   ├── ppo_model/</p>
          <p className="pl-8">│   └── hybrid_llm_model/</p>
          <p className="pl-4">├── logs/</p>
          <p className="pl-8">│   └── simulation_*.json</p>
          <p className="pl-4">├── web/</p>
          <p className="pl-8">│   ├── index.html</p>
          <p className="pl-8">│   └── _next/ (Next.js build)</p>
          <p className="pl-4">├── docs/</p>
          <p className="pl-8">│   ├── README.md</p>
          <p className="pl-8">│   ├── TRAINING_GUIDE.md</p>
          <p className="pl-8">│   └── ARCHITECTURE.md</p>
          <p className="pl-4">└── USAGE.md</p>
        </div>
      </div>

      {/* Judge Information */}
      <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-6">
        <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
          <Globe className="w-5 h-5 text-blue-400" />
          For Competition Judges
        </h3>
        <ul className="text-sm text-blue-300 space-y-2">
          <li>✅ Self-contained package - no internet required</li>
          <li>✅ Open web demo in any browser with offline HTML version</li>
          <li>✅ View training logs, model architecture, and performance metrics</li>
          <li>✅ Run simulation videos and comparison analyses</li>
          <li>✅ Complete documentation for technical evaluation</li>
        </ul>
      </div>

      {/* Export Button */}
      <div className="flex gap-4">
        <button
          onClick={handleExport}
          disabled={isExporting || exportStatus === 'completed'}
          className="flex-1 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 disabled:from-gray-600 disabled:to-gray-600 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition"
        >
          <Download className="w-5 h-5" />
          {isExporting ? 'Exporting...' : exportStatus === 'completed' ? 'Export Complete' : 'Export Offline Package'}
        </button>

        {exportStatus === 'completed' && (
          <button
            onClick={() => {
              setExportStatus('idle');
              setExportProgress(0);
            }}
            className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded-lg transition"
          >
            Export Again
          </button>
        )}
      </div>

      {/* USB Kit Info */}
      <div className="bg-purple-900/20 border border-purple-700 rounded-lg p-6">
        <p className="text-sm text-purple-300 leading-relaxed">
          <strong>💾 USB Kit for Judges:</strong> All export files can be copied directly to a USB drive for offline
          judge review. Recommended folder structure: <code className="text-purple-200">USB:/aurora/</code>. Include
          USAGE.md for quick start instructions. Total package fits on any standard USB (most exports 400-500 MB).
        </p>
      </div>
    </div>
  );
}
