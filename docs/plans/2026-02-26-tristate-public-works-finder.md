# TriState Public Works Finder Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an MVP SaaS that aggregates public construction bid opportunities from NY/NJ government portals, normalizes data, and provides searchable UI + API + email alerts.

**Architecture:** Microservices architecture with FastAPI backend, Next.js frontend, PostgreSQL database, job queue for scraping, and AI enrichment pipeline. Each scraper is a plugin implementing BaseScraper interface.

**Tech Stack:** Python 3.11+, FastAPI, PostgreSQL, Redis, Next.js 14, TypeScript, Docker Compose, Anthropic Claude API

---

## Phase 1: Foundation & Infrastructure

### Task 1: Repository Structure

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/requirements-dev.txt`
- Create: `backend/pyproject.toml`
- Create: `frontend/package.json`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `README.md`

**Step 1: Create backend requirements**

Create `backend/requirements.txt`:
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
alembic==1.13.1
pydantic==2.5.3
pydantic-settings==2.1.0
redis==5.0.1
celery==5.3.6
httpx==0.26.0
beautifulsoup4==4.12.3
lxml==5.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
anthropic==0.18.0
python-dotenv==1.0.0
tenacity==8.2.3
structlog==24.1.0
```

**Step 2: Create backend dev requirements**

Create `backend/requirements-dev.txt`:
```txt
-r requirements.txt
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
httpx==0.26.0
faker==22.5.1
black==24.1.1
ruff==0.1.14
mypy==1.8.0
```

**Step 3: Create pyproject.toml**

Create `backend/pyproject.toml`:
```toml
[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

**Step 4: Create frontend package.json**

Create `frontend/package.json`:
```json
{
  "name": "tristate-public-works-finder-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "14.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.5",
    "date-fns": "^3.2.0",
    "react-hook-form": "^7.49.3",
    "zod": "^3.22.4",
    "@hookform/resolvers": "^3.3.4"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "autoprefixer": "^10.0.1",
    "postcss": "^8",
    "tailwindcss": "^3.3.0",
    "typescript": "^5"
  }
}
```

**Step 5: Create Docker Compose**

Create `docker-compose.yml`:
```yaml
version: '3.9'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: tristate
      POSTGRES_PASSWORD: tristate_dev
      POSTGRES_DB: tristate_bids
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-BASH", "pg_isready -U tristate"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://tristate:tristate_dev@postgres:5432/tristate_bids
      - REDIS_URL=redis://redis:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SECRET_KEY=${SECRET_KEY:-dev_secret_key_change_in_production}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.worker.celery_app worker --loglevel=info
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql://tristate:tristate_dev@postgres:5432/tristate_bids
      - REDIS_URL=redis://redis:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SECRET_KEY=${SECRET_KEY:-dev_secret_key_change_in_production}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  scheduler:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.worker.celery_app beat --loglevel=info
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql://tristate:tristate_dev@postgres:5432/tristate_bids
      - REDIS_URL=redis://redis:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SECRET_KEY=${SECRET_KEY:-dev_secret_key_change_in_production}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    command: npm run dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend

volumes:
  postgres_data:
```

**Step 6: Create .env.example**

Create `.env.example`:
```env
# Database
DATABASE_URL=postgresql://tristate:tristate_dev@postgres:5432/tristate_bids

# Redis
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your_secret_key_here_change_in_production

# AI
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Email (for production)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASSWORD=your_password
FROM_EMAIL=noreply@tristatebids.com

# App
APP_URL=http://localhost:3000
```

**Step 7: Create .gitignore**

Create `.gitignore`:
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/
.pytest_cache/
.mypy_cache/
.ruff_cache/
*.egg-info/
dist/
build/

# Node
node_modules/
.next/
out/
.npm
.yarn
*.log

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Database
*.db
*.sqlite
```

**Step 8: Create README**

Create `README.md`:
```markdown
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
```

**Step 9: Commit foundation**

```bash
git add .
git commit -m "chore: initialize repository structure and docker compose"
```

---

### Task 2: Backend Dockerfile

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/.dockerignore`

**Step 1: Create backend Dockerfile**

Create `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: Create .dockerignore**

Create `backend/.dockerignore`:
```dockerignore
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
venv
.venv
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis
.env
.env.local
*.db
*.sqlite
```

**Step 3: Commit Docker setup**

```bash
git add backend/Dockerfile backend/.dockerignore
git commit -m "chore: add backend Dockerfile and dockerignore"
```

---

### Task 3: Frontend Dockerfile

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/.dockerignore`

**Step 1: Create frontend Dockerfile**

Create `frontend/Dockerfile`:
```dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application
COPY . .

# Build application
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

**Step 2: Create .dockerignore**

Create `frontend/.dockerignore`:
```dockerignore
node_modules
.next
out
.git
.gitignore
*.log
.env
.env.local
.env.production
.env.development
README.md
```

**Step 3: Commit frontend Docker setup**

```bash
git add frontend/Dockerfile frontend/.dockerignore
git commit -m "chore: add frontend Dockerfile and dockerignore"
```

---

## Phase 2: Database Schema & Migrations

### Task 4: Database Models

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/database.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/tender.py`
- Create: `backend/app/models/source.py`
- Create: `backend/app/models/scrape_run.py`
- Create: `backend/app/models/user.py`

**Step 1: Create database connection**

Create `backend/app/__init__.py`:
```python
"""TriState Public Works Finder Backend Application."""
```

Create `backend/app/database.py`:
```python
"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 2: Create config module**

Create `backend/app/config.py`:
```python
"""Application configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ANTHROPIC_API_KEY: str

    # JWT settings
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    # Email settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@tristatebids.com"

    # App settings
    APP_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()
```

**Step 3: Create models __init__.py**

Create `backend/app/models/__init__.py`:
```python
"""Database models."""
from app.database import Base
from app.models.tender import Tender
from app.models.source import Source
from app.models.scrape_run import ScrapeRun
from app.models.user import User

__all__ = ["Base", "Tender", "Source", "ScrapeRun", "User"]
```

**Step 4: Create tender model**

Create `backend/app/models/tender.py`:
```python
"""Tender model."""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Float,
    Enum,
    Integer,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class TenderStatus(str, enum.Enum):
    """Tender status enum."""

    ACTIVE = "active"
    CLOSED = "closed"
    AWARDED = "awarded"
    CANCELLED = "cancelled"


class TenderCategory(str, enum.Enum):
    """Tender category enum."""

    CONSTRUCTION = "construction"
    ENGINEERING = "engineering"
    FACILITIES = "facilities"
    OTHER = "other"


class Tender(Base):
    """Tender model representing a public works opportunity."""

    __tablename__ = "tenders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)

    # Core fields
    source_url = Column(String(500), nullable=False)
    title = Column(String(500), nullable=False)
    description_text = Column(Text)

    # Location
    agency = Column(String(200))
    state = Column(String(2), nullable=False)  # NY or NJ
    city = Column(String(100))
    county = Column(String(100))

    # Classification
    category = Column(Enum(TenderCategory), default=TenderCategory.OTHER)
    status = Column(Enum(TenderStatus), default=TenderStatus.ACTIVE)

    # Dates & Budget
    publish_date = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    budget_amount = Column(Float)
    currency = Column(String(3), default="USD")

    # Documents & Contact
    documents = Column(JSONB, default=list)  # [{"name": str, "url": str, "size": int}]
    contact = Column(JSONB)  # {"name": str, "email": str, "phone": str}

    # Deduplication
    fingerprint = Column(String(64), unique=True, nullable=False, index=True)

    # AI Enrichment
    ai_summary = Column(Text)
    ai_trade_tags = Column(JSONB, default=list)  # ["electrical", "plumbing", ...]
    ai_requirements = Column(JSONB)  # {"bid_bond": bool, "pre_bid_meeting": bool, ...}
    confidence = Column(Float)  # AI confidence score

    # Metadata
    scraped_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    raw_ref = Column(JSONB)  # Reference to raw scrape data

    # Relationships
    source = relationship("Source", back_populates="tenders")

    def __repr__(self) -> str:
        return f"<Tender {self.title[:50]}>"
```

**Step 5: Create source model**

Create `backend/app/models/source.py`:
```python
"""Source model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Source(Base):
    """Source model representing a procurement portal."""

    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    state = Column(String(2), nullable=False)  # NY or NJ
    base_url = Column(String(500), nullable=False)
    scraper_class = Column(String(100), nullable=False)  # e.g., "NYCPassportScraper"

    active = Column(Boolean, default=True)
    config = Column(JSONB, default=dict)  # Scraper-specific config

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenders = relationship("Tender", back_populates="source")
    scrape_runs = relationship("ScrapeRun", back_populates="source")

    def __repr__(self) -> str:
        return f"<Source {self.name}>"
```

**Step 6: Create scrape_run model**

Create `backend/app/models/scrape_run.py`:
```python
"""Scrape run model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ScrapeRunStatus(str, enum.Enum):
    """Scrape run status enum."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class ScrapeRun(Base):
    """Scrape run model tracking scraper execution."""

    __tablename__ = "scrape_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)

    status = Column(Enum(ScrapeRunStatus), default=ScrapeRunStatus.PENDING)

    # Counts
    tenders_found = Column(Integer, default=0)
    tenders_new = Column(Integer, default=0)
    tenders_updated = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)

    # Execution details
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(String(1000))
    error_details = Column(JSONB)  # Stack trace, context, etc.

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    source = relationship("Source", back_populates="scrape_runs")

    def __repr__(self) -> str:
        return f"<ScrapeRun {self.source_id} {self.status}>"
```

**Step 7: Create user model**

Create `backend/app/models/user.py`:
```python
"""User model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    full_name = Column(String(200))
    company = Column(String(200))

    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<User {self.email}>"
```

**Step 8: Commit models**

```bash
git add backend/app/
git commit -m "feat: add database models for tenders, sources, scrape runs, and users"
```

---

### Task 5: Alembic Setup & Initial Migration

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/<timestamp>_initial_schema.py`

**Step 1: Initialize Alembic**

Run in backend directory:
```bash
cd backend
alembic init alembic
```

**Step 2: Configure alembic.ini**

Edit `backend/alembic.ini` - change line:
```ini
sqlalchemy.url = driver://user:pass@localhost/dbname
```

To:
```ini
# sqlalchemy.url = driver://user:pass@localhost/dbname
# URL is set in env.py from environment variable
```

**Step 3: Configure alembic env.py**

Create `backend/alembic/env.py`:
```python
"""Alembic environment configuration."""
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import Base
from app.models import Tender, Source, ScrapeRun, User
from app.config import settings

# this is the Alembic Config object
config = context.config

# Set database URL from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 4: Generate initial migration**

Run:
```bash
docker-compose exec backend alembic revision --autogenerate -m "initial schema"
```

Expected: Migration file created in `backend/alembic/versions/`

**Step 5: Run migration**

```bash
docker-compose exec backend alembic upgrade head
```

Expected: Tables created in database

**Step 6: Verify migration**

```bash
docker-compose exec postgres psql -U tristate -d tristate_bids -c "\dt"
```

Expected output should list: `tenders`, `sources`, `scrape_runs`, `users`

**Step 7: Commit migrations**

```bash
git add backend/alembic/
git commit -m "feat: add initial database migration"
```

---

## Phase 3: Scraper Framework

### Task 6: Base Scraper Interface

**Files:**
- Create: `backend/app/scrapers/__init__.py`
- Create: `backend/app/scrapers/base.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/tender.py`

**Step 1: Write test for BaseScraper**

Create `backend/tests/__init__.py`:
```python
"""Tests package."""
```

Create `backend/tests/test_scrapers/__init__.py`:
```python
"""Scraper tests."""
```

Create `backend/tests/test_scrapers/test_base.py`:
```python
"""Test base scraper."""
import pytest
from app.scrapers.base import BaseScraper
from app.schemas.tender import TenderCreate


class TestBaseScraper:
    """Test BaseScraper interface."""

    def test_base_scraper_is_abstract(self):
        """Test that BaseScraper cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseScraper()

    def test_subclass_must_implement_scrape(self):
        """Test that subclasses must implement scrape method."""

        class IncompleteScraper(BaseScraper):
            def get_source_name(self) -> str:
                return "Test"

        with pytest.raises(TypeError):
            IncompleteScraper()
```

**Step 2: Run test to verify it fails**

```bash
docker-compose exec backend pytest tests/test_scrapers/test_base.py -v
```

Expected: FAIL - module not found

**Step 3: Create tender schemas**

Create `backend/app/schemas/__init__.py`:
```python
"""Pydantic schemas."""
```

Create `backend/app/schemas/tender.py`:
```python
"""Tender schemas."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, HttpUrl, Field

from app.models.tender import TenderCategory, TenderStatus


class DocumentSchema(BaseModel):
    """Document attachment schema."""

    name: str
    url: str
    size: Optional[int] = None


class ContactSchema(BaseModel):
    """Contact information schema."""

    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class TenderCreate(BaseModel):
    """Schema for creating a tender."""

    source_url: str = Field(..., max_length=500)
    title: str = Field(..., max_length=500)
    description_text: Optional[str] = None

    agency: Optional[str] = Field(None, max_length=200)
    state: str = Field(..., pattern="^(NY|NJ)$")
    city: Optional[str] = Field(None, max_length=100)
    county: Optional[str] = Field(None, max_length=100)

    category: TenderCategory = TenderCategory.OTHER
    status: TenderStatus = TenderStatus.ACTIVE

    publish_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    budget_amount: Optional[float] = None
    currency: str = "USD"

    documents: List[DocumentSchema] = Field(default_factory=list)
    contact: Optional[ContactSchema] = None

    raw_ref: Optional[Dict[str, Any]] = None


class TenderResponse(BaseModel):
    """Schema for tender response."""

    id: UUID
    source_url: str
    title: str
    description_text: Optional[str]

    agency: Optional[str]
    state: str
    city: Optional[str]
    county: Optional[str]

    category: TenderCategory
    status: TenderStatus

    publish_date: Optional[datetime]
    due_date: Optional[datetime]
    budget_amount: Optional[float]
    currency: str

    documents: List[DocumentSchema]
    contact: Optional[ContactSchema]

    ai_summary: Optional[str]
    ai_trade_tags: List[str]
    ai_requirements: Optional[Dict[str, Any]]
    confidence: Optional[float]

    scraped_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

**Step 4: Create BaseScraper interface**

Create `backend/app/scrapers/__init__.py`:
```python
"""Scrapers package."""
```

Create `backend/app/scrapers/base.py`:
```python
"""Base scraper interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
import hashlib
import structlog

from app.schemas.tender import TenderCreate

logger = structlog.get_logger()


class BaseScraper(ABC):
    """Base class for all scrapers.

    Each scraper must implement:
    - get_source_name(): Return the unique source name
    - scrape(): Execute scraping and return list of tenders
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize scraper with optional config."""
        self.config = config or {}
        self.logger = logger.bind(scraper=self.get_source_name())

    @abstractmethod
    def get_source_name(self) -> str:
        """Return unique source name (e.g., 'nyc_passport')."""
        pass

    @abstractmethod
    async def scrape(self) -> List[TenderCreate]:
        """Execute scraping and return tender data.

        Returns:
            List of TenderCreate objects

        Raises:
            Exception: If scraping fails
        """
        pass

    def generate_fingerprint(self, tender: TenderCreate) -> str:
        """Generate unique fingerprint for deduplication.

        Uses source_url + title + publish_date to create stable hash.
        """
        components = [
            tender.source_url,
            tender.title,
            str(tender.publish_date) if tender.publish_date else "",
        ]
        content = "|".join(components).encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    def log_info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, **kwargs)

    def log_error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, **kwargs)
```

**Step 5: Run tests to verify they pass**

```bash
docker-compose exec backend pytest tests/test_scrapers/test_base.py -v
```

Expected: PASS

**Step 6: Commit scraper framework**

```bash
git add backend/app/scrapers/ backend/app/schemas/ backend/tests/
git commit -m "feat: add base scraper interface and tender schemas"
```

---

### Task 7: Scraper Registry

**Files:**
- Create: `backend/app/scrapers/registry.py`
- Create: `backend/tests/test_scrapers/test_registry.py`

**Step 1: Write test for registry**

Create `backend/tests/test_scrapers/test_registry.py`:
```python
"""Test scraper registry."""
import pytest
from app.scrapers.registry import ScraperRegistry
from app.scrapers.base import BaseScraper


class TestScraperRegistry:
    """Test scraper registry."""

    def test_register_scraper(self):
        """Test registering a scraper."""
        registry = ScraperRegistry()

        class TestScraper(BaseScraper):
            def get_source_name(self) -> str:
                return "test_source"

            async def scrape(self):
                return []

        registry.register("test_source", TestScraper)
        assert "test_source" in registry.list_scrapers()

    def test_get_scraper(self):
        """Test retrieving a scraper."""
        registry = ScraperRegistry()

        class TestScraper(BaseScraper):
            def get_source_name(self) -> str:
                return "test_source"

            async def scrape(self):
                return []

        registry.register("test_source", TestScraper)
        scraper_class = registry.get_scraper("test_source")
        assert scraper_class == TestScraper

    def test_get_nonexistent_scraper(self):
        """Test getting scraper that doesn't exist."""
        registry = ScraperRegistry()
        with pytest.raises(KeyError):
            registry.get_scraper("nonexistent")
```

**Step 2: Run test to verify it fails**

```bash
docker-compose exec backend pytest tests/test_scrapers/test_registry.py -v
```

Expected: FAIL - module not found

**Step 3: Create scraper registry**

Create `backend/app/scrapers/registry.py`:
```python
"""Scraper registry for managing available scrapers."""
from typing import Dict, Type, List
import structlog

from app.scrapers.base import BaseScraper

logger = structlog.get_logger()


class ScraperRegistry:
    """Registry for managing scraper classes."""

    def __init__(self):
        """Initialize registry."""
        self._scrapers: Dict[str, Type[BaseScraper]] = {}

    def register(self, name: str, scraper_class: Type[BaseScraper]) -> None:
        """Register a scraper class.

        Args:
            name: Unique identifier for the scraper
            scraper_class: Scraper class (not instance)
        """
        self._scrapers[name] = scraper_class
        logger.info(f"Registered scraper: {name}")

    def get_scraper(self, name: str) -> Type[BaseScraper]:
        """Get scraper class by name.

        Args:
            name: Scraper identifier

        Returns:
            Scraper class

        Raises:
            KeyError: If scraper not found
        """
        if name not in self._scrapers:
            raise KeyError(f"Scraper '{name}' not found in registry")
        return self._scrapers[name]

    def list_scrapers(self) -> List[str]:
        """List all registered scraper names."""
        return list(self._scrapers.keys())

    def create_scraper(self, name: str, config: dict = None) -> BaseScraper:
        """Create scraper instance.

        Args:
            name: Scraper identifier
            config: Optional configuration dict

        Returns:
            Scraper instance
        """
        scraper_class = self.get_scraper(name)
        return scraper_class(config=config)


# Global registry instance
registry = ScraperRegistry()
```

**Step 4: Run tests to verify they pass**

```bash
docker-compose exec backend pytest tests/test_scrapers/test_registry.py -v
```

Expected: PASS

**Step 5: Commit registry**

```bash
git add backend/app/scrapers/registry.py backend/tests/test_scrapers/test_registry.py
git commit -m "feat: add scraper registry for managing scraper plugins"
```

---

## Phase 4: NYC PASSPort Scraper (First Source)

### Task 8: NYC PASSPort Scraper Implementation

**Files:**
- Create: `backend/app/scrapers/sources/__init__.py`
- Create: `backend/app/scrapers/sources/nyc_passport.py`
- Create: `backend/tests/test_scrapers/test_nyc_passport.py`

**Step 1: Write test for NYC PASSPort scraper**

Create `backend/tests/test_scrapers/test_nyc_passport.py`:
```python
"""Test NYC PASSPort scraper."""
import pytest
from app.scrapers.sources.nyc_passport import NYCPassportScraper


class TestNYCPassportScraper:
    """Test NYC PASSPort scraper."""

    def test_get_source_name(self):
        """Test source name."""
        scraper = NYCPassportScraper()
        assert scraper.get_source_name() == "nyc_passport"

    @pytest.mark.asyncio
    async def test_scrape_returns_list(self):
        """Test scrape returns list of tenders."""
        scraper = NYCPassportScraper()
        tenders = await scraper.scrape()
        assert isinstance(tenders, list)

    @pytest.mark.asyncio
    async def test_scraped_tenders_have_required_fields(self):
        """Test scraped tenders have required fields."""
        scraper = NYCPassportScraper()
        tenders = await scraper.scrape()

        if len(tenders) > 0:
            tender = tenders[0]
            assert tender.source_url
            assert tender.title
            assert tender.state == "NY"
            assert tender.city == "New York"
```

**Step 2: Run test to verify it fails**

```bash
docker-compose exec backend pytest tests/test_scrapers/test_nyc_passport.py -v
```

Expected: FAIL - module not found

**Step 3: Create NYC PASSPort scraper**

Create `backend/app/scrapers/sources/__init__.py`:
```python
"""Source scrapers."""
```

Create `backend/app/scrapers/sources/nyc_passport.py`:
```python
"""NYC PASSPort scraper.

Scrapes public RFx opportunities from NYC PASSPort portal.
Base URL: https://www1.nyc.gov/site/mocs/public-rfx/public-rfx.page
"""
from typing import List, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import structlog

from app.scrapers.base import BaseScraper
from app.schemas.tender import TenderCreate, DocumentSchema, ContactSchema
from app.models.tender import TenderCategory, TenderStatus

logger = structlog.get_logger()


class NYCPassportScraper(BaseScraper):
    """Scraper for NYC PASSPort public opportunities."""

    BASE_URL = "https://www1.nyc.gov/site/mocs/public-rfx/public-rfx.page"

    # Mapping of keywords to categories
    CATEGORY_KEYWORDS = {
        TenderCategory.CONSTRUCTION: [
            "construction", "building", "renovation", "infrastructure",
            "roadway", "bridge", "site work", "demolition"
        ],
        TenderCategory.ENGINEERING: [
            "engineering", "design", "architectural", "survey",
            "geotechnical", "structural"
        ],
        TenderCategory.FACILITIES: [
            "facilities", "maintenance", "repair", "janitorial",
            "hvac", "plumbing", "electrical"
        ],
    }

    def get_source_name(self) -> str:
        """Return source name."""
        return "nyc_passport"

    async def scrape(self) -> List[TenderCreate]:
        """Scrape NYC PASSPort opportunities.

        Returns:
            List of TenderCreate objects
        """
        self.log_info("Starting NYC PASSPort scrape")
        tenders = []

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                # Fetch the page
                response = await client.get(self.BASE_URL)
                response.raise_for_status()

                # Parse HTML
                soup = BeautifulSoup(response.text, "lxml")

                # Find tender listings
                # Note: Actual selectors will need to be updated based on real page structure
                tender_items = soup.select(".rfx-listing-item") or soup.select("tr.rfx-row")

                if not tender_items:
                    self.log_info("No tender items found - checking alternative selectors")
                    # Try alternative structure
                    tender_items = soup.select("div[class*='opportunity']") or []

                self.log_info(f"Found {len(tender_items)} tender items")

                for item in tender_items:
                    try:
                        tender = await self._parse_tender_item(item, client)
                        if tender:
                            tenders.append(tender)
                    except Exception as e:
                        self.log_error(f"Error parsing tender item: {str(e)}")
                        continue

            self.log_info(f"Scraped {len(tenders)} tenders")
            return tenders

        except Exception as e:
            self.log_error(f"Scraping failed: {str(e)}")
            raise

    async def _parse_tender_item(
        self, item: BeautifulSoup, client: httpx.AsyncClient
    ) -> Optional[TenderCreate]:
        """Parse a single tender item.

        Args:
            item: BeautifulSoup element containing tender data
            client: HTTP client for fetching detail pages

        Returns:
            TenderCreate object or None if parsing fails
        """
        try:
            # Extract title and URL
            title_elem = item.select_one("a.rfx-title") or item.select_one("td.title a")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            url = title_elem.get("href", "")

            # Make URL absolute
            if url and not url.startswith("http"):
                url = f"https://www1.nyc.gov{url}"

            if not url:
                return None

            # Extract agency
            agency_elem = item.select_one(".agency") or item.select_one("td.agency")
            agency = agency_elem.get_text(strip=True) if agency_elem else "NYC PASSPort"

            # Extract due date
            due_date_elem = item.select_one(".due-date") or item.select_one("td.due-date")
            due_date = self._parse_date(
                due_date_elem.get_text(strip=True) if due_date_elem else None
            )

            # Extract description
            desc_elem = item.select_one(".description") or item.select_one("td.description")
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            # Determine category from title and description
            category = self._categorize_tender(title, description)

            # Create tender object
            tender = TenderCreate(
                source_url=url,
                title=title,
                description_text=description or None,
                agency=agency,
                state="NY",
                city="New York",
                category=category,
                status=TenderStatus.ACTIVE,
                due_date=due_date,
                documents=[],
                raw_ref={"html": str(item)[:1000]},  # Store first 1000 chars
            )

            return tender

        except Exception as e:
            self.log_error(f"Error parsing tender item: {str(e)}")
            return None

    def _categorize_tender(self, title: str, description: str) -> TenderCategory:
        """Categorize tender based on title and description.

        Args:
            title: Tender title
            description: Tender description

        Returns:
            TenderCategory enum value
        """
        text = f"{title} {description}".lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return category

        return TenderCategory.OTHER

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime.

        Args:
            date_str: Date string in various formats

        Returns:
            datetime object or None
        """
        if not date_str:
            return None

        # Try common date formats
        formats = [
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%Y-%m-%d",
            "%B %d, %Y",
            "%b %d, %Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None
```

**Step 4: Run tests**

```bash
docker-compose exec backend pytest tests/test_scrapers/test_nyc_passport.py -v
```

Expected: PASS (or WARNING if no live data - that's ok for now)

**Step 5: Register scraper**

Edit `backend/app/scrapers/registry.py` - add at end:
```python
# Import and register scrapers
from app.scrapers.sources.nyc_passport import NYCPassportScraper

registry.register("nyc_passport", NYCPassportScraper)
```

**Step 6: Commit NYC PASSPort scraper**

```bash
git add backend/app/scrapers/sources/ backend/tests/test_scrapers/test_nyc_passport.py backend/app/scrapers/registry.py
git commit -m "feat: add NYC PASSPort scraper with categorization"
```

---

### Task 9: Tender Service with Deduplication

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/tender_service.py`
- Create: `backend/tests/test_services/__init__.py`
- Create: `backend/tests/test_services/test_tender_service.py`

**Step 1: Write test for tender service**

Create `backend/tests/test_services/__init__.py`:
```python
"""Service tests."""
```

Create `backend/tests/test_services/test_tender_service.py`:
```python
"""Test tender service."""
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime

from app.services.tender_service import TenderService
from app.schemas.tender import TenderCreate
from app.models.tender import TenderCategory, TenderStatus


class TestTenderService:
    """Test TenderService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def service(self, mock_db):
        """Create tender service."""
        return TenderService(mock_db)

    @pytest.fixture
    def sample_tender_create(self):
        """Sample tender create data."""
        return TenderCreate(
            source_url="https://example.com/tender/123",
            title="Test Construction Project",
            description_text="Test description",
            agency="Test Agency",
            state="NY",
            city="New York",
            category=TenderCategory.CONSTRUCTION,
            status=TenderStatus.ACTIVE,
        )

    def test_generate_fingerprint(self, service, sample_tender_create):
        """Test fingerprint generation."""
        fp1 = service._generate_fingerprint(sample_tender_create)
        fp2 = service._generate_fingerprint(sample_tender_create)

        assert fp1 == fp2
        assert len(fp1) == 64  # SHA256 hex digest

    def test_create_or_update_new_tender(self, service, mock_db, sample_tender_create):
        """Test creating new tender."""
        source_id = uuid4()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.create_or_update_tender(sample_tender_create, source_id)

        assert result["action"] == "created"
        assert mock_db.add.called

    def test_create_or_update_existing_tender(self, service, mock_db, sample_tender_create):
        """Test updating existing tender."""
        source_id = uuid4()
        existing_tender = Mock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = existing_tender

        result = service.create_or_update_tender(sample_tender_create, source_id)

        assert result["action"] == "updated"
        assert mock_db.add.called
```

**Step 2: Run test to verify it fails**

```bash
docker-compose exec backend pytest tests/test_services/test_tender_service.py -v
```

Expected: FAIL - module not found

**Step 3: Create tender service**

Create `backend/app/services/__init__.py`:
```python
"""Services package."""
```

Create `backend/app/services/tender_service.py`:
```python
"""Tender service for CRUD operations."""
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
import hashlib
from sqlalchemy.orm import Session
import structlog

from app.models.tender import Tender
from app.schemas.tender import TenderCreate
from app.models.tender import TenderStatus

logger = structlog.get_logger()


class TenderService:
    """Service for managing tenders."""

    def __init__(self, db: Session):
        """Initialize service."""
        self.db = db

    def _generate_fingerprint(self, tender: TenderCreate) -> str:
        """Generate unique fingerprint for deduplication.

        Uses source_url + title + publish_date to create stable hash.
        """
        components = [
            tender.source_url,
            tender.title,
            str(tender.publish_date) if tender.publish_date else "",
        ]
        content = "|".join(components).encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    def create_or_update_tender(
        self, tender_data: TenderCreate, source_id: UUID
    ) -> Dict[str, Any]:
        """Create new tender or update existing one based on fingerprint.

        Args:
            tender_data: Tender data
            source_id: Source UUID

        Returns:
            Dict with action ("created" or "updated") and tender object
        """
        fingerprint = self._generate_fingerprint(tender_data)

        # Check if tender exists
        existing = self.db.query(Tender).filter_by(fingerprint=fingerprint).first()

        if existing:
            # Update existing tender
            logger.info(f"Updating existing tender: {existing.id}")

            for field, value in tender_data.model_dump().items():
                if value is not None and field != "raw_ref":  # Don't overwrite with None
                    setattr(existing, field, value)

            existing.updated_at = datetime.utcnow()
            existing.scraped_at = datetime.utcnow()

            self.db.add(existing)
            self.db.commit()
            self.db.refresh(existing)

            return {"action": "updated", "tender": existing}
        else:
            # Create new tender
            logger.info(f"Creating new tender: {tender_data.title}")

            tender = Tender(
                source_id=source_id,
                fingerprint=fingerprint,
                **tender_data.model_dump(),
            )

            self.db.add(tender)
            self.db.commit()
            self.db.refresh(tender)

            return {"action": "created", "tender": tender}

    def get_tender(self, tender_id: UUID) -> Optional[Tender]:
        """Get tender by ID."""
        return self.db.query(Tender).filter(Tender.id == tender_id).first()

    def list_tenders(
        self,
        skip: int = 0,
        limit: int = 100,
        state: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[TenderStatus] = None,
    ) -> List[Tender]:
        """List tenders with filters."""
        query = self.db.query(Tender)

        if state:
            query = query.filter(Tender.state == state)
        if category:
            query = query.filter(Tender.category == category)
        if status:
            query = query.filter(Tender.status == status)

        query = query.order_by(Tender.scraped_at.desc())
        return query.offset(skip).limit(limit).all()

    def count_tenders(
        self,
        state: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[TenderStatus] = None,
    ) -> int:
        """Count tenders with filters."""
        query = self.db.query(Tender)

        if state:
            query = query.filter(Tender.state == state)
        if category:
            query = query.filter(Tender.category == category)
        if status:
            query = query.filter(Tender.status == status)

        return query.count()
```

**Step 4: Run tests**

```bash
docker-compose exec backend pytest tests/test_services/test_tender_service.py -v
```

Expected: PASS

**Step 5: Commit tender service**

```bash
git add backend/app/services/ backend/tests/test_services/
git commit -m "feat: add tender service with deduplication via fingerprinting"
```

---

### Task 10: Scraper Executor & Job Queue

**Files:**
- Create: `backend/app/worker/__init__.py`
- Create: `backend/app/worker/celery_app.py`
- Create: `backend/app/worker/tasks.py`
- Create: `backend/app/services/scrape_service.py`

**Step 1: Create Celery app**

Create `backend/app/worker/__init__.py`:
```python
"""Worker package."""
```

Create `backend/app/worker/celery_app.py`:
```python
"""Celery app configuration."""
from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "tristate_bids",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/New_York",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Schedule daily scrapes at 6 AM EST
celery_app.conf.beat_schedule = {
    "run-daily-scrapes": {
        "task": "app.worker.tasks.run_all_scrapers",
        "schedule": crontab(hour=6, minute=0),
    },
}
```

**Step 2: Create scrape service**

Create `backend/app/services/scrape_service.py`:
```python
"""Scrape service for managing scrape runs."""
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
import structlog

from app.models.source import Source
from app.models.scrape_run import ScrapeRun, ScrapeRunStatus
from app.scrapers.registry import registry
from app.services.tender_service import TenderService

logger = structlog.get_logger()


class ScrapeService:
    """Service for managing scrape operations."""

    def __init__(self, db: Session):
        """Initialize service."""
        self.db = db
        self.tender_service = TenderService(db)

    async def execute_scrape(self, source_id: UUID) -> Dict[str, Any]:
        """Execute scrape for a specific source.

        Args:
            source_id: Source UUID

        Returns:
            Dict with scrape results
        """
        # Get source
        source = self.db.query(Source).filter(Source.id == source_id).first()
        if not source:
            raise ValueError(f"Source {source_id} not found")

        if not source.active:
            logger.info(f"Source {source.name} is inactive, skipping")
            return {"status": "skipped", "reason": "inactive"}

        # Create scrape run
        scrape_run = ScrapeRun(
            source_id=source_id,
            status=ScrapeRunStatus.RUNNING,
            started_at=datetime.utcnow(),
        )
        self.db.add(scrape_run)
        self.db.commit()

        try:
            # Get scraper
            scraper = registry.create_scraper(source.scraper_class, source.config)

            # Execute scrape
            logger.info(f"Starting scrape for {source.name}")
            tenders = await scraper.scrape()

            # Process tenders
            new_count = 0
            updated_count = 0

            for tender_data in tenders:
                result = self.tender_service.create_or_update_tender(
                    tender_data, source_id
                )
                if result["action"] == "created":
                    new_count += 1
                else:
                    updated_count += 1

            # Update scrape run
            scrape_run.status = ScrapeRunStatus.SUCCESS
            scrape_run.completed_at = datetime.utcnow()
            scrape_run.tenders_found = len(tenders)
            scrape_run.tenders_new = new_count
            scrape_run.tenders_updated = updated_count

            self.db.commit()

            logger.info(
                f"Scrape complete for {source.name}: "
                f"{new_count} new, {updated_count} updated"
            )

            return {
                "status": "success",
                "source": source.name,
                "tenders_found": len(tenders),
                "tenders_new": new_count,
                "tenders_updated": updated_count,
            }

        except Exception as e:
            logger.error(f"Scrape failed for {source.name}: {str(e)}")

            scrape_run.status = ScrapeRunStatus.FAILED
            scrape_run.completed_at = datetime.utcnow()
            scrape_run.error_message = str(e)[:1000]
            scrape_run.errors_count = 1

            self.db.commit()

            return {
                "status": "failed",
                "source": source.name,
                "error": str(e),
            }

    def get_active_sources(self) -> List[Source]:
        """Get all active sources."""
        return self.db.query(Source).filter(Source.active == True).all()

    def get_recent_scrape_runs(self, limit: int = 50) -> List[ScrapeRun]:
        """Get recent scrape runs."""
        return (
            self.db.query(ScrapeRun)
            .order_by(ScrapeRun.created_at.desc())
            .limit(limit)
            .all()
        )
```

**Step 3: Create Celery tasks**

Create `backend/app/worker/tasks.py`:
```python
"""Celery tasks."""
import asyncio
from typing import List
from uuid import UUID
import structlog

from app.worker.celery_app import celery_app
from app.database import SessionLocal
from app.services.scrape_service import ScrapeService

logger = structlog.get_logger()


@celery_app.task(name="app.worker.tasks.scrape_source")
def scrape_source(source_id: str) -> dict:
    """Scrape a specific source.

    Args:
        source_id: Source UUID as string

    Returns:
        Dict with scrape results
    """
    db = SessionLocal()
    try:
        service = ScrapeService(db)

        # Run async scrape in sync context
        result = asyncio.run(service.execute_scrape(UUID(source_id)))

        return result
    finally:
        db.close()


@celery_app.task(name="app.worker.tasks.run_all_scrapers")
def run_all_scrapers() -> dict:
    """Run all active scrapers.

    Returns:
        Dict with results for all scrapers
    """
    logger.info("Starting scheduled scrape for all sources")

    db = SessionLocal()
    try:
        service = ScrapeService(db)
        sources = service.get_active_sources()

        results = []
        for source in sources:
            logger.info(f"Queuing scrape for {source.name}")
            result = scrape_source.delay(str(source.id))
            results.append({
                "source": source.name,
                "task_id": result.id,
            })

        return {
            "status": "queued",
            "sources_queued": len(results),
            "tasks": results,
        }
    finally:
        db.close()
```

**Step 4: Commit worker setup**

```bash
git add backend/app/worker/ backend/app/services/scrape_service.py
git commit -m "feat: add Celery worker with scheduled scraping tasks"
```

---

## Phase 5: Basic FastAPI Endpoints

### Task 11: FastAPI Application Setup

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/v1/__init__.py`
- Create: `backend/app/api/v1/tenders.py`

**Step 1: Create FastAPI app**

Create `backend/app/main.py`:
```python
"""FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.config import settings
from app.api.v1 import tenders

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()

app = FastAPI(
    title="TriState Public Works Finder API",
    description="API for aggregating NY/NJ public construction bids",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tenders.router, prefix="/api/v1", tags=["tenders"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "TriState Public Works Finder API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Step 2: Create tenders API router**

Create `backend/app/api/__init__.py`:
```python
"""API package."""
```

Create `backend/app/api/v1/__init__.py`:
```python
"""API v1 package."""
```

Create `backend/app/api/v1/tenders.py`:
```python
"""Tenders API endpoints."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.tender import TenderResponse
from app.services.tender_service import TenderService
from app.models.tender import TenderStatus, TenderCategory

router = APIRouter()


@router.get("/tenders", response_model=List[TenderResponse])
async def list_tenders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    state: Optional[str] = Query(None, pattern="^(NY|NJ)$"),
    category: Optional[TenderCategory] = None,
    status: Optional[TenderStatus] = None,
    db: Session = Depends(get_db),
):
    """List tenders with optional filters.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        state: Filter by state (NY or NJ)
        category: Filter by category
        status: Filter by status
        db: Database session

    Returns:
        List of tenders
    """
    service = TenderService(db)
    tenders = service.list_tenders(
        skip=skip,
        limit=limit,
        state=state,
        category=category,
        status=status,
    )
    return tenders


@router.get("/tenders/count")
async def count_tenders(
    state: Optional[str] = Query(None, pattern="^(NY|NJ)$"),
    category: Optional[TenderCategory] = None,
    status: Optional[TenderStatus] = None,
    db: Session = Depends(get_db),
):
    """Count tenders with optional filters.

    Args:
        state: Filter by state (NY or NJ)
        category: Filter by category
        status: Filter by status
        db: Database session

    Returns:
        Count of matching tenders
    """
    service = TenderService(db)
    count = service.count_tenders(
        state=state,
        category=category,
        status=status,
    )
    return {"count": count}


@router.get("/tenders/{tender_id}", response_model=TenderResponse)
async def get_tender(
    tender_id: UUID,
    db: Session = Depends(get_db),
):
    """Get tender by ID.

    Args:
        tender_id: Tender UUID
        db: Database session

    Returns:
        Tender details

    Raises:
        HTTPException: If tender not found
    """
    service = TenderService(db)
    tender = service.get_tender(tender_id)

    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    return tender
```

**Step 3: Test API locally**

```bash
docker-compose up -d backend
```

Then visit: http://localhost:8000/docs

Expected: Swagger UI with API documentation

**Step 4: Test health endpoint**

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"healthy"}`

**Step 5: Commit API**

```bash
git add backend/app/main.py backend/app/api/
git commit -m "feat: add FastAPI application with tenders endpoints"
```

---

## Phase 6: Database Seed & First Scrape

### Task 12: Seed NYC PASSPort Source

**Files:**
- Create: `backend/scripts/__init__.py`
- Create: `backend/scripts/seed_sources.py`

**Step 1: Create seed script**

Create `backend/scripts/__init__.py`:
```python
"""Scripts package."""
```

Create `backend/scripts/seed_sources.py`:
```python
"""Seed initial sources into database."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models.source import Source


def seed_sources():
    """Seed initial sources."""
    db = SessionLocal()

    try:
        sources = [
            {
                "name": "NYC PASSPort",
                "state": "NY",
                "base_url": "https://www1.nyc.gov/site/mocs/public-rfx/public-rfx.page",
                "scraper_class": "nyc_passport",
                "active": True,
                "config": {},
            },
        ]

        for source_data in sources:
            # Check if source exists
            existing = (
                db.query(Source)
                .filter(Source.name == source_data["name"])
                .first()
            )

            if existing:
                print(f"Source '{source_data['name']}' already exists")
                continue

            source = Source(**source_data)
            db.add(source)
            print(f"Added source: {source_data['name']}")

        db.commit()
        print("✅ Sources seeded successfully")

    except Exception as e:
        print(f"❌ Error seeding sources: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_sources()
```

**Step 2: Run seed script**

```bash
docker-compose exec backend python scripts/seed_sources.py
```

Expected: "✅ Sources seeded successfully"

**Step 3: Verify in database**

```bash
docker-compose exec postgres psql -U tristate -d tristate_bids -c "SELECT id, name, state, active FROM sources;"
```

Expected: NYC PASSPort source listed

**Step 4: Commit seed script**

```bash
git add backend/scripts/
git commit -m "feat: add database seeding script for sources"
```

---

### Task 13: Run First Scrape

**Files:**
- No new files

**Step 1: Trigger manual scrape**

Create a simple admin endpoint for triggering scrapes:

Create `backend/app/api/v1/admin.py`:
```python
"""Admin API endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.worker.tasks import scrape_source
from app.services.scrape_service import ScrapeService

router = APIRouter()


@router.post("/admin/scrape/{source_id}")
async def trigger_scrape(
    source_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger scrape for a specific source.

    Args:
        source_id: Source UUID
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Status message
    """
    # Queue scrape task
    task = scrape_source.delay(str(source_id))

    return {
        "status": "queued",
        "task_id": task.id,
        "message": f"Scrape queued for source {source_id}",
    }


@router.get("/admin/scrape-runs")
async def list_scrape_runs(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List recent scrape runs.

    Args:
        limit: Maximum number of runs to return
        db: Database session

    Returns:
        List of scrape runs
    """
    service = ScrapeService(db)
    runs = service.get_recent_scrape_runs(limit=limit)

    return {
        "runs": [
            {
                "id": str(run.id),
                "source_id": str(run.source_id),
                "status": run.status.value,
                "tenders_found": run.tenders_found,
                "tenders_new": run.tenders_new,
                "tenders_updated": run.tenders_updated,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "error_message": run.error_message,
            }
            for run in runs
        ]
    }
```

**Step 2: Add admin router to main app**

Edit `backend/app/main.py` - add after imports:
```python
from app.api.v1 import admin

# ... existing code ...

# Add after tenders router
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
```

**Step 3: Restart backend**

```bash
docker-compose restart backend
```

**Step 4: Get source ID**

```bash
docker-compose exec postgres psql -U tristate -d tristate_bids -c "SELECT id, name FROM sources WHERE name = 'NYC PASSPort';"
```

Copy the UUID.

**Step 5: Trigger scrape via API**

Replace `<SOURCE_ID>` with the actual UUID:
```bash
curl -X POST http://localhost:8000/api/v1/admin/scrape/<SOURCE_ID>
```

Expected: `{"status":"queued","task_id":"...","message":"Scrape queued for source ..."}`

**Step 6: Check scrape status**

```bash
curl http://localhost:8000/api/v1/admin/scrape-runs
```

Expected: List of scrape runs with status

**Step 7: Verify tenders were created**

```bash
curl http://localhost:8000/api/v1/tenders/count
```

Expected: `{"count": N}` where N > 0

**Step 8: Commit admin endpoints**

```bash
git add backend/app/api/v1/admin.py backend/app/main.py
git commit -m "feat: add admin endpoints for triggering scrapes and viewing runs"
```

---

## Phase 7: Frontend Feed Page

### Task 14: Next.js Setup

**Files:**
- Create: `frontend/tsconfig.json`
- Create: `frontend/next.config.js`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/src/app/layout.tsx`
- Create: `frontend/src/app/page.tsx`
- Create: `frontend/src/app/globals.css`

**Step 1: Initialize Next.js structure**

```bash
mkdir -p frontend/src/app
```

**Step 2: Create tsconfig.json**

Create `frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

**Step 3: Create Next.js config**

Create `frontend/next.config.js`:
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
}

module.exports = nextConfig
```

**Step 4: Create Tailwind config**

Create `frontend/tailwind.config.js`:
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

Create `frontend/postcss.config.js`:
```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

**Step 5: Create global CSS**

Create `frontend/src/app/globals.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --foreground-rgb: 0, 0, 0;
  --background-start-rgb: 214, 219, 220;
  --background-end-rgb: 255, 255, 255;
}

body {
  color: rgb(var(--foreground-rgb));
  background: linear-gradient(
      to bottom,
      transparent,
      rgb(var(--background-end-rgb))
    )
    rgb(var(--background-start-rgb));
}
```

**Step 6: Create layout**

Create `frontend/src/app/layout.tsx`:
```tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'TriState Public Works Finder',
  description: 'Find public construction bid opportunities in NY and NJ',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <nav className="bg-blue-600 text-white p-4">
          <div className="container mx-auto">
            <h1 className="text-2xl font-bold">TriState Public Works Finder</h1>
          </div>
        </nav>
        <main className="container mx-auto p-4">
          {children}
        </main>
      </body>
    </html>
  )
}
```

**Step 7: Create home page**

Create `frontend/src/app/page.tsx`:
```tsx
import Link from 'next/link'

export default function Home() {
  return (
    <div className="max-w-4xl mx-auto py-12">
      <h2 className="text-4xl font-bold mb-6">
        Find Public Construction Opportunities
      </h2>
      <p className="text-lg mb-8 text-gray-700">
        Access aggregated bid opportunities from New York and New Jersey government procurement portals.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link
          href="/tenders"
          className="block p-6 bg-white rounded-lg shadow hover:shadow-lg transition"
        >
          <h3 className="text-xl font-semibold mb-2">Browse Tenders</h3>
          <p className="text-gray-600">
            Search and filter public works opportunities
          </p>
        </Link>
        <div className="block p-6 bg-gray-100 rounded-lg">
          <h3 className="text-xl font-semibold mb-2">Saved Searches</h3>
          <p className="text-gray-600">
            Coming soon: Save searches and get alerts
          </p>
        </div>
      </div>
    </div>
  )
}
```

**Step 8: Test frontend**

```bash
docker-compose up -d frontend
```

Visit: http://localhost:3000

Expected: Homepage loads with navigation

**Step 9: Commit frontend setup**

```bash
git add frontend/
git commit -m "feat: initialize Next.js frontend with Tailwind CSS"
```

---

### Task 15: Tenders Feed Page

**Files:**
- Create: `frontend/src/app/tenders/page.tsx`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/types/tender.ts`
- Create: `frontend/src/components/TenderCard.tsx`
- Create: `frontend/src/components/TenderFilters.tsx`

**Step 1: Create types**

Create `frontend/src/types/tender.ts`:
```typescript
export enum TenderCategory {
  CONSTRUCTION = 'construction',
  ENGINEERING = 'engineering',
  FACILITIES = 'facilities',
  OTHER = 'other',
}

export enum TenderStatus {
  ACTIVE = 'active',
  CLOSED = 'closed',
  AWARDED = 'awarded',
  CANCELLED = 'cancelled',
}

export interface Document {
  name: string
  url: string
  size?: number
}

export interface Contact {
  name?: string
  email?: string
  phone?: string
}

export interface Tender {
  id: string
  source_url: string
  title: string
  description_text?: string
  agency?: string
  state: string
  city?: string
  county?: string
  category: TenderCategory
  status: TenderStatus
  publish_date?: string
  due_date?: string
  budget_amount?: number
  currency: string
  documents: Document[]
  contact?: Contact
  ai_summary?: string
  ai_trade_tags: string[]
  ai_requirements?: Record<string, any>
  confidence?: number
  scraped_at: string
  updated_at: string
}
```

**Step 2: Create API client**

Create `frontend/src/lib/api.ts`:
```typescript
import axios from 'axios'
import { Tender, TenderCategory, TenderStatus } from '@/types/tender'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface ListTendersParams {
  skip?: number
  limit?: number
  state?: string
  category?: TenderCategory
  status?: TenderStatus
}

export async function listTenders(params?: ListTendersParams): Promise<Tender[]> {
  const response = await api.get('/tenders', { params })
  return response.data
}

export async function getTender(id: string): Promise<Tender> {
  const response = await api.get(`/tenders/${id}`)
  return response.data
}

export async function countTenders(params?: Omit<ListTendersParams, 'skip' | 'limit'>): Promise<number> {
  const response = await api.get('/tenders/count', { params })
  return response.data.count
}
```

**Step 3: Create TenderCard component**

Create `frontend/src/components/TenderCard.tsx`:
```tsx
import { Tender } from '@/types/tender'
import { formatDistanceToNow } from 'date-fns'
import Link from 'next/link'

interface TenderCardProps {
  tender: Tender
}

export function TenderCard({ tender }: TenderCardProps) {
  const dueDateText = tender.due_date
    ? formatDistanceToNow(new Date(tender.due_date), { addSuffix: true })
    : null

  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition">
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-xl font-semibold text-gray-900 flex-1">
          <Link href={`/tenders/${tender.id}`} className="hover:text-blue-600">
            {tender.title}
          </Link>
        </h3>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
          tender.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
        }`}>
          {tender.status}
        </span>
      </div>

      <div className="flex gap-2 mb-3">
        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded">
          {tender.state}
        </span>
        <span className="px-2 py-1 bg-purple-100 text-purple-800 text-sm rounded">
          {tender.category}
        </span>
      </div>

      {tender.agency && (
        <p className="text-sm text-gray-600 mb-2">
          <strong>Agency:</strong> {tender.agency}
        </p>
      )}

      {tender.city && (
        <p className="text-sm text-gray-600 mb-2">
          <strong>Location:</strong> {tender.city}
          {tender.county && `, ${tender.county} County`}
        </p>
      )}

      {tender.ai_summary && (
        <p className="text-gray-700 mb-3">{tender.ai_summary}</p>
      )}

      {tender.ai_trade_tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {tender.ai_trade_tags.map((tag) => (
            <span
              key={tag}
              className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      <div className="flex justify-between items-center text-sm text-gray-500 mt-4">
        {dueDateText && (
          <span className="font-medium text-red-600">Due {dueDateText}</span>
        )}
        <a
          href={tender.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
        >
          View Original →
        </a>
      </div>
    </div>
  )
}
```

**Step 4: Create TenderFilters component**

Create `frontend/src/components/TenderFilters.tsx`:
```tsx
'use client'

import { TenderCategory, TenderStatus } from '@/types/tender'

interface TenderFiltersProps {
  state?: string
  category?: TenderCategory
  status?: TenderStatus
  onStateChange: (state: string) => void
  onCategoryChange: (category: TenderCategory | undefined) => void
  onStatusChange: (status: TenderStatus | undefined) => void
}

export function TenderFilters({
  state,
  category,
  status,
  onStateChange,
  onCategoryChange,
  onStatusChange,
}: TenderFiltersProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h3 className="text-lg font-semibold mb-4">Filters</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* State Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            State
          </label>
          <select
            value={state || ''}
            onChange={(e) => onStateChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All States</option>
            <option value="NY">New York</option>
            <option value="NJ">New Jersey</option>
          </select>
        </div>

        {/* Category Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Category
          </label>
          <select
            value={category || ''}
            onChange={(e) =>
              onCategoryChange(
                e.target.value ? (e.target.value as TenderCategory) : undefined
              )
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Categories</option>
            <option value={TenderCategory.CONSTRUCTION}>Construction</option>
            <option value={TenderCategory.ENGINEERING}>Engineering</option>
            <option value={TenderCategory.FACILITIES}>Facilities</option>
            <option value={TenderCategory.OTHER}>Other</option>
          </select>
        </div>

        {/* Status Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Status
          </label>
          <select
            value={status || ''}
            onChange={(e) =>
              onStatusChange(
                e.target.value ? (e.target.value as TenderStatus) : undefined
              )
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value={TenderStatus.ACTIVE}>Active</option>
            <option value={TenderStatus.CLOSED}>Closed</option>
            <option value={TenderStatus.AWARDED}>Awarded</option>
            <option value={TenderStatus.CANCELLED}>Cancelled</option>
          </select>
        </div>
      </div>
    </div>
  )
}
```

**Step 5: Create tenders page**

Create `frontend/src/app/tenders/page.tsx`:
```tsx
'use client'

import { useState, useEffect } from 'react'
import { Tender, TenderCategory, TenderStatus } from '@/types/tender'
import { listTenders } from '@/lib/api'
import { TenderCard } from '@/components/TenderCard'
import { TenderFilters } from '@/components/TenderFilters'

export default function TendersPage() {
  const [tenders, setTenders] = useState<Tender[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [state, setState] = useState<string>('')
  const [category, setCategory] = useState<TenderCategory | undefined>()
  const [status, setStatus] = useState<TenderStatus | undefined>()

  useEffect(() => {
    loadTenders()
  }, [state, category, status])

  async function loadTenders() {
    try {
      setLoading(true)
      setError(null)
      const data = await listTenders({
        state: state || undefined,
        category,
        status,
        limit: 50,
      })
      setTenders(data)
    } catch (err) {
      setError('Failed to load tenders. Please try again.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto py-8">
      <h1 className="text-3xl font-bold mb-6">Public Works Opportunities</h1>

      <TenderFilters
        state={state}
        category={category}
        status={status}
        onStateChange={setState}
        onCategoryChange={setCategory}
        onStatusChange={setStatus}
      />

      {loading && (
        <div className="text-center py-12">
          <p className="text-gray-600">Loading opportunities...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {!loading && !error && tenders.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-600">
            No opportunities found. Try adjusting your filters.
          </p>
        </div>
      )}

      {!loading && !error && tenders.length > 0 && (
        <div className="space-y-6">
          {tenders.map((tender) => (
            <TenderCard key={tender.id} tender={tender} />
          ))}
        </div>
      )}
    </div>
  )
}
```

**Step 6: Test frontend**

Visit: http://localhost:3000/tenders

Expected: Feed page showing scraped tenders with filters

**Step 7: Commit feed page**

```bash
git add frontend/src/
git commit -m "feat: add tenders feed page with filters"
```

---

## Phase 8: Additional Scrapers

### Task 16: NYS OGS Scraper

**Files:**
- Create: `backend/app/scrapers/sources/nys_ogs.py`
- Create: `backend/tests/test_scrapers/test_nys_ogs.py`

**Step 1: Implement NYS OGS scraper**

Create `backend/app/scrapers/sources/nys_ogs.py`:
```python
"""NYS OGS Procurement Services scraper.

Scrapes bid opportunities from New York State Office of General Services.
Base URL: https://online.ogs.ny.gov/purchase/spg/
"""
from typing import List, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper
from app.schemas.tender import TenderCreate
from app.models.tender import TenderCategory, TenderStatus


class NYSOGSScraper(BaseScraper):
    """Scraper for NYS OGS procurement opportunities."""

    BASE_URL = "https://online.ogs.ny.gov/purchase/spg/"

    def get_source_name(self) -> str:
        """Return source name."""
        return "nys_ogs"

    async def scrape(self) -> List[TenderCreate]:
        """Scrape NYS OGS opportunities."""
        self.log_info("Starting NYS OGS scrape")
        tenders = []

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(self.BASE_URL)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "lxml")

                # Parse bid listings
                # Note: Update selectors based on actual page structure
                bid_items = soup.select("tr.bid-row") or soup.select("div.bid-item")

                self.log_info(f"Found {len(bid_items)} bid items")

                for item in bid_items:
                    try:
                        tender = await self._parse_bid_item(item)
                        if tender:
                            tenders.append(tender)
                    except Exception as e:
                        self.log_error(f"Error parsing bid: {str(e)}")
                        continue

            self.log_info(f"Scraped {len(tenders)} tenders from NYS OGS")
            return tenders

        except Exception as e:
            self.log_error(f"NYS OGS scraping failed: {str(e)}")
            raise

    async def _parse_bid_item(self, item: BeautifulSoup) -> Optional[TenderCreate]:
        """Parse a single bid item."""
        try:
            # Extract title and URL
            title_elem = item.select_one("a")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            url = title_elem.get("href", "")

            if url and not url.startswith("http"):
                url = f"https://online.ogs.ny.gov{url}"

            if not url:
                return None

            # Extract description
            desc_elem = item.select_one(".description")
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            # Extract due date
            due_elem = item.select_one(".due-date")
            due_date = self._parse_date(
                due_elem.get_text(strip=True) if due_elem else None
            )

            tender = TenderCreate(
                source_url=url,
                title=title,
                description_text=description or None,
                agency="NYS Office of General Services",
                state="NY",
                category=TenderCategory.OTHER,
                status=TenderStatus.ACTIVE,
                due_date=due_date,
                documents=[],
                raw_ref={"html": str(item)[:1000]},
            )

            return tender

        except Exception as e:
            self.log_error(f"Error parsing NYS OGS bid: {str(e)}")
            return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string."""
        if not date_str:
            return None

        formats = ["%m/%d/%Y", "%Y-%m-%d", "%B %d, %Y"]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None
```

**Step 2: Register NYS OGS scraper**

Edit `backend/app/scrapers/registry.py` - add:
```python
from app.scrapers.sources.nys_ogs import NYSOGSScraper

registry.register("nys_ogs", NYSOGSScraper)
```

**Step 3: Add to seed script**

Edit `backend/scripts/seed_sources.py` - add to sources list:
```python
{
    "name": "NYS OGS Procurement",
    "state": "NY",
    "base_url": "https://online.ogs.ny.gov/purchase/spg/",
    "scraper_class": "nys_ogs",
    "active": True,
    "config": {},
},
```

**Step 4: Run seed script**

```bash
docker-compose exec backend python scripts/seed_sources.py
```

**Step 5: Commit NYS OGS scraper**

```bash
git add backend/app/scrapers/sources/nys_ogs.py backend/app/scrapers/registry.py backend/scripts/seed_sources.py
git commit -m "feat: add NYS OGS Procurement scraper"
```

---

[Continue with remaining scrapers - NJ Treasury, NJDOT, and optional sources following same pattern...]

---

## Summary & Next Steps

This plan provides the foundation for the TriState Public Works Finder MVP. The remaining tasks include:

1. **Additional Scrapers** (Task 17-20): NJ Treasury, NJDOT, Newark, and any additional sources
2. **AI Enrichment** (Task 21-22): Claude API integration for summaries and tagging
3. **Authentication** (Task 23-24): User registration/login with JWT
4. **Saved Searches** (Task 25-26): CRUD operations for saved searches
5. **Email Digests** (Task 27-28): Daily email alerts matching user preferences
6. **Admin Dashboard** (Task 29): View scrape runs and system health
7. **Tender Detail Page** (Task 30): Full tender details with documents
8. **Testing & Polish** (Task 31-32): Integration tests, error handling, documentation

Each task follows the same TDD pattern:
1. Write test
2. Verify it fails
3. Implement minimal code
4. Verify it passes
5. Commit

The architecture supports easy addition of new sources by implementing the `BaseScraper` interface and registering in the registry.
