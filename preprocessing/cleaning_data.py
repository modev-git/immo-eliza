import pandas as pd 
import numpy as np

MODEL_COLUMNS = [
    "property_type", "subtype",
    "num_rooms", "living_area_m2", "terrace",
    "garden", "land_surface_m2", "num_facades", "num_bathrooms",
    "building_state_encoded", "swimming_pool",
    "fully_equipped_kitchen","dist_train_km", 
    "dist_bus_km","province_code"
]


def preprocess(df):
    required_info = ["num_rooms", "living_area_m2", 
                     "property_type", "locality", "state_of_building"]


    for info in required_info:
        if info not in df or df[info] is None:
            raise ValueError(f"Error : '{info}' is missing.")


    # Postal code → province_code
    df["province_code"] = df["postal_code"] // 100

     # Règle spéciale pour les appartements
    if "land_surface_m2" not in df.columns:
        df["land_surface_m2"] = np.nan

    df.loc[df["property_type"] == "Apartment", "land_surface_m2"] = df.loc[
        df["property_type"] == "Apartment", "land_surface_m2"
    ].fillna(0)

    # Encode state_of_building
    state_order = {
        "To demolish": 1,
        "To restore": 2,
        "To renovate": 3,
        "To be renovated": 4,
        "Normal": 5,
        "Under construction": 6,
        "Fully renovated": 7,
        "Excellent": 8,
        "New": 9,
    }
    df["building_state_encoded"] = df["state_of_building"].map(state_order).fillna(5)

    df = df.reindex(columns=MODEL_COLUMNS, fill_value=np.nan)

    return df
        