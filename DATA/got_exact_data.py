import pandas as pd
import requests
import time
import math

# ---------- Haversine distance function (meters) ----------
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great‑circle distance between two points
    on the Earth (specified in decimal degrees).
    Returns distance in meters.
    """
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# 1. Load data
df = pd.read_csv('navic_clean_log_walking_3.csv')
print("CSV columns:", df.columns.tolist())

# 2. Use exact column names from your CSV – adjust if needed
LON_COL = 'Longitude'   # change to match your CSV
LAT_COL = 'Latitude'    # change to match your CSV

exact_lats = []
exact_lons = []
errors = []               # new list for deviation in meters

# 3. Correct OSRM endpoint for nearest road
OSRM_URL = "http://router.project-osrm.org/nearest/v1/cycling/"  # or walking/driving

for idx, row in df.iterrows():
    lon, lat = row[LON_COL], row[LAT_COL]
    url = f"{OSRM_URL}{lon},{lat}?number=1"

    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get('code') == 'Ok' and data.get('waypoints'):
            snapped = data['waypoints'][0]['location']  # [lon, lat]
            snapped_lon = snapped[0]
            snapped_lat = snapped[1]
        else:
            # No road found – keep original
            snapped_lon = lon
            snapped_lat = lat
    except Exception as e:
        print(f"Error at index {idx}: {e}")
        snapped_lon = lon
        snapped_lat = lat

    # Store snapped coordinates
    exact_lons.append(snapped_lon)
    exact_lats.append(snapped_lat)

    # Compute deviation in meters
    error_m = haversine(lon, lat, snapped_lon, snapped_lat)
    errors.append(error_m)

    # Be polite to the free API
    time.sleep(0.1)

    if idx % 100 == 0:
        print(f"Processed {idx} / {len(df)} points")

# 4. Add new columns and save
df['Exact_Longitude'] = exact_lons
df['Exact_Latitude']  = exact_lats
df['Error_meters']    = errors                     # new column with deviation

df.to_csv('navic_road_snapped_nearest.csv', index=False)
print("Done! Saved to navic_road_snapped_nearest.csv")