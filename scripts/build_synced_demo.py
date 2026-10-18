"""Builds the final Kisan Mitra demo video with the synthesized narration
(scripts/synthesize_narration.py) already timed per-segment -- this script
reads each segment's actual synthesized duration and sizes every matching
video clip/card hold to it exactly, so narration and visuals land in sync
without guesswork. Produces docs/video/Kisan_Mitra_Demo.mp4 directly
(video + muxed audio), not just the silent assembly.

Run scripts/synthesize_narration.py first.
Usage: python scripts/build_synced_demo.py
"""
import os
import subprocess

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_DIR = os.path.join(APP_ROOT, "docs", "video")
RAW_DIR = os.path.join(VIDEO_DIR, "raw")
CARDS_DIR = os.path.join(VIDEO_DIR, "cards")
RENDERED_DIR = os.path.join(VIDEO_DIR, "rendered_synced")
TAKES_DIR = os.path.join(VIDEO_DIR, "narration_takes")
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

SIZE = {"width": 1280, "height": 960}
GAP = 0.15  # matches the gap baked into narration_synthesized.mp3


def probe_duration(path):
    result = subprocess.run([FFMPEG, "-i", path], capture_output=True, text=True)
    for line in result.stderr.splitlines():
        if "Duration" in line:
            ts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = ts.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise RuntimeError(f"Could not read duration of {path}")


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
        page.wait_for_timeout(400)
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


def webm_to_mp4_trimmed(webm_path, out_mp4, start, duration):
    subprocess.run([
        FFMPEG, "-y", "-i", webm_path, "-ss", str(start), "-t", str(duration),
        "-vf", f"scale={SIZE['width']}:{SIZE['height']}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
        out_mp4,
    ], check=True, capture_output=True)


def extend_with_freeze(in_mp4, out_mp4, target_duration):
    """Pads the clip with a frozen last frame until it reaches target_duration."""
    cur = probe_duration(in_mp4)
    extra = max(0.0, target_duration - cur)
    subprocess.run([
        FFMPEG, "-y", "-i", in_mp4,
        "-vf", f"tpad=stop_mode=clone:stop_duration={extra}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
        out_mp4,
    ], check=True, capture_output=True)


def concat_clips(clip_paths, out_mp4):
    list_path = os.path.join(RENDERED_DIR, "concat_list.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for c in clip_paths:
            f.write(f"file '{os.path.abspath(c).replace(chr(92), chr(92)+chr(92))}'\n")
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", list_path,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
        out_mp4,
    ], check=True, capture_output=True)


def main():
    os.makedirs(RENDERED_DIR, exist_ok=True)

    # ---- Read each narration segment's actual duration ----
    seg_ids = [
        "00_title", "01_problem", "01b_solution", "02_watch", "03_diagnosis",
        "04a_combo_intro", "04b_kannada", "04c_combo_outro", "04d_groupbuy",
        "05_one_screen", "06_scale", "07_dashboard", "08_closing",
    ]
    dur = {}
    for seg_id in seg_ids:
        path = os.path.join(TAKES_DIR, f"{seg_id}.mp3")
        dur[seg_id] = probe_duration(path)
        print(f"{seg_id}: {dur[seg_id]:.2f}s")

    # Video-segment duration = narration duration + trailing gap (every
    # segment has a gap after it except the very last).
    vdur = {sid: dur[sid] + GAP for sid in seg_ids}
    vdur["08_closing"] = dur["08_closing"]  # no trailing gap on the last one

    # ---- Title / beat / closing cards, held exactly as long as needed ----
    title_png = os.path.join(RENDERED_DIR, "title.png")
    render_card_png(os.path.join(CARDS_DIR, "title.html"), title_png)
    png_to_clip(title_png, os.path.join(RENDERED_DIR, "c_title.mp4"), vdur["00_title"])

    stat_block = (
        '<div class="stat-row">'
        '<div class="stat"><div class="stat-num">86%</div><div class="stat-label">of India\'s farmers<br>are smallholders</div></div>'
        '<div class="stat"><div class="stat-num">1</div><div class="stat-label">bar of signal.<br>Zero agronomists on call</div></div>'
        "</div>"
    )
    list_block = (
        '<div class="checklist">'
        '<div class="check-item"><div class="mark">&#10003;</div>Cited diagnosis, not a black-box guess</div>'
        '<div class="check-item"><div class="mark">&#10003;</div>Spoken answer, in the farmer\'s own language</div>'
        '<div class="check-item"><div class="mark">&#10003;</div>Nearest dealer, outbreak warning, insurance, group discount</div>'
        "</div>"
    )
    beat_specs = {
        "01_problem": ("The problem is enormous", "Smallholders have no agronomist, no reliable signal, and no warning before damage spreads.", stat_block, ""),
        "01b_solution": ("The solution: one photo, five real actions", "Not just a diagnosis app — an agent that acts on it.", "", list_block),
        "02_watch": ("Live diagnosis, cited — and the orchestration behind it", "Gemini diagnoses with a citation, then a second Gemini call decides which tools to invoke.", "", ""),
        "05_one_screen": ("One screen, five actions", "Outbreak alert, dealer, insurance packet — diagnosis that doesn't stop at diagnosis.", "", ""),
        "06_scale": ("Scale: the district view", "The same signal, aggregated and anonymized, for an extension officer.", "", ""),
    }
    for sid, (headline, sub, stat_html, list_html) in beat_specs.items():
        png = os.path.join(RENDERED_DIR, f"{sid}.png")
        render_card_png(
            os.path.join(CARDS_DIR, "beat_label.html"), png,
            replacements={"__HEADLINE__": headline, "__SUB__": sub, "__STAT_BLOCK__": stat_html, "__LIST_BLOCK__": list_html},
        )
        png_to_clip(png, os.path.join(RENDERED_DIR, f"c_{sid}.mp4"), vdur[sid])

    # ---- Group-buy explainer card: real screenshot + callouts ----
    groupbuy_img_path = os.path.abspath(os.path.join(VIDEO_DIR, "assets", "groupbuy_card_crop.png")).replace("\\", "/")
    groupbuy_png = os.path.join(RENDERED_DIR, "04d_groupbuy.png")
    render_card_png(
        os.path.join(CARDS_DIR, "groupbuy_explainer.html"), groupbuy_png,
        replacements={
            "__HEADLINE__": "The group-buy card, explained",
            "__SUB__": "Real screenshot from the deployed app — not a mockup.",
            "__IMG_PATH__": groupbuy_img_path,
        },
    )
    png_to_clip(groupbuy_png, os.path.join(RENDERED_DIR, "c_04d_groupbuy.mp4"), vdur["04d_groupbuy"])

    closing_png = os.path.join(RENDERED_DIR, "closing.png")
    render_card_png(os.path.join(CARDS_DIR, "closing.html"), closing_png)
    png_to_clip(closing_png, os.path.join(RENDERED_DIR, "c_08_closing.mp4"), vdur["08_closing"])

    # ---- App diagnosis clip: trim to exactly cover 03_diagnosis's duration ----
    app_webm = [f for f in os.listdir(os.path.join(RAW_DIR, "beat_app")) if f.endswith(".webm")][0]
    app_webm_path = os.path.join(RAW_DIR, "beat_app", app_webm)
    raw_app_duration = probe_duration(app_webm_path)

    diag_target = vdur["03_diagnosis"]
    webm_to_mp4_trimmed(app_webm_path, os.path.join(RENDERED_DIR, "app_diag.mp4"), 0, min(diag_target, raw_app_duration))
    if diag_target > raw_app_duration:
        extend_with_freeze(os.path.join(RENDERED_DIR, "app_diag.mp4"), os.path.join(RENDERED_DIR, "app_diag.mp4"), diag_target)

    # ---- App combo clip: covers 04a + 04b (Kannada) + 04c combined ----
    # (04d_groupbuy is its own screenshot-explainer card, not part of this live clip)
    combo_target = vdur["04a_combo_intro"] + vdur["04b_kannada"] + vdur["04c_combo_outro"]
    remaining_raw = max(0.0, raw_app_duration - diag_target)
    combo_raw_path = os.path.join(RENDERED_DIR, "app_combo_raw.mp4")
    if remaining_raw > 0.5:
        webm_to_mp4_trimmed(app_webm_path, combo_raw_path, diag_target, remaining_raw)
    else:
        # Fallback: hold on the last frame of app_diag instead.
        webm_to_mp4_trimmed(app_webm_path, combo_raw_path, max(0, raw_app_duration - 0.5), 0.5)
    app_combo_path = os.path.join(RENDERED_DIR, "app_combo.mp4")
    extend_with_freeze(combo_raw_path, app_combo_path, combo_target)

    # ---- Dashboard clip: trim to 07_dashboard's duration ----
    dash_webm = [f for f in os.listdir(os.path.join(RAW_DIR, "beat_dashboard")) if f.endswith(".webm")][0]
    dash_webm_path = os.path.join(RAW_DIR, "beat_dashboard", dash_webm)
    raw_dash_duration = probe_duration(dash_webm_path)
    dash_target = vdur["07_dashboard"]
    dash_path = os.path.join(RENDERED_DIR, "dash.mp4")
    webm_to_mp4_trimmed(dash_webm_path, dash_path, 0, min(dash_target, raw_dash_duration))
    if dash_target > raw_dash_duration:
        extend_with_freeze(dash_path, dash_path, dash_target)

    # ---- Concatenate the full video track ----
    sequence = [
        os.path.join(RENDERED_DIR, "c_title.mp4"),
        os.path.join(RENDERED_DIR, "c_01_problem.mp4"),
        os.path.join(RENDERED_DIR, "c_01b_solution.mp4"),
        os.path.join(RENDERED_DIR, "c_02_watch.mp4"),
        os.path.join(RENDERED_DIR, "app_diag.mp4"),
        app_combo_path,
        os.path.join(RENDERED_DIR, "c_04d_groupbuy.mp4"),
        os.path.join(RENDERED_DIR, "c_05_one_screen.mp4"),
        os.path.join(RENDERED_DIR, "c_06_scale.mp4"),
        dash_path,
        os.path.join(RENDERED_DIR, "c_08_closing.mp4"),
    ]
    video_only = os.path.join(RENDERED_DIR, "video_track.mp4")
    concat_clips(sequence, video_only)

    video_total = probe_duration(video_only)
    audio_path = os.path.join(VIDEO_DIR, "narration_synthesized.mp3")
    audio_total = probe_duration(audio_path)
    print(f"\nVideo track: {video_total:.2f}s, Narration: {audio_total:.2f}s")

    # ---- Mux video + narration ----
    out_path = os.path.join(VIDEO_DIR, "Kisan_Mitra_Demo.mp4")
    subprocess.run([
        FFMPEG, "-y", "-i", video_only, "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        out_path,
    ], check=True, capture_output=True)
    final_dur = probe_duration(out_path)
    print(f"Wrote {out_path} -- {final_dur:.1f}s")


if __name__ == "__main__":
    main()
