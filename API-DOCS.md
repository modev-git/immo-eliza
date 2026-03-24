# ImmoEliza — Price Prediction API

> Predict Belgian real estate prices instantly. Send property features in JSON, get back a predicted market price in euros.

---

## Overview

| | |
|---|---|
| **Model** | XGBoost Regressor |
| **R² Score** | 0.786 |
| **Training data** | 23,106 listings from immovlan.be |
| **Coverage** | 11 Belgian provinces |
| **Version** | 1.0.0 |

---

## Base URL

```
https://<your-service>.onrender.com
```

Interactive docs (Swagger UI) available at `/docs`.

---

## Endpoints

### `GET /`
Health check. Returns `"alive"` when the server is running.

**Response `200`**
```json
"alive"
```

---

### `GET /predict`
Returns a description of the POST `/predict` endpoint format — useful for self-discovery.

---

### `POST /predict`
Accepts property features and returns a predicted price in EUR.

**Request body**
```json
{
  "data": {
    "area": 120,
    "property-type": "HOUSE",
    "rooms-number": 3,
    "zip-code": 1050,
    "land-area": 300,
    "garden": true,
    "garden-area": 150,
    "equipped-kitchen": true,
    "full-address": "Rue de la Loi 1, 1050 Bruxelles",
    "swimming-pool": false,
    "furnished": false,
    "terrace": true,
    "terrace-area": 20,
    "facades-number": 4,
    "building-state": "GOOD"
  }
}
```

**Response `200`**
```json
{
  "prediction": 412500.0,
  "status_code": 200
}
```

---

## Fields Reference

| Field | Type | Required | Description |
|---|---|---|---|
| `area` | `int` | ✅ | Living area in m² |
| `property-type` | `str` | ✅ | `"APARTMENT"` · `"HOUSE"` · `"OTHERS"` |
| `rooms-number` | `int` | ✅ | Number of bedrooms |
| `zip-code` | `int` | ✅ | 4-digit Belgian postal code |
| `land-area` | `int` | ❌ | Total land surface in m² |
| `garden` | `bool` | ❌ | Garden present |
| `garden-area` | `int` | ❌ | Garden area in m² |
| `equipped-kitchen` | `bool` | ❌ | Fully equipped kitchen |
| `full-address` | `str` | ❌ | Free-text address *(not used by model)* |
| `swimming-pool` | `bool` | ❌ | Swimming pool present |
| `furnished` | `bool` | ❌ | Furnished *(not used by model)* |
| `terrace` | `bool` | ❌ | Terrace present |
| `terrace-area` | `int` | ❌ | Terrace area in m² |
| `facades-number` | `int` | ❌ | Number of facades |
| `building-state` | `str` | ❌ | `"NEW"` · `"GOOD"` · `"TO RENOVATE"` · `"JUST RENOVATED"` · `"TO REBUILD"` |

> Missing optional fields are automatically filled by the model using median/mode imputation.

---

## Error Codes

| Code | Meaning | Example |
|---|---|---|
| `200` | Success | Prediction returned |
| `400` | Bad Request | Missing required field or invalid value |
| `503` | Service Unavailable | Model file not found on server |
| `500` | Internal Server Error | Unexpected error |

**Error response shape**
```json
{
  "detail": "Missing required field: 'area'"
}
```

---

## Example

```bash
curl -X POST https://<your-service>.onrender.com/predict \
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

---

## Model Details

The model predicts at **province level** — it uses the first two digits of the zip code (`province_code`) rather than the full postal code. This means it cannot distinguish between communes within the same province.

| Feature | Importance |
|---|---|
| `living_area_m2` | Highest |
| `province_code` | High |
| `num_rooms` | High |
| `land_surface_m2` | Medium |
| `building_state_encoded` | Medium |

---

## Built With

- [FastAPI](https://fastapi.tiangolo.com)
- [XGBoost](https://xgboost.readthedocs.io)
- [scikit-learn](https://scikit-learn.org)
- Data from [immovlan.be](https://immovlan.be)
