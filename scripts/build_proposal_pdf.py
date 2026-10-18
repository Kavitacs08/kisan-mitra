"""Prompt 24 (packaging)  -  renders docs/proposal_deck_content.md into a
landscape, slide-styled PDF matching the hackathon's "deck/PPT converted to
PDF" submission requirement, using reportlab (pure Python, no external
binary needed).
"""
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "docs", "Kisan_Mitra_Proposal.pdf")

PAGE_SIZE = (13.333 * inch, 7.5 * inch)  # 16:9 widescreen, matches a PPT export

INK = colors.HexColor("#1b1f23")
MUTED = colors.HexColor("#5b6168")
ACCENT = colors.HexColor("#1f7a4c")
ACCENT_SOFT = colors.HexColor("#e5f4ee")
BORDER = colors.HexColor("#dcd8ce")
BG = colors.HexColor("#f6f5f0")

MARGIN_X = 0.75 * inch
TITLE_Y = 6.55 * inch
CONTENT_TOP = 5.95 * inch
CONTENT_BOTTOM = 0.55 * inch
LINE_HEIGHT = 0.34 * inch
WRAP_WIDTH_CHARS = 108


def wrap(text, width=WRAP_WIDTH_CHARS):
    import textwrap
    return textwrap.wrap(text, width=width)


def draw_chrome(c, eyebrow, slide_no, total_slides):
    c.setFillColor(BG)
    c.rect(0, 0, PAGE_SIZE[0], PAGE_SIZE[1], stroke=0, fill=1)

    c.setFillColor(ACCENT)
    c.rect(0, PAGE_SIZE[1] - 0.14 * inch, PAGE_SIZE[0], 0.14 * inch, stroke=0, fill=1)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(ACCENT)
    c.drawString(MARGIN_X, PAGE_SIZE[1] - 0.42 * inch, eyebrow.upper())

    c.setFont("Helvetica", 9)
    c.setFillColor(MUTED)
    c.drawRightString(PAGE_SIZE[0] - MARGIN_X, 0.35 * inch,
                       f"Kisan Mitra  |  AI Builder Cup 2026  |  {slide_no} / {total_slides}")


def draw_title(c, title):
    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(INK)
    c.drawString(MARGIN_X, TITLE_Y, title)
    c.setStrokeColor(BORDER)
    c.setLineWidth(1)
    c.line(MARGIN_X, TITLE_Y - 0.18 * inch, PAGE_SIZE[0] - MARGIN_X, TITLE_Y - 0.18 * inch)


def draw_bullets(c, bullets, y_start=CONTENT_TOP, bullet_gap=0.14 * inch, body_width=None):
    y = y_start
    width = body_width or (PAGE_SIZE[0] - 2 * MARGIN_X)
    for b in bullets:
        if y < CONTENT_BOTTOM:
            break
        label = b.get("label")
        text = b["text"]
        c.setFillColor(ACCENT)
        c.circle(MARGIN_X + 0.06 * inch, y + 0.07 * inch, 0.035 * inch, stroke=0, fill=1)

        if label:
            c.setFont("Helvetica-Bold", 13)
            c.setFillColor(INK)
            c.drawString(MARGIN_X + 0.22 * inch, y, f"{label}  ")
            label_w = c.stringWidth(f"{label}  ", "Helvetica-Bold", 13)
            indent = MARGIN_X + 0.22 * inch + label_w
        else:
            indent = MARGIN_X + 0.22 * inch

        c.setFont("Helvetica", 13)
        c.setFillColor(INK)
        chars_per_line = int((width - (indent - MARGIN_X)) / 6.6)
        lines = wrap(text, width=chars_per_line)
        first = True
        for line in lines:
            x = indent if first else MARGIN_X + 0.22 * inch
            c.drawString(x, y, line)
            y -= LINE_HEIGHT
            first = False
        y -= bullet_gap
    return y


def slide_cover(c, total):
    draw_chrome(c, "AI Builder Cup 2026  -  Google Cloud GenAI Hackathon", 1, total)
    c.setFont("Helvetica-Bold", 46)
    c.setFillColor(INK)
    c.drawString(MARGIN_X, 4.3 * inch, "Kisan Mitra")
    c.setFont("Helvetica", 18)
    c.setFillColor(MUTED)
    c.drawString(MARGIN_X, 3.75 * inch, "Smallholder Crop Advisory Agent")
    c.setFont("Helvetica", 14)
    c.setFillColor(INK)
    for i, line in enumerate(wrap(
        "A photo and a spoken description become a cited diagnosis, a voice advisory in the "
        "farmer's own language, the nearest dealer with today's price, and a proactive outbreak "
        "alert  -  before the next farmer's crop even shows symptoms.", width=78)):
        c.drawString(MARGIN_X, 3.1 * inch - i * 0.3 * inch, line)

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(ACCENT)
    c.drawString(MARGIN_X, 0.9 * inch, "Theme: Sustainability & Social Impact")


def slide_content(c, slide_no, total, eyebrow, title, bullets):
    draw_chrome(c, eyebrow, slide_no, total)
    draw_title(c, title)
    draw_bullets(c, bullets)


SLIDES = [
    {
        "eyebrow": "Problem Statement",
        "title": "The Problem",
        "bullets": [
            {"text": "A smallholder tomato farmer in Karnataka spots a diseased leaf with no "
                      "agronomist to call and unreliable connectivity to search with."},
            {"text": "Existing diagnosis apps (Plantix, PlantVillage) identify the disease but stop "
                      "there  -  they don't say where to buy the treatment nearby, what it costs, "
                      "or whether a nearby outbreak means the farmer should check sooner."},
        ],
    },
    {
        "eyebrow": "Target User",
        "title": "Who This Is For",
        "bullets": [
            {"text": "Smallholder tomato farmers in the Kolar tomato belt, Karnataka."},
            {"text": "Typically 0.5-4 acre plots, variable literacy, intermittent connectivity, "
                      "no dedicated access to an agronomist."},
            {"text": "Primary language: Kannada."},
        ],
    },
    {
        "eyebrow": "Solution Overview",
        "title": "What Kisan Mitra Does",
        "bullets": [
            {"label": "1.", "text": "A cited disease diagnosis  -  not a black-box guess."},
            {"label": "2.", "text": "A spoken advisory in the farmer's own language, weather-aware."},
            {"label": "3.", "text": "The nearest dealer in stock for the recommended treatment, with "
                                     "today's price."},
            {"label": "4.", "text": "A proactive outbreak alert when nearby plots report the same "
                                     "disease  -  before this farmer's own crop shows symptoms."},
            {"label": "5.", "text": "When the crop is healthy and near harvest, the best nearby price "
                                     "to sell at today."},
            {"label": "6.", "text": "A crop-loss insurance evidence packet, a group-buy discount "
                                     "alert, and an aggregated district dashboard for extension "
                                     "officers."},
        ],
    },
    {
        "eyebrow": "Beyond Diagnosis",
        "title": "From Advice to Economic Action",
        "bullets": [
            {"label": "Insurance claim assistant:", "text": "a severe, confident diagnosis "
                      "auto-generates a structured evidence packet (citation, confidence, "
                      "estimated yield loss) formatted for a crop-loss insurance claim  -  most "
                      "farmers with insurance never file because the paperwork is a barrier they "
                      "can't clear alone."},
            {"label": "Group-buy alert:", "text": "when an outbreak signal shows 3+ nearby farmers "
                      "need the same treatment, checks whether combined demand clears the "
                      "dealer's bulk-pricing threshold and surfaces a group discount  -  turning "
                      "an early warning into coordinated economic action."},
            {"label": "District dashboard:", "text": "an anonymized, village-level aggregate view "
                      "of outbreak clusters for a local extension officer or NGO  -  not built for "
                      "one farmer, built for deciding where to send resources district-wide."},
        ],
    },
    {
        "eyebrow": "Architecture",
        "title": "How It's Built",
        "bullets": [
            {"text": "Farmer (photo + voice) -> Firebase Hosting -> Cloud Run (FastAPI backend)"},
            {"text": "Gemini multimodal diagnosis, grounded via Vertex AI Search over the regional "
                      "disease guide"},
            {"text": "Cloud Translation + Text-to-Speech for the voice advisory"},
            {"text": "Firestore holds the dealer directory, mandi prices, and diagnosis history"},
            {"text": "Diagnosis history feeds three agentic reasoning steps: a geo-radius outbreak "
                      "query across farmers, a per-plot history query for recurring issues, and a "
                      "district-wide aggregation for the extension-officer dashboard"},
            {"text": "An outbreak signal additionally triggers a bulk-pricing check against the "
                      "dealer directory for the group-buy alert"},
        ],
    },
    {
        "eyebrow": "Gen AI Usage",
        "title": "How Generative AI Is Used",
        "bullets": [
            {"label": "Gemini multimodal:", "text": "diagnoses from a photo plus a spoken description "
                                                      "together, citing the specific passage that "
                                                      "supports the diagnosis rather than guessing."},
            {"label": "Vertex AI Search (RAG):", "text": "grounds every diagnosis in the actual "
                                                           "regional extension guide, so the system can "
                                                           "say why, not just what."},
            {"label": "Gemini function calling:", "text": "orchestrates which tool to call next  -  "
                                                            "dealer lookup when diseased, sell-price "
                                                            "lookup when healthy and near harvest, "
                                                            "group-buy check when an outbreak signal "
                                                            "fires."},
            {"label": "Gemini synthesis:", "text": "turns a cluster of raw nearby diagnosis records into "
                                                     "a plain-language early-warning alert, and packages "
                                                     "a severe diagnosis into a structured insurance "
                                                     "evidence summary."},
        ],
    },
    {
        "eyebrow": "Impact",
        "title": "Why This Matters",
        "bullets": [
            {"text": "Each piece exists separately today  -  Plantix diagnoses, AgroStar connects to "
                      "dealers, PlantVillage pairs AI with weather  -  but none combine diagnosis, "
                      "voice, and market linkage into one flow."},
            {"text": "None reason across farmers or across time on the same plot."},
            {"text": "The outbreak alert reaches a farmer before their own crop shows damage  -  "
                      "something no existing tool in this space does."},
            {"text": "No existing tool turns a diagnosis into a fileable insurance claim, a "
                      "coordinated bulk-buy discount, or a district-level resourcing signal  -  "
                      "moving the whole system from advice to economic action and policy support."},
        ],
    },
    {
        "eyebrow": "Resource & Environmental Impact",
        "title": "Why This Is Sustainability, Not Just Social Good",
        "bullets": [
            {"label": "Targeted treatment, not blanket spraying:", "text": "a cited diagnosis "
                      "recommends the specific input needed (e.g. copper oxychloride for early "
                      "blight) instead of a farmer guessing and over-applying agrochemicals  -  "
                      "reducing chemical runoff into the surrounding soil and water."},
            {"label": "Weather-timed application:", "text": "the live weather check avoids "
                      "recommending a spray right before rain washes it off  -  less wasted "
                      "product, less chemical runoff from a wasted application."},
            {"label": "Earlier detection means less crop loss:", "text": "every tomato lost to a "
                      "late-caught disease is wasted water, soil nutrients, and land-use already "
                      "invested in that crop  -  the outbreak alert catches disease before "
                      "symptoms even appear on a given plot."},
            {"label": "Plot-level memory enables root-cause fixes:", "text": "flagging a "
                      "recurring disease as a drainage or soil issue, not just re-treating the "
                      "symptom, shifts the farmer toward a lasting fix instead of repeat chemical "
                      "use season after season."},
        ],
    },
    {
        "eyebrow": "Scalability & Roadmap",
        "title": "What's Next",
        "bullets": [
            {"label": "Built:", "text": "sell-side market linkage  -  extends the agent from \"where "
                                          "to buy treatment\" to \"where to sell the harvest.\""},
            {"label": "Planned:", "text": "an offline-first fallback  -  a distilled on-device "
                                           "classifier for the 8-10 most common regional diseases, "
                                           "so core diagnosis keeps working with no connectivity."},
            {"label": "Expansion path:", "text": "a new crop or region means indexing a new disease "
                                                   "guide into Vertex AI Search, not rewriting the "
                                                   "diagnosis logic  -  crop-agnostic by design."},
        ],
    },
    {
        "eyebrow": "Submission",
        "title": "Built On Google Cloud",
        "bullets": [
            {"label": "Gen AI:", "text": "Gemini (multimodal diagnosis, function calling, synthesis)"},
            {"label": "Retrieval:", "text": "Vertex AI Search"},
            {"label": "Deployment:", "text": "Cloud Run (backend) + Firebase Hosting (frontend)"},
            {"label": "Data:", "text": "Firestore (dealers, mandi prices, diagnosis history)"},
            {"label": "Accessibility:", "text": "Cloud Translation + Cloud Text-to-Speech"},
        ],
    },
]


def build():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    c = canvas.Canvas(OUT_PATH, pagesize=PAGE_SIZE)

    total = len(SLIDES) + 1
    slide_cover(c, total)
    c.showPage()

    for i, s in enumerate(SLIDES, start=2):
        slide_content(c, i, total, s["eyebrow"], s["title"], s["bullets"])
        c.showPage()

    c.save()
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    build()
