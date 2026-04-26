import requests
import csv
import time
import os
from dotenv import load_dotenv

# Load API token from .env file
load_dotenv()
API_TOKEN = os.getenv("APIFY_API_TOKEN")

# The two Apify actors we're using
ZIP_SEARCH_ACTOR = "maxcopell~zillow-zip-search"
DETAIL_ACTOR = "maxcopell~zillow-detail-scraper"

# Denver zip codes to search
ZIP_CODES = ["80203", "80209", "80218", "80206"]

def run_actor(actor_id, input_data):
    """Start an Apify actor run and return the run ID"""
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.post(url, json=input_data, headers=headers)
    run = response.json()
    if "data" not in run:
        raise RuntimeError(f"Unexpected Apify response: {run}")
    return run["data"]["id"], run["data"]["defaultDatasetId"]

def wait_for_run(run_id):
    """Poll until the actor run finishes"""
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
    """Fetch results from a completed run"""
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(url, headers=headers)
    return response.json()

def extract_owner_fields(listing):
    """Pull only the fields we care about from a listing"""
    attribution = listing.get("attributionInfo", {}) or {}
    contact = listing.get("postingContact", {}) or {}
    address = listing.get("address", {}) or {}

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
        "listing_url": listing.get("hdpUrl"),
        "description": listing.get("description"),
    }

def main():
    print("Step 1: Running zip code search...")
    run_id, dataset_id = run_actor(ZIP_SEARCH_ACTOR, {
        "forRent": True,
        "forSaleByAgent": False,
        "forSaleByOwner": False,
        "priceMin": 1500,
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
            # Skip building/complex pages — only individual listings have isListedByOwner
            if "/homedetails/" in url:
                urls.append(url)
    print(f"Found {len(urls)} individual listings (skipped building/complex pages)")

    print("Step 2: Running detail scraper...")
    run_id, dataset_id = run_actor(DETAIL_ACTOR, {
    "startUrls": [{"url": u} for u in urls[:30]] # limit to 30 for test
    })

    status = wait_for_run(run_id)
    if status != "SUCCEEDED":
        print(f"Detail scraper failed with status: {status}")
        return

    print("Fetching listing details...")
    listings = get_dataset_items(dataset_id)
    print(f"Total listings returned: {len(listings)}")

    if listings:
        sample = listings[0]
        raw_val = sample.get("isListedByOwner")
        print(f"isListedByOwner sample value: {raw_val!r} (type: {type(raw_val).__name__})")

    print("Step 3: Filtering owner listings...")
    owner_listings = [
        extract_owner_fields(l) for l in listings
        if str(l.get("isListedByOwner", "")).lower() in ("true", "1")
    ]
    print(f"Found {len(owner_listings)} owner-listed properties")

    if not owner_listings:
        print("No owner listings found — check debug output above")
        return

    print("Step 4: Writing to CSV...")
    with open("owner_leads.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=owner_listings[0].keys())
        writer.writeheader()
        writer.writerows(owner_listings)

    print("Done. Results saved to owner_leads.csv")

if __name__ == "__main__":
    main()