/**
 * Ports backend/group_buy.py 1:1 (Feature #3 — group-buy / collective
 * bargaining alert). Extends the outbreak signal into a coordinated
 * economic action: when 3+ nearby farmers need the SAME treatment this
 * week, suggests they buy together from the same dealer for a bulk
 * discount.
 */
import { findNearestDealer } from "./market.js";

// Disease -> primary treatment, mirrors advisory.js's own mapping so a
// group-buy alert recommends the same product the individual advisory does.
const PRIMARY_TREATMENT = {
  early_blight: "copper_oxychloride_50wp",
  late_blight: "mancozeb_75wp",
  leaf_curl_virus: "imidacloprid_17.8sl",
  septoria_leaf_spot: "mancozeb_75wp",
  spider_mite_damage: "neem_oil",
};

// A bulk discount kicks in once combined demand crosses this threshold --
// illustrative for the demo; a real deployment would source this from the
// dealer's own bulk pricing tiers.
const BULK_THRESHOLD_KG = 10.0;
const BULK_DISCOUNT_PCT = 12;

/**
 * Given an outbreak signal (same disease, N nearby reports), checks whether
 * combined demand for the shared treatment crosses the dealer's bulk-
 * pricing threshold, and if so returns a group-buy alert naming the dealer,
 * the discounted price, and how many farmers are in on it.
 * @param {string} disease
 * @param {number} nearbyReportCount
 * @param {number} estimatedKgPerFarmer
 * @returns {Promise<object|null>}
 */
export async function checkGroupBuyOpportunity(disease, nearbyReportCount, estimatedKgPerFarmer = 2.0) {
  const treatment = PRIMARY_TREATMENT[disease];
  if (!treatment || nearbyReportCount < 3) return null;

  const dealer = await findNearestDealer(treatment);
  if (!dealer) return null;

  const combinedKg = nearbyReportCount * estimatedKgPerFarmer;
  if (combinedKg < BULK_THRESHOLD_KG) return null;

  const bulkPrice = Math.round(dealer.price_per_kg * (1 - BULK_DISCOUNT_PCT / 100) * 100) / 100;
  const message =
    `${nearbyReportCount} nearby farmers need ${treatment.replaceAll("_", " ")} this week. ` +
    `Buying together from ${dealer.name} at an estimated ${Math.round(combinedKg)}kg combined ` +
    `qualifies for a bulk price of ₹${bulkPrice}/kg instead of ₹${dealer.price_per_kg}/kg.`;

  return {
    treatment,
    nearby_farmer_count: nearbyReportCount,
    dealer_name: dealer.name,
    dealer_distance_km: dealer.distance_km,
    standard_price_per_kg: dealer.price_per_kg,
    bulk_price_per_kg: bulkPrice,
    bulk_threshold_kg: BULK_THRESHOLD_KG,
    message,
  };
}
