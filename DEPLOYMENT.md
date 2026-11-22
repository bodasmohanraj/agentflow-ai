# AgentFlow AI — Deployment Guide

## Overview
AgentFlow AI is an autonomous AI-powered digital agency platform built with:
- **Frontend**: Next.js 14 with Pages Router, TypeScript, Tailwind CSS
- **Backend**: FastAPI with Python, SQLAlchemy ORM, JWT authentication
- **Database**: SQLite (development) / PostgreSQL (production)
- **LLM**: FreeLLMAPI (OpenAI-compatible) provider abstraction
- **Agent Orchestration**: LangGraph StateGraph with Supervisor Agent

## Render Deployment

### Prerequisites
- Render account
- Managed PostgreSQL database
- GitHub repository connected

### Setup Steps

1. **Backend Service**
   - Root Directory: `/`
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - Node Version: `Node.js` (for frontend)

2. **Frontend Service**
   - Root Directory: `/frontend`
   - Build Command: `npm run build`
   - Publish Directory: `.next`
   - Node Version: `18.x`

3. **Environment Variables**

   **Backend (.env file in Render dashboard):**
   ```
   PROJECT_NAME=AgentFlow AI
   SECRET_KEY=your-secret-key-change-this-in-production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=604800
   
   DATABASE_URL=postgresql://user:password@db.host:5432/agentflow_db
   
   # FreeLLMAPI Configuration
   FREELLMAPI_BASE_URL=https://your-freellmapi-endpoint.com
   FREELLMAPI_API_KEY=your-freellmapi-key
   FREELLMAPI_MODEL=gpt-3.5-turbo
   FREELLMAPI_TEMPERATURE=0.7
   FREELLMAPI_MAX_TOKENS=1000
   
   # CORS Configuration
   CORS_ORIGINS=https://your-vercel-app.vercel.app,http://localhost:3001
   ```

   **Frontend (.env.example):**
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
   
   # Analytics Configuration
   NEXT_PUBLIC_ANALYTICS_ENABLED=true
   ```

4. **Health Check Endpoint**
   - URL: `https://your-service.onrender.com/health`
   - Expected: `{"status": "healthy"}` or HTTP 200

5. **Database Migration**
   - Run: `alembic upgrade head` after deploying backend
   - Ensure PostgreSQL managed database is configured before running migrations

6. **CORS Configuration**
   - Add allowed origins to backend `ALLOWED_ORIGINS` environment variable
   - Include both frontend and any API gateway URLs

7. **Rollback Procedure**
   - Use Render dashboard to revert to previous deployment
   - Or redeploy previous commit from GitHub
   - Database backups should be manually maintained

## Vercel Deployment

### Frontend Configuration

1. **vercel.json** (create in frontend root):
   ```json
   {
     "build": {
       "command": "npm run build",
       "outputDirectory": ".next"
     },
     "routes": {
       "/api/(.*)": "http://localhost:8000/api/$1"
     }
   }
   ```

2. **Environment Variables** (in Vercel dashboard):
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
   NEXT_PUBLIC_WS_URL=wss://your-backend.onrender.com/ws
   
   # FreeLLMAPI (if needed for client-side features)
   # FREELLMAPI_BASE_URL=
   # FREELLMAPI_API_KEY=
   ```

3. **Output**: `npm run build` produces `.next/` directory

## Local Development

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your credentials
uvicorn app.main:app --reload
# Server runs on http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env  # Edit with your credentials
npm run dev
# Server runs on http://localhost:3001
```

### Database Initialization
```bash
# Create tables
alembic upgrade head

# Or with SQLite directly
cd backend
python -c "from backend.app.models.models import Base; Base.metadata.create_all(bind=engine)"
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login with credentials
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/logout` - Logout and clear token

### Client Management
- `GET /api/v1/agency/clients` - List clients (requires auth)
- `POST /api/v1/agency/clients` - Create client (requires auth)
- `GET /api/v1/agency/clients/{id}` - Get client by ID

### Strategies
- `POST /api/v1/agency/strategies/generate` - Generate strategy for client
- `GET /api/v1/agency/strategies/` - List strategies (requires auth)
- `GET /api/v1/agency/strategies/{id}` - Get strategy by ID

### Analytics
- `GET /api/v1/analytics/summary` - KPI summary (requires auth)
- `GET /api/v1/analytics/kpis` - KPI details (requires auth)
- `GET /api/v1/analytics/strategies` - Strategy metrics (requires auth)

### Approvals
- `GET /api/v1/approvals/pending` - List pending approvals (requires auth)
- `POST /api/v1/approvals/{id}/approve` - Approve request (requires auth)
- `POST /api/v1/approvals/{id}/reject` - Reject request (requires auth)

## Security

### JWT Configuration
- Algorithm: HS256
- Token expiration: 7 days (604800 seconds)
- Secret key: Must be set via SECRET_KEY environment variable
- Never expose JWT secrets in frontend code or client-side storage

### CORS
- Development: Allow localhost:3001 and localhost:8000
- Production: Configure via CORS_ORIGINS environment variable
- Credentials: Support cookies and authorization headers

### Data Ownership
- All queries scope results to authenticated user
- Client ownership validated via user_id foreign key
- Strategies and executions belong to authenticated user's clients

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Verify DATABASE_URL format
   - Ensure PostgreSQL is running and accessible
   - Check alembic migration version

2. **LLM provider errors**
   - Validate FREELLMAPI_BASE_URL and FREELLMAPI_API_KEY
   - Ensure endpoint is reachable from deployment environment
   - Check token usage and cost tracking

3. **CORS errors**
   - Verify CORS_ORIGINS includes correct frontend URL
   - Ensure credentials are supported

4. **Authentication failures**
   - Check SECRET_KEY is consistent between .env and code
   - Verify JWT token format in Authorization header
   - Ensure user exists in database

### Logs
- Backend: Render dashboard logs or `tail -f logs.txt`
- Frontend: Vercel dashboard or `npm run dev` console
- Database: Alembic migration output

## License
AgentFlow AI - Proprietary software. All rights reserved.
