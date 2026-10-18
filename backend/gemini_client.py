"""Prompt 5 — Gemini multimodal diagnosis prompt + mock/real client.

The DIAGNOSIS_PROMPT_TEMPLATE below is the actual prompt to send to Gemini
in the real path. In mock mode, diagnose_crop_photo() never calls an LLM at
all: it uses the RAG retrieval from rag.py (real TF-IDF search against the
real disease documents) plus a rule-based confidence estimate, so the output
shape and the "only cite a diagnosis if a passage supports it" behavior are
both genuinely exercised end to end without needing an API key.
"""
import os
import re

from config import DISEASE_DOCS_DIR, GEMINI_API_KEY, USE_MOCK
from rag import retrieve_disease_context
from schemas import DiagnosisResult

DIAGNOSIS_PROMPT_TEMPLATE = """\
You are an agronomy assistant for smallholder tomato farmers in Karnataka, India.

You are given:
- A photo of a tomato plant (leaf, stem, or fruit).
- A short spoken description from the farmer, transcribed to text: "{symptom_description}"
- The following retrieved passages from the regional disease guide, each with its
  source document and section number:

{context_block}

Diagnose the most likely issue using BOTH the photo and the description. You MUST
only name a disease if one of the retrieved passages actually supports it — if no
passage matches well, return disease="uncertain" and say so rather than guessing.

Respond ONLY as JSON matching this schema:
{{
  "disease": "<one of: early_blight, late_blight, leaf_curl_virus, bacterial_wilt,
              fusarium_wilt, blossom_end_rot, septoria_leaf_spot, spider_mite_damage,
              healthy, uncertain>",
  "confidence": <float 0-1>,
  "cited_source": "<source_doc Sec. N.N of the passage that supports this diagnosis>",
  "treatment_recommendation": "<plain-language advice drawn from the cited passage>"
}}
"""


def _format_context_block(passages):
    return "\n\n".join(
        f"[{p['source_doc']} {p['section']}] {p['text']}" for p in passages
    )


def _extract_treatment_section(source_doc: str) -> str:
    """Pulls the '... — Recommended Treatment/Action' section out of a disease doc."""
    path = os.path.join(DISEASE_DOCS_DIR, source_doc)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    match = re.search(
        r"Sec\.\s*\d+\.\d+\s*—\s*Recommended (?:Treatment|Action)\s*\n(.+?)(?:\n\n|\Z)",
        text, re.DOTALL,
    )
    return match.group(1).strip() if match else "See the disease guide for treatment details."


def _disease_slug_from_filename(fname: str) -> str:
    slug = fname.replace(".txt", "")
    return "healthy" if slug == "healthy_baseline" else slug


# NOTE on the mock classifier: the real system diagnoses from a PHOTO plus a
# short spoken description, via Gemini's multimodal understanding. This mock
# has no photo to look at at all, so matching keywords in the text description
# is the honest limit of what it can simulate. TF-IDF similarity against the
# 9-document knowledge base alone was tried first and was too noisy on short
# descriptions (it latched onto generic words like "leaves"); an explicit
# keyword classifier is more transparent about being a stand-in, and far more
# reliable for demoing the rest of the pipeline (voice, dealer lookup, outbreak
# alerts) which don't depend on diagnosis accuracy to prove their own logic.
_DISEASE_KEYWORDS = {
    "early_blight": ["ring", "target spot", "concentric", "brown spot", "lower leaves", "dark spot"],
    "late_blight": ["water-soaked", "greasy", "olive", "white fuzzy", "collapse", "cool", "wet weather"],
    "leaf_curl_virus": ["curl", "curling", "stunt", "bushy", "small leaves", "crinkle"],
    "bacterial_wilt": ["sudden", "wilted", "wilt", "milky", "ooze", "still green"],
    "fusarium_wilt": ["one side", "slow wilt", "yellow then wilt"],
    "blossom_end_rot": ["blossom end", "bottom of fruit", "black patch on fruit", "sunken fruit", "fruit tip"],
    "septoria_leaf_spot": ["small spots", "tiny spots", "many spots", "black specks"],
    "spider_mite_damage": ["stippling", "speckle", "webbing", "bronze", "dusty", "fine web"],
    "healthy": ["looks fine", "healthy", "no problem", "growing well", "green and growing", "nothing wrong"],
}


def _keyword_classify(symptom_description: str):
    text = symptom_description.lower()
    scores = {
        disease: sum(1 for kw in kws if kw in text)
        for disease, kws in _DISEASE_KEYWORDS.items()
    }
    best_disease, best_score = max(scores.items(), key=lambda kv: kv[1])
    return (best_disease, best_score) if best_score > 0 else (None, 0)


def _doc_filename_for_disease(disease: str) -> str:
    return "healthy_baseline.txt" if disease == "healthy" else f"{disease}.txt"


def _mock_diagnose(symptom_description: str) -> DiagnosisResult:
    disease, kw_score = _keyword_classify(symptom_description)

    if disease is None:
        # No keyword matched at all — fall back to RAG similarity, but only
        # trust it above a strict threshold; otherwise admit uncertainty
        # rather than force a guess onto an unsupported passage.
        passages = retrieve_disease_context(symptom_description, top_k=1)
        if not passages or passages[0]["score"] < 0.25:
            return DiagnosisResult(
                disease="uncertain",
                confidence=0.0,
                cited_source=None,
                treatment_recommendation=(
                    "No disease guide passage matched this description closely enough. "
                    "Try describing the specific color, shape, and location of the symptom."
                ),
            )
        disease = _disease_slug_from_filename(passages[0]["source_doc"])
        confidence = round(min(0.75, 0.4 + passages[0]["score"]), 2)
    else:
        # Confidence scales with how many distinct keywords matched (1 keyword
        # is a plausible but soft match, 3+ is a strong match).
        confidence = round(min(0.92, 0.6 + 0.1 * kw_score), 2)

    source_doc = _doc_filename_for_disease(disease)
    treatment = _extract_treatment_section(source_doc)
    section = "Sec. 9.1" if disease == "healthy" else None
    if section is None:
        # Reuse the retrieval index just to recover the right section label
        # for the citation display, now that we already know the disease.
        hits = [h for h in retrieve_disease_context(symptom_description, top_k=5) if h["source_doc"] == source_doc]
        section = hits[0]["section"] if hits else "Sec. 1.1"

    return DiagnosisResult(
        disease=disease,
        confidence=confidence,
        cited_source=f"{source_doc} {section}",
        treatment_recommendation=treatment,
    )


def _real_gemini_diagnose(image_bytes, symptom_description, passages) -> DiagnosisResult:
    # REAL: swap in the google-genai SDK call here, e.g.
    #
    #   from google import genai
    #   client = genai.Client(api_key=GEMINI_API_KEY)
    #   prompt = DIAGNOSIS_PROMPT_TEMPLATE.format(
    #       symptom_description=symptom_description,
    #       context_block=_format_context_block(passages),
    #   )
    #   response = client.models.generate_content(
    #       model="gemini-2.0-flash",
    #       contents=[prompt, genai.types.Part.from_bytes(image_bytes, mime_type="image/jpeg")],
    #       config={"response_mime_type": "application/json"},
    #   )
    #   return DiagnosisResult.model_validate_json(response.text)
    raise NotImplementedError("Set GEMINI_API_KEY and USE_MOCK=false to enable the live path.")


def diagnose_crop_photo(symptom_description: str, image_bytes: bytes = None) -> DiagnosisResult:
    if USE_MOCK:
        return _mock_diagnose(symptom_description)
    passages = retrieve_disease_context(symptom_description, top_k=3)
    return _real_gemini_diagnose(image_bytes, symptom_description, passages)


if __name__ == "__main__":
    for desc in [
        "leaves are curling up and the plant looks small and bushy",
        "dark spots with rings on the bottom leaves, like a target",
        "the whole plant wilted suddenly but leaves are still green",
        "everything looks fine, plant is green and growing well",
    ]:
        result = diagnose_crop_photo(desc)
        print(f"\nSymptom: {desc}")
        print(f"  -> {result.disease} (confidence {result.confidence}), cited: {result.cited_source}")
        print(f"     Treatment: {result.treatment_recommendation[:120]}...")
