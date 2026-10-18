/**
 * Shared low-level Gemini API call + retry helper, extracted from
 * diagnosis.js so orchestrator.js can reuse the same retry/backoff pattern
 * instead of duplicating it. Both callers pass their own request body
 * (responseSchema-constrained for diagnosis, tools-based for orchestration)
 * and parse the response shape appropriate to their call.
 */
import { GEMINI_API_URL, GEMINI_API_KEY } from "./config.js";

/**
 * @param {object} body - the full Gemini generateContent request body
 * @returns {Promise<object>} the raw parsed JSON response
 */
export async function callGeminiRaw(body) {
  const res = await fetch(`${GEMINI_API_URL}?key=${GEMINI_API_KEY}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errBody = await res.text().catch(() => "");
    throw new Error(`Gemini API ${res.status}: ${errBody.slice(0, 200)}`);
  }

  return res.json();
}

/**
 * @param {object} body - the full Gemini generateContent request body
 * @param {number} maxAttempts
 * @returns {Promise<object>} the raw parsed JSON response
 */
export async function callGeminiRawWithRetry(body, maxAttempts = 3) {
  let lastErr;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await callGeminiRaw(body);
    } catch (err) {
      lastErr = err;
      console.warn(`Gemini attempt ${attempt}/${maxAttempts} failed:`, err.message);
      if (attempt < maxAttempts) await new Promise((r) => setTimeout(r, 1500 * attempt));
    }
  }
  throw lastErr;
}
