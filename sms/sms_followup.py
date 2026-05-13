"""
sms_followup.py — Send follow-up SMS to leads who haven't replied after DAYS_WAIT days.

Reads sms_log.csv, finds leads sent message #1 (status="sent") more than
DAYS_WAIT days ago, checks for replies via Twilio, skips opt-outs, and
sends Hillary's follow-up text. Logs each send as status="followup_sent".

Required .env vars:
    TWILIO_ACCOUNT_SID    — Twilio account SID
    TWILIO_AUTH_TOKEN     — Twilio auth token
    TWILIO_FROM_NUMBER    — Your Twilio number (e.g. +17205551234)

Usage:
    python3 sms_followup.py           # sends follow-ups due today
    python3 sms_followup.py --dry-run # preview without sending
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from twilio.rest import Client

from sms_utils import (
    SMS_LOG, OPTOUT_LOG,
    load_log, load_optouts, log_send, fetch_repliers,
)

load_dotenv()

ACCOUNT_SID  = os.environ["TWILIO_ACCOUNT_SID"]
AUTH_TOKEN   = os.environ["TWILIO_AUTH_TOKEN"]
FROM_NUMBER  = os.environ["TWILIO_FROM_NUMBER"]

DAYS_WAIT   = 3     # days after initial text before sending follow-up
DAILY_LIMIT = 30
DRY_RUN     = "--dry-run" in sys.argv

FOLLOWUP_MESSAGE = (
    "Hi again, it's Hillary from Roots Realty. Just wanted to make sure my last "
    "message didn't get lost. Happy to answer any questions about property management "
    "in Denver whenever you're ready. Feel free to reply or call anytime!"
)


def main():
    print(f"{'[DRY RUN] ' if DRY_RUN else ''}Loading SMS log...")
    log = load_log()
    print(f"  {len(log)} total log entries")

    # Find everyone who got the initial text
    sent_entries = {
        row["phone"]: row
        for row in log
        if row["status"] == "sent"
    }

    # Find everyone who already got the follow-up
    already_followed_up = {
        row["phone"]
        for row in log
        if row["status"] == "followup_sent"
    }

    # Eligible = got initial text, not yet followed up, waited long enough
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=DAYS_WAIT)

    eligible = {}
    for phone, row in sent_entries.items():
        if phone in already_followed_up:
            continue
        try:
            sent_at = datetime.fromisoformat(row["sent_at"])
            if sent_at <= cutoff:
                eligible[phone] = row["address"]
        except (ValueError, KeyError):
            continue

    print(f"  {len(eligible)} eligible for follow-up (sent {DAYS_WAIT}+ days ago, no follow-up yet)")

    twilio = None if DRY_RUN else Client(ACCOUNT_SID, AUTH_TOKEN)

    print("Checking opt-outs...")
    optouts = load_optouts(twilio, FROM_NUMBER)
    print(f"  {len(optouts)} opted out")

    print("Checking for replies...")
    repliers = set() if DRY_RUN else fetch_repliers(twilio, FROM_NUMBER)
    print(f"  {len(repliers)} have already replied")

    sent = skipped_optout = skipped_replied = 0

    for phone, address in eligible.items():
        if sent >= DAILY_LIMIT:
            print(f"\nDaily limit of {DAILY_LIMIT} reached. Run again tomorrow.")
            break

        if phone in optouts:
            skipped_optout += 1
            continue

        if phone in repliers:
            skipped_replied += 1
            continue

        print(f"\n→ {phone} | {address}")
        print(f"  {FOLLOWUP_MESSAGE}")

        if DRY_RUN:
            log_send(phone, address, "followup_dry_run")
        else:
            try:
                msg = twilio.messages.create(
                    from_=FROM_NUMBER, to=phone, body=FOLLOWUP_MESSAGE
                )
                log_send(phone, address, "followup_sent")
                print(f"  ✓ Sent ({msg.sid})")
            except Exception as e:
                log_send(phone, address, f"followup_error: {e}")
                print(f"  ✗ Failed: {e}")

        sent += 1

    print(f"\n── Summary ──────────────────────────")
    print(f"  Follow-ups sent:     {sent}")
    print(f"  Skipped (opted out): {skipped_optout}")
    print(f"  Skipped (replied):   {skipped_replied}")
    print(f"  Log:                 {SMS_LOG}")


if __name__ == "__main__":
    main()
