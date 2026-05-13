# Roots Realty — Operations Roadmap

---

## Now (May 2026)

**SMS Outreach**
- 10DLC pending approval (~2026-05-15)
- Once approved: run sms_outreach.py against all 393 Zillow leads from 2026-05-02
- Monitor reply rates, refine message templates

**Newsletter**
- First automated delivery: Monday 2026-05-18
- Tune sources and prompt based on what resonates
- Ozzy and Hillary steer content direction over time

---

## Next (Q2 2026)

**Supabase: Core Schema**

Three tables replacing CSVs and Google Sheets as the source of truth.

`landlord_leads`
- name, phone, email, address
- lead_source: zillow, agent_referral, inbound
- referring_agent_id: nullable FK to agents (only when lead_source = agent_referral)
- status: new, contacted, replied, qualified, won
- pm_start_date

`agents`
- name, phone, email, linkedin_url
- source: linkedin, event, inbound
- status: connected, nurturing, active_partner

`interactions` (append only)
- lead_id FK, channel (sms, phone, email), type (outreach, follow_up, reply, opt_out)
- message, timestamp
- Replaces sms_log.csv and optouts.csv
- Full audit trail — never update or delete

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

**Newsletter: Agent Distribution**
- If social posts are working, evolve into a direct weekly email to agent list
- "Denver PM Pulse" — becomes a relationship touchpoint that compounds over time
- Differentiator: Roots POV content (internal data, cost seg takes, market observations)

---

## Decisions Deferred

- Newsletter does not need a DB — it's a broadcast, not a CRM function. Revisit if it becomes direct email.
- No dedicated referrals table — referrals are landlord_leads with lead_source = agent_referral and a referring_agent_id.
- Supabase replaces Google Sheets for leads storage eventually, but Sheets stays until Supabase is validated.
