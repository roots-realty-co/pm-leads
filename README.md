# pm-leads

Automated lead generation pipeline for Roots Realty PM, a Denver residential property management company. Two parallel channels: owner leads from Zillow and referral partnerships with local real estate agents via LinkedIn.

## Channels

### Channel 1: Zillow Owner Leads
Scrape Zillow rental listings, identify DIY landlords (not using a PM company), enrich their contact info, and run cold email outreach.

**Pipeline:** Apify → Supabase → n8n → Clay → Instantly.ai

**Status:** `isListedByOwner` filter returning 0 results — active blocker.

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
2. Test Clay enrichment match rate on name + phone
3. Build n8n pipeline

**Channel 2**
1. Monitor Heyreach campaign acceptance and reply rates
2. Decide referral tracking approach (Supabase vs. CRM)
3. Run next LinkedIn scrape when v1 campaign winds down
