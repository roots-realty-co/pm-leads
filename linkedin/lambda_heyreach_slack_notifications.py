# AWS Lambda function — receives Heyreach webhook events and posts notifications to Slack.
# Handles connection requests accepted and message replies.
#
# Environment variables (set in Lambda console):
#   SLACK_BOT_TOKEN  — Slack bot token for posting messages
#   SLACK_CHANNEL_ID — Slack channel to post notifications to
#
# Function URL: public (Auth type: NONE) — Heyreach posts webhook events directly to this URL
# Runtime: Python 3.12, x86_64

import json
import os
import urllib.request

SLACK_BOT_TOKEN = os.environ['SLACK_BOT_TOKEN']
SLACK_CHANNEL_ID = os.environ['SLACK_CHANNEL_ID']

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
    body = json.loads(event.get('body', '{}'))
    event_type = body.get('event_type', '')
    lead = body.get('lead', {})
    name = lead.get('full_name', 'Unknown')
    profile_url = lead.get('profile_url', '')
    position = lead.get('position', '')
    company = lead.get('company_name', '')

    if event_type == 'connection_request_accepted':
        message = (
            f":handshake: *New connection accepted*\n"
            f"*{name}*\n"
            f"{position} at {company}\n"
            f"{profile_url}"
        )
    elif event_type == 'every_message_reply_received':
        messages = body.get('recent_messages', [])
        replies = [m.get('message', '') for m in messages if m.get('is_reply') and m.get('message')]
        reply_text = replies[0] if replies else '(no text - attachment or voice note)'
        message = (
            f":speech_balloon: *New reply from {name}*\n"
            f"{position} at {company}\n"
            f"_{reply_text}_\n"
            f"{profile_url}"
        )
    else:
        return {'statusCode': 200, 'body': 'unhandled event type'}

    result = post_to_slack(message)
    return {
        'statusCode': 200,
        'body': json.dumps({'slack_ok': result.get('ok'), 'event': event_type})
    }
