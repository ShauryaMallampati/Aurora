'use client';

import { X, Settings } from 'lucide-react';
import { SafetyModeControl } from './safety-mode-control';
import { useState } from 'react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<'safety' | 'general' | 'advanced'>('safety');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-slate-800 to-slate-900 border-b border-slate-700 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings className="w-6 h-6 text-blue-400" />
            <h2 className="text-2xl font-bold text-white">Simulation Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-slate-700 flex">
          {(['safety', 'general', 'advanced'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-3 px-4 font-semibold transition ${
                activeTab === tab
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-gray-300 hover:bg-slate-700'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-6">
          {activeTab === 'safety' && (
            <SafetyModeControl />
          )}

          {activeTab === 'general' && (
            <div className="space-y-6">
              <div className="bg-gradient-to-r from-blue-900 to-indigo-900 border border-blue-700 rounded-lg p-6">
                <h3 className="text-xl font-bold text-white mb-2">General Settings</h3>
                <p className="text-blue-200">Simulation playback and behavior controls</p>
              </div>

              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <h4 className="font-semibold text-white mb-4">Playback Controls</h4>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Default Playback Speed
                    </label>
                    <select className="w-full bg-slate-700 border border-slate-600 text-white rounded px-3 py-2">
                      <option>0.5x</option>
                      <option selected>1x</option>
                      <option>2x</option>
                      <option>4x</option>
                      <option>8x</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Auto-restart on Completion
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input type="checkbox" className="w-4 h-4" />
                      <span className="text-sm text-gray-300">Automatically restart simulation when complete</span>
                    </label>
                  </div>
                </div>
              </div>

              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <h4 className="font-semibold text-white mb-4">Visualization</h4>
                <div className="space-y-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" defaultChecked className="w-4 h-4" />
                    <span className="text-sm text-gray-300">Show fire heat map</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" defaultChecked className="w-4 h-4" />
                    <span className="text-sm text-gray-300">Show drone pathfinding trails</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" defaultChecked className="w-4 h-4" />
                    <span className="text-sm text-gray-300">Show weather overlay</span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'advanced' && (
            <div className="space-y-6">
              <div className="bg-gradient-to-r from-amber-900 to-orange-900 border border-amber-700 rounded-lg p-6">
                <h3 className="text-xl font-bold text-white mb-2">Advanced Settings</h3>
                <p className="text-amber-200">Expert-level configuration for model behavior and optimization</p>
              </div>

              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <h4 className="font-semibold text-white mb-4">LLM Configuration</h4>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      LLM Guidance Frequency (steps)
                    </label>
                    <input
                      type="number"
                      defaultValue={50}
                      min={10}
                      max={500}
                      step={10}
                      className="w-full bg-slate-700 border border-slate-600 text-white rounded px-3 py-2"
                    />
                    <p className="text-xs text-gray-400 mt-1">Lower = more frequent guidance, higher accuracy but slower</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      LLM Model
                    </label>
                    <select className="w-full bg-slate-700 border border-slate-600 text-white rounded px-3 py-2">
                      <option>Qwen/Qwen2.5-1.5B-Instruct</option>
                      <option>meta-llama/Llama-2-7b-chat-hf</option>
                      <option>Mixtral-8x7B-Instruct-v0.1</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <h4 className="font-semibold text-white mb-4">PPO Hyperparameters</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Learning Rate</label>
                    <input
                      type="number"
                      defaultValue={0.0003}
                      step={0.00001}
                      className="w-full bg-slate-700 border border-slate-600 text-white rounded px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Discount Factor (γ)</label>
                    <input
                      type="number"
                      defaultValue={0.99}
                      step={0.01}
                      min={0.9}
                      max={0.999}
                      className="w-full bg-slate-700 border border-slate-600 text-white rounded px-3 py-2 text-sm"
                    />
                  </div>
                </div>
              </div>

              <div className="bg-amber-900/20 border border-amber-700 rounded-lg p-4">
                <p className="text-sm text-amber-300">
                  ⚠️ <strong>Advanced settings affect training behavior.</strong> Only modify if you understand the implications.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-700 bg-slate-800 px-6 py-4 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded-lg transition"
          >
            Close
          </button>
          <button
            onClick={onClose}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
}
