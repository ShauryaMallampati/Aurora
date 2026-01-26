"use client";

import { WildfireCostComparison } from "@/components/wildfire-cost-comparison";
import { Navigation } from "@/shared/Navigation";

export default function CostsPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white flex flex-col">
      <Navigation />
      
      <main className="flex-1 max-w-6xl mx-auto px-6 py-12 w-full">
        <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Cost Analysis</h1>
            <p className="text-gray-400">Comparing AI-driven wildfire suppression against traditional methods.</p>
        </div>
        
        <WildfireCostComparison />
        
        <div className="mt-12 text-sm text-gray-500">
            <p>Data extrapolated from NIFC (National Interagency Fire Center) and USGS historical cost reports (2018-2023).</p>
        </div>
      </main>
    </div>
  );
}
