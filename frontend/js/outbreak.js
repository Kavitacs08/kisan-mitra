/**
 * Ports backend/outbreak.py 1:1 (Prompt 15 — outbreak early-warning).
 * Haversine distance + time-window query over plots.csv/diagnosis_history.csv,
 * loaded as static files instead of a Firestore collection. Only plot_id/
 * lat/lon are read from plots.csv -- farmer_id is not in the trimmed,
 * publicly-shipped version of this file at all (see the migration plan's
 * privacy section).
 */
import { fetchCsv } from "./csv.js";

let _plots = null;
let _history = null;

async function loadOutbreakData() {
  if (_plots && _history) return;
  _plots = await fetchCsv("data/plots.csv");
  _history = await fetchCsv("data/diagnosis_history.csv");
}

function haversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371.0;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.asin(Math.sqrt(a));
}

/**
 * @param {number} lat
 * @param {number} lon
 * @param {number} radiusKm
 * @param {number} windowDays
 * @param {number} minReports
 * @param {string|null} excludePlotId
 * @returns {Promise<object|null>}
 */
export async function checkOutbreak(
  lat, lon, radiusKm = 10, windowDays = 7, minReports = 3, excludePlotId = null
) {
  await loadOutbreakData();
  const plotsById = {};
  for (const p of _plots) plotsById[p.plot_id] = p;

  const now = new Date();
  const cutoff = new Date(now.getTime() - windowDays * 24 * 60 * 60 * 1000);

  const nearbyByDisease = {};
  for (const record of _history) {
    if (!record.disease || record.disease === "healthy") continue;
    if (record.plot_id === excludePlotId) continue;
    const plot = plotsById[record.plot_id];
    if (!plot) continue;
    const ts = new Date(record.timestamp);
    if (isNaN(ts.getTime()) || ts < cutoff) continue;
    const dist = haversineKm(lat, lon, parseFloat(plot.lat), parseFloat(plot.lon));
    if (dist <= radiusKm) {
      nearbyByDisease[record.disease] = (nearbyByDisease[record.disease] || 0) + 1;
    }
  }

  const entries = Object.entries(nearbyByDisease);
  if (entries.length === 0) return null;
  const [disease, count] = entries.reduce((a, b) => (b[1] > a[1] ? b : a));
  if (count < minReports) return null;

  const diseaseTitle = disease
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
  const message =
    `${diseaseTitle} has been reported on ${count} nearby tomato ` +
    `plots in the last ${windowDays} days. Inspect your crop today — early action ` +
    `prevents spread.`;

  return { disease, nearby_report_count: count, radius_km: radiusKm, window_days: windowDays, message };
}
