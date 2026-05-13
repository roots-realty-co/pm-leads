# AWS Lambda function — reads Zillow leads from Google Sheets and posts a summary to Slack.
#
# Environment variables (set in Lambda console):
#   SPREADSHEET_ID             — Google Sheet ID containing Zillow leads
#   SLACK_BOT_TOKEN            — Slack bot token for posting messages
#   SLACK_CHANNEL_ID           — Slack channel to post summaries to
#   GOOGLE_SERVICE_ACCOUNT_B64 — Base64-encoded service account JSON (zillow-leads@pm-leads)
#
# Layers:
#   Klayers-p312-gspread (version 20) — provides gspread + google-auth for python3.12 x86_64
#   ARN: arn:aws:lambda:us-east-2:770693421928:layer:Klayers-p312-gspread:20

import json
import os
import base64
import urllib.request
from datetime import datetime, timezone
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = os.environ['SPREADSHEET_ID']
SLACK_BOT_TOKEN = os.environ['SLACK_BOT_TOKEN']
SLACK_CHANNEL_ID = os.environ['SLACK_CHANNEL_ID']
GOOGLE_SERVICE_ACCOUNT_B64 = os.environ['GOOGLE_SERVICE_ACCOUNT_B64']

def get_leads():
    creds_json = base64.b64decode(GOOGLE_SERVICE_ACCOUNT_B64).decode('utf-8')
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet.get_all_records()

def build_summary(leads):
    total = len(leads)
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    with_name = sum(1 for l in leads if l.get('owner_name') and str(l['owner_name']) not in ('None', ''))
    home_types = {}
    for l in leads:
        ht = l.get('home_type', 'Unknown')
        home_types[ht] = home_types.get(ht, 0) + 1
    prices = [int(l['price']) for l in leads if l.get('price') and str(l['price']).isdigit()]
    avg_price = sum(prices) // len(prices) if prices else 0
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0
    recent = [l for l in leads if str(l.get('date_listed', '')) >= '2026-04-19']
    return (
        f":house: *Zillow Leads Summary — {today}*\n\n"
        f"*Run stats*\n"
        f"• Total leads: {total}\n"
        f"• Leads with owner name: {with_name} / {total} ({int(with_name/total*100) if total else 0}%)\n"
        f"• Listed in last 7 days: {len(recent)}\n\n"
        f"*Property breakdown*\n"
        f"• Single family: {home_types.get('SINGLE_FAMILY', 0)}\n"
        f"• Apartment: {home_types.get('APARTMENT', 0)}\n"
        f"• Townhouse: {home_types.get('TOWNHOUSE', 0)}\n\n"
        f"*Rent pricing*\n"
        f"• Avg: ${avg_price:,}/mo\n"
        f"• Range: ${min_price:,} — ${max_price:,}\n\n"
        f":bar_chart: Full data: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
    )

def post_to_slack(message):
    payload = json.dumps({'channel': SLACK_CHANNEL_ID, 'text': message}).encode('utf-8')
    req = urllib.request.Request(
        'https://slack.com/api/chat.postMessage',
        data=payload,
        headers={
            'Authorization': f'Bearer {SLACK_BOT_TOKEN}',
            'Content-Type': 'application/json'
        }
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def lambda_handler(event, context):
    leads = get_leads()
    if not leads:
        return {'statusCode': 200, 'body': 'No leads found'}
    summary = build_summary(leads)
    result = post_to_slack(summary)
    return {
        'statusCode': 200,
        'body': json.dumps({'slack_ok': result.get('ok'), 'leads': len(leads)})
    }
