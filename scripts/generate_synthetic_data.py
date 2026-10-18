"""Prompt 1 — synthetic farmer/plot/diagnosis dataset for Kisan Mitra.

Generates farmers.csv, plots.csv, diagnosis_history.csv into ../data/.
Clusters some diagnosis timestamps within a 4-day window and 6km radius
to simulate an outbreak, which the outbreak-alert feature detects.
"""
import csv
import os
import random
from datetime import datetime, timedelta

from faker import Faker

# Faker has no kn_IN locale; en_IN still produces realistic Indian names and
# is the closest supported locale for this demo's purposes.
fake = Faker("en_IN")
random.seed(42)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")

# Center of the demo area: Kolar district, Karnataka -- one of India's major
# tomato-growing belts.
CENTER_LAT, CENTER_LON = 13.1372, 78.1298

DISEASES = ["early_blight", "late_blight", "leaf_curl_virus", "healthy"]
DISEASE_WEIGHTS = [0.35, 0.20, 0.15, 0.30]

VILLAGES = ["Kolar", "Bangarpet", "Mulbagal", "Srinivaspur", "Malur", "Chintamani", "Chikkaballapur"]


def jitter_latlon(lat, lon, max_km=10):
    # Rough conversion: 1 degree lat ~ 111km
    deg_radius = max_km / 111.0
    dlat = random.uniform(-deg_radius, deg_radius)
    dlon = random.uniform(-deg_radius, deg_radius)
    return round(lat + dlat, 5), round(lon + dlon, 5)


def gen_farmers(n=50):
    rows = []
    for i in range(1, n + 1):
        rows.append({
            "farmer_id": f"F{i:03d}",
            "name": fake.name(),
            "village": random.choice(VILLAGES),
            "district": "Karnataka",
            "preferred_language": "kn-IN",
            "phone": fake.msisdn()[:10],
        })
    return rows


def gen_plots(farmers, n=80):
    rows = []
    for i in range(1, n + 1):
        farmer = random.choice(farmers)
        lat, lon = jitter_latlon(CENTER_LAT, CENTER_LON, max_km=10)
        rows.append({
            "plot_id": f"P{i:03d}",
            "farmer_id": farmer["farmer_id"],
            "crop": "tomato",
            "area_acres": round(random.uniform(0.5, 4.0), 2),
            "lat": lat,
            "lon": lon,
        })
    return rows


def gen_diagnosis_history(plots, n=300):
    rows = []
    now = datetime.now()

    # Reserve a handful of records to form a deliberate outbreak cluster:
    # same disease, within 6km, within the last 4 days.
    outbreak_plots = random.sample(plots, 4)
    outbreak_center = outbreak_plots[0]
    outbreak_disease = "early_blight"
    for i, plot in enumerate(outbreak_plots):
        rows.append({
            "diagnosis_id": f"D{len(rows)+1:04d}",
            "plot_id": plot["plot_id"],
            "timestamp": (now - timedelta(days=random.uniform(0, 4))).isoformat(timespec="seconds"),
            "disease": outbreak_disease,
            "confidence_score": round(random.uniform(0.72, 0.9), 2),
            "treatment_applied": "" if i > 0 else "copper_oxychloride_50wp",
        })

    # Fill the rest with ordinary scattered history over the last 60 days.
    while len(rows) < n:
        plot = random.choice(plots)
        disease = random.choices(DISEASES, weights=DISEASE_WEIGHTS)[0]
        rows.append({
            "diagnosis_id": f"D{len(rows)+1:04d}",
            "plot_id": plot["plot_id"],
            "timestamp": (now - timedelta(days=random.uniform(0, 60))).isoformat(timespec="seconds"),
            "disease": disease,
            "confidence_score": round(random.uniform(0.55, 0.95), 2) if disease != "healthy" else 1.0,
            "treatment_applied": "" if disease == "healthy" else random.choice(
                ["copper_oxychloride_50wp", "mancozeb_75wp", "imidacloprid_17.8sl", ""]
            ),
        })
    return rows


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows -> {path}")


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)

    farmers = gen_farmers(50)
    plots = gen_plots(farmers, 80)
    diagnosis_history = gen_diagnosis_history(plots, 300)

    write_csv(os.path.join(DATA_DIR, "farmers.csv"), farmers,
              ["farmer_id", "name", "village", "district", "preferred_language", "phone"])
    write_csv(os.path.join(DATA_DIR, "plots.csv"), plots,
              ["plot_id", "farmer_id", "crop", "area_acres", "lat", "lon"])
    write_csv(os.path.join(DATA_DIR, "diagnosis_history.csv"), diagnosis_history,
              ["diagnosis_id", "plot_id", "timestamp", "disease", "confidence_score", "treatment_applied"])

    print("\nOutbreak cluster seeded as diagnosis_history.csv rows D0001-D0004 (same disease, within 6km, within 4 days)")
