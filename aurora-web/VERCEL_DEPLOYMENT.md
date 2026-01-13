# Vercel Deployment Guide for Aurora Web

Your Vercel deployment likely failed due to one of three reasons:
1.  **Wrong Root Directory**: Since `aurora-web` is a folder inside your repository, you must tell Vercel where to find it.
2.  **Missing Environment Variables**: Your Google Maps API key needs to be set in Vercel.
3.  **Filesystem Access**: The app was trying to access Python scripts and result files (`../results`) that don't exist on Vercel servers.

## 🛠 Fix 1: Configure Project Settings

1.  Go to your Vercel Dashboard -> Select your Project.
2.  Go to **Settings** -> **General**.
3.  Find **Root Directory**.
4.  Click **Edit** and set it to: `aurora-web`.
5.  Save. This ensures Vercel finds `package.json` and builds the correct app.

## 🔑 Fix 2: Add Environment Variables

1.  Go to **Settings** -> **Environment Variables**.
2.  Add the key from your `.env.local` file:
    *   **Key**: `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`
    *   **Value**: (Your API Key starting with AIza...)
3.  Click **Save**.

## ☁️ Fix 3: Code Compatibility (Already Patched)

I have automatically patched the following files to prevent crashes on Vercel:
*   `src/app/api/runs/route.ts`: Removed file system calls that look for local result folders.
*   `src/app/api/run_experiment/route.ts`: Added a check to disable live Python training on Vercel (since Vercel cannot run your local `train_manager.py` script).

## ⚠️ Important Limitations on Vercel

Because Vercel is a serverless cloud environment:
1.  **Live Training Won't Work**: You cannot run new experiments via the web interface.
2.  **Local Logs Unavailable**: The dashboard will not show past runs stored on your laptop (`../results`). It will show mock/demo data instead.

**To restore full functionality**, running locally is recommended:
```bash
cd aurora-web
npm run dev
```
