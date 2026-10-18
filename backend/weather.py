"""Prompt 7 — weather tool call. Open-Meteo needs no API key, so this one
runs live even in mock mode; it's the one real external call in the stack.
"""
import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def get_local_weather(lat: float, lon: float) -> dict:
    """Gemini function-calling tool: returns today's conditions and a 2-day
    rain forecast, used to decide whether to recommend spraying now or to
    wait out forecast rain."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation",
        "daily": "precipitation_sum,precipitation_probability_max",
        "forecast_days": 3,
        "timezone": "Asia/Kolkata",
    }
    resp = requests.get(OPEN_METEO_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    current = data.get("current", {})
    daily = data.get("daily", {})
    rain_next_2_days = any(
        p and p > 40 for p in daily.get("precipitation_probability_max", [])[1:3]
    )

    return {
        "temperature_c": current.get("temperature_2m"),
        "humidity_pct": current.get("relative_humidity_2m"),
        "rain_expected_in_2_days": rain_next_2_days,
        "rain_probability_tomorrow": daily.get("precipitation_probability_max", [None, None])[1],
    }


FUNCTION_SCHEMA = {
    "name": "get_local_weather",
    "description": "Get current weather and 2-day rain forecast for a location, "
                    "used before recommending a spray treatment.",
    "parameters": {
        "type": "object",
        "properties": {
            "lat": {"type": "number"},
            "lon": {"type": "number"},
        },
        "required": ["lat", "lon"],
    },
}


if __name__ == "__main__":
    # Demo coordinates: the tomato belt near Kolar, Karnataka
    result = get_local_weather(13.1372, 78.1298)
    print("Live Open-Meteo response for Kolar, Karnataka:")
    print(result)
