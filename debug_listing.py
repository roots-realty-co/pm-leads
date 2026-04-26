import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("APIFY_API_TOKEN")

# Fetch the most recent detail scraper run
runs_url = "https://api.apify.com/v2/acts/maxcopell~zillow-detail-scraper/runs?limit=1&desc=1"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

run = requests.get(runs_url, headers=headers).json()["data"]["items"][0]
dataset_id = run["defaultDatasetId"]
print(f"Using dataset: {dataset_id} (run finished: {run['finishedAt']})")

items = requests.get(
    f"https://api.apify.com/v2/datasets/{dataset_id}/items?limit=2",
    headers=headers
).json()

if not items:
    print("No items in dataset")
else:
    with open("sample_listing.json", "w") as f:
        json.dump(items[0], f, indent=2)
    print("Full first listing saved to sample_listing.json")

    # Print keys and any owner-related values
    flat = items[0]
    print("\n--- Top-level keys ---")
    print(list(flat.keys()))

    print("\n--- Owner-related fields ---")
    for key in ("isListedByOwner", "listedBy", "isRentedByOwner", "postingType"):
        print(f"  {key}: {flat.get(key)!r}")

    for section in ("attributionInfo", "postingContact", "hdpData"):
        val = flat.get(section)
        if val:
            print(f"\n  {section}: {json.dumps(val, indent=4)[:500]}")
