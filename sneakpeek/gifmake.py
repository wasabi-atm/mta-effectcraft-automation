#!/usr/bin/env python3
"""Rendered frames -> email GIF (640x360 by default), under a size budget.

Input is a folder of PNG frames (what `effectcraft-cli render --format png` writes) or any video
ffmpeg reads. A temporal hold keeps pixels that changed by <= T per channel from the previous
frame, so the GIF encoder can reuse them (renderers dither by +-1 per frame, which otherwise
makes every frame a full frame). Then a ladder steps down until the file fits: palette, gifsicle lossy LZW
(when installed), fewer colours, and only then 15 fps.

Usage: gifmake.py <frames_dir | video> <out.gif> [max_mb] [--fps 20] [--width 640]
"""
import argparse
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageChops

T = 5  # per-channel change at or below this counts as noise
# (fps, colours, dither, gifsicle lossy). Quality first: full frame rate and palette, then lossy LZW
# (gifsicle, when installed), then fewer colours, and only then fewer frames.
LADDER = [(20, 128, 4, 0), (20, 128, 4, 60), (20, 96, "none", 80), (20, 96, "none", 120), (20, 64, "none", 120),
          (15, 96, "none", 80), (15, 64, "none", 120), (15, 64, "none", 200)]


def _frames(src_dir):
    return sorted(f for f in os.listdir(src_dir) if f.lower().endswith(".png"))


def extract(src, raw_dir, width, height, fps):
    """Scale every input frame to width x height PNGs numbered %04d.png."""
    scale = f"scale={width}:{height}:flags=lanczos"
    if os.path.isdir(src):
        for i, f in enumerate(_frames(src), 1):
            im = Image.open(os.path.join(src, f)).convert("RGB")
            if im.size != (width, height):
                im = im.resize((width, height), Image.LANCZOS)
            im.save(os.path.join(raw_dir, "%04d.png" % i))
    else:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vf", f"fps={fps},{scale}",
                        os.path.join(raw_dir, "%04d.png")], check=True)
    return len(_frames(raw_dir))


def hold(src_dir, dst_dir):
    prev = None
    files = _frames(src_dir)
    for f in files:
        cur = Image.open(os.path.join(src_dir, f)).convert("RGB")
        if prev is None:
            out = cur
        else:
            r, g, b = ImageChops.difference(cur, prev).split()
            m = ImageChops.lighter(ImageChops.lighter(r, g), b)
            mask = m.point(lambda v: 255 if v <= T else 0)  # 255 = keep previous pixel
            out = Image.composite(prev, cur, mask)
        out.save(os.path.join(dst_dir, f))
        prev = out
    return len(files)


def encode(frames_dir, out, fps, colors, dither):
    pal = os.path.join(frames_dir, "pal.png")
    pattern = os.path.join(frames_dir, "%04d.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", pattern,
                    "-vf", f"palettegen=max_colors={colors}:stats_mode=full", pal], check=True)
    du = "dither=none" if dither == "none" else f"dither=bayer:bayer_scale={dither}"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", pattern, "-i", pal,
                    "-lavfi", f"paletteuse={du}:diff_mode=rectangle", "-loop", "0", out], check=True)
    os.remove(pal)
    return os.path.getsize(out) / 1e6


def lossy(path, level):
    """gifsicle -O3 --lossy=level in place; returns False when gifsicle isn't installed."""
    if not level or not shutil.which("gifsicle"):
        return False
    tmp = path + ".lossy.gif"
    subprocess.run(["gifsicle", "-O3", f"--lossy={level}", "-o", tmp, path], check=True)
    os.replace(tmp, path)
    return True


def make_gif(src, out, max_mb=2.2, fps=20, width=640, height=360):
    tmp = tempfile.mkdtemp(prefix="gifmake_")
    raw, held = os.path.join(tmp, "raw"), os.path.join(tmp, "held")
    os.makedirs(raw)
    os.makedirs(held)
    try:
        extract(src, raw, width, height, fps)
        n = hold(raw, held)
        tried, mb = [], 0.0
        has_gifsicle = bool(shutil.which("gifsicle"))
        for lfps, colors, dither, lossy_level in LADDER:
            if lossy_level and not has_gifsicle:
                continue
            lfps = min(lfps, fps)
            frames = held
            if lfps < fps:  # drop frames evenly (20 -> 15 keeps 3 of every 4)
                frames = os.path.join(tmp, f"f{lfps}")
                os.makedirs(frames, exist_ok=True)
                keep = _frames(held)
                j = 0
                for i, f in enumerate(keep):
                    if int(i * lfps / fps) != int((i + 1) * lfps / fps):
                        j += 1
                        shutil.copy(os.path.join(held, f), os.path.join(frames, "%04d.png" % j))
            mb = encode(frames, out, lfps, colors, dither)
            if lossy(out, lossy_level):
                mb = os.path.getsize(out) / 1e6
            tried.append(f"{lfps}fps/{colors}c/{dither}" + (f"/L{lossy_level}" if lossy_level else "") + f"={mb:.2f}MB")
            if mb <= max_mb:
                break
        return {"out": out, "frames": n, "mb": round(mb, 2), "tried": tried, "fits": mb <= max_mb}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("max_mb", nargs="?", type=float, default=2.2)
    ap.add_argument("--fps", type=int, default=20)
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=360)
    a = ap.parse_args()
    r = make_gif(a.src, a.out, a.max_mb, a.fps, a.width, a.height)
    print(f"{r['out']}: {r['frames']} frames; " + " | ".join(r["tried"]))


if __name__ == "__main__":
    main()
