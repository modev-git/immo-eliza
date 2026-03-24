from typing import Optional, Literal, Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from preprocessing.cleaning_data import preprocess
from predict.prediction import predict


app = FastAPI(
    title="ImmoEliza Price Prediction API",
    description="API to predict Belgian real estate prices",
    version="1.0.0",
)


# ===============================
# Request / response schemas
# ===============================
class HouseData(BaseModel):
    area: int = Field(..., gt=0, description="Living area in square meters")
    property_type: Literal["APARTMENT", "HOUSE", "OTHERS"] = Field(
    ...,
    alias="property-type",
    )
    rooms_number: int = Field(..., gt=0, alias="rooms-number")
    zip_code: int = Field(..., alias="zip-code")

    land_area: Optional[int] = Field(None, alias="land-area")
    garden: Optional[bool] = None
    garden_area: Optional[int] = Field(None, alias="garden-area")
    equipped_kitchen: Optional[bool] = Field(None, alias="equipped-kitchen")
    full_address: Optional[str] = Field(None, alias="full-address")
    swimming_pool: Optional[bool] = Field(None, alias="swimming-pool")
    furnished: Optional[bool] = None
    open_fire: Optional[bool] = Field(None, alias="open-fire")
    terrace: Optional[bool] = None
    terrace_area: Optional[int] = Field(None, alias="terrace-area")
    facades_number: Optional[int] = Field(None, alias="facades-number")
    dist_train_km: Optional[float] = Field(None, alias="dist-train-km")
    dist_bus_km: Optional[float] = Field(None, alias="dist-bus-km")
    building_state: Optional[
        Literal["NEW", "GOOD", "TO RENOVATE", "JUST RENOVATED", "TO REBUILD"]
    ] = Field(None, alias="building-state")

    model_config = ConfigDict(populate_by_name=True)


class PredictionRequest(BaseModel):
    data: HouseData


class PredictionResponse(BaseModel):
    prediction: Optional[float]
    status_code: int


# ===============================
# Helper functions
# ===============================
def map_property_type(value: str) -> str:
    mapping = {
        "APARTMENT": "Apartment",
        "HOUSE": "House",
        "OTHERS": "Others",
    }
    return mapping.get(value, "Others")


def map_building_state(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    mapping = {
        "NEW": "New",
        "GOOD": "Good",
        "TO RENOVATE": "To renovate",
        "JUST RENOVATED": "Fully renovated",
        "TO REBUILD": "To demolish",
    }
    return mapping.get(value, None)


def normalize_payload(house: HouseData) -> pd.DataFrame:
    """
    Convert API input into the dataframe format expected
    by preprocessing.cleaning_data.preprocess().
    """
    row = {
        "living_area_m2": house.area,
        "property_type": map_property_type(house.property_type),
        "num_rooms": house.rooms_number,
        "postal_code": house.zip_code,
        "land_surface_m2": house.land_area,
        "garden": int(house.garden) if house.garden is not None else 0,
        "terrace": int(house.terrace) if house.terrace is not None else 0,
        "terrace_area": house.terrace_area,
        "num_facades": house.facades_number,
        "swimming_pool": int(house.swimming_pool) if house.swimming_pool is not None else 0,
        "fully_equipped_kitchen": int(house.equipped_kitchen) if house.equipped_kitchen is not None else 0,
        "state_of_building": map_building_state(house.building_state),
        "locality": house.full_address if house.full_address else str(house.zip_code),
        "subtype": None,
        "num_bathrooms": None,
        "dist_train_km": house.dist_train_km,
        "dist_bus_km": house.dist_bus_km,
    }

    return pd.DataFrame([row])


# ===============================
# Routes
# ===============================
@app.get("/")
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
        normalized_df = normalize_payload(request.data)
        preprocessed_df = preprocess(normalized_df)
        prediction_value = predict(preprocessed_df)

        if hasattr(prediction_value, "__len__") and not isinstance(prediction_value, (str, bytes)):
            prediction_value = prediction_value[0]

        return PredictionResponse(
            prediction=float(prediction_value),
            status_code=200,
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc