import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import os

fake = Faker('en_IN')

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
OUTPUT_FILE = os.path.join(DATA_DIR, "aadhaar_synthetic_data.csv")
os.makedirs(DATA_DIR, exist_ok=True)

# --- CHANGED TO 5000 FOR BETTER PERFORMANCE ---
NUM_RECORDS = 5000

# SIMPLIFIED INDIA BORDER POLYGON
INDIA_POLYGON = [
    (35.5, 74.0), (34.5, 76.5), (32.0, 78.5), (31.0, 79.0), 
    (29.5, 80.5), (28.0, 81.0), (27.0, 84.0), (27.5, 88.0), 
    (28.0, 96.0), (29.0, 96.0), (26.0, 95.0), (24.0, 93.0), 
    (22.0, 89.0), (21.0, 87.0), (20.0, 86.0), (16.0, 81.0), 
    (10.0, 79.5), (8.0, 77.5),  (10.0, 76.0), (13.0, 74.5), 
    (16.0, 73.0), (20.0, 72.5), (22.5, 69.0), (24.0, 68.0), 
    (26.0, 70.0), (28.0, 71.0), (30.0, 72.5), (32.5, 74.0) 
]

# STRATEGY: FULL COVERAGE MESH
REGIONS = {
    # --- CORE ZONES ---
    'North_District':   {'lat': 28.6139, 'lng': 77.2090, 'rad': 450}, 
    'South_Tech_Hub':   {'lat': 12.9716, 'lng': 77.5946, 'rad': 400}, 
    'East_Industrial':  {'lat': 22.5726, 'lng': 88.3639, 'rad': 400}, 
    'West_Rural':       {'lat': 19.0760, 'lng': 72.8777, 'rad': 350}, 
    'Central_Metro':    {'lat': 23.2599, 'lng': 77.4126, 'rad': 450}, 
    
    # --- BRIDGE ZONES ---
    'Deccan_Plateau':   {'lat': 17.3850, 'lng': 78.4867, 'rad': 350, 'map_to': 'South_Tech_Hub'},
    'Gangetic_Plain':   {'lat': 25.3176, 'lng': 82.9739, 'rad': 400, 'map_to': 'North_District'},
    'Rajasthan_Desert': {'lat': 26.2389, 'lng': 73.0243, 'rad': 350, 'map_to': 'West_Rural'},
    'Odisha_Coast':     {'lat': 20.2961, 'lng': 85.8245, 'rad': 350, 'map_to': 'East_Industrial'},
    'Northeast_Hills':  {'lat': 26.1445, 'lng': 91.7362, 'rad': 300, 'map_to': 'East_Industrial'},
    'Gujarat_Coast':    {'lat': 22.2587, 'lng': 71.1924, 'rad': 300, 'map_to': 'West_Rural'},
    'Kashmir_Valley':   {'lat': 34.0837, 'lng': 74.7973, 'rad': 200, 'map_to': 'North_District'},

    # --- FILLER ZONES ---
    'Central_Gap':      {'lat': 21.1458, 'lng': 79.0882, 'rad': 300, 'map_to': 'Central_Metro'}, 
    'South_Gap':        {'lat': 15.8281, 'lng': 75.9000, 'rad': 250, 'map_to': 'South_Tech_Hub'}, 
    'West_Gap':         {'lat': 20.5937, 'lng': 78.9629, 'rad': 300, 'map_to': 'West_Rural'},     
    'North_Gap':        {'lat': 30.7333, 'lng': 76.7794, 'rad': 250, 'map_to': 'North_District'}, 
    'East_Gap':         {'lat': 25.5941, 'lng': 85.1376, 'rad': 300, 'map_to': 'East_Industrial'} 
}

def is_point_in_india(lat, lng):
    n = len(INDIA_POLYGON)
    inside = False
    p1x, p1y = INDIA_POLYGON[0]
    for i in range(n + 1):
        p2x, p2y = INDIA_POLYGON[i % n]
        if lng > min(p1y, p2y):
            if lng <= max(p1y, p2y):
                if lat <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (lng - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or lat <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def get_valid_geo_point(base_lat, base_lng, base_rad):
    while True:
        # Fuzzy Radius Logic
        actual_radius = base_rad * random.uniform(0.8, 1.2)
        radius_deg = actual_radius / 111.0
        
        u = random.random()
        v = random.random()
        w = radius_deg * np.sqrt(u)
        t = 2 * np.pi * v
        x = w * np.cos(t)
        y = w * np.sin(t)
        
        new_lat = base_lat + x
        new_lng = base_lng + (y / np.cos(np.radians(base_lat)))
        
        # Check if valid
        if is_point_in_india(new_lat, new_lng):
            return round(new_lat, 6), round(new_lng, 6)

def generate_synthetic_data(n):
    print(f"Generating {n} records (Performance Optimized)...")
    data = []
    region_keys = list(REGIONS.keys())
    
    for _ in range(n):
        r_key = random.choice(region_keys)
        region_data = REGIONS[r_key]
        
        district_name = region_data.get('map_to', r_key)
        
        lat, lng = get_valid_geo_point(region_data['lat'], region_data['lng'], region_data['rad'])
        
        gender = random.choice(['Male', 'Female', 'Other'])
        age = random.randint(5, 90)
        
        if age > 18:
            occupation = random.choice(['Farmer', 'Construction', 'IT_Professional', 'Student', 'Retired', 'Small_Business'])
        else:
            occupation = 'Student'
            
        days_since_update = random.randint(10, 3650) 
        last_update_date = datetime.now() - timedelta(days=days_since_update)
        
        # Math
        raw_decay = days_since_update * 0.012
        if age > 50: age_factor = 1 + ((age - 50)**2 / 3000) 
        elif age < 12: age_factor = 1 + ((12 - age)**2 / 800)
        else: age_factor = 1.0
            
        occ_factor = 1.0
        if occupation in ['Farmer', 'Construction']: occ_factor = 1.4
        elif occupation in ['Small_Business', 'Retired']: occ_factor = 1.15
            
        chaos = 0
        if random.random() < 0.15:
            chaos = random.randint(15, 30)

        total_decay_points = (raw_decay * age_factor * occ_factor) + chaos
        total_decay_points = min(total_decay_points, 100)
        
        health_score = int(100 - total_decay_points)
        fail_prob = total_decay_points / 100.0
        auth_status = 'Failed' if random.random() < fail_prob else 'Active'

        record = {
            'aadhaar_id': fake.unique.aadhaar_id(),
            'name': fake.name(),
            'age': age,
            'gender': gender,
            'district': district_name,
            'latitude': lat,
            'longitude': lng,
            'occupation': occupation,
            'last_update_date': last_update_date.strftime('%Y-%m-%d'),
            'days_since_update': days_since_update,
            'health_score': health_score,
            'auth_status': auth_status
        }
        data.append(record)
        
    return pd.DataFrame(data)

if __name__ == "__main__":
    df = generate_synthetic_data(NUM_RECORDS)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Success! Generated {NUM_RECORDS} records.")