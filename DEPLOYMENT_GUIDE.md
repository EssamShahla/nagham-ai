# Nagham AI — Deployment & Management Guide

This guide covers two ways to put Nagham AI online, how to manage it afterwards, and a
testing checklist you can send to anyone trying the app. It assumes no prior hosting
experience.

> **Nothing in this guide has been deployed for you yet.** It documents the plan, the
> exact steps, and the trade-offs, so you can decide what to do and then do it (or ask
> for help doing it) without surprise charges.

---

## 1. The two options

| | **Option A — Cloudflare Tunnel** | **Option B — Cloud hosting** |
|---|---|---|
| What runs | Your existing local stack (Postgres, FastAPI, Next.js, **real Ollama**) | Frontend on Vercel, backend on Render, database on Neon, AI on Groq |
| Fidelity | 100% identical to local dev — the real local LLM, full speed | AI assistant uses a hosted LLM instead of Ollama (see §3) |
| Needs your PC on? | **Yes**, the whole time testers are using it | No — runs independently once deployed |
| Cost | Free, no account needed for a quick tunnel | Free tier on all 4 services, no credit card on any of them |
| Best for | A scheduled demo session, a quick link for Nauman to try *right now* | A link that stays up so people can test over days/weeks |
| Setup effort | ~5 minutes | ~45–60 minutes (one-time) |

**Recommendation:** use **Option A** for your first demo with Nauman (it's faster and
shows the real AI Assistant exactly as you built it). Set up **Option B** afterwards if
you want a link that keeps working without your laptop being on.

You can do both — they don't conflict.

---

## 2. Option A: Cloudflare Tunnel (fastest, full fidelity)

This exposes your already-running local app (`localhost:3000`) to a temporary public
HTTPS URL. No account, no code changes, nothing committed to GitHub.

### Steps

1. Make sure your full stack is running locally exactly as in the README: Postgres
   (`docker compose up -d`), backend (`uvicorn app.main:app --reload`), Ollama
   (`ollama serve`, model pulled), frontend (`npm run dev`).
2. Install `cloudflared` (one-time): download from
   [developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads)
   or `winget install --id Cloudflare.cloudflared`.
3. Run:
   ```powershell
   cloudflared tunnel --url http://localhost:3000
   ```
4. Cloudflare prints a random public URL like `https://random-words-1234.trycloudflare.com`.
   Share that with Nauman.
5. When you're done, press `Ctrl+C` in that terminal. The link stops working immediately
   — nothing stays exposed.

### Important limitations

- **Quick tunnels are anonymous and temporary** — the URL changes every time you restart
  the tunnel. There is no way to get a stable custom URL without a free Cloudflare
  account and a domain you control.
- Only the frontend port is tunneled above. The frontend talks to the backend via
  `NEXT_PUBLIC_API_URL`, which is baked in at build time as `http://127.0.0.1:8000` —
  that's fine because the tunnel runs on the *same machine*, so `127.0.0.1:8000` still
  resolves correctly for the Next.js server-side code. Browser-side calls also hit
  `127.0.0.1:8000` from the tester's browser, which will **not work** for a remote
  tester, because `127.0.0.1` means "the tester's own computer," not yours.
  **You must also tunnel the backend** and point the frontend at that tunnel URL:
  ```powershell
  cloudflared tunnel --url http://localhost:8000
  ```
  Then restart the frontend with that backend tunnel URL:
  ```powershell
  $env:NEXT_PUBLIC_API_URL = "https://<backend-tunnel-domain>"
  npm run dev
  ```
  You'll end up with two tunnels running in two terminals (frontend URL to share,
  backend tunnel used internally by the frontend).
- Anyone with the link can reach your local Postgres-backed API while the tunnel is
  open. Don't leave it running unattended; treat the link as "live only while you're
  watching."

---

## 3. Option B: Free cloud hosting (always-on)

### 3.1 Architecture

```
Browser ──HTTPS──> Vercel (Next.js frontend)
                         │
                         ▼  HTTPS (NEXT_PUBLIC_API_URL)
                    Render (FastAPI backend)
                         │
            ┌────────────┼───────────────┐
            ▼                            ▼
   Neon (Postgres + pgvector)     Groq (hosted LLM, OpenAI-compatible)
```

- **Frontend — Vercel.** Free "Hobby" tier, no card required. Deploys directly from
  your GitHub repo on every push.
- **Backend — Render.** Free "Web Service" tier, no card required. Runs the FastAPI
  app + the local embedding model (sentence-transformers) in the same process.
- **Database — Neon.** Free tier, no card required, Postgres with the `pgvector`
  extension available out of the box. Good fit because it auto-suspends when idle and
  wakes on the next query (no 30-day data expiry like some other free Postgres offers).
- **AI language model — Groq.** Free tier, no card required, OpenAI-compatible API.
  Used instead of Ollama because Render's free compute (0.1 CPU / 512 MB RAM) cannot
  run a local LLM — Ollama + `qwen2.5:3b` alone needs several GB of RAM.

### 3.2 What stays exactly the same

- The **LangGraph workflow** (`backend/app/ai/graph.py`, `tools.py`) is untouched —
  routing between structured / semantic / hybrid search is unchanged.
- The **embedding model** (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`,
  384 dimensions) keeps running locally inside the backend process, exactly as today.
  No vector data needs to be re-computed and no column size changes.
- All database migrations, auth, and JWT logic are unchanged.

### 3.3 What's different from local dev

- The LLM calls (`backend/app/ai/llm_client.py`) go to Groq's hosted API instead of a
  local Ollama server. This is controlled entirely by environment variables — nothing
  is hardcoded. Expect:
  - **Latency**: Groq is typically *faster* than a local 3B model on a laptop CPU, but
    depends on Groq's current load.
  - **Model behavior**: Groq doesn't host `qwen2.5:3b` specifically. You'll pick a
    comparable instruction-following model from Groq's current free model list (check
    [console.groq.com](https://console.groq.com) → Playground → model dropdown, since
    available free models change over time). Answers may phrase things slightly
    differently than your local Qwen model, but the retrieval logic, system prompt, and
    JSON-schema constraints are identical.
  - **Free-tier rate limits** (subject to change — verify at
    [console.groq.com/docs/rate-limits](https://console.groq.com/docs/rate-limits)):
    roughly 30 requests/minute and a few thousand requests/day on free models as of
    late 2026. Fine for a handful of testers; not for heavy concurrent load.
- **Known risk — embedding model RAM**: Render's free tier gives only 512 MB RAM. The
  sentence-transformers model plus PyTorch plus FastAPI may be tight on that budget. If
  the backend crashes or fails to start on Render, that's the most likely cause. There's
  no code workaround for this within the "genuinely free" constraint — the only fixes
  are (a) upgrading Render to a paid Starter instance ($7/mo, more RAM) or (b) hosting
  the backend on a provider with more free RAM if/when one becomes available. **Do not
  upgrade to a paid tier without deciding that explicitly** — it is not required to try
  the free deployment first.

### 3.4 Accounts you need to create

All of the following are free and do not ask for a credit card at signup (verified
October 2026 — hosting providers change terms, so double-check at signup time):

1. **Vercel** — [vercel.com/signup](https://vercel.com/signup) (sign up with your
   GitHub account for the easiest setup).
2. **Render** — [render.com](https://render.com) (sign up with GitHub).
3. **Neon** — [neon.tech](https://neon.tech) (sign up with GitHub or email).
4. **Groq** — [console.groq.com](https://console.groq.com) (sign up, then create an API
   key under "API Keys").

You already have a GitHub repo (`github.com/EssamShahla/nagham-ai`). **The current
working tree has uncommitted changes from this session that are not yet pushed** — ask
me to commit and push them first, since deployment needs the code on GitHub.

### 3.5 Step-by-step setup

**Database (Neon) — do this first:**
1. Create a project in Neon. Note the connection string it gives you (starts with
   `postgresql://`).
2. Neon connection strings already include `?sslmode=require` — keep that.
3. From your machine, run the existing migrations against the Neon database:
   ```powershell
   cd backend
   $env:DATABASE_URL = "<neon-connection-string>"
   .\venv\Scripts\Activate.ps1
   alembic upgrade head
   ```
4. Enable the `pgvector` extension if Neon hasn't already: connect with `psql` (Neon
   gives you a one-click SQL editor in its dashboard) and run `CREATE EXTENSION IF NOT
   EXISTS vector;`.
5. Your existing song/maqam/user data is local-only right now (in the Docker Postgres
   container) — it will **not** automatically appear in Neon. If you want the same demo
   data on the public site, you'll need to export/import it (`pg_dump` from local,
   `psql` restore into Neon), or re-enter it through the app's own "Add song" / "Add
   maqam" forms.

**AI (Groq):**
1. Create an API key at [console.groq.com](https://console.groq.com/keys).
2. Note a current free-tier model name from the Groq docs/playground.

**Backend (Render):**
1. New → Web Service → connect your GitHub repo → root directory `backend`.
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Environment variables (set these in Render's dashboard, never commit them):
   - `DATABASE_URL` = your Neon connection string
   - `JWT_SECRET_KEY` = a long random string (generate with
     `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `EMAIL_ADDRESS`, `EMAIL_APP_PASSWORD` = same Gmail app-password setup as local
   - `FRONTEND_URL` = your Vercel URL (set after step below)
   - `CORS_ALLOWED_ORIGINS` = your Vercel URL (e.g. `https://nagham-ai.vercel.app`)
   - `LLM_PROVIDER` = `openai_compatible`
   - `LLM_BASE_URL` = `https://api.groq.com/openai/v1`
   - `LLM_API_KEY` = your Groq API key
   - `LLM_MODEL` = the Groq model name you picked
5. Deploy. Render gives you a URL like `https://nagham-ai-backend.onrender.com`.

**Frontend (Vercel):**
1. New Project → import the same GitHub repo → root directory `frontend`.
2. Environment variable: `NEXT_PUBLIC_API_URL` = your Render backend URL.
3. Deploy. Vercel gives you a URL like `https://nagham-ai.vercel.app`.
4. Go back to Render and set `FRONTEND_URL` / `CORS_ALLOWED_ORIGINS` to this exact URL,
   then redeploy the backend so CORS allows it.

**Ollama**: not deployed anywhere in this architecture — intentionally, since no free
tier here has the RAM for it.

---

## 4. Managing the deployment yourself

### 4.1 Where things live
- **Frontend**: Vercel dashboard → your project.
- **Backend**: Render dashboard → your web service.
- **Database**: Neon dashboard → your project.
- **AI**: Groq console → API keys / usage.
- **Code**: GitHub repo, same as today.

### 4.2 Start / stop / restart
- **Vercel**: there's no manual "start/stop" — it's always deployed. To take the site
  down, go to Project → Settings → scroll to "Delete Project" (irreversible) or simply
  stop sharing the URL. To restart after a bad deploy, go to Deployments → pick a
  previous working deployment → "Promote to Production."
- **Render**: Dashboard → your service → "Manual Deploy" restarts it. There's also a
  "Suspend" option in Settings if you want to stop it without deleting it.
- **Neon**: Databases auto-suspend when idle and auto-resume on the next query — no
  manual start/stop needed. You can manually suspend compute from the dashboard too.

### 4.3 Viewing logs
- **Render**: Dashboard → your service → "Logs" tab, live-streamed. This is where
  you'll see Python tracebacks, startup errors, or OOM kills.
- **Vercel**: Dashboard → your project → "Deployments" → click a deployment → "Logs" /
  "Runtime Logs" for request-level errors.
- **Neon**: Dashboard → "Monitoring" tab shows connection counts and compute usage.

### 4.4 Redeploying after GitHub changes
Both Vercel and Render auto-deploy on every push to the branch you connected (usually
`main`). Push your changes, then watch the "Deployments" tab on each dashboard. No
manual redeploy step needed unless auto-deploy is turned off.

### 4.5 Updating environment variables
- **Render**: Settings → "Environment" → edit values → "Save Changes" triggers an
  automatic redeploy with the new values.
- **Vercel**: Settings → "Environment Variables" → edit → you must trigger a new
  deployment (redeploy the latest commit) for `NEXT_PUBLIC_...` changes to take effect,
  since they're baked in at build time.

### 4.6 Checking database connectivity
Visit `https://<your-render-backend-url>/db-test` in a browser. It returns
`{"message": "Database connection successful"}` on success, or a 500 error with a
traceback in Render's logs if the connection fails (wrong `DATABASE_URL`, Neon project
suspended/deleted, etc.).

### 4.7 Monitoring resource usage
- **Render**: Dashboard → "Metrics" tab shows CPU and memory usage over time. Watch
  memory specifically — if it's pinned near 512 MB, that's the RAM risk from §3.3.
- **Vercel**: Dashboard → "Usage" (account level) shows bandwidth, function
  invocations, and build minutes against the Hobby plan's monthly limits.
- **Neon**: Dashboard → "Usage" shows storage and compute-hours against the free
  allowance.
- **Groq**: Console → usage shows requests against your rate limit.

### 4.8 Diagnosing downtime
1. Visit `/` on the Render URL directly. If it doesn't load at all, check Render's
   "Events" tab for a crash/restart loop, and "Logs" for the actual error.
2. If `/` loads but `/db-test` fails, the problem is Neon (suspended project, expired
   free-tier project, wrong credentials) — check the Neon dashboard.
3. If pages load but the AI Assistant fails, check Render logs for Groq API errors
   (commonly: rate limit hit, invalid API key, or model name no longer available on the
   free tier — Groq's free model lineup changes periodically).
4. If the frontend loads but every API call fails with a CORS error in the browser
   console, double check `CORS_ALLOWED_ORIGINS` on Render matches the exact Vercel URL
   (including `https://`, no trailing slash).

### 4.9 Backing up and restoring the database
- **Backup**: Neon dashboard → your project → "Backup & restore" has point-in-time
  recovery on paid plans; on the free plan, take manual backups yourself with
  `pg_dump`:
  ```powershell
  pg_dump "<neon-connection-string>" -f nagham_backup.sql
  ```
- **Restore**: into a fresh Neon project (or back into the same one) with:
  ```powershell
  psql "<neon-connection-string>" -f nagham_backup.sql
  ```
- Keep `nagham_backup.sql` somewhere private — it contains real user emails and
  password hashes. Never commit it to GitHub.

### 4.10 Shutting everything down safely
1. Vercel: Project Settings → Delete Project.
2. Render: Service Settings → Delete Service.
3. Neon: Project Settings → Delete Project (**this permanently deletes the database —
   back it up first if you want to keep the data**).
4. Groq: revoke the API key from the console (optional, but good hygiene).
5. Remove the corresponding entries from your local `.env` / Render/Vercel env var
   screens — nothing else to clean up, since no secrets are committed to GitHub.

### 4.11 What happens when a free tier sleeps or hits its limit
- **Render**: after 15 minutes with no traffic, the free web service spins down. The
  next request wakes it up but takes about a minute to respond while it cold-starts —
  testers may see a loading/timeout on the very first request after idle time. Later
  requests are fast again. If you exceed 750 instance-hours in a month (unlikely for a
  demo with occasional testers), Render pauses the service until the next month.
- **Vercel**: Hobby sites don't sleep. If you exceed the monthly bandwidth/function
  quota, Vercel pauses the project until you upgrade or the next billing cycle starts —
  it will not silently start charging you.
- **Neon**: compute auto-suspends after a short idle period and resumes on the next
  query, typically within about a second — rarely noticeable. If you exceed the storage
  cap (1 GB/project), writes start failing until you free up space or upgrade.
- **Groq**: once you hit the rate limit, requests return an error (visible to the user
  as "Nagham AI ran into a problem answering that" in the Assistant UI, since the
  frontend's error handling surfaces the backend's error message). It resets on the
  next rate-limit window (per-minute and per-day).

None of these free tiers will auto-upgrade you into a paid plan or charge a card on
file — they cap you off instead. That's exactly why no card is needed for this setup.

---

## 5. Sharing with testers

Send testers:
1. The public URL (Vercel URL for Option B, or the `trycloudflare.com` URL for Option
   A — remind them it changes every time you restart the tunnel).
2. The testing checklist below.
3. A heads-up that first load after idle time can take up to a minute (Option B,
   Render cold start) — not a bug, just the free tier waking up.

### Testing checklist for external testers

- [ ] Landing page loads and looks right on your device (try both phone and desktop if
  you can).
- [ ] Register a new account.
- [ ] Check your email for the verification code and enter it on the Verify page.
- [ ] Log in with that account.
- [ ] Browse the **Songs** library — search, filter by maqam/difficulty.
- [ ] Open the **Maqamat** page — click into a couple of maqamat, check the detail page.
- [ ] Try the **AI Assistant** — ask something like "اعطني اغاني فيروز" or "songs about
  longing in Bayati." Confirm you get a real, relevant answer (not an error).
- [ ] Try the **Lyrics / meaning search** page with a feeling-based query.
- [ ] Add a song via **Add Song** (any test data is fine) and confirm it shows up in the
  library afterwards.
- [ ] Open your **Profile** page, edit something, save, refresh the page, confirm the
  change stuck.
- [ ] Try the site on your phone's browser — check the menu opens/closes properly and
  nothing overflows the screen.
- [ ] Report anything that errored, looked broken, or felt confusing — screenshots help.

---

## 6. Security notes before inviting testers

- Test accounts created by testers are real rows in your production-ish database —
  nobody can reach admin-only actions (adding maqamat, editing other users' songs)
  unless you manually promote their account's `role` to `admin` in the database.
  Don't do that for test accounts.
- OTP emails are sent from your real Gmail address (via `EMAIL_ADDRESS` /
  `EMAIL_APP_PASSWORD`). Testers will see "Nagham AI" as the sender name, but it's your
  address underneath — that's expected and matches local dev behavior.
- There is currently no rate limiting on `/auth/login` or `/auth/register` beyond the
  OTP resend cooldown. For a small group of named testers this is a low risk; it would
  need addressing before a fully public, unauthenticated launch.
- Postgres (Neon) and the LLM provider (Groq) are never exposed directly to the
  internet from the frontend — all traffic goes through your FastAPI backend, which is
  the intended boundary.
- Keep `backend/.env` and any local `.env.local` files out of GitHub (already enforced
  by `.gitignore`) and out of chat messages/screenshots you send to testers.
