# Roots Realty — Operations

Automated pipelines for Roots Realty, a Denver residential property management company. Lead generation, agent outreach, SMS, and content marketing.

---

## Zillow Owner Leads

Find DIY landlords renting without a PM company and reach out directly.

**How it works:**
1. `zillow/zillow_scraper.py` runs monthly (manually triggered)
2. Hits Apify in two stages: zip code search, then detail scraper on individual listings
3. Filters for `isListedByOwner = true` AND a phone number present
4. Writes results to a dated CSV, appends to Google Sheet, posts Slack summary
5. Manual outreach via phone/text or SMS pipeline

**Run cadence:** Monthly

**Last run:** 2026-05-02 — 393 leads with phone numbers, Denver metro + Boulder

**Zip codes:** Full Denver metro + Boulder. Excludes Aurora, Westminster, Broomfield, Thornton, Louisville, Lafayette, Superior, Erie.

**Filters:**
- For rent only, min $2,000/mo
- `isListedByOwner = true`
- Must have a phone number

**Apify actors:**
- `maxcopell~zillow-zip-search` — finds listing URLs by zip code
- `maxcopell~zillow-detail-scraper` — scrapes full listing data

**Infrastructure:**
- Google Sheet: `14t-FWQKJVN3zsIoA-QB1-ZryS4Tw2Njiw_H4mR3-vIw`
- Service account: `zillow-leads@pm-leads.iam.gserviceaccount.com` (editor on sheet)
- Credentials: `zillow/service_account.json` (gitignored)

**Blockers:**
- No enrichment solution for phone to email. Clay and others tested, poor match rates for individual landlords.
- SMS outreach is the path forward (see SMS pipeline below).

---

## LinkedIn Agent Referrals

Find Denver residential real estate agents on LinkedIn, connect via automated outreach, and build referral partnerships. Agents refer investor clients in exchange for referral fees.

**How it works:**
1. Run Apify LinkedIn Profile Search actor (industry ID 1770)
2. Download JSON dataset, drop in `linkedin/Datasets/`
3. From inside `linkedin/Datasets/`, run `python3 ../flatten_profiles.py`
4. Import output CSV into Heyreach as a new list, add to campaign

**Run cadence:** As needed (when current campaign winds down or new geography is ready)

**Campaigns:**
- Denver metro v1: 113 agents, live 2026-04-26, running through 2026-06-30
- Denver metro + suburbs v2: 123 agents added 2026-05-02

**Apify actor input:**
- Industry ID: `1770` (Real Estate Agents and Brokers)
- Location: target city (e.g. `Denver, Colorado`)
- Keep broad, no additional filters

**Deduplication:** Python script (by LinkedIn URL), Heyreach at import, Heyreach campaign exclude options.

**Heyreach webhooks (2 active):**
- `connection_accepted` — posts to Slack via Lambda
- `message_reply` — posts to Slack via Lambda

---

## SMS Outreach

Send personalized SMS to Zillow owner leads who haven't been reached via phone.

**How it works:**
1. `sms/sms_outreach.py` reads uncontacted leads from Google Sheet, sends up to a daily limit via Twilio
2. `sms/sms_followup.py` sends follow-ups to leads who haven't replied after a set number of days
3. `sms/sms_utils.py` — shared utilities for both scripts

**Run cadence:** Daily (manual trigger for now)

**Status:** Scripts built. Blocked on A2P 10DLC registration for compliant mass SMS in Colorado.

---

## Newsletter: Weekly Social Post Candidates

Surfaces LinkedIn and Instagram post candidates every Monday morning. Goal: keep Roots top of mind with Denver agents so they refer investor clients.

**How it works:**
1. Pulls the 3 most recent articles from 7 RSS sources
2. Claude API selects the 3-5 most relevant topics and drafts post candidates
3. Posts a summary to Slack `#content` with each candidate as a thread reply
4. Ozzy and Hillary review, Hillary posts

**Run cadence:** Every Monday at 8am MDT (automated via Lambda)

**RSS sources:**
- BiggerPockets
- Zillow Research
- Colorado Association of Realtors
- SBWP Law (Springman, Braden, Wilson & Pontius)
- RentCafe
- RentCast (via Google News)
- Colorado landlord-tenant law (via Google News)

**Infrastructure:**
- AWS Lambda: `claudtent-creator`
- EventBridge: `cron(0 14 ? * MON *)` — 8am MDT. Use `cron(0 15 ? * MON *)` in winter (MST).
- Slack: posts to `#content`

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| **Apify** | Scraping (Zillow listings + LinkedIn profiles) |
| **Python** | Data processing and pipeline glue |
| **Google Sheets** | Zillow leads storage and review |
| **AWS Lambda** | Heyreach webhook listener + newsletter scheduler |
| **Heyreach** | LinkedIn outreach automation |
| **Twilio** | SMS outreach to Zillow leads |
| **Slack** | Run summaries, Heyreach notifications, newsletter candidates |
| **Claude API** | Generates social post candidates for newsletter |

---

## Scripts

| Script | Purpose |
|--------|---------|
| `zillow/zillow_scraper.py` | Full Zillow pipeline — scrape, filter, CSV, sheet, Slack |
| `zillow/lambda_zillow_leads_slack_sheets.py` | AWS Lambda — Zillow Slack summary (dormant) |
| `linkedin/flatten_profiles.py` | Process LinkedIn JSON → Heyreach CSV |
| `linkedin/lambda_heyreach_slack_notifications.py` | AWS Lambda — Heyreach webhook → Slack (active) |
| `sms/sms_outreach.py` | Send SMS to uncontacted Zillow leads via Twilio |
| `sms/sms_followup.py` | Send follow-up SMS to non-responders |
| `sms/sms_utils.py` | Shared SMS utilities |
| `newsletter/lambda_newsletter.py` | AWS Lambda — weekly newsletter (deployed) |
| `newsletter/newsletter.py` | Local version for testing |
| `newsletter/deploy.sh` | Package and zip for Lambda upload |

---

## Next Steps

**Zillow**
1. Manual outreach on 393 phone leads from 2026-05-02 run
2. Run monthly scrape when due

**LinkedIn**
1. Monitor Heyreach campaign acceptance and reply rates
2. Run next scrape when v1 campaign winds down or expand to new geography

**SMS**
1. Complete A2P 10DLC registration for compliant mass texting in Colorado
2. Once registered, run sms_outreach.py against Zillow leads

**Newsletter**
1. Review first Monday delivery (2026-05-18) and adjust sources or prompt as needed
2. Track which post types resonate and refine over time
