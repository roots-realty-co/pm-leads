import os
import re
import feedparser
import anthropic
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../pm_leads/.env"))

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CONTENT_CHANNEL_ID")

RSS_FEEDS = {
    # Direct feeds
    "BiggerPockets":                  "https://www.biggerpockets.com/blog/feed",
    "Zillow Research":                "https://www.zillow.com/research/feed/",
    "Colorado Assoc. of Realtors":   "https://www.coloradorealtors.com/feed/",
    "SBWP Law":                       "https://www.sbwp-law.com/feed/",
    "RentCafe":                       "https://www.rentcafe.com/blog/feed/",
    # Google News RSS for sources without public feeds
    "RentCast":                       "https://news.google.com/rss/search?q=site:rentcast.io&hl=en-US&gl=US&ceid=US:en",
    "CO Landlord-Tenant Law":         "https://news.google.com/rss/search?q=Colorado+landlord+tenant+law+eviction&hl=en-US&gl=US&ceid=US:en",
}

ARTICLES_PER_SOURCE = 3


def fetch_articles():
    articles = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                print(f"  No entries: {source}")
                continue
            for entry in feed.entries[:ARTICLES_PER_SOURCE]:
                raw_summary = entry.get("summary", entry.get("description", ""))
                summary = re.sub(r"<[^>]+>", "", raw_summary).strip()[:500]
                articles.append({
                    "source": source,
                    "title": entry.get("title", "").strip(),
                    "summary": summary,
                    "url": entry.get("link", ""),
                })
            print(f"  OK: {source} ({min(len(feed.entries), ARTICLES_PER_SOURCE)} articles)")
        except Exception as e:
            print(f"  FAILED: {source} — {e}")
    return articles


def build_prompt(articles):
    article_text = ""
    for i, a in enumerate(articles, 1):
        article_text += (
            f"{i}. [{a['source']}] {a['title']}\n"
            f"   {a['summary']}\n"
            f"   {a['url']}\n\n"
        )

    return f"""You are a social media content writer for Roots Realty, a residential property management company in Denver, CO.

Roots Realty's goal with social media is to build relationships with Denver real estate agents so they refer investor clients for property management. Posts should signal that Roots knows the Denver market, understands landlords and investors, and is the obvious PM partner when an agent's client buys a rental.

Review the following articles from this week. Select the 3-5 most relevant topics and write one post candidate per topic, tagged as LINKEDIN or INSTAGRAM.

LINKEDIN posts: 100-200 words. Analytical and narrative. Written for agents and investors. Frame insights around what it means for Denver landlords or investor clients. Position Roots as a knowledgeable local expert.
INSTAGRAM posts: 30-60 words. Punchy, local, conversational. Lead with a hook or stat. Relatable landlord or investor voice.

IMPORTANT STYLE RULES:
- Never use em dashes (—). Use commas, colons, or parentheses instead.
- Write like a sharp local expert, not a marketing bot. Avoid cliches and generic real estate language.

Format each post exactly like this:

---
PLATFORM: [LINKEDIN or INSTAGRAM]
SOURCE: [publication name]
HEADLINE: [one-line hook]
POST:
[post body]
URL: [article url]
---

Articles this week:
{article_text}"""


def generate_posts(prompt):
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def parse_posts(content):
    sections = re.split(r"\n?---\n?", content)
    return [s.strip() for s in sections if s.strip()]


def slack_post(channel, text, thread_ts=None):
    payload = {
        "channel": channel,
        "text": text,
        "mrkdwn": True,
    }
    if thread_ts:
        payload["thread_ts"] = thread_ts

    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-Type": "application/json",
        },
        json=payload,
    )
    result = response.json()
    if not result.get("ok"):
        raise Exception(f"Slack error: {result.get('error')}")
    return result["ts"]


def post_to_slack(content):
    date_str = datetime.now().strftime("%B %d, %Y")
    posts = parse_posts(content)

    summary = (
        f":newspaper: *Roots Post Candidates — {date_str}*\n"
        f"{len(posts)} options this week. Review and pick what resonates, Hillary posts."
    )
    thread_ts = slack_post(SLACK_CHANNEL_ID, summary)

    for post in posts:
        slack_post(SLACK_CHANNEL_ID, post, thread_ts=thread_ts)

    print(f"Posted summary + {len(posts)} candidates to Slack thread.")


def main():
    print("Fetching articles...")
    articles = fetch_articles()
    print(f"\nTotal: {len(articles)} articles from {len(RSS_FEEDS)} sources.\n")

    if not articles:
        print("No articles fetched. Exiting.")
        return

    print("Generating post candidates via Claude...")
    prompt = build_prompt(articles)
    posts = generate_posts(prompt)

    print("Posting to Slack...")
    post_to_slack(posts)
    print("Done.")


if __name__ == "__main__":
    main()
