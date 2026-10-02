# Reddit AI Outreach Platform

Multi-tenant lead generation on Reddit: agents find buying-intent posts, score them, and draft replies, and a person approves every reply before it is posted.

> **Status: skeleton.** Reddit and OpenAI are **mocked**, so no external API keys are needed.
> `REDDIT_MODE=mock` returns canned sample posts, and `LLM_MODE=mock` uses heuristic agents.

## Layout

```
backend/                 FastAPI + SQLAlchemy (async) + Celery
  app/
    api/v1/              auth, org/team, config, leads, replies, pipeline/analytics
    agents/              Niche Interpreter, Scout, Classifier, Drafter (mock implementations)
    integrations/reddit/ RedditClient protocol + MockRedditClient
    services/            pipeline, compliance (subreddit rules), distribution, sender
    models/              organizations, users, reddit_accounts, tenant_configs,
                         leads, lead_assignments, replies, subreddit_rules
    workers/             Celery app + Beat schedule (per-tenant poll intervals)
  alembic/               migrations
  tests/                 end-to-end flow, tenant isolation, member permissions
frontend/                Next.js app with /admin and /member portals (gated by middleware.ts)
nginx/                   reverse proxy (/api -> FastAPI, / -> Next.js)
docker-compose.yml       postgres, redis, api, worker, beat, web, nginx
```

## Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

Open http://localhost and sign in with any email and an organization name. That account becomes the owner.

## Run locally without Docker

```bash
# backend (needs Postgres + Redis running, or point DATABASE_URL at sqlite+aiosqlite)
cd backend
python -m venv .venv && .venv/Scripts/activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload                       # http://localhost:8000/docs

# tests (SQLite, no services needed)
pytest

# frontend
cd frontend
npm install
npm run dev                                         # http://localhost:3000, proxies /api to :8000
```

## Try the flow

1. **Niche config**: describe what you sell, click *Suggest configuration*, then save.
2. **Overview**: click *Run pipeline now*. The mock Scout returns sample posts, the Classifier scores them, and the Drafter queues replies.
3. **Review queue**: edit a draft, then approve (the mock posts it) or reject it.
4. **Team**: invite a member. They sign in with their email and see only their assigned leads and drafts.
5. **API approval**: fill in your details, click *Save & check now*, fix what fails, follow the steps, then copy the generated request into Reddit's form. It defaults to the free, non-commercial tier.

## Plugging in the real APIs later

| What | Where |
|---|---|
| Reddit Data API | Add a `LiveRedditClient` that implements `integrations/reddit/base.py:RedditClient`, and return it from `get_reddit_client()` when `REDDIT_MODE=live`. |
| Reddit OAuth login | Fill in the `auth.py` `/reddit/login` and `/reddit/callback` stubs. Store tokens with `core/security.encrypt_token`. |
| OpenAI Agents SDK | Replace each agent's `run()` with an SDK `Agent`, and use the pydantic models in `agents/schemas.py` as `output_type`. |
| Migrations | `alembic revision --autogenerate -m "initial"` then `alembic upgrade head`. Set `DB_AUTO_CREATE=false` in production. |

## Safeguards already in the code

- Every draft starts as `pending_review`. Only `/replies/{id}/approve` sends it, and the approving user is recorded.
- The first contact is always a public comment. DM sending exists in the sender but is never drafted automatically.
- A subreddit rule that disallows commercial replies stops a draft from being created.
- Every query is scoped by the `org_id` from the JWT. `test_tenant_isolation` covers this.
