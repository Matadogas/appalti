# Bing Search API Setup Guide

## Why Bing Search API?

- ✅ **Free tier:** 1,000 searches/month
- ✅ **Fast:** 3 searches/second
- ✅ **Comprehensive:** Will find 200-300 NJ portals
- ✅ **Better than Google CSE:** No "search entire web" restriction
- ✅ **Quick setup:** ~5 minutes

## Cost Analysis

### For NJ Discovery
- **145 NJ entities × 3 queries = 435 searches**
- **Free tier:** 1,000/month = ✅ **Completely FREE**
- **Time:** ~2 minutes for 435 searches

### For Full Tri-State (NY + NJ + CT)
- **229 entities × 3 queries = 687 searches**
- **Free tier:** 1,000/month = ✅ **Still FREE**
- **Time:** ~3-4 minutes

## Setup Steps

### Step 1: Create Azure Account (Free)

1. Go to https://portal.azure.com
2. Click "Sign in" or "Start free"
3. Use your Microsoft account (or create one)
4. **No credit card required for free tier**

### Step 2: Create Bing Search Resource

1. In Azure Portal, click "Create a resource"
2. Search for **"Bing Search v7"**
3. Click "Create"
4. Fill in:
   - **Subscription:** Your subscription
   - **Resource group:** Create new: `appalti-discovery`
   - **Region:** East US (or closest to you)
   - **Name:** `appalti-bing-search`
   - **Pricing tier:** **F1 (Free)** ✅
     - 1,000 searches/month
     - 3 calls/second
     - **$0/month**

5. Click "Review + Create"
6. Click "Create"
7. Wait ~1 minute for deployment

### Step 3: Get API Key

1. After deployment, click "Go to resource"
2. In left menu, click **"Keys and Endpoint"**
3. Copy **"KEY 1"** (looks like: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)
4. Save it somewhere safe

### Step 4: Add to .env File

Open `C:\Users\tonilore\Desktop\Appalti\.env` and add:

```env
# Bing Search API
BING_SEARCH_API_KEY=YOUR_KEY_HERE
```

Replace `YOUR_KEY_HERE` with your actual key from Step 3.

### Step 5: Test the API

```bash
cd backend/scripts
python discover_nj_bing.py --test --api-key YOUR_KEY_HERE
```

**Expected output:**
```
TEST MODE: Running sample Bing search...

Success! Found 5 results:

1. Bergen County - Purchasing
   URL: https://www.co.bergen.nj.us/procurement
   Snippet: Bergen County Purchasing Department handles all procurement...

2. ...

✓ Bing Search API is working!
```

If you see "✓ Bing Search API is working!" - you're ready to go!

## Usage

### Test with 5 Entities (FREE)

```bash
cd backend/scripts
python discover_nj_bing.py \
  --api-key YOUR_KEY \
  --max-entities 5
```

**Cost:** FREE (15 searches)
**Time:** ~5 seconds
**Expected:** 15-30 candidate portals

### Full NJ Discovery (FREE)

```bash
cd backend/scripts
python discover_nj_bing.py \
  --api-key YOUR_KEY
```

**Cost:** FREE (435 searches under 1,000 limit)
**Time:** ~2 minutes
**Expected:** 200-300 candidate portals

### Custom Configuration

```bash
python discover_nj_bing.py \
  --api-key YOUR_KEY \
  --queries-per-entity 5 \
  --max-entities 50 \
  --output custom_output.csv
```

Options:
- `--queries-per-entity N` - Searches per entity (default: 3)
- `--max-entities N` - Limit entities (for testing)
- `--output FILE` - Output CSV path

## Troubleshooting

### Error: "Invalid API Key"

**Fix:**
1. Check you copied the full key from Azure
2. Make sure it's in `.env` or passed via `--api-key`
3. Verify the key is for "Bing Search v7" (not other services)

### Error: "Rate limit exceeded"

**Fix:**
- Free tier: 3 calls/second max
- Script automatically handles rate limiting
- If issue persists, wait 1 minute and retry

### Error: "Quota exceeded"

**Cause:** Used all 1,000 free searches this month

**Solutions:**
1. **Wait:** Quota resets monthly
2. **Upgrade to S1:** $7/1000 searches (only if needed)

### No Results Found

**Check:**
1. Entity names are correct in CSV
2. Search queries are relevant
3. Increase `--queries-per-entity` to 5

## What's Next?

After running discovery:

### 1. Review Results

```bash
# Open the CSV
cat nj_portals_bing_discovery.csv
```

**You should see:**
- 200-300 unique portals
- 60%+ government domains (.gov, .us)
- Relevance scores 0-100
- Priority rankings 1-10

### 2. Validate URLs

```bash
python validate_candidates.py \
  --input nj_portals_bing_discovery.csv \
  --output nj_portals_validated.csv
```

This checks which URLs are actually accessible.

### 3. Extract Construction RFPs

```bash
python extract_nj_construction_rfps.py \
  --input nj_portals_validated.csv \
  --output nj_construction_rfps_final.csv
```

Extracts actual construction bid listings.

### 4. Start Scraping

Use Crawl4AI to scrape the validated portals and extract RFPs.

## Comparison: Bing vs Google CSE

| Feature | Bing Search | Google CSE |
|---------|-------------|------------|
| **Free tier** | 1,000/month | 100/day = 3,000/month |
| **Setup** | 5 minutes | 10 minutes |
| **Restrictions** | None | "Search entire web" deprecated |
| **Rate limit** | 3/second | 100/day burst |
| **Quality** | Excellent | Excellent |
| **For NJ (435 queries)** | ✅ FREE | ✅ FREE (5 days) |
| **Recommendation** | ✅ **Use this** | ⚠️ Has issues |

**Verdict:** Bing is better - no CSE restrictions, same free tier, easier setup.

## Cost Projections

### If You Need More Than Free Tier

**Bing Search S1 Tier:**
- **Price:** $7 per 1,000 searches
- **Rate limit:** 10 calls/second

**For all tri-state:**
- 229 entities × 5 queries = 1,145 searches
- Cost: ~$8
- Time: ~4 minutes

**For all phases (4,003 queries from original plan):**
- Cost: ~$28
- Time: ~20 minutes

**Comparison to SerpAPI:**
- SerpAPI: $50/month (5,000 searches)
- Bing S1: Pay per use ($7/1,000)
- **Bing is cheaper** if you only need ~2,000 searches

## Support

**Azure Support:**
- Docs: https://learn.microsoft.com/azure/cognitive-services/bing-web-search/
- Portal: https://portal.azure.com

**Issues?**
- Check Azure resource is running
- Verify billing (free tier needs billing enabled, but won't charge)
- Review API usage in Azure Portal → Your Resource → Metrics

## Summary

✅ **Free:** 1,000 searches/month
✅ **Fast:** 5-minute setup
✅ **Covers NJ:** 435 searches = under free limit
✅ **Better than Google:** No restrictions
✅ **Ready to use:** Just get API key and run

**Next:** Get your API key and run the test!

```bash
python discover_nj_bing.py --test --api-key YOUR_KEY
```
