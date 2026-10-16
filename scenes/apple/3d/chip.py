"""Apple sneak peek, 3D pass: the chip.

One continuous camera move, frames 1-78 (0-3.85 s at 20 fps); the end card is 2D only.
  f1-30   macro: grazing close-up on the lid's chamfered corner, f/1.4, a strip light sweeps a
          specular streak across the brushed aluminium
  f30-78  pull back and rise to a three-quarter top view; the traces light up from the package
          outward in a blue -> purple -> pink -> orange gradient, the die's floorplan glows last

Generic chip: no logo, no product name, no claim. Runs under `sneakpeek 3d` (OUT is set) or the
Blender MCP `run_file` tool (OUT defaults below).
"""
import math
import os
import random

import bmesh
import bpy
import mta3d as M

OUT = globals().get("OUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "3d", "chip")
PREVIEW = globals().get("ARGS", {}).get("preview") if isinstance(globals().get("ARGS"), dict) else None

W, H, FPS = 1280, 720, 20
LAST = 78                       # last rendered frame
PALETTE = ["#2997FF", "#7D7AFF", "#BF5AF2", "#FF375F", "#FF9F0A"]   # Apple system blue..orange

random.seed(7)
M.reset(W, H, FPS, LAST / FPS, transparent=False, samples=64)
sc = bpy.context.scene
sc.frame_end = LAST
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 6
sc.cycles.glossy_bounces = 4
sc.cycles.transparent_max_bounces = 2
sc.view_settings.view_transform = "AgX"           # filmic roll-off for speculars on metal
sc.view_settings.look = "AgX - Medium High Contrast"


# ------------------------------------------------------------------ materials
def principled(name, base, metallic=0.0, rough=0.4, coat=0.0, coat_rough=0.05):
    m = M.mat(name, base, metallic=metallic, roughness=rough)
    p = m.node_tree.nodes["Principled BSDF"]
    if coat:
        p.inputs["Coat Weight"].default_value = coat
        p.inputs["Coat Roughness"].default_value = coat_rough
    return m, p


def brushed(name, base, rough_lo=0.16, rough_hi=0.34, scale=(1.0, 260.0, 1.0), bump=0.03):
    """Brushed metal: noise stretched along one axis drives roughness and a fine bump."""
    m, p = principled(name, base, metallic=1.0)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 6.0
    nz.inputs["Detail"].default_value = 8.0
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = rough_lo
    mr.inputs["To Max"].default_value = rough_hi
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], p.inputs["Roughness"])
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m


def ramp_palette(nt, fac_socket):
    cr = nt.nodes.new("ShaderNodeValToRGB")
    els = cr.color_ramp.elements
    cols = PALETTE + [PALETTE[0]]
    while len(els) < len(cols):
        els.new(0.5)
    for i, h in enumerate(cols):
        els[i].position = i / (len(cols) - 1)
        els[i].color = M.hex2lin(h)
    nt.links.new(fac_socket, cr.inputs["Fac"])
    return cr


def angle_fac(nt):
    """0..1 around the chip centre (atan2 of object-space XY), for the radial palette."""
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    at = nt.nodes.new("ShaderNodeMath"); at.operation = "ARCTAN2"
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -math.pi
    mr.inputs["From Max"].default_value = math.pi
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    nt.links.new(sep.outputs["Y"], at.inputs[0])
    nt.links.new(sep.outputs["X"], at.inputs[1])
    nt.links.new(at.outputs[0], mr.inputs["Value"])
    return geo, sep, mr.outputs["Result"]


def keyed_value(nt, name, keys, ease="out"):
    v = nt.nodes.new("ShaderNodeValue")
    v.label = name
    for t, val in keys:
        v.outputs[0].default_value = val
        v.outputs[0].keyframe_insert("default_value", frame=M.sec(t))
    ad = nt.animation_data
    if ad and ad.action:
        for fc in M._fcurves(ad.action, 'nodes["%s"].outputs[0].default_value' % v.name):
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
                kp.handle_left_type = kp.handle_right_type = "FREE"
            M._ease(fc, ease)
    return v.outputs[0]


def trace_material():
    """Dark metal traces; emission sweeps outward from the package (reach R), hot at the wavefront."""
    m, p = principled("trace", "#2a2e36", metallic=1.0, rough=0.28)
    nt = m.node_tree
    geo, sep, afac = angle_fac(nt)
    col = ramp_palette(nt, afac)
    cmb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sep.outputs["X"], cmb.inputs["X"])
    nt.links.new(sep.outputs["Y"], cmb.inputs["Y"])
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
    nt.links.new(cmb.outputs[0], ln.inputs[0])
    d = ln.outputs["Value"]
    R = keyed_value(nt, "reach", [(0.0, 1.9), (1.45, 1.9), (3.55, 15.0)], "out")
    # lit = 1 - smoothstep(R - 1.2, R, d)
    lo = nt.nodes.new("ShaderNodeMath"); lo.operation = "SUBTRACT"; lo.inputs[1].default_value = 1.2
    nt.links.new(R, lo.inputs[0])
    lit = nt.nodes.new("ShaderNodeMapRange"); lit.interpolation_type = "SMOOTHSTEP"
    lit.inputs["To Min"].default_value = 1.0; lit.inputs["To Max"].default_value = 0.0
    nt.links.new(d, lit.inputs["Value"]); nt.links.new(lo.outputs[0], lit.inputs["From Min"]); nt.links.new(R, lit.inputs["From Max"])
    # head = 1 - smoothstep(0, 0.45, |d - R|)
    df = nt.nodes.new("ShaderNodeMath"); df.operation = "SUBTRACT"
    nt.links.new(d, df.inputs[0]); nt.links.new(R, df.inputs[1])
    ab = nt.nodes.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"
    nt.links.new(df.outputs[0], ab.inputs[0])
    hd = nt.nodes.new("ShaderNodeMapRange"); hd.interpolation_type = "SMOOTHSTEP"
    hd.inputs["From Min"].default_value = 0.0; hd.inputs["From Max"].default_value = 0.45
    hd.inputs["To Min"].default_value = 1.0; hd.inputs["To Max"].default_value = 0.0
    nt.links.new(ab.outputs[0], hd.inputs["Value"])
    # strength = lit * 4 + head * 30, faded out at distance so the far board melts into black
    a = nt.nodes.new("ShaderNodeMath"); a.operation = "MULTIPLY"; a.inputs[1].default_value = 2.2
    nt.links.new(lit.outputs["Result"], a.inputs[0])
    b = nt.nodes.new("ShaderNodeMath"); b.operation = "MULTIPLY_ADD"; b.inputs[1].default_value = 30.0
    nt.links.new(hd.outputs["Result"], b.inputs[0]); nt.links.new(a.outputs[0], b.inputs[2])
    far = nt.nodes.new("ShaderNodeMapRange"); far.interpolation_type = "SMOOTHSTEP"
    far.inputs["From Min"].default_value = 6.0; far.inputs["From Max"].default_value = 13.0
    far.inputs["To Min"].default_value = 1.0; far.inputs["To Max"].default_value = 0.0
    nt.links.new(d, far.inputs["Value"])
    s = nt.nodes.new("ShaderNodeMath"); s.operation = "MULTIPLY"
    nt.links.new(b.outputs[0], s.inputs[0]); nt.links.new(far.outputs["Result"], s.inputs[1])
    nt.links.new(col.outputs["Color"], p.inputs["Emission Color"])
    nt.links.new(s.outputs[0], p.inputs["Emission Strength"])
    return m


def die_material():
    """Polished black glass die (the floorplan on it is geometry, see floorplan())."""
    m, p = principled("die", "#040507", metallic=0.0, rough=0.05, coat=1.0, coat_rough=0.02)
    return m


def floorplan_material():
    m, p = principled("floorplan", "#1b1e24", metallic=1.0, rough=0.3)
    nt = m.node_tree
    geo, sep, afac = angle_fac(nt)
    col = ramp_palette(nt, afac)
    on = keyed_value(nt, "floorplan glow", [(0.0, 0.0), (2.5, 0.0), (3.35, 3.0)], "inout")
    nt.links.new(col.outputs["Color"], p.inputs["Emission Color"])
    nt.links.new(on, p.inputs["Emission Strength"])
    return m


def board_material():
    m, p = principled("board", "#06070a", rough=0.62)
    nt = m.node_tree
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 180.0
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.025   # fine grain costs GIF bytes
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m


M_LID = brushed("lid", "#c9cdd3")
M_SUB, _ = principled("substrate", "#14161b", rough=0.22, coat=0.7)
M_PAD, _ = principled("pad", "#b9bdc5", metallic=1.0, rough=0.18)
M_CAP_BODY, _ = principled("cap body", "#2b2622", rough=0.45)
M_DIE = die_material()
M_TRACE = trace_material()
M_PLAN = floorplan_material()
M_VIA, _ = principled("via", "#9aa0aa", metallic=1.0, rough=0.2)
M_BOARD = board_material()


# ------------------------------------------------------------------ geometry
def rounded_box(name, sx, sy, sz, corner, edge, z0, material, seg=12):
    """Box sx * sy * sz with rounded vertical corners (radius `corner`) and softened top/bottom edges."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, z0 + sz / 2), verts=bm.verts)
    vert = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-6]
    bmesh.ops.bevel(bm, geom=vert, offset=corner, segments=seg, affect="EDGES", profile=0.5)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    me.materials.append(material)
    if edge:
        bv = ob.modifiers.new("edge", "BEVEL")
        bv.width = edge
        bv.segments = 5
        bv.limit_method = "ANGLE"
        bv.angle_limit = math.radians(50)
        bv.harden_normals = True
    for poly in me.polygons:
        poly.use_smooth = True
    return ob


def board():
    bpy.ops.mesh.primitive_plane_add(size=48, location=(0, 0, 0))
    ob = bpy.context.object
    ob.name = "board"
    ob.data.materials.append(M_BOARD)
    return ob


def traces():
    """PCB fan-out: from each side of the package, straight out, a 45 degree jog, straight on."""
    curves = bpy.data.curves.new("traces", "CURVE")
    curves.dimensions = "3D"
    curves.bevel_depth = 0.014
    curves.bevel_resolution = 1
    vias = []
    z = 0.004
    for side in range(4):
        rot = side * math.pi / 2
        c, s = math.cos(rot), math.sin(rot)
        n = 30
        for i in range(n):
            u = -2.0 + 4.0 * (i + 0.5) / n + random.uniform(-0.02, 0.02)   # along the side
            out0 = 2.28
            run1 = random.uniform(0.25, 1.6)
            jog = random.choice([-1, 1]) * random.uniform(0.2, 1.4) * (1 if u > 0 else -1 if random.random() < 0.7 else 1)
            run2 = random.uniform(1.5, 8.5)
            pts = [(u, out0), (u, out0 + run1), (u + jog, out0 + run1 + abs(jog)), (u + jog, out0 + run1 + abs(jog) + run2)]
            sp = curves.splines.new("POLY")
            sp.points.add(len(pts) - 1)
            for k, (x, y) in enumerate(pts):
                X, Y = x * c - y * s, x * s + y * c
                sp.points[k].co = (X, Y, z, 1)
            if random.random() < 0.55:
                x, y = pts[-1]
                vias.append((x * c - y * s, x * s + y * c))
    ob = bpy.data.objects.new("traces", curves)
    sc.collection.objects.link(ob)
    curves.materials.append(M_TRACE)
    for (x, y) in vias:
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.045, depth=0.01, location=(x, y, 0.006))
        v = bpy.context.object
        v.data.materials.append(M_TRACE)
    return ob


def package():
    rounded_box("substrate", 4.5, 4.5, 0.10, 0.18, 0.012, 0.0, M_SUB)
    lid = rounded_box("lid", 3.25, 3.25, 0.15, 0.34, 0.035, 0.10, M_LID)
    rounded_box("die", 2.45, 2.45, 0.022, 0.20, 0.006, 0.25, M_DIE)
    # capacitors in the gap between lid and substrate edge, and pads along the edge
    for side in range(4):
        rot = side * math.pi / 2
        c, s = math.cos(rot), math.sin(rot)
        for i in range(9):
            u = -1.45 + i * (2.9 / 8)
            if i in (3, 4, 5) and side % 2 == 0:
                continue
            x, y = u, 1.9
            X, Y = x * c - y * s, x * s + y * c
            body = rounded_box("cap", 0.16, 0.08, 0.07, 0.015, 0.006, 0.10, M_CAP_BODY, seg=3)
            body.location = (X, Y, 0)
            body.rotation_euler = (0, 0, rot)
            for e in (-1, 1):
                end = rounded_box("cap end", 0.04, 0.085, 0.075, 0.01, 0.004, 0.10, M_PAD, seg=2)
                end.location = (X + e * 0.08 * c, Y + e * 0.08 * s, 0)
                end.rotation_euler = (0, 0, rot)
        for i in range(36):
            u = -2.1 + i * (4.2 / 35)
            x, y = u, 2.2
            X, Y = x * c - y * s, x * s + y * c
            pad = rounded_box("pad", 0.06, 0.05, 0.012, 0.01, 0.0, 0.10, M_PAD, seg=2)
            pad.location = (X, Y, 0)
            pad.rotation_euler = (0, 0, rot)
    return lid


def floorplan(z=0.2738, half=1.08, gap=0.045):
    """Die floorplan: the die split recursively into blocks (cores, caches, GPU, neural engine), each
    drawn as a fine rounded outline; some blocks carry a grid of cores."""
    cu = bpy.data.curves.new("floorplan", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.0035
    cu.bevel_resolution = 0
    rng = random.Random(11)

    def outline(x0, y0, x1, y1, r=0.025):
        pts = []
        for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
            for k in range(4):
                a = math.radians(a0 + k * 30)
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for i, (x, y) in enumerate(pts):
            sp.points[i].co = (x, y, z, 1)
        sp.use_cyclic_u = True

    def line(x0, y0, x1, y1):
        sp = cu.splines.new("POLY")
        sp.points.add(1)
        sp.points[0].co = (x0, y0, z, 1)
        sp.points[1].co = (x1, y1, z, 1)

    def split(x0, y0, x1, y1, depth, vertical):
        w, h = x1 - x0, y1 - y0
        if depth == 0 or min(w, h) < 0.32:
            outline(x0, y0, x1, y1)
            if rng.random() < 0.45 and min(w, h) > 0.3:      # a grid of cores inside
                nx, ny = rng.randint(2, 4), rng.randint(2, 3)
                for i in range(1, nx):
                    xx = x0 + w * i / nx
                    line(xx, y0 + 0.04, xx, y1 - 0.04)
                for j in range(1, ny):
                    yy = y0 + h * j / ny
                    line(x0 + 0.04, yy, x1 - 0.04, yy)
            return
        t = rng.uniform(0.34, 0.66)
        if vertical:
            m = x0 + w * t
            split(x0, y0, m - gap / 2, y1, depth - 1, not vertical)
            split(m + gap / 2, y0, x1, y1, depth - 1, not vertical)
        else:
            m = y0 + h * t
            split(x0, y0, x1, m - gap / 2, depth - 1, not vertical)
            split(x0, m + gap / 2, x1, y1, depth - 1, not vertical)

    split(-half, -half, half, half, 4, True)
    ob = bpy.data.objects.new("floorplan", cu)
    sc.collection.objects.link(ob)
    cu.materials.append(M_PLAN)
    return ob


board()
traces()
package()
floorplan()


# ------------------------------------------------------------------ lights
def area(name, loc, size, energy, hexc="#ffffff", shape="RECTANGLE", sy=None, aim=(0, 0, 0.2)):
    L = M.light("AREA", loc, energy, hexc, size, name, aim)
    L.data.shape = shape
    if sy is not None:
        L.data.size_y = sy
    return L


area("key", (-3.5, -3.0, 6.0), 6.0, 520)
# rim: low and soft. It sits in the mirror direction of the mid-move camera, so a hot one clips the die
area("rim", (0.0, 6.0, 1.6), 5.0, 120, "#dfe8ff", sy=1.0, aim=(0, 0, 0.2))
area("fill", (5.0, -4.5, 1.2), 3.0, 60, "#ffe8d8")
# gradient softbox behind and above the chip, seen only in reflections (camera ray off): the lid and
# the black glass die pick up a soft bright-to-black gradient from the final three-quarter view.
# Off during the macro so that stays moody.
def softbox(name, loc, size, peak, aim=(0, 0, 0.2)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    card = bpy.context.object
    card.name = name
    card.scale = (size[0], size[1], 1)
    c = card.constraints.new("TRACK_TO")
    e = bpy.data.objects.new(name + " aim", None)
    sc.collection.objects.link(e)
    e.location = aim
    c.target = e
    c.track_axis, c.up_axis = "TRACK_Z", "UP_Y"
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    gr = nt.nodes.new("ShaderNodeTexGradient")
    gr.gradient_type = "QUADRATIC"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(90))   # ramp along the card's height
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], gr.inputs["Vector"])
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    nt.links.new(gr.outputs["Fac"], mul.inputs[0])
    strength = keyed_value(nt, "softbox", [(0.0, 0.0), (1.5, 0.0), (3.2, peak)], "inout")
    nt.links.new(strength, mul.inputs[1])
    nt.links.new(mul.outputs[0], em.inputs["Strength"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    card.data.materials.append(m)
    card.visible_camera = False
    card.visible_shadow = False
    return card


softbox("softbox", (0.0, 9.5, 8.0), (11.0, 5.0), 2.6)
sweep = area("sweep", (-7.0, -1.0, 4.2), 9.0, 1600, "#ffffff", sy=0.12, aim=(0, 0, 0.2))
sweep.constraints.clear()
sweep.rotation_euler = (math.radians(14), 0, math.radians(90))
M.key(sweep, "location", [[0.0, (-6.5, -1.2, 4.2)], [1.9, (6.5, -1.2, 4.2)]], "inout")
M.key(sweep.data, "energy", [[0.0, 0.0], [0.25, 1600.0], [1.6, 1600.0], [2.0, 200.0]], "lin")


# ------------------------------------------------------------------ camera
tgt = bpy.data.objects.new("focus", None)
sc.collection.objects.link(tgt)
M.key(tgt, "location", [[0.0, (1.48, -1.52, 0.24)], [1.55, (0.85, -0.95, 0.2)], [3.85, (0.0, 0.55, 0.12)]], "inout")
cdata = bpy.data.cameras.new("CAM")
cam = bpy.data.objects.new("CAM", cdata)
sc.collection.objects.link(cam)
sc.camera = cam
tt = cam.constraints.new("TRACK_TO")
tt.target = tgt
tt.track_axis, tt.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
M.key(cam, "location", [[0.0, (2.35, -2.62, 0.43)], [1.55, (3.0, -4.6, 1.75)], [3.85, (0.3, -8.3, 7.3)]], "inout")
cdata.sensor_width = 36
cdata.dof.use_dof = True
cdata.dof.focus_object = tgt
M.key(cdata, "lens", [[0.0, 62.0], [3.85, 42.0]], "inout")
M.key(cdata, "dof.aperture_fstop", [[0.0, 1.4], [1.55, 2.4], [3.85, 6.0]], "inout")


# ------------------------------------------------------------------ render
if PREVIEW:
    sc.render.resolution_percentage = PREVIEW.get("pct", 50)
    sc.cycles.samples = PREVIEW.get("samples", 24)
    for f in PREVIEW.get("frames", [1, 30, 60, 78]):
        M.render_still(os.path.join(OUT, "preview_%03d.png" % f), frame=f)
else:
    # the email GIF is 640x360: 960x540 keeps headroom for the comp's push-ins at a third of the cost
    sc.render.resolution_percentage = 75
    sc.cycles.samples = 40
    M.render_sequence(OUT)
