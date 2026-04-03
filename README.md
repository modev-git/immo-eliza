# 🏠 ImmoEliza — Belgian Real Estate Analysis & Price Prediction API

A complete data pipeline for collecting, cleaning, analysing, and predicting real estate prices from [immovlan.be](https://immovlan.be/en) — covering houses and apartments for sale across all Belgian provinces.

---

## 📋 Project Overview

This project was built in four stages:

1. **Scraping** — Collecting ~26,000 property listings from Immovlan across all 11 Belgian provinces, using price-range segmentation to bypass the 50-page query limit.
2. **Cleaning** — Removing duplicates, handling missing values, filtering outliers, and engineering new features for analysis.
3. **Analysis** — Exploring correlations, regional price differences, municipality rankings, and property size distributions to extract actionable market insights.
4. **API Deployment** — A REST API built with FastAPI that serves price predictions from a trained XGBoost model, deployed on Render via Docker.

---

## 🌐 Target URLs

| Parameter | Value |
|---|---|
| Base URL | `https://immovlan.be/en` |
| Transaction Types | `for-sale`, `in-public-sale` |
| Property Types | `house`, `apartment` |
| Provinces | All 11 Belgian provinces |
| Results per page | 20 |
| Max pages per segment | 50 |

### URL Structure

```
# Page 1
https://immovlan.be/en/real-estate?transactiontypes=for-sale,in-public-sale&propertytypes=house,apartment&provinces={province}&noindex=1

# Page N (N > 1)
https://immovlan.be/en/real-estate?transactiontypes=for-sale,in-public-sale&propertytypes=house,apartment&provinces={province}&page={N}&noindex=1
```

> **Note:** Immovlan caps results at 50 pages (1,000 listings) per query. To overcome this, the scraper segments each province by **price range**, collecting all pages within each segment and merging the results.

---

## 📁 Project Structure

```
immo-prediction/
│
├── 📁 data/
│   ├── 📁 raw/
│   │   └── all_provinces_links.csv
│   └── 📁 processed/
│       └── cleaned_listings.csv
│
├── 📁 model/
│   └── model.pkl                  ← trained XGBoost pipeline
│
├── 📁 notebooks/
│   ├── cleaning.ipynb
│   ├── analysis.ipynb
│   └── regression.ipynb
│
├── 📁 predict/                    ← prediction module
│   ├── __init__.py
│   └── prediction.py
│
├── 📁 preprocessing/              ← preprocessing module
│   ├── __init__.py
│   └── cleaning_data.py
│
├── 📁 src/                        ← phases 1–3 scraping code
│   ├── config.py
│   ├── parser.py
│   └── scraper.py
│
├── .gitignore
├── API_DOCS.md
├── Dockerfile
├── README.md
├── app.py                         ← FastAPI application
├── main.py                        ← phases 1–3 entry point
├── requirements.txt
└── train_model.py                 ← run once to generate model.pkl
```

---

## ⚙️ Configuration (`config.py`)

```python
BASE_URL = "https://immovlan.be/en/real-estate"

PROVINCES = ["brussels", "antwerp", "east-flanders", ...]  # all 11 provinces

PARAMS = {
    "transactiontypes": "for-sale,in-public-sale",
    "propertytypes": "house,apartment",
    "noindex": 1,
}

PRICE_RANGES = [
    (0, 100_000),
    (100_000, 200_000),
    (200_000, 300_000),
    (300_000, 500_000),
    (500_000, 750_000),
    (750_000, 9_999_999),
]

MAX_PAGES = 50
RESULTS_PER_PAGE = 20
REQUEST_DELAY = 1.5  # seconds between requests
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/KlitiHamataj/immo-eliza.git
cd immo-eliza
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the scraper

```bash
python main.py
```

### 4. Run the notebooks

Open `notebooks/cleaning.ipynb` first, then `notebooks/analysis.ipynb`. The cleaning notebook outputs `cleaned_listings.csv`, which the analysis notebook reads as its input.

---

## 🧹 Data Cleaning

The cleaning pipeline (`cleaning.ipynb`) processes the raw `listings.csv` into a clean, analysis-ready dataset.

### Steps performed

| Step | Description |
|---|---|
| **Remove duplicates** | Drops duplicate rows |
| **Fill binary flags** | `swimming_pool`, `garden`, `terrace`, `fully_equipped_kitchen`, `num_facades` filled with `0` where null (absence = not present) |
| **Conditional fill** | `garden_area_m2` and `terrace_area_m2` filled with `0` only when the corresponding flag is `0` |
| **Remove price outliers** | Dropped listings with `price_eur < €20,000` (likely data errors) |
| **Remove area outliers** | Dropped `living_area_m2 > 1,000 m²`, `garden_area_m2 > 5,000 m²`, `land_surface_m2 < 10 m²` or `> 10,000 m²` |
| **Drop missing prices** | Removed rows with no price — required for all analysis |

### Feature engineering

| Feature | Description |
|---|---|
| `postal_code` | Extracted 4-digit postal code from the `locality` string |
| `region` | Assigned Brussels / Flanders / Wallonia based on postal code ranges |
| `price_per_m2` | `price_eur / living_area_m2`, rounded to 2 decimals |
| `avg_price_locality` | Mean price per locality via groupby transform (target encoding) |
| `building_state_encoded` | Ordinal encoding of `state_of_building` (1 = To demolish → 9 = New) |
| `outlier_flag` | Boolean flag for listings with `price_eur > €2M` and `num_rooms < 4` |

**Final dataset: 23,202 rows × 21 columns**

---

## 📊 Analysis

The analysis notebook (`analysis.ipynb`) answers the following questions using the cleaned dataset.

### Correlation with price

| Variable | Correlation (r) |
|---|---|
| `living_area_m2` | 0.57 |
| `avg_price_locality` | 0.54 |
| `num_rooms` | 0.42 |
| `land_surface_m2` | 0.33 |
| `furnished` | 0.02 *(lowest)* |

> Living area and location are nearly equal in predictive power — both dominate all other variables. Furnishing status has near-zero impact, confirming it is a personal choice rather than a property attribute.

### Inter-variable correlations

- **Rooms ↔ Living area** (r=0.68): More rooms almost always means more total area.
- **Garden area ↔ Land surface** (r=0.77): Larger plots naturally have more garden.
- **Garden ↔ Number of facades** (r=0.33): Properties with gardens tend to be detached villas with 4 facades.
- **Building state ↔ Price** (r=0.20): Location and size dominate. A run-down villa in Brussels still outprices a renovated property in rural Wallonia.

### The 5 most important variables

1. **Living area (m²)** — The single strongest predictor (r=0.57).
2. **Locality** — Proximity to major cities captures demand, infrastructure, and prestige.
3. **Number of rooms** — Priced independently of total size.
4. **Land surface (m²)** — Larger plots mean more privacy and upgrade potential.
5. **State of building** — Better condition means faster occupancy with no renovation cost.

### Business insight

Approximately 80% of listings sit between **€200,000 and €450,000** — the Belgian market's "Golden Range".

---

## 🤖 Phase 4 — Price Prediction API

### Overview

| Property | Value |
|---|---|
| Framework | FastAPI |
| Model | XGBoost Regressor |
| R² Score | 0.786 |
| Deployment | Render (Docker) |
| Live URL | https://immo-eliza-ezyg.onrender.com |
| Interactive docs | https://immo-eliza-ezyg.onrender.com/docs |

### Routes

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Health check — returns `"alive"` |
| `GET` | `/predict` | Describes the POST endpoint format |
| `POST` | `/predict` | Predicts a property price |

### Example request

```bash
curl -X POST https://immo-eliza-ezyg.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "area": 120,
      "property-type": "HOUSE",
      "rooms-number": 3,
      "zip-code": 1050,
      "garden": true,
      "building-state": "GOOD"
    }
  }'
```

### Example response

```json
{
  "prediction": 412500.0,
  "status_code": 200
}
```

### Required fields

| Field | Type | Description |
|---|---|---|
| `area` | `int` | Living area in m² |
| `property-type` | `str` | `"APARTMENT"` · `"HOUSE"` · `"OTHERS"` |
| `rooms-number` | `int` | Number of bedrooms |
| `zip-code` | `int` | 4-digit Belgian postal code |

> All other fields are optional. Missing values are automatically imputed by the model. See [API_DOCS.md](API_DOCS.md) for the full fields reference.

### Run locally

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Train and save the model
python train_model.py --data data/processed/cleaned_listings.csv

# 4. Start the API
uvicorn app:app --reload --port 8000
```

Open `http://localhost:8000/docs` for the interactive Swagger UI.

### Docker

```bash
docker build -t immo-api .
docker run -p 8000:8000 immo-api
```

---

## 📤 Output Schema

| Column | Type | Description | Example |
|---|---|---|---|
| `locality` | `str` | Postal code + city name | `7540 Kain` |
| `property_type` | `str` | High-level type | `House`, `Apartment` |
| `subtype` | `str` | Detailed subtype | `Villa`, `Apartment` |
| `price_eur` | `int` | Listing price in euros | `370000` |
| `num_rooms` | `float` | Number of bedrooms | `3.0` |
| `living_area_m2` | `float` | Living surface in m² | `130.0` |
| `fully_equipped_kitchen` | `float` | Kitchen fully equipped (0/1) | `0.0`, `1.0` |
| `terrace` | `float` | Terrace present (0/1) | `1.0`, `0.0` |
| `garden` | `float` | Garden present (0/1) | `1.0`, `0.0` |
| `land_surface_m2` | `float` | Total plot area in m² | `1328.0` |
| `num_facades` | `float` | Number of building facades | `4.0` |
| `swimming_pool` | `float` | Swimming pool (0/1) | `0.0`, `1.0` |
| `state_of_building` | `str` | Condition of the property | `Normal`, `New` |
| `postal_code` | `int` | Extracted 4-digit postal code | `7540` |
| `region` | `str` | Brussels / Flanders / Wallonia | `Flanders` |
| `price_per_m2` | `float` | Price divided by living area | `2846.15` |
| `building_state_encoded` | `int` | Ordinal encoding of building state | `5` |

---

## 📦 Dependencies

```
fastapi==0.110.0
uvicorn[standard]==0.29.0
pydantic==2.6.4
scikit-learn==1.4.2
xgboost==1.7.6
pandas==2.2.1
numpy==1.26.4
joblib==1.3.2
beautifulsoup4==4.14.3
requests==2.32.5
lxml==6.0.2
```

```bash
pip install -r requirements.txt
```

---

## 👥 Contributors

| Name | GitHub |
|---|---|
| Kliti Hamataj | [@KlitiHamataj](https://github.com/KlitiHamataj) |
| Jonbes Ahmadzai | [@JonbeshAhmadzai](https://github.com/JonbeshAhmadzai) |
| Mohamed Toukane | [@modev-git](https://github.com/modev-git) |
| Fernand Gatera | [@ndinhoo](https://github.com/ndinhoo) |

---

## ⚠️ Disclaimer

This project is intended for **personal research and educational purposes** only. Always respect the website's `robots.txt` and Terms of Service. The scraper includes a `REQUEST_DELAY` of 1.5 seconds between requests to avoid overloading the server.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
