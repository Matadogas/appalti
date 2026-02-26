# TriState Public Works Finder

Aggregates public construction bid opportunities from NY/NJ government portals.

## Setup

1. Copy `.env.example` to `.env` and fill in values:
   ```bash
   cp .env.example .env
   ```

2. Start services:
   ```bash
   docker-compose up -d
   ```

3. Run migrations:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

4. Access:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Development

### Backend
```bash
# Enter backend container
docker-compose exec backend bash

# Run tests
pytest

# Run migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Format code
black .
ruff check .
```

### Frontend
```bash
# Enter frontend container
docker-compose exec frontend sh

# Install new package
npm install <package>
```

### Adding a New Scraper Source

1. Create new file in `backend/app/scrapers/sources/<source_name>.py`
2. Implement `BaseScraper` interface
3. Add to `backend/app/scrapers/registry.py`
4. See existing scrapers for examples

## Architecture

- **Backend**: FastAPI + PostgreSQL + Redis + Celery
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **Scrapers**: Plugin architecture with BaseScraper interface
- **AI Enrichment**: Anthropic Claude for summaries and tagging
- **Job Queue**: Celery with Redis broker for scheduled scrapes
