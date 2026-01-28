from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import os
import sys

# Initialize the App
app = FastAPI(title="Aadhaar Health-Score API")

# --- 1. LOAD THE TRAINED MODEL ---
# Robust path finding to locate the model in the sibling directory 'ml_engine'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
model_path = os.path.join(project_root, 'ml_engine', 'aadhaar_model.pkl')

print(f"Loading model from: {model_path}")

try:
    artifacts = joblib.load(model_path)
    model = artifacts['model']
    encoders = artifacts['encoders']
    print("✅ Model and Encoders loaded successfully!")
except FileNotFoundError:
    print("❌ Error: Model file not found. Run train_model.py first.")
    model = None
    encoders = None

# --- 2. DEFINE INPUT FORMAT ---
# This ensures the API receives exactly the data it needs
class CitizenData(BaseModel):
    age: int
    days_since_update: int
    district: str
    occupation: str
    gender: str

# --- 3. PREDICTION ENDPOINT ---
@app.post("/predict_health_score")
def predict_health(data: CitizenData):
    if not model:
        raise HTTPException(status_code=500, detail="Model not loaded")

    try:
        # Prepare the input dataframe
        input_data = pd.DataFrame([{
            'age': data.age,
            'days_since_update': data.days_since_update,
            'district': data.district,
            'occupation': data.occupation,
            'gender': data.gender
        }])

        # Encode categorical variables using the saved encoders
        # (e.g., Converts 'Farmer' -> 1)
        for col, encoder in encoders.items():
            if col in input_data.columns:
                # Handle unknown categories safely
                try:
                    input_data[col] = encoder.transform(input_data[col])
                except ValueError:
                    # If we see a new job/district not in training, default to 0
                    input_data[col] = 0

        # Predict Probability of Failure (Class 1)
        # model.predict_proba returns [[prob_success, prob_fail]]
        fail_prob = model.predict_proba(input_data)[0][1]
        
        # Calculate Health Score (Inverse of failure probability)
        # Score 100 = Perfect Health, 0 = High Risk
        health_score = int(100 - (fail_prob * 100))

        # Determine Status
        status = "Safe"
        if health_score < 40:
            status = "CRITICAL_RISK"
        elif health_score < 70:
            status = "Moderate_Risk"

        return {
            "health_score": health_score,
            "failure_probability": float(fail_prob),
            "status": status,
            "nudge_required": health_score < 40
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint to check if server is running
@app.get("/")
def read_root():
    return {"message": "Aadhaar Predictive System API is Running"}