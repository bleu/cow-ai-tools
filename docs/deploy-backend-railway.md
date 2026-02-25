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
   - `PROJECT` = `cow`
   - `OP_CHAT_BASE_PATH` = `/app/data`
   - `GOOGLE_API_KEY` = your Gemini API key (from [Google AI Studio](https://aistudio.google.com/apikey))
   - **Important:** After adding or changing any variable, trigger a **new deployment** (e.g. Deployments → ⋮ → Redeploy). Railway injects variables when the container starts; existing containers keep the old env until redeployed.
4. Service **Settings** (if needed):
   - **Root Directory:** empty (repo root).
   - Do not set Build Command / Start Command; the Dockerfile handles that.
5. **Data (FAISS) — required for RAG:** The Dockerfile copies `data/cow-docs/faiss` into the image. **Before** your first deploy (or any deploy from Git), generate that folder locally:
   - From repo root: ensure you have `data/cow-docs/cow_docs.txt` (and optionally `openapi.yml`). Create them with the scripts in `scripts/cow-1-create-docs-dataset` and `scripts/cow-2-fetch-openapi` if needed.
   - Then run:  
     `cd pkg/op-app && PROJECT=cow OP_CHAT_BASE_PATH=../../data GOOGLE_API_KEY=<your-key> poetry run python -m cow_brains.build_faiss`  
     This creates `data/cow-docs/faiss/` (e.g. `index.faiss`, `index.pkl`).
   - Either **commit** `data/cow-docs/faiss/` (remove it from `.gitignore` if present) so Railway’s build can copy it, or build the Docker image locally (where the folder exists) and push to your registry. Set `OP_CHAT_BASE_PATH=/app/data` in Railway variables.
6. Railway generates a public URL (e.g. `https://cow-ai-backend-production.up.railway.app`). In **Settings** → **Networking** → **Generate Domain** if you don't have one yet.
7. In the **frontend** (Vercel or elsewhere), set:
   - `NEXT_PUBLIC_CHAT_API_URL` = `https://<your-railway-url>/predict`  
   (The Quart API exposes `/up` and `/predict` at the root; there is no `/api` prefix like on Vercel.)

### Image size limit (Railway)

Railway limits Docker images to **4 GB** on the default plan. To stay under this limit, the backend image uses **`requirements-backend.txt`** (no torch, sentence-transformers, or transformers). CoW uses **Gemini only** for embeddings, so those packages are not needed at runtime. The image should be under 4 GB; if it still exceeds, try **Render** (Option 2) or upgrade Railway.

### Test the backend

```bash
curl -s https://<your-railway-url>/up
curl -s -X POST https://<your-railway-url>/predict \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I compute appData?", "memory": []}'
```

### Troubleshooting: "GOOGLE_API_KEY not set" but it's in Variables

If the deploy log shows `WARNING: GOOGLE_API_KEY (or GEMINI_API_KEY) not set` even though you added it in the Variables tab:

1. **Confirm the service** — Variables are per **service**. Open the service that runs the backend (the one with `RAILWAY_DOCKERFILE_PATH=Dockerfile.backend`), then **Variables**. Add or edit the key there, not in another service.
2. **Redeploy after every change** — Use **Deployments** → ⋮ → **Redeploy** (or push a commit). The running container only gets variables from when it was started.
3. **Exact variable name** — Use `GOOGLE_API_KEY` or `GEMINI_API_KEY`. No extra spaces; value = the key only (no quotes in the value).
4. **Raw Editor** — In Variables, switch to **Raw Editor** and ensure one line is exactly:  
   `GOOGLE_API_KEY=AIza...`  
   (your key after the `=`). Save and redeploy.
5. **File fallback** — If env still doesn’t reach the process, you can pass the key via a file: set `GOOGLE_API_KEY_FILE=/app/secrets/gemini_key` and ensure that path exists in the container with the key as its contents (e.g. via a secret mount or a custom Docker step; platform-dependent).

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
