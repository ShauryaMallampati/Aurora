'use client';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0a0b] text-white">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold">404</h1>
        <p className="text-white/60">Page not found</p>
        <a href="/" className="inline-block mt-6 px-6 py-2 bg-orange-500 hover:bg-orange-600 rounded-lg transition-colors">
          Go Home
        </a>
      </div>
    </div>
  );
}
