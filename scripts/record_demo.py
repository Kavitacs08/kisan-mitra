"""Records the live Kisan Mitra app for the hackathon demo video, using
Playwright's own video recording (not screen-capture software) for exact,
repeatable pacing. Produces one raw .webm clip per beat under
docs/video/raw/, matched to the timings in docs/video/narration_script.md.

Run this against a key with live Gemini quota (see the plan: a temporary
test key swapped into frontend/js/config.js for this recording session
only -- never committed, never deployed). Restore the real config.js with
scripts/generate_config.py immediately after recording.

Usage:
    cd frontend && python -m http.server 8732   # in one terminal
    python scripts/record_demo.py               # in another
"""
import os
import shutil
import sys

from playwright.sync_api import sync_playwright

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(APP_ROOT, "docs", "video", "raw")
URL = "http://127.0.0.1:8732/index.html"
DASHBOARD_URL = "http://127.0.0.1:8732/dashboard.html"

VIDEO_SIZE = {"width": 1280, "height": 960}  # matches viewport below


def record_main_app():
    """Beat 2-4: load -> diagnose -> hold on the full combo result."""
    out_dir = os.path.join(RAW_DIR, "beat_app")
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport=VIDEO_SIZE,
            record_video_dir=out_dir,
            record_video_size=VIDEO_SIZE,
        )
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        page.goto(URL)
        page.wait_for_selector("#symptomInput")
        page.wait_for_timeout(2500)  # hold on empty form -- narration Beat 2 opening

        # Symptom text is already pre-filled in the HTML; just show it, then click.
        page.wait_for_timeout(1500)
        page.click("#diagnoseBtn")

        try:
            page.wait_for_selector("#resultCard:not(.hidden)", timeout=30000)
        except Exception as e:
            print(f"FAILED waiting for result card: {e}")
            print("Console errors:", console_errors)
            context.close()
            browser.close()
            sys.exit(1)

        page.wait_for_timeout(800)  # let outbreak banner / other cards settle

        # Hold on the diagnosis + citation + "(via Gemini)" label -- Beat 2/3.
        source_text = page.inner_text("#citedSource")
        print("citedSource text:", source_text)
        if "fallback" in source_text.lower():
            print("WARNING: result used fallback, not live Gemini. Check the swapped-in test key's quota.")
        page.wait_for_timeout(4000)

        # Scroll slowly down through dealer / insurance / group-buy cards -- Beat 4.
        for frac in [0.25, 0.5, 0.75, 1.0]:
            page.evaluate(f"window.scrollTo({{top: document.body.scrollHeight * {frac}, behavior: 'smooth'}})")
            page.wait_for_timeout(2200)

        page.wait_for_timeout(1500)
        context.close()
        browser.close()

    # Playwright names the file automatically; find and report it.
    files = [f for f in os.listdir(out_dir) if f.endswith(".webm")]
    print(f"Recorded: {os.path.join(out_dir, files[0]) if files else '(none found!)'}")


def record_dashboard():
    """Beat 5: district dashboard, extension-officer view."""
    out_dir = os.path.join(RAW_DIR, "beat_dashboard")
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport=VIDEO_SIZE,
            record_video_dir=out_dir,
            record_video_size=VIDEO_SIZE,
        )
        page = context.new_page()
        page.goto(DASHBOARD_URL)
        try:
            page.wait_for_selector("#dashboardContent:not(.hidden)", timeout=8000)
        except Exception as e:
            print(f"FAILED waiting for dashboard: {e}")
            context.close()
            browser.close()
            sys.exit(1)
        page.wait_for_timeout(1500)
        for frac in [0.3, 0.6, 1.0]:
            page.evaluate(f"window.scrollTo({{top: document.body.scrollHeight * {frac}, behavior: 'smooth'}})")
            page.wait_for_timeout(2000)
        page.wait_for_timeout(1500)
        context.close()
        browser.close()

    files = [f for f in os.listdir(out_dir) if f.endswith(".webm")]
    print(f"Recorded: {os.path.join(out_dir, files[0]) if files else '(none found!)'}")


if __name__ == "__main__":
    os.makedirs(RAW_DIR, exist_ok=True)
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "app"):
        record_main_app()
    if which in ("all", "dashboard"):
        record_dashboard()
