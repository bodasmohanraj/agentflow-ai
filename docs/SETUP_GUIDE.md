# Setup Guide: AgentFlow AI

## Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional for local dev)

## Backend Setup
1. Create virtual environment: \`python3 -m venv venv\`
2. Activate: \`source venv/bin/activate\`
3. Install dependencies: \`pip install -r backend/requirements.txt\`
4. Configure \`.env\` file.
5. Initialize database: \`PYTHONPATH=. python3 backend/app/main.py\` (Automatic on start)
6. Run server: \`uvicorn backend.app.main:app --reload\`

## Frontend Setup
1. Navigate to \`frontend/\`.
2. Install dependencies: \`npm install\`
3. Run development server: \`npm run dev\`

## Docker Setup
Run everything with: \`docker-compose up --build\`
