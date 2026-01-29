"use client";

import { useSimulationStore } from "@/shared/store";
import { Download } from "lucide-react";
import { useRef, useEffect } from "react";

export function LogsTab() {
  const logs = useSimulationStore((state) => state.logs);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new logs
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const handleExport = () => {
    const logText = logs.join("\n");
    const blob = new Blob([logText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `aurora_logs_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-800 flex items-center justify-between">
        <h3 className="font-semibold text-white">Simulation Logs</h3>
        <button
          onClick={handleExport}
          className="px-3 py-1.5 bg-gray-800 text-white rounded text-sm flex items-center gap-2 hover:bg-gray-700 transition"
          disabled={logs.length === 0}
        >
          <Download className="w-4 h-4" />
          Export
        </button>
      </div>

      {/* Log Entries */}
      <div className="flex-1 overflow-y-auto p-4 font-mono text-xs">
        {logs.length === 0 ? (
          <div className="text-gray-400 text-center mt-8">
            No logs yet. Logs will appear here during simulation.
          </div>
        ) : (
          <div className="space-y-1">
            {logs.map((log, i) => (
              <div key={i} className="text-gray-300">
                {log}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>
    </div>
  );
}
