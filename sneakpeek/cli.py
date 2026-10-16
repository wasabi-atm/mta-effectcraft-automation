#!/usr/bin/env python3
"""sneakpeek - headless email 3 sneak-peek GIFs: EffectCraft (2D/compositing) + Blender (3D).

Replaces the After Effects toolkit (osascript DoScriptFile into a desktop AE, Mac only) so the
whole pipeline runs in a cloud session with no display.

A scene is a folder:

    <scene>/
      brief.md          concept, brand notes, claims and their sources
      brand/            brand.json, logo.png, home.png (from `sneakpeek brand`), extra stills
      scene.jsx         EffectCraft scene: After Effects-style ExtendScript using lib_mta.jsx (MTA.*)
      3d/*.py           optional Blender passes; each renders an RGBA PNG sequence to out/3d/<name>/
      out/              scene.ecproj, frames/, <slug>.gif, <slug>_sheet.png, status.json

Commands:
    doctor                         check EffectCraft, Blender (bpy), ffmpeg, Pillow, Chromium, ImageKit
    new <scene>                    scaffold a scene folder from the template
    brand <concepts.csv> <dir>     pull logo / CTA / colours from each company's site (Playwright)
    3d <scene>                     run the Blender passes
    build <scene>                  run scene.jsx in headless EffectCraft, save out/scene.ecproj
    render <scene>                 render the SP_ comp to out/frames/
    gif <scene>                    out/frames -> out/<slug>.gif (+ contact sheet)
    run <scene> [<scene> ...]      3d + build + render + gif for each scene
    host <scene> --prefix eu1015   upload the GIF to ImageKit, print the versioned URL
"""
import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LIB = os.path.join(HERE, "jsx", "lib_mta.jsx")
TEMPLATE = os.path.join(ROOT, "templates", "scene")
sys.path.insert(0, HERE)


def load_env():
    """Read ROOT/.env (KEY=VALUE) into os.environ without overriding what is already set."""
    p = os.path.join(ROOT, ".env")
    if not os.path.exists(p):
        return
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def effectcraft_bin():
    for c in (os.environ.get("EFFECTCRAFT_CLI"), os.path.join(ROOT, ".tools", "bin", "effectcraft-cli"), shutil.which("effectcraft-cli")):
        if c and os.path.exists(c):
            return c
    return None


def blender_python():
    """A Python that can `import bpy`: $BLENDER_PYTHON, the project venv, or this interpreter."""
    for c in (os.environ.get("BLENDER_PYTHON"), os.path.join(ROOT, ".venv", "bin", "python"), sys.executable):
        if c and os.path.exists(c):
            r = subprocess.run([c, "-c", "import bpy; print(bpy.app.version_string)"], capture_output=True, text=True)
            if r.returncode == 0:
                return c, r.stdout.strip().splitlines()[-1]
    return None, None


def slug_of(scene):
    return os.path.basename(os.path.normpath(scene)).lower().replace(".", "-")


def comp_name(scene):
    return "SP_" + slug_of(scene).replace("-", "")


def out_dir(scene):
    d = os.path.join(scene, "out")
    os.makedirs(d, exist_ok=True)
    return d


def write_status(scene, **kw):
    p = os.path.join(out_dir(scene), "status.json")
    st = json.load(open(p)) if os.path.exists(p) else {}
    st.update(kw)
    st["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    json.dump(st, open(p, "w"), indent=1)
    return st


# ---------------------------------------------------------------- doctor
def cmd_doctor(_a):
    ok = True

    def line(good, name, detail):
        nonlocal ok
        ok = ok and (good or good is None)
        mark = "ok  " if good else ("--  " if good is None else "FAIL")
        print(f"{mark} {name:<12} {detail}")

    ec = effectcraft_bin()
    if ec:
        r = subprocess.run([ec, "info", "--empty", "--json"], capture_output=True, text=True)
        line(r.returncode == 0, "effectcraft", ec + ("" if r.returncode == 0 else "  (info failed: " + r.stderr.strip()[:120] + ")"))
    else:
        line(False, "effectcraft", "effectcraft-cli not found: run scripts/setup.sh (or set EFFECTCRAFT_CLI)")
    py, ver = blender_python()
    line(bool(py), "blender", f"bpy {ver} via {py}" if py else "no Python with `import bpy`: run scripts/setup.sh (pip install bpy, Python 3.13)")
    line(bool(shutil.which("ffmpeg")), "ffmpeg", shutil.which("ffmpeg") or "missing (apt-get install ffmpeg)")
    line(True if shutil.which("gifsicle") else None, "gifsicle", shutil.which("gifsicle") or "not installed: GIFs fall back to 15 fps sooner to fit 2.2 MB")
    try:
        import PIL
        line(True, "pillow", PIL.__version__)
    except ImportError:
        line(False, "pillow", "missing (pip install pillow)")
    try:
        import playwright  # noqa: F401
        line(True, "playwright", "installed (brand extraction)")
    except ImportError:
        line(None, "playwright", "not installed: `sneakpeek brand` unavailable (optional)")
    load_env()
    from host import configured
    line(True if configured() else None, "imagekit", "IMAGEKIT_PRIVATE_KEY set" if configured() else "not set: `sneakpeek host` unavailable (optional)")
    print("doctor:", "ready" if ok else "NOT READY")
    return 0 if ok else 1


# ---------------------------------------------------------------- new
def cmd_new(a):
    if os.path.exists(a.scene) and os.listdir(a.scene):
        sys.exit(f"{a.scene} exists and is not empty")
    shutil.copytree(TEMPLATE, a.scene, dirs_exist_ok=True)
    for name in ("scene.jsx", "brief.md", os.path.join("3d", "hero.py")):
        p = os.path.join(a.scene, name)
        if os.path.exists(p):
            s = open(p, encoding="utf-8").read().replace("{{COMP}}", comp_name(a.scene)).replace("{{SLUG}}", slug_of(a.scene))
            open(p, "w", encoding="utf-8").write(s)
    print("scaffolded", a.scene, "comp", comp_name(a.scene))


# ---------------------------------------------------------------- brand
def cmd_brand(a):
    import brand_extract
    sys.argv = ["brand_extract.py", a.concepts, a.out] + a.domains
    brand_extract.main()


# ---------------------------------------------------------------- 3d
def cmd_3d(a):
    d = os.path.join(a.scene, "3d")
    passes = sorted(f for f in os.listdir(d) if f.endswith(".py")) if os.path.isdir(d) else []
    if not passes:
        print("no 3d passes")
        return 0
    py, _ = blender_python()
    if not py:
        sys.exit("no Blender: run `sneakpeek doctor`")
    for f in passes:
        name = f[:-3]
        dest = os.path.join(out_dir(a.scene), "3d", name)
        if os.path.isdir(dest) and not a.force and _newer(dest, os.path.join(d, f)):
            print(f"3d {name}: up to date")
            continue
        shutil.rmtree(dest, ignore_errors=True)
        t0 = time.time()
        code = (f"import sys; sys.path.insert(0, {os.path.join(HERE, 'blender')!r}); import mta3d as M; "
                f"OUT = {dest!r}; SCENE = {os.path.abspath(a.scene)!r}; __file__ = {os.path.abspath(os.path.join(d, f))!r}; "
                f"exec(compile(open(__file__).read(), __file__, 'exec'))")
        r = subprocess.run([py, "-c", code], capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-2000:], r.stderr[-4000:])
            sys.exit(f"3d {name}: FAILED")
        n = len([x for x in os.listdir(dest) if x.endswith(".png")]) if os.path.isdir(dest) else 0
        print(f"3d {name}: {n} frames in {time.time() - t0:.0f}s -> {dest}")
    write_status(a.scene, three_d=passes)
    return 0


def _newer(dest, src):
    pngs = [os.path.join(dest, x) for x in os.listdir(dest) if x.endswith(".png")]
    return bool(pngs) and min(os.path.getmtime(p) for p in pngs) > os.path.getmtime(src)


# ---------------------------------------------------------------- build
def runner_jsx(scene):
    scene = os.path.abspath(scene)
    root = scene.rstrip("/") + "/"
    return f"""$.evalFile({json.dumps(LIB)});
MTA.ROOT = {json.dumps(root)};
MTA.BRAND = MTA.ROOT + "brand/";
MTA.OUT3D = MTA.ROOT + "out/3d/";
MTA.COMP = {json.dumps(comp_name(scene))};
var __msg;
try {{
  app.beginUndoGroup("build {comp_name(scene)}");
  $.evalFile({json.dumps(os.path.join(scene, "scene.jsx"))});
  app.endUndoGroup();
  var __c = MTA.findComp(MTA.COMP);
  if (!__c) {{ throw new Error("comp " + MTA.COMP + " not found: scene.jsx must create it with MTA.newComp(MTA.COMP, ...)"); }}
  __msg = "ok layers=" + __c.numLayers + " duration=" + __c.duration;
}} catch (e) {{ __msg = "ERR " + e.toString() + (e.line ? " line " + e.line : "") + (e.fileName ? " file " + e.fileName : ""); }}
__msg;
"""


def cmd_build(a):
    ec = effectcraft_bin() or sys.exit("effectcraft-cli not found: run scripts/setup.sh")
    od = out_dir(a.scene)
    run = os.path.join(od, "_run.jsx")
    open(run, "w", encoding="utf-8").write(runner_jsx(a.scene))
    proj = os.path.join(od, "scene.ecproj")
    t0 = time.time()
    # Scripts may only read files beside themselves unless "Allow Scripts to Write Files and Access
    # Network" is on (as in After Effects). Turn it on for this session only, in a config dir of our
    # own, so a desktop EffectCraft's preferences are never touched.
    env = dict(os.environ, EFFECTCRAFT_CONFIG_DIR=os.path.join(ROOT, ".tools", "config"))
    os.makedirs(env["EFFECTCRAFT_CONFIG_DIR"], exist_ok=True)
    params = json.dumps({"code": open(run, encoding="utf-8").read(), "name": run})
    r = subprocess.run([ec, "run", "prefs.set", json.dumps({"key": "scripting.allowScriptsWriteFiles", "value": True}),
                        "script.run", params, "--empty", "--save-as", proj, "--json"], capture_output=True, text=True, env=env)
    res = {}
    try:
        reply = json.loads(r.stdout.strip().splitlines()[-1])   # {"result": [{command, result}...], "saved": path}
        steps = reply.get("result", reply) if isinstance(reply, dict) else reply
        res = next((st.get("result") or {} for st in steps if st.get("command") == "script.run"), {})
    except (ValueError, IndexError, AttributeError):
        pass
    msg = str(res.get("result") or "") or (res.get("error") or {}).get("message") or r.stderr.strip()[-600:]
    out = (res.get("output") or "").strip()
    if out:
        print(out[-3000:])
    good = r.returncode == 0 and msg.startswith("ok")
    write_status(a.scene, build=msg, project=proj if good else None)
    print(f"build {slug_of(a.scene)}: {msg} ({time.time() - t0:.1f}s)")
    if not good:
        sys.exit(1)


# ---------------------------------------------------------------- render
def cmd_render(a):
    ec = effectcraft_bin() or sys.exit("effectcraft-cli not found")
    od = out_dir(a.scene)
    proj = os.path.join(od, "scene.ecproj")
    if not os.path.exists(proj):
        sys.exit("no out/scene.ecproj: run `sneakpeek build` first")
    frames = os.path.join(od, "frames")
    shutil.rmtree(frames, ignore_errors=True)
    os.makedirs(frames)
    t0 = time.time()
    cmd = [ec, "render", "--project", proj, "--comp", comp_name(a.scene), "--format", "png",
           "--out", os.path.join(frames, "f_[####].png"), "--quality", "best"]
    if a.gpu:
        cmd.append("--gpu")
    r = subprocess.run(cmd, capture_output=True, text=True)
    n = len([f for f in os.listdir(frames) if f.endswith(".png")])
    if r.returncode != 0 or n == 0:
        print(r.stdout[-1500:], r.stderr[-3000:])
        write_status(a.scene, render="FAILED")
        sys.exit(f"render {slug_of(a.scene)}: FAILED")
    write_status(a.scene, render=f"{n} frames", render_s=round(time.time() - t0, 1))
    print(f"render {slug_of(a.scene)}: {n} frames in {time.time() - t0:.0f}s -> {frames}")


# ---------------------------------------------------------------- gif
def cmd_gif(a):
    from gifmake import make_gif
    from sheet import make_sheet
    od = out_dir(a.scene)
    frames = os.path.join(od, "frames")
    gif = os.path.join(od, slug_of(a.scene) + ".gif")
    r = make_gif(frames, gif, a.max_mb, fps=a.fps, width=a.width, height=a.width * 9 // 16)
    sheet = make_sheet(frames, os.path.join(od, slug_of(a.scene) + "_sheet.png"), fps=a.fps)
    write_status(a.scene, gif=gif, gif_mb=r["mb"], gif_fits=r["fits"], sheet=sheet)
    print(f"gif {slug_of(a.scene)}: {r['mb']} MB ({' | '.join(r['tried'])}) -> {gif}")
    print(f"sheet -> {sheet}")


# ---------------------------------------------------------------- run
def cmd_run(a):
    for s in a.scenes:
        ns = argparse.Namespace(scene=s, force=a.force, gpu=a.gpu, max_mb=a.max_mb, fps=a.fps, width=a.width)
        print(f"== {slug_of(s)}")
        cmd_3d(ns)
        cmd_build(ns)
        cmd_render(ns)
        cmd_gif(ns)
    print("ALLDONE")


# ---------------------------------------------------------------- host
def cmd_host(a):
    load_env()
    import host
    gif = os.path.join(out_dir(a.scene), slug_of(a.scene) + ".gif")
    if not os.path.exists(gif):
        sys.exit("no GIF: run `sneakpeek gif` first")
    domain = (a.domain or slug_of(a.scene)).replace(".", "-")
    url = host.upload(gif, f"{a.prefix}-sp-{domain}.gif")
    status = host.check(url)
    write_status(a.scene, url=url, url_status=status)
    print(url, status)
    if a.csv:
        new = not os.path.exists(a.csv)
        with open(a.csv, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["Company", "Domain", "SneakPeekUrl", "SizeKB"])
            w.writerow([a.company or slug_of(a.scene), domain, url, os.path.getsize(gif) // 1024])
    if status != 200:
        sys.exit(f"hosted URL answered {status}: do not put it in a campaign")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sneakpeek", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor").set_defaults(fn=cmd_doctor)
    p = sub.add_parser("new")
    p.add_argument("scene")
    p.set_defaults(fn=cmd_new)
    p = sub.add_parser("brand")
    p.add_argument("concepts")
    p.add_argument("out")
    p.add_argument("domains", nargs="*")
    p.set_defaults(fn=cmd_brand)
    for name, fn in (("3d", cmd_3d), ("build", cmd_build), ("render", cmd_render), ("gif", cmd_gif)):
        p = sub.add_parser(name)
        p.add_argument("scene")
        p.add_argument("--force", action="store_true")
        p.add_argument("--gpu", action="store_true")
        p.add_argument("--max-mb", type=float, default=2.2)
        p.add_argument("--fps", type=int, default=20)
        p.add_argument("--width", type=int, default=640)
        p.set_defaults(fn=fn)
    p = sub.add_parser("run")
    p.add_argument("scenes", nargs="+")
    p.add_argument("--force", action="store_true")
    p.add_argument("--gpu", action="store_true")
    p.add_argument("--max-mb", type=float, default=2.2)
    p.add_argument("--fps", type=int, default=20)
    p.add_argument("--width", type=int, default=640)
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("host")
    p.add_argument("scene")
    p.add_argument("--prefix", required=True, help="run prefix, e.g. eu1015")
    p.add_argument("--domain")
    p.add_argument("--company")
    p.add_argument("--csv", help="append Company,Domain,SneakPeekUrl,SizeKB to this CSV")
    p.set_defaults(fn=cmd_host)
    a = ap.parse_args(argv)
    return a.fn(a) or 0


if __name__ == "__main__":
    sys.exit(main())
