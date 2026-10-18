# Kisan Mitra — Proposal Deck Content

**Theme:** Sustainability & Social Impact | **Submission:** AI Builder Cup 2026, Google Cloud GenAI Hackathon

---

## Slide 1 — Problem Statement
A smallholder tomato farmer in Karnataka spots a diseased leaf with no agronomist to call
and unreliable connectivity to search with. Existing diagnosis apps (Plantix, PlantVillage)
identify the disease but stop there — they don't say where to buy the treatment nearby, what
it costs, or whether a nearby outbreak means the farmer should check their crop sooner than
they otherwise would.

## Slide 2 — Target User
Smallholder tomato farmers in the Kolar tomato belt, Karnataka — typically 0.5-4 acre
plots, variable literacy, intermittent connectivity, and no dedicated access to an
agronomist. Primary language: Kannada.

## Slide 3 — Solution Overview
Kisan Mitra turns a photo and a spoken description into:
1. A cited disease diagnosis (not a black-box guess)
2. A spoken advisory in the farmer's own language, weather-aware
3. The nearest dealer in stock for the recommended treatment, with today's price
4. A proactive outbreak alert when nearby plots report the same disease — before this
   farmer's own crop shows symptoms
5. (When the crop is healthy and near harvest) the best nearby price to sell at today
6. A crop-loss insurance evidence packet, a group-buy discount alert, and an aggregated
   district dashboard for extension officers

## Slide 4 — Beyond Diagnosis: From Advice to Economic Action
- **Insurance claim assistant**: a severe, confident diagnosis auto-generates a structured
  evidence packet (citation, confidence, estimated yield loss) formatted for a crop-loss
  insurance claim — most farmers with insurance never file because the paperwork is a
  barrier they can't clear alone.
- **Group-buy alert**: when an outbreak signal shows 3+ nearby farmers need the same
  treatment, checks whether combined demand clears the dealer's bulk-pricing threshold and
  surfaces a group discount — turning an early warning into coordinated economic action.
- **District dashboard**: an anonymized, village-level aggregate view of outbreak clusters
  for a local extension officer or NGO — not built for one farmer, built for deciding where
  to send resources district-wide.

## Slide 5 — Architecture Diagram (description for the designer)
Left to right: Farmer (photo + voice) → Firebase Hosting (frontend) → Cloud Run (FastAPI
backend) → branches to: Gemini multimodal diagnosis (grounded via Vertex AI Search over the
regional disease guide) · Cloud Translation + Text-to-Speech (voice advisory) · Firestore
(dealer directory, mandi prices, diagnosis history) · Open-Meteo (weather context). The
Firestore diagnosis history feeds back into three agentic reasoning steps: a geo-radius
query for outbreak detection across farmers, a per-plot history query for recurring-issue
detection on the same plot, and a district-wide aggregation for the extension-officer
dashboard. An outbreak signal additionally triggers a bulk-pricing check against the dealer
directory for the group-buy alert.

## Slide 6 — Gen AI Usage Summary
- **Gemini multimodal**: diagnoses from a photo plus a spoken description together, citing
  the specific disease-guide passage that supports the diagnosis rather than guessing.
- **Vertex AI Search (RAG)**: grounds every diagnosis in the actual regional extension guide,
  so the system can say *why*, not just *what*.
- **Gemini function calling**: orchestrates which tool to call next — the dealer lookup when
  diseased, the sell-price lookup when healthy and near harvest, the group-buy check when an
  outbreak signal fires — based on the diagnosis outcome, not a fixed menu.
- **Gemini synthesis**: turns a cluster of raw nearby diagnosis records into a plain-language
  early-warning alert, and packages a severe diagnosis into a structured insurance evidence
  summary.

## Slide 7 — Impact Statement
Each piece of this exists separately in the market today — Plantix diagnoses, AgroStar
connects to dealers, PlantVillage pairs AI with weather context — but none combine diagnosis,
voice, and market linkage into one flow, and none reason across farmers or across time on the
same plot. The outbreak alert in particular reaches a farmer before their own crop shows
damage, which no existing tool in this space does. No existing tool turns a diagnosis into a
fileable insurance claim, a coordinated bulk-buy discount, or a district-level resourcing
signal — moving the whole system from advice to economic action and policy support.

## Slide 8 — Resource & Environmental Impact
- **Targeted treatment, not blanket spraying**: a cited diagnosis recommends the specific
  input needed instead of a farmer guessing and over-applying agrochemicals — reducing
  chemical runoff into the surrounding soil and water.
- **Weather-timed application**: the live weather check avoids recommending a spray right
  before rain washes it off — less wasted product, less chemical runoff from a wasted
  application.
- **Earlier detection means less crop loss**: every tomato lost to a late-caught disease is
  wasted water, soil nutrients, and land-use already invested in that crop — the outbreak
  alert catches disease before symptoms even appear on a given plot.
- **Plot-level memory enables root-cause fixes**: flagging a recurring disease as a drainage
  or soil issue, not just re-treating the symptom, shifts the farmer toward a lasting fix
  instead of repeat chemical use season after season.

## Slide 9 — Scalability & Future Roadmap
- **Sell-side market linkage** (built): extends the agent from "where to buy treatment" to
  "where to sell the harvest," turning a disease-lookup tool into a season-long companion.
- **Offline-first fallback** (planned): a distilled on-device classifier for the most common
  8-10 regional diseases, so core diagnosis keeps working when connectivity drops entirely.
- **Expansion path**: adding a new crop or region means indexing a new disease guide into
  Vertex AI Search, not rewriting the diagnosis logic — the architecture is crop-agnostic by
  design even though this build is scoped to tomato in Karnataka for the demo.
