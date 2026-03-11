BASE_URL = "https://immovlan.be/en/real-estate"

PARAMS = "transactiontypes=for-sale,in-public-sale&propertytypes=house,apartment"

APARTMENT_SUBTYPES = {
    "apartment",
    "studio",
    "penthouse",
    "duplex",
    "ground floor",
    "triplex",
    "loft",
}
HOUSE_SUBTYPES = {
    "residence",
    "mixed building",
    "villa",
    "master house",
    "bungalow",
    "chalet",
    "mansion",
    "house",
    "cottage",
}

NUM_WORKERS_PARSER = 20  # workers for threadpoolexec
NUM_WORKERS_SCRAPER = 10

# CONSTANT variables in phase2.py
INPUT_FILE = "data/raw/all_provinces_links.csv"
OUTPUT_FILE = "data/processed/listings.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

PROVINCES = [
    "brussels",
    "antwerp",
    "east-flanders",
    "west-flanders",
    "vlaams-brabant",
    "limburg",
    "liege",
    "hainaut",
    "namur",
    "luxembourg",
    "brabant-wallon",
]

PRICE_RANGES = [
    (0, 100000),
    (100000, 200000),
    (200000, 300000),
    (300000, 400000),
    (400000, 500000),
    (500000, 750000),
    (750000, 9999999),
]

COLUMNS = [
    "locality",
    "property_type",
    "subtype",
    "price_eur",
    "type_of_sale",
    "num_rooms",
    "living_area_m2",
    "fully_equipped_kitchen",
    "furnished",
    "terrace",
    "terrace_area_m2",
    "garden",
    "garden_area_m2",
    "land_surface_m2",
    "num_facades",
    "swimming_pool",
    "state_of_building",
    "num_bathrooms"
]

FIELD_MAP = {
    "number of toilets": "num_bathrooms",
    "number of bedrooms": "num_rooms",
    "livable surface": "living_area_m2",
    "kitchen equipment": "fully_equipped_kitchen",
    "furnished": "furnished",
    "terrace": "terrace",
    "surface terrace": "terrace_area_m2",
    "garden": "garden",
    "surface garden": "garden_area_m2",
    "total land surface": "land_surface_m2",
    "number of facades": "num_facades",
    "swimming pool": "swimming_pool",
    "state of the property": "state_of_building",
}
