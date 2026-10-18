/**
 * Real Gemini multimodal diagnosis call -- ports the intent of
 * backend/gemini_client.py's DIAGNOSIS_PROMPT_TEMPLATE and
 * _real_gemini_diagnose, which were written but never run in the original
 * Python build. This replaces the keyword-classifier mock with an actual
 * Gemini call, grounded by RAG retrieval over the disease guide, same as
 * the original design intended.
 *
 * Falls back to the old keyword/RAG heuristic ONLY if the live Gemini call
 * fails (network error, quota, transient 503) -- so a flaky connection
 * degrades gracefully instead of breaking the demo, but the primary path
 * is always the real model.
 */
import { GEMINI_API_URL, GEMINI_API_KEY } from "./config.js";
import { retrieveDiseaseContext } from "./rag.js";

const KNOWN_DISEASES = [
  "early_blight", "late_blight", "leaf_curl_virus", "bacterial_wilt",
  "fusarium_wilt", "blossom_end_rot", "septoria_leaf_spot",
  "spider_mite_damage", "healthy", "uncertain",
];

const DIAGNOSIS_SCHEMA = {
  type: "OBJECT",
  properties: {
    disease: { type: "STRING", enum: KNOWN_DISEASES },
    confidence: { type: "NUMBER" },
    cited_source: { type: "STRING" },
    treatment_recommendation: { type: "STRING" },
  },
  required: ["disease", "confidence", "treatment_recommendation"],
};

function formatContextBlock(passages) {
  return passages
    .map((p) => `[${p.source_doc} ${p.section}] ${p.text}`)
    .join("\n\n");
}

function buildPrompt(symptomDescription, contextBlock) {
  return (
    "You are an agronomy assistant for smallholder tomato farmers in Karnataka, India.\n\n" +
    "You are given:\n" +
    "- Optionally, a photo of a tomato plant (leaf, stem, or fruit).\n" +
    `- A short spoken description from the farmer, transcribed to text: "${symptomDescription}"\n` +
    "- The following retrieved passages from the regional disease guide, each with its " +
    "source document and section number:\n\n" +
    `${contextBlock}\n\n` +
    "Diagnose the most likely issue using the photo (if provided) and the description. You MUST " +
    "only name a disease if one of the retrieved passages actually supports it -- if no passage " +
    'matches well, return disease="uncertain" and say so rather than guessing.\n\n' +
    "Respond with disease (one of: early_blight, late_blight, leaf_curl_virus, bacterial_wilt, " +
    "fusarium_wilt, blossom_end_rot, septoria_leaf_spot, spider_mite_damage, healthy, uncertain), " +
    "confidence (0-1), cited_source (e.g. \"early_blight.txt Sec. 1.3\" -- the exact passage that " +
    "supports this diagnosis), and treatment_recommendation (plain-language advice drawn from the " +
    "cited passage)."
  );
}

async function callGemini(prompt, imageDataUrl) {
  const parts = [{ text: prompt }];
  if (imageDataUrl) {
    const [, mimeType, base64] = imageDataUrl.match(/^data:([^;]+);base64,(.+)$/) || [];
    if (base64) {
      parts.push({ inline_data: { mime_type: mimeType, data: base64 } });
    }
  }

  const res = await fetch(`${GEMINI_API_URL}?key=${GEMINI_API_KEY}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents: [{ parts }],
      generationConfig: {
        responseMimeType: "application/json",
        responseSchema: DIAGNOSIS_SCHEMA,
      },
    }),
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Gemini API ${res.status}: ${body.slice(0, 200)}`);
  }

  const data = await res.json();
  const text = data?.candidates?.[0]?.content?.parts?.find((p) => p.text)?.text;
  if (!text) throw new Error("Gemini returned no text content");
  return JSON.parse(text);
}

async function callGeminiWithRetry(prompt, imageDataUrl, maxAttempts = 3) {
  let lastErr;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await callGemini(prompt, imageDataUrl);
    } catch (err) {
      lastErr = err;
      console.warn(`Gemini attempt ${attempt}/${maxAttempts} failed:`, err.message);
      if (attempt < maxAttempts) await new Promise((r) => setTimeout(r, 1500 * attempt));
    }
  }
  throw lastErr;
}

/**
 * @param {string} symptomDescription
 * @param {string|null} imageDataUrl - optional data: URL of the uploaded photo
 * @returns {Promise<{disease: string, confidence: number, cited_source: string|null, treatment_recommendation: string, source: "gemini"|"fallback"}>}
 */
export async function diagnoseCropPhoto(symptomDescription, imageDataUrl = null) {
  const passages = await retrieveDiseaseContext(symptomDescription, 3);
  const contextBlock = formatContextBlock(passages);
  const prompt = buildPrompt(symptomDescription, contextBlock);

  try {
    const result = await callGeminiWithRetry(prompt, imageDataUrl);
    return {
      disease: result.disease,
      confidence: Math.max(0, Math.min(1, result.confidence)),
      cited_source: result.cited_source || null,
      treatment_recommendation: result.treatment_recommendation,
      source: "gemini",
    };
  } catch (err) {
    console.warn("Gemini call failed, falling back to local heuristic:", err.message);
    const fallback = await fallbackDiagnose(symptomDescription, passages);
    return { ...fallback, source: "fallback" };
  }
}

// --- Fallback path: the original keyword/RAG heuristic, used ONLY when the
// live Gemini call fails after retries. ---

const DISEASE_KEYWORDS = {
  early_blight: ["ring", "target spot", "concentric", "brown spot", "lower leaves", "dark spot"],
  late_blight: ["water-soaked", "greasy", "olive", "white fuzzy", "collapse", "cool", "wet weather"],
  leaf_curl_virus: ["curl", "curling", "stunt", "bushy", "small leaves", "crinkle"],
  bacterial_wilt: ["sudden", "wilted", "wilt", "milky", "ooze", "still green"],
  fusarium_wilt: ["one side", "slow wilt", "yellow then wilt"],
  blossom_end_rot: ["blossom end", "bottom of fruit", "black patch on fruit", "sunken fruit", "fruit tip"],
  septoria_leaf_spot: ["small spots", "tiny spots", "many spots", "black specks"],
  spider_mite_damage: ["stippling", "speckle", "webbing", "bronze", "dusty", "fine web"],
  healthy: ["looks fine", "healthy", "no problem", "growing well", "green and growing", "nothing wrong"],
};

function keywordClassify(symptomDescription) {
  const text = symptomDescription.toLowerCase();
  let bestDisease = null;
  let bestScore = 0;
  for (const [disease, keywords] of Object.entries(DISEASE_KEYWORDS)) {
    const score = keywords.filter((kw) => text.includes(kw)).length;
    if (score > bestScore) {
      bestDisease = disease;
      bestScore = score;
    }
  }
  return bestScore > 0 ? [bestDisease, bestScore] : [null, 0];
}

function docFilenameForDisease(disease) {
  return disease === "healthy" ? "healthy_baseline.txt" : `${disease}.txt`;
}

// Strips both the ".txt" extension and, if present, the "_kn" suffix that
// marks a Kannada-language document (e.g. "early_blight_kn.txt" -> "early_blight"),
// so a RAG match against either language's doc set resolves to the same
// canonical disease slug.
function diseaseSlugFromFilename(filename) {
  const slug = filename.replace(/(_kn)?\.txt$/, "");
  return slug === "healthy_baseline" ? "healthy" : slug;
}

const _docTextCache = new Map();

async function fetchDocText(filename) {
  if (_docTextCache.has(filename)) return _docTextCache.get(filename);
  const res = await fetch(`data/disease_docs/${filename}`);
  const text = await res.text();
  _docTextCache.set(filename, text);
  return text;
}

// Matches the "Recommended Treatment/Action" header in either language's
// documents: English docs use that literal phrase; Kannada docs use
// "ಶಿಫಾರಸು ಮಾಡಲಾದ ಚಿಕಿತ್ಸೆ" (Recommended Treatment) or
// "ಶಿಫಾರಸು ಮಾಡಲಾದ ಕ್ರಮ" (Recommended Action).
const TREATMENT_HEADER_RE =
  /Sec\.\s*\d+\.\d+\s*—\s*(?:Recommended (?:Treatment|Action)|ಶಿಫಾರಸು ಮಾಡಲಾದ (?:ಚಿಕಿತ್ಸೆ|ಕ್ರಮ))\s*\n([\s\S]+?)(?:\n\n|$)/;

async function extractTreatmentSection(sourceDoc) {
  const text = await fetchDocText(sourceDoc);
  const match = text.match(TREATMENT_HEADER_RE);
  return match ? match[1].trim() : "See the disease guide for treatment details.";
}

async function fallbackDiagnose(symptomDescription, passages) {
  let [disease, kwScore] = keywordClassify(symptomDescription);
  let confidence;

  if (disease === null) {
    if (passages.length === 0 || passages[0].score < 0.25) {
      return {
        disease: "uncertain",
        confidence: 0.0,
        cited_source: null,
        treatment_recommendation:
          "No disease guide passage matched this description closely enough. " +
          "Try describing the specific color, shape, and location of the symptom.",
      };
    }
    disease = diseaseSlugFromFilename(passages[0].source_doc);
    confidence = Math.round(Math.min(0.75, 0.4 + passages[0].score) * 100) / 100;
  } else {
    confidence = Math.round(Math.min(0.92, 0.6 + 0.1 * kwScore) * 100) / 100;
  }

  const sourceDoc = docFilenameForDisease(disease);
  const treatment = await extractTreatmentSection(sourceDoc);

  let section;
  if (disease === "healthy") {
    section = "Sec. 9.1";
  } else {
    const hits = (await retrieveDiseaseContext(symptomDescription, 5)).filter(
      (h) => h.source_doc === sourceDoc
    );
    section = hits.length > 0 ? hits[0].section : "Sec. 1.1";
  }

  return {
    disease,
    confidence,
    cited_source: `${sourceDoc} ${section}`,
    treatment_recommendation: treatment,
  };
}
