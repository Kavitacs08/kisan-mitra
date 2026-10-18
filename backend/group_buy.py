"""Feature #3 -- group-buy / collective bargaining alert.

Extends the outbreak detector (outbreak.py) into a coordinated economic
action: when 3+ nearby farmers need the SAME treatment this week, suggest
they buy together from the same dealer for a bulk discount, instead of each
paying full price alone. Real logic over the real synthetic data and the
real dealer directory, no mocking needed.
"""
import csv
import os
from datetime import datetime, timedelta

from config import DATA_DIR
from market_tools import find_nearest_dealer
from schemas import GroupBuyAlert

# Disease -> primary treatment, mirrors advisory.py's own mapping so a
# group-buy alert recommends the same product the individual advisory does.
_PRIMARY_TREATMENT = {
    "early_blight": "copper_oxychloride_50wp",
    "late_blight": "mancozeb_75wp",
    "leaf_curl_virus": "imidacloprid_17.8sl",
    "septoria_leaf_spot": "mancozeb_75wp",
    "spider_mite_damage": "neem_oil",
}

# A bulk discount kicks in once combined demand crosses this threshold --
# illustrative for the demo; a real deployment would source this from the
# dealer's own bulk pricing tiers.
_BULK_THRESHOLD_KG = 10.0
_BULK_DISCOUNT_PCT = 12


def _load_diagnosis_history():
    with open(os.path.join(DATA_DIR, "diagnosis_history.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check_group_buy_opportunity(disease: str, nearby_report_count: int,
                                 estimated_kg_per_farmer: float = 2.0) -> GroupBuyAlert | None:
    """Given an outbreak signal (same disease, N nearby reports), checks
    whether combined demand for the shared treatment crosses the dealer's
    bulk-pricing threshold, and if so returns a group-buy alert naming the
    dealer, the discounted price, and how many farmers are in on it."""
    treatment = _PRIMARY_TREATMENT.get(disease)
    if not treatment or nearby_report_count < 3:
        return None

    dealer = find_nearest_dealer(treatment)
    if not dealer:
        return None

    combined_kg = nearby_report_count * estimated_kg_per_farmer
    if combined_kg < _BULK_THRESHOLD_KG:
        return None

    bulk_price = round(dealer.price_per_kg * (1 - _BULK_DISCOUNT_PCT / 100), 2)
    message = (
        f"{nearby_report_count} nearby farmers need {treatment.replace('_', ' ')} this week. "
        f"Buying together from {dealer.name} at an estimated {combined_kg:.0f}kg combined "
        f"qualifies for a bulk price of ₹{bulk_price}/kg instead of ₹{dealer.price_per_kg}/kg."
    )

    return GroupBuyAlert(
        treatment=treatment,
        nearby_farmer_count=nearby_report_count,
        dealer_name=dealer.name,
        dealer_distance_km=dealer.distance_km,
        standard_price_per_kg=dealer.price_per_kg,
        bulk_price_per_kg=bulk_price,
        bulk_threshold_kg=_BULK_THRESHOLD_KG,
        message=message,
    )


if __name__ == "__main__":
    from outbreak import check_outbreak

    history = _load_diagnosis_history()
    # Reuse the same seeded outbreak cluster (early_blight, 4 plots within 6km/4 days)
    # that outbreak.py's own test already finds.
    import csv as _csv
    with open(os.path.join(DATA_DIR, "plots.csv"), encoding="utf-8") as f:
        plots = {row["plot_id"]: row for row in _csv.DictReader(f)}
    sample_plot = next(iter(plots.values()))
    alert = check_outbreak(float(sample_plot["lat"]), float(sample_plot["lon"]), exclude_plot_id=sample_plot["plot_id"])
    if alert:
        group_buy = check_group_buy_opportunity(alert.disease, alert.nearby_report_count)
        print(group_buy.message if group_buy else "No group-buy opportunity (demand below bulk threshold).")
    else:
        print("No outbreak detected -- nothing to check for a group-buy opportunity.")
