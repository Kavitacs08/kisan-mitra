/**
 * Ports backend/advisory.py 1:1 (Prompts 11 & 14 — end-to-end advisory
 * assembly and agent orchestration). Decides which tool to call based on
 * the diagnosis outcome, and assembles everything -- diagnosis, weather,
 * translated/spoken advisory, market linkage, outbreak alert, plot memory,
 * insurance claim packet, group-buy alert -- into one response object.
 */
import { diagnoseCropPhoto } from "./diagnosis.js";
import { checkGroupBuyOpportunity } from "./group-buy.js";
import { buildInsuranceClaimPacket } from "./insurance.js";
import { findBestSellPrice, findNearestDealer } from "./market.js";
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

  let weatherNote = null;
  let dealer = null;
  let sellPrice = null;

  if (diagnosis.disease !== "healthy" && diagnosis.disease !== "uncertain") {
    const weather = await getLocalWeather(farmerLat, farmerLon);
    weatherNote = weather.rain_expected_in_2_days
      ? "Rain is forecast in the next 2 days — spray before it arrives, not after."
      : "No significant rain forecast in the next 2 days.";

    const treatment = PRIMARY_TREATMENT[diagnosis.disease];
    if (treatment) {
      dealer = await findNearestDealer(treatment);
    }
  } else if (diagnosis.disease === "healthy" && nearHarvest) {
    sellPrice = await findBestSellPrice("tomato");
  }

  const outbreakAlert = await checkOutbreak(farmerLat, farmerLon, 10, 7, 3, plotId);
  const plotMemoryNote = plotId ? await getPlotMemoryNote(plotId, diagnosis.disease) : null;

  // Feature #1 — crop-loss insurance claim assistant.
  const insuranceClaim = buildInsuranceClaimPacket(diagnosis, plotId);

  // Feature #3 — group-buy alert: only checked if an outbreak signal exists.
  let groupBuyAlert = null;
  if (outbreakAlert) {
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
  };
}
