"""Assembles the Kisan Mitra demo video from the Playwright-recorded raw
clips (docs/video/raw/) and the HTML title/beat/closing cards
(docs/video/cards/), producing a SILENT assembly at
docs/video/Kisan_Mitra_Demo_silent.mp4. The user records their own
narration against this (or separately, using docs/video/narration_script.md)
and we mux it in afterward with mux_narration.py.

Usage: python scripts/build_demo_video.py
"""
import os
import subprocess

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_DIR = os.path.join(APP_ROOT, "docs", "video")
RAW_DIR = os.path.join(VIDEO_DIR, "raw")
CARDS_DIR = os.path.join(VIDEO_DIR, "cards")
RENDERED_DIR = os.path.join(VIDEO_DIR, "rendered")
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

SIZE = {"width": 1280, "height": 960}


def render_card_png(html_path, out_png, replacements=None):
    html = ""
    if replacements:
        with open(html_path, encoding="utf-8") as f:
            html = f.read()
        for k, v in replacements.items():
            html = html.replace(k, v)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=SIZE)
        if replacements:
            tmp_path = out_png + ".tmp.html"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(html)
            page.goto("file://" + tmp_path.replace("\\", "/"))
        else:
            page.goto("file://" + html_path.replace("\\", "/"))
        page.wait_for_timeout(400)  # let web font load
        page.screenshot(path=out_png)
        browser.close()
        if replacements:
            os.remove(tmp_path)


def png_to_clip(png_path, out_mp4, seconds):
    subprocess.run([
        FFMPEG, "-y", "-loop", "1", "-i", png_path, "-t", str(seconds),
        "-vf", f"scale={SIZE['width']}:{SIZE['height']}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
        out_mp4,
    ], check=True, capture_output=True)


def webm_to_mp4(webm_path, out_mp4):
    subprocess.run([
        FFMPEG, "-y", "-i", webm_path,
        "-vf", f"scale={SIZE['width']}:{SIZE['height']}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
        out_mp4,
    ], check=True, capture_output=True)


def trim_clip(in_mp4, out_mp4, start, duration):
    subprocess.run([
        FFMPEG, "-y", "-i", in_mp4, "-ss", str(start), "-t", str(duration),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
        out_mp4,
    ], check=True, capture_output=True)


def concat_clips(clip_paths, out_mp4):
    list_path = os.path.join(RENDERED_DIR, "concat_list.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for c in clip_paths:
            f.write(f"file '{os.path.abspath(c).replace(chr(39), chr(92)+chr(39))}'\n")
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", list_path,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
        out_mp4,
    ], check=True, capture_output=True)


def main():
    os.makedirs(RENDERED_DIR, exist_ok=True)

    # ---- 1. Render HTML cards to PNG, then to short static-hold clips ----
    beats = [
        ("1", "The problem", "A smallholder tomato farmer near Kolar, one bar of signal, no agronomist to call."),
        ("2 / 3", "Live diagnosis, cited — and the orchestration behind it", "Gemini diagnoses with a citation, then a second Gemini call decides which tools to invoke."),
        ("4", "One screen, five actions", "Outbreak alert, dealer, insurance packet — diagnosis that doesn't stop at diagnosis."),
        ("5", "Scale: the district view", "The same signal, aggregated and anonymized, for an extension officer."),
    ]

    title_png = os.path.join(RENDERED_DIR, "title.png")
    render_card_png(os.path.join(CARDS_DIR, "title.html"), title_png)
    png_to_clip(title_png, os.path.join(RENDERED_DIR, "c_title.mp4"), 5)

    for i, (num, headline, sub) in enumerate(beats):
        png = os.path.join(RENDERED_DIR, f"beat_{i}.png")
        render_card_png(
            os.path.join(CARDS_DIR, "beat_label.html"), png,
            replacements={"__NUM__": f"BEAT {num}", "__HEADLINE__": headline, "__SUB__": sub},
        )
        png_to_clip(png, os.path.join(RENDERED_DIR, f"c_beat_{i}.mp4"), 3)

    closing_png = os.path.join(RENDERED_DIR, "closing.png")
    render_card_png(os.path.join(CARDS_DIR, "closing.html"), closing_png)
    png_to_clip(closing_png, os.path.join(RENDERED_DIR, "c_closing.mp4"), 6)

    # ---- 2. Convert the raw Playwright .webm recordings to mp4 ----
    app_webm = [f for f in os.listdir(os.path.join(RAW_DIR, "beat_app")) if f.endswith(".webm")][0]
    dash_webm = [f for f in os.listdir(os.path.join(RAW_DIR, "beat_dashboard")) if f.endswith(".webm")][0]
    app_mp4_full = os.path.join(RENDERED_DIR, "app_full.mp4")
    dash_mp4_full = os.path.join(RENDERED_DIR, "dash_full.mp4")
    webm_to_mp4(os.path.join(RAW_DIR, "beat_app", app_webm), app_mp4_full)
    webm_to_mp4(os.path.join(RAW_DIR, "beat_dashboard", dash_webm), dash_mp4_full)

    # app_full.mp4 is ~30s: 0-4s empty form, 4-5.5s loading, 5.5-30s result +
    # scroll. Split into "diagnosis moment" (0-14s) and "combo scroll" (14-30s)
    # so we can insert the orchestration beat card between them.
    app_diag = os.path.join(RENDERED_DIR, "app_diag.mp4")
    app_combo = os.path.join(RENDERED_DIR, "app_combo.mp4")
    trim_clip(app_mp4_full, app_diag, 0, 14)
    trim_clip(app_mp4_full, app_combo, 14, 16)

    # ---- 3. Concatenate the full sequence ----
    sequence = [
        os.path.join(RENDERED_DIR, "c_title.mp4"),
        os.path.join(RENDERED_DIR, "c_beat_0.mp4"),
        os.path.join(RENDERED_DIR, "c_beat_1.mp4"),
        app_diag,
        app_combo,
        os.path.join(RENDERED_DIR, "c_beat_2.mp4"),
        # app_combo already shown above right after diagnosis; re-show the
        # tail of it isn't needed, combo card leads into dashboard instead.
        os.path.join(RENDERED_DIR, "c_beat_3.mp4"),
        dash_mp4_full,
        os.path.join(RENDERED_DIR, "c_closing.mp4"),
    ]
    out_path = os.path.join(VIDEO_DIR, "Kisan_Mitra_Demo_silent.mp4")
    concat_clips(sequence, out_path)
    print(f"Wrote {out_path}")

    # Report total duration
    probe = subprocess.run([FFMPEG, "-i", out_path], capture_output=True, text=True)
    for line in probe.stderr.splitlines():
        if "Duration" in line:
            print(line.strip())


if __name__ == "__main__":
    main()
