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
- **Session outcome** means the **`outcome` column on `conversations`**: a single label per thread describing **how that chat session is regarded to have ended**—`completed` (user reached a satisfactory stopping point), `abandoned` (they left without that closure), or `open` (still in progress). In a real product you would set this via **explicit instrumentation** (e.g. “Resolve”, “Close”, idle timeout, CRM sync)—not by parsing message bodies. **This codebase does not infer `outcome` from text**; the **seed data picks values at random** so the quality charts are populated for the demo.
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

## Data model

Persistence is **SQLite** (single `.db` file). Set **`TWIN_DASHBOARD_DB`** to an absolute path if you do not want the default location.

### Entities and relationships

| Table | Role |
|-------|------|
| **`twins`** | One **deployed Twin** (e.g. a Slack workspace installation or a web app instance). Columns: human-readable `name`, `platform` (`slack`, `web`, …), `created_at`. This is the top-level “product instance” you report on. |
| **`twin_users`** | A **person** who can talk to that Twin: the **owner** who configured it and **collaborators** invited by the org. `twin_id` ties them to exactly one Twin; `role` is `owner` or `collaborator`. This split lets the dashboard measure **adoption inside a team** (volume by role). |
| **`conversations`** | A **single chat thread** (e.g. one DM or one channel thread). It belongs to a Twin and is **started by one** `twin_user_id`. `channel` stores where it happened (`dm`, `#general`, …) for **structural** breakdowns. `outcome` (`completed` / `abandoned` / `open`) is a **session-level** signal of whether the user got to a satisfying end state—kept on the thread, not on every message, so product can filter “successful” sessions without interpreting chat text. |
| **`messages`** | **Individual utterances** in a thread. `direction` is `inbound` (human → Twin) or `outbound` (Twin → human). `twin_user_id` is set for inbound rows (who spoke); outbound rows leave it `null` because the “speaker” is the Twin. Timestamps drive **volume**, **DAU**, and **stickiness** queries. |
| **`message_feedback`** | At most **one rating per outbound message** (`score`: +1 / −1), optional. Tied to `messages.id` so **quality** is anchored to a **specific Twin reply**, which matches how UIs usually show thumbs next to a message. |
| **`document_events`** | A **separate fact** when the user saves or exports a **draft** (email, memo, Slack post, …) in their style. It references `twin_id`, `twin_user_id`, and optionally `conversation_id` if the draft came from that chat. Kept out of `messages` so **“chat volume”** and **“documents produced”** stay distinct product metrics. |

Conceptually:

```text
twin (deployment)
 ├── twin_users (owner + collaborators)
 ├── conversations (threads: channel, outcome, starter)
 │    └── messages (inbound / outbound)
 │         └── message_feedback (optional, on outbound rows only)
 └── document_events (drafts; may link to a conversation)
```

### Why this shape

1. **Twin vs TwinUser** — One org may deploy one Twin but many employees use it; engagement must be attributed to **people** and **roles**, not only to “the bot”.
2. **Conversation vs Message** — Metrics need both **session starts** (new topics, funnel) and **message traffic** (depth, latency/cost proxies). Storing threads explicitly avoids inferring session boundaries from time gaps alone.
3. **Feedback on Message** — Granular and actionable (“this answer was bad”) vs a single score on the whole conversation.
4. **Document events** — Aligns with the product promise (draft in the user’s voice); counting only chat lines would understate **value delivered**.

### Implementation note

Heavy **counts and averages** are computed in **SQL** where possible. **Stickiness** metrics that need **median gaps between active days** use a small amount of **Python** after a grouped query.

---

## Repo layout

```
backend/    # uv + FastAPI
frontend/   # Vite + React + TS + Recharts
```

## Notes

- Charts: [Recharts](https://recharts.org/). Vite is pinned to **5.x** for broad Node compatibility (`frontend/package.json`).
- At least one aggregation endpoint with averages: **`/api/metrics/overview`** and others above.
