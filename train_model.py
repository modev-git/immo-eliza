import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from xgboost import XGBRegressor
from sklearn.metrics import r2_score

#Preprocessing function imported
from preprocessing.cleaning_data import preprocess

def main():
    # 1. Ingest Data
    print("Loading data...")
    df = pd.read_csv('../immo-eliza/analysis_KLITI/data/processed/cleaned_listings.csv')

    #Cleaning data
    preprocess(df)

    # Define features (X) and target (y)
    feature_cols = [
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
    "province_code"
    ]

    target = "price_eur"

    X = df[feature_cols]
    y = df[target]

    #Split Data
    print("Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    #Preprocessing Pipelines

    # Splitting feature_cols in two lists
    numeric_features = [
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

    categorical_features = [
        "property_type",
        "subtype",
        ]

    numeric_transformer = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())]
    )

    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore'))
    ])

    preprocessor = ColumnTransformer(transformers=[
    ('num', numeric_transformer, numeric_features),
    ('cat', categorical_transformer, categorical_features)
    ])

    #Build model pipeline
    print("Building pipeline...")

    #preprocessor = preprocessing()

    model_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', XGBRegressor(n_estimators=500,
                learning_rate=0.05,
                max_depth=6,
                random_state=42,
                n_jobs=-1))
    ])

    #Train model pipeline
    print("Training pipeline...")
    model_pipeline.fit(X_train, y_train)

    #Evaluate
    print("Evaluating model...")
    y_pred = model_pipeline.predict(X_test)
    score = r2_score(y_test, y_pred)
    print(f"Model R2 Score: {score:.4f}")

    #Serialize
    if score > 0.75:
        print("Saving model pipeline...")
        joblib.dump(model_pipeline, "model/model.joblib")
    else:
        print("Model performance is too low. Pipeline not saved")

if __name__ == "__main__":
    main()