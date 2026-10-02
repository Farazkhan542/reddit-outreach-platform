# Reddit Lead Finder (prototype)

Finds Reddit posts where someone is asking for a product recommendation, scores how likely they are to buy, and drafts a helpful reply **for a person to review**.

**The app never writes to Reddit.** It doesn't post, comment, vote or send messages, and its Reddit client has no write methods. If a reviewer approves a draft, they copy it, post it themselves on reddit.com from their own account, then mark it as posted in the app.

> **Status: personal prototype for development and testing.** No users or customers, not monetized.
> Reddit and the AI model are **mocked** (`REDDIT_MODE=mock`, `LLM_MODE=mock`): the app uses canned sample posts and heuristic agents, and makes no external API calls.
> If it ever becomes a commercial product, a separate commercial Reddit API access request will be filed first.

## How it uses Reddit

| | |
|---|---|
| Access | Read-only. OAuth scopes `identity read` |
| What it reads | New public posts in a small, fixed list of subreddits |
| Volume | About 1 request per minute |
| What it stores | Post title, body, author and permalink, for up to 90 days |
| Not done | No posting, voting or messaging. No model training on Reddit data. No resale or sharing |

## Flow

1. **Scout** reads new posts from the configured subreddits.
2. **Classifier** scores buying intent ("need a dining table under $800" scores high; "finished my living room" is ignored) and pulls out needs like budget and urgency.
3. **Subreddit rules check:** posts in subreddits that disallow commercial replies are skipped.
4. **Drafter** writes a reply based on that post's specific details. Drafts are not templated.
5. **Human review:** a person edits, approves or rejects each draft.
6. **Manual posting:** for an approved draft, *Copy reply & open post* copies the text and opens the thread. The person posts it themselves, then clicks *Mark as posted*.

## Layout

```
backend/                 FastAPI + SQLAlchemy (async) + Celery
  app/
    api/v1/              auth, org/team, config, leads, replies (review + mark-posted), pipeline/analytics, approval guide
    agents/              Niche Interpreter, Scout, Classifier, Drafter (mock implementations)
    integrations/reddit/ read-only RedditClient protocol + MockRedditClient
    services/            pipeline, compliance (subreddit rules), lead distribution, API-approval guide
    models/              organizations, users, reddit_accounts, tenant_configs, leads,
                         lead_assignments, replies, subreddit_rules, api_access_applications
    workers/             Celery app + Beat schedule (periodic polling)
  alembic/               migrations
  tests/                 end-to-end flow, read-only client, data isolation, permissions
frontend/                Next.js app with /admin and /member portals
nginx/                   reverse proxy (/api -> FastAPI, / -> Next.js)
docker-compose.yml       postgres, redis, api, worker, beat, web, nginx
```

The data model supports organizations with more than one reviewer, so that teams can be added later. Right now it's used by a single developer for testing.

## Run it locally (no Docker)

Windows, from the project folder:

```powershell
powershell -ExecutionPolicy Bypass -File dev.ps1
```

This uses SQLite and opens the backend (http://localhost:8000/docs) and the app (http://localhost:3000). Sign in with any email and an organization name.

Manual setup:

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
DATABASE_URL=sqlite+aiosqlite:///./dev.db DB_AUTO_CREATE=true uvicorn app.main:app --reload
pytest                                              # tests use SQLite, no services needed

cd frontend
npm install && npm run dev                          # proxies /api to :8000
```

## Run with Docker

```bash
cp .env.example .env
docker compose up --build                          # http://localhost
```

## Try it

1. **Niche config:** describe what you sell, click *Suggest configuration*, then save.
2. **Overview:** click *Run pipeline now* to scout, classify and draft against mock posts.
3. **Review queue:** edit and approve a draft, click *Copy reply & open post*, then *Mark as posted*.
4. **Team:** invite a reviewer. They see only the leads assigned to them.
5. **API approval:** a checklist and request-text generator for Reddit Data API access.

## When Reddit API access is approved

| What | Where |
|---|---|
| Reading posts | Add a `LiveRedditClient` that implements the read-only `integrations/reddit/base.py:RedditClient`, and return it when `REDDIT_MODE=live` |
| Reddit login | Fill in the `/auth/reddit/login` and `/callback` stubs in `api/v1/auth.py` (scopes `identity read`) |
| AI model | Replace each agent's `run()` with a real model call, and use the pydantic models in `agents/schemas.py` as structured output |
| Migrations | `alembic revision --autogenerate -m "initial"`, then `alembic upgrade head` |
