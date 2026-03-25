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
def predict_info():
    """
    Explains what data the POST /predict endpoint expects.
    """
    return {
        "description": (
            "Send a POST request to /predict with a JSON body containing "
            "property features. The API returns a predicted price in EUR."
        ),
        "required_fields": {
            "area": "int — living area in m²",
            "property-type": "str — 'APARTMENT', 'HOUSE', or 'OTHERS'",
            "rooms-number": "int — number of bedrooms",
            "zip-code": "int — Belgian 4-digit postal code",
        },
        "optional_fields": {
            "land-area": "int — total land surface in m² (houses)",
            "garden": "bool — garden present",
            "garden-area": "int — garden area in m²",
            "equipped-kitchen": "bool — fully equipped kitchen",
            "swimming-pool": "bool — swimming pool present",
            "terrace": "bool — terrace present",
            "terrace-area": "int — terrace area in m²",
            "facades-number": "int — number of facades",
            "building-state": (
                "str — one of: 'NEW', 'GOOD', 'TO RENOVATE', "
                "'JUST RENOVATED', 'TO REBUILD'"
            ),
        },
        "example_request": {
            "data": {
                "area": 120,
                "property-type": "HOUSE",
                "rooms-number": 3,
                "zip-code": 1050,
                "garden": True,
                "building-state": "GOOD",
            }
        },
        "example_response": {"prediction": 385000.0, "status_code": 200},
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
