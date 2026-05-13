import requests
import csv
import json
import time
import os
import urllib.request
from datetime import datetime, timezone
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()
API_TOKEN = os.getenv("APIFY_API_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "service_account.json")

ZIP_SEARCH_ACTOR = "maxcopell~zillow-zip-search"
DETAIL_ACTOR = "maxcopell~zillow-detail-scraper"

ZIP_CODES = [
    # Denver city
    "80202", "80203", "80204", "80205", "80206", "80207", "80209", "80210",
    "80211", "80212", "80216", "80218", "80219", "80220", "80221", "80222",
    "80223", "80224", "80226", "80227", "80228", "80229", "80230", "80231",
    "80232", "80233", "80234", "80235", "80236", "80237", "80238", "80239",
    "80246", "80247", "80249",
    # Arvada
    "80002", "80003", "80004", "80005", "80007",
    # Commerce City / Henderson
    "80022", "80640",
    # Englewood
    "80110", "80113",
    # Littleton / Highlands Ranch
    "80120", "80121", "80122", "80123", "80124", "80126", "80127", "80128",
    "80129", "80130",
    # Centennial / Greenwood Village / Lone Tree
    "80111", "80112",
    # Parker
    "80134", "80138",
    # Castle Rock
    "80104", "80108", "80109",
    # Lakewood
    "80214", "80215",
    # Boulder
    "80301", "80302", "80303", "80304", "80305",
]

def run_actor(actor_id, input_data):
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.post(url, json=input_data, headers=headers)
    run = response.json()
    if "data" not in run:
        raise RuntimeError(f"Unexpected Apify response: {run}")
    return run["data"]["id"], run["data"]["defaultDatasetId"]

def wait_for_run(run_id):
    url = f"https://api.apify.com/v2/actor-runs/{run_id}"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    while True:
        response = requests.get(url, headers=headers)
        status = response.json()["data"]["status"]
        print(f"Status: {status}")
        if status in ["SUCCEEDED", "FAILED", "ABORTED"]:
            return status
        time.sleep(5)

def get_dataset_items(dataset_id):
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(url, headers=headers)
    return response.json()

def ms_to_date(ms):
    if not ms:
        return None
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    except:
        return None

def extract_owner_fields(listing):
    attribution = listing.get("attributionInfo", {}) or {}
    contact = listing.get("postingContact", {}) or {}
    address = listing.get("address", {}) or {}
    reso = listing.get("resoFacts", {}) or {}

    return {
        "owner_name": contact.get("name"),
        "owner_phone": attribution.get("brokerPhoneNumber"),
        "is_listed_by_owner": listing.get("isListedByOwner"),
        "address": address.get("streetAddress"),
        "city": address.get("city"),
        "state": address.get("state"),
        "zip_code": address.get("zipcode"),
        "price": listing.get("price"),
        "bedrooms": listing.get("bedrooms"),
        "bathrooms": listing.get("bathrooms"),
        "sqft": listing.get("livingArea"),
        "home_type": listing.get("homeType"),
        "days_on_zillow": listing.get("daysOnZillow"),
        "listing_url": ("https://www.zillow.com" + listing["hdpUrl"] if listing.get("hdpUrl", "").startswith("/") else listing.get("hdpUrl")),
        "rent_zestimate": listing.get("rentZestimate"),
        "zestimate": listing.get("zestimate"),
        "date_listed": ms_to_date(reso.get("onMarketDate")),
        "date_available": ms_to_date(reso.get("availabilityDate")),
        "lease_term": reso.get("leaseTerm"),
        "zillow_user_id": listing.get("listingAccountUserId"),
        "price_history": listing.get("priceHistory"),
        "date_scraped": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }

def build_summary(leads, date):
    total = len(leads)
    with_name = sum(1 for l in leads if l.get("owner_name") and str(l["owner_name"]) not in ("None", ""))
    home_types = {}
    for l in leads:
        ht = l.get("home_type", "Unknown")
        home_types[ht] = home_types.get(ht, 0) + 1
    prices = [int(l["price"]) for l in leads if l.get("price") and str(l["price"]).isdigit()]
    avg_price = sum(prices) // len(prices) if prices else 0
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0
    return (
        f":house: *Zillow Leads Summary — {date}*\n\n"
        f"*Run stats*\n"
        f"• Total leads: {total}\n"
        f"• Leads with owner name: {with_name} / {total} ({int(with_name/total*100) if total else 0}%)\n\n"
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
    payload = json.dumps({"channel": SLACK_CHANNEL_ID, "text": message}).encode("utf-8")
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=payload,
        headers={
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-Type": "application/json",
        }
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def main():
    date_scraped = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print("Step 1: Running zip code search...")
    run_id, dataset_id = run_actor(ZIP_SEARCH_ACTOR, {
        "forRent": True,
        "forSaleByAgent": False,
        "forSaleByOwner": False,
        "priceMin": 2000,
        "sold": False,
        "zipCodes": ZIP_CODES,
        "daysOnZillow": ""
    })

    status = wait_for_run(run_id)
    if status != "SUCCEEDED":
        print(f"Zip search failed with status: {status}")
        return

    print("Fetching URLs from zip search...")
    search_results = get_dataset_items(dataset_id)
    urls = []
    for item in search_results:
        url = item.get("url") or item.get("hdpUrl") or item.get("detailUrl")
        if url:
            if url.startswith("/"):
                url = "https://www.zillow.com" + url
            if "/homedetails/" in url:
                urls.append(url)
    print(f"Found {len(urls)} individual listings (skipped building/complex pages)")

    print("Step 2: Running detail scraper...")
    run_id, dataset_id = run_actor(DETAIL_ACTOR, {
        "startUrls": [{"url": u} for u in urls]
    })

    status = wait_for_run(run_id)
    if status != "SUCCEEDED":
        print(f"Detail scraper failed with status: {status}")
        return

    print("Fetching listing details...")
    listings = get_dataset_items(dataset_id)
    print(f"Total listings returned: {len(listings)}")

    print("Step 3: Filtering owner listings...")
    owner_listings = [
        extract_owner_fields(l) for l in listings
        if str(l.get("isListedByOwner", "")).lower() in ("true", "1")
        and (
            (l.get("attributionInfo") or {}).get("brokerPhoneNumber")
            or (l.get("attributionInfo") or {}).get("agentPhoneNumber")
        )
    ]
    print(f"Found {len(owner_listings)} owner-listed properties")

    if not owner_listings:
        print("No owner listings found — check debug output above")
        return

    print("Step 4: Writing to CSV...")
    csv_filename = os.path.join(os.path.dirname(__file__), f"zillow_leads_{date_scraped}.csv")
    with open(csv_filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=owner_listings[0].keys())
        writer.writeheader()
        writer.writerows(owner_listings)
    print(f"Saved to {csv_filename}")

    print("Step 5: Appending to Google Sheets...")
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    existing = sheet.get_all_values()
    headers = list(owner_listings[0].keys())
    if not existing:
        sheet.append_row(headers)
    rows = [[str(l.get(h, "")) for h in headers] for l in owner_listings]
    sheet.append_rows(rows)
    print(f"{len(owner_listings)} leads appended to Google Sheets")

    print("Step 6: Posting to Slack...")
    summary = build_summary(owner_listings, date_scraped)
    result = post_to_slack(summary)
    if result.get("ok"):
        print("Slack summary posted")
    else:
        print(f"Slack post failed: {result}")

if __name__ == "__main__":
    main()
