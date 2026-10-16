"""mta3d - Blender helpers for the 3D parts of a sneak peek (headless, bpy).

Replaces what the After Effects toolkit did with the Cinema 4D renderer (`MTA.ernst`,
`MTA.extrude3d`, `MTA.rig3`): real extruded, bevelled type and logos, lit and rendered with motion
blur and depth of field, written as an RGBA PNG sequence that EffectCraft imports as footage.

Coordinates: Blender units. `cam()` puts the camera on -Y looking at +Y, so X is screen right and
Z is screen up; `text3d()` and `svg3d()` stand objects up in the XZ plane facing it. Times are seconds; `key()`
converts to frames with the scene fps.

Every function works the same under the MCP server (`blender_mcp/server.py`) and in a plain
`python -c "import bpy"` / `blender -b -P` run.
"""
import math
import os

import bpy

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "fonts")
# Same faces as lib_mta.jsx's MTA.F: Inter Display (fonts-inter) when installed, else the bundled Inter.
DISPLAY = {"black": "InterDisplay-Black.otf", "heavy": "InterDisplay-ExtraBold.otf", "bold": "InterDisplay-Bold.otf",
           "semi": "InterDisplay-SemiBold.otf", "med": "InterDisplay-Medium.otf", "reg": "InterDisplay-Regular.otf"}
FONTS = {"black": "Inter-Bold.ttf", "heavy": "Inter-Bold.ttf", "bold": "Inter-Bold.ttf", "semi": "Inter-SemiBold.ttf",
         "med": "Inter-Medium.ttf", "reg": "Inter-Regular.ttf"}
FONT_SEARCH = ["/usr/share/fonts/opentype/inter", os.path.expanduser("~/Library/Fonts"), "/Library/Fonts"]


def _scene():
    return bpy.context.scene


def hex2lin(h, alpha=1.0):
    """'#ffcd19' -> linear RGBA tuple (Blender colours are linear)."""
    h = str(h).lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (out[0], out[1], out[2], alpha)


def reset(width=1280, height=720, fps=20, duration=5.0, transparent=True, samples=48):
    """Empty scene with the MTA defaults. Cycles on the CPU: EEVEE needs a GPU/EGL and is ~15x slower
    on a software rasteriser, so Cycles is the headless default."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        import addon_utils
        addon_utils.enable("cycles", default_set=True)
    except Exception:
        pass
    sc = _scene()
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = width, height, 100
    sc.render.fps = fps
    sc.frame_start, sc.frame_end = 1, max(1, int(round(duration * fps)))
    sc.render.film_transparent = transparent
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5  # 180 degrees, as the AE comps
    sc.view_settings.view_transform = "Standard"  # brand colours stay brand colours (no Filmic/AgX shift)
    if sc.world is None:
        sc.world = bpy.data.worlds.new("World")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0, 0, 0, 1)
        bg.inputs[1].default_value = 0.0
    return sc


def sec(t):
    """seconds -> frame number (frame 1 is t=0)."""
    return 1 + t * _scene().render.fps


def mat(name, hex_color, metallic=0.0, roughness=0.35, emission=0.0, emission_hex=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = hex2lin(hex_color)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = roughness
    if emission:
        p.inputs["Emission Color"].default_value = hex2lin(emission_hex or hex_color)
        p.inputs["Emission Strength"].default_value = emission
    return m


def _font(style):
    """'semi' / 'black'... (Inter Display if installed, else bundled Inter) or a path to a brand font."""
    path = None
    if style in DISPLAY:
        for d in FONT_SEARCH:
            if os.path.exists(os.path.join(d, DISPLAY[style])):
                path = os.path.join(d, DISPLAY[style])
                break
        path = path or os.path.join(FONT_DIR, FONTS[style])
    else:
        path = style
    key = os.path.abspath(path)
    for f in bpy.data.fonts:
        if f.filepath and os.path.abspath(bpy.path.abspath(f.filepath)) == key:
            return f
    return bpy.data.fonts.load(key)


def text3d(body, size=1.0, extrude=0.12, bevel=0.012, font="black", face=None, side=None, loc=(0, 0, 0), name=None, spacing=1.0):
    """Extruded, bevelled type standing upright facing the camera. face/side: material or hex."""
    cu = bpy.data.curves.new(name or ("txt " + body[:16]), "FONT")
    cu.body = body
    cu.font = _font(font)
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = 3
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.space_character = spacing
    ob = bpy.data.objects.new(cu.name, cu)
    _scene().collection.objects.link(ob)
    ob.rotation_euler = (math.radians(90), 0, 0)  # XY curve plane -> XZ (facing -Y, the camera)
    ob.location = loc
    _assign(ob, face, side)
    return ob


def svg3d(path, height=1.0, extrude=0.06, bevel=0.004, face=None, side=None, loc=(0, 0, 0), name="logo"):
    """Import an SVG logo, join it, centre it, scale it to `height` units and extrude it."""
    before = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=os.path.abspath(path))
    objs = [o for o in bpy.data.objects if o not in before and o.type == "CURVE"]
    if not objs:
        raise RuntimeError("no curves in " + path)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.extrude = extrude
    ob.data.bevel_depth = bevel
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    dims = ob.dimensions
    s = height / max(dims.y, 1e-6)
    ob.scale = (s, s, s)
    ob.rotation_euler = (math.radians(90), 0, 0)
    ob.location = loc
    for c in list(ob.users_collection):
        if c != _scene().collection:
            c.objects.unlink(ob)
    if ob.name not in _scene().collection.objects:
        _scene().collection.objects.link(ob)
    _assign(ob, face, side)
    return ob


def _assign(ob, face, side):
    """face material on the caps; side material (optional) on the extrusion and bevel. Curves can't hold a
    separate side material, so with `side` the object is converted to a mesh (bake animation on the object,
    not the curve data)."""
    fm = face if isinstance(face, bpy.types.Material) else mat(ob.name + " face", face or "#ffffff")
    ob.data.materials.append(fm)
    if side is None:
        return ob
    sm = side if isinstance(side, bpy.types.Material) else mat(ob.name + " side", side)
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob.data.materials.append(sm)
    for poly in ob.data.polygons:  # caps face local +-Z (the curve plane normal)
        poly.material_index = 0 if abs(poly.normal.z) > 0.95 else 1
    return ob


def plane(w, h, hex_color="#000000", loc=(0, 0, 0), name="plane", emission=0.0, shadow_catcher=False):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (w, h, 1)
    ob.data.materials.append(mat(name, hex_color, emission=emission))
    if shadow_catcher:
        ob.is_shadow_catcher = True
    return ob


def cam(dist=10.0, lens=50.0, target=(0, 0, 0), name="CAM", dof_fstop=None):
    """Camera on -Y looking at target. Returns the camera; animate .location / .data.lens with key()."""
    data = bpy.data.cameras.new(name)
    data.lens = lens
    ob = bpy.data.objects.new(name, data)
    _scene().collection.objects.link(ob)
    ob.location = (target[0], target[1] - dist, target[2])
    ob.rotation_euler = (math.radians(90), 0, 0)
    _scene().camera = ob
    if dof_fstop:
        data.dof.use_dof = True
        data.dof.focus_distance = dist
        data.dof.aperture_fstop = dof_fstop
    return ob


def light(kind="AREA", loc=(0, -4, 4), energy=600, hex_color="#ffffff", size=3.0, name=None, aim=(0, 0, 0)):
    data = bpy.data.lights.new(name or kind.lower(), kind)
    data.energy = energy
    data.color = hex2lin(hex_color)[:3]
    if kind == "AREA":
        data.size = size
    ob = bpy.data.objects.new(data.name, data)
    _scene().collection.objects.link(ob)
    ob.location = loc
    c = ob.constraints.new("TRACK_TO")
    e = bpy.data.objects.new(ob.name + " aim", None)
    _scene().collection.objects.link(e)
    e.location = aim
    c.target = e
    c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    return ob


def rig3(rim_hex="#ffffff", key=900, rim=700, fill=0.15):
    """Key top-left, coloured rim behind-right, soft world fill: the AE MTA.rig3 look."""
    light("AREA", (-4, -6, 5), key, "#ffffff", 4, "key")
    light("AREA", (5, 4, -1.5), rim, rim_hex, 3, "rim")
    w = _scene().world.node_tree.nodes.get("Background")
    if w:
        w.inputs[0].default_value = (1, 1, 1, 1)
        w.inputs[1].default_value = fill


def key(obj, path, keys, ease="out", index=-1):
    """keys = [[t_seconds, value], ...]. ease: out | in | inout | lin | snap (bezier handles like MTA.k)."""
    for t, v in keys:
        setattr_path(obj, path, v)
        obj.keyframe_insert(data_path=path, frame=sec(t), index=index)
    ad = obj.animation_data
    if not ad or not ad.action:
        return obj
    for fc in _fcurves(ad.action, path):
        for kp in fc.keyframe_points:
            if ease == "lin":
                kp.interpolation = "LINEAR"
                continue
            kp.interpolation = "BEZIER"
            kp.handle_left_type = kp.handle_right_type = "FREE"
        _ease(fc, ease)
    return obj


def _fcurves(action, path):
    if hasattr(action, "fcurves") and action.fcurves is not None:
        try:
            return [fc for fc in action.fcurves if fc.data_path == path]
        except Exception:
            pass
    out = []  # Blender 5 layered actions
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                out += [fc for fc in bag.fcurves if fc.data_path == path]
    return out


def _ease(fc, ease):
    """Flat (zero-speed) handles with After Effects-style influence, as MTA.k: every key gets the same
    incoming / outgoing influence (fraction of the interval)."""
    inf_in, inf_out = {"out": (0.88, 0.12), "in": (0.15, 0.85), "inout": (0.72, 0.72), "snap": (0.96, 0.08)}.get(ease, (0.8, 0.2))
    pts = fc.keyframe_points
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        dx = b.co.x - a.co.x
        a.handle_right = (a.co.x + dx * inf_out, a.co.y)
        b.handle_left = (b.co.x - dx * inf_in, b.co.y)


def setattr_path(obj, path, v):
    tgt = obj
    parts = path.split(".")
    for p in parts[:-1]:
        tgt = getattr(tgt, p)
    setattr(tgt, parts[-1], v)


def info():
    sc = _scene()
    return {"blender": bpy.app.version_string, "engine": sc.render.engine, "fps": sc.render.fps,
            "frames": [sc.frame_start, sc.frame_end], "resolution": [sc.render.resolution_x, sc.render.resolution_y],
            "transparent": sc.render.film_transparent, "camera": sc.camera.name if sc.camera else None,
            "objects": [{"name": o.name, "type": o.type, "loc": [round(x, 3) for x in o.location]} for o in sc.objects]}


def render_still(path, frame=None, samples=None):
    sc = _scene()
    if frame is not None:
        sc.frame_set(frame)
    if samples:
        sc.cycles.samples = samples
    sc.render.filepath = os.path.abspath(path)
    bpy.ops.render.render(write_still=True)
    return path


def render_sequence(out_dir, start=None, end=None, samples=None):
    """RGBA PNG sequence out_dir/f_0001.png... EffectCraft: file.import the first frame (sequence=true)."""
    sc = _scene()
    os.makedirs(out_dir, exist_ok=True)
    if start is not None:
        sc.frame_start = start
    if end is not None:
        sc.frame_end = end
    if samples:
        sc.cycles.samples = samples
    sc.render.filepath = os.path.join(os.path.abspath(out_dir), "f_")
    bpy.ops.render.render(animation=True)
    return sorted(os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.startswith("f_") and f.endswith(".png"))
