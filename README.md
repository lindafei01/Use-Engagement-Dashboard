# Twin Engagement Dashboard

Full-stack demo: **FastAPI + SQLite** backend with aggregated metrics APIs; **React + TypeScript (Vite)** dashboard UI in **English** for global teams.

## How to run

### 1. Backend

Requires [uv](https://docs.astral.sh/uv/).

```bash
cd backend
uv sync
uv run twin-dashboard-seed    # sample data (safe to re-run; resets DB content)
uv run uvicorn twin_dashboard_api.main:app --host 127.0.0.1 --port 8765 --reload
```

- Health: <http://127.0.0.1:8765/api/health>
- Swagger: <http://127.0.0.1:8765/docs>

### 2. Frontend

**Node.js 18+** (20 LTS recommended). Do **not** rely on Ubuntu’s default **Node 12** from `apt install npm` — Vite will fail with `SyntaxError: Unexpected reserved word`.

```bash
node -v   # must be v18+
cd frontend
rm -rf node_modules
npm install
npm run dev
```

Vite proxies `/api`, `/docs`, and `/openapi.json` to `http://127.0.0.1:8765`. Open <http://localhost:5173>.

**Remote server:** run backend + `npm run dev` (host `0.0.0.0` on port 5173), then from your laptop:  
`ssh -L 5173:127.0.0.1:5173 user@server` and browse `http://localhost:5173`.

### 3. Production build (frontend)

```bash
cd frontend
npm run build
npm run preview
```

If API is on another origin: `VITE_API_BASE=http://your-api:8765 npm run build` and set backend `CORS_ORIGINS`.

---

## Dashboard screenshots

Below are captures of the web UI (English copy, seeded sample data). Files live under [`visualizations/`](visualizations/).

### 1. Volume — KPIs and daily activity

![Volume KPI cards and daily inbound/outbound trend](visualizations/vis1.png)

### 2. Volume — new conversations

![New conversations per day](visualizations/vis2.png)

### 3. Quality and stickiness

![Feedback, documents, outcomes, and retention metrics](visualizations/vis3.png)

### 4. Structure and Twins directory

![Inbound by role and channel, and Twin list](visualizations/vis4.png)

---

## Metrics

The dashboard is organised around four pillars:

| Pillar | What we measure | Why it matters |
|--------|-----------------|----------------|
| **Volume** | Inbound/outbound messages, new conversations, DAU (mean), depth per conversation | Is the product used enough? Capacity and cost. |
| **Quality** | Thumbs up/down on Twin replies, share of outbound with feedback, **document drafts** (email, memo, Slack post), **session outcome** (completed / abandoned / open) | Did answers help? Did users produce work in their style? |
| **Stickiness** | Distinct users, repeat days, median gap between active days, **half-period retention** (first vs second half of window) | One-off trials vs sustained adoption. |
| **Structure** | Inbound split by **owner vs collaborator**, and by **channel** (DM, `#channel`, etc.) | Is adoption spreading inside the org? |

**Assumptions**

- “Active” = at least one **inbound** message that day (UTC). Passive reads are not tracked.
- **Session outcome** is a product-side classification (or manual tag); sample data is synthetic.
- **Feedback** is stored per **outbound** message; **document events** are separate rows when a user saves a draft.
- Timestamps are **UTC**; production should align to tenant timezone for reporting.

**API routes (aggregations)**

- `GET /api/metrics/overview` — volume KPIs (includes averages).
- `GET /api/metrics/daily` — time series.
- `GET /api/metrics/quality` — feedback, documents, outcomes.
- `GET /api/metrics/stickiness` — retention-style metrics.
- `GET /api/metrics/structure` — breakdown by role and channel.
- `GET /api/twins` — Twin directory.

---

## Data model (why these tables)

- **SQLite** file; default path under OS temp dir `twin_dashboard/twin_metrics.db` (often local disk; avoids NFS `disk I/O` issues). Override with **`TWIN_DASHBOARD_DB`**.
- **`twins`** → **`twin_users`** (owner / collaborator), **`conversations`** (includes `channel`, `outcome`) → **`messages`** (inbound/outbound).
- **`message_feedback`** — optional rating on an outbound message (`score` ±1).
- **`document_events`** — user generated a draft (`doc_type`: email, memo, slack_post, other).
- Aggregations stay in **SQL** where possible; heavier stickiness (median gaps) uses small follow-up logic in Python.

---

## Repo layout

```
backend/    # uv + FastAPI
frontend/   # Vite + React + TS + Recharts
```

## Notes

- Charts: [Recharts](https://recharts.org/). Vite is pinned to **5.x** for broad Node compatibility (`frontend/package.json`).
- At least one aggregation endpoint with averages: **`/api/metrics/overview`** and others above.
