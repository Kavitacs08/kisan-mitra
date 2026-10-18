/**
 * Ports backend/advisory.py's intent (Prompts 11 & 14 — end-to-end advisory
 * assembly and agent orchestration), upgraded so the "which tool to call"
 * decision is made by Gemini via real function-calling (orchestrator.js),
 * not hardcoded if/else branching. Weather, outbreak-check, and plot-memory
 * stay unconditional -- they're informational context the advisory always
 * needs, not the "which action to take" decision the orchestrator covers.
 */
import { diagnoseCropPhoto } from "./diagnosis.js";
import { checkGroupBuyOpportunity } from "./group-buy.js";
import { buildInsuranceClaimPacket } from "./insurance.js";
import { findBestSellPrice, findNearestDealer } from "./market.js";
import { decideOrchestration } from "./orchestrator.js";
import { checkOutbreak } from "./outbreak.js";
import { getPlotMemoryNote } from "./plot-memory.js";
import { translateAdvisory } from "./translation.js";
import { speakAdvisory } from "./tts.js";
import { getLocalWeather } from "./weather.js";

// A disease is treatable with a known input in our seed data; map disease ->
// the primary treatment product name used to look up a dealer.
const PRIMARY_TREATMENT = {
  early_blight: "copper_oxychloride_50wp",
  late_blight: "mancozeb_75wp",
  leaf_curl_virus: "imidacloprid_17.8sl",
  bacterial_wilt: null, // no chemical cure -- no dealer call
  fusarium_wilt: null,
  blossom_end_rot: null, // physiological disorder, not a product fix
  septoria_leaf_spot: "mancozeb_75wp",
  spider_mite_damage: "neem_oil",
};

/**
 * @param {object} opts
 * @param {string} opts.symptomDescription
 * @param {number} opts.farmerLat
 * @param {number} opts.farmerLon
 * @param {string} [opts.farmerLanguage]
 * @param {string|null} [opts.plotId]
 * @param {boolean} [opts.nearHarvest]
 * @param {string|null} [opts.imageDataUrl] - optional uploaded photo as a data: URL
 * @returns {Promise<object>} AdvisoryResponse-shaped object
 */
export async function buildAdvisoryResponse({
  symptomDescription,
  farmerLat,
  farmerLon,
  farmerLanguage = "kn-IN",
  plotId = null,
  nearHarvest = false,
  imageDataUrl = null,
}) {
  const diagnosis = await diagnoseCropPhoto(symptomDescription, imageDataUrl);

  // Unconditional context -- always gathered, never gated by the
  // orchestration decision below. Weather is still only fetched for a
  // treatable diagnosis (a healthy/uncertain result has no spray timing to
  // advise on), matching the original behavior.
  let weatherNote = null;
  if (diagnosis.disease !== "healthy" && diagnosis.disease !== "uncertain") {
    const weather = await getLocalWeather(farmerLat, farmerLon);
    weatherNote = weather.rain_expected_in_2_days
      ? "Rain is forecast in the next 2 days — spray before it arrives, not after."
      : "No significant rain forecast in the next 2 days.";
  }
  const outbreakAlert = await checkOutbreak(farmerLat, farmerLon, 10, 7, 3, plotId);
  const plotMemoryNote = plotId ? await getPlotMemoryNote(plotId, diagnosis.disease) : null;

  // The decision of WHICH action tools to invoke is made by Gemini via
  // real function-calling (or the deterministic fallback if that call
  // fails) -- see orchestrator.js. Arguments passed to each tool below
  // still come from the known mappings, not from Gemini's chosen args
  // (see orchestrator.js's own comment on why).
  const { toolCalls, source: orchestrationSource } = await decideOrchestration({
    diagnosis, outbreakAlert, nearHarvest,
  });

  let dealer = null;
  let sellPrice = null;
  let insuranceClaim = null;
  let groupBuyAlert = null;

  if (toolCalls.includes("find_nearest_dealer")) {
    const treatment = PRIMARY_TREATMENT[diagnosis.disease];
    if (treatment) dealer = await findNearestDealer(treatment);
  }
  if (toolCalls.includes("find_best_sell_price")) {
    sellPrice = await findBestSellPrice("tomato");
  }
  if (toolCalls.includes("check_insurance_eligibility")) {
    insuranceClaim = buildInsuranceClaimPacket(diagnosis, plotId);
  }
  if (toolCalls.includes("check_group_buy_opportunity") && outbreakAlert) {
    groupBuyAlert = await checkGroupBuyOpportunity(outbreakAlert.disease, outbreakAlert.nearby_report_count);
  }

  let advisoryEn = diagnosis.treatment_recommendation;
  if (weatherNote) advisoryEn = `${advisoryEn} ${weatherNote}`;

  const advisoryLocal = translateAdvisory(diagnosis.disease, advisoryEn, farmerLanguage);
  const { audioAvailable } = await speakAdvisory(advisoryLocal, farmerLanguage);

  return {
    diagnosis,
    weather_note: weatherNote,
    advisory_text_en: advisoryEn,
    advisory_text_local: advisoryLocal,
    local_language: farmerLanguage,
    audio_available: audioAvailable,
    dealer,
    sell_price: sellPrice,
    outbreak_alert: outbreakAlert,
    plot_memory_note: plotMemoryNote,
    insurance_claim: insuranceClaim,
    group_buy_alert: groupBuyAlert,
    orchestration_source: orchestrationSource,
  };
}
