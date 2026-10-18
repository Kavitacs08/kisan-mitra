/**
 * UI wiring for index.html. Replaces every fetch(`${API_BASE}/...`) call
 * with a direct call into advisory.js / outbreak.js -- there is no backend
 * in this deployment, everything below runs in the browser.
 */
import { buildAdvisoryResponse } from "./advisory.js";
import { checkOutbreak } from "./outbreak.js";

// Demo coordinates: Kolar belt, Karnataka, matching the seeded dealer/outbreak data.
const FARMER_LAT = 13.0991, FARMER_LON = 78.0543, PLOT_ID = "P001";

const statusEl = document.getElementById("status");
const photoInput = document.getElementById("photoInput");
const photoPreview = document.getElementById("photoPreview");
const diagnoseBtn = document.getElementById("diagnoseBtn");
const recordBtn = document.getElementById("recordBtn");
const dismissOutbreakBtn = document.getElementById("dismissOutbreakBtn");

let uploadedImageDataUrl = null;

photoInput.addEventListener("change", () => {
  const file = photoInput.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    uploadedImageDataUrl = e.target.result;
    photoPreview.src = uploadedImageDataUrl;
    photoPreview.style.display = "block";
  };
  reader.readAsDataURL(file);
});

dismissOutbreakBtn.addEventListener("click", () => {
  document.getElementById("outbreakBanner").style.display = "none";
});

let recognizer = null;
let recording = false;

function toggleRecording() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    statusEl.textContent = "Voice input isn't supported in this browser — type the description instead.";
    return;
  }
  if (recording) {
    recognizer.stop();
    return;
  }
  recognizer = new SpeechRecognition();
  recognizer.lang = "kn-IN";
  recognizer.onresult = (e) => {
    document.getElementById("symptomInput").value = e.results[0][0].transcript;
  };
  recognizer.onend = () => {
    recording = false;
    recordBtn.textContent = "🎙 Speak instead";
  };
  recognizer.onerror = () => {
    statusEl.textContent = "Couldn't hear that — try typing instead.";
  };
  recognizer.start();
  recording = true;
  recordBtn.textContent = "⏹ Listening...";
}

recordBtn.addEventListener("click", toggleRecording);

async function runDiagnosis() {
  const symptom = document.getElementById("symptomInput").value.trim();
  if (!symptom) {
    statusEl.textContent = "Describe what you see first.";
    return;
  }

  diagnoseBtn.disabled = true;
  statusEl.textContent = uploadedImageDataUrl
    ? "Analyzing photo with Gemini..."
    : "Analyzing description with Gemini...";

  try {
    const data = await buildAdvisoryResponse({
      symptomDescription: symptom,
      farmerLat: FARMER_LAT,
      farmerLon: FARMER_LON,
      farmerLanguage: "kn-IN",
      plotId: PLOT_ID,
      imageDataUrl: uploadedImageDataUrl,
    });
    renderResult(data);
    await renderOutbreakBanner();
    statusEl.textContent = "";
  } catch (err) {
    statusEl.textContent = `Something went wrong: ${err.message}`;
  } finally {
    diagnoseBtn.disabled = false;
  }
}

diagnoseBtn.addEventListener("click", runDiagnosis);

function renderResult(data) {
  const d = data.diagnosis;
  document.getElementById("resultCard").classList.remove("hidden");
  document.getElementById("diseaseName").textContent = d.disease.replaceAll("_", " ");
  document.getElementById("confidencePill").textContent = `${Math.round(d.confidence * 100)}% confidence`;
  const sourceNote = d.source === "fallback"
    ? " (Gemini unavailable — local fallback used)"
    : " (via Gemini)";
  document.getElementById("citedSource").textContent =
    (d.cited_source ? `Source: ${d.cited_source}` : "") + sourceNote;
  document.getElementById("advisoryEn").textContent = data.advisory_text_en;
  document.getElementById("advisoryLocal").textContent = data.advisory_text_local;
  document.getElementById("audioNote").textContent = data.audio_available
    ? "🔊 Voice advisory played automatically."
    : "🔇 No Kannada voice found on this device/browser — showing text advisory.";

  const memEl = document.getElementById("plotMemory");
  if (data.plot_memory_note) {
    memEl.textContent = data.plot_memory_note;
    memEl.classList.remove("hidden");
  } else {
    memEl.classList.add("hidden");
  }

  const dealerCard = document.getElementById("dealerCard");
  if (data.dealer) {
    dealerCard.classList.remove("hidden");
    document.getElementById("dealerName").textContent = data.dealer.name;
    document.getElementById("dealerDist").textContent = `${data.dealer.distance_km} km`;
    document.getElementById("dealerPrice").textContent =
      `${data.dealer.treatment.replaceAll("_", " ")} — ₹${data.dealer.price_per_kg}/kg, in stock today`;
  } else {
    dealerCard.classList.add("hidden");
  }

  const sellCard = document.getElementById("sellCard");
  if (data.sell_price) {
    sellCard.classList.remove("hidden");
    document.getElementById("marketName").textContent = data.sell_price.name;
    document.getElementById("marketDist").textContent = `${data.sell_price.distance_km} km`;
    document.getElementById("marketPrice").textContent = `₹${data.sell_price.price_per_quintal_today}/quintal`;
    const trendEl = document.getElementById("marketTrend");
    trendEl.textContent = `Price is ${data.sell_price.trend_direction} this week`;
    trendEl.className =
      data.sell_price.trend_direction === "rising" ? "trend-up"
        : data.sell_price.trend_direction === "falling" ? "trend-down" : "";
  } else {
    sellCard.classList.add("hidden");
  }

  const claimCard = document.getElementById("claimCard");
  if (data.insurance_claim) {
    const claim = data.insurance_claim;
    claimCard.classList.remove("hidden");
    document.getElementById("claimId").textContent = claim.claim_id;
    const sevEl = document.getElementById("claimSeverity");
    sevEl.textContent = claim.severity_estimate;
    sevEl.className = `sev-badge sev-${claim.severity_estimate}`;
    document.getElementById("claimYieldLoss").textContent =
      ` Estimated yield loss: ${claim.estimated_yield_loss_pct}% if untreated`;
    document.getElementById("claimSummary").textContent = claim.evidence_summary;
    document.getElementById("claimNextStep").textContent = claim.recommended_next_step;
  } else {
    claimCard.classList.add("hidden");
  }

  const groupBuyCard = document.getElementById("groupBuyCard");
  if (data.group_buy_alert) {
    const gb = data.group_buy_alert;
    groupBuyCard.classList.remove("hidden");
    document.getElementById("groupBuyFarmerCount").textContent =
      `${gb.nearby_farmer_count} nearby farmers need ${gb.treatment.replaceAll("_", " ")} this week`;
    document.getElementById("groupBuyStandardPrice").textContent = `₹${gb.standard_price_per_kg}/kg`;
    document.getElementById("groupBuyBulkPrice").textContent = `₹${gb.bulk_price_per_kg}/kg`;
    document.getElementById("groupBuyNote").textContent =
      `Buy together from ${gb.dealer_name} (${gb.dealer_distance_km} km) to unlock this bulk price.`;
  } else {
    groupBuyCard.classList.add("hidden");
  }
}

async function renderOutbreakBanner() {
  try {
    const data = await checkOutbreak(FARMER_LAT, FARMER_LON, 10, 7, 3, PLOT_ID);
    const banner = document.getElementById("outbreakBanner");
    if (data) {
      document.getElementById("outbreakText").textContent = `⚠ ${data.message}`;
      banner.style.display = "block";
    } else {
      banner.style.display = "none";
    }
  } catch (_) {
    /* outbreak check is best-effort, never block the main flow */
  }
}
