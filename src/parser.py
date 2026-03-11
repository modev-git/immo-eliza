import requests
from bs4 import BeautifulSoup
import time
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from src.config import (
    INPUT_FILE,
    NUM_WORKERS_PARSER,
    OUTPUT_FILE,
    HEADERS,
    COLUMNS,
    FIELD_MAP,
    APARTMENT_SUBTYPES,
    HOUSE_SUBTYPES,
)

session = requests.Session()
session.headers.update(HEADERS)


# Loads and filters valid listing URLs from a text file
def load_urls(filename):
    with open(filename, "r", encoding="utf-8") as f:
        urls = [
            line.strip()
            for line in f
            if line.strip()
            and "/detail/" in line
            and "/projectdetail/" not in line  # filters projectdetail
        ]
    return urls


# Fetches the HTML content of a single listing page
def fetch_page(url, session):
    try:
        response = session.get(url, timeout=15)
        if response.status_code != 200:
            print(f" Skipping {url} — status {response.status_code}")
            return None
        return response.text
    except requests.RequestException as e:
        print(f"  ✗ Could not fetch {url}: {e}")
        return None


# ─────────────────────────────────────────────
# Parse helpers
# ─────────────────────────────────────────────


# Determines the property category based on its subtype
def get_property_type(subtype):
    subtype = subtype.lower().strip()
    if subtype in APARTMENT_SUBTYPES:
        return "Apartment"
    elif subtype in HOUSE_SUBTYPES:
        return "House"
    else:
        return "Other"


# Extracts and cleans the property price from the HTML
def extract_price(soup):
    price_tag = soup.select_one(".detail__header_price_data")
    if price_tag:
        raw_price = price_tag.get_text(strip=True)
        clean_price = re.sub(r"[^\d]", "", raw_price)
        return clean_price if clean_price else None
    return None


# Extracts the city or locality of the property
def extract_locality(soup):
    locality_tag = soup.select_one(".city-line")
    if locality_tag:
        raw_locality = locality_tag.get_text(strip=True)
        indexed_locality = raw_locality
        return indexed_locality
    return None


# Extracts additional property attributes from the info table
def extract_fields(soup):
    """
    Extracts fields based on FIELD_MAP.
    Returns a dictionary of cleaned field values.
    """
    fields_more_info = {}

    wrapper_more_info = soup.select_one(".general-info-wrapper")
    if not wrapper_more_info:
        return fields_more_info

    for div in wrapper_more_info.select(".data-row-wrapper > div"):
        h4 = div.select_one("h4")
        p = div.select_one("p")
        if not (h4 and p):
            continue

        key = h4.get_text(strip=True).lower()
        value = p.get_text(strip=True)

        if key not in FIELD_MAP:
            continue

        col = FIELD_MAP[key]
        clean_value = value.lower().strip()

        # Determine field value based on type/content
        if col == "fully_equipped_kitchen":
            fields_more_info[col] = 1
        elif clean_value == "yes":
            fields_more_info[col] = 1
        elif clean_value == "no":
            fields_more_info[col] = 0
        elif any(char.isdigit() for char in clean_value):
            num_only = re.sub(r"[^\d]", "", clean_value)
            fields_more_info[col] = int(num_only) if num_only else None
        else:
            fields_more_info[col] = value

    return fields_more_info


# Parses a single listing page into structured data
def parse_listing(html, url):
    soup = BeautifulSoup(html, "html.parser")
    split_url = url.split("/")

    data_all_info = {col: None for col in COLUMNS}  # None for empty values

    # get type of sale
    data_all_info["type_of_sale"] = (
        split_url[6].replace("-", " ") if len(split_url) > 6 else None
    )
    # get price
    data_all_info["price_eur"] = extract_price(soup)
    # get locality
    data_all_info["locality"] = extract_locality(soup)

    data_all_info.update(extract_fields(soup))

    # get property type
    subtype_raw = split_url[5] if len(split_url) > 5 else None
    if subtype_raw:
        subtype = subtype_raw.replace("-", " ").title()
        data_all_info["subtype"] = subtype
        data_all_info["property_type"] = get_property_type(subtype)
    return data_all_info


# ─────────────────────────────────────────────
# Worker — one thread runs this per URL
# ─────────────────────────────────────────────


# Scrapes one listing (executed by each thread)
def scrape_one(args):
    url, session, index, total = args
    print(f"  [{index}/{total}] Scraping: {url}")
    time.sleep(random.uniform(0.5, 1.0))

    html = fetch_page(url, session)
    if not html:
        return None
    data = parse_listing(html, url)
    print(
        f"  [{index}/{total}] ✓ {data['locality']} | {data['price_eur']}€ | {data['property_type']}"
    )
    return data


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────


# Coordinates multi-threaded scraping of all listings
def scrape_all_listings():
    all_urls = load_urls(INPUT_FILE)  # remove [:200] to scrape everything
    total = len(all_urls)
    print(f"Loaded {total} URLs — scraping with 20 threads")

    # Each thread gets its own session
    sessions = [requests.Session() for _ in range(NUM_WORKERS_PARSER)]
    for s in sessions:
        s.headers.update(HEADERS)

    jobs = []
    for i, url in enumerate(all_urls):
        session = sessions[i % NUM_WORKERS_PARSER]  # pick a session
        index = i + 1  # display number
        jobs.append((url, session, index, total))

    all_data = []
    with ThreadPoolExecutor(max_workers=NUM_WORKERS_PARSER) as executor:
        futures = [executor.submit(scrape_one, job) for job in jobs]
        for future in as_completed(futures):
            result = future.result()
            if result:
                all_data.append(result)

    return all_data


# save to pandas Dataframe function
def save_to_pd_csv(all_data):
    df = pd.DataFrame(all_data, columns=COLUMNS)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig", na_rep="None")
    print(f"\nDone! {len(df)} listings saved to {OUTPUT_FILE}")
