# pm-leads

Automated lead generation pipeline for Roots Realty PM, a Denver residential property management company. Two parallel channels: owner leads from Zillow and referral partnerships with local real estate agents via LinkedIn.

## Channels

### Channel 1: Zillow Owner Leads
Scrape Zillow rental listings, identify DIY landlords (not using a PM company), enrich their contact info, and reach out directly.

**Current pipeline:** Apify → Google Sheet → manual texting

**Blockers**
- `isListedByOwner` filter in `zillow_scraper.py` returns 0 results — Zillow data shape needs investigation.
- No enrichment solution found yet. We have owner phone numbers from Zillow but cannot reliably reverse-lookup an email from a phone number. Clay, and others tested so far, have poor match rates for this specific input.

**Future pipeline (aspirational):** Apify → Supabase → n8n → enrichment → Instantly.ai (cold email)

**Path forward**
1. Fix `isListedByOwner` filter to get clean owner lead data
2. Keep testing enrichment tools — need one that can reliably go phone → email for individual landlords
3. If email enrichment remains unsolvable, stand up an SMS campaign instead — requires researching A2P 10DLC registration rules and compliance for automated texting in Colorado

### Channel 2: RA Agent Referrals
Find Denver residential real estate agents on LinkedIn, connect via automated outreach, and build referral partnerships. Agents send investor clients our way in exchange for referral fees.

**Pipeline:** Apify (LinkedIn scrape) → Python filter → Heyreach

**Status:** Campaign live as of 2026-04-26. 113 agents, running through 2026-06-30.

## Tech Stack

| Tool | Purpose |
|------|---------|
| **Apify** | Scraping (Zillow listings + LinkedIn profiles) |
| **Supabase** | Postgres database |
| **n8n** | Workflow automation |
| **Clay** | Contact enrichment (name + phone to email) |
| **Instantly.ai** | Cold email sequences |
| **Heyreach** | LinkedIn outreach automation |
| **Python** | Data processing and glue scripts |

## Next Steps

**Channel 1**
1. Fix `isListedByOwner` filter
2. Continue testing enrichment tools for phone to email lookup
3. Research A2P 10DLC compliance if pivoting to SMS outreach

**Channel 2**
1. Monitor Heyreach campaign acceptance and reply rates
2. Decide referral tracking approach (Supabase vs. CRM)
3. Run next LinkedIn scrape when v1 campaign winds down
