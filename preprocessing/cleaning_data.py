"""
preprocessing/cleaning_data.py

Converts the raw JSON payload (as received by the /predict endpoint)
into a pandas DataFrame that matches exactly what the saved sklearn pipeline
expects as input.

Public API
----------
preprocess(data: dict) -> pd.DataFrame
    Raises ValueError if a required field is missing or invalid.
"""

import pandas as pd
import numpy as np

# ── Constants ─────────────────────────────────────────────────────────────────

# Required fields in the incoming payload
REQUIRED_FIELDS = ["area", "property-type", "rooms-number", "zip-code"]

# Map API property-type → model property_type
PROPERTY_TYPE_MAP = {
    "APARTMENT": "Apartment",
    "HOUSE": "House",
    "OTHERS": "Other",
}

# Map API building-state → building_state_encoded (ordinal, same as cleaning notebook)
BUILDING_STATE_MAP = {
    "TO REBUILD": 1,  # To demolish
    "TO RENOVATE": 3,  # To renovate
    "GOOD": 5,  # Normal
    "JUST RENOVATED": 7,  # Fully renovated
    "NEW": 9,  # New
}

# Ordered list of feature columns the pipeline expects
FEATURE_COLS = [
    "property_type",
    "subtype",
    "num_rooms",
    "living_area_m2",
    "terrace",
    "garden",
    "land_surface_m2",
    "num_facades",
    "num_bathrooms",
    "building_state_encoded",
    "swimming_pool",
    "fully_equipped_kitchen",
    "dist_train_km",
    "dist_bus_km",
    "province_code",
]


# ── Public function ───────────────────────────────────────────────────────────


def preprocess(data: dict) -> pd.DataFrame:
    """
    Validate and transform a single property payload into a feature DataFrame.

    Parameters
    ----------
    data : dict
        The value of the "data" key from the POST body.

    Returns
    -------
    pd.DataFrame
        One-row DataFrame with columns matching FEATURE_COLS.

    Raises
    ------
    ValueError
        If a required field is absent or contains an invalid value.
    """
    # ── 1. Check required fields ──────────────────────────────────────────────
    for field in REQUIRED_FIELDS:
        if data.get(field) is None:
            raise ValueError(f"Missing required field: '{field}'")

    # ── 2. Map property type ──────────────────────────────────────────────────
    raw_type = str(data["property-type"]).upper()
    if raw_type not in PROPERTY_TYPE_MAP:
        raise ValueError(
            f"Invalid property-type '{data['property-type']}'. "
            f"Must be one of: {list(PROPERTY_TYPE_MAP.keys())}"
        )
    property_type = PROPERTY_TYPE_MAP[raw_type]

    # ── 3. Province code (first two digits of zip code) ───────────────────────
    try:
        zip_code = int(data["zip-code"])
    except (ValueError, TypeError):
        raise ValueError(f"Invalid zip-code '{data['zip-code']}': must be an integer.")
    province_code = zip_code // 100

    # ── 4. Building-state encoding ────────────────────────────────────────────
    building_state_encoded = np.nan
    if data.get("building-state") is not None:
        raw_state = str(data["building-state"]).upper()
        building_state_encoded = BUILDING_STATE_MAP[raw_state]

    # ── 5. Boolean helpers ────────────────────────────────────────────────────
    def to_binary(value) -> int | None:
        """Convert bool/None to 1/0/None."""
        if value is None:
            return None
        return 1 if value else 0

    # ── 6. Assemble the feature row ───────────────────────────────────────────
    row = {
        "property_type": property_type,
        "subtype": None,  # not in API → imputer fills
        "num_rooms": data.get("rooms-number"),
        "living_area_m2": data.get("area"),
        "terrace": to_binary(data.get("terrace")),
        "garden": to_binary(data.get("garden")),
        "land_surface_m2": data.get("land-area"),
        "num_facades": data.get("facades-number"),
        "num_bathrooms": None,  # not in API → imputer fills
        "building_state_encoded": building_state_encoded,  # None → imputer fills
        "swimming_pool": to_binary(data.get("swimming-pool")),
        "fully_equipped_kitchen": to_binary(data.get("equipped-kitchen")),
        "dist_train_km": None,  # not in API → imputer fills
        "dist_bus_km": None,  # not in API → imputer fills
        "province_code": province_code,
    }

    return pd.DataFrame([row], columns=FEATURE_COLS)
