# RFP Source Discovery - Current Status

## Overview

We are systematically discovering ALL procurement portals in the NYC/NJ/CT tri-state area that publish construction RFPs.

## What We've Built

### 1. Entity Database (✅ Complete)
- **229 governmental entities** mapped across NY, NJ, CT
- Includes: counties, cities, townships, authorities, school districts
- Priority scoring (1-10) for phased discovery
- File: `docs/data/tristate-entities-comprehensive.csv`

### 2. Search Query Generation (✅ Complete)
- **4,003 search queries** pre-generated
- Organized into 4 priority phases
- 3 query types: basic, site-restricted, construction-specific
- Files: `docs/data/search-queries-phase_*.json`

### 3. Automated Discovery System (✅ Complete)
- Database model for candidate websites
- Google Custom Search API client
- Discovery service with relevance scoring
- Interactive review workflow
- CSV export for manual verification
- Scripts:
  - `backend/scripts/automated_discovery.py`
  - `backend/scripts/review_candidates.py`
  - `backend/scripts/export_candidates.py`

### 4. Bootstrap Candidate Generation (✅ Complete)
- **2,043 candidate URLs** generated from entity list
- Based on common government procurement portal URL patterns
- Includes third-party platforms (Bonfire, BidSync, etc.)
- File: `backend/scripts/bootstrap_candidates.csv`

### 5. URL Validation (🔄 In Progress)
- Checking which of the 2,043 candidate URLs are accessible
- Currently running validation on all candidates
- Expected: ~40-50 accessible URLs (2% hit rate from testing)
- Will output: `backend/scripts/target_websites.csv`

## Current Blocker: Google Search API

### Issue
The Google Custom Search API is returning **403 Forbidden** errors when we try to query it.

### Error Details
```
Client error '403 Forbidden' for url 'https://www.googleapis.com/customsearch/v1?key=AIzaSyCea7nwu-elpSXCx8BCVyZRlMVps4DK6NI&cx=a75fcb2f3aef24fe9&q=...'
```

### Likely Causes
1. **Custom Search API not enabled** in Google Cloud Console
2. **API key restrictions** (HTTP referrer, IP address, etc.)
3. **CSE not configured correctly** (not set to search entire web)
4. **Billing not enabled** (required for paid tier)

### How to Fix

#### Step 1: Enable Custom Search API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to "APIs & Services" → "Library"
4. Search for "Custom Search API"
5. Click "Enable"

#### Step 2: Check API Key Restrictions
1. Go to "APIs & Services" → "Credentials"
2. Click on your API key
3. Under "API restrictions":
   - Select "Restrict key"
   - Enable "Custom Search API"
4. Under "Application restrictions":
   - For testing: Select "None"
   - For production: Add your IP or domain

#### Step 3: Verify CSE Configuration
1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Select your search engine (ID: `a75fcb2f3aef24fe9`)
3. Click "Edit search engine" → "Setup"
4. Under "Sites to search":
   - Select "Search the entire web"
   - NOT "Search only included sites"
5. Save changes

#### Step 4: Enable Billing (for paid tier)
1. Go to Google Cloud Console → "Billing"
2. Link a billing account
3. Free tier: 100 queries/day
4. Paid tier: $5 per 1,000 queries (up to 10,000/day)

#### Step 5: Test API
```bash
cd backend
python scripts/automated_discovery.py \
  --test \
  --api-key AIzaSyCea7nwu-elpSXCx8BCVyZRlMVps4DK6NI \
  --cse-id a75fcb2f3aef24fe9
```

Expected output: 5 search results from Google

## Alternative Approach (Current)

Since the Google API isn't working yet, we're using a **bootstrap approach**:

### Bootstrap Method
1. **Generate candidate URLs** based on common patterns (✅ Complete)
   - Pattern: `www.co.[county].nj.us/procurement`
   - Pattern: `[city].gov/purchasing`
   - Pattern: `[entity].bonfirehub.com`
   - etc.

2. **Validate URLs** by checking HTTP accessibility (🔄 In Progress)
   - Testing each URL to see if it responds
   - ~2% hit rate (40-50 accessible URLs expected)

3. **Manual verification** of accessible URLs
   - Confirm they actually have RFP listings
   - Check if they're construction-related
   - Verify they're scrapeable

### Bootstrap Results (Preliminary)
From testing 50 URLs:
- ✅ **Accessible:** 1 URL (2%)
  - Bergen County NJ: `https://www.co.bergen.nj.us/procurement`
- ❌ **Inaccessible:** 49 URLs (98%)

This confirms that:
- URL patterns work for some entities
- We need Google Search for comprehensive discovery
- Bootstrap gives us a starter list (~40-50 URLs)

## Data Files

### Generated Files
| File | Description | Status |
|------|-------------|--------|
| `tristate-entities-comprehensive.csv` | 229 entities | ✅ Complete |
| `search-queries-phase_*.json` | 4,003 search queries | ✅ Complete |
| `bootstrap_candidates.csv` | 2,043 candidate URLs | ✅ Complete |
| `validated_candidates.csv` | Validation results | 🔄 In Progress |
| `target_websites.csv` | Final accessible URLs | 🔄 In Progress |

### Expected Output Format
The final `target_websites.csv` will have:
```csv
website_url,website_name,state,entity_type,entity_name,estimated_platform,priority
https://www.co.bergen.nj.us/procurement,Bergen County,NJ,county,Bergen County,custom_html,9
...
```

## Next Steps

### Immediate (Today)
1. ✅ Fix Settings class to accept Google API credentials
2. 🔄 Complete URL validation on 2,043 bootstrap candidates
3. ⏳ Review validation results and create target list
4. ⏳ Fix Google Search API configuration

### Short Term (This Week)
1. Once Google API is fixed:
   - Run test with 5 entities
   - Run Phase 1 discovery (30 entities)
   - Review and verify discovered candidates
2. Manual verification of bootstrap URLs
3. Begin Crawl4AI integration for scraping

### Medium Term (Next 2 Weeks)
1. Phase 2 discovery (61 entities, 1,200 queries)
2. Phase 3 discovery (134 entities, 2,500 queries)
3. Build comprehensive verified source list (200-300 sites)
4. Set up automated scraping for verified sources

## Cost Estimates

### Bootstrap Method (Current)
- **Cost:** $0
- **Time:** ~5 minutes for validation
- **Expected results:** 40-50 accessible URLs
- **Limitation:** Low coverage, many false positives

### Google Search API (Recommended)
| Phase | Entities | Queries | Cost | Results |
|-------|----------|---------|------|---------|
| 1 | 30 | 600 | $3 | 300-500 candidates |
| 2 | 61 | 1,200 | $6 | 500-800 candidates |
| 3 | 134 | 2,500 | $12 | 800-1,200 candidates |
| 4 | 229 | 4,000 | $20 | 1,500-2,000 candidates |

**Total:** $41 for all phases, or $0 using free tier over 40 days

## Success Metrics

### Target Goals
- **200-300 verified procurement portals** across tri-state
- **60%+ government domains** (.gov, .us)
- **30-50% approval rate** (of discovered candidates)
- **Comprehensive coverage** of all 229 entities

### Current Status
- Entities mapped: **229** ✅
- Search queries ready: **4,003** ✅
- Bootstrap candidates: **2,043** ✅
- Validated URLs: **~40-50** (pending)
- Verified sources: **3** (NYC PASSPort, NYS OGS, Port Authority)
- Google API: **Not working** ❌

## Repository

**GitHub:** https://github.com/Matadogas/appalti

**Key directories:**
- `/docs/data/` - Entity lists and search queries
- `/docs/` - Implementation plans and guides
- `/backend/scripts/` - Discovery and validation scripts
- `/backend/app/models/` - Database models
- `/backend/app/services/` - Discovery services

## Support

For Google API issues:
- [Custom Search API Documentation](https://developers.google.com/custom-search/v1/overview)
- [Programmable Search Engine](https://programmablesearchengine.google.com/)
- [API Key Management](https://console.cloud.google.com/apis/credentials)

For script issues:
- Check script documentation in `/docs/AUTOMATED_DISCOVERY_GUIDE.md`
- Review quick start: `/docs/QUICK_START_DISCOVERY.md`

---

**Last Updated:** 2026-03-08
**Status:** Bootstrap validation in progress, Google API configuration needed
