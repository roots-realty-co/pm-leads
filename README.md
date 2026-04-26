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

## Scripts

### `zillow_scraper.py`
Calls Apify Zillow scraper, filters for owner-listed rentals, outputs CSV.

### `flatten_profiles.py`
Filters Apify LinkedIn profile data down to residential agents and outputs a Heyreach-ready CSV.

Input: `dataset_linkedin-profile-search_*.json` (Apify export, gitignored)
Output: `heyreach_import.csv`

Filter logic:
- Excludes: commercial, business brokers, mortgage, capital, healthcare, admin roles
- Includes: Realtor, broker associate, residential brokerages (Keller Williams, Coldwell, RE/MAX, Compass, etc.)
- Excludes: Acorn and Oak (competitor)

## Database Schema (Supabase — not yet created)

```sql
CREATE TYPE property_type AS ENUM (
  'sfr', 'duplex', 'triplex',
  'fourplex', 'apartment', 'condo', 'townhouse'
);

CREATE TYPE outreach_status AS ENUM (
  'not_contacted', 'emailed', 'replied',
  'call_booked', 'signed', 'dead'
);

CREATE TABLE listings (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  address_1         TEXT NOT NULL,
  city              TEXT,
  zip_code          TEXT,
  property_type     property_type,
  bedroom_count     INT,
  bathroom_count    INT,
  sqft              INT,
  advertised_rent   INT,
  owner_name        TEXT,
  owner_email       TEXT,
  owner_phone       TEXT,
  source            TEXT,
  listing_url       TEXT,
  is_diy            BOOLEAN,
  first_seen_date   TIMESTAMP DEFAULT now(),
  last_seen_date    TIMESTAMP DEFAULT now(),
  times_seen        INT DEFAULT 1,
  outreach_status   outreach_status DEFAULT 'not_contacted',
  notes             TEXT,
  created_at        TIMESTAMP DEFAULT now()
);
```

## Key Zillow Data Fields

| Field | Notes |
|-------|-------|
| `isListedByOwner` | Boolean — `true` = DIY landlord |
| `attributionInfo.brokerPhoneNumber` | Owner phone when no agent |
| `postingContact.name` | Owner name |
| `daysOnZillow` | Clean integer |
| Email | Not in Zillow — requires Clay enrichment |

## Channel 1 Next Steps

1. Fix `isListedByOwner` filter in `zillow_scraper.py`
2. Get clean CSV with 20-30 owner leads
3. Test Clay enrichment match rate on name + phone
4. Run Supabase schema
5. Build n8n pipeline

## Channel 2 Next Steps

1. Monitor Heyreach campaign — track connection acceptance rate and replies
2. Decide referral tracking approach (Supabase table vs. CRM)
3. Run next LinkedIn scrape when v1 campaign winds down
