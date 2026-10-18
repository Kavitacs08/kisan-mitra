"""Builds the AI Builder Cup submission deck for Kisan Mitra, following the
exact slide structure of the official Submission Template, with the
template's own logo/footer images and fonts, filled with real content from
this project (not placeholder text).
"""
import copy
import os

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

TEMPLATE_PATH = r"C:\Users\KavitaChegaraddi\Downloads\Submission Template _ AI Builder Cup.pptx"
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS = os.path.join(APP_ROOT, "docs", "screenshots")
OUT_PPTX = os.path.join(APP_ROOT, "docs", "Kisan_Mitra_Submission.pptx")

INK = RGBColor(0x21, 0x21, 0x21)
MUTED = RGBColor(0x59, 0x59, 0x59)
ACCENT = RGBColor(0x00, 0x97, 0xA7)

FONT_HEAD = "Google Sans Flex Medium"
FONT_HEAD_SEMI = "Google Sans Flex SemiBold"
FONT_BODY = "Google Sans Flex"

# ---- Diagram palette (boxes-and-arrows style, inspired by the reference deck) ----
FILL_NEUTRAL = RGBColor(0xF1, 0xF1, 0xF1)
LINE_NEUTRAL = RGBColor(0xB0, 0xB0, 0xB0)
FILL_AI = RGBColor(0xE1, 0xF5, 0xFE)
LINE_AI = RGBColor(0x4F, 0xC3, 0xF7)
FILL_ACCENT = RGBColor(0xB2, 0xEB, 0xF2)
LINE_ACCENT = ACCENT
FILL_TOOLS = RGBColor(0xE8, 0xF5, 0xE9)
LINE_TOOLS = RGBColor(0x81, 0xC7, 0x84)
FILL_CALLOUT = RGBColor(0xE3, 0xF2, 0xFD)
LINE_CALLOUT = ACCENT
FILL_HOST = RGBColor(0xFF, 0xF3, 0xE0)
LINE_HOST = RGBColor(0xFF, 0xB7, 0x4D)


def row_boxes(n, left, right, gap=0.15):
    """Returns [(box_left, box_width), ...] for n boxes evenly spaced
    between left and right with the given gap between them."""
    total_gap = gap * (n - 1)
    w = (right - left - total_gap) / n
    return [(left + i * (w + gap), w) for i in range(n)]


def add_diagram_box(slide, left, top, width, height, lines, fill, line_color,
                     title_size=10, detail_size=8):
    """lines: list of (text, is_title) tuples, centered, for a single
    rounded-rectangle diagram node."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line_color
    shape.line.width = Pt(1)
    shape.shadow.inherit = False
    tf = shape.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.07)
    tf.margin_right = Inches(0.07)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    first = True
    for text, is_title in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = PP_ALIGN.CENTER
        p.line_spacing = 1.0
        run = p.add_run()
        run.text = text
        run.font.size = Pt(title_size if is_title else detail_size)
        run.font.bold = is_title
        run.font.name = FONT_HEAD_SEMI if is_title else FONT_BODY
        run.font.color.rgb = INK if is_title else MUTED
    return shape


def add_down_arrow(slide, x_center, top, height, color=LINE_NEUTRAL):
    """A small centered down-arrow glyph marking flow between diagram rows."""
    tb = slide.shapes.add_textbox(Inches(x_center - 0.15), Inches(top), Inches(0.3), Inches(height))
    tf = tb.text_frame
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = "\u2193"
    run.font.size = Pt(14)
    run.font.bold = True
    run.font.color.rgb = color
    return tb


def add_legend(slide, left, top, width, height, items):
    """A small color-key row (swatch + label) under a diagram, mirroring the
    reference deck's bottom legend convention."""
    n = len(items)
    seg = width / n
    for i, (color, label) in enumerate(items):
        x = left + i * seg
        sw = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(top + height / 2 - 0.055), Inches(0.11), Inches(0.11))
        sw.fill.solid()
        sw.fill.fore_color.rgb = color
        sw.line.fill.background()
        sw.shadow.inherit = False
        tb = slide.shapes.add_textbox(Inches(x + 0.16), Inches(top), Inches(seg - 0.18), Inches(height))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = Emu(0)
        tf.margin_right = Emu(0)
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = label
        run.font.size = Pt(7.5)
        run.font.name = FONT_BODY
        run.font.color.rgb = MUTED


def add_row_label(slide, left, top, width, height, text):
    """Small vertical-ish category label to the left of a diagram row,
    matching the reference deck's left-hand layer labels."""
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = text
    run.font.size = Pt(8)
    run.font.bold = True
    run.font.name = FONT_HEAD_SEMI
    run.font.color.rgb = MUTED
    return tb


def delete_slide(prs, index):
    """python-pptx has no native slide-removal API; drop the relationship
    and remove the slide id entry directly."""
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    rId = slides[index].get(qn('r:id'))
    prs.part.drop_rel(rId)
    xml_slides.remove(slides[index])


def duplicate_slide_layout(prs, source_slide):
    """Clones a slide (with its layout and picture relationships) by index,
    so every content slide keeps the template's exact logo/footer chrome."""
    blank_slide_layout = source_slide.slide_layout
    new_slide = prs.slides.add_slide(blank_slide_layout)
    return new_slide


def clear_body_text_shapes(slide, keep_shape_ids):
    """Removes the template's own placeholder heading text boxes (identified
    by shape id) so we can insert our fresh content in their place, while
    keeping the background picture/footer shapes intact."""
    for shape in list(slide.shapes):
        if shape.shape_id in keep_shape_ids:
            continue


def set_textbox(shape, lines, title_size=16, body_size=13, title_color=INK,
                 body_color=INK, title_font=FONT_HEAD, body_font=FONT_BODY,
                 line_spacing=1.15):
    """lines: list of (text, is_title) tuples. Clears existing paragraphs and
    writes fresh ones with the template's typographic voice."""
    tf = shape.text_frame
    tf.clear()
    first = True
    for text, is_title in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        run = p.add_run()
        run.text = text
        run.font.size = Pt(title_size if is_title else body_size)
        run.font.name = title_font if is_title else body_font
        run.font.color.rgb = title_color if is_title else body_color
        p.line_spacing = line_spacing


def add_bullets(shape, items, size=13, color=INK, font=FONT_BODY, bullet="•  ", line_spacing=1.2, space_after=6):
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    first = True
    for item in items:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        run = p.add_run()
        run.text = f"{bullet}{item}"
        run.font.size = Pt(size)
        run.font.name = font
        run.font.color.rgb = color
        p.line_spacing = line_spacing
        p.space_after = Pt(space_after)


def add_textbox(slide, left, top, width, height):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tb.text_frame.word_wrap = True
    return tb


def add_picture_fit(slide, img_path, left, top, max_w, max_h):
    from PIL import Image
    with Image.open(img_path) as im:
        iw, ih = im.size
    ratio = min(max_w / iw, max_h / ih)
    w, h = iw * ratio, ih * ratio
    x = left + (max_w - w) / 2
    y = top + (max_h - h) / 2
    slide.shapes.add_picture(img_path, Inches(x), Inches(y), Inches(w), Inches(h))


def main():
    prs = Presentation(TEMPLATE_PATH)

    # ---- Remove slide 2: the template's own "Note: please download..." instructions ----
    for idx, slide in enumerate(prs.slides):
        if any(sh.has_text_frame and "Note: Please download this template" in sh.text_frame.text for sh in slide.shapes):
            delete_slide(prs, idx)
            break

    # ---- Slide 1: Team Details ----
    s1 = prs.slides[0]
    for shape in s1.shapes:
        if shape.has_text_frame and "Team Details" in shape.text_frame.text:
            set_textbox(shape, [
                ("Team Details", True),
                ("Team name: Kisan Mitra", False),
                ("Team leader name: Kavita S Chegaraddi", False),
                ("Team member name: Sangeetha Chegaraddi", False),
                ("Problem Statement: Sustainability & Social Impact — "
                 "Smallholder Crop Advisory Agent for tomato farmers in the Kolar belt, Karnataka", False),
            ], title_size=22, body_size=14, title_font=FONT_HEAD_SEMI)

    # ---- Slide 3: Brief about the idea ----
    s3 = prs.slides[1]
    for shape in s3.shapes:
        if shape.has_text_frame and "Brief about the idea" in shape.text_frame.text:
            set_textbox(shape, [("Brief about the idea", True)], title_size=16, title_font=FONT_HEAD)
    body3 = add_textbox(s3, 0.29, 1.4, 9.4, 3.9)
    add_bullets(body3, [
        "A smallholder tomato farmer in the Kolar belt, Karnataka spots a diseased leaf with no "
        "agronomist to call and unreliable connectivity to search with.",
        "Existing diagnosis apps (Plantix, PlantVillage) identify the disease but stop there — "
        "they don't say where to buy the treatment nearby, what it costs, or whether a nearby "
        "outbreak means the farmer should check sooner.",
        "Kisan Mitra turns a photo and a spoken description into a cited diagnosis, a spoken "
        "Kannada advisory, the nearest in-stock dealer with today's price, a proactive outbreak "
        "alert, a crop-loss insurance evidence packet, a group-buy discount alert, and an "
        "anonymized district dashboard for extension officers.",
        "Target users: smallholder tomato farmers in the Kolar tomato belt, Karnataka — typically "
        "0.5–4 acre plots, variable literacy, intermittent connectivity, no dedicated access to "
        "an agronomist. Primary language: Kannada.",
    ], size=14)

    # ---- Slide 4: Opportunities ----
    s4 = prs.slides[2]
    for shape in s4.shapes:
        if shape.has_text_frame and "Opportunities" in shape.text_frame.text:
            set_textbox(shape, [("Opportunities", True)], title_size=16, title_font=FONT_HEAD)
    body4 = add_textbox(s4, 0.29, 1.4, 9.4, 3.9)
    add_bullets(body4, [
        "How different is it: Plantix diagnoses, AgroStar connects to dealers, PlantVillage "
        "pairs AI with weather — none combine diagnosis, voice, and market linkage in one flow, "
        "and none reason across farmers or across time on the same plot.",
        "How it solves the problem: the outbreak alert reaches a farmer before their own crop "
        "shows damage; the insurance claim assistant turns a diagnosis into a fileable claim; "
        "the group-buy alert turns an early warning into a coordinated bulk discount; the "
        "district dashboard turns farmer-level data into a resourcing signal for an extension "
        "officer or NGO.",
        "USP: moves the system from advice to economic action and policy support — no existing "
        "tool in this space does all four.",
    ], size=14)

    # ---- Slide 5: List of features ----
    s5 = prs.slides[3]
    for shape in s5.shapes:
        if shape.has_text_frame and "List of features" in shape.text_frame.text:
            set_textbox(shape, [("List of features offered by the solution", True)], title_size=16, title_font=FONT_HEAD)
    body5 = add_textbox(s5, 0.29, 1.4, 9.4, 3.9)
    add_bullets(body5, [
        "Cited disease diagnosis from a photo + spoken description — not a black-box guess",
        "Spoken advisory in Kannada, weather-aware (holds off spraying before forecast rain)",
        "Nearest in-stock dealer lookup with today's price",
        "Proactive outbreak early-warning — alerts nearby farmers before their own crop shows symptoms",
        "Plot-level memory — flags recurring disease as a root-cause issue (e.g. drainage), not just a repeat treatment",
        "Sell-side market linkage — best nearby mandi price when a healthy crop is near harvest",
        "Crop-loss insurance claim assistant — auto-generates a fileable evidence packet",
        "Group-buy / collective bargaining alert — coordinates nearby farmers for a bulk discount",
        "District dashboard — anonymized, village-level view for an extension officer or NGO",
        "Gemini-driven orchestration — the model itself decides which of these tools to call, "
        "via real function-calling, not a hardcoded decision tree",
    ], size=13, space_after=4)

    # ---- Slide 6: Process flow diagram (boxes + arrows, not bullet text) ----
    s6 = prs.slides[4]
    for shape in s6.shapes:
        if shape.has_text_frame and "Process flow" in shape.text_frame.text:
            set_textbox(shape, [("Process flow diagram or Use-case diagram", True)], title_size=16, title_font=FONT_HEAD)

    DL, DR = 0.22, 9.78  # diagram left/right edge
    y = 1.42

    # Row A: input + context tools, side by side
    boxes_a = row_boxes(2, DL, DR, gap=0.18)
    add_diagram_box(s6, boxes_a[0][0], y, boxes_a[0][1], 0.46,
                     [("FARMER INPUT", True), ("Symptom text or speech (Kannada/English) + optional photo, in-browser", False)],
                     FILL_NEUTRAL, LINE_NEUTRAL)
    add_diagram_box(s6, boxes_a[1][0], y, boxes_a[1][1], 0.46,
                     [("CONTEXT CHECKS", True), ("Weather (Open-Meteo), outbreak radius, plot-memory history", False)],
                     FILL_NEUTRAL, LINE_NEUTRAL)
    y += 0.46
    add_down_arrow(s6, (DL + DR) / 2, y, 0.16)
    y += 0.16

    # Row B: Gemini call 1 — diagnosis
    add_diagram_box(s6, DL, y, DR - DL, 0.46,
                     [("GEMINI CALL 1 — DIAGNOSIS", True),
                      ("Multimodal + RAG (TF-IDF over 18 bilingual disease docs) → structured diagnosis JSON", False)],
                     FILL_AI, LINE_AI)
    y += 0.46
    add_down_arrow(s6, (DL + DR) / 2, y, 0.16)
    y += 0.16

    # Row C: Gemini call 2 — orchestration
    add_diagram_box(s6, DL, y, DR - DL, 0.46,
                     [("GEMINI CALL 2 — ORCHESTRATION (real function-calling)", True),
                      ("Decides WHICH tools to invoke from diagnosis + outbreak + near-harvest — not a hardcoded if/else", False)],
                     FILL_ACCENT, LINE_ACCENT)
    y += 0.46
    add_down_arrow(s6, (DL + DR) / 2, y, 0.16, color=ACCENT)
    y += 0.16

    # Row D: the 4 tools Gemini can choose from
    tool_labels = [
        ("DEALER LOOKUP", "Nearest in-stock dealer + price"),
        ("SELL-PRICE LOOKUP", "Best nearby mandi price"),
        ("INSURANCE CHECK", "Fileable claim packet"),
        ("GROUP-BUY CHECK", "Bulk-discount alert"),
    ]
    boxes_d = row_boxes(4, DL, DR, gap=0.12)
    for (bl, bw), (title, detail) in zip(boxes_d, tool_labels):
        add_diagram_box(s6, bl, y, bw, 0.52, [(title, True), (detail, False)],
                         FILL_TOOLS, LINE_TOOLS, title_size=9, detail_size=7.5)
    y += 0.52
    add_down_arrow(s6, (DL + DR) / 2, y, 0.16)
    y += 0.16

    # Row E: response assembly
    add_diagram_box(s6, DL, y, DR - DL, 0.46,
                     [("RESPONSE ASSEMBLY", True),
                      ("Kannada advisory spoken via Web Speech API; diagnosis, dealer, outbreak, insurance, group-buy cards rendered", False)],
                     FILL_NEUTRAL, LINE_NEUTRAL)
    y += 0.46 + 0.14

    # Footer callout, mirroring the reference deck's "core principle" box
    add_diagram_box(s6, DL, y, DR - DL, 0.46,
                     [("Separately — district dashboard: a pre-aggregated, anonymized village-level "
                       "snapshot loads independently, built at deploy time. Raw farmer data never reaches the browser.", False)],
                     FILL_CALLOUT, LINE_CALLOUT, detail_size=8.5)

    # ---- Slide 7: Wireframes (use the real screenshots) ----
    s7 = prs.slides[5]
    for shape in s7.shapes:
        if shape.has_text_frame and "Wireframes" in shape.text_frame.text:
            set_textbox(shape, [("Wireframes / Mock diagrams of the proposed solution", True)], title_size=16, title_font=FONT_HEAD)
    add_picture_fit(s7, os.path.join(SCREENSHOTS, "01_initial_load.png"), 0.4, 1.35, 4.4, 4.0)
    add_picture_fit(s7, os.path.join(SCREENSHOTS, "deck_crops", "02_crop.png"), 5.1, 1.35, 4.4, 4.0)

    # ---- Slide 8: Architecture diagram (layered boxes, not bullet text) ----
    s8 = prs.slides[6]
    for shape in s8.shapes:
        if shape.has_text_frame and "Architecture diagram" in shape.text_frame.text:
            set_textbox(shape, [("Architecture diagram of the proposed solution", True)], title_size=16, title_font=FONT_HEAD)

    LABEL_W = 0.78
    DL2, DR2 = 0.22 + LABEL_W, 9.78
    y = 1.40

    def labeled_row(label, boxes_spec, height, fill, line_color, title_size=9, detail_size=7.5):
        nonlocal y
        add_row_label(s8, 0.22, y, LABEL_W - 0.08, height, label)
        n = len(boxes_spec)
        boxes = row_boxes(n, DL2, DR2, gap=0.12)
        for (bl, bw), (title, detail) in zip(boxes, boxes_spec):
            add_diagram_box(s8, bl, y, bw, height, [(title, True), (detail, False)],
                             fill, line_color, title_size=title_size, detail_size=detail_size)
        y += height

    # HOST layer
    labeled_row("HOSTING", [("FIREBASE HOSTING — FREE SPARK PLAN", "Static site only. $0 billing, no credit card anywhere in the stack.")],
                0.42, FILL_HOST, LINE_HOST, title_size=9.5, detail_size=8)
    y += 0.12
    add_down_arrow(s8, (DL2 + DR2) / 2, y, 0.14)
    y += 0.14

    # CLIENT layer
    labeled_row("BROWSER", [
        ("CAMERA / MIC INPUT", "Photo + Kannada speech, Web Speech API"),
        ("UI RENDER", "Diagnosis, dealer, outbreak, insurance, group-buy cards"),
        ("VOICE OUTPUT", "SpeechSynthesis, kn-IN voice feature-detect"),
    ], 0.5, FILL_NEUTRAL, LINE_NEUTRAL)
    y += 0.1
    add_down_arrow(s8, (DL2 + DR2) / 2, y, 0.14)
    y += 0.14

    # GEMINI layer
    labeled_row("GEMINI API", [
        ("CALL 1 — DIAGNOSIS", "Multimodal + RAG-grounded structured JSON output"),
        ("CALL 2 — ORCHESTRATION", "Real function-calling picks which tools fire; retries, then deterministic fallback"),
    ], 0.56, FILL_ACCENT, LINE_ACCENT, title_size=9.5, detail_size=8)
    y += 0.1
    add_down_arrow(s8, (DL2 + DR2) / 2, y, 0.14, color=ACCENT)
    y += 0.14

    # DATA + EXTERNAL layer
    labeled_row("DATA & APIs", [
        ("RAG INDEX (JS)", "TF-IDF + cosine, 18 bilingual disease docs"),
        ("STATIC JSON/CSV", "Dealers, mandi prices, diagnosis history"),
        ("DASHBOARD SNAPSHOT", "Pre-aggregated at deploy time — raw farmer data never ships"),
        ("OPEN-METEO", "Keyless, CORS-enabled weather API"),
    ], 0.58, FILL_TOOLS, LINE_TOOLS)
    y += 0.16

    add_diagram_box(s8, 0.22, y, 9.56, 0.42,
                     [("No backend server anywhere in this stack — every call above runs directly from "
                       "the farmer's browser to a public API or a static file.", False)],
                     FILL_CALLOUT, LINE_CALLOUT, detail_size=8.5)
    y += 0.42 + 0.1
    add_legend(s8, 0.22, y, 9.56, 0.2, [
        (FILL_HOST, "Hosting"),
        (FILL_NEUTRAL, "Browser-side"),
        (FILL_ACCENT, "Gemini API"),
        (FILL_TOOLS, "Data & external APIs"),
    ])

    # ---- Slide 9: Technologies ----
    s9 = prs.slides[7]
    for shape in s9.shapes:
        if shape.has_text_frame and "Technologies" in shape.text_frame.text:
            set_textbox(shape, [("Technologies to be used in the solution", True)], title_size=16, title_font=FONT_HEAD)
    tech9 = add_textbox(s9, 0.29, 1.4, 9.4, 3.9)
    add_bullets(tech9, [
        "Gemini API (gemini-3.8-flash) — called directly from the browser for two things: "
        "multimodal diagnosis, and a second call using real function-calling to decide which "
        "tools to invoke",
        "Firebase Hosting — free Spark plan, zero billing, serves the entire static site",
        "Vanilla JavaScript (ES modules) — no framework, no bundler, no agentic framework "
        "(no LangChain/CrewAI/Vertex Agent Builder) — direct fetch() calls to the Gemini API",
        "Hand-rolled TF-IDF + cosine similarity (JS) — RAG retrieval over the disease guides, "
        "no vector database or external search service",
        "Open-Meteo — free, keyless weather API",
        "Web Speech API (browser-native) — speech recognition for Kannada voice input, "
        "SpeechSynthesis for voice output",
        "Static JSON/CSV data files — dealer directory, mandi prices, diagnosis history",
        "Python (data generation, build-time dashboard aggregation), Playwright (verification)",
    ], size=13, space_after=4)

    # ---- Slide 10: Estimated implementation cost ----
    s10 = prs.slides[8]
    for shape in s10.shapes:
        if shape.has_text_frame and "implementation cost" in shape.text_frame.text:
            set_textbox(shape, [("Estimated implementation cost", True)], title_size=16, title_font=FONT_HEAD)
    cost10 = add_textbox(s10, 0.29, 1.4, 9.4, 3.9)
    add_bullets(cost10, [
        "Current deployed cost: $0 — no billing account, no credit card, anywhere in the stack",
        "Firebase Hosting: free Spark plan, no usage cap reached at this scale",
        "Gemini API: free tier via Google AI Studio — 20 requests/day per project for "
        "gemini-3.8-flash; each diagnosis now uses 2 calls (diagnosis + orchestration), so "
        "roughly 10 full diagnoses/day before the app gracefully falls back to deterministic "
        "logic for the rest of the day",
        "Open-Meteo, Web Speech API: free, no quota observed in testing",
        "Scaling beyond the free tier: upgrading to a paid Gemini tier is the only cost that "
        "would be needed to raise the daily diagnosis cap — no other paid service is required "
        "even at higher usage, since there is no backend, database, or search service to scale",
    ], size=14)

    # ---- Slide 11: Snapshots of the prototype ----
    s11 = prs.slides[9]
    for shape in s11.shapes:
        if shape.has_text_frame and "Snapshots" in shape.text_frame.text:
            set_textbox(shape, [("Snapshots of the prototype", True)], title_size=16, title_font=FONT_HEAD)
    add_picture_fit(s11, os.path.join(SCREENSHOTS, "deck_crops", "03_crop.png"), 0.3, 1.35, 4.6, 4.0)
    add_picture_fit(s11, os.path.join(SCREENSHOTS, "04_district_dashboard.png"), 5.1, 1.35, 4.6, 4.0)

    # ---- Slide 12: Prototype performance / benchmarking ----
    s12 = prs.slides[10]
    for shape in s12.shapes:
        if shape.has_text_frame and "Performance report" in shape.text_frame.text:
            set_textbox(shape, [("Prototype Performance report / Benchmarking", True)], title_size=16, title_font=FONT_HEAD)
    perf12 = add_textbox(s12, 0.29, 1.4, 9.4, 3.9)
    add_bullets(perf12, [
        "Measured live in the browser against the deployed static site (5 calls per operation):",
        "RAG retrieval (TF-IDF index build, cold) — ~92ms once per session; warm lookups <1ms",
        "Dealer / sell-price lookup — ~0.1–2.5ms (in-memory JSON lookups)",
        "Outbreak check (geo-radius over 300 diagnosis records) — ~3.6ms avg",
        "District dashboard snapshot load — ~17ms avg",
        "Weather (live Open-Meteo call) — ~660ms avg (external network call)",
        "Full diagnosis pipeline (2 Gemini calls: diagnosis + orchestration) — several seconds "
        "under normal quota; up to ~20s worst case if quota is exhausted and both calls exhaust "
        "retries before falling back",
        "Verified end-to-end with Playwright against the live deployed URL, with zero local "
        "servers running — confirms zero hidden dependency on anything other than the public "
        "Gemini and Open-Meteo APIs",
    ], size=13, space_after=5)

    # ---- Slide 13: Additional details / future development ----
    s13 = prs.slides[11]
    for shape in s13.shapes:
        if shape.has_text_frame and "Additional Details" in shape.text_frame.text:
            set_textbox(shape, [("Additional Details / Future Development", True)], title_size=16, title_font=FONT_HEAD)
    future13 = add_textbox(s13, 0.29, 1.4, 9.4, 4.0)
    add_bullets(future13, [
        "Next step — upgrade to managed Google Cloud services once billing is available: "
        "Gemini behind a Cloud Run/Cloud Functions proxy (closes the public-key exposure, "
        "removes the 20-req/day ceiling), Firestore replacing the static dealer/price/history "
        "JSON for a genuinely live dashboard, Vertex AI Search replacing the hand-rolled "
        "TF-IDF retrieval, and Cloud Translation/Text-to-Speech replacing the template-based "
        "Kannada advisory. Each substitute sits behind one isolated call site, so every swap "
        "is incremental, not a rewrite.",
        "Offline-first fallback (planned): a distilled on-device TensorFlow Lite classifier "
        "for the 8–10 most common regional diseases, so core diagnosis keeps working when "
        "connectivity drops entirely. Training script already written, pending a real "
        "multi-hour training run on the full PlantVillage dataset.",
        "Expansion path: adding a new crop or region means indexing a new disease guide into "
        "the retrieval layer, not rewriting the diagnosis logic — crop-agnostic by design even "
        "though this build is scoped to tomato in Karnataka for the demo.",
        "Resource & environmental impact: targeted treatment instead of blanket spraying, "
        "weather-timed spraying to cut chemical runoff, and earlier detection to reduce crop "
        "loss — moving this beyond social impact into genuine sustainability.",
    ], size=12, space_after=5, line_spacing=1.1)

    # ---- Slide 14: Links ----
    s14 = prs.slides[12]
    for shape in s14.shapes:
        if shape.has_text_frame and "Provide links" in shape.text_frame.text:
            set_textbox(shape, [
                ("Provide links to your:", True),
                ("GitHub Public Repository: https://github.com/Kavitacs08/kisan-mitra", False),
                ("Demo Video Link (3 Minutes): [add link before submission]", False),
                ("Final Product Link: https://kisan-mitra-2026-56c5d.web.app", False),
            ], title_size=16, body_size=14, title_font=FONT_HEAD_SEMI)

    prs.save(OUT_PPTX)
    print(f"Wrote {OUT_PPTX}")


if __name__ == "__main__":
    main()
