"""One-off Playwright driver: open the Kisan Mitra frontend, run a diagnosis,
screenshot the result. Not part of the app itself -- a verification script.
"""
import os
import sys

from playwright.sync_api import sync_playwright

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "screenshots")
os.makedirs(OUT_DIR, exist_ok=True)

URL = "http://127.0.0.1:8732/index.html"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 480, "height": 900})

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))

        page.goto(URL)
        page.wait_for_selector("#symptomInput")
        page.screenshot(path=os.path.join(OUT_DIR, "01_initial_load.png"))
        print("Captured: initial load")

        # The textarea already has a default value in the HTML; click Diagnose directly.
        page.click("#diagnoseBtn")

        try:
            page.wait_for_selector("#resultCard:not(.hidden)", timeout=8000)
        except Exception as e:
            page.screenshot(path=os.path.join(OUT_DIR, "02_error_state.png"))
            print(f"FAILED waiting for result card: {e}")
            print("Status text was:", page.inner_text("#status"))
            print("Console errors:", console_errors)
            browser.close()
            sys.exit(1)

        page.wait_for_timeout(500)  # let outbreak banner fetch resolve too
        page.screenshot(path=os.path.join(OUT_DIR, "02_diagnosis_result.png"), full_page=True)
        print("Captured: diagnosis result (full page)")

        disease = page.inner_text("#diseaseName")
        confidence = page.inner_text("#confidencePill")
        cited = page.inner_text("#citedSource")
        advisory_local = page.inner_text("#advisoryLocal")
        dealer_visible = page.is_visible("#dealerCard") and "hidden" not in (page.get_attribute("#dealerCard", "class") or "")
        outbreak_visible = page.is_visible("#outbreakBanner")

        print(f"\nDisease: {disease}")
        print(f"Confidence: {confidence}")
        print(f"Citation: {cited}")
        print(f"Kannada advisory: {advisory_local}")
        print(f"Dealer card visible: {dealer_visible}")
        print(f"Outbreak banner visible: {outbreak_visible}")

        if console_errors:
            print("\nBrowser console errors encountered:")
            for e in console_errors:
                print(" -", e)
        else:
            print("\nNo browser console errors.")

        browser.close()


if __name__ == "__main__":
    main()
