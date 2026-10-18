"""One-off Playwright driver: verify the 3 new features (insurance claim,
group-buy alert, district dashboard) render correctly in a real browser.
"""
import os
import sys

from playwright.sync_api import sync_playwright

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "screenshots")
os.makedirs(OUT_DIR, exist_ok=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # --- Page 1: main app, insurance claim + group-buy cards ---
        page = browser.new_page(viewport={"width": 480, "height": 1400})
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))

        page.goto("http://127.0.0.1:8732/index.html")
        page.wait_for_selector("#symptomInput")
        page.click("#diagnoseBtn")

        try:
            page.wait_for_selector("#resultCard:not(.hidden)", timeout=8000)
        except Exception as e:
            print(f"FAILED on main app: {e}")
            print(console_errors)
            sys.exit(1)

        page.wait_for_timeout(600)
        claim_visible = page.is_visible("#claimCard") and "hidden" not in (page.get_attribute("#claimCard", "class") or "")
        groupbuy_visible = page.is_visible("#groupBuyCard") and "hidden" not in (page.get_attribute("#groupBuyCard", "class") or "")
        print(f"Insurance claim card visible: {claim_visible}")
        print(f"Group-buy card visible: {groupbuy_visible}")

        if claim_visible:
            print(" Claim ID:", page.inner_text("#claimId"))
            print(" Severity:", page.inner_text("#claimSeverity"))
        if groupbuy_visible:
            print(" Group-buy note:", page.inner_text("#groupBuyNote"))
            print(" Bulk price:", page.inner_text("#groupBuyBulkPrice"))

        page.screenshot(path=os.path.join(OUT_DIR, "03_new_features_main_app.png"), full_page=True)
        print("Captured: main app with new feature cards\n")

        if console_errors:
            print("Console errors on main app:", console_errors)
        page.close()

        # --- Page 2: district dashboard ---
        page2 = browser.new_page(viewport={"width": 760, "height": 900})
        console_errors2 = []
        page2.on("console", lambda msg: console_errors2.append(msg.text) if msg.type == "error" else None)
        page2.on("pageerror", lambda exc: console_errors2.append(str(exc)))

        page2.goto("http://127.0.0.1:8732/dashboard.html")
        try:
            page2.wait_for_selector("#dashboardContent:not(.hidden)", timeout=8000)
        except Exception as e:
            print(f"FAILED on dashboard: {e}")
            print(console_errors2)
            sys.exit(1)

        page2.wait_for_timeout(300)
        print("Total reports:", page2.inner_text("#totalReports"))
        print("Plots monitored:", page2.inner_text("#plotsMonitored"))
        print("Cluster count:", page2.inner_text("#clusterCount"))
        print("Most requested treatment:", page2.inner_text("#mostRequested"))

        page2.screenshot(path=os.path.join(OUT_DIR, "04_district_dashboard.png"), full_page=True)
        print("Captured: district dashboard")

        if console_errors2:
            print("Console errors on dashboard:", console_errors2)
        else:
            print("No console errors on dashboard.")

        browser.close()


if __name__ == "__main__":
    main()
