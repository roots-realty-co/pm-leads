import json
import csv

INPUT_FILE = "dataset_linkedin-profile-search_2026-04-26_16-20-48-983.json"
OUTPUT_FILE = "heyreach_import.csv"

EXCLUDE_KEYWORDS = [
    "commercial", "business broker", "mergers", "acquisitions",
    "mortgage", "lending", "capital", "healthcare", "industrial",
    "business advisor", "photographer", "marketing", "administrative"
]

EXCLUDE_COMPANIES = [
    "acorn and oak"
]

INCLUDE_KEYWORDS = [
    "realtor", "real estate agent", "broker associate", "listing agent",
    "buyer's agent", "residential", "keller williams", "re/max", "remax",
    "coldwell", "kentwood", "exit realty", "century 21", "compass",
    "exp realty", "eexp", "sotheby"
]

def is_residential_agent(profile):
    headline = (profile.get("headline") or "").lower()
    position = ""
    company = ""
    current = profile.get("currentPosition") or []
    if current:
        position = (current[0].get("position") or "").lower()
        company = (current[0].get("companyName") or "").lower()

    text = f"{headline} {position} {company}"

    if any(kw in text for kw in EXCLUDE_KEYWORDS):
        return False
    if any(co in company for co in EXCLUDE_COMPANIES):
        return False
    if any(kw in text for kw in INCLUDE_KEYWORDS):
        return True
    return False

def flatten(profile):
    current = profile.get("currentPosition") or []
    return {
        "First Name": profile.get("firstName", ""),
        "Last Name": profile.get("lastName", ""),
        "LinkedIn URL": profile.get("linkedinUrl", ""),
        "Headline": profile.get("headline", ""),
        "Title": current[0].get("position", "") if current else "",
        "Company": current[0].get("companyName", "") if current else "",
    }

with open(INPUT_FILE) as f:
    profiles = json.load(f)

filtered = [flatten(p) for p in profiles if is_residential_agent(p)]

with open(OUTPUT_FILE, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=filtered[0].keys())
    writer.writeheader()
    writer.writerows(filtered)

print(f"{len(profiles)} total profiles")
print(f"{len(filtered)} after filtering")
print(f"Saved to {OUTPUT_FILE}")
