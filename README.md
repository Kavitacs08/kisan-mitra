# Kisan Mitra

Smallholder Crop Advisory Agent — AI Builder Cup 2026, Google Cloud GenAI Hackathon.
Built end-to-end from the 24-prompt catalog in `Kisan_Mitra_Implementation_Guide.html`,
run one phase at a time, with every claim below actually tested, not just written.

**Architecture note (2026-10-18):** this app was originally built as a Python FastAPI
backend deployed to Cloud Run. It has since been ported to a **100% client-side static
site** (`frontend/js/*.js`), so it can deploy on Firebase Hosting's free Spark plan with
zero billing, zero credit card, zero GCP Console access needed. The `backend/` directory
is kept in the repo as reference/history (see "Legacy backend" below) but is **not**
part of the deployed app anymore — every module in it was ported losslessly to JS; see
the file-by-file mapping in that section.

**Gen AI note (2026-10-18):** diagnosis calls the real **Gemini API** (`gemini-3.8-flash`)
directly from the browser, grounded by RAG retrieval over bilingual (English + Kannada)
disease guides, satisfying the hackathon's mandatory "must use Google Gemini/Gemma"
requirement. A local keyword/RAG heuristic exists only as a fallback if the live Gemini
call fails after retries — see `frontend/js/diagnosis.js`.

## Setup (first time after cloning)

The Gemini API key is not committed to this repo. Before running the app locally or
deploying it, generate `frontend/js/config.js` from your own key:

```bash
cp .env.example .env
# edit .env, paste a real key from https://aistudio.google.com/apikey
python scripts/generate_config.py
```

This writes `frontend/js/config.js` (gitignored) from `.env` (also gitignored). Re-run
`generate_config.py` any time you change the key in `.env`.

## Run it locally

```bash
cd frontend
python -m http.server 8732
```

Open `http://127.0.0.1:8732/index.html` in a browser. Everything runs client-side —
no backend process is needed at all.

For the extension-officer / policy view, open `http://127.0.0.1:8732/dashboard.html`
in a separate tab. It loads a pre-built snapshot (`frontend/data/dashboard_data.json`);
to refresh it after the underlying data changes, run
`python scripts/export_dashboard_json.py` and redeploy.

To regenerate the synthetic dataset (then re-copy/trim it into `frontend/data/`,
see "Legacy backend" below): `python scripts/generate_synthetic_data.py`

## What's real right now

- **Diagnosis** — a real `gemini-3.8-flash` multimodal call (photo optional, symptom text
  always included), grounded by a hand-rolled TF-IDF + cosine similarity index over 18
  disease documents — 9 English + 9 Kannada — in `frontend/data/disease_docs/`, so a
  Kannada-language symptom description (e.g. from speech recognition) retrieves relevant
  passages natively instead of failing to match English-only documents
  (`frontend/js/rag.js`, `frontend/js/diagnosis.js`). Falls back to a local
  keyword-classifier heuristic only if the live Gemini call fails after 3 retries — the
  UI visibly shows "(via Gemini)" vs. "(Gemini unavailable — local fallback used)" so
  this is never silently hidden.
- **Weather** — a real, live call to the free Open-Meteo API, no key needed, direct from
  the browser (confirmed CORS-enabled) (`frontend/js/weather.js`)
- **Dealer & market-price lookup** — real queries against the seeded
  `frontend/data/dealers.json` and `frontend/data/mandi_prices.json` (`frontend/js/market.js`)
- **Outbreak early-warning** — a real geo-radius + time-window query over
  `frontend/data/diagnosis_history.csv` (`frontend/js/outbreak.js`)
- **Plot-level memory** — a real recurring-disease check over the same plot's diagnosis
  history (`frontend/js/plot-memory.js`)
- **Orchestration** — real branching logic: diseased → dealer lookup; healthy + near
  harvest → sell-price lookup (`frontend/js/advisory.js`)
- **Translation** — pre-written Kannada templates per known disease (not a generic
  translator — see the honesty note in `frontend/js/translation.js`)
- **Voice advisory** — feature-detects a real `kn-IN` voice via the browser's
  `SpeechSynthesis` API; speaks it when one is found (most reliable on Chrome for
  Android), falls back to the same "voice unavailable, text shown" UX otherwise
  (`frontend/js/tts.js`)
- **Crop-loss insurance claim assistant** — a real severity/confidence gate that packages
  the diagnosis into a structured, fileable evidence packet with a claim ID
  (`frontend/js/insurance.js`)
- **Group-buy / collective bargaining alert** — a real check against the live outbreak
  signal and the real dealer directory for whether combined nearby demand clears a bulk
  discount threshold (`frontend/js/group-buy.js`)
- **District dashboard for extension officers** — loads a pre-aggregated, village-level
  snapshot (`frontend/data/dashboard_data.json`, built by
  `scripts/export_dashboard_json.py`); never ships raw farmer/plot data to the browser
  (`frontend/js/dashboard-data.js`, `frontend/dashboard.html`)
- **Frontend** — a real, working single-page app (camera input, Web Speech API voice
  input, result/dealer/outbreak/insurance/group-buy cards) plus a separate extension-officer
  dashboard page, both served, reachable, and verified with Playwright with **zero
  backend process running** (zero console errors) (`frontend/index.html`,
  `frontend/dashboard.html`)

## Going live

This repo is on GitHub: https://github.com/Kavitacs08/kisan-mitra — deploys are driven
from a local clone's committed state, not ad hoc edits.

**First time on a new machine:**
1. `git clone https://github.com/Kavitacs08/kisan-mitra.git && cd kisan-mitra`
2. Complete the "Setup" step above (`.env` → `generate_config.py`) — every machine
   deploying this repo needs its own `.env`; it is never committed.
3. `npm install -g firebase-tools` (if not already installed), then `firebase login`
   (interactive; opens a browser, or gives a manual code flow if that fails).
4. The project is already linked via the committed `.firebaserc`
   (`kisan-mitra-2026-56c5d`) — `firebase use` with no args should print it.
   (If you're setting up a *different* Firebase project, create a brand-new one
   directly at https://console.firebase.google.com — do **not** import an existing GCP
   project with billing already linked, that inherits the paid Blaze plan — then
   `firebase use <your-project-id>` to update `.firebaserc`.)

**Every deploy after that:**
```bash
bash deploy/deploy_from_git.sh
```
This pulls the latest commit, regenerates `frontend/js/config.js` from your local
`.env`, refreshes the district-dashboard snapshot, and deploys. Or run the steps by
hand: `git pull --ff-only`, `python scripts/generate_config.py`,
`python scripts/export_dashboard_json.py`, `firebase deploy --only hosting`.

That's it — no Cloud Run, no Firestore, no Vertex AI, no billing account, no credit
card. This project is live at **https://kisan-mitra-2026-56c5d.web.app**.

`deploy/firebase.json` and `deploy/deploy_firebase.sh` are an earlier draft kept for
reference; the config actually used lives at the project root (`firebase.json` +
`.firebaserc`).

## Legacy backend (not deployed, kept for reference)

The original architecture lives in `backend/*.py` (Python/FastAPI) and was ported
losslessly to `frontend/js/*.js` — same logic, same constants, same thresholds, verified
to produce identical output (see migration notes). Mapping:

| Python (legacy, not deployed) | JS (live) |
|---|---|
| `backend/rag.py` | `frontend/js/rag.js` |
| `backend/gemini_client.py` (mock path) | `frontend/js/diagnosis.js` |
| `backend/translation.py` | `frontend/js/translation.js` |
| `backend/tts.py` | `frontend/js/tts.js` (upgraded: real `kn-IN` voice feature-detection) |
| `backend/weather.py` | `frontend/js/weather.js` |
| `backend/market_tools.py` | `frontend/js/market.js` |
| `backend/outbreak.py` | `frontend/js/outbreak.js` |
| `backend/plot_memory.py` | `frontend/js/plot-memory.js` |
| `backend/insurance.py` | `frontend/js/insurance.js` |
| `backend/group_buy.py` | `frontend/js/group-buy.js` |
| `backend/dashboard.py` | run once at build time via `scripts/export_dashboard_json.py`, **not** ported to JS (see privacy note below) |
| `backend/advisory.py` | `frontend/js/advisory.js` |
| `backend/main.py` (FastAPI routes) | `frontend/js/main.js` / `frontend/js/dashboard-main.js` (UI wiring, no HTTP server) |

**Privacy note on the dashboard**: `backend/dashboard.py` joins `farmers.csv` (names,
phone numbers) to compute village-level aggregates. Shipping that raw file to a public
static bundle so the browser could do the same join would leak farmer identity/location
linkage. Instead, `scripts/export_dashboard_json.py` runs the original Python
aggregation once, locally, against the private `backend/data/farmers.csv`, and writes
only the anonymized result to `frontend/data/dashboard_data.json`. `frontend/data/plots.csv`
(shipped publicly, used by `outbreak.js`/`plot-memory.js`) has its `farmer_id` column
stripped — neither of those two features ever needs it.

The never-implemented real-service paths (`# REAL:` stubs for Gemini multimodal, Vertex
AI Search, Cloud Translation, Cloud Text-to-Speech) and the Cloud Run deploy scripts
(`deploy/Dockerfile`, `deploy/deploy_cloud_run.sh`) remain in the repo as reference for
if/when a GCP project with billing becomes available and a true multimodal Gemini
upgrade is wanted.

## Project layout

```
.env                   NOT committed — your real Gemini API key (copy from .env.example)
.env.example           committed template for .env
firebase.json          Firebase Hosting config actually used for deploy (project root)
.firebaserc            committed — links this repo to kisan-mitra-2026-56c5d
frontend/              THE DEPLOYED APP (static site)
  index.html            farmer-facing single-page app
  dashboard.html         extension-officer dashboard
  js/                     every ported module (see mapping table above)
                           config.js is NOT committed — generated by generate_config.py;
                           config.example.js is the committed template
  data/                   dealers.json, mandi_prices.json, plots.csv (trimmed),
                           diagnosis_history.csv, disease_docs/*.txt (9 English + 9
                           Kannada), dashboard_data.json (pre-built snapshot)
backend/               LEGACY, not deployed — original Python/FastAPI reference impl.
data/                  LEGACY — the original (untrimmed) dataset backend/ reads from
scripts/               data generator, generate_config.py (writes config.js from .env),
                        export_dashboard_json.py (build-time dashboard aggregation),
                        offline-model training script, PDF/PPTX builders,
                        Playwright verification drivers
deploy/                firebase.json (earlier draft, see "Going live"), deploy_firebase.sh;
                        Dockerfile/deploy_cloud_run.sh kept as legacy reference
docs/                  demo script, proposal deck content, proposal PDF/PPTX,
                        OpenAPI spec (legacy), verification screenshots
```
