"""Build-time export for the client-only deployment.

Runs the existing (private, server-side) dashboard.py aggregation ONCE,
against the full farmers.csv/plots.csv/diagnosis_history.csv in backend/data/,
and writes only the resulting anonymized aggregate to frontend/data/dashboard_data.json.

This is the one piece of logic that stays server-side (i.e. "build-time", run
by a developer, never in the browser) specifically so raw farmer_id/village
linkage never ships in the public static bundle -- see the plan's privacy
section. Re-run this and redeploy whenever the dashboard snapshot should
refresh; it is NOT recomputed live by the static site.
"""
import json
import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND_DIR)

from dashboard import build_district_dashboard  # noqa: E402

OUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "frontend", "data", "dashboard_data.json",
)


def main():
    dashboard = build_district_dashboard(window_days=7)
    data = dashboard.model_dump()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Wrote {OUT_PATH}")
    print(f"  total_diagnosis_reports={data['total_diagnosis_reports']}")
    print(f"  plots_monitored={data['plots_monitored']}")
    print(f"  active_outbreak_clusters={len(data['active_outbreak_clusters'])}")


if __name__ == "__main__":
    main()
