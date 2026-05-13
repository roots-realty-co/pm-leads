"""
sms_utils.py — Shared helpers for SMS outreach scripts.
"""

import csv
import json
import os
import re
from datetime import datetime, timezone

import gspread
from google.oauth2.service_account import Credentials

SMS_LOG    = "sms_log.csv"
OPTOUT_LOG = "optouts.csv"
STOP_KEYWORDS = {"stop", "stopall", "unsubscribe", "cancel", "end", "quit"}


def normalize_phone(raw):
    """Strip everything except digits, return E.164 format or None."""
    if not raw:
        return None
    digits = re.sub(r"\D", "", str(raw))
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return None


def load_sheet(spreadsheet_id):
    """Read all leads from Google Sheets using the local service account."""
    with open("service_account.json") as f:
        creds_dict = json.load(f)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(spreadsheet_id).sheet1
    rows = sheet.get_all_values()
    if not rows:
        return []
    headers = rows[0]
    records = []
    for row in rows[1:]:
        record = {}
        for i, header in enumerate(headers):
            if header:
                record[header] = row[i] if i < len(row) else ""
        records.append(record)
    return records


def load_log():
    """Return all rows from sms_log.csv as a list of dicts."""
    if not os.path.exists(SMS_LOG):
        return []
    with open(SMS_LOG, newline="") as f:
        return list(csv.DictReader(f))


def load_contacted():
    """Return a set of all phone numbers ever logged (any status)."""
    return {row["phone"] for row in load_log()}


def load_optouts(twilio_client=None, from_number=None):
    """
    Return a set of opted-out phone numbers.
    Pulls incoming STOP replies from Twilio, merges with local optouts.csv,
    and saves the updated list back to disk.
    """
    local = set()
    if os.path.exists(OPTOUT_LOG):
        with open(OPTOUT_LOG, newline="") as f:
            local = {row["phone"] for row in csv.DictReader(f)}

    remote = set()
    if twilio_client and from_number:
        try:
            incoming = twilio_client.messages.list(to=from_number)
            for msg in incoming:
                if msg.body and msg.body.strip().lower() in STOP_KEYWORDS:
                    normalized = normalize_phone(msg.from_)
                    if normalized:
                        remote.add(normalized)
        except Exception as e:
            print(f"  Warning: could not fetch opt-outs from Twilio: {e}")

    combined = local | remote

    new_numbers = combined - local
    if new_numbers:
        write_header = not os.path.exists(OPTOUT_LOG)
        with open(OPTOUT_LOG, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["phone", "added_at"])
            if write_header:
                writer.writeheader()
            for phone in new_numbers:
                writer.writerow({
                    "phone": phone,
                    "added_at": datetime.now(timezone.utc).isoformat(),
                })
        print(f"  {len(new_numbers)} new opt-out(s) saved to {OPTOUT_LOG}")

    return combined


def log_send(phone, address, status):
    """Append a row to sms_log.csv."""
    write_header = not os.path.exists(SMS_LOG)
    with open(SMS_LOG, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["phone", "address", "status", "sent_at"])
        if write_header:
            writer.writeheader()
        writer.writerow({
            "phone": phone,
            "address": address,
            "status": status,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        })


def fetch_repliers(twilio_client, from_number):
    """
    Return a set of phone numbers that have sent any inbound reply
    to our Twilio number (excluding STOP keywords).
    """
    repliers = set()
    try:
        incoming = twilio_client.messages.list(to=from_number)
        for msg in incoming:
            if msg.body and msg.body.strip().lower() not in STOP_KEYWORDS:
                normalized = normalize_phone(msg.from_)
                if normalized:
                    repliers.add(normalized)
    except Exception as e:
        print(f"  Warning: could not fetch replies from Twilio: {e}")
    return repliers
