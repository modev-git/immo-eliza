from typing import Optional, Literal, Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from preprocessing.cleaning_data import preprocess
from predict.prediction import predict


app = FastAPI(
    title="ImmoEliza — Belgian Real Estate Price Predictor",
    description=(
        "Predicts house and apartment prices across Belgium using an XGBoost "
        "model trained on ~23,000 listings scraped from immovlan.be."
    ),
    version="1.0.0",
)


# ===============================
# Request / response schemas
# ===============================

class HouseData(BaseModel):
    area: int = Field(..., gt=0, description="Living area in m²")
    property_type: str = Field(..., alias="property-type", description="Type of property ('House', 'Apartment', 'Other')")
    rooms_number: int = Field(..., alias="rooms-number")
    zip_code: int = Field(..., alias="zip-code")
    land_area: Optional[int] = Field(None, alias="land-area")
    garden: Optional[bool] = Field(default=False)
    garden_area: Optional[int] = Field(None, alias="garden-area")
    equipped_kitchen: Optional[bool] = Field(alias="equipped-kitchen", default=False)
    full_address: Optional[str] = Field(None, alias="full-address")
    swimming_pool: Optional[bool] = Field(alias="swimming-pool", default=False)
    furnished: Optional[bool] = Field(default=False)
    terrace: Optional[bool] = Field(default=False)
    terrace_area: Optional[int] = Field(None, alias="terrace-area")
    facades_number: Optional[int] = Field(None, alias="facades-number")
    building_state: Optional[
        Literal["NEW", "GOOD", "TO RENOVATE", "JUST RENOVATED", "TO REBUILD"]
    ] = Field(default=None, alias="building-state", description="State of the building")

    model_config = ConfigDict(populate_by_name=True)


class PredictionRequest(BaseModel):
    data: HouseData


class PredictionResponse(BaseModel):
    prediction: Optional[float]
    status_code: int

# ===============================
# Routes
# ===============================

@app.get("/", summary="Health check")
def healthcheck() -> str:
    return "alive"


@app.get("/predict")
def predict_info() -> dict[str, Any]:
    return {
        "message": "Send a POST request to /predict with house data under the 'data' key.",
        "expected_format": {
            "data": {
                "area": 120,
                "property-type": "HOUSE",
                "rooms-number": 3,
                "zip-code": 1000,
                "land-area": 300,
                "garden": True,
                "garden-area": 100,
                "equipped-kitchen": True,
                "full-address": "Example street 1, 1000 Brussels",
                "swimming-pool": False,
                "furnished": False,
                "open-fire": False,
                "terrace": True,
                "terrace-area": 20,
                "facades-number": 2,
                "dist-train-km": 1.2,
                "dist-bus-km": 0.3,
                "building-state": "GOOD",
            }
        },
    }


@app.post("/predict", response_model=PredictionResponse)
def predict_price(request: PredictionRequest) -> PredictionResponse:
    try:
        raw = request.data.model_dump(by_alias=True)
        X = preprocess(raw)
        price = predict(X)
        return PredictionResponse(prediction=price, status_code=200)

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(exc)}")
