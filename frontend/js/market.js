/**
 * Ports backend/market_tools.py (Prompts 12 & 13 — buy-side dealer lookup
 * and sell-side price lookup) 1:1. Both query the same JSON seed data the
 * Python version used (data/dealers.json, data/mandi_prices.json) --
 * fetched once and cached module-level, mirroring the Python module's
 * import-time load.
 */

let _dealers = null;
let _mandiPrices = null;

async function loadMarketData() {
  if (_dealers && _mandiPrices) return;
  const [dealersRes, pricesRes] = await Promise.all([
    fetch("data/dealers.json"),
    fetch("data/mandi_prices.json"),
  ]);
  _dealers = await dealersRes.json();
  _mandiPrices = await pricesRes.json();
}

/**
 * Gemini function-calling tool equivalent: nearest dealer in stock for a
 * treatment, with today's price.
 * @param {string} treatment
 * @returns {Promise<object|null>}
 */
export async function findNearestDealer(treatment) {
  await loadMarketData();
  const candidates = _dealers.filter((d) => d.stocked_treatments.includes(treatment));
  if (candidates.length === 0) return null;
  const best = candidates.reduce((a, b) => (b.distance_km < a.distance_km ? b : a));
  return {
    dealer_id: best.dealer_id,
    name: best.name,
    village: best.village,
    distance_km: best.distance_km,
    price_per_kg: best.price_per_kg,
    treatment,
  };
}

/**
 * Gemini function-calling tool equivalent: best nearby mandi price today
 * for a crop, with the 7-day trend direction.
 * @param {string} crop
 * @returns {Promise<object|null>}
 */
export async function findBestSellPrice(crop = "tomato") {
  await loadMarketData();
  const candidates = _mandiPrices.filter((m) => m.crop === crop);
  if (candidates.length === 0) return null;
  const best = candidates.reduce((a, b) =>
    b.price_per_quintal_today > a.price_per_quintal_today ? b : a
  );
  const trend = best.price_trend_7day;
  let direction;
  if (trend[trend.length - 1] > trend[0] * 1.03) {
    direction = "rising";
  } else if (trend[trend.length - 1] < trend[0] * 0.97) {
    direction = "falling";
  } else {
    direction = "flat";
  }
  return {
    market_id: best.market_id,
    name: best.name,
    distance_km: best.distance_km,
    price_per_quintal_today: best.price_per_quintal_today,
    trend_direction: direction,
  };
}
