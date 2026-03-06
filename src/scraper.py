import requests
from bs4 import BeautifulSoup
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
from src.config import (
    BASE_URL,
    NUM_WORKERS_SCRAPER,
    PARAMS,
    HEADERS,
    PROVINCES,
    PRICE_RANGES,
    INPUT_FILE,
)


# Constructs and returns the precise target URL by injecting province, page, and price parameters.
def build_url(province, page=1, min_price=None, max_price=None):
    price_param = ""
    if min_price is not None:
        price_param += f"&minprice={min_price}"
    if max_price is not None:
        price_param += f"&maxprice={max_price}"
    page_param = f"&page={page}" if page > 1 else ""
    return (
        f"{BASE_URL}?{PARAMS}&provinces={province}{price_param}{page_param}&noindex=1"
    )


# Scrapes all listing URLs for one province and one price range
def get_listing_urls(province, session, min_price=None, max_price=None):
    urls = []

    for page in range(1, 51):
        try:
            url = build_url(province, page, min_price, max_price)
            response = session.get(url, timeout=15)

            if response.status_code == 429:
                print(f"\n  ⚠ Rate limited on {province} page {page} — waiting 5s...")
                time.sleep(5)
                continue

            if response.status_code != 200:
                print(
                    f"\n  ✗ Unexpected status {response.status_code} on {province} page {page} — skipping"
                )
                break

            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.select("h2.card-title a[href]")

            if not links:
                break

            for link in links:
                href = link.get("href")
                if href and "/projectdetail/" not in href:
                    urls.append(href)

            print(f"  Page {page} — {len(urls)} links collected so far...", end="\r")
            time.sleep(random.uniform(0.1, 0.3))

        except requests.RequestException as e:
            print(f"\n  ✗ Request failed on {province} page {page}: {e}")
            break

    return urls


# Worker — one thread runs this per province/price combination
def fetch_province_price(args):
    province, min_price, max_price, session = args
    print(f"\nScraping: {province} | {min_price}€ - {max_price}€ ...")
    urls = get_listing_urls(province, session, min_price, max_price)
    print(f"  ✓ {len(urls)} links collected from {province} {min_price}-{max_price}")
    return urls


# Collects listing URLs for all provinces and price ranges using multiple threads
def collect_all_urls():
    all_urls = set()

    # Create one session per worker
    sessions = [requests.Session() for _ in range(NUM_WORKERS_SCRAPER)]
    for s in sessions:
        s.headers.update(HEADERS)

    # Build all province + price range combinations
    combinations = [
        (province, min_price, max_price)
        for province in PROVINCES
        for min_price, max_price in PRICE_RANGES
    ]

    # Assign a session to each job
    jobs = [
        (province, min_price, max_price, sessions[i % NUM_WORKERS_SCRAPER])
        for i, (province, min_price, max_price) in enumerate(combinations)
    ]

    total_jobs = len(jobs)
    completed = 0

    with ThreadPoolExecutor(max_workers=NUM_WORKERS_SCRAPER) as executor:
        futures = [executor.submit(fetch_province_price, job) for job in jobs]
        for future in as_completed(futures):
            result = future.result()
            all_urls.update(result)
            completed += 1
            print(
                f"\n[{completed}/{total_jobs}] combinations done — {len(all_urls)} unique URLs so far"
            )

    print(f"\nDone! Collected {len(all_urls)} unique links in total.")
    return list(all_urls)


# Saves all collected URLs into a CSV file
def save_to_csv(urls, filename=INPUT_FILE):
    df = pd.DataFrame(urls, columns=["URL"])
    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"File '{filename}' created with {len(urls)} entries.")
