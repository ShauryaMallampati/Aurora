"use client";

import { useState } from "react";
import { MapPin, Flame, Wind, Droplets, DollarSign, X } from "lucide-react";

interface FireCreatorProps {
  onClose: () => void;
  onCreateFire: (fireConfig: CustomFireConfig) => void;
  onStartSimulation?: (fireConfig: CustomFireConfig) => void;
}

export interface CustomFireConfig {
  location: {
    lat: number;
    lng: number;
    address?: string;
  };
  strength: number; // 1-10
  windFactor: number; // 0-2
  numDrones: number; // 1-10
  waterAmount: number; // gallons per drop
  estimatedCost: number; // calculated
}

export function FireCreator({ onClose, onCreateFire, onStartSimulation }: FireCreatorProps) {
  const [lat, setLat] = useState<string>("36.7783");
  const [lng, setLng] = useState<string>("-119.4179");
  const [address, setAddress] = useState<string>("");
  const [strength, setStrength] = useState<number>(5);
  const [windFactor, setWindFactor] = useState<number>(1.0);
  const [numDrones, setNumDrones] = useState<number>(3);
  const [waterAmount, setWaterAmount] = useState<number>(500);
  const [isGeocoding, setIsGeocoding] = useState(false);

  // Calculate estimated cost
  const calculateCost = () => {
    const baseCost = 50000; // Base deployment cost
    const droneCost = numDrones * 15000; // $15k per drone
    const waterCost = waterAmount * numDrones * 0.5; // $0.50 per gallon
    const difficultyCost = strength * windFactor * 2000; // Difficulty multiplier
    return Math.round(baseCost + droneCost + waterCost + difficultyCost);
  };

  const handleGeocodeAddress = async () => {
    if (!address.trim()) return;
    
    setIsGeocoding(true);
    try {
      // Using Nominatim (OpenStreetMap) for geocoding - free and no API key needed
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`,
        {
          headers: {
            'User-Agent': 'AURORA-Fire-Sim'
          }
        }
      );
      const data = await response.json();
      
      if (data && data.length > 0) {
        setLat(data[0].lat);
        setLng(data[0].lon);
      } else {
        alert('Address not found. Please try a different address or enter coordinates manually.');
      }
    } catch (error) {
      console.error('Geocoding error:', error);
      alert('Failed to geocode address. Please enter coordinates manually.');
    } finally {
      setIsGeocoding(false);
    }
  };

  const handleCreate = () => {
    const fireConfig: CustomFireConfig = {
      location: {
        lat: parseFloat(lat),
        lng: parseFloat(lng),
        address: address || undefined,
      },
      strength,
      windFactor,
      numDrones,
      waterAmount,
      estimatedCost: calculateCost(),
    };
    
    // Move map to custom fire location
    window.dispatchEvent(new CustomEvent('moveMapToFire', {
      detail: { 
        lat: parseFloat(lat), 
        lng: parseFloat(lng), 
        zoom: 12 
      }
    }));
    
    onCreateFire(fireConfig);
  };

  const handleStartSimulation = () => {
    const fireConfig: CustomFireConfig = {
      location: {
        lat: parseFloat(lat),
        lng: parseFloat(lng),
        address: address || undefined,
      },
      strength,
      windFactor,
      numDrones,
      waterAmount,
      estimatedCost: calculateCost(),
    };
    
    // Move map to custom fire location
    window.dispatchEvent(new CustomEvent('moveMapToFire', {
      detail: { 
        lat: parseFloat(lat), 
        lng: parseFloat(lng), 
        zoom: 12 
      }
    }));
    
    // Call start simulation if provided
    if (onStartSimulation) {
      onStartSimulation(fireConfig);
    } else {
      // Fall back to just creating
      onCreateFire(fireConfig);
    }
  };

  const isValid = () => {
    const latNum = parseFloat(lat);
    const lngNum = parseFloat(lng);
    return !isNaN(latNum) && !isNaN(lngNum) && 
           latNum >= -90 && latNum <= 90 && 
           lngNum >= -180 && lngNum <= 180;
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border-2 border-orange-500/50 rounded-2xl shadow-2xl shadow-orange-500/20 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-orange-900/90 to-red-900/90 backdrop-blur-xl border-b border-orange-500/30 px-6 py-4 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-orange-500/20 rounded-xl flex items-center justify-center">
              <Flame className="w-7 h-7 text-orange-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">Custom Fire Creator</h2>
              <p className="text-sm text-orange-200">Design your own wildfire scenario</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition"
          >
            <X className="w-6 h-6 text-white" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Location Section */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <MapPin className="w-5 h-5 text-blue-400" />
              Fire Location
            </h3>
            
            {/* Address Search */}
            <div className="mb-4">
              <label className="block text-sm font-semibold text-gray-300 mb-2">
                Search by Address
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleGeocodeAddress()}
                  placeholder="e.g., Paradise, CA or Yellowstone National Park"
                  className="flex-1 px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
                />
                <button
                  onClick={handleGeocodeAddress}
                  disabled={isGeocoding || !address.trim()}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white rounded-lg font-semibold transition"
                >
                  {isGeocoding ? 'Searching...' : 'Search'}
                </button>
              </div>
              <p className="text-xs text-gray-400 mt-2">
                Or click on the map when simulation starts to set location
              </p>
            </div>

            {/* Manual Coordinates */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-300 mb-2">
                  Latitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={lat}
                  onChange={(e) => setLat(e.target.value)}
                  placeholder="36.7783"
                  className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-300 mb-2">
                  Longitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={lng}
                  onChange={(e) => setLng(e.target.value)}
                  placeholder="-119.4179"
                  className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Fire Parameters */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Flame className="w-5 h-5 text-orange-400" />
              Fire Parameters
            </h3>

            <div className="space-y-4">
              {/* Fire Strength */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-semibold text-gray-300">
                    Fire Strength
                  </label>
                  <span className="text-lg font-bold text-orange-400">{strength}/10</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  step="1"
                  value={strength}
                  onChange={(e) => setStrength(parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-orange-500"
                />
                <p className="text-xs text-gray-400 mt-1">
                  {strength <= 3 && "Small fire - easily containable"}
                  {strength > 3 && strength <= 6 && "Medium fire - moderate challenge"}
                  {strength > 6 && strength <= 8 && "Large fire - high difficulty"}
                  {strength > 8 && "Extreme fire - maximum challenge"}
                </p>
              </div>

              {/* Wind Factor */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                    <Wind className="w-4 h-4 text-cyan-400" />
                    Wind Factor
                  </label>
                  <span className="text-lg font-bold text-cyan-400">{windFactor.toFixed(1)}x</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={windFactor}
                  onChange={(e) => setWindFactor(parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                />
                <p className="text-xs text-gray-400 mt-1">
                  {windFactor < 0.5 && "Calm - minimal wind"}
                  {windFactor >= 0.5 && windFactor < 1.0 && "Light breeze"}
                  {windFactor >= 1.0 && windFactor < 1.5 && "Moderate wind - spreads fire faster"}
                  {windFactor >= 1.5 && "Strong wind - rapid fire spread"}
                </p>
              </div>
            </div>
          </div>

          {/* Resource Allocation */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Droplets className="w-5 h-5 text-blue-400" />
              Resource Allocation
            </h3>

            <div className="grid grid-cols-2 gap-4">
              {/* Number of Drones */}
              <div>
                <label className="block text-sm font-semibold text-gray-300 mb-2">
                  Number of Drones
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={numDrones}
                  onChange={(e) => setNumDrones(parseInt(e.target.value) || 1)}
                  className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
                <p className="text-xs text-gray-400 mt-1">1-10 drones available</p>
              </div>

              {/* Water per Drone */}
              <div>
                <label className="block text-sm font-semibold text-gray-300 mb-2">
                  Water per Drone (gallons)
                </label>
                <input
                  type="number"
                  min="100"
                  max="2000"
                  step="100"
                  value={waterAmount}
                  onChange={(e) => setWaterAmount(parseInt(e.target.value) || 100)}
                  className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                />
                <p className="text-xs text-gray-400 mt-1">100-2000 gallons capacity</p>
              </div>
            </div>
          </div>

          {/* Cost Estimate */}
          <div className="bg-gradient-to-r from-green-900/30 to-emerald-900/30 border border-green-600/30 rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-green-400" />
              Estimated Operational Cost
            </h3>
            <div className="text-4xl font-black text-green-400 mb-2">
              ${calculateCost().toLocaleString()}
            </div>
            <div className="text-sm text-gray-300 space-y-1">
              <p>• Base deployment: $50,000</p>
              <p>• Drones: {numDrones} × $15,000 = ${(numDrones * 15000).toLocaleString()}</p>
              <p>• Water: {(waterAmount * numDrones).toLocaleString()} gal × $0.50 = ${(waterAmount * numDrones * 0.5).toLocaleString()}</p>
              <p>• Difficulty multiplier: {(strength * windFactor).toFixed(1)}x = ${Math.round(strength * windFactor * 2000).toLocaleString()}</p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={handleStartSimulation}
              disabled={!isValid()}
              className="px-6 py-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-700 disabled:to-gray-700 text-white rounded-xl font-bold transition shadow-lg hover:shadow-purple-500/50 disabled:shadow-none flex items-center justify-center gap-2"
            >
              ▶️ Start Sim Now
            </button>
            <button
              onClick={handleCreate}
              disabled={!isValid()}
              className="px-6 py-4 bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 disabled:from-gray-700 disabled:to-gray-700 text-white rounded-xl font-bold transition shadow-lg hover:shadow-orange-500/50 disabled:shadow-none"
            >
              Create & Configure
            </button>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="flex-1 px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-xl font-semibold transition"
            >
              Cancel
            </button>
          </div>

          <p className="text-xs text-center text-gray-500">
            Note: This creates a simulation scenario. Model training must be complete to run actual predictions.
          </p>
        </div>
      </div>
    </div>
  );
}
