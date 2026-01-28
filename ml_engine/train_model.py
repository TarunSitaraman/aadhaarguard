import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# CONFIGURATION
# Robust path handling (same as before)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'aadhaar_synthetic_data.csv')
MODEL_PATH = os.path.join(PROJECT_ROOT, 'ml_engine', 'aadhaar_model.pkl')
ENCODER_PATH = os.path.join(PROJECT_ROOT, 'ml_engine', 'encoders.pkl')

def train_aadhaar_model():
    print("⏳ Loading data...")
    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: Data file not found at {DATA_PATH}")
        return

    df = pd.read_csv(DATA_PATH)
    
    # --- 1. PREPROCESSING ---
    print("⚙️  Preprocessing data...")
    
    # Convert 'auth_status' to numbers: Active=0, Failed=1 (Target Variable)
    # We want to predict failure, so Failed is the "positive" class (1)
    df['target'] = df['auth_status'].apply(lambda x: 1 if x == 'Failed' else 0)
    
    # We drop columns we don't need for prediction (like Name or ID)
    # We ONLY keep features that affect biometric decay
    features = ['age', 'days_since_update', 'district', 'occupation', 'gender']
    X = df[features]
    y = df['target']
    
    # Handle Categorical Data (District, Occupation, Gender)
    # Machine learning models only understand numbers, not words.
    # We use LabelEncoders to convert "Farmer" -> 1, "Student" -> 2, etc.
    encoders = {}
    categorical_cols = ['district', 'occupation', 'gender']
    
    for col in categorical_cols:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col])
        encoders[col] = le  # Save encoder to reverse this later if needed
        
    # Split data: 80% for training, 20% for testing
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # --- 2. TRAIN MODEL ---
    print("🧠 Training XGBoost Model...")
    
    # Initialize XGBoost Classifier
    model = xgb.XGBClassifier(
        n_estimators=100,     # Number of "trees" in the forest
        learning_rate=0.1,    # How fast it learns
        max_depth=5,          # How complex each tree can be
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)

    # --- 3. EVALUATE ---
    print("📊 Evaluating Model...")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"✅ Model Accuracy: {accuracy * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # --- 4. SAVE ARTIFACTS ---
    print("💾 Saving Model & Encoders...")
    
    # We save a dictionary containing the model AND the encoders
    # We need the encoders later to translate user input for the API
    artifacts = {
        'model': model,
        'encoders': encoders
    }
    
    joblib.dump(artifacts, MODEL_PATH)
    print(f"🎉 Model saved to: {MODEL_PATH}")

if __name__ == "__main__":
    train_aadhaar_model()