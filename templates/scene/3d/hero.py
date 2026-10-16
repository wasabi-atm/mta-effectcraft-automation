"""{{SLUG}} 3D pass: real extruded type / logo / product, rendered as an RGBA PNG sequence.

`M` is sneakpeek/blender/mta3d.py; OUT is out/3d/hero/ (set by `sneakpeek 3d`). Delete this file if
the scene needs no 3D. See scenes/apple/3d/chip.py for a full worked example.
"""
import os

import mta3d as M

OUT = globals().get("OUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "3d", "hero")

M.reset(1280, 720, 20, 3.8, transparent=True, samples=32)
word = M.text3d("{{SLUG}}", size=1.4, extrude=0.3, bevel=0.025, font="black", face="#ffffff", side="#9aa0aa")
M.key(word, "rotation_euler", [[0.0, (1.5708, 0, -0.5)], [1.2, (1.5708, 0, 0.0)]], "out")
M.cam(dist=9, lens=50)
M.rig3("#2997FF")
bpy_scene = M._scene()
bpy_scene.render.resolution_percentage = 75   # 960x540 is plenty for a 640x360 GIF
M.render_sequence(OUT)
