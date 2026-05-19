# Roots Realty — Operations Roadmap

---

## Now (May 2026)

**SMS Outreach**
- 10DLC campaign rejected — carriers require explicit opt-in consent, cold outreach from public listings does not qualify
- Path forward: Hillary does initial outreach manually (call or personal text). Once a lead replies, they've engaged and can be moved into the automated follow-up flow via Twilio.
- sms_followup.py remains useful for tracking and follow-ups on warm leads
- Revisit automated cold SMS at scale when volume exceeds what Hillary can touch manually (2,000+ leads/mo)

**Newsletter**
- First automated delivery: Monday 2026-05-18
- Tune sources and prompt based on what resonates
- Ozzy and Hillary steer content direction over time

---

## Next (Q2 2026)

**Supabase: Core Schema**

Three tables replacing CSVs and Google Sheets as the source of truth.

`landlord_leads`
- name, phone, email
- address_1, address_2, city, state, zip
- bedroom_count, bathroom_count, square_footage
- rent (numeric)
- fee (numeric)
- service_type (enum: management, lease_only)
- lead_source (enum: zillow, nomad, agent_referral, friends_family, management_company, inbound)
- referring_agent_id (nullable UUID FK to agents — only when lead_source = agent_referral)
- status (enum: new, contacted, replied, qualified, won, lost)
- lost_reason (enum: price, timing, went_another_direction, selling, roots_decision, unresponsive, other)
- lost_notes (freeform text)
- management_start_date
- created_at, created_by, updated_at, updated_by
- UNIQUE (email, address_1) — one owner can have multiple properties (same email, different address) but the same property cannot be entered twice

`agents`
- name, phone, email, linkedin_url, brokerage_firm
- source: linkedin, event, inbound
- status: pending, connected, nurturing, active_partner, deadend
- created_at, created_by, updated_at, updated_by

`interactions` (append only)
- lead_id FK, channel (sms, phone, email), type (initial_outreach, follow_up, reply, opt_out)
- message, timestamp
- Replaces sms_log.csv and optouts.csv
- Full audit trail — never update or delete
- created_at, created_by, updated_at, updated_by

**SMS Pipeline Migration**
- Migrate sms_utils.py from CSV to Supabase (I/O already isolated, migration is contained)
- Basic SMS reporting: reply rate, opt-out rate, follow-up conversion

**Zillow Scraper Automation**
- Move from manual trigger to monthly Lambda schedule
- Same EventBridge pattern as the newsletter

---

## Later (Q3 2026+)

**CRM Reporting**
- SQL queries against Supabase for pipeline visibility
- Which agents have sent referrals, how many converted
- Lead funnel: new → contacted → replied → qualified → won
- SMS performance by message template and send timing

**LinkedIn Feedback Loop**
- Track which connected agents converted to active referral partners
- Expand to new geographies (Boulder, Fort Collins, Colorado Springs) as Denver saturates

**Referral Partner Campaigns (post June 30, one at a time)**

Run sequentially through Heyreach after the Denver agent campaign winds down. Same playbook as agents — lead with client value, not referral fees. Warm up each campaign with a LinkedIn post first.

Rank order:
1. **Loan Brokers** (LinkedIn industry ID: 1696) — highest intent, in the transaction when an investor buys. They can mention Roots at the exact right moment.
2. **Accounting** (LinkedIn industry ID: 47) — CPAs advise on buy decisions and tax strategy. Natural fit for cost seg and REPS content angle.
3. **Law Practice** (LinkedIn industry ID: 9) — real estate attorneys see transactions happen. SBWP relationship already warm.
4. **Investment Advice** (LinkedIn industry ID: 1720) — financial advisors manage the wealth and refer the PM. Longer relationship cycle, lower urgency.

Note: confirm industry IDs with Apify before scraping — CSV IDs may differ from what Apify uses. ID 44 = Real Estate, 47 = Accounting in LinkedIn's taxonomy.

Add each as a lead_source value in Supabase schema when built.

**Newsletter: Agent Distribution**
- If social posts are working, evolve into a direct weekly email to agent list
- "Denver PM Pulse" — becomes a relationship touchpoint that compounds over time
- Differentiator: Roots POV content (internal data, cost seg takes, market observations)

---

## Conventions

**created_by / updated_by**
Every row identifies what created or last modified it:
- `WES_SQL` — manual update by Ozzy directly in Supabase
- `zillow_scraper` — Zillow pipeline
- `sms_outreach` — SMS outreach script
- `sms_followup` — SMS follow-up script
- `newsletter` — newsletter pipeline
- Add new service identifiers as new scripts are built

---

## Decisions Deferred

- Newsletter does not need a DB — it's a broadcast, not a CRM function. Revisit if it becomes direct email.
- No dedicated referrals table — referrals are landlord_leads with lead_source = agent_referral and a referring_agent_id.
- Supabase replaces Google Sheets for leads storage eventually, but Sheets stays until Supabase is validated.
