from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
import os
import sys
from backend.sms_manager import send_sms_nudge 

app = FastAPI(title="Aadhaar Health-Score API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PATHS
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
model_path = os.path.join(project_root, 'ml_engine', 'aadhaar_model.pkl')
data_path = os.path.join(project_root, 'data', 'aadhaar_synthetic_data.csv')

# LOAD MODEL
try:
    artifacts = joblib.load(model_path)
    model = artifacts['model']
    encoders = artifacts['encoders']
    print("✅ Model loaded.")
except FileNotFoundError:
    model = None

class CitizenData(BaseModel):
    age: int
    days_since_update: int
    district: str
    occupation: str
    gender: str

@app.post("/predict_health_score")
def predict_health(data: CitizenData):
    if not model: raise HTTPException(status_code=500, detail="Model missing")
    try:
        input_data = pd.DataFrame([{
            'age': data.age, 'days_since_update': data.days_since_update,
            'district': data.district, 'occupation': data.occupation, 'gender': data.gender
        }])

        for col, encoder in encoders.items():
            if col in input_data.columns:
                try: input_data[col] = encoder.transform(input_data[col])
                except ValueError: input_data[col] = 0

        fail_prob = model.predict_proba(input_data)[0][1]
        health_score = int(100 - (fail_prob * 100))

        status = "Safe"
        nudge_triggered = False
        if health_score < 40:
            status = "CRITICAL_RISK"
            nudge_triggered = send_sms_nudge("Citizen", health_score, fail_prob)
        elif health_score < 70:
            status = "Moderate_Risk"

        return {
            "health_score": health_score,
            "failure_probability": float(fail_prob),
            "status": status,
            "nudge_required": health_score < 40,
            "sms_sent": nudge_triggered
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- NEW ENDPOINT: SERVE ALL 10K POINTS ---
@app.get("/map_data")
def get_map_data():
    if not os.path.exists(data_path): return []
    try:
        df = pd.read_csv(data_path)
        # Only send what we need for the map to keep it fast
        # We limit to 5000 points if 10k is too slow, but let's try 10k first.
        map_df = df[['latitude', 'longitude', 'health_score', 'district']]
        return map_df.to_dict(orient="records")
    except Exception as e:
        print(f"Error serving map data: {e}")
        return []