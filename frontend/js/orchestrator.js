/**
 * Gemini function-calling orchestration. Replaces advisory.js's hardcoded
 * if/else branching ("if disease is treatable, call the dealer lookup; if
 * outbreak exists, call group-buy...") with a real decision made by
 * Gemini: given the diagnosis and context, Gemini chooses WHICH of four
 * available tools are appropriate to call, via the Gemini API's
 * tools/functionDeclarations mechanism.
 *
 * Important design choice, confirmed by a live test call: Gemini's chosen
 * function-call ARGUMENTS cannot be trusted (e.g. it filled a `treatment`
 * param with the disease name, not the actual product slug, because it has
 * no access to the disease->treatment mapping unless taught the whole
 * table). So this module uses Gemini ONLY to decide which tool NAMES to
 * invoke; the actual arguments passed to each tool still come from the
 * same deterministic mappings advisory.js already had. This keeps the
 * decision genuinely model-driven while keeping the data correct.
 *
 * Falls back to a deterministic reproduction of advisory.js's original
 * branching if the live call fails after retries -- the fallback is not a
 * downgrade in behavior, just a downgrade in HOW the same decision was
 * reached.
 */
import { callGeminiRawWithRetry } from "./gemini-client.js";

const TOOL_DECLARATIONS = [
  {
    name: "find_nearest_dealer",
    description:
      "Find the nearest dealer in stock for the recommended treatment, with today's price. " +
      "Call this when the diagnosed disease has a known effective chemical treatment available.",
    parameters: { type: "OBJECT", properties: {} },
  },
  {
    name: "find_best_sell_price",
    description:
      "Find the best nearby market price today to sell the harvested crop. " +
      "Call this ONLY when the plant is healthy AND the farmer has indicated the crop is near harvest.",
    parameters: { type: "OBJECT", properties: {} },
  },
  {
    name: "check_insurance_eligibility",
    description:
      "Check whether this diagnosis is severe and confident enough to be worth filing a " +
      "crop-loss insurance claim. Reasonable to call whenever a real disease (not healthy, " +
      "not uncertain) was diagnosed.",
    parameters: { type: "OBJECT", properties: {} },
  },
  {
    name: "check_group_buy_opportunity",
    description:
      "Check whether nearby farmers reporting the same disease this week qualifies the group " +
      "for a bulk-purchase discount on the shared treatment. Call this ONLY when there is an " +
      "active nearby outbreak signal for the same disease as this diagnosis.",
    parameters: { type: "OBJECT", properties: {} },
  },
];

const VALID_TOOL_NAMES = new Set(TOOL_DECLARATIONS.map((t) => t.name));

// Mirrors advisory.js's own PRIMARY_TREATMENT map -- diseases mapped to
// null have no chemical treatment, so a dealer lookup is never appropriate
// for them regardless of what Gemini or the fallback decides. Duplicated
// here deliberately (rather than imported) because the fallback needs to
// make the exact same "is there a treatment to buy" check advisory.js did,
// without this module depending on advisory.js (which depends on this
// module) and creating a circular import.
const HAS_CHEMICAL_TREATMENT = {
  early_blight: true,
  late_blight: true,
  leaf_curl_virus: true,
  bacterial_wilt: false,
  fusarium_wilt: false,
  blossom_end_rot: false,
  septoria_leaf_spot: true,
  spider_mite_damage: true,
};

function buildOrchestrationPrompt({ diagnosis, outbreakAlert, nearHarvest }) {
  const hasTreatment = HAS_CHEMICAL_TREATMENT[diagnosis.disease];
  return (
    "You are deciding which follow-up actions to take for a smallholder tomato farmer in " +
    "Karnataka, India, after a crop diagnosis.\n\n" +
    `Diagnosis result: disease="${diagnosis.disease}", confidence=${diagnosis.confidence}, ` +
    `a chemical treatment is ${hasTreatment === false ? "NOT " : ""}available for this disease.\n` +
    (outbreakAlert
      ? `Nearby outbreak signal: ${outbreakAlert.nearby_report_count} nearby farmers reported ` +
        `"${outbreakAlert.disease}" in the last ${outbreakAlert.window_days} days.\n`
      : "No active nearby outbreak signal.\n") +
    `Farmer indicated the crop is near harvest: ${nearHarvest}.\n\n` +
    "Based on this, call every tool (zero or more) that is genuinely appropriate given the " +
    "descriptions above. Do not call a tool that doesn't fit the situation -- e.g. don't look " +
    "up a dealer for a healthy plant, and don't check group-buy eligibility if there's no " +
    "outbreak signal."
  );
}

function extractToolNames(response) {
  const parts = response?.candidates?.[0]?.content?.parts || [];
  const names = parts
    .filter((p) => p.functionCall && VALID_TOOL_NAMES.has(p.functionCall.name))
    .map((p) => p.functionCall.name);
  return [...new Set(names)];
}

async function callGeminiOrchestration(context) {
  const prompt = buildOrchestrationPrompt(context);
  const body = {
    contents: [{ parts: [{ text: prompt }] }],
    tools: [{ functionDeclarations: TOOL_DECLARATIONS }],
  };
  const response = await callGeminiRawWithRetry(body);
  return extractToolNames(response);
}

/**
 * Deterministic fallback -- reproduces advisory.js's original branching
 * exactly, as a plain list of tool names, so quota exhaustion or a network
 * failure never degrades the app below what was already shipped.
 */
function fallbackOrchestration({ diagnosis, outbreakAlert, nearHarvest }) {
  const tools = [];
  const isTreatable = diagnosis.disease !== "healthy" && diagnosis.disease !== "uncertain";

  if (isTreatable && HAS_CHEMICAL_TREATMENT[diagnosis.disease]) {
    tools.push("find_nearest_dealer");
  } else if (diagnosis.disease === "healthy" && nearHarvest) {
    tools.push("find_best_sell_price");
  }

  // Matches advisory.js's original unconditional call -- insurance.js's own
  // buildInsuranceClaimPacket already gates eligibility internally (returns
  // null for ineligible diseases/confidence), so calling it unconditionally
  // here is correct, not a behavior change.
  tools.push("check_insurance_eligibility");

  if (outbreakAlert) {
    tools.push("check_group_buy_opportunity");
  }

  return tools;
}

/**
 * @param {object} context
 * @param {object} context.diagnosis - the DiagnosisResult-shaped object
 * @param {object|null} context.outbreakAlert
 * @param {boolean} context.nearHarvest
 * @returns {Promise<{toolCalls: string[], source: "gemini"|"fallback"}>}
 */
export async function decideOrchestration(context) {
  try {
    const toolCalls = await callGeminiOrchestration(context);
    return { toolCalls, source: "gemini" };
  } catch (err) {
    console.warn("Gemini orchestration call failed, falling back to deterministic rules:", err.message);
    return { toolCalls: fallbackOrchestration(context), source: "fallback" };
  }
}
