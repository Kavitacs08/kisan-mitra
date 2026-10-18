"""Prompts 11 & 14 — end-to-end advisory assembly and agent orchestration.

Decides which tool to call based on the diagnosis outcome (buy-side dealer
lookup if diseased, sell-side price lookup if healthy and near harvest),
and assembles everything — diagnosis, weather, translated/spoken advisory,
market linkage, outbreak alert, plot memory, insurance claim packet, and
group-buy alert — into one AdvisoryResponse.
"""
from gemini_client import diagnose_crop_photo
from group_buy import check_group_buy_opportunity
from insurance import build_insurance_claim_packet
from market_tools import find_best_sell_price, find_nearest_dealer
from outbreak import check_outbreak
from plot_memory import get_plot_memory_note
from schemas import AdvisoryResponse
from translation import translate_advisory
from tts import speak_advisory
from weather import get_local_weather

# A disease is treatable with a known input in our seed data; map disease ->
# the primary treatment product name used to look up a dealer.
_PRIMARY_TREATMENT = {
    "early_blight": "copper_oxychloride_50wp",
    "late_blight": "mancozeb_75wp",
    "leaf_curl_virus": "imidacloprid_17.8sl",
    "bacterial_wilt": None,  # no chemical cure — no dealer call
    "fusarium_wilt": None,
    "blossom_end_rot": None,  # physiological disorder, not a product fix
    "septoria_leaf_spot": "mancozeb_75wp",
    "spider_mite_damage": "neem_oil",
}


def build_advisory_response(
    symptom_description: str,
    farmer_lat: float,
    farmer_lon: float,
    farmer_language: str = "kn-IN",
    plot_id: str = None,
    near_harvest: bool = False,
) -> AdvisoryResponse:
    diagnosis = diagnose_crop_photo(symptom_description)

    weather = None
    weather_note = None
    dealer = None
    sell_price = None

    if diagnosis.disease not in ("healthy", "uncertain"):
        weather = get_local_weather(farmer_lat, farmer_lon)
        if weather["rain_expected_in_2_days"]:
            weather_note = "Rain is forecast in the next 2 days — spray before it arrives, not after."
        else:
            weather_note = "No significant rain forecast in the next 2 days."

        treatment = _PRIMARY_TREATMENT.get(diagnosis.disease)
        if treatment:
            dealer = find_nearest_dealer(treatment)
    elif diagnosis.disease == "healthy" and near_harvest:
        sell_price = find_best_sell_price("tomato")

    outbreak_alert = check_outbreak(farmer_lat, farmer_lon, exclude_plot_id=plot_id)
    plot_memory_note = get_plot_memory_note(plot_id, diagnosis.disease) if plot_id else None

    # Feature #1 — crop-loss insurance claim assistant: only fires for a
    # severe-enough, confident-enough diagnosis; see insurance.py for the bar.
    insurance_claim = build_insurance_claim_packet(diagnosis, plot_id=plot_id)

    # Feature #3 — group-buy alert: only fires when an outbreak signal exists
    # AND combined nearby demand for the shared treatment clears the bulk
    # threshold; see group_buy.py.
    group_buy_alert = None
    if outbreak_alert:
        group_buy_alert = check_group_buy_opportunity(
            outbreak_alert.disease, outbreak_alert.nearby_report_count,
        )

    advisory_en = diagnosis.treatment_recommendation
    if weather_note:
        advisory_en = f"{advisory_en} {weather_note}"

    advisory_local = translate_advisory(diagnosis.disease, advisory_en, farmer_language)
    audio_available, _audio_bytes, _spoken_text = speak_advisory(advisory_local, farmer_language)

    return AdvisoryResponse(
        diagnosis=diagnosis,
        weather_note=weather_note,
        advisory_text_en=advisory_en,
        advisory_text_local=advisory_local,
        local_language=farmer_language,
        audio_available=audio_available,
        dealer=dealer,
        sell_price=sell_price,
        outbreak_alert=outbreak_alert,
        plot_memory_note=plot_memory_note,
        insurance_claim=insurance_claim,
        group_buy_alert=group_buy_alert,
    )


if __name__ == "__main__":
    import json

    response = build_advisory_response(
        symptom_description="dark spots with rings on the bottom leaves, like a target",
        farmer_lat=13.0991, farmer_lon=78.0543,
        farmer_language="kn-IN", plot_id="P001",
    )
    print(json.dumps(response.model_dump(), indent=2, ensure_ascii=False))
