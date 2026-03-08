# Quick Start: Automated RFP Source Discovery

## What We Built

A complete **automated discovery pipeline** to find ALL procurement portals in the NYC/NJ/CT tri-state area that publish construction RFPs.

### System Components

```
📊 Entity List (229 entities)
    ↓
🔍 Search Queries (4,003 queries)
    ↓
🌐 Google Search API (automated)
    ↓
💾 Candidate Database (with scoring)
    ↓
✅ Manual Verification (interactive)
    ↓
📥 Export Approved (ready for Crawl4AI)
```

## Files Created

### 1. Entity & Query Data
- `docs/data/tristate-entities-comprehensive.csv` - 229 entities
- `docs/data/search-queries-phase_*.json` - 4,003 queries organized by priority
- `backend/scripts/generate_search_queries.py` - Query generator

### 2. Discovery System
- `backend/app/models/candidate_website.py` - Database model
- `backend/app/services/google_search_service.py` - Discovery service
- `backend/app/services/google_custom_search.py` - Google API client
- `backend/scripts/automated_discovery.py` - Main discovery script
- `backend/scripts/review_candidates.py` - Interactive review
- `backend/scripts/export_candidates.py` - CSV export

### 3. Documentation
- `docs/AUTOMATED_DISCOVERY_GUIDE.md` - Complete guide
- `docs/SOURCE_DISCOVERY_GUIDE.md` - Strategy overview
- `docs/QUICK_START_DISCOVERY.md` - This file

## Quick Start (5 Steps)

### Step 1: Get API Credentials

**Option A: Google Custom Search API**
1. Visit https://developers.google.com/custom-search
2. Create project & enable API
3. Create API key
4. Create Custom Search Engine: https://programmablesearchengine.google.com/
5. Get CSE ID

**Option B: SerpAPI (easier but paid)**
1. Visit https://serpapi.com
2. Sign up ($50/month for 5,000 searches)
3. Get API key

### Step 2: Configure Environment

Add to `.env`:
```env
# Google Custom Search
GOOGLE_SEARCH_API_KEY=your_api_key_here
GOOGLE_CSE_ID=your_cse_id_here

# OR SerpAPI
SERPAPI_KEY=your_serpapi_key_here
```

### Step 3: Run Database Migration

```bash
docker-compose exec backend alembic revision --autogenerate -m "add candidate websites"
docker-compose exec backend alembic upgrade head
```

### Step 4: Test API Connection

```bash
docker-compose exec backend python scripts/automated_discovery.py \
  --test \
  --api-key $GOOGLE_SEARCH_API_KEY \
  --cse-id $GOOGLE_CSE_ID
```

Expected: 5 search results displayed

### Step 5: Run Discovery (Phase 1)

```bash
# Start with 5 entities for testing
docker-compose exec backend python scripts/automated_discovery.py \
  --phase 1 \
  --api-key $GOOGLE_SEARCH_API_KEY \
  --cse-id $GOOGLE_CSE_ID \
  --max-entities 5
```

This will:
- Execute ~15 Google searches
- Find 30-50 candidate websites
- Store in database with scores
- Take ~30 seconds

## Review & Export

### Review Candidates Interactively

```bash
docker-compose exec backend python scripts/review_candidates.py --interactive
```

For each candidate:
- Press `v` to mark as Verified (has RFPs)
- Press `a` to mark as Approved (ready for scraping)
- Press `r` to Reject
- Press `o` to Open in browser
- Press `q` to Quit

### Export to CSV for Bulk Review

```bash
docker-compose exec backend python scripts/export_candidates.py --for-review
```

Opens `candidates_for_review.csv` with all high-priority candidates.

### Export Approved for Scraping

```bash
docker-compose exec backend python scripts/export_candidates.py --for-scraping
```

Creates `candidates_approved_for_scraping.csv` ready for Crawl4AI.

## Full Production Run

### Phase 1: Critical Entities (Week 1)

```bash
# 30 entities, ~600 queries
docker-compose exec backend python scripts/automated_discovery.py \
  --phase 1 \
  --api-key $GOOGLE_SEARCH_API_KEY \
  --cse-id $GOOGLE_CSE_ID

# Cost: ~$3 (paid) or 6 days (free 100/day)
```

**Expected results:**
- 300-500 candidate websites
- 100-150 verified sources
- 50-75 approved for scraping

### Phase 2: High Priority (Week 2)

```bash
# 61 entities, ~1,200 queries
docker-compose exec backend python scripts/automated_discovery.py \
  --phase 2 \
  --api-key $GOOGLE_SEARCH_API_KEY \
  --cse-id $GOOGLE_CSE_ID

# Cost: ~$6 or 12 days free
```

**Expected results:**
- +500-800 candidates
- +150-250 verified
- +75-125 approved

### Phase 3-4: Comprehensive (Week 3-4)

```bash
# Phase 3: 134 entities
docker-compose exec backend python scripts/automated_discovery.py --phase 3 ...

# Phase 4: All 229 entities
docker-compose exec backend python scripts/automated_discovery.py --phase 4 ...

# Combined cost: ~$15 or 30 days free
```

**Final totals:**
- 1,500-2,000 total candidates
- 400-600 verified sources
- 200-300 approved for scraping

## Cost Analysis

### Google Custom Search API

| Tier | Queries/Day | Cost | Timeline (All Phases) |
|------|-------------|------|-----------------------|
| Free | 100         | $0   | 40 days               |
| Paid | 10,000      | $20  | 1 week                |

**Recommendation:** Use free tier for Phases 2-4, paid for Phase 1 ($3)
**Total cost:** ~$3-5, Timeline: 2-3 weeks

### SerpAPI

| Plan | Searches | Cost/Month | Timeline |
|------|----------|------------|----------|
| Base | 5,000    | $50        | 1 month  |
| Plus | 15,000   | $125       | 1 week   |

**Recommendation:** Only if you need speed and have budget

## Database Schema

### candidate_websites table

```sql
id                      uuid PRIMARY KEY
url                     varchar(500) UNIQUE     -- Website URL
entity_name             varchar(200)            -- Associated entity
entity_state            varchar(2)              -- NY, NJ, CT
status                  enum                    -- discovered/verified/approved
relevance_score         float (0-100)           -- Auto-scored relevance
priority                integer (1-10)          -- Review priority
is_government_domain    boolean                 -- .gov or .us domain
procurement_keywords_found jsonb                -- Keywords detected
verified_at             timestamp               -- Manual verification date
verified_by             varchar(100)            -- Who verified
```

## Verification Workflow

```
┌─────────────┐
│ DISCOVERED  │  ← Automatic (from Google search)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  VERIFIED   │  ← Manual (has RFPs confirmed)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  APPROVED   │  ← Ready for scraper setup
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Crawl4AI    │  ← Next phase: automated scraping
│ Scraping    │
└─────────────┘
```

**Rejected paths:**
- REJECTED (no RFPs)
- DUPLICATE (same as existing)
- INACCESSIBLE (site down)

## Next Steps After Approval

### 1. Portal Vendor Detection

Use the portal detector on approved candidates:
```python
from app.discovery.portal_detector import PortalDetector

detector = PortalDetector()
vendor = await detector.detect_portal_vendor(candidate.url)
```

### 2. Add to Source Registry

Add approved candidates to source registry:
```python
from app.models.source_registry import SourceRegistry

source = SourceRegistry(
    entity_name=candidate.entity_name,
    state=candidate.entity_state,
    portal_vendor=vendor,
    bid_list_url=candidate.url,
    ...
)
```

### 3. Configure Scrapers

Create scraper configuration using Crawl4AI:
- See: `docs/plans/2026-02-27-source-discovery-master-plan.md`
- Tasks 4-5: Crawl4AI Integration
- Task 6: Portal Vendor Detection

## Monitoring & Quality

### Check Discovery Stats

```bash
docker-compose exec backend python -c "
from app.database import SessionLocal
from app.services.google_search_service import GoogleSearchService

db = SessionLocal()
service = GoogleSearchService(db)
stats = service.get_statistics()
print(stats)
db.close()
"
```

### Quality Metrics

**Target metrics:**
- Approval rate: 30-50% (of discovered)
- Gov domain rate: >60%
- Avg relevance score: >40
- False positive rate: <10%

## Troubleshooting

### "Rate limit exceeded"

**Free tier:** Wait 24 hours for quota reset
**Solution:** Use `--max-entities 5` to limit, or upgrade to paid

### "No results found"

**Check:**
1. API key is correct
2. CSE ID is correct
3. CSE is configured to search entire web
4. Test with `--test` flag

### "Low relevance scores"

**Adjust:**
- Add more keywords to `PROCUREMENT_KEYWORDS` in `google_search_service.py`
- Use site-restricted queries (`site:.gov`)
- Increase weight for government domains

## Repository Links

**GitHub:** https://github.com/Matadogas/appalti

**Key files:**
- Entity list: `/docs/data/tristate-entities-comprehensive.csv`
- Search queries: `/docs/data/search-queries-phase_*.json`
- Discovery script: `/backend/scripts/automated_discovery.py`
- Full guide: `/docs/AUTOMATED_DISCOVERY_GUIDE.md`

## Summary

✅ **229 entities** mapped across NY, NJ, CT
✅ **4,003 search queries** pre-generated
✅ **Automated discovery** via Google Search API
✅ **Candidate database** with scoring & prioritization
✅ **Manual verification** workflow
✅ **CSV export** for bulk review
✅ **Ready for Crawl4AI** scraping integration

**Total cost:** $20-25 (or free over 40 days)
**Expected outcome:** 200-300 approved procurement portals
**Timeline:** 2-4 weeks depending on budget

🚀 **You're ready to discover ALL RFP sources systematically!**
