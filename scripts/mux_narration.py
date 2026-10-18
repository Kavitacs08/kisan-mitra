"""Muxes a recorded narration audio file onto the silent demo video
assembly, producing the final docs/video/Kisan_Mitra_Demo.mp4.

Usage:
    python scripts/mux_narration.py path/to/your_narration.mp3

If the narration is shorter than the 62.4s silent video, the video is
trimmed to match (so it doesn't run on in silence after narration ends).
If the narration is longer, the last video frame is held to cover the gap
rather than cutting the narration off.
"""
import os
import subprocess
import sys

import imageio_ffmpeg

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_DIR = os.path.join(APP_ROOT, "docs", "video")
SILENT_PATH = os.path.join(VIDEO_DIR, "Kisan_Mitra_Demo_silent.mp4")
OUT_PATH = os.path.join(VIDEO_DIR, "Kisan_Mitra_Demo.mp4")
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def probe_duration(path):
    result = subprocess.run([FFMPEG, "-i", path], capture_output=True, text=True)
    for line in result.stderr.splitlines():
        if "Duration" in line:
            # "  Duration: 00:01:02.40, start: ..."
            ts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = ts.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise RuntimeError(f"Could not read duration of {path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/mux_narration.py path/to/narration_audio_file")
        sys.exit(1)
    audio_path = sys.argv[1]
    if not os.path.exists(audio_path):
        print(f"File not found: {audio_path}")
        sys.exit(1)
    if not os.path.exists(SILENT_PATH):
        print(f"Silent assembly not found at {SILENT_PATH} -- run scripts/build_demo_video.py first.")
        sys.exit(1)

    video_dur = probe_duration(SILENT_PATH)
    audio_dur = probe_duration(audio_path)
    print(f"Silent video: {video_dur:.1f}s, narration: {audio_dur:.1f}s")

    if audio_dur <= video_dur:
        # Trim video to match narration length (avoid trailing silence).
        subprocess.run([
            FFMPEG, "-y", "-i", SILENT_PATH, "-i", audio_path,
            "-t", str(audio_dur),
            "-c:v", "copy", "-c:a", "aac", "-shortest",
            OUT_PATH,
        ], check=True)
    else:
        # Freeze the last video frame to cover the extra narration time.
        extra = audio_dur - video_dur
        subprocess.run([
            FFMPEG, "-y", "-i", SILENT_PATH,
            "-vf", f"tpad=stop_mode=clone:stop_duration={extra}",
            "-i", audio_path,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-shortest",
            OUT_PATH,
        ], check=True)

    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
