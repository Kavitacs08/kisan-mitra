"""Prompts 12 & 13 — buy-side dealer lookup and sell-side price lookup.

Both query the local Firestore-shaped JSON seed data directly (data/dealers.json,
data/mandi_prices.json) — these are genuinely functional, no mocking needed,
since Firestore itself is just a document store the real deployment points at
instead of a local file.
"""
import json
import os

from config import DATA_DIR
from schemas import DealerMatch, SellPriceMatch

with open(os.path.join(DATA_DIR, "dealers.json"), encoding="utf-8") as f:
    _DEALERS = json.load(f)

with open(os.path.join(DATA_DIR, "mandi_prices.json"), encoding="utf-8") as f:
    _MANDI_PRICES = json.load(f)


def find_nearest_dealer(treatment: str) -> DealerMatch | None:
    """Gemini function-calling tool: nearest dealer in stock for a treatment."""
    candidates = [d for d in _DEALERS if treatment in d["stocked_treatments"]]
    if not candidates:
        return None
    best = min(candidates, key=lambda d: d["distance_km"])
    return DealerMatch(
        dealer_id=best["dealer_id"], name=best["name"], village=best["village"],
        distance_km=best["distance_km"], price_per_kg=best["price_per_kg"],
        treatment=treatment,
    )


def find_best_sell_price(crop: str = "tomato") -> SellPriceMatch | None:
    """Gemini function-calling tool: best nearby mandi price today, with trend."""
    candidates = [m for m in _MANDI_PRICES if m["crop"] == crop]
    if not candidates:
        return None
    best = max(candidates, key=lambda m: m["price_per_quintal_today"])
    trend = best["price_trend_7day"]
    if trend[-1] > trend[0] * 1.03:
        direction = "rising"
    elif trend[-1] < trend[0] * 0.97:
        direction = "falling"
    else:
        direction = "flat"
    return SellPriceMatch(
        market_id=best["market_id"], name=best["name"], distance_km=best["distance_km"],
        price_per_quintal_today=best["price_per_quintal_today"], trend_direction=direction,
    )


FIND_DEALER_SCHEMA = {
    "name": "find_nearest_dealer",
    "description": "Find the nearest dealer in stock for a given treatment, with today's price.",
    "parameters": {"type": "object", "properties": {"treatment": {"type": "string"}}, "required": ["treatment"]},
}

FIND_SELL_PRICE_SCHEMA = {
    "name": "find_best_sell_price",
    "description": "Find the mandi (market yard) with the best price today for a crop, with the 7-day trend.",
    "parameters": {"type": "object", "properties": {"crop": {"type": "string"}}, "required": ["crop"]},
}


if __name__ == "__main__":
    print(find_nearest_dealer("copper_oxychloride_50wp"))
    print(find_best_sell_price("tomato"))
