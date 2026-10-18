/**
 * Ports backend/weather.py 1:1 (Prompt 7 — weather tool call). Open-Meteo
 * needs no API key and sends Access-Control-Allow-Origin: * on every
 * response (confirmed via direct curl test), so this calls it directly
 * from the browser with no proxy.
 */

const OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast";

/**
 * Gemini function-calling tool equivalent: returns today's conditions and
 * a 2-day rain forecast, used to decide whether to recommend spraying now
 * or to wait out forecast rain.
 * @param {number} lat
 * @param {number} lon
 * @returns {Promise<{temperature_c: number|null, humidity_pct: number|null, rain_expected_in_2_days: boolean, rain_probability_tomorrow: number|null}>}
 */
export async function getLocalWeather(lat, lon) {
  const params = new URLSearchParams({
    latitude: lat,
    longitude: lon,
    current: "temperature_2m,relative_humidity_2m,precipitation",
    daily: "precipitation_sum,precipitation_probability_max",
    forecast_days: "3",
    timezone: "Asia/Kolkata",
  });

  const resp = await fetch(`${OPEN_METEO_URL}?${params}`);
  if (!resp.ok) throw new Error(`Open-Meteo request failed: ${resp.status}`);
  const data = await resp.json();

  const current = data.current || {};
  const daily = data.daily || {};
  const probs = daily.precipitation_probability_max || [];
  const rainNext2Days = probs.slice(1, 3).some((p) => p && p > 40);

  return {
    temperature_c: current.temperature_2m ?? null,
    humidity_pct: current.relative_humidity_2m ?? null,
    rain_expected_in_2_days: rainNext2Days,
    rain_probability_tomorrow: probs.length > 1 ? probs[1] : null,
  };
}
