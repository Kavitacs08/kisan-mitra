/**
 * Ports backend/insurance.py 1:1 (Feature #1 — crop-loss insurance claim
 * assistant). Pure packaging of data already produced by diagnosis.js --
 * no mocking needed, same as the Python original.
 */

// Illustrative demo figures, not actuarial numbers -- a real deployment
// would source this from an agricultural insurer's own loss tables.
const CLAIMABLE_DISEASES = {
  early_blight: { severity: "moderate", yield_loss_pct: 15 },
  late_blight: { severity: "severe", yield_loss_pct: 35 },
  bacterial_wilt: { severity: "severe", yield_loss_pct: 40 },
  fusarium_wilt: { severity: "severe", yield_loss_pct: 30 },
  leaf_curl_virus: { severity: "moderate", yield_loss_pct: 20 },
};

const MIN_CONFIDENCE_TO_CLAIM = 0.6;

function pad2(n) {
  return String(n).padStart(2, "0");
}

/** Mirrors Python's now.strftime('%Y%m%d'). */
function yyyymmdd(date) {
  return `${date.getFullYear()}${pad2(date.getMonth() + 1)}${pad2(date.getDate())}`;
}

/** Mirrors Python's now.isoformat(timespec="seconds"). */
function isoSeconds(date) {
  return (
    `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}` +
    `T${pad2(date.getHours())}:${pad2(date.getMinutes())}:${pad2(date.getSeconds())}`
  );
}

function randomHex6() {
  // crypto.randomUUID() is the browser equivalent of Python's uuid.uuid4();
  // take the first 6 hex chars, uppercased, matching uuid4().hex[:6].upper().
  return crypto.randomUUID().replace(/-/g, "").slice(0, 6).toUpperCase();
}

/**
 * Returns a claim packet only when the diagnosis is both severe enough and
 * confident enough to be worth a farmer's time filing -- a low-confidence
 * or minor-disorder diagnosis correctly returns null rather than nudging
 * someone toward a claim that likely won't be approved.
 *
 * @param {{disease: string, confidence: number, cited_source: string|null}} diagnosis
 * @param {string|null} plotId
 * @returns {object|null}
 */
export function buildInsuranceClaimPacket(diagnosis, plotId = null) {
  const profile = CLAIMABLE_DISEASES[diagnosis.disease];
  if (!profile || diagnosis.confidence < MIN_CONFIDENCE_TO_CLAIM) {
    return null;
  }

  const now = new Date();
  const claimId = `CLM-${yyyymmdd(now)}-${randomHex6()}`;

  const evidenceSummary =
    `Diagnosis: ${diagnosis.disease.replaceAll("_", " ")} ` +
    `(${Math.trunc(diagnosis.confidence * 100)}% confidence), grounded in ` +
    `${diagnosis.cited_source || "the regional disease guide"}. ` +
    `Estimated yield loss: ${profile.yield_loss_pct}% if untreated.`;

  return {
    claim_id: claimId,
    generated_at: isoSeconds(now),
    plot_id: plotId,
    disease: diagnosis.disease,
    confidence: diagnosis.confidence,
    cited_source: diagnosis.cited_source,
    severity_estimate: profile.severity,
    estimated_yield_loss_pct: profile.yield_loss_pct,
    evidence_summary: evidenceSummary,
    recommended_next_step: (
      "This evidence packet is ready to attach to a crop-loss insurance claim. " +
      "Take 2-3 more photos today dated clearly, then contact your insurer's " +
      "local agent or helpline to file within the standard reporting window."
    ),
  };
}
