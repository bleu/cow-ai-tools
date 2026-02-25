# CoW Backend Outside Vercel (Railway / Render)

The backend **cannot** run as serverless on Vercel: dependencies (sentence-transformers, faiss-cpu, torch, etc.) exceed **8 GB**; Vercel's deployment limit is **500 MB** ephemeral storage. Use a service that runs a long-lived process (Railway, Render, Fly.io, etc.).

---

## Option 1: Railway

Railway's Railpack may fail with **"Error creating build plan with Railpack"** on monorepos. Use the **Dockerfile** for the backend.

1. Go to [railway.app](https://railway.app) and create a project.
2. **Add Service** → **GitHub Repo** → select `bleu/cow-ai-tools`.
3. **Variables** (environment variables) — add **before** the first deploy:
   - `RAILWAY_DOCKERFILE_PATH` = `Dockerfile.backend`  
   (so Railway uses Docker instead of Railpack.)
4. Service **Settings** (if needed):
   - **Root Directory:** empty (repo root).
   - Do not set Build Command / Start Command; the Dockerfile handles that.
   - `PROJECT` = `cow`
   - `OP_CHAT_BASE_PATH` = path to data (see below)
   - `GOOGLE_API_KEY` = your Gemini API key
6. **Data (FAISS):** Build the index locally (`python -m cow_brains.build_faiss` with `OP_CHAT_BASE_PATH` pointing to a `data/` folder), then:
   - **Option A:** Include `data/cow-docs/faiss` in the repo (adjust `.gitignore`) and use `OP_CHAT_BASE_PATH=/app/data` (or the working directory on Railway).
   - **Option B:** Use Railway **Volumes** to persist a `data` folder and build FAISS on first deploy (build command that runs build_faiss).
7. Railway generates a public URL (e.g. `https://cow-ai-backend-production.up.railway.app`). In **Settings** → **Networking** → **Generate Domain** if you don't have one yet.
8. In the **frontend** (Vercel or elsewhere), set:
   - `NEXT_PUBLIC_CHAT_API_URL` = `https://<your-railway-url>/predict`  
   (The Quart API exposes `/up` and `/predict` at the root; there is no `/api` prefix like on Vercel.)

### Image size limit (Railway)

Railway limits Docker images to **4 GB** on the default plan. This backend image (torch, sentence-transformers, faiss-cpu) is typically **~9 GB**, so the build may fail with *"Image of size X GB exceeded limit of 4.0 GB"*.

**Options:**

- **Use Render instead** — Render does not enforce the same image size cap for web services; building with the same Dockerfile or with Build/Start commands often works. Prefer **Option 2: Render** below if you hit the limit on Railway.
- **Upgrade Railway** — Higher plans may allow larger images; check [Railway pricing](https://railway.app/pricing).
- The Dockerfile is already optimized (build tools removed after `pip install`); further shrinking would require dropping or replacing heavy deps (e.g. different embedding model).

### Test the backend

```bash
curl -s https://<your-railway-url>/up
curl -s -X POST https://<your-railway-url>/predict \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I compute appData?", "memory": []}'
```

---

## Option 2: Render (Web Service)

1. [render.com](https://render.com) → **New** → **Web Service**.
2. Connect the repo `bleu/cow-ai-tools`.
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `bash scripts/run-backend.sh`
5. **Environment:** add `PROJECT`, `OP_CHAT_BASE_PATH`, `GOOGLE_API_KEY`.
6. Render sets `PORT` automatically; the `run-backend.sh` script uses that variable.
7. Use the generated URL (e.g. `https://cow-ai-backend.onrender.com`) in `NEXT_PUBLIC_CHAT_API_URL` + `/predict`.

---

## Summary

| Where   | Frontend | Backend |
|--------|----------|---------|
| Vercel | ✅ Next.js (Root: `www`) | ❌ Does not fit (500 MB limit) |
| Railway / Render | — | ✅ Quart with FAISS + Gemini |

Always set `NEXT_PUBLIC_CHAT_API_URL` in the frontend to the backend URL (e.g. `https://xxx.up.railway.app/predict` or `https://xxx.onrender.com/predict`).
