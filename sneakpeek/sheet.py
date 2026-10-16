#!/usr/bin/env python3
"""Contact sheet of a render, for a quick visual check (and for the user's review).

Usage: sheet.py <frames_dir | video> <out.png> [--fps 20]
"""
import argparse
import os
import subprocess
import tempfile

from PIL import Image

TIMES = [0.3, 0.7, 1.1, 1.5, 1.9, 2.3, 2.7, 3.1, 3.4, 3.7, 4.0, 4.3, 4.6, 4.95]
W, H, COLS = 400, 225, 4


def frame_at(src, t, fps, tmp, i):
    if os.path.isdir(src):
        files = sorted(f for f in os.listdir(src) if f.lower().endswith(".png"))
        if not files:
            return None
        return os.path.join(src, files[min(len(files) - 1, int(round(t * fps)))])
    f = os.path.join(tmp, "%02d.png" % i)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", src, "-frames:v", "1", f])
    return f if os.path.exists(f) else None


def make_sheet(src, out, fps=20, times=TIMES):
    tmp = tempfile.mkdtemp()
    rows = (len(times) + COLS - 1) // COLS
    sh = Image.new("RGB", (W * COLS, H * rows), "#777")
    for i, t in enumerate(times):
        f = frame_at(src, t, fps, tmp, i)
        if f:
            sh.paste(Image.open(f).convert("RGB").resize((W, H)), ((i % COLS) * W, (i // COLS) * H))
    sh.save(out)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--fps", type=int, default=20)
    a = ap.parse_args()
    print(make_sheet(a.src, a.out, a.fps))
