// Apple sneak peek (DEMO). One hero moment: a chip, lit like an Apple product film.
// A) 0.00-0.50  a hairline of light splits open on the macro: brushed aluminium, a specular sweep
// B) 0.50-2.55  one continuous pull-back (Blender pass 3d/chip.py): the traces light up from the package
//               outward in Apple's system palette, the die's floorplan glows last
// C) 2.55-3.60  "Think different." (Apple's own line) over the traces
// D) 3.55-3.95  the chip flares to white
// E) 3.80-5.00  end card: the line, Apple's "Learn more" / "Buy" pills, apple.com
// Look: black, #F5F5F7 type (Inter Display for SF Pro Display), system blue #0071E3 / link blue #2997FF.
// No Apple logo (a trademark glyph we don't redraw), no product names, no claims.
(function () {
    var BG = "#000000", INK = "#F5F5F7", GREY = "#86868B", BLUE = "#0071E3", LINK = "#2997FF";
    var CHIP = MTA.OUT3D + "chip/f_0001.png", LASTF = MTA.OUT3D + "chip/f_0078.png";
    var END = 3.8;

    var c = MTA.newComp(MTA.COMP, BG);
    MTA.solid(c, BG, "bg");

    // ---------- A/B) the 3D pass
    var chip = MTA.sequence(c, CHIP, MTA.W, [640, 360]);
    chip.name = "chip";
    chip.outPoint = 3.96;
    var s0 = MTA.P(chip, "scale").value[0];
    MTA.k(MTA.P(chip, "scale"), [[0, [s0, s0]], [3.45, [s0 * 1.035, s0 * 1.035]]], "inout");
    MTA.k(MTA.P(chip, "scale"), [[3.5, [s0 * 1.036, s0 * 1.036]], [3.9, [s0 * 1.16, s0 * 1.16]]], "in");
    MTA.glow(chip, 34, 0.55);                                  // bloom on speculars and the lit traces

    // the hairline open: a feathered band mask on the footage (layer space, 960x540 source)
    var src = chip.source, sw = src.width, sh = src.height, cy = sh / 2;
    var mk = chip.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
    var band = function (h) { var b = new Shape(); b.vertices = [[-40, cy - h], [sw + 40, cy - h], [sw + 40, cy + h], [-40, cy + h]]; b.closed = true; return b; };
    var mp = mk.property("ADBE Mask Shape");
    mp.setValueAtTime(0.05, band(0)); mp.setValueAtTime(0.5, band(sh * 0.36)); mp.setValueAtTime(0.75, band(sh * 0.75));
    mk.property("ADBE Mask Feather").setValue([0, 46]);
    var edges = [];
    for (var e = 0; e < 2; e++) {                                // the two light edges riding the band
        var edge = MTA.rect(c, { name: "open edge " + e, w: 1280, h: 2, r: 0, fill: "#ffffff", pos: [640, 360] });
        MTA.k(MTA.P(edge, "pos"), [[0.05, [640, 360]], [0.62, [640, e ? 640 : 80]]], "out");
        MTA.k(MTA.P(edge, "scale"), [[0.0, [0, 100]], [0.2, [100, 100]]], "out");
        MTA.k(MTA.P(edge, "op"), [[0.0, 0], [0.06, 100], [0.4, 70], [0.62, 0]], "lin");
        MTA.glow(edge, 30, 2.0);
        edge.outPoint = 0.64;
        edges.push(edge);
    }
    var spark = MTA.ellipse(c, { name: "open spark", w: 900, h: 4, fill: "#ffffff", pos: [640, 360] });
    MTA.k(MTA.P(spark, "scale"), [[0.0, [0, 100]], [0.14, [100, 100]], [0.4, [40, 100]]], "out");
    MTA.k(MTA.P(spark, "op"), [[0.0, 0], [0.05, 100], [0.38, 0]], "lin");
    MTA.glow(spark, 40, 2.4);
    spark.outPoint = 0.4;

    // filmic vignette over the 3D (inverted feathered ellipse)
    var vig = MTA.solid(c, "#000000", "vignette");
    var vm = vig.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
    var ve = new Shape();
    ve.vertices = [[640, -60], [1400, 360], [640, 780], [-120, 360]];
    ve.inTangents = [[-420, 0], [0, -230], [420, 0], [0, 230]];
    ve.outTangents = [[420, 0], [0, 230], [-420, 0], [0, -230]];
    ve.closed = true;
    vm.property("ADBE Mask Shape").setValue(ve);
    vm.property("ADBE Mask Feather").setValue([260, 260]);
    vm.inverted = true;
    MTA.P(vig, "op").setValue(70);
    vig.outPoint = 3.96;

    // ---------- C) the line over the traces, on a soft dark band
    var shade = MTA.band(c, "#000000", -200, 190, 130, 0);
    shade.name = "line band";
    MTA.k(MTA.P(shade, "op"), [[2.4, 0], [2.7, 72], [3.5, 72], [3.62, 0]], "lin");
    shade.outPoint = 3.64;
    var line = MTA.text(c, { text: "Think different.", font: MTA.F.semi, size: 72, color: INK, just: "C", tracking: -12, center: true, pos: [640, 112] });
    line.inPoint = 2.55; line.outPoint = 3.62;
    MTA.reveal(line, 2.55, 2.95, 22);
    MTA.k(MTA.P(line, "op"), [[3.42, 100], [3.6, 0]], "lin");
    MTA.k(MTA.P(line, "pos"), [[3.4, [640, 112]], [3.6, [640, 96]]], "in");
    MTA.shadow(line, 70, 0, 26);

    // ---------- D) the chip flares to white
    var bloom = MTA.glowBlob(c, "#ffffff", [640, 380], 820, 0);
    bloom.name = "flare bloom";
    MTA.k(MTA.P(bloom, "op"), [[3.5, 0], [3.74, 80], [3.98, 0]], "inout");
    bloom.inPoint = 3.5; bloom.outPoint = 4.0;
    var flash = MTA.solid(c, "#ffffff", "flash");
    flash.blendingMode = BlendingMode.ADD;
    MTA.k(MTA.P(flash, "op"), [[3.62, 0], [3.76, 30], [3.96, 0]], "lin");
    flash.inPoint = 3.6; flash.outPoint = 4.0;

    // ---------- E) end card
    var endBg = MTA.solid(c, BG, "end bg"); endBg.inPoint = END;
    var glowBack = null;
    if (new File(LASTF).exists) {                                // the last 3D frame as an ambient, deeply blurred backdrop
        glowBack = MTA.image(c, LASTF, 1280 * 1.25, [640, 420]);
        glowBack.name = "end glow";
        glowBack.inPoint = END;
        var gb = glowBack.property("ADBE Effect Parade").addProperty("ADBE Gaussian Blur 2");
        gb.property("ADBE Gaussian Blur 2-0001").setValue(90);
        MTA.k(MTA.P(glowBack, "op"), [[END, 0], [4.15, 32]], "out");
    }
    var head = MTA.text(c, { text: "Think different.", font: MTA.F.semi, size: 116, color: INK, just: "C", tracking: -18, center: true, pos: [640, 266] });
    head.inPoint = 3.84;
    MTA.reveal(head, 3.84, 4.22, 26);
    MTA.k(MTA.P(head, "scale"), [[3.84, [106, 106]], [4.5, [100, 100]]], "out");
    // colour shimmer: Apple's blue -> pink travels through the white type once (gradient band, matted by a copy of the line)
    var sheenMatte = head.duplicate(); sheenMatte.name = "sheen matte";
    var sheen = MTA.solid(c, "#000000", "sheen");
    MTA.ramp(sheen, { from: [380, 266], to: [900, 266], c1: LINK, c2: "#FF375F" });
    var sm = sheen.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
    var bandAt = function (x) { var b = new Shape(); b.vertices = [[x - 60, 120], [x + 120, 120], [x + 60, 420], [x - 120, 420]]; b.closed = true; return b; };
    var smp = sm.property("ADBE Mask Shape");
    smp.setValueAtTime(4.3, bandAt(160)); smp.setValueAtTime(4.95, bandAt(1120));
    sm.property("ADBE Mask Feather").setValue([150, 0]);
    sheen.inPoint = 4.3; sheen.outPoint = 4.97; sheenMatte.inPoint = 4.3; sheenMatte.outPoint = 4.97;
    sheenMatte.moveBefore(sheen);
    sheen.setTrackMatte(sheenMatte, TrackMatteType.ALPHA);

    var learn = MTA.button(c, { text: "Learn more", bg: BLUE, fg: "#ffffff", radius: 35, h: 70, padX: 36, font: MTA.F.reg, size: 29, pos: [640, 406] });
    var buy = MTA.button(c, { text: "Buy", fg: LINK, border: LINK, borderW: 2.5, radius: 35, h: 70, padX: 34, font: MTA.F.reg, size: 29, pos: [640, 406] });
    MTA.row([learn, buy], 640, 406, 22);
    var pills = [[learn, 4.28], [buy, 4.38]];
    for (var i = 0; i < pills.length; i++) {
        var b = pills[i][0], t0 = pills[i][1], p0 = MTA.P(b, "pos").value;
        b.inPoint = t0;
        for (var z = 1; z <= c.numLayers; z++) { if (c.layer(z).parent === b) { c.layer(z).inPoint = t0; } }
        MTA.k(MTA.P(b, "op"), [[t0, 0], [t0 + 0.22, 100]], "lin");
        MTA.k(MTA.P(b, "pos"), [[t0, [p0[0], p0[1] + 16]], [t0 + 0.32, p0]], "out");
    }
    var dom = MTA.text(c, { text: "apple.com", font: MTA.F.med, size: 24, color: GREY, just: "C", tracking: 10, center: true, pos: [640, 500] });
    dom.inPoint = 4.55;
    MTA.k(MTA.P(dom, "op"), [[4.55, 0], [4.8, 100]], "lin");

    MTA.motionBlurAll(c);
    var crisp = [vig, shade, endBg, bloom, flash, sheen, sheenMatte].concat(edges);
    for (var q = 0; q < crisp.length; q++) { crisp[q].motionBlur = false; }
    if (glowBack) { glowBack.motionBlur = false; }
})();
