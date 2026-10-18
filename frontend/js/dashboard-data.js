/**
 * Loads the pre-built dashboard_data.json (see scripts/export_dashboard_json.py).
 * No aggregation logic runs in the browser -- the village-level aggregation
 * is computed once, at build time, server-side against the private
 * farmers.csv, specifically so raw farmer/plot linkage never ships in this
 * public static bundle. Refreshing the dashboard means re-running that
 * script and redeploying; this is a build-time snapshot, not a live query.
 */

/** @returns {Promise<object>} the DistrictDashboard-shaped aggregate */
export async function loadDistrictDashboard() {
  const res = await fetch("data/dashboard_data.json");
  if (!res.ok) throw new Error(`Failed to load dashboard data: ${res.status}`);
  return res.json();
}
