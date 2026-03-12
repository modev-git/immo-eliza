from src.scraper import collect_all_urls, save_to_csv
from src.parser import scrape_all_listings as run_parser, save_to_pd_csv


if __name__ == "__main__":
    """print("--- Phase 1: Scraping URLs ---")
    urls = collect_all_urls()
    save_to_csv(urls)"""

    print("\n--- Phase 2: Parsing Listings ---")
    all_data = run_parser()

    print("\n--- Phase 3: Saving to CSV ---")
    save_to_pd_csv(all_data)
