# Deploying on Vercel

Deploy only the **frontend** (Next.js) on Vercel. The **backend** does not run on Vercel (dependencies exceed the 500 MB limit); use [Railway or Render](deploy-backend-railway.md) for the backend.

## Frontend (Next.js)

### Option A: Vercel Dashboard (recommended)

1. Go to [vercel.com](https://vercel.com) and log in.
2. **Add New** → **Project** and import your Git repository (GitHub/GitLab/Bitbucket).
3. In **Configure Project**, set **Root Directory** → **Edit** → `www`.
4. Click **Deploy**. The first build may take a few minutes.
5. After deploy, in **Settings → Environment Variables** add:
   - `NEXT_PUBLIC_CHAT_API_URL` = backend URL (e.g. `https://your-backend.up.railway.app/predict`)
   - `NEXT_PUBLIC_BRAND` = `cow`
   - Other variables from `www/.envrc.example` if needed (e.g. `NEXT_PUBLIC_POSTHOG_KEY`).
6. **Redeploy** to apply the variables.

### Option B: Vercel CLI

```bash
# Install CLI (once)
npm i -g vercel

# From repo root
cd /path/to/cow-ai-tools
vercel

# When prompted "Set up and deploy?", choose the project or create a new one.
# Important: set Root Directory = www in the dashboard afterward, or use:
vercel --cwd www
```

The frontend calls the backend at `NEXT_PUBLIC_CHAT_API_URL` for chat (POST with `question` and `memory`). The backend should run on **Railway** or **Render** — see [deploy-backend-railway.md](deploy-backend-railway.md).

## Summary

| Where   | Root Directory | Notes |
|--------|----------------|-------|
| Vercel | `www`          | Frontend only. Set `NEXT_PUBLIC_CHAT_API_URL` = backend URL (Railway/Render). |
