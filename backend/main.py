"""Prompt 19 — Cloud Run backend service (FastAPI).

Endpoints: POST /diagnose, GET /dealer-lookup, GET /sell-price,
GET /outbreak-check, GET /district-dashboard. In the real deployment this is
what Cloud Run hosts; locally it runs with `uvicorn main:app --reload`
against the same mock-mode logic exercised by every module above.
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from advisory import build_advisory_response
from config import USE_MOCK
from dashboard import build_district_dashboard
from market_tools import find_best_sell_price, find_nearest_dealer
from outbreak import check_outbreak
from schemas import AdvisoryResponse, DealerMatch, DistrictDashboard, OutbreakAlert, SellPriceMatch

app = FastAPI(title="Kisan Mitra API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the deployed Firebase Hosting origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "mock_mode": USE_MOCK}


@app.post("/diagnose", response_model=AdvisoryResponse)
def diagnose(
    symptom_description: str,
    farmer_lat: float,
    farmer_lon: float,
    farmer_language: str = "kn-IN",
    plot_id: str | None = None,
    near_harvest: bool = False,
):
    return build_advisory_response(
        symptom_description=symptom_description,
        farmer_lat=farmer_lat,
        farmer_lon=farmer_lon,
        farmer_language=farmer_language,
        plot_id=plot_id,
        near_harvest=near_harvest,
    )


@app.get("/dealer-lookup", response_model=DealerMatch | None)
def dealer_lookup(treatment: str = Query(...)):
    return find_nearest_dealer(treatment)


@app.get("/sell-price", response_model=SellPriceMatch | None)
def sell_price(crop: str = Query("tomato")):
    return find_best_sell_price(crop)


@app.get("/outbreak-check", response_model=OutbreakAlert | None)
def outbreak_check(lat: float, lon: float, exclude_plot_id: str | None = None):
    return check_outbreak(lat, lon, exclude_plot_id=exclude_plot_id)


@app.get("/district-dashboard", response_model=DistrictDashboard)
def district_dashboard(window_days: int = 7):
    """Feature #5 — aggregated, anonymized view for an extension officer or
    local agricultural body. No individual farmer identity or exact plot
    location is exposed here, only village-level and district-level counts."""
    return build_district_dashboard(window_days=window_days)
