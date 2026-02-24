# Deploying on Vercel

You can deploy the **frontend** (Next.js) and the **backend** (Quart chat API) as two separate Vercel projects from this monorepo.

## 1. Frontend (Next.js)

### Opção A: Vercel Dashboard (recomendado)

1. Acesse [vercel.com](https://vercel.com) e faça login.
2. **Add New** → **Project** e importe o repositório Git (GitHub/GitLab/Bitbucket).
3. Em **Configure Project**, defina **Root Directory** → **Edit** → `www`.
4. Clique em **Deploy**. O primeiro build pode levar alguns minutos.
5. Depois do deploy, em **Settings → Environment Variables** adicione:
   - `NEXT_PUBLIC_CHAT_API_URL` = URL do backend (ex.: `https://seu-backend.vercel.app/api/predict`)
   - `NEXT_PUBLIC_BRAND` = `cow`
   - Outras variáveis de `www/.envrc.example` se precisar (ex.: `NEXT_PUBLIC_POSTHOG_KEY`).
6. Faça **Redeploy** para aplicar as variáveis.

### Opção B: Vercel CLI

```bash
# Instalar CLI (uma vez)
npm i -g vercel

# Na raiz do repo
cd /caminho/para/cow-ai-tools
vercel

# Quando perguntar "Set up and deploy?", escolha o projeto ou crie um novo.
# Importante: defina Root Directory = www no dashboard depois, ou use:
vercel --cwd www
```

O frontend chama o backend em `NEXT_PUBLIC_CHAT_API_URL` para o chat (POST com `question` e `memory`).

## 2. Backend (Chat API)

The backend is a Quart app served as a Vercel serverless function. It uses the `api/` folder and `requirements.txt` at the **repository root**.

### O que preencher no "New Project" (backend)

1. **Vercel Team** — deixe como está.
2. **Project Name** — ex.: `cow-ai-backend`.
3. **Application Preset** — **Other** (Python serverless).
4. **Root Directory** — deixe **vazio** ou `./`. Não use `www`.
5. **Build and Output Settings** — toggles desligados.
6. **Environment Variables** — adicione:

   | Key | Value |
   |-----|--------|
   | `PROJECT` | `cow` |
   | `OP_CHAT_BASE_PATH` | `/var/task/data` (se dados em `data/` no repo) |
   | `GOOGLE_API_KEY` | sua chave Gemini |

### Dados (FAISS) — obrigatório para o CoW

O backend precisa do índice FAISS. Crie um **segundo** projeto Vercel (mesmo repo).
2. Leave **Root Directory** empty (repo root).
3. In **Settings → Environment Variables**, set at least:
   - `PROJECT` = `cow` (for CoW Protocol)
   - `OP_CHAT_BASE_PATH` = path to data (see below)
   - `GOOGLE_API_KEY` = your Gemini/embedding key

   For CoW, the app expects FAISS and docs under `OP_CHAT_BASE_PATH`. At runtime Vercel’s project root is `/var/task`. Options:
   - **Include data in the repo**: Commit `data/cow-docs/faiss` (and `cow_docs.txt` if needed), then set `OP_CHAT_BASE_PATH=/var/task/data`.
   - **Generate at build time**: in **Build Command**, run your script to build the CoW docs artifact and FAISS, then set `OP_CHAT_BASE_PATH` to that directory (e.g. under `/tmp` is writable but not persistent; building FAISS in the build step and leaving it in the deployment is preferred if your build outputs are included).

4. **Requirements**: The repo root has a `requirements.txt` (PyPI deps only). Local packages (`pkg/op-app`, `pkg/op-brains`, etc.) are loaded via `sys.path` in `api/index.py`. No extra install step is needed for them if the repo is deployed as-is.

5. Deploy. The API will be available at:
   - `https://<your-backend-project>.vercel.app/api/up` (health)
   - `https://<your-backend-project>.vercel.app/api/predict` (chat)

### Regenerating `requirements.txt`

If you add or change dependencies in `pkg/op-app`, regenerate the root `requirements.txt`:

```bash
cd pkg/op-app
poetry run pip list --format=freeze | grep -v -E '^(op-app|op-brains|cow-brains|op-core|op-data|op-artifacts|-[e ])' | sed 's/==/>=/' > ../../requirements.txt
# Remove any remaining local package lines (op_app, etc.) from ../../requirements.txt
```

### Limits and alternatives

- **Bundle size**: Python serverless on Vercel has a 250 MB uncompressed limit. This app pulls in `sentence-transformers`, `faiss-cpu`, and other heavy deps; the bundle may approach or exceed the limit.
- **Timeout**: Function timeout is 60 s (Pro). Chat can be slow under load.
- **Cold starts**: First request after idle can be slow.

If you hit limits or need a long-running process, run the backend elsewhere (e.g. **Railway**, **Render**, or **Fly.io**) and point the frontend’s `NEXT_PUBLIC_CHAT_API_URL` at that host. You can run the same Quart app with e.g. `hypercorn op_app.api:app` in `pkg/op-app`.

## Summary

| Project   | Root Directory | API base URL (example) |
|----------|----------------|-------------------------|
| Frontend | `www`          | —                       |
| Backend  | (empty = root) | `https://xxx.vercel.app/api` |

Set the frontend env `NEXT_PUBLIC_CHAT_API_URL` to `https://<backend-project>.vercel.app/api/predict`.
