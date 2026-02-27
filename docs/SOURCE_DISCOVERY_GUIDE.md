# Source Discovery & Coverage Master Guide

## Overview

This guide explains how to systematically discover, track, and scrape ALL NYC + NJ public construction RFP/RFQ/IFB sources using our procurement data supply chain.

## The Procurement Data Supply Chain

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Discover   │───▶│    Detect    │───▶│   Configure  │───▶│    Scrape    │
│   Entities   │    │ Portal Type  │    │   Adapter    │    │  & Normalize │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                                                      │
                                                                      ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│    Email     │◀───│    Store     │◀───│   Enrich     │◀───│   Monitor    │
│   Alerts     │    │   Tenders    │    │  with AI     │    │  Coverage    │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

## Phase 1: Discovery (How to Find All Sources)

### Step 1: Use Seed Lists

**Start with known directories:**
1. **NJ Treasury "Other Bid Opportunity Sites"** - https://www.nj.gov/treasury/purchase/bid.shtml
   - Contains ~20-30 authority/agency portals
   - Already vetted by NJ government
   - High-value starting point

2. **NYC Agency Directory** - https://www.nyc.gov/agencies
   - 40+ city agencies
   - Many have procurement pages
   - Start with construction-heavy: DDC, DEP, DOT, DSNY, SCA

3. **NJ County/City Lists**
   - Use our `docs/templates/discovery-checklist.csv` as starting point
   - 21 NJ counties
   - 15 major NJ cities
   - Upstate NY counties near metro area

### Step 2: Automated Discovery

**Run the entity discovery script:**
```bash
docker-compose exec backend python scripts/discover_entities.py
```

This will:
- Try predictable URL patterns for each entity
- Fetch pages and verify they contain procurement content
- Detect portal vendor automatically
- Export to `discovered_entities.csv`

**Predictable URL patterns we try:**
- `https://www.co.{county}.nj.us/procurement`
- `https://www.cityof{city}.org/purchasing`
- `https://www.{city}nj.gov/departments/purchasing`

### Step 3: Google Search Strategy

For entities not found via predictable URLs:

**Search query template:**
```
"{entity name}" + (procurement OR purchasing OR bids OR "current bids" OR RFP)
```

**Examples:**
- `"Bergen County" procurement site:nj.us`
- `"City of Paterson" current bids site:patersonnj.gov`
- `"Newark Public Schools" RFP purchasing`

**Look for:**
- Official .gov domains
- Pages with "Current Bids", "Open Solicitations", "Bid Opportunities"
- Portal embeds (OpenGov, ProcureNow badges)

### Step 4: Cross-Reference with Aggregators

**Use aggregators for QA only (don't depend on them):**
- BidNet Direct - https://www.bidnetdirect.com/new-jersey
- Onvia DemandStar - https://www.demandstar.com/
- Check weekly: do they have bids you don't?

**Process:**
1. Sample 10 random entities from aggregator
2. Check if those bids exist in your system
3. If missing, investigate source

## Phase 2: Portal Vendor Detection

### Automatic Detection

Our `PortalDetector` class automatically identifies portal vendors:

**Domain-based detection (fast):**
- `bidexpress.com` → BidExpress
- `opengov.com/procurement` → OpenGov
- `njstart.gov` → NJSTART
- `procurenow.com` → ProcureNow

**HTML signature detection:**
- Looks for vendor names in page content
- Detects JavaScript frameworks (React, Angular)
- Identifies authentication requirements

**Run detection:**
```bash
docker-compose exec backend python -c "
import asyncio
from app.discovery.portal_detector import PortalDetector

async def detect():
    detector = PortalDetector()
    vendor = await detector.detect_portal_vendor('https://example.gov/bids')
    print(f'Vendor: {vendor}')
    await detector.close()

asyncio.run(detect())
"
```

### Portal Vendor Patterns

**Common vendors in NYC/NJ:**

| Vendor | Characteristics | Examples | Scraping Complexity |
|--------|----------------|----------|-------------------|
| **PASSPort** | NYC-specific, heavy JS | NYC agencies | High - requires JS |
| **BidExpress** | Construction-focused, login required | NJDOT, NJ Transit | Medium - free registration |
| **OpenGov** | Modern SaaS, clean API | Newark, many cities | Low - JSON endpoints |
| **ProcureNow** | Canadian vendor, iframe embeds | Newark (alternative view) | Medium - embedded content |
| **NJSTART** | NJ state system, search interface | NJ state agencies | Medium - POST forms |
| **Bonfire** | Modern platform | Some municipalities | Low - good structure |
| **DemandStar** | Subscription-based | Jersey City area | High - paywall |
| **Custom HTML** | Simple listing pages | Small counties/schools | Low - basic parsing |

### Building Portal Adapters

**When to build a new adapter:**
- You discover 5+ entities using the same portal vendor
- The vendor has a unique structure not covered by existing adapters

**Adapter template:**
```python
from app.scrapers.crawl4ai_scraper import Crawl4AIScraper
from app.schemas.tender import TenderCreate

class MyPortalAdapter(Crawl4AIScraper):
    """Adapter for [Portal Vendor Name]."""

    def get_source_name(self) -> str:
        return "my_portal"

    async def scrape(self) -> List[TenderCreate]:
        # 1. Fetch listing page
        result = await self.fetch_page(self.config["bid_list_url"])

        # 2. Parse tender list
        soup = BeautifulSoup(result["html"], "lxml")

        # 3. Extract and return tenders
        tenders = []
        for item in soup.select(".bid-item"):
            tender = self._parse_item(item)
            tenders.append(tender)

        return tenders
```

## Phase 3: Tracking & Organization

### Source Registry

**The source_registry table is your source of truth.**

**Add new sources via seed script:**
```python
# Edit backend/scripts/seed_sources.py
sources = [
    {
        "name": "Bergen County",
        "state": "NJ",
        "base_url": "https://www.co.bergen.nj.us",
        "jurisdiction": JurisdictionType.NJ_COUNTY,
        "portal_vendor": PortalVendor.CUSTOM_HTML,
        "bid_list_url": "https://www.co.bergen.nj.us/procurement/current-bids",
        "scraper_class": "custom_html",
        "active": True,
        "priority": 7,
        "expected_monthly_postings": 10,
        "config": {
            "enable_javascript": False,
            "selectors": {
                "bid_items": ".bid-row",
                "title": ".bid-title",
                "due_date": ".due-date"
            }
        }
    }
]
```

**Export to Excel for review:**
```bash
docker-compose exec backend python scripts/export_registry_to_excel.py
```

### Spreadsheet Workflow

**Use the provided CSV templates:**

1. **source-registry-template.csv** - Master list of all sources
   - Update weekly as you discover new entities
   - Track verification status
   - Note portal vendors

2. **discovery-checklist.csv** - Discovery progress tracker
   - Mark entities as you investigate them
   - Track which need portal detection
   - Prioritize by importance

3. **coverage-scorecard-template.csv** - Weekly health monitoring
   - Generated automatically each week
   - Review anomalies
   - Validate sample manually

**Workflow:**
```
Monday morning:
1. Export source registry to Excel
2. Review last week's coverage scorecard
3. Add 5-20 new sources from discovery checklist
4. Update expected_monthly_postings for sources with data

Daily:
1. Run daily operations script
2. Check for scraper failures
3. Investigate anomalies

Weekly:
1. Generate coverage scorecard
2. Run entity discovery for new counties/cities
3. Build adapters for common portal vendors
```

## Phase 4: Coverage Verification (Ensuring 100%)

### Cross-Check Methodology

**1. Historical Baselines**
- Track average postings per month per source
- Flag variance > 50% from expected
- Example: NYC PASSPort usually posts ~50/month, if you see 10, investigate

**2. Sentinel Keywords**
- Search your tenders for: "construction", "building", "HVAC", "plumbing"
- If sentinel hits drop sharply, you likely lost a source

**3. Manual Sampling**
- Every week, randomly pick 10 sources
- Visit their portal manually
- Count open bids
- Compare to your system's count
- Should match ±2

**4. Aggregator Spot-Check**
- Monthly: sample 20 bids from BidNet/DemandStar
- Check if they exist in your system
- If missing, trace back to source

**5. Entity Count Verification**
- NYC: 40+ agencies
- NJ State: 20+ agencies/authorities
- NJ Counties: 21 counties
- NJ Cities: 15+ major cities
- NJ School Districts: 10+ large districts
- Total target: **100-150 active sources**

### Anomaly Detection

**Automated alerts for:**
- **Zero results** when expected > 0
- **High failure rate** (>50% of scrapes failing)
- **Low count** (<50% of expected)
- **High count** (>200% of expected - check for duplicates)

**Weekly scorecard shows:**
```bash
docker-compose exec backend python scripts/generate_weekly_scorecard.py
```

Output:
```
⚠️  Anomalies detected:

  NJ Treasury (custom_html)
    Type: zero_results
    Expected: 40, Actual: 0
    → Action: Check if page structure changed

  Newark (opengov)
    Type: low_count
    Expected: 15, Actual: 7
    → Action: Verify manually - may be legitimate
```

## Phase 5: Scaling Operations

### Weekly Entity Addition Target

**Goal: Add 5-20 new sources per week**

**Week 1-4: High Priority (Priority 8-10)**
- NYC PASSPort ✅
- NJSTART ✅
- NJDOT/BidExpress ✅
- NJ Transit
- Port Authority NY/NJ
- NYC DDC
- NYC DEP
- NYC DOT

**Week 5-8: Medium Priority (Priority 6-7)**
- Major NJ counties (Bergen, Essex, Hudson, Middlesex, Passaic, Union)
- Major NJ cities (Newark, Jersey City, Elizabeth, Paterson)
- NJ authorities (NJEDA, Turnpike, Sports Authority)

**Week 9-12: Lower Priority (Priority 4-5)**
- Smaller NJ counties
- Medium NJ cities
- School districts
- Special districts

**Ongoing:**
- Add sources as discovered
- Respond to user-reported missing opportunities
- Expand to NY counties/cities

### Portal Adapter Development

**As you discover patterns, build adapters:**

**Already built:**
- NYC PASSPort scraper
- NYS OGS scraper

**To build (in order of ROI):**
1. **BidExpress adapter** - covers NJDOT, NJ Transit, many others (~10+ sources)
2. **OpenGov adapter** - covers Newark, many cities (~15+ sources)
3. **NJSTART adapter** - covers state agencies (~10+ sources)
4. **Custom HTML adapter** - template for simple listing pages (~30+ sources)
5. **ProcureNow adapter** - covers some cities (~5+ sources)
6. **Bonfire adapter** - covers modern platforms (~5+ sources)

## Phase 6: Operational Metrics

### Coverage KPIs

**Track weekly:**
- **Total sources in registry:** Target 100-150
- **Active sources:** >90% of total
- **Sources with 0 failures:** >80%
- **Variance from expected:** <20% on average
- **Manual verification match rate:** >95%

**Dashboard view:**
```
📊 Coverage Dashboard - Week of Feb 24, 2026

Total Sources:        127
Active:               119 (94%)
Inactive:             8 (6%)

This Week:
  Tenders scraped:    1,847
  New tenders:        1,203
  Updated:            644

Health:
  Sources with anomalies:  7 (6%)
  Scrape success rate:     96%
  Manual verification:     97% match

Top Producers:
  1. NYC PASSPort:     287 tenders
  2. NJSTART:          156 tenders
  3. NJDOT:            98 tenders
```

### Quality Metrics

**Monitor:**
- **Parse accuracy:** Are dates/amounts extracted correctly?
- **Deduplication rate:** Are you creating duplicates?
- **Change detection:** Catching addenda/amendments?
- **AI enrichment quality:** Are summaries/tags accurate?

## Quick Reference Commands

### Daily Operations
```bash
# Run all scrapers
docker-compose exec backend python scripts/daily_operations.py

# Check recent scrape runs
curl http://localhost:8000/api/v1/admin/scrape-runs

# Export registry to Excel
docker-compose exec backend python scripts/export_registry_to_excel.py
```

### Weekly Operations
```bash
# Generate coverage scorecard
docker-compose exec backend python scripts/generate_weekly_scorecard.py

# Discover new entities
docker-compose exec backend python scripts/discover_entities.py

# Add new sources
docker-compose exec backend python scripts/seed_sources.py
```

### Manual Testing
```bash
# Test a single scraper
docker-compose exec backend python -c "
import asyncio
from app.scrapers.registry import registry

async def test():
    scraper = registry.create_scraper('nyc_passport')
    tenders = await scraper.scrape()
    print(f'Found {len(tenders)} tenders')
    await scraper.cleanup()

asyncio.run(test())
"

# Detect portal vendor
docker-compose exec backend python -c "
import asyncio
from app.discovery.portal_detector import PortalDetector

async def detect():
    detector = PortalDetector()
    vendor = await detector.detect_portal_vendor('YOUR_URL_HERE')
    print(f'Vendor: {vendor}')
    await detector.close()

asyncio.run(detect())
"
```

## Troubleshooting

### "Source has 0 results but should have some"

**Checklist:**
1. Visit portal manually - are there actually bids posted?
2. Check scraper logs for errors
3. Test CSS selectors still match
4. Verify no CAPTCHA/authentication added
5. Check if portal vendor changed

### "Portal vendor detection returns 'unknown'"

**Checklist:**
1. Check if it's a known vendor with custom domain
2. Manually inspect page source for vendor signatures
3. Look for "powered by" text in footer
4. Check network tab for API endpoints
5. Add to portal detector if new pattern found

### "Scraper failing with JavaScript errors"

**Fix:**
1. Set `enable_javascript: true` in source config
2. Add `wait_for_selector` for dynamic content
3. Increase `delay_before_return_html`
4. Use Crawl4AI's JavaScript execution features

### "High duplicate rate"

**Fix:**
1. Check fingerprint generation logic
2. Verify source_url is stable (not session-specific)
3. Look for duplicate sources scraping same portal
4. Add normalization to title before fingerprinting

## Next Steps

**Immediate (This Week):**
1. ✅ Implement source registry database
2. ✅ Integrate Crawl4AI
3. ⬜ Build BidExpress adapter (high ROI)
4. ⬜ Add 10 high-priority sources

**Short-term (Next 2 Weeks):**
1. ⬜ Build OpenGov adapter
2. ⬜ Add 20 medium-priority sources
3. ⬜ Set up weekly scorecard automation
4. ⬜ Manual verification of top 20 sources

**Long-term (Next Month):**
1. ⬜ Reach 100 active sources
2. ⬜ Build remaining portal adapters
3. ⬜ Achieve 95%+ coverage match rate
4. ⬜ Implement user feedback loop

## Resources

- **Implementation Plan:** `docs/plans/2026-02-27-source-discovery-master-plan.md`
- **Daily Checklist:** `docs/operations/DAILY_CHECKLIST.md`
- **Source Registry Template:** `docs/templates/source-registry-template.csv`
- **Discovery Checklist:** `docs/templates/discovery-checklist.csv`
- **Coverage Scorecard:** `docs/templates/coverage-scorecard-template.csv`
