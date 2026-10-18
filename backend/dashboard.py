"""Feature #5 -- extension-officer / policy dashboard.

An aggregated, ANONYMIZED view of outbreak and diagnosis data across all
farmers, meant for a local agricultural extension officer or government
body -- not the individual farmer. No single farmer's identity or exact
location appears here, only district-wide counts and cluster signals. This
is the one feature that turns Kisan Mitra from a per-farmer tool into
something a government or NGO could plausibly deploy region-wide.
"""
import csv
import os
from collections import Counter
from datetime import datetime, timedelta

from config import DATA_DIR
from schemas import DistrictDashboard, OutbreakCluster


def _load_plots():
    with open(os.path.join(DATA_DIR, "plots.csv"), encoding="utf-8") as f:
        return {row["plot_id"]: row for row in csv.DictReader(f)}


def _load_farmers():
    with open(os.path.join(DATA_DIR, "farmers.csv"), encoding="utf-8") as f:
        return {row["farmer_id"]: row for row in csv.DictReader(f)}


def _load_diagnosis_history():
    with open(os.path.join(DATA_DIR, "diagnosis_history.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _severity_from_count(count: int) -> str:
    if count >= 6:
        return "critical"
    if count >= 4:
        return "elevated"
    return "watch"


def build_district_dashboard(window_days: int = 7) -> DistrictDashboard:
    plots = _load_plots()
    farmers = _load_farmers()
    history = _load_diagnosis_history()
    now = datetime.now()
    cutoff = now - timedelta(days=window_days)

    recent = []
    for record in history:
        try:
            ts = datetime.fromisoformat(record["timestamp"])
        except ValueError:
            continue
        if ts >= cutoff:
            recent.append(record)

    disease_counts = Counter(r["disease"] for r in recent if r["disease"] not in ("", "healthy"))

    # Cluster by (disease, village) -- this is the anonymization boundary:
    # we aggregate to the village level, never to an individual plot or farmer.
    village_disease_counts: dict[tuple[str, str], int] = {}
    for r in recent:
        if r["disease"] in ("", "healthy"):
            continue
        plot = plots.get(r["plot_id"])
        if not plot:
            continue
        farmer = farmers.get(plot["farmer_id"])
        village = farmer["village"] if farmer else "Unknown"
        key = (r["disease"], village)
        village_disease_counts[key] = village_disease_counts.get(key, 0) + 1

    clusters = [
        OutbreakCluster(
            disease=disease, report_count=count, center_village=village,
            severity=_severity_from_count(count),
        )
        for (disease, village), count in village_disease_counts.items()
        if count >= 3  # same "min_reports" bar outbreak.py uses for a single farmer
    ]
    clusters.sort(key=lambda c: c.report_count, reverse=True)

    treatment_by_disease = {
        "early_blight": "copper_oxychloride_50wp", "late_blight": "mancozeb_75wp",
        "leaf_curl_virus": "imidacloprid_17.8sl", "septoria_leaf_spot": "mancozeb_75wp",
        "spider_mite_damage": "neem_oil",
    }
    treatment_demand = Counter()
    for disease, count in disease_counts.items():
        t = treatment_by_disease.get(disease)
        if t:
            treatment_demand[t] += count
    most_requested = treatment_demand.most_common(1)[0][0] if treatment_demand else None

    return DistrictDashboard(
        generated_at=now.isoformat(timespec="seconds"),
        window_days=window_days,
        total_diagnosis_reports=len(recent),
        disease_counts=dict(disease_counts),
        active_outbreak_clusters=clusters,
        most_requested_treatment=most_requested,
        plots_monitored=len(plots),
    )


if __name__ == "__main__":
    dashboard = build_district_dashboard()
    print(dashboard.model_dump_json(indent=2))
