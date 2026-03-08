# Automated Website Discovery Guide

## Overview

This system automates the discovery of procurement portals by:
1. **Querying Google** with 4,003 pre-generated search queries
2. **Storing candidates** in a database with relevance scoring
3. **Manual verification** workflow for quality control
4. **Export approved sites** for Crawl4AI scraping

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Search Queries │────▶│  Google Search   │────▶│   Candidate     │
│   (4,003 pre-   │     │   API Client     │     │   Database      │
│   generated)    │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Crawl4AI      │◀────│    Approved      │◀────│     Manual      │
│   Scraping      │     │   Candidates     │     │  Verification   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Prerequisites

### 1. Get Google Custom Search API Credentials

**Option A: Google Custom Search API (Recommended)**
- Free tier: 100 queries/day
- Paid tier: $5 per 1000 queries (up to 10K/day)

**Steps:**
1. Go to https://developers.google.com/custom-search/v1/overview
2. Create a project in Google Cloud Console
3. Enable Custom Search API
4. Create credentials (API key)
5. Create a Custom Search Engine (CSE) at https://programmablesearchengine.google.com/
   - Search the entire web
   - Copy your CSE ID

**Option B: SerpAPI (Alternative)**
- Pricing: $50/month for 5,000 searches
- No setup required, just API key
- Sign up at https://serpapi.com/

### 2. Set Environment Variables

Create or update `.env`:
```env
# Google Custom Search API
GOOGLE_SEARCH_API_KEY=your_api_key_here
GOOGLE_CSE_ID=your_cse_id_here

# OR use SerpAPI
SERPAPI_KEY=your_serpapi_key_here
```

### 3. Database Migration

The candidate_websites table will be created by migration:
```bash
docker-compose exec backend alembic revision --autogenerate -m "add candidate websites table"
docker-compose exec backend alembic upgrade head
```

## Usage

### Phase 1: Automated Discovery

**Test API Connection:**
```bash
docker-compose exec backend python scripts/automated_discovery.py \
  --test \
  --api-key YOUR_KEY \
  --cse-id YOUR_CSE_ID
```

**Run Phase 1 Discovery (Critical entities - 30 entities):**
```bash
docker-compose exec backend python scripts/automated_discovery.py \
  --phase 1 \
  --api-key YOUR_KEY \
  --cse-id YOUR_CSE_ID \
  --results-per-query 10
```

**Run with limits (for testing):**
```bash
docker-compose exec backend python scripts/automated_discovery.py \
  --phase 1 \
  --api-key YOUR_KEY \
  --cse-id YOUR_CSE_ID \
  --max-entities 5 \
  --results-per-query 5
```

**Using SerpAPI instead:**
```bash
docker-compose exec backend python scripts/automated_discovery.py \
  --phase 1 \
  --api-key YOUR_SERPAPI_KEY \
  --use-serpapi
```

### Phase 2: Review Candidates

**Interactive Review:**
```bash
docker-compose exec backend python scripts/review_candidates.py --interactive
```

This presents each candidate with:
- Entity name and state
- URL, title, description
- Relevance score and priority
- Keywords found

Actions:
- `v` = Verified (has RFPs)
- `a` = Approved (ready for scraping)
- `r` = Rejected (no RFPs)
- `d` = Duplicate
- `i` = Inaccessible
- `o` = Open in browser
- `s` = Skip
- `q` = Quit

**List candidates by status:**
```bash
docker-compose exec backend python scripts/review_candidates.py \
  --list \
  --status discovered \
  --limit 50
```

### Phase 3: Export for Manual Review

**Export high-priority candidates to CSV:**
```bash
docker-compose exec backend python scripts/export_candidates.py --for-review
```

This creates `candidates_for_review.csv` with:
- Only high-priority (7+) discovered candidates
- All relevant metadata
- Ready for bulk review in Excel/Sheets

**Export approved candidates for scraping:**
```bash
docker-compose exec backend python scripts/export_candidates.py --for-scraping
```

This creates `candidates_approved_for_scraping.csv` with candidates ready to configure scrapers for.

**Export all by status:**
```bash
docker-compose exec backend python scripts/export_candidates.py \
  --status verified \
  --output verified_candidates.csv
```

## Discovery Workflow

### Week 1-2: Phase 1 (Critical Entities)

**Entities:** 30 high-priority (NYC, major authorities)
**Queries:** ~500-600 search queries
**Expected candidates:** 300-500 websites

```bash
# Run discovery
python scripts/automated_discovery.py --phase 1 --api-key $API_KEY --cse-id $CSE_ID

# Review interactively
python scripts/review_candidates.py --interactive

# Export for team review
python scripts/export_candidates.py --for-review

# Export approved for scraping
python scripts/export_candidates.py --for-scraping
```

### Week 3-4: Phase 2 (High Priority)

**Entities:** 61 major counties/cities
**Queries:** ~1,000-1,200
**Expected candidates:** 500-800 websites

```bash
python scripts/automated_discovery.py --phase 2 --api-key $API_KEY --cse-id $CSE_ID
python scripts/review_candidates.py --interactive
```

### Week 5-8: Phase 3 (Medium Priority)

**Entities:** 134 medium municipalities
**Queries:** ~2,000-2,500
**Expected candidates:** 800-1,200 websites

### Week 9-12: Phase 4 (Comprehensive)

**Entities:** All 229 entities
**Queries:** 4,003 total
**Expected candidates:** 1,500-2,000 websites

## Candidate Scoring

### Relevance Score (0-100)

**Base scoring:**
- +10 points per procurement keyword found
- +30 points for .gov or .us domain
- +20 points for procurement keywords in URL path
- +10 points for "current" or "open" in text

**Priority Score (1-10):**
- Based on relevance score
- Search result rank (higher = better)
- Government domain (+1 bonus)

### Status Workflow

```
DISCOVERED → VERIFIED → APPROVED → Ready for Scraping
                ↓
            REJECTED / DUPLICATE / INACCESSIBLE
```

**DISCOVERED:** Found via search, awaiting review
**VERIFIED:** Manually confirmed to have RFPs
**APPROVED:** Ready for scraper configuration
**REJECTED:** Doesn't have RFPs or not relevant
**DUPLICATE:** Duplicate of existing source
**INACCESSIBLE:** Site down or blocked

## API Quota Management

### Google Custom Search API

**Free tier limits:**
- 100 queries/day
- Can process ~3-5 entities/day
- Phase 1 would take ~7-10 days on free tier

**Paid tier ($5 per 1000 queries):**
- 10,000 queries/day max
- Phase 1: $2.50-$3.00
- Phase 2: $5-$6
- Phase 3-4: $10-$12
- **Total cost: ~$20-25 for all 4 phases**

### SerpAPI

**Pricing:**
- $50/month: 5,000 searches
- $125/month: 15,000 searches
- All 4 phases: Would need $125/month plan

### Strategy

**Option 1: Slow & Free**
- Use free 100 queries/day
- Process 5-7 entities/day
- Complete all phases in ~30-40 days
- **Cost: $0**

**Option 2: Fast & Paid**
- Use Google paid tier
- Process all phases in 4-5 days
- **Cost: ~$25 total**

**Option 3: Hybrid**
- Phase 1 on paid (highest priority)
- Phase 2-4 on free tier
- **Cost: ~$5, Time: 20 days**

## Database Schema

### candidate_websites Table

```sql
id                        uuid PRIMARY KEY
url                       varchar(500) UNIQUE
domain                    varchar(200)
title                     varchar(500)
description               text
entity_name               varchar(200)
entity_state              varchar(2)
entity_type               varchar(50)
discovery_method          enum
search_query              varchar(500)
search_rank               integer
relevance_score           float (0-100)
procurement_keywords_found jsonb
has_bid_list              boolean
has_search_function       boolean
requires_login            boolean
detected_portal_vendor    varchar(50)
is_government_domain      boolean
status                    enum
verified_at               timestamp
verified_by               varchar(100)
verification_notes        text
priority                  integer (1-10)
notes                     text
response_time_ms          float
http_status               integer
ssl_valid                 boolean
created_at                timestamp
updated_at                timestamp
last_checked_at           timestamp
```

## Quality Control

### Manual Verification Checklist

For each candidate, verify:
1. **Site loads** - Not 404 or broken
2. **Has RFPs** - Actually lists procurement opportunities
3. **Construction-related** - Not just general RFPs
4. **Public access** - Can view without login
5. **Up-to-date** - Has recent postings
6. **Scrapeable** - Not behind CAPTCHA or heavy JS

### Approval Criteria

**Approve if:**
- ✅ Government entity site
- ✅ Lists construction/public works RFPs
- ✅ Publicly accessible
- ✅ Has current opportunities
- ✅ Reasonable to scrape

**Reject if:**
- ❌ Not a procurement site
- ❌ Requires paid subscription
- ❌ Only archived/historical bids
- ❌ Refers to external portal (use that portal instead)
- ❌ Not construction-related

## Next Steps After Approval

### 1. Configure Scrapers

For approved candidates, create scraper configurations:
```python
# Add to source_registry
{
    "name": "Bergen County",
    "url": "https://www.co.bergen.nj.us/procurement",
    "portal_vendor": "custom_html",  # or detected_portal_vendor
    "scraper_class": "bergen_county",
    "active": True,
}
```

### 2. Use Crawl4AI for Scraping

The approved candidates are ready for:
- Portal vendor detection
- Crawl4AI-based scraping
- Structure analysis
- Data extraction

See: `docs/plans/2026-02-27-source-discovery-master-plan.md`

### 3. Monitor Quality

Track:
- Scraping success rate
- Data quality
- Update frequency
- False positives (approved but no RFPs)

## Troubleshooting

### "Rate limit exceeded"

**Solution:**
- Wait 24 hours for quota reset (free tier)
- Upgrade to paid tier
- Use `--max-entities` to limit scope
- Spread searches over multiple days

### "No results found"

**Solution:**
- Check API credentials
- Test with `--test` flag
- Verify CSE is configured to search entire web
- Try alternative search queries

### "Too many duplicates"

**Solution:**
- Existing candidate URLs are automatically skipped
- Duplicates within same entity are normal (different queries)
- Mark as DUPLICATE in review to ignore

### "Low relevance scores"

**Solution:**
- Adjust scoring weights in `google_search_service.py`
- Add more procurement keywords
- Use site-restricted queries (site:.gov)

## Performance Metrics

### Expected Results by Phase

| Phase | Entities | Queries | API Calls | Cost | Time (Paid) | Candidates Expected |
|-------|----------|---------|-----------|------|-------------|---------------------|
| 1     | 30       | ~600    | 600       | $3   | 1-2 days    | 300-500             |
| 2     | 61       | ~1,200  | 1,200     | $6   | 2-3 days    | 500-800             |
| 3     | 134      | ~2,500  | 2,500     | $12  | 3-4 days    | 800-1,200           |
| 4     | 229      | ~4,000  | 4,000     | $20  | 4-5 days    | 1,500-2,000         |

### Quality Targets

- **Approval rate:** 30-50% (of discovered)
- **False positive rate:** <10% (approved but no RFPs)
- **Government domain rate:** >60%
- **Avg relevance score:** >40

## Scripts Reference

### automated_discovery.py
```bash
# Test API
python scripts/automated_discovery.py --test --api-key KEY --cse-id CSE

# Run phase
python scripts/automated_discovery.py --phase 1 --api-key KEY --cse-id CSE

# Limit for testing
python scripts/automated_discovery.py --phase 1 --api-key KEY --cse-id CSE --max-entities 5

# Use SerpAPI
python scripts/automated_discovery.py --phase 1 --api-key KEY --use-serpapi
```

### review_candidates.py
```bash
# Interactive review
python scripts/review_candidates.py --interactive

# List by status
python scripts/review_candidates.py --list --status discovered

# List all
python scripts/review_candidates.py --list --limit 100
```

### export_candidates.py
```bash
# Export for review
python scripts/export_candidates.py --for-review

# Export for scraping
python scripts/export_candidates.py --for-scraping

# Export by status
python scripts/export_candidates.py --status verified --output verified.csv

# Export high-priority only
python scripts/export_candidates.py --min-priority 8 --output high_priority.csv
```

## Resources

- **Google Custom Search API:** https://developers.google.com/custom-search
- **SerpAPI:** https://serpapi.com/
- **Entity List:** `docs/data/tristate-entities-comprehensive.csv`
- **Search Queries:** `docs/data/search-queries-phase_*.json`
- **Discovery Plan:** `docs/plans/2026-02-27-source-discovery-master-plan.md`
