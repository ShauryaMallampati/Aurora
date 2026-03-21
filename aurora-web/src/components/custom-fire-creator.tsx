'use client';

import { useState } from 'react';
import { Map, Zap, Flame, Wind, Droplets, Loader } from 'lucide-react';

interface FireScenario {
  latitude: number;
  longitude: number;
  fireSize: 'small' | 'medium' | 'large';
  weather: {
    temperature_c: number;
    wind_speed_mph: number;
    wind_direction: string;
    humidity: number;
  };
  numDrones: number;
}

interface CreationStatus {
  id: string;
  status: 'idle' | 'creating' | 'running' | 'completed' | 'error';
  ppoRunId?: string;
  hybridRunId?: string;
  message: string;
  estimatedTimeMinutes?: number;
}

export function CustomFireCreator() {
  const [scenario, setScenario] = useState<FireScenario>({
    latitude: 36.7783,
    longitude: -119.4179,
    fireSize: 'medium',
    weather: {
      temperature_c: 32,
      wind_speed_mph: 15,
      wind_direction: 'NE',
      humidity: 25,
    },
    numDrones: 4,
  });

  const [creationStatus, setCreationStatus] = useState<CreationStatus>({
    id: '',
    status: 'idle',
    message: 'Ready to prepare a custom scenario',
  });

  const [runBothModels, setRunBothModels] = useState(true);

  const handleCreateScenario = async () => {
    setCreationStatus({ ...creationStatus, status: 'creating', message: 'Submitting scenario request...' });

    try {
      const response = await fetch('/api/scenarios/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...scenario,
          runBothModels,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setCreationStatus({
          id: data.id,
          status: runBothModels ? 'running' : 'completed',
          ppoRunId: data.ppoRunId,
          hybridRunId: data.hybridRunId,
          message: data.message,
          estimatedTimeMinutes: data.estimatedTimeMinutes,
        });

        // If running both models, poll for completion
        if (runBothModels) {
          pollScenarioStatus(data.id);
        }
      } else {
        setCreationStatus({
          id: '',
          status: 'error',
          message: data.error || 'Failed to create scenario',
        });
      }
    } catch (error) {
      setCreationStatus({
        id: '',
        status: 'error',
        message: `Error: ${String(error)}`,
      });
    }
  };

  const pollScenarioStatus = (scenarioId: string) => {
    // Poll every 5 seconds for up to 15 minutes
    const maxPolls = 180;
    let pollCount = 0;

    const interval = setInterval(async () => {
      pollCount++;

      try {
        const response = await fetch(`/api/scenarios/create?id=${scenarioId}`);
        const data = await response.json();

        setCreationStatus({
          id: data.id,
          status: data.status === 'completed' ? 'completed' : 'running',
          ppoRunId: data.ppoRunId,
          hybridRunId: data.hybridRunId,
          message: data.message,
          estimatedTimeMinutes: data.estimatedTimeMinutes,
        });

        if (data.status === 'completed' || pollCount >= maxPolls) {
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 5000);
  };

  const fireSizeDetails = {
    small: { acres: '100-500', duration: '2 min' },
    medium: { acres: '500-2000', duration: '4 min' },
    large: { acres: '2000+', duration: '6 min' },
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-md border border-slate-700 bg-slate-900 p-6">
        <div className="flex items-center gap-3 mb-2">
          <Flame className="w-6 h-6 text-slate-300" />
          <h2 className="text-2xl font-semibold text-white">Custom scenario</h2>
        </div>
        <p className="text-slate-400">Create a scenario request and run PPO and hybrid models for comparison.</p>
      </div>

      {/* Location Input */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-semibold text-white mb-2 flex items-center gap-2">
            <Map className="w-4 h-4" />
            Latitude
          </label>
          <input
            type="number"
            value={scenario.latitude}
            onChange={(e) => setScenario({ ...scenario, latitude: parseFloat(e.target.value) })}
            min="-90"
            max="90"
            step="0.001"
            className="w-full bg-slate-800 border border-slate-700 text-white rounded px-3 py-2 hover:border-slate-600 focus:border-blue-500 focus:outline-none"
            placeholder="36.7783"
          />
          <p className="text-xs text-gray-400 mt-1">Range: -90 to 90</p>
        </div>

        <div>
          <label className="block text-sm font-semibold text-white mb-2 flex items-center gap-2">
            <Map className="w-4 h-4" />
            Longitude
          </label>
          <input
            type="number"
            value={scenario.longitude}
            onChange={(e) => setScenario({ ...scenario, longitude: parseFloat(e.target.value) })}
            min="-180"
            max="180"
            step="0.001"
            className="w-full bg-slate-800 border border-slate-700 text-white rounded px-3 py-2 hover:border-slate-600 focus:border-blue-500 focus:outline-none"
            placeholder="-119.4179"
          />
          <p className="text-xs text-gray-400 mt-1">Range: -180 to 180</p>
        </div>
      </div>

      {/* Fire Size */}
      <div>
        <label className="block text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <Flame className="w-4 h-4" />
          Fire Size
        </label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {['small', 'medium', 'large'].map((size) => (
            <button
              key={size}
              onClick={() => setScenario({ ...scenario, fireSize: size as any })}
              className={`p-4 rounded-lg border-2 transition ${
                scenario.fireSize === size
                  ? 'bg-orange-600 border-orange-400'
                  : 'bg-slate-800 border-slate-700 hover:border-slate-600'
              }`}
            >
              <div className="font-semibold text-white capitalize">{size}</div>
              <div className="text-xs text-gray-300 mt-1">{fireSizeDetails[size as keyof typeof fireSizeDetails].acres} acres</div>
              <div className="text-xs text-gray-400">{fireSizeDetails[size as keyof typeof fireSizeDetails].duration}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Weather */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-semibold text-white mb-2 flex items-center gap-2">
            <Droplets className="w-4 h-4" />
            Temperature (°C)
          </label>
          <input
            type="number"
            value={scenario.weather.temperature_c}
            onChange={(e) =>
              setScenario({
                ...scenario,
                weather: { ...scenario.weather, temperature_c: parseFloat(e.target.value) },
              })
            }
            min="0"
            max="50"
            className="w-full bg-slate-800 border border-slate-700 text-white rounded px-3 py-2 hover:border-slate-600 focus:border-blue-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-white mb-2 flex items-center gap-2">
            <Wind className="w-4 h-4" />
            Wind Speed (mph)
          </label>
          <input
            type="number"
            value={scenario.weather.wind_speed_mph}
            onChange={(e) =>
              setScenario({
                ...scenario,
                weather: { ...scenario.weather, wind_speed_mph: parseFloat(e.target.value) },
              })
            }
            min="0"
            max="50"
            className="w-full bg-slate-800 border border-slate-700 text-white rounded px-3 py-2 hover:border-slate-600 focus:border-blue-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-white mb-2">Wind Direction</label>
          <select
            value={scenario.weather.wind_direction}
            onChange={(e) =>
              setScenario({
                ...scenario,
                weather: { ...scenario.weather, wind_direction: e.target.value },
              })
            }
            className="w-full bg-slate-800 border border-slate-700 text-white rounded px-3 py-2 hover:border-slate-600 focus:border-blue-500 focus:outline-none"
          >
            {['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'].map((dir) => (
              <option key={dir} value={dir}>
                {dir}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-semibold text-white mb-2 flex items-center gap-2">
            <Droplets className="w-4 h-4" />
            Humidity (%)
          </label>
          <input
            type="number"
            value={scenario.weather.humidity}
            onChange={(e) =>
              setScenario({
                ...scenario,
                weather: { ...scenario.weather, humidity: parseFloat(e.target.value) },
              })
            }
            min="0"
            max="100"
            className="w-full bg-slate-800 border border-slate-700 text-white rounded px-3 py-2 hover:border-slate-600 focus:border-blue-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Drone Count */}
      <div>
        <label className="block text-sm font-semibold text-white mb-2 flex items-center gap-2">
          <Zap className="w-4 h-4" />
          Number of Drones
        </label>
        <input
          type="number"
          value={scenario.numDrones}
          onChange={(e) => setScenario({ ...scenario, numDrones: parseInt(e.target.value) })}
          min="1"
          max="10"
          className="w-full bg-slate-800 border border-slate-700 text-white rounded px-3 py-2 hover:border-slate-600 focus:border-blue-500 focus:outline-none"
        />
      </div>

      {/* Model Selection */}
      <div>
        <label className="block text-sm font-semibold text-white mb-3">Run models</label>
        <div className="flex gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={runBothModels}
              onChange={(e) => setRunBothModels(e.target.checked)}
              className="w-4 h-4 bg-slate-800 border border-slate-600 rounded"
            />
            <span className="text-white">Run both PPO and Hybrid for comparison</span>
          </label>
        </div>
      </div>

      {/* Create Button */}
      <button
        onClick={handleCreateScenario}
        disabled={creationStatus.status === 'creating' || creationStatus.status === 'running'}
        className="flex w-full items-center justify-center gap-2 rounded-md border border-blue-600 bg-blue-600 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:border-slate-700 disabled:bg-slate-700"
      >
        {creationStatus.status === 'creating' || creationStatus.status === 'running' ? (
          <>
            <Loader className="w-4 h-4 animate-spin" />
            {creationStatus.status === 'creating' ? 'Creating...' : 'Running...'}
          </>
        ) : (
          <>
            <Flame className="w-4 h-4" />
            Create scenario
          </>
        )}
      </button>

      {/* Status */}
      {creationStatus.status !== 'idle' && (
        <div
          className={`p-4 rounded-lg border ${
            creationStatus.status === 'error'
              ? 'bg-red-900/20 border-red-700 text-red-300'
              : creationStatus.status === 'completed'
              ? 'bg-emerald-900/20 border-emerald-700 text-emerald-300'
              : 'bg-blue-900/20 border-blue-700 text-blue-300'
          }`}
        >
          <p className="font-semibold mb-2">{creationStatus.message}</p>
          {creationStatus.estimatedTimeMinutes && creationStatus.status === 'running' && (
            <p className="text-sm">Estimated time: {creationStatus.estimatedTimeMinutes} minutes</p>
          )}
          {creationStatus.status === 'completed' && (
            <div className="mt-3 pt-3 border-t border-current">
              <p className="text-sm font-mono mb-2">Scenario ID: {creationStatus.id}</p>
              {creationStatus.ppoRunId && (
                <a
                  href={`/sim?run=${creationStatus.ppoRunId}`}
                  className="inline-block px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded text-sm font-semibold transition mr-2"
                >
                  View PPO Run
                </a>
              )}
              {creationStatus.hybridRunId && (
                <a
                  href={`/sim?run=${creationStatus.hybridRunId}`}
                  className="inline-block px-3 py-1.5 bg-purple-600 hover:bg-purple-700 rounded text-sm font-semibold transition mr-2"
                >
                  View Hybrid Run
                </a>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
