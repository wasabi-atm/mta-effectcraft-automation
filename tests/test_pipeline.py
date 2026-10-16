"""Tests for the sneak-peek pipeline. Run: .venv/bin/python -m unittest discover -s tests -v

The EffectCraft and Blender tests skip when those tools are not installed (scripts/setup.sh).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "sneakpeek"))

import cli  # noqa: E402
from gifmake import make_gif  # noqa: E402
from sheet import make_sheet  # noqa: E402

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    Image = None


def frames(d, n=24, size=(1280, 720)):
    os.makedirs(d, exist_ok=True)
    for i in range(n):
        im = Image.new("RGB", size, "#000000")
        dr = ImageDraw.Draw(im)
        x = 100 + i * 40
        dr.ellipse([x, 300, x + 120, 420], fill="#2997ff")
        im.save(os.path.join(d, "f_%04d.png" % (i + 1)))
    return d


@unittest.skipIf(Image is None, "Pillow not installed")
class GifTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg not installed")
    def test_gif_from_frames_fits_budget(self):
        src = frames(os.path.join(self.tmp, "frames"))
        out = os.path.join(self.tmp, "x.gif")
        r = make_gif(src, out, max_mb=2.2)
        self.assertTrue(os.path.exists(out))
        self.assertTrue(r["fits"])
        im = Image.open(out)
        self.assertEqual(im.size, (640, 360))
        self.assertEqual(r["frames"], 24)

    def test_sheet_from_frames(self):
        src = frames(os.path.join(self.tmp, "frames"), n=100)
        out = make_sheet(src, os.path.join(self.tmp, "s.png"))
        self.assertEqual(Image.open(out).size, (1600, 225 * 4))


class RunnerTests(unittest.TestCase):
    def test_names(self):
        self.assertEqual(cli.slug_of("scenes/caronsale.com"), "caronsale-com")
        self.assertEqual(cli.comp_name("scenes/caronsale.com"), "SP_caronsalecom")

    def test_runner_sets_paths_and_checks_comp(self):
        js = cli.runner_jsx("/x/scenes/apple")
        self.assertIn(json.dumps(cli.LIB), js)
        self.assertIn('MTA.ROOT = "/x/scenes/apple/"', js)
        self.assertIn('MTA.COMP = "SP_apple"', js)
        self.assertIn('"/x/scenes/apple/scene.jsx"', js)


@unittest.skipUnless(cli.effectcraft_bin(), "effectcraft-cli not installed (scripts/setup.sh)")
class EffectCraftTests(unittest.TestCase):
    """lib_mta.jsx and the build runner against the real EffectCraft."""

    def test_build_and_render_frame(self):
        tmp = tempfile.mkdtemp()
        try:
            scene = os.path.join(tmp, "demo")
            os.makedirs(scene)
            open(os.path.join(scene, "scene.jsx"), "w").write(
                'var c = MTA.newComp(MTA.COMP, "#000000"); MTA.solid(c, "#000000", "bg");'
                'var b = MTA.button(c, { text: "Learn more", bg: "#0071E3", fg: "#ffffff", radius: 35, h: 70, pos: [640, 360] });'
                'MTA.pop(b, 0, 0.3); MTA.text(c, { text: "Hi", font: MTA.F.semi, size: 90, color: "#ffffff", just: "C", center: true });')
            cli.cmd_build(type("A", (), {"scene": scene})())
            proj = os.path.join(scene, "out", "scene.ecproj")
            self.assertTrue(os.path.exists(proj))
            png = os.path.join(tmp, "f.png")
            subprocess.run([cli.effectcraft_bin(), "render-frame", "--project", proj, "--comp", "SP_demo", "--time", "1",
                            "--max-side", "320", "--out", png], check=True, capture_output=True)
            im = Image.open(png).convert("RGB")
            self.assertGreater(im.getpixel((160, 90))[2], 150)  # the blue pill is in the middle
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_extrude3d_unsupported(self):
        """Documented gap: no Cinema 4D renderer. If this starts passing, drop the Blender workaround note."""
        r = subprocess.run([cli.effectcraft_bin(), "script", "--eval",
                            'var c = app.project.items.addComp("x", 100, 100, 1, 1, 20); var l = c.layers.addText("x");'
                            'String(l.property("ADBE Extrsn Options Group"))', "--empty"], capture_output=True, text=True)
        self.assertIn("null", r.stdout + r.stderr)


def _bpy_python():
    py, _ = cli.blender_python()
    return py


@unittest.skipUnless(_bpy_python(), "no Python with bpy (scripts/setup.sh)")
class BlenderMcpTests(unittest.TestCase):
    def test_protocol_and_scene(self):
        srv = subprocess.Popen([_bpy_python(), os.path.join(ROOT, "blender_mcp", "server.py")], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)

        def call(i, method, params=None):
            srv.stdin.write(json.dumps({"jsonrpc": "2.0", "id": i, "method": method, "params": params or {}}) + "\n")
            srv.stdin.flush()
            return json.loads(srv.stdout.readline())

        try:
            init = call(1, "initialize", {"protocolVersion": "2025-06-18"})
            self.assertEqual(init["result"]["protocolVersion"], "2025-06-18")
            names = [t["name"] for t in call(2, "tools/list")["result"]["tools"]]
            self.assertIn("render_frame", names)
            r = call(3, "tools/call", {"name": "run_python", "arguments": {"code": 'M.reset(64, 36, 20, 0.5)\nt = M.text3d("Hi", face="#ffffff", side="#888888")\nresult = len(t.data.materials)'}})
            self.assertFalse(r["result"]["isError"], r)
            self.assertEqual(json.loads(r["result"]["content"][0]["text"])["result"], 2)
            bad = call(4, "tools/call", {"name": "run_python", "arguments": {"code": "raise ValueError('boom')"}})
            self.assertTrue(bad["result"]["isError"])
            self.assertIn("boom", bad["result"]["content"][0]["text"])
        finally:
            srv.stdin.close()
            srv.wait(timeout=30)


if __name__ == "__main__":
    unittest.main()
