/**
 * Ports backend/plot_memory.py 1:1 (Prompt 16 — plot-level memory). Only
 * reads diagnosis_history.csv filtered by plot_id -- never touches
 * farmers.csv or plots.csv, so no farmer_id/village linkage is involved.
 */
import { fetchCsv } from "./csv.js";

const ROOT_CAUSE_HINTS = {
  early_blight:
    "Recurring early blight often points to poor airflow or splash from " +
    "overhead watering rather than bad luck each time — consider spacing " +
    "or switching to base-level irrigation.",
  late_blight:
    "Recurring late blight suggests this plot sits in a cool, damp pocket " +
    "(low drainage, shade, or poor airflow) that stays wet longer than " +
    "neighboring plots after rain.",
  bacterial_wilt:
    "Recurring bacterial wilt usually means the pathogen has built up in " +
    "the soil itself — rotating away from tomato/potato/brinjal on this " +
    "plot for a season or two is more effective than repeat treatment.",
  fusarium_wilt:
    "Recurring fusarium wilt points to a soil-borne buildup; consider a " +
    "resistant variety next season rather than treating the symptom again.",
};

let _history = null;

async function loadHistory() {
  if (_history) return _history;
  _history = await fetchCsv("data/diagnosis_history.csv");
  return _history;
}

/**
 * @param {string} plotId
 * @param {string} currentDisease
 * @returns {Promise<string|null>}
 */
export async function getPlotMemoryNote(plotId, currentDisease) {
  const all = await loadHistory();
  const history = all
    .filter((r) => r.plot_id === plotId)
    .sort((a, b) => a.timestamp.localeCompare(b.timestamp));

  const pastDiseases = history
    .map((r) => r.disease)
    .filter((d) => d !== "healthy" && d !== "");

  const counts = {};
  for (const d of pastDiseases) counts[d] = (counts[d] || 0) + 1;

  const occurrences =
    (counts[currentDisease] || 0) +
    (currentDisease !== "healthy" && currentDisease !== "uncertain" ? 1 : 0);

  if (occurrences < 3) return null;

  const hint =
    ROOT_CAUSE_HINTS[currentDisease] ||
    "This disease has recurred on this plot multiple times — the underlying cause " +
      "may be environmental (drainage, spacing, soil) rather than a one-off infection.";

  const suffix = occurrences === 3 ? "rd" : "th";
  return (
    `This is the ${occurrences}${suffix} time this plot has had ` +
    `${currentDisease.replaceAll("_", " ")}. ${hint}`
  );
}
