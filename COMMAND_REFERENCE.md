# 🚀 AURORA Split View - Complete Command Reference

## Quick Start (Copy & Paste)

```bash
# 1. Navigate to project
cd /Users/ankit/Aurora

# 2. Go to web app
cd aurora-web

# 3. Install dependencies (first time only)
npm install

# 4. Start development server
npm run dev

# 5. Open browser to:
# http://localhost:3000
```

**Time to get running: ~5 minutes** ⏱️

---

## All Available Commands

### Development

```bash
# Start dev server (with hot reload)
npm run dev
# Runs on: http://localhost:3000
# 🔥 Hot reload enabled - changes auto-apply

# Type check (verify TypeScript is correct)
npm run type-check

# Lint code (check code style)
npm run lint
```

### Production Build

```bash
# Build for production (optimized)
npm run build

# Start production server (after build)
npm start
```

### Dependency Management

```bash
# Install all dependencies
npm install

# Add a new package
npm install package-name

# Update all packages
npm update

# Clean install (remove and reinstall)
rm -rf node_modules package-lock.json
npm install
```

---

## Detailed Setup Steps

### Step 1: Prerequisites

```bash
# Check Node.js version (needs 16+)
node --version

# Check npm version (needs 8+)
npm --version

# If not installed, download from https://nodejs.org/
# Or use Homebrew:
brew install node
```

### Step 2: Navigate & Install

```bash
# Go to project root
cd /Users/ankit/Aurora

# Enter web app directory
cd aurora-web

# Install dependencies
# (This downloads ~500MB of packages)
npm install

# ⏳ First time takes 2-3 minutes
# ✅ Subsequent installs are faster
```

### Step 3: Start Server

```bash
# Start development server
npm run dev

# You should see:
# ✔ Ready in 2.5s
# ▲ Next.js 14.x.x
# - Local:        http://localhost:3000
# - Environments: .env.local

# Keep this terminal open while developing
```

### Step 4: Open Browser

```bash
# Option A: Click the link from terminal output
# Option B: Manually open:
http://localhost:3000

# Option C: Use curl to verify it's running
curl http://localhost:3000
```

---

## File Structure After Install

```
aurora-web/
├── node_modules/              ← Downloaded packages (500MB+)
│   └── (1000+ packages)
├── .next/                     ← Build cache
├── src/
│   ├── app/
│   │   └── sim/
│   │       ├── SplitViewComparison.tsx ✅ NEW
│   │       └── MapStage.tsx (updated)
│   └── shared/
│       ├── runsDataLoader.ts ✅ NEW
│       └── store.ts (updated)
├── public/                    ← Static assets
├── package.json              ← Dependencies list
├── package-lock.json         ← Lock file (auto-generated)
├── tsconfig.json            ← TypeScript config
├── next.config.mjs          ← Next.js config
├── tailwind.config.ts       ← Tailwind config
└── .env.local               ← API keys
```

---

## Common Tasks

### Run the App

```bash
# From /Users/ankit/Aurora/aurora-web/

# Development (recommended for testing)
npm run dev
# Hot reload enabled, easier debugging

# Production (optimized build)
npm run build
npm start
```

### Stop the Server

```bash
# In the terminal running npm run dev:
Ctrl+C

# This stops the server
# You can restart with: npm run dev
```

### Clear Cache & Rebuild

```bash
# If you get weird errors, try:
rm -rf .next
npm run dev

# This clears Next.js cache and rebuilds
```

### Check for Issues

```bash
# TypeScript type checking
npm run type-check

# Will show any type errors
# Fix them before deploying

# ESLint (code style)
npm run lint

# Shows code style issues
```

---

## Debugging

### Browser Developer Tools

```bash
# Open with:
# macOS: Cmd + Option + I
# Windows: F12
# Linux: F12

# Then use:
# Console tab       → See error messages
# Network tab       → See API calls
# Sources tab       → Debug code
# Elements tab      → Inspect HTML
```

### Server Logs

```bash
# Watch terminal where npm run dev is running
# You'll see:
# - GET /sim 200 (successful page load)
# - Error messages (in red)
# - Build progress

# Keep this visible while testing
```

### File Changes

```bash
# Next.js auto-reloads when you:
# - Edit .tsx files
# - Edit .ts files
# - Edit .css files

# Save with Cmd+S (macOS) or Ctrl+S (Windows/Linux)
# Browser should refresh within 1-2 seconds

# If not:
# 1. Check terminal for error messages
# 2. Hard refresh browser: Cmd+Shift+R (macOS)
# 3. Restart: Ctrl+C in terminal, then npm run dev
```

---

## Troubleshooting Commands

### Port Already in Use

```bash
# If "Port 3000 already in use" error:

# Find process using port 3000
lsof -i :3000

# Kill the process (macOS/Linux)
lsof -ti:3000 | xargs kill -9

# Then restart:
npm run dev
```

### Module Not Found

```bash
# If "Cannot find module" error:

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Then restart:
npm run dev
```

### TypeScript Errors

```bash
# Check for TypeScript issues
npm run type-check

# View all errors:
npm run type-check 2>&1 | less

# Fix errors and try again
npm run type-check
```

### Permissions Error

```bash
# If permission denied errors:

# On macOS/Linux:
chmod +x node_modules/.bin/*

# Or use sudo (not recommended):
sudo npm run dev
```

---

## Environment Setup

### .env.local File

Already exists at: `/Users/ankit/Aurora/aurora-web/.env.local`

Contains:
```
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=[REDACTED_GOOGLE_KEY]
```

To modify:
```bash
# Edit with any text editor
nano /Users/ankit/Aurora/aurora-web/.env.local

# Or in VS Code:
code /Users/ankit/Aurora/aurora-web/.env.local
```

---

## Monitoring Development

### While Running `npm run dev`

```bash
# Terminal shows activity like:
GET /sim 200 in 45ms          ← Page loaded
POST /api/runs 201 in 120ms   ← Data fetched
[webpack] compiled successfully  ← Code compiled

# Red text = Errors (check console)
# Yellow = Warnings (usually safe to ignore)
# Blue = Info messages
```

### Browser Network Tab

```
Shows all HTTP requests:
- GET / 200 OK              (page load)
- GET /api/runs 200 OK      (fetch data)
- GET /_next/static/... 200 (JS bundles)
- GET fonts/... 200         (Google Fonts)
```

---

## Production Deployment

### Build for Production

```bash
# Generate optimized build
npm run build

# Output shows:
# ✓ Build completed successfully
# - Compiled 12 files
# - Generated static files

# This creates: .next/ folder (optimized)
```

### Run Production Server

```bash
# After building:
npm start

# Runs optimized production build
# Use this for showing judges (faster than dev)
```

### Deployment Options

```bash
# Option 1: Vercel (recommended - free)
# 1. git push (commits changes)
# 2. Go to https://vercel.com
# 3. Import repository
# 4. Deploy (auto-deploys on every git push)

# Option 2: Docker
docker build -t aurora-web .
docker run -p 3000:3000 aurora-web

# Option 3: Traditional server
# Copy built app to server, run: npm start
```

---

## Performance Optimization

### Check Bundle Size

```bash
# Install analyzer
npm install --save-dev @next/bundle-analyzer

# Then run:
ANALYZE=true npm run build

# Shows visual breakdown of bundle size
```

### Improve Build Time

```bash
# Speed up dev build:
# Edit next.config.mjs:

module.exports = {
  swcMinify: true,
  productionBrowserSourceMaps: false,
}
```

---

## Package.json Scripts Explained

```json
{
  "scripts": {
    // Develop with hot reload
    "dev": "next dev",
    
    // Build optimized production version
    "build": "next build",
    
    // Run production build
    "start": "next start",
    
    // Check code style
    "lint": "next lint",
    
    // Verify TypeScript is correct
    "type-check": "tsc --noEmit"
  }
}
```

---

## Git Integration

### Version Control

```bash
# Check status
git status

# Add changes
git add .

# Commit
git commit -m "Add: SplitViewComparison component"

# Push to GitHub
git push origin Main

# Pull latest
git pull origin Main
```

### Rollback Changes

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Revert to specific commit
git checkout abc123def .
```

---

## Useful VS Code Extensions

```
Optional but helpful:

1. "ES7+ React/Redux/React-Native snippets"
   - Auto-complete for React code

2. "Tailwind CSS IntelliSense"
   - Auto-complete for Tailwind classes

3. "Prettier - Code formatter"
   - Format code with Shift+Option+F (macOS)

4. "ESLint"
   - Shows linting errors as you type

5. "Thunder Client"
   - Test API endpoints directly
```

---

## 30-Second Refresh

### "How do I run it?"

```bash
cd /Users/ankit/Aurora/aurora-web
npm install  # First time only
npm run dev  # Start server
# Open: http://localhost:3000
```

### "How do I stop it?"

```bash
# In terminal: Ctrl+C
```

### "How do I see changes?"

```bash
# Edit files in VS Code
# Save with Cmd+S
# Browser auto-reloads (1-2 seconds)
```

### "How do I build for demo?"

```bash
npm run build
npm start
# Faster and more optimized
```

---

## Summary

```
┌─────────────────────────────────────────────┐
│          Command Reference Card             │
├─────────────────────────────────────────────┤
│ npm install      → Install dependencies    │
│ npm run dev      → Start development       │
│ npm run build    → Build for production    │
│ npm start        → Run production build    │
│ npm run lint     → Check code style        │
│ Ctrl+C           → Stop server             │
│ Cmd+S            → Save file (auto reload) │
│ Cmd+Option+I     → Open DevTools           │
└─────────────────────────────────────────────┘
```

---

**Last Updated**: November 1, 2025  
**Status**: ✅ Ready to Run  
**Next Step**: `npm run dev` and open browser!
