// lib_mta.jsx - low-level helpers for bespoke sneak-peek comps (shapes, text, easing, extrude, logo, button, camera).
// No scene structure lives here: every company builds its own scene from these pieces. ES3 only (ExtendScript).
var MTA = MTA || {};
MTA.W = 1280; MTA.H = 720; MTA.FPS = 20; MTA.DUR = 5;
// EffectCraft port: SF Pro is macOS-only and an unknown name falls back to Inter *Regular*, which
// silently flattens every weight. Inter Display (fonts-inter; scripts/setup.sh installs it) is the
// closest open match to SF Pro Display. Inter (no "Display") is bundled with EffectCraft.
MTA.F = { black: "InterDisplay-Black", heavy: "InterDisplay-ExtraBold", bold: "InterDisplay-Bold", semi: "InterDisplay-SemiBold",
          med: "InterDisplay-Medium", reg: "InterDisplay-Regular", round: "InterDisplay-Black", mono: "JetBrainsMono-Regular" };
// ROOT / BRAND / OUT3D / COMP are set by the sneakpeek runner (sneakpeek/cli.py) before scene.jsx runs.
MTA.ROOT = MTA.ROOT || ""; MTA.BRAND = MTA.BRAND || ""; MTA.OUT3D = MTA.OUT3D || "";
MTA.findComp = function (name) {
    for (var i = 1; i <= app.project.numItems; i++) { var it = app.project.item(i); if (it instanceof CompItem && it.name === name) { return it; } }
    return null;
};
// Import a rendered PNG sequence (a Blender pass: out/3d/<name>/f_0001.png...) as one footage item at the comp rate.
MTA.sequence = function (comp, firstFrame, width, pos) {
    var io = new ImportOptions(new File(firstFrame)); io.sequence = true;
    var it = app.project.importFile(io); it.mainSource.conformFrameRate = MTA.FPS;
    var l = comp.layers.add(it);
    var s = (width || MTA.W) / it.width * 100; MTA.P(l, "scale").setValue([s, s]); MTA.P(l, "pos").setValue(pos || [MTA.W / 2, MTA.H / 2]);
    l.name = "seq " + it.name;
    return l;
};

MTA.hex = function (h) {
    h = String(h).replace("#", "");
    if (h.length === 3) { h = h.charAt(0) + h.charAt(0) + h.charAt(1) + h.charAt(1) + h.charAt(2) + h.charAt(2); }
    return [parseInt(h.substr(0, 2), 16) / 255, parseInt(h.substr(2, 2), 16) / 255, parseInt(h.substr(4, 2), 16) / 255];
};
MTA.mix = function (h, k, toHex) { // mix colour h towards toHex (default black) by k (0..1)
    var a = MTA.hex(h), b = MTA.hex(toHex || "#000000"), o = [];
    for (var i = 0; i < 3; i++) { o.push(Math.round((a[i] * (1 - k) + b[i] * k) * 255)); }
    var s = "#"; for (var j = 0; j < 3; j++) { var x = o[j].toString(16); s += (x.length < 2 ? "0" : "") + x; }
    return s;
};

MTA.newComp = function (name, bgHex, dur) {
    for (var i = app.project.numItems; i >= 1; i--) { var it = app.project.item(i); if (it instanceof CompItem && it.name === name) { it.remove(); } }
    var c = app.project.items.addComp(name, MTA.W, MTA.H, 1, dur || MTA.DUR, MTA.FPS);
    c.bgColor = MTA.hex(bgHex || "#ffffff");
    c.motionBlur = true; c.shutterAngle = 180; c.shutterPhase = -90;
    return c;
};

MTA.T = function (l) { return l.property("ADBE Transform Group"); };
MTA.P = function (l, name) {
    var t = MTA.T(l);
    var map = { pos: "ADBE Position", scale: "ADBE Scale", rot: "ADBE Rotate Z", op: "ADBE Opacity", anchor: "ADBE Anchor Point" };
    return t.property(map[name] || name);
};

MTA.solid = function (comp, hex, name) {
    var l = comp.layers.addSolid(MTA.hex(hex), name || "bg", MTA.W, MTA.H, 1, comp.duration);
    return l;
};
// Linear or radial ramp on a solid: o = {from:[x,y], to:[x,y], c1, c2, radial}
MTA.ramp = function (layer, o) {
    var fx = layer.property("ADBE Effect Parade").addProperty("ADBE Ramp");
    fx.property("ADBE Ramp-0001").setValue(o.from || [0, 0]);
    fx.property("ADBE Ramp-0002").setValue(MTA.hex(o.c1));
    fx.property("ADBE Ramp-0003").setValue(o.to || [MTA.W, MTA.H]);
    fx.property("ADBE Ramp-0004").setValue(MTA.hex(o.c2));
    fx.property("ADBE Ramp-0005").setValue(o.radial ? 2 : 1);
    return fx;
};

MTA.glowBlob = function (comp, hex, center, radius, opacity) {
    var l = MTA.solid(comp, "#000000", "glow " + hex);
    MTA.ramp(l, { from: center, to: [center[0] + radius, center[1]], c1: hex, c2: "#000000", radial: true });
    l.blendingMode = BlendingMode.SCREEN;
    MTA.P(l, "op").setValue(opacity == null ? 100 : opacity);
    return l;
};
// lay out buttons side by side, centred on cx, gap px apart
MTA.row = function (btns, cx, y, gap) {
    var tot = 0, i; for (i = 0; i < btns.length; i++) { tot += parseFloat(btns[i].comment); } tot += gap * (btns.length - 1);
    var x = cx - tot / 2;
    for (i = 0; i < btns.length; i++) { var w = parseFloat(btns[i].comment); MTA.P(btns[i], "pos").setValue([x + w / 2, y]); x += w + gap; }
};
MTA.inheritOpacity = function (l) { MTA.P(l, "op").expression = "parent.transform.opacity"; };
MTA._group = function (layer, name) {
    var g = layer.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group");
    g.name = name || "g";
    return g;
};
MTA._paint = function (gc, o) {
    if (o.fill) {
        var f = gc.addProperty("ADBE Vector Graphic - Fill");
        f.property("ADBE Vector Fill Color").setValue(MTA.hex(o.fill));
        if (o.fillOpacity != null) { f.property("ADBE Vector Fill Opacity").setValue(o.fillOpacity); }
    }
    if (o.stroke) {
        var s = gc.addProperty("ADBE Vector Graphic - Stroke");
        s.property("ADBE Vector Stroke Color").setValue(MTA.hex(o.stroke));
        s.property("ADBE Vector Stroke Width").setValue(o.sw || 6);
        s.property("ADBE Vector Stroke Line Cap").setValue(2); // round
        s.property("ADBE Vector Stroke Line Join").setValue(2);
    }
};
// Rounded rectangle centred on the layer position. o = {name, w, h, r, fill, stroke, sw, pos}
MTA.rect = function (comp, o) {
    var l = comp.layers.addShape(); l.name = o.name || "rect";
    var g = MTA._group(l, "r"), gc = g.property("ADBE Vectors Group");
    var rr = gc.addProperty("ADBE Vector Shape - Rect");
    rr.property("ADBE Vector Rect Size").setValue([o.w, o.h]);
    rr.property("ADBE Vector Rect Roundness").setValue(o.r || 0);
    MTA._paint(gc, o);
    MTA.P(l, "pos").setValue(o.pos || [640, 360]);
    return l;
};
MTA.ellipse = function (comp, o) {
    var l = comp.layers.addShape(); l.name = o.name || "ellipse";
    var g = MTA._group(l, "e"), gc = g.property("ADBE Vectors Group");
    var e = gc.addProperty("ADBE Vector Shape - Ellipse");
    e.property("ADBE Vector Ellipse Size").setValue([o.w, o.h || o.w]);
    MTA._paint(gc, o);
    MTA.P(l, "pos").setValue(o.pos || [640, 360]);
    return l;
};
// Polyline / polygon. o = {pts:[[x,y]...] (layer space, around 0,0), closed, fill, stroke, sw, pos, trim:true}
MTA.path = function (comp, o) {
    var l = comp.layers.addShape(); l.name = o.name || "path";
    var g = MTA._group(l, "p"), gc = g.property("ADBE Vectors Group");
    var pp = gc.addProperty("ADBE Vector Shape - Group");
    var sh = new Shape(); sh.vertices = o.pts; sh.closed = !!o.closed;
    if (o.inT) { sh.inTangents = o.inT; } if (o.outT) { sh.outTangents = o.outT; }
    pp.property("ADBE Vector Shape").setValue(sh);
    if (o.trim) { gc.addProperty("ADBE Vector Filter - Trim"); }
    MTA._paint(gc, o);
    MTA.P(l, "pos").setValue(o.pos || [0, 0]);
    return l;
};
MTA.trimEnd = function (l) { return l.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group").property("ADBE Vector Filter - Trim").property("ADBE Vector Trim End"); };

// Text. o = {text, font, size, color, just:'L'|'C'|'R', tracking, leading, pos, center:true}
MTA.text = function (comp, o) {
    var l = comp.layers.addText(o.text);
    l.name = o.name || String(o.text).substr(0, 24);
    var st = l.property("ADBE Text Properties").property("ADBE Text Document");
    var td = st.value;
    td.resetCharStyle(); td.resetParagraphStyle();
    td.font = o.font || MTA.F.black; td.fontSize = o.size || 100;
    td.applyFill = true; td.fillColor = MTA.hex(o.color || "#111111"); td.applyStroke = false;
    td.justification = o.just === "C" ? ParagraphJustification.CENTER_JUSTIFY : (o.just === "R" ? ParagraphJustification.RIGHT_JUSTIFY : ParagraphJustification.LEFT_JUSTIFY);
    td.tracking = o.tracking || 0;
    if (o.leading) { td.autoLeading = false; td.leading = o.leading; }
    if (o.caps) { try { td.allCaps = true; } catch (eCaps) {} }
    st.setValue(td);
    if (o.center) { MTA.centerAnchor(l); }
    MTA.P(l, "pos").setValue(o.pos || [640, 360]);
    return l;
};
MTA.setTextColor = function (l, hex) {
    var st = l.property("ADBE Text Properties").property("ADBE Text Document"); var td = st.value; td.fillColor = MTA.hex(hex); st.setValue(td);
};
MTA.centerAnchor = function (l) {
    var r = l.sourceRectAtTime(0, false);
    MTA.P(l, "anchor").setValue([r.left + r.width / 2, r.top + r.height / 2]);
    return r;
};

// --- keyframes with ease. keys = [[t, v], ...]; ease = 'out' (decelerate), 'in', 'inout', 'snap' (hard decel), 'lin'
MTA.dims = function (p) {
    var t = p.propertyValueType;
    if (t === PropertyValueType.TwoD_SPATIAL || t === PropertyValueType.ThreeD_SPATIAL) { return 1; }
    if (t === PropertyValueType.TwoD) { return 2; }
    if (t === PropertyValueType.ThreeD) { return 3; }
    return 1;
};
MTA.k = function (prop, keys, ease) {
    var start = prop.numKeys;
    for (var i = 0; i < keys.length; i++) { prop.setValueAtTime(keys[i][0], keys[i][1]); }
    if (ease === "lin" || prop.propertyValueType === PropertyValueType.COLOR) { return prop; }
    var d = MTA.dims(prop);
    var infIn = { out: 88, "in": 15, inout: 72, snap: 96 }[ease || "out"] || 80;
    var infOut = { out: 12, "in": 85, inout: 72, snap: 8 }[ease || "out"] || 20;
    for (var j = 1; j <= prop.numKeys; j++) {
        var ei = [], eo = [];
        for (var n = 0; n < d; n++) { ei.push(new KeyframeEase(0, infIn)); eo.push(new KeyframeEase(0, infOut)); }
        try { prop.setTemporalEaseAtKey(j, ei, eo); } catch (e) {}
        if (prop.isSpatial) { try { prop.setSpatialAutoBezierAtKey(j, false); prop.setSpatialContinuousAtKey(j, false); } catch (e2) {} }
    }
    return prop;
};
// scale pop with overshoot: 0 -> over -> to
MTA.pop = function (l, t, dur, to, over) {
    to = to || 100; over = over || to * 1.12;
    MTA.k(MTA.P(l, "scale"), [[t, [0, 0]], [t + dur * 0.62, [over, over]], [t + dur, [to, to]]], "inout");
    return l;
};
MTA.fade = function (l, t0, t1, a, b) { MTA.k(MTA.P(l, "op"), [[t0, a == null ? 0 : a], [t1, b == null ? 100 : b]], "lin"); };
MTA.hideUntil = function (l, t) { l.inPoint = t; };
MTA.hideAfter = function (l, t) { l.outPoint = t; };

// Fake extrusion: stacked darker copies parented to the face layer. Strips copied keyframes from the copies.
MTA.extrude = function (face, depth, sideHex, step, angleDeg) {
    step = step || 1.6; var a = (angleDeg == null ? 45 : angleDeg) * Math.PI / 180;
    var anchor = MTA.P(face, "anchor").value, prev = face, copies = [];
    for (var i = 1; i <= depth; i++) {
        var d = face.duplicate();
        d.name = face.name + " ex" + i;
        var props = ["pos", "scale", "rot", "op"];
        for (var p = 0; p < props.length; p++) { var pr = MTA.P(d, props[p]); while (pr.numKeys > 0) { pr.removeKey(1); } if (pr.expressionEnabled) { pr.expression = ""; } }
        d.parent = face;
        MTA.P(d, "pos").setValue([anchor[0] + Math.cos(a) * step * i, anchor[1] + Math.sin(a) * step * i]);
        MTA.P(d, "scale").setValue([100, 100]); MTA.P(d, "rot").setValue(0);
        MTA.P(d, "op").expression = "parent.transform.opacity";
        var shade = MTA.mix(sideHex, (i / depth) * 0.35);
        if (d.property("ADBE Text Properties")) { MTA.setTextColor(d, shade); }
        else { MTA.recolorShape(d, shade); }
        d.inPoint = face.inPoint; d.outPoint = face.outPoint;
        d.moveAfter(prev); prev = d; copies.push(d);
    }
    return copies;
};
MTA.recolorShape = function (l, hex) {
    var walk = function (grp) {
        for (var i = 1; i <= grp.numProperties; i++) {
            var p = grp.property(i);
            if (p.matchName === "ADBE Vector Graphic - Fill") { p.property("ADBE Vector Fill Color").setValue(MTA.hex(hex)); }
            else if (p.matchName === "ADBE Vector Graphic - Stroke") { p.property("ADBE Vector Stroke Color").setValue(MTA.hex(hex)); }
            else if (p.numProperties) { walk(p); }
        }
    };
    walk(l.property("ADBE Root Vectors Group"));
};
// Soft drop shadow (keeps things dimensional on light backgrounds)
MTA.shadow = function (l, opacity, dist, soft, hex) {
    var fx = l.property("ADBE Effect Parade").addProperty("ADBE Drop Shadow");
    fx.property("ADBE Drop Shadow-0001").setValue(MTA.hex(hex || "#000000"));
    fx.property("ADBE Drop Shadow-0002").setValue((opacity == null ? 35 : opacity) * 2.55);
    fx.property("ADBE Drop Shadow-0003").setValue(135);
    fx.property("ADBE Drop Shadow-0004").setValue(dist == null ? 18 : dist);
    fx.property("ADBE Drop Shadow-0005").setValue(soft == null ? 40 : soft);
    return fx;
};
MTA.glow = function (l, radius, intensity) {
    var fx = l.property("ADBE Effect Parade").addProperty("ADBE Glo2");
    fx.property("ADBE Glo2-0003").setValue(radius || 60);
    fx.property("ADBE Glo2-0004").setValue(intensity || 1.2);
    return fx;
};

// Images
MTA.importImg = function (path) {
    var f = new File(path); if (!f.exists) { throw new Error("missing image " + path); }
    var it = app.project.importFile(new ImportOptions(f));
    return it;
};
MTA.image = function (comp, path, width, pos) {
    var it = MTA.importImg(path); var l = comp.layers.add(it);
    var s = width / it.width * 100; MTA.P(l, "scale").setValue([s, s]); MTA.P(l, "pos").setValue(pos || [640, 360]);
    l.name = "img " + it.name;
    return l;
};

// Button in the brand's own CTA style. o = {text, bg, fg, border, radius, h, padX, font, size, pos}
MTA.button = function (comp, o) {
    var t = MTA.text(comp, { text: o.text, font: o.font || MTA.F.semi, size: o.size || 34, color: o.fg || "#ffffff", just: "C", tracking: o.tracking || 0, caps: o.caps, center: true, pos: [0, 0] });
    var r = t.sourceRectAtTime(0, false);
    var w = Math.round(r.width + (o.padX || 56) * 2), h = o.h || 86;
    var b = MTA.rect(comp, { name: "btn " + o.text, w: w, h: h, r: o.radius == null ? 14 : o.radius, fill: o.bg, stroke: o.border, sw: o.borderW || 3, pos: o.pos || [640, 520] });
    t.parent = b; MTA.P(t, "pos").setValue([0, 2]);
    t.moveBefore(b);
    MTA.P(t, "op").expression = "parent.transform.opacity";
    b.comment = String(w);
    return b;
};

// Camera rig: a null everything scene-level parents to; animate its position/scale for pushes and whips.
MTA.camRig = function (comp) {
    var n = comp.layers.addNull(comp.duration); n.name = "CAM";
    MTA.P(n, "anchor").setValue([0, 0]); MTA.P(n, "pos").setValue([0, 0]); // identity while attaching; move it afterwards
    return n;
};
MTA.attach = function (layers, cam) {
    for (var i = 0; i < layers.length; i++) { if (!layers[i].parent && layers[i] !== cam) { layers[i].parent = cam; } }
};
// Directional blur adjustment layer for whip-pans: windows = [[t0, t1, length]]
MTA.whipBlur = function (comp, windows, angle) {
    var a = comp.layers.addSolid([1, 1, 1], "whip blur", MTA.W, MTA.H, 1, comp.duration);
    a.adjustmentLayer = true;
    var fx = a.property("ADBE Effect Parade").addProperty("ADBE Motion Blur");
    fx.property("ADBE Motion Blur-0001").setValue(angle == null ? 90 : angle);
    var len = fx.property("ADBE Motion Blur-0002");
    for (var i = 0; i < windows.length; i++) {
        var w = windows[i], mid = (w[0] + w[1]) / 2;
        len.setValueAtTime(w[0], 0); len.setValueAtTime(mid, w[2]); len.setValueAtTime(w[1], 0);
    }
    a.moveToBeginning();
    return a;
};
MTA.motionBlurAll = function (comp) {
    for (var i = 1; i <= comp.numLayers; i++) { var l = comp.layer(i); if (!(l instanceof AVLayer) && !(l instanceof ShapeLayer) && !(l instanceof TextLayer)) { continue; } if (l.adjustmentLayer) { continue; } try { l.motionBlur = true; } catch (e) {} }
};

// Render comp to a lossless .mov in-app (fresh queue item each time; only this item renders).
MTA.render = function (comp, movPath, template) {
    var rq = app.project.renderQueue;
    for (var i = rq.numItems; i >= 1; i--) { var it = rq.item(i); if (it.status !== RQItemStatus.RENDERING) { it.remove(); } }
    var item = rq.items.add(comp);
    var om = item.outputModule(1);
    om.applyTemplate(template || "Lossless");
    var f = new File(movPath); if (f.exists) { f.remove(); }
    om.file = f;
    rq.render();
    return item.status;
};

// Typewriter via hold-keyframed Source Text (one key per character group)
MTA.typeOn = function (l, full, t0, t1, cursor) {
    var st = l.property("ADBE Text Properties").property("ADBE Text Document");
    var n = full.length, steps = Math.max(1, Math.round((t1 - t0) * MTA.FPS));
    for (var i = 0; i <= steps; i++) {
        var k = Math.round(n * i / steps); var td = st.value;
        td.text = full.substr(0, k) + (cursor && i < steps ? "|" : "") ; if (td.text === "") { td.text = " "; }
        st.setValueAtTime(t0 + i / MTA.FPS, td);
    }
};
// Number counter (hold keys). fmt(n) -> string
MTA.counter = function (l, from, to, t0, t1, fmt, ease) {
    var st = l.property("ADBE Text Properties").property("ADBE Text Document");
    var steps = Math.max(1, Math.round((t1 - t0) * MTA.FPS));
    for (var i = 0; i <= steps; i++) {
        var u = i / steps; u = ease === "lin" ? u : 1 - Math.pow(1 - u, 3);
        var td = st.value; td.text = fmt(from + (to - from) * u); st.setValueAtTime(t0 + i / MTA.FPS, td);
    }
};
MTA.setText = function (l, t, str) { var st = l.property("ADBE Text Properties").property("ADBE Text Document"); var td = st.value; td.text = str; st.setValueAtTime(t, td); };
MTA.fillColorProp = function (l) { return l.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group").property("ADBE Vector Graphic - Fill").property("ADBE Vector Fill Color"); };
MTA.strokeColorProp = function (l) { return l.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group").property("ADBE Vector Graphic - Stroke").property("ADBE Vector Stroke Color"); };
MTA.colorKeys = function (prop, keys) { for (var i = 0; i < keys.length; i++) { prop.setValueAtTime(keys[i][0], MTA.hex(keys[i][1])); } };
// Tint a layer (logos) to one colour with the Fill effect
MTA.tint = function (l, hex) { var fx = l.property("ADBE Effect Parade").addProperty("ADBE Fill"); fx.property("ADBE Fill-0002").setValue(MTA.hex(hex)); return fx; };
MTA.kids = function (parent, arr) { for (var i = arr.length - 1; i >= 0; i--) { arr[i].parent = parent; arr[i].moveBefore(parent); MTA.P(arr[i], "op").expression = "parent.transform.opacity * value / 100"; } };

MTA.log = function (path, s) { var f = new File(path); f.open("w"); f.encoding = "UTF-8"; f.write(s); f.close(); };

// ---- premium helpers (v3, 15 Oct) ----
// sub-comp of any size (replaces an existing comp of the same name)
MTA.sub = function (name, w, h, dur, bgHex) {
    for (var i = app.project.numItems; i >= 1; i--) { var it = app.project.item(i); if (it instanceof CompItem && it.name === name) { it.remove(); } }
    var c = app.project.items.addComp(name, w || MTA.W, h || MTA.H, 1, dur || MTA.DUR, MTA.FPS);
    if (bgHex) { c.bgColor = MTA.hex(bgHex); }
    c.motionBlur = true; c.shutterAngle = 180; c.shutterPhase = -90;
    return c;
};
// a 1280x720 comp on the Cinema 4D renderer: the only renderer where text/shape extrusion works.
// EffectCraft has no Cinema 4D renderer (the comp stays Classic 3D) and no extrusion group, so
// MTA.extrude3d throws there: build extruded type in a Blender pass (sneakpeek/blender/mta3d.py).
MTA.ernst = function (name, dur) { var c = MTA.sub(name, MTA.W, MTA.H, dur); c.renderer = "ADBE Ernst"; return c; };
MTA.tf = function (l, matchName) { return l.property("ADBE Transform Group").property(matchName); };
// real extrusion + angular bevel on a text/shape layer inside an MTA.ernst comp; returns the transform group
MTA.extrude3d = function (l, depth, bevel) {
    l.threeDLayer = true;
    var g = l.property("ADBE Extrsn Options Group");
    g.property("ADBE Extrsn Depth").setValue(depth);
    if (bevel) { g.property("ADBE Bevel Styles").setValue(2); g.property("ADBE Bevel Depth").setValue(bevel); }
    return l.property("ADBE Transform Group");
};
MTA.light = function (comp, name, type, pos, inten, hex) {
    var L = comp.layers.addLight(name, [MTA.W / 2, MTA.H / 2]); L.lightType = type;
    L.property("ADBE Light Options Group").property("ADBE Light Intensity").setValue(inten);
    if (hex) { L.property("ADBE Light Options Group").property("ADBE Light Color").setValue(MTA.hex(hex)); }
    if (pos) { L.property("ADBE Transform Group").property("ADBE Position").setValue(pos); }
    return L;
};
// standard three-light rig: key top-left, coloured rim bottom-right, ambient
MTA.rig3 = function (comp, rimHex, key, rim, amb) {
    MTA.light(comp, "key", LightType.POINT, [300, 100, -700], key || 115);
    MTA.light(comp, "rim", LightType.POINT, [1100, 680, -260], rim || 80, rimHex || "#ffffff");
    MTA.light(comp, "amb", LightType.AMBIENT, null, amb || 32);
};
// character reveal: chars rise dy px and fade in left to right between t0 and t1
MTA.reveal = function (l, t0, t1, dy) {
    var an = l.property("ADBE Text Properties").property("ADBE Text Animators").addProperty("ADBE Text Animator");
    var pr = an.property("ADBE Text Animator Properties");
    pr.addProperty("ADBE Text Opacity").setValue(0);
    if (dy) { pr.addProperty("ADBE Text Position 3D").setValue([0, dy, 0]); }
    var sel = an.property("ADBE Text Selectors").addProperty("ADBE Text Selector");
    MTA.k(sel.property("ADBE Text Percent Start"), [[t0, 0], [t1, 100]], "out");
    return sel;
};
// ellipse size property (grow rings by size so strokes stay thin)
MTA.ringSize = function (l) { return l.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group").property("ADBE Vector Shape - Ellipse").property("ADBE Vector Ellipse Size"); };
// expanding ring: crisp stroke, no motion blur
MTA.ring = function (comp, o) {
    var r = MTA.ellipse(comp, { name: o.name || "ring", w: o.w0 || 20, stroke: o.color, sw: o.sw || 4, pos: o.pos });
    r.inPoint = o.t; r.outPoint = o.t + o.dur + 0.02;
    MTA.k(MTA.ringSize(r), [[o.t, [o.w0 || 20, o.w0 || 20]], [o.t + o.dur, [o.w1, o.w1]]], "out");
    MTA.k(MTA.P(r, "op"), [[o.t, o.op || 100], [o.t + o.dur, 0]], "lin");
    if (o.squash) { MTA.P(r, "scale").setValue([100, o.squash]); }
    if (o.glow) { MTA.glow(r, o.glow, 1.4); }
    r.motionBlur = false;
    return r;
};
// CC Light Sweep across a layer (logos, end cards)
MTA.sweep = function (l, t0, t1, y, width) {
    var sw = l.property("ADBE Effect Parade").addProperty("CC Light Sweep");
    try { sw.property("Direction").setValue(-30); sw.property("Width").setValue(width || 60); sw.property("Sweep Intensity").setValue(85); MTA.k(sw.property("Center"), [[t0, [-250, y]], [t1, [1550, y]]], "inout"); } catch (e) {}
    return sw;
};
// solid with a feathered rectangular mask (soft bands behind text, vignettes)
MTA.band = function (comp, hex, y0, y1, feather, op) {
    var s = MTA.solid(comp, hex, "band");
    var mk = s.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
    var sh = new Shape(); sh.vertices = [[-200, y0], [1480, y0], [1480, y1], [-200, y1]]; sh.closed = true;
    mk.property("ADBE Mask Shape").setValue(sh); mk.property("ADBE Mask Feather").setValue([0, feather || 80]);
    MTA.P(s, "op").setValue(op == null ? 85 : op);
    return s;
};
// cubic bezier arc between two points, lifted by `lift` px, drawn as a comet (trim start chases trim end)
MTA.arc = function (comp, o) {
    var S = o.from, E = o.to, dx = E[0] - S[0], dy = E[1] - S[1], lift = o.lift == null ? 80 : o.lift;
    var C1 = [S[0] + dx * 0.25, S[1] + dy * 0.25 - lift], C2 = [S[0] + dx * 0.75, S[1] + dy * 0.75 - lift];
    var a = MTA.path(comp, { name: o.name || "arc", pts: [S, E], outT: [[C1[0] - S[0], C1[1] - S[1]], [0, 0]], inT: [[0, 0], [C2[0] - E[0], C2[1] - E[1]]], stroke: o.color, sw: o.sw || 4, pos: [0, 0], trim: true });
    var tr = a.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group").property("ADBE Vector Filter - Trim");
    MTA.k(tr.property("ADBE Vector Trim End"), [[o.t, 0], [o.t + o.dur, 100]], "inout");
    if (o.comet !== false) { MTA.k(tr.property("ADBE Vector Trim Start"), [[o.t + o.dur * 0.3, 0], [o.t + o.dur + 0.12, 100]], "inout"); a.outPoint = o.t + o.dur + 0.14; }
    if (o.glow) { MTA.glow(a, o.glow, 1.5); }
    a.inPoint = o.t;
    return a;
};
