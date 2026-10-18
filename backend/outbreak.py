"""Prompt 15 — outbreak early-warning.

Real logic, no mocking needed: a geo-radius + time-window query over
diagnosis_history.csv (standing in for a Firestore collection), then a
templated synthesis step (standing in for the Gemini synthesis call) that
turns 3+ matching nearby reports into a plain-language alert.
"""
import csv
import math
import os
from datetime import datetime, timedelta

from config import DATA_DIR
from schemas import OutbreakAlert


def _haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return r * 2 * math.asin(math.sqrt(a))


def _load_plots():
    with open(os.path.join(DATA_DIR, "plots.csv"), encoding="utf-8") as f:
        return {row["plot_id"]: row for row in csv.DictReader(f)}


def _load_diagnosis_history():
    with open(os.path.join(DATA_DIR, "diagnosis_history.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check_outbreak(lat: float, lon: float, radius_km: float = 10, window_days: int = 7,
                    min_reports: int = 3, exclude_plot_id: str = None) -> OutbreakAlert | None:
    plots = _load_plots()
    history = _load_diagnosis_history()
    now = datetime.now()
    cutoff = now - timedelta(days=window_days)

    nearby_by_disease: dict[str, int] = {}
    for record in history:
        if record["disease"] in ("healthy", ""):
            continue
        if record["plot_id"] == exclude_plot_id:
            continue
        plot = plots.get(record["plot_id"])
        if not plot:
            continue
        try:
            ts = datetime.fromisoformat(record["timestamp"])
        except ValueError:
            continue
        if ts < cutoff:
            continue
        dist = _haversine_km(lat, lon, float(plot["lat"]), float(plot["lon"]))
        if dist <= radius_km:
            nearby_by_disease[record["disease"]] = nearby_by_disease.get(record["disease"], 0) + 1

    if not nearby_by_disease:
        return None
    disease, count = max(nearby_by_disease.items(), key=lambda kv: kv[1])
    if count < min_reports:
        return None

    message = (
        f"{disease.replace('_', ' ').title()} has been reported on {count} nearby tomato "
        f"plots in the last {window_days} days. Inspect your crop today — early action "
        f"prevents spread."
    )
    return OutbreakAlert(disease=disease, nearby_report_count=count, radius_km=radius_km,
                          window_days=window_days, message=message)


if __name__ == "__main__":
    plots = _load_plots()
    # Use the first plot from the dataset as the "farmer's own plot" for this test.
    sample_plot = next(iter(plots.values()))
    alert = check_outbreak(float(sample_plot["lat"]), float(sample_plot["lon"]), exclude_plot_id=sample_plot["plot_id"])
    print(f"Checking from plot {sample_plot['plot_id']} ({sample_plot['lat']}, {sample_plot['lon']}):")
    print(alert.message if alert else "No outbreak detected nearby.")
