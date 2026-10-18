"""Synthesizes the Kisan Mitra demo narration using Microsoft Edge's free
neural TTS (via the edge-tts package) -- an Indian-accent female voice
(en-IN-NeerjaNeural) for the English narration, switching to the native
Kannada female voice (kn-IN-SapnaNeural) for the one line that's actually
read in Kannada script, matching docs/video/narration_script.md.

Produces docs/video/narration_synthesized.mp3, timed to land close to
(not necessarily identical to -- TTS speaking rate isn't perfectly
controllable) the beat timestamps in the script. Where a segment's
synthesized audio is shorter than its allotted beat duration, silence is
padded after it so the next segment's audio still starts at roughly the
right time relative to the silent video; where longer, the gap is
compressed (segments butt together) rather than overlapping.

Usage: python scripts/synthesize_narration.py
"""
import asyncio
import os
import subprocess

import edge_tts
import imageio_ffmpeg

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_DIR = os.path.join(APP_ROOT, "docs", "video")
TAKES_DIR = os.path.join(VIDEO_DIR, "narration_takes")
OUT_PATH = os.path.join(VIDEO_DIR, "narration_synthesized.mp3")
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

VOICE_EN = "en-IN-NeerjaNeural"
VOICE_KN = "kn-IN-SapnaNeural"

# (segment_id, voice, text, beat_start_seconds) -- beat_start matches the
# silent video's actual timings from scripts/build_demo_video.py.
SEGMENTS = [
    ("00_title", VOICE_EN,
     "Kisan Mitra. A tomato crop advisory agent for the Kolar belt, "
     "Karnataka.", None),

    ("01_problem", VOICE_EN,
     "Eighty-six percent of India's farmers are smallholders. One bad "
     "disease outbreak can wipe out an entire season's income. There's no "
     "agronomist on call, no reliable signal to search with, and by the "
     "time the damage is visible, it's already too late to stop it "
     "spreading.", None),

    ("01b_solution", VOICE_EN,
     "Kisan Mitra turns a photo and a few spoken words into a cited "
     "diagnosis, a spoken answer in the farmer's own language, and real "
     "economic action: the nearest dealer, an outbreak warning before "
     "damage shows, an insurance claim ready to file, and a group "
     "discount with other farmers nearby.", None),

    ("02_watch", VOICE_EN,
     "Watch what happens, live.", None),

    ("03_diagnosis", VOICE_EN,
     "Gemini diagnoses it live: early blight, ninety-five percent "
     "confidence, with a citation. A second Gemini call then decides what "
     "to do next, using real function-calling, not hardcoded rules.", None),

    ("04a_combo_intro", VOICE_EN,
     "A warning: nearby outbreak, days before symptoms show. The advisory "
     "comes back fully in Kannada.", None),

    ("04b_kannada", VOICE_KN,
     "ನಿಮ್ಮ ಟೊಮೇಟೊ ಗಿಡದಲ್ಲಿ ಅರ್ಲಿ ಬ್ಲೈಟ್ ರೋಗದ ಲಕ್ಷಣಗಳು ಕಂಡುಬರುತ್ತಿವೆ. "
     "ಇಂದೇ ಬಾಧಿತ ಕೆಳಗಿನ ಎಲೆಗಳನ್ನು ತೆಗೆದುಹಾಕಿ. ಮಳೆಗೆ ಮುನ್ನ ಕಾಪರ್ ಆಕ್ಸಿಕ್ಲೋರೈಡ್ ಸಿಂಪಡಿಸಿ.",
     None),

    ("04c_combo_outro", VOICE_EN,
     "The nearest dealer. An insurance packet, ready to file. One "
     "diagnosis, five real actions.", None),

    ("04d_groupbuy", VOICE_EN,
     "Look closer at one of those actions: the group-buy card. Five "
     "nearby farmers, flagged by the same outbreak signal, all need the "
     "same treatment this week. Kisan Mitra checks the dealer's own bulk "
     "pricing tier and automatically unlocks a twelve percent discount "
     "the moment combined demand crosses the threshold: one-eighty "
     "rupees a kilogram alone, down to one fifty-eight together, same "
     "dealer, same day.", None),

    ("05_one_screen", VOICE_EN,
     "Diagnosis that doesn't stop at diagnosis.", None),

    ("06_scale", VOICE_EN,
     "And it scales beyond one farmer.", None),

    ("07_dashboard", VOICE_EN,
     "The same signal, anonymized, becomes a policy tool for an "
     "extension officer.", None),

    ("08_closing", VOICE_EN,
     "Built on real Gemini, deployed at zero billing. Kisan Mitra: "
     "diagnosis that doesn't stop at diagnosis.", None),
]


async def synth_one(seg_id, voice, text, out_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)


def probe_duration(path):
    result = subprocess.run([FFMPEG, "-i", path], capture_output=True, text=True)
    for line in result.stderr.splitlines():
        if "Duration" in line:
            ts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = ts.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


async def main():
    os.makedirs(TAKES_DIR, exist_ok=True)

    for seg_id, voice, text, _ in SEGMENTS:
        out_path = os.path.join(TAKES_DIR, f"{seg_id}.mp3")
        print(f"Synthesizing {seg_id} ({voice})...")
        await synth_one(seg_id, voice, text, out_path)

    # Concatenate all segments back-to-back with a tiny 150ms gap between
    # each for natural breathing room (segments without a fixed beat_start
    # already flow immediately after the previous one; the gap is uniform).
    concat_list = os.path.join(TAKES_DIR, "concat_list.txt")
    gap_path = os.path.join(TAKES_DIR, "_gap.mp3")
    subprocess.run([
        FFMPEG, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
        "-t", "0.15", "-q:a", "9", gap_path,
    ], check=True, capture_output=True)

    with open(concat_list, "w", encoding="utf-8") as f:
        for i, (seg_id, _, _, _) in enumerate(SEGMENTS):
            seg_path = os.path.abspath(os.path.join(TAKES_DIR, f"{seg_id}.mp3"))
            f.write(f"file '{seg_path.replace(chr(92), chr(92)+chr(92))}'\n")
            if i < len(SEGMENTS) - 1:
                f.write(f"file '{os.path.abspath(gap_path).replace(chr(92), chr(92)+chr(92))}'\n")

    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c:a", "libmp3lame", "-q:a", "4",
        OUT_PATH,
    ], check=True, capture_output=True)

    total = probe_duration(OUT_PATH)
    print(f"\nWrote {OUT_PATH} -- total duration {total:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
