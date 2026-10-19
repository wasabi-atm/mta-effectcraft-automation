#!/usr/bin/env python3
"""Rendered frames -> email GIF (640x360 by default), under a size budget.

Input is a folder of PNG frames (what `effectcraft-cli render --format png` writes) or any video
ffmpeg reads. A temporal hold keeps pixels that changed by <= T per channel from the previous
frame, so the GIF encoder can reuse them (renderers dither by +-1 per frame, which otherwise
makes every frame a full frame). Then a ladder steps down until the file fits: a palette per segment
(when gifsicle is installed to join them), fewer colours, light gifsicle lossy LZW, one global palette,
and only then 15 fps.

Why segments: one global palette has to cover a dark 3D opening, the UI beat and a light end card, so
a soft glow gets a handful of blues and bands into contour rings. Cutting the piece at its biggest
frame-to-frame changes (usually the 3D-to-UI handover and the end-card transition) and giving each
part its own palette keeps gradients smooth; inside a segment the dither stays stable, so the hold
still pays off. A per-frame palette does not: its dither changes every frame and the GIF triples.

Usage: gifmake.py <frames_dir | video> <out.gif> [max_mb] [--fps 20] [--width 640]
"""
import argparse
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageChops, ImageStat

T = 5  # per-channel change at or below this counts as noise
SEGMENTS = 3   # palettes per GIF on the segmented rungs
MIN_SEG = 12   # frames
# (fps, colours, dither, gifsicle lossy, segments). Quality first: full frame rate with a palette per
# segment, then fewer colours, then light lossy LZW (grain reads better than contour-banded glows), then one
# global palette, and only then fewer frames.
# Segmented and lossy rungs need gifsicle; without it they are skipped.
LADDER = [(20, 128, 4, 0, SEGMENTS), (20, 96, 3, 0, SEGMENTS), (20, 80, 3, 0, SEGMENTS), (20, 96, 3, 20, SEGMENTS),
          (20, 96, 3, 30, SEGMENTS), (20, 96, 3, 40, SEGMENTS), (20, 80, 3, 60, SEGMENTS), (20, 128, 4, 0, 1),
          (20, 128, 4, 60, 1), (20, 96, "none", 80, 1), (20, 96, "none", 120, 1), (20, 64, "none", 120, 1),
          (15, 96, "none", 80, 1), (15, 64, "none", 120, 1), (15, 64, "none", 200, 1)]


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


def _maxdiff(a, b):
    r, g, b2 = ImageChops.difference(a, b).split()
    return ImageChops.lighter(ImageChops.lighter(r, g), b2)


def hold(src_dir, dst_dir):
    """Keep the previous output pixel where the change is noise. A held pixel is refreshed once the
    source has settled there (raw frame-to-frame change <= 1) but still differs from the held value by
    more than 2: otherwise a slow change of <= T (a light card dissolving into a light end card) stays
    frozen as a ghost for the rest of the GIF."""
    prev = raw_prev = None
    files = _frames(src_dir)
    for f in files:
        cur = Image.open(os.path.join(src_dir, f)).convert("RGB")
        if prev is None:
            out = cur
        else:
            near = _maxdiff(cur, prev).point(lambda v: 255 if v <= T else 0)          # 255 = within noise of held
            stale = ImageChops.multiply(_maxdiff(cur, raw_prev).point(lambda v: 255 if v <= 1 else 0),
                                        _maxdiff(cur, prev).point(lambda v: 255 if v > 2 else 0))
            mask = ImageChops.subtract(near, stale)                                     # 255 = keep previous pixel
            out = Image.composite(prev, cur, mask)
        out.save(os.path.join(dst_dir, f))
        prev, raw_prev = out, cur
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


def cuts(frames_dir, k, min_len=MIN_SEG):
    """Frame indices (0-based, each starting a segment) at the k-1 biggest frame-to-frame changes,
    at least min_len frames apart and from either end."""
    files = _frames(frames_dir)
    change = [0.0]
    prev = Image.open(os.path.join(frames_dir, files[0])).convert("RGB")
    for f in files[1:]:
        cur = Image.open(os.path.join(frames_dir, f)).convert("RGB")
        change.append(sum(ImageStat.Stat(ImageChops.difference(cur, prev)).mean))
        prev = cur
    picked = []
    for i in sorted(range(1, len(files)), key=lambda j: -change[j]):
        if len(picked) == k - 1:
            break
        if all(abs(i - j) >= min_len for j in picked + [0, len(files)]):
            picked.append(i)
    return sorted(picked)


def encode_segments(frames_dir, out, fps, colors, dither, k):
    """A palette per segment (ffmpeg), joined with gifsicle -O3. Returns MB."""
    files = _frames(frames_dir)
    bounds = [0] + cuts(frames_dir, k) + [len(files)]
    parts = []
    for s, (a, b) in enumerate(zip(bounds, bounds[1:])):
        seg = os.path.join(frames_dir, f"_seg{s}")
        os.makedirs(seg, exist_ok=True)
        for j, f in enumerate(files[a:b], 1):
            shutil.copy(os.path.join(frames_dir, f), os.path.join(seg, "%04d.png" % j))
        part = os.path.join(frames_dir, f"_seg{s}.gif")
        encode(seg, part, fps, colors, dither)
        shutil.rmtree(seg)
        parts.append(part)
    subprocess.run(["gifsicle", "-O3", "--loopcount=forever"] + parts + ["-o", out], check=True, capture_output=True)
    for p in parts:
        os.remove(p)
    return os.path.getsize(out) / 1e6


def lossy(path, level):
    """gifsicle -O3 --lossy=level in place; returns False when gifsicle isn't installed."""
    if not level or not shutil.which("gifsicle"):
        return False
    tmp = path + ".lossy.gif"
    subprocess.run(["gifsicle", "-O3", f"--lossy={level}", "-o", tmp, path], check=True, capture_output=True)
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
        for lfps, colors, dither, lossy_level, segs in LADDER:
            if (lossy_level or segs > 1) and not has_gifsicle:
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
            if segs > 1:
                mb = encode_segments(frames, out, lfps, colors, dither, segs)
            else:
                mb = encode(frames, out, lfps, colors, dither)
            if lossy(out, lossy_level):
                mb = os.path.getsize(out) / 1e6
            tried.append(f"{lfps}fps/{colors}c/{dither}" + (f"/{segs}seg" if segs > 1 else "")
                         + (f"/L{lossy_level}" if lossy_level else "") + f"={mb:.2f}MB")
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
