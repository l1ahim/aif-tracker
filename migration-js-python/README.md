# AIF Tracker - JavaScript Frontend + Python Backend Migration

This project migrates the existing Next.js application to a separated architecture:

- **Frontend**: React with Vite (JavaScript)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL (unchanged)

## Architecture Overview

```
┌─────────────────┐    HTTP/REST    ┌──────────────────┐
│   React + Vite  │ ──────────────> │   FastAPI       │
│   (Frontend)    │                 │   (Backend)     │
└─────────────────┘                 └──────────────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │   PostgreSQL     │
                                    │   (Database)     │
                                    └──────────────────┘
```

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Run the quick start script
./quick-start.sh

# Or manually with Docker Compose
cd docker
docker-compose up -d
```

### Option 2: Manual Setup

#### Backend Setup
```bash
cd backend
cp .env.example .env  # Edit with your API keys
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### Frontend Setup
```bash
cd frontend
cp .env.example .env  # Edit if needed
npm install
npm run dev  # Runs on http://localhost:5173
```

### Configuration

#### Required for Receipt Scanning
- **Gemini API**: Get key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Azure AI**: Get credentials from [Azure Portal](https://portal.azure.com)

#### Optional Services
- **Clerk**: For production authentication
- **Stripe**: For subscription management
- **SendGrid**: For email notifications

## Migration Progress

- [ ] Phase 1: Backend API Creation (Weeks 1-2)
- [ ] Phase 2: Background Jobs Migration (Weeks 3-4)
- [ ] Phase 3: Frontend Adaptation (Weeks 5-6)
- [ ] Phase 4: Authentication Integration (Week 7)
- [ ] Phase 5: Testing & Deployment (Weeks 8-10)

## Performance Benefits

- **Build Speed**: Vite builds 10-100x faster than Next.js
- **Runtime Performance**: No SSR overhead for dynamic data
- **Scalability**: Independent frontend/backend scaling
- **AI/ML**: Better Python libraries for financial processing

## Directory Structure

```
migration-js-python/
├── backend/           # Python FastAPI backend
├── frontend/          # React + Vite frontend
├── shared/           # Shared utilities and types
├── docker/           # Docker configuration
└── docs/             # Migration documentation
```
