/**
 * TEMPLATE — copy this to config.js (or run `python scripts/generate_config.py`
 * to generate it from a .env file) and fill in a real key before running the
 * app locally or deploying.
 *
 * config.js itself is gitignored because it holds a real API key; this
 * template is the only version committed to the repo.
 *
 * Get a free key at https://aistudio.google.com/apikey (no Cloud billing
 * required). The key is necessarily visible to anyone who views the
 * deployed site's JS -- there is no backend to hide it behind in this
 * zero-billing, static-hosting deployment. Mitigate by restricting the
 * key's Application restrictions to your deployed domain in Cloud Console
 * (APIs & Services -> Credentials -> this key -> HTTP referrers) if that
 * option is available for your key type; some AI-Studio-created keys have
 * it grayed out.
 */
export const GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE";
export const GEMINI_MODEL = "gemini-3.8-flash";
export const GEMINI_API_URL =
  `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent`;
