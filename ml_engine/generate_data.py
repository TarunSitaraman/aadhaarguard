import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import os

# Initialize Faker for Indian names/addresses
fake = Faker('en_IN')

# Configuration - ROBUST PATH HANDLING
# 1. Get the directory where this script (generate_data.py) is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Go up one level to the project root ('aadhaarguard')
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# 3. Define the path to the data folder
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

# 4. Create the full path for the CSV
OUTPUT_FILE = os.path.join(DATA_DIR, "aadhaar_synthetic_data.csv")

# Safety Check: Create the directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

NUM_RECORDS = 10000

def generate_synthetic_data(n):
    print(f"Generating {n} synthetic records...")
    
    data = []
    
    for _ in range(n):
        # 1. Basic Demographics
        gender = random.choice(['Male', 'Female', 'Other'])
        age = random.randint(5, 90)
        
        # 2. Location (Simulating Districts)
        # We'll use 5 fictional districts with varying risk profiles
        districts = ['North_District', 'South_Tech_Hub', 'East_Industrial', 'West_Rural', 'Central_Metro']
        district = random.choice(districts)
        
        # 3. Occupation (Crucial for Biometric Decay)
        # Manual laborers have higher risk of fingerprint fading
        if age > 18:
            occupation = random.choice(['Farmer', 'Construction', 'IT_Professional', 'Student', 'Retired', 'Small_Business'])
        else:
            occupation = 'Student'
            
        # 4. Biometric History
        # Randomize the last time they updated their data (0 to 10 years ago)
        days_since_update = random.randint(10, 3650) 
        last_update_date = datetime.now() - timedelta(days=days_since_update)
        
        # 5. Calculate "Biometric Decay" (The logic we want our ML to learn later)
        # Base decay based on time
        decay_score = days_since_update * 0.01 
        
        # Accelerate decay for manual labor (wear and tear)
        if occupation in ['Farmer', 'Construction']:
            decay_score *= 1.5
            
        # Accelerate decay for very young or very old (biological changes)
        if age < 15 or age > 70:
            decay_score *= 1.3
            
        # 6. Determine Authentication Status
        # If decay score is high, the auth is likely to fail
        # This creates our "Target Variable" for the ML model
        fail_probability = 1 / (1 + np.exp(-(decay_score - 10))) # Sigmoid function to normalize
        auth_status = 'Failed' if random.random() < fail_probability else 'Active'

        record = {
            'aadhaar_id': fake.unique.aadhaar_id(),
            'name': fake.name(),
            'age': age,
            'gender': gender,
            'district': district,
            'occupation': occupation,
            'last_update_date': last_update_date.strftime('%Y-%m-%d'),
            'days_since_update': days_since_update,
            'mobile_linked': random.choice([True, False]), # Some people don't have mobile linked
            'auth_status': auth_status  # This is what we want to predict!
        }
        data.append(record)
        
    return pd.DataFrame(data)

if __name__ == "__main__":
    df = generate_synthetic_data(NUM_RECORDS)
    
    # Save to CSV
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Success! Generated {NUM_RECORDS} records.")
    print(f"📂 Data saved to: {OUTPUT_FILE}")
    print("\nSample Data:")
    print(df.head())