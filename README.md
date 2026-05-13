# Roots Realty PM — Operations

Automated pipelines for Roots Realty, a Denver residential property management company. Lead generation (Zillow and LinkedIn) and content marketing (weekly social post candidates).

---

## Channel 1: Zillow Owner Leads

Find DIY landlords renting their properties without a PM company and reach out directly.

**How it works:**
1. `pm_leads/zillow_scraper.py` runs monthly (manually triggered)
2. Hits Apify in two stages: zip code search → detail scraper on individual listings
3. Filters for `isListedByOwner = true` AND a phone number present
4. Writes results to a dated CSV (`zillow_leads_YYYY-MM-DD.csv`), appends to Google Sheet, posts Slack summary
5. Manual outreach via phone/text

**Run cadence:** Monthly

**Last run:** 2026-05-02 — 393 leads with phone numbers, Denver metro + Boulder

**Zip codes:** Full Denver metro (see `ZIP_CODES` in scraper) + Boulder. Excludes Aurora, Westminster, Broomfield, Thornton, and Louisville/Lafayette/Superior/Erie.

**Filters:**
- For rent only, min $2,000/mo
- `isListedByOwner = true`
- Must have a phone number (broker or agent)

**Apify actors:**
- `maxcopell~zillow-zip-search` — finds listing URLs by zip code
- `maxcopell~zillow-detail-scraper` — scrapes full listing data

**Infrastructure:**
- Google Sheet: `14t-FWQKJVN3zsIoA-QB1-ZryS4Tw2Njiw_H4mR3-vIw`
- Service account: `zillow-leads@pm-leads.iam.gserviceaccount.com` (editor on sheet)
- AWS Lambda: `zillow-leads-slack-summary` (dormant — Slack now handled by the scraper directly)
- Credentials: `pm_leads/service_account.json` (gitignored)

**Blockers:**
- No enrichment solution for phone → email. Clay and others tested, poor match rates for individual landlords.
- If email enrichment remains unsolvable, SMS outreach via A2P 10DLC is the path forward (requires compliance research for Colorado).

---

## Channel 2: LinkedIn Agent Referrals

Find Denver-area residential real estate agents on LinkedIn, connect via automated outreach, and build referral partnerships. Agents refer investor clients in exchange for referral fees.

**How it works:**
1. Run Apify LinkedIn Profile Search actor (industry ID 1770 — Real Estate Agents and Brokers)
2. Download JSON dataset, drop in `pm_leads/Datasets/`
3. From inside `pm_leads/Datasets/`, run `python3 ../flatten_profiles.py` — it picks up all `dataset_linkedin-profile-search_*.json` files in the current directory, filters for residential agents, dedupes by LinkedIn URL, and outputs `heyreach_import_YYYY-MM-DD.csv` in that same folder
4. Import CSV into Heyreach as a new list, add to campaign

**Run cadence:** As needed (when current campaign winds down or a new geography is ready)

**Campaigns:**
- Denver metro v1: 113 agents, live 2026-04-26, running through 2026-06-30
- Denver metro + suburbs v2: 123 agents added 2026-05-02

**Apify actor input:**
- Industry ID: `1770` (Real Estate Agents and Brokers)
- Location: target city (e.g. `Denver, Colorado`, `Boulder, Colorado`, etc.)
- Keep broad — no additional filters

**Deduplication:** Handled at three layers — Python script (by LinkedIn URL within dataset), Heyreach (at import), Heyreach campaign exclude options.

**Heyreach webhooks (2 active):**
- `connection_accepted` — fires on all campaigns when a connection request is accepted
- `message_reply` — fires on every message/InMail reply received
- Both post to the Lambda Function URL (`lambda_heyreach_slack_notifications.py`) which forwards to Slack

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| **Apify** | Scraping (Zillow listings + LinkedIn profiles) |
| **Python** | Data processing and pipeline glue |
| **Google Sheets** | Zillow leads storage and review |
| **AWS Lambda** | Heyreach webhook listener (active) + Zillow Slack summary (dormant) |
| **Heyreach** | LinkedIn outreach automation |
| **Slack** | Zillow run summaries + Heyreach notifications + weekly newsletter candidates |
| **Claude API** | Generates social post candidates for newsletter pipeline |

---

## Scripts

| Script | Purpose |
|--------|---------|
| `pm_leads/zillow_scraper.py` | Full Zillow pipeline — scrape, filter, CSV, sheet, Slack |
| `pm_leads/flatten_profiles.py` | Process LinkedIn JSON → Heyreach CSV |
| `pm_leads/lambda_heyreach_slack_notifications.py` | AWS Lambda — Heyreach webhook → Slack notifications (active) |
| `pm_leads/lambda_zillow_leads_slack_sheets.py` | AWS Lambda — Zillow Slack summary (dormant) |

---

---

## Newsletter: Weekly Social Post Candidates

Automated pipeline that surfaces content for LinkedIn and Instagram every Monday morning. Goal: keep Roots top of mind with Denver agents so they refer investor clients for property management.

**How it works:**
1. Pulls the 3 most recent articles from 7 RSS sources
2. Sends them to Claude API to select the 3-5 most relevant topics and draft post candidates
3. Posts a summary to Slack `#content` with each candidate as a thread reply

**Run cadence:** Every Monday at 8am MDT (automated)

**RSS sources:**
- BiggerPockets
- Zillow Research
- Colorado Association of Realtors
- SBWP Law (Springman, Braden, Wilson & Pontius) — Colorado landlord-tenant law
- RentCafe
- RentCast (via Google News)
- Colorado landlord-tenant law news (via Google News)

**Post format:**
- LinkedIn: 100-200 words, analytical, agent and investor audience
- Instagram: 30-60 words, punchy, local, conversational

**Infrastructure:**
- AWS Lambda: `claudtent-creator`
- EventBridge schedule: `cron(0 14 ? * MON *)` — 8am MDT (adjust to `cron(0 15 ? * MON *)` in winter)
- Slack: posts to `#content` channel

**Scripts:**
- `newsletter/lambda_newsletter.py` — Lambda function (deployed)
- `newsletter/newsletter.py` — local version for testing
- `newsletter/deploy.sh` — packages dependencies and zips for Lambda upload

---

## Next Steps

**Channel 1**
1. Manual outreach on 393 phone leads from 2026-05-02 run
2. Keep testing phone → email enrichment tools
3. Research A2P 10DLC compliance if pivoting to SMS

**Channel 2**
1. Monitor Heyreach campaign acceptance and reply rates
2. Run next scrape when v1 campaign winds down or expand to new geography

**Newsletter**
1. Review first Monday delivery and adjust sources or prompt as needed
2. Track which post types resonate and refine over time
