# AgentFlow AI deployment

This project deploys the existing Next.js frontend to Vercel and the FastAPI
backend to Render. PostgreSQL is supplied separately as a managed database.
This guide prepares the application; it does not create or deploy external
services.

## Render backend

The root-level `render.yaml` describes one Python web service. In Render,
select the repository Blueprint and set the environment variables listed
below. The service uses:

- Build: `pip install -r backend/requirements.txt`
- Start: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`

`/health` reports application process health only. It deliberately does not
claim that the database or AI provider is reachable.

## PostgreSQL and migrations

Set `DATABASE_URL` to the managed PostgreSQL connection URL in the Render
service environment. Both `postgresql://` and legacy `postgres://` URLs are
accepted by the backend. PostgreSQL connectivity has not been validated until
the service is configured with a real reachable PostgreSQL instance.

From the repository root, install the backend dependencies and apply pending
migrations:

```sh
python -m pip install -r backend/requirements.txt
alembic -c alembic.ini upgrade head
```

Run the migration command as a release/pre-deploy step or once against the
configured database before sending application traffic. The initial migration
creates tables missing from the current SQLAlchemy metadata and leaves existing
tables and rows intact. It records the baseline in `alembic_version`; its
downgrade is intentionally a no-op because a baseline may adopt tables that
existed before Alembic. Back up a managed database using its provider's backup
facility before applying schema changes.

To inspect the configured migration history without changing the database:

```sh
alembic -c alembic.ini history
alembic -c alembic.ini heads
```

## Vercel frontend

Set the Vercel project root to `frontend` and use the standard Next.js build
command `npm run build`. Configure this public variable:

- `NEXT_PUBLIC_API_URL`: backend origin, such as `https://<render-service>.onrender.com`,
  or the full API prefix ending in `/api/v1`. The frontend adds `/api/v1` when
  only an origin is supplied.

Do not put backend secrets or the FreeLLMAPI key in Vercel variables prefixed
with `NEXT_PUBLIC_`.

## Backend environment variables

Set these in Render's service environment. Do not commit actual values.

| Variable | Required | Purpose |
| --- | --- | --- |
| `ENVIRONMENT` | Yes | Set to `production`; disables the development CORS defaults. |
| `WORKFLOW_AI_MODE` | Yes | Set to `live` in production. The `mock` mode is for explicit development use only. |
| `SECRET_KEY` | Yes | Private JWT signing key. Supply a strong generated value in Render. |
| `DATABASE_URL` | Yes | Managed PostgreSQL connection URL. |
| `CORS_ORIGINS` | Yes | Comma-separated exact frontend origin(s), e.g. `https://<your-vercel-domain>`. |
| `FREELLMAPI_BASE_URL` | For provider use | FreeLLMAPI OpenAI-compatible base URL, with or without `/v1`. |
| `FREELLMAPI_API_KEY` | For provider use | Private provider API key. |
| `FREELLMAPI_MODEL` | Optional | Provider model; defaults to `gpt-3.5-turbo`. |
| `FREELLMAPI_TEMPERATURE` | Optional | Provider sampling temperature; defaults to `0.7`. |
| `FREELLMAPI_MAX_TOKENS` | Optional | Provider output token limit; defaults to `1000`. |
| `PROJECT_NAME` | Optional | API title. |
| `API_V1_STR` | Optional | API prefix; defaults to `/api/v1`. |
| `ALGORITHM` | Optional | JWT algorithm; defaults to `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | JWT lifetime in minutes; defaults to seven days. |

In development, when `CORS_ORIGINS` is empty, localhost origins on ports 3000
and 3001 are allowed. In production, no origins are implicitly allowed; set
`CORS_ORIGINS` to the exact deployed frontend origin(s). Wildcard origins are
not configured by the application.

## Local run

Run commands from the repository root so Python can import `backend.app`:

```sh
python -m pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Supply local settings through environment variables or a local `.env` file.
The checked-in `.env.example` documents development settings; never replace an
existing `.env` containing local credentials or data.

## Deployment verification

After configuring services:

1. Confirm `GET https://<render-service>.onrender.com/health` returns HTTP 200
   and `{"status":"ok"}`.
2. Confirm the Render logs show the backend started with the configured port.
3. Confirm migrations completed successfully against the intended PostgreSQL
   database and that existing rows remain present.
4. Set `NEXT_PUBLIC_API_URL` in Vercel, build and deploy the frontend, then
   verify login and authenticated API requests from the deployed origin.
5. Confirm the deployed browser origin exactly matches an entry in
   `CORS_ORIGINS`.
6. If using FreeLLMAPI directly, verify provider credentials and endpoint from
   the deployed backend without logging the API key.

## Current provider integration note

`/agency/workflow/run` runs the Research, Strategy, Content, and QA steps through
the OpenAI-compatible FreeLLMAPI chat completion endpoint when
`WORKFLOW_AI_MODE=live`. Each step validates the JSON content against the
existing workflow fields. Missing credentials, provider errors, or malformed
responses return HTTP 503; the production path does not fall back to mock
results. In development, set `WORKFLOW_AI_MODE=mock` to opt into the existing
deterministic agents. Live AI use still requires valid provider credentials
and has not been verified against the external service.
