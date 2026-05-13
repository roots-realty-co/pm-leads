"""
sms_outreach.py — Send personalized SMS to Zillow owner leads via Twilio.

Reads leads from Google Sheets, skips anyone already contacted or opted out,
sends Hillary's intro text, and logs every send to sms_log.csv.

Required .env vars:
    SPREADSHEET_ID        — Google Sheet ID with Zillow leads
    TWILIO_ACCOUNT_SID    — Twilio account SID
    TWILIO_AUTH_TOKEN     — Twilio auth token
    TWILIO_FROM_NUMBER    — Your Twilio number (e.g. +17205551234)

Usage:
    python3 sms_outreach.py           # sends up to DAILY_LIMIT messages
    python3 sms_outreach.py --dry-run # preview without sending
"""

import os
import sys
from dotenv import load_dotenv
from twilio.rest import Client

from sms_utils import (
    SMS_LOG, OPTOUT_LOG,
    normalize_phone, load_sheet, load_contacted,
    load_optouts, log_send,
)

load_dotenv()

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
ACCOUNT_SID    = os.environ["TWILIO_ACCOUNT_SID"]
AUTH_TOKEN     = os.environ["TWILIO_AUTH_TOKEN"]
FROM_NUMBER    = os.environ["TWILIO_FROM_NUMBER"]

DAILY_LIMIT = 30
DRY_RUN     = "--dry-run" in sys.argv

MESSAGE_TEMPLATE = (
    "Hi, my name is Hillary - I'm the managing broker of Roots Realty in Denver. "
    "I saw your property at {address} on Zillow and wanted to reach out - "
    "if you ever need help leasing or managing it, I'd be happy to help."
)


def main():
    print(f"{'[DRY RUN] ' if DRY_RUN else ''}Loading leads from Google Sheets...")
    leads = load_sheet(SPREADSHEET_ID)
    print(f"  {len(leads)} total leads in sheet")

    contacted = load_contacted()
    print(f"  {len(contacted)} already contacted")

    twilio = None if DRY_RUN else Client(ACCOUNT_SID, AUTH_TOKEN)

    print("Checking opt-outs...")
    optouts = load_optouts(twilio, FROM_NUMBER)
    print(f"  {len(optouts)} opted out")

    sent = skipped_no_phone = skipped_already_contacted = skipped_optout = 0

    for lead in leads:
        if sent >= DAILY_LIMIT:
            print(f"\nDaily limit of {DAILY_LIMIT} reached. Run again tomorrow.")
            break

        phone = normalize_phone(lead.get("owner_phone") or lead.get("phone"))

        if not phone:
            skipped_no_phone += 1
            continue
        if phone in contacted:
            skipped_already_contacted += 1
            continue
        if phone in optouts:
            skipped_optout += 1
            continue

        address = lead.get("address") or lead.get("address_1") or "your property"
        body = MESSAGE_TEMPLATE.format(address=address)

        print(f"\n→ {phone} | {address}")
        print(f"  {body}")

        if DRY_RUN:
            log_send(phone, address, "dry_run")
        else:
            try:
                msg = Client(ACCOUNT_SID, AUTH_TOKEN).messages.create(
                    from_=FROM_NUMBER, to=phone, body=body
                )
                log_send(phone, address, "sent")
                print(f"  ✓ Sent ({msg.sid})")
            except Exception as e:
                log_send(phone, address, f"error: {e}")
                print(f"  ✗ Failed: {e}")

        sent += 1

    print(f"\n── Summary ──────────────────────────")
    print(f"  Sent:                {sent}")
    print(f"  No phone number:     {skipped_no_phone}")
    print(f"  Already contacted:   {skipped_already_contacted}")
    print(f"  Opted out:           {skipped_optout}")
    print(f"  Log:                 {SMS_LOG}")
    print(f"  Opt-out list:        {OPTOUT_LOG}")


if __name__ == "__main__":
    main()
