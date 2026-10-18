/**
 * Minimal CSV parser shared by outbreak.js and plot-memory.js. None of the
 * three CSV files in this app contain quoted fields with embedded commas
 * (confirmed: zero `"` characters in any of them), so a naive split-based
 * parser is safe here and matches Python's csv.DictReader behavior closely
 * enough for this dataset -- no CSV library needed.
 *
 * @param {string} text
 * @returns {object[]} array of row objects keyed by header
 */
export function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const headers = lines[0].split(",");
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    if (!lines[i]) continue;
    const values = lines[i].split(",");
    const row = {};
    headers.forEach((h, idx) => { row[h] = values[idx]; });
    rows.push(row);
  }
  return rows;
}

/** Fetches and parses a CSV file served alongside the page. */
export async function fetchCsv(path) {
  const res = await fetch(path);
  const text = await res.text();
  return parseCsv(text);
}
