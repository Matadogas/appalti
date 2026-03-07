# Tri-State Governmental Entities List

## Overview

This comprehensive list contains **300+ governmental entities** across New York, New Jersey, and Connecticut that may publish construction RFP/RFQ/IFB opportunities.

## File: tristate-entities-comprehensive.csv

### Coverage Statistics

**New Jersey (145 entities):**
- 21 counties
- 50+ cities/townships (all major municipalities)
- 15+ state/regional authorities
- 10 large school districts

**New York (100+ entities):**
- 18 counties (all downstate + major upstate)
- 40+ cities/towns (NYC boroughs + major municipalities)
- 20+ authorities (MTA, NYCHA, Port Authority, etc.)
- 5 major school districts

**Connecticut (55+ entities):**
- 8 counties
- 30+ cities/towns (all major municipalities)
- 10+ authorities
- 7 school districts

**Bi-State (3 entities):**
- Port Authority of NY & NJ
- Delaware River Port Authority
- Waterfront Commission

### Data Structure

**Columns:**
- `state`: NY, NJ, CT, or BISTATE
- `entity_type`: county, city, township, authority, school_district
- `entity_name`: Official entity name
- `search_keywords`: Comma-separated search term variations
- `priority`: 1-10 (10 = highest priority, most RFPs expected)
- `population_tier`: mega, large, medium, small

### Priority Scoring

**10 - Critical (Must scrape first):**
- NYC and its agencies
- Port Authority NY/NJ
- Newark, Jersey City

**9 - Very High:**
- Major counties (Bergen, Essex, Hudson, Middlesex, Westchester, Nassau)
- NYC agencies (DDC, DEP, DOT, SCA)
- MTA, NYCHA

**8 - High:**
- Large cities (Elizabeth, Paterson, Stamford, Hartford)
- Major authorities (NJ Transit, Turnpike)

**7 - Medium-High:**
- Medium counties and cities
- Regional authorities

**6 and below - Medium to Low:**
- Smaller municipalities
- Specialized authorities
- School districts

## Usage for Automated Search

### Google Search Query Format

For each entity, construct queries like:

```
"{entity_name}" + (procurement OR purchasing OR bids OR "current bids" OR RFP OR RFQ OR IFB)
```

**Examples:**
```
"Bergen County NJ" procurement
"City of Newark" current bids
"Port Authority NY NJ" rfp
"Westchester County" purchasing
```

### Search Variations

Use the `search_keywords` column for variations:
```
"bergen county nj" procurement
"bergen county new jersey" bids
```

### Advanced Search Operators

```
site:.gov "Bergen County" procurement
site:nj.us "current bids"
site:ny.gov RFP construction
```

### Python Script Usage

See `backend/scripts/automated_entity_search.py` for automated search implementation.

## Entity Selection Strategy

### Phase 1: High-Value Entities (Weeks 1-4)
Focus on priority 8-10:
- NYC agencies (10 entities)
- Major NJ/NY counties (12 entities)
- Top authorities (10 entities)
**Target: 30-40 sources**

### Phase 2: Medium-Value Entities (Weeks 5-8)
Priority 6-7:
- Medium counties (20 entities)
- Major cities (25 entities)
- Regional authorities (15 entities)
**Target: 60 additional sources**

### Phase 3: Comprehensive Coverage (Weeks 9-12)
Priority 4-5:
- Smaller municipalities (50+ entities)
- School districts (20 entities)
- Specialized authorities (15 entities)
**Target: 85 additional sources**

### Total Coverage Target
**175-200 active sources** across tri-state area

## Data Maintenance

### Quarterly Updates
- Add newly discovered entities
- Update priority scores based on RFP volume
- Add new authorities/districts
- Update search keywords based on findings

### Quality Checks
- Verify entity names match official names
- Test search keywords for effectiveness
- Update population tiers based on census data

## Related Files

- `discovery-checklist.csv` - Discovery progress tracker
- `source-registry-template.csv` - Master source inventory
- `backend/scripts/automated_entity_search.py` - Automated search script
- `backend/app/discovery/entity_finder.py` - Entity discovery service

## Notes

**Multiple townships with same name:**
Some NJ townships have the same name (e.g., Washington Township exists in 5 counties). Always include county in searches.

**NYC is special:**
NYC has 40+ agencies but procurement is centralized via PASSPort. Focus on major construction agencies:
- DDC (Department of Design & Construction)
- DEP (Environmental Protection)
- DOT (Transportation)
- SCA (School Construction Authority)
- H+H (Health + Hospitals)

**Connecticut counties:**
CT counties are administrative divisions with limited functions. Focus on cities/towns for procurement.

**Authorities vs Municipalities:**
Authorities are often separate legal entities with their own procurement. Don't skip them!

## Search Priority by RFP Volume

**Highest Volume (500+ RFPs/year):**
- NYC PASSPort (all agencies)
- Port Authority NY/NJ
- MTA

**High Volume (100-500 RFPs/year):**
- Major counties (Bergen, Essex, Nassau, Westchester)
- Large cities (Newark, Jersey City, Stamford)
- NJ Transit, NJDOT

**Medium Volume (50-100 RFPs/year):**
- Medium counties
- Medium cities
- Major school districts

**Lower Volume (<50 RFPs/year):**
- Small municipalities
- Specialized authorities
- Small school districts
